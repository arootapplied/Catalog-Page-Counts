#!/usr/bin/env python3
"""Minimal dependency-free .xlsx writer (Python standard library only).

Exists so the billing workbook can be produced in locked-down environments
where `openpyxl` cannot be installed (no network / blocked package index).
An .xlsx file is just a zip of XML parts, and everything this skill needs
(inline string + number cells, bold, solid fill, font color, column widths,
multiple sheets) is expressible with the stdlib `zipfile` + string XML.

This is intentionally small and covers only what the billing workbook uses.
It is not a general-purpose Excel library. If `openpyxl` IS available, prefer
it — but this keeps the Excel deliverable working when it is not, so the skill
never has to fall back to HTML/CSV as a stand-in for the real workbook.

Style dict per cell (all keys optional):
    {"bold": True, "fill": "FFFF00", "color": "FF0000"}
Colors are RGB hex strings without the leading '#'.
"""
import zipfile
from xml.sax.saxutils import escape


def _col_letter(idx):
    """0-based column index -> Excel column letter(s) (0->A, 26->AA)."""
    s = ""
    idx += 1
    while idx:
        idx, rem = divmod(idx - 1, 26)
        s = chr(65 + rem) + s
    return s


class Sheet:
    def __init__(self, name):
        self.name = name
        self.rows = []          # each row: list of (value, style_dict|None)
        self.col_widths = {}    # 0-based col index -> width

    def append(self, cells):
        """cells: list where each item is a bare value or (value, style)."""
        row = []
        for item in cells:
            if isinstance(item, tuple):
                row.append((item[0], item[1]))
            else:
                row.append((item, None))
        self.rows.append(row)

    def set_col_width(self, idx, width):
        self.col_widths[idx] = width


class Workbook:
    def __init__(self):
        self.sheets = []

    def add_sheet(self, name):
        s = Sheet(name)
        self.sheets.append(s)
        return s

    # --- style registry -------------------------------------------------
    def _collect_styles(self):
        """Return (style_key -> xf_index) plus the font/fill tables needed."""
        fonts = [{}]          # index 0: default
        fills = [None, None]  # 0 = none, 1 = gray125 (both reserved by spec)
        xfs = [{}]            # index 0: default
        key_to_xf = {}

        def font_index(bold, color):
            sig = (bool(bold), color or None)
            for i, f in enumerate(fonts):
                if (f.get("bold", False), f.get("color")) == sig:
                    return i
            fonts.append({"bold": bool(bold), "color": color})
            return len(fonts) - 1

        def fill_index(rgb):
            if rgb is None:
                return 0
            for i, f in enumerate(fills):
                if f == rgb:
                    return i
            fills.append(rgb)
            return len(fills) - 1

        for sheet in self.sheets:
            for row in sheet.rows:
                for _, style in row:
                    if not style:
                        continue
                    key = (style.get("bold", False), style.get("fill"),
                           style.get("color"))
                    if key in key_to_xf:
                        continue
                    fi = font_index(style.get("bold"), style.get("color"))
                    li = fill_index(style.get("fill"))
                    xfs.append({"font": fi, "fill": li})
                    key_to_xf[key] = len(xfs) - 1
        return key_to_xf, fonts, fills, xfs

    def _styles_xml(self, fonts, fills, xfs):
        font_parts = []
        for f in fonts:
            bits = ["<sz val=\"11\"/><name val=\"Calibri\"/>"]
            if f.get("bold"):
                bits.append("<b/>")
            if f.get("color"):
                bits.append(f"<color rgb=\"FF{f['color']}\"/>")
            font_parts.append("<font>" + "".join(bits) + "</font>")
        fill_parts = ["<fill><patternFill patternType=\"none\"/></fill>",
                      "<fill><patternFill patternType=\"gray125\"/></fill>"]
        for rgb in fills[2:]:
            fill_parts.append(
                "<fill><patternFill patternType=\"solid\">"
                f"<fgColor rgb=\"FF{rgb}\"/></patternFill></fill>")
        xf_parts = []
        for xf in xfs:
            fi = xf.get("font", 0)
            li = xf.get("fill", 0)
            applies = []
            if fi:
                applies.append("applyFont=\"1\"")
            if li:
                applies.append("applyFill=\"1\"")
            xf_parts.append(
                f"<xf numFmtId=\"0\" fontId=\"{fi}\" fillId=\"{li}\" "
                f"borderId=\"0\" xfId=\"0\" {' '.join(applies)}/>")
        return (
            "<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"yes\"?>"
            "<styleSheet xmlns=\"http://schemas.openxmlformats.org/spreadsheetml/2006/main\">"
            f"<fonts count=\"{len(font_parts)}\">{''.join(font_parts)}</fonts>"
            f"<fills count=\"{len(fill_parts)}\">{''.join(fill_parts)}</fills>"
            "<borders count=\"1\"><border><left/><right/><top/><bottom/><diagonal/></border></borders>"
            "<cellStyleXfs count=\"1\"><xf numFmtId=\"0\" fontId=\"0\" fillId=\"0\" borderId=\"0\"/></cellStyleXfs>"
            f"<cellXfs count=\"{len(xf_parts)}\">{''.join(xf_parts)}</cellXfs>"
            "<cellStyles count=\"1\"><cellStyle name=\"Normal\" xfId=\"0\" builtinId=\"0\"/></cellStyles>"
            "</styleSheet>")

    def _sheet_xml(self, sheet, key_to_xf):
        cols_xml = ""
        if sheet.col_widths:
            parts = []
            for idx, w in sorted(sheet.col_widths.items()):
                c = idx + 1
                parts.append(
                    f"<col min=\"{c}\" max=\"{c}\" width=\"{w}\" customWidth=\"1\"/>")
            cols_xml = "<cols>" + "".join(parts) + "</cols>"
        rows_xml = []
        for r, row in enumerate(sheet.rows, start=1):
            cells = []
            for c, (value, style) in enumerate(row):
                ref = f"{_col_letter(c)}{r}"
                s_attr = ""
                if style:
                    key = (style.get("bold", False), style.get("fill"),
                           style.get("color"))
                    s_attr = f" s=\"{key_to_xf[key]}\""
                if value is None or value == "":
                    if s_attr:
                        cells.append(f"<c r=\"{ref}\"{s_attr}/>")
                    continue
                if isinstance(value, bool):
                    value = str(value)
                if isinstance(value, (int, float)):
                    cells.append(f"<c r=\"{ref}\"{s_attr}><v>{value}</v></c>")
                else:
                    txt = escape(str(value))
                    cells.append(
                        f"<c r=\"{ref}\"{s_attr} t=\"inlineStr\">"
                        f"<is><t xml:space=\"preserve\">{txt}</t></is></c>")
            rows_xml.append(f"<row r=\"{r}\">{''.join(cells)}</row>")
        return (
            "<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"yes\"?>"
            "<worksheet xmlns=\"http://schemas.openxmlformats.org/spreadsheetml/2006/main\">"
            f"{cols_xml}<sheetData>{''.join(rows_xml)}</sheetData></worksheet>")

    def save(self, path):
        key_to_xf, fonts, fills, xfs = self._collect_styles()
        n = len(self.sheets)
        content_types = (
            "<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"yes\"?>"
            "<Types xmlns=\"http://schemas.openxmlformats.org/package/2006/content-types\">"
            "<Default Extension=\"rels\" ContentType=\"application/vnd.openxmlformats-package.relationships+xml\"/>"
            "<Default Extension=\"xml\" ContentType=\"application/xml\"/>"
            "<Override PartName=\"/xl/workbook.xml\" ContentType=\"application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml\"/>"
            "<Override PartName=\"/xl/styles.xml\" ContentType=\"application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml\"/>"
            + "".join(
                f"<Override PartName=\"/xl/worksheets/sheet{i+1}.xml\" "
                "ContentType=\"application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml\"/>"
                for i in range(n))
            + "</Types>")
        root_rels = (
            "<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"yes\"?>"
            "<Relationships xmlns=\"http://schemas.openxmlformats.org/package/2006/relationships\">"
            "<Relationship Id=\"rId1\" Type=\"http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument\" Target=\"xl/workbook.xml\"/>"
            "</Relationships>")
        sheets_decl = "".join(
            f"<sheet name=\"{escape(s.name)}\" sheetId=\"{i+1}\" r:id=\"rId{i+1}\"/>"
            for i, s in enumerate(self.sheets))
        workbook = (
            "<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"yes\"?>"
            "<workbook xmlns=\"http://schemas.openxmlformats.org/spreadsheetml/2006/main\" "
            "xmlns:r=\"http://schemas.openxmlformats.org/officeDocument/2006/relationships\">"
            f"<sheets>{sheets_decl}</sheets></workbook>")
        wb_rels = (
            "<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"yes\"?>"
            "<Relationships xmlns=\"http://schemas.openxmlformats.org/package/2006/relationships\">"
            + "".join(
                f"<Relationship Id=\"rId{i+1}\" Type=\"http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet\" Target=\"worksheets/sheet{i+1}.xml\"/>"
                for i in range(n))
            + f"<Relationship Id=\"rId{n+1}\" Type=\"http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles\" Target=\"styles.xml\"/>"
            "</Relationships>")

        with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
            z.writestr("[Content_Types].xml", content_types)
            z.writestr("_rels/.rels", root_rels)
            z.writestr("xl/workbook.xml", workbook)
            z.writestr("xl/_rels/workbook.xml.rels", wb_rels)
            z.writestr("xl/styles.xml", self._styles_xml(fonts, fills, xfs))
            for i, s in enumerate(self.sheets):
                z.writestr(f"xl/worksheets/sheet{i+1}.xml",
                           self._sheet_xml(s, key_to_xf))
