#!/usr/bin/env python3
"""Chapter-grouped, single-supplier billing workbook for /catalog-page-counts.

This is the DEFAULT Excel deliverable format as of 2026-08 (see
references/calibration-history.md, "Climax Metal format adoption"), replacing
the old multi-supplier Entry-column layout (catalog_billing_workbook.py) for
the common case: one extract PDF is about ONE named/target supplier, and the
deliverable answers "how many pages does this supplier occupy, by catalog
chapter" -- not a full co-op-billing split of every brand on every page.

Scope is intentionally narrow: `regions.json` for this script should contain
ONLY the target supplier's own billable regions. Any other supplier sharing a
page is simply left unmeasured -- its share of the page shows up as the
measurement engine's own ">15% unattributed" invariant flag, which is
EXPECTED here (not a defect to resolve) and gets written into the workbook as
an explained note rather than suppressed. This is a deliberate scope choice,
not a shortcut: don't also try to fully bill co-located suppliers in the same
run, and don't hide the resulting flags -- explain them.

Usage:
  python3 catalog_chapter_workbook.py <catalog.pdf> <regions.json> \
      <folio_map.json> <chapter_map.json> <supplier> <source_pdf_name> \
      <out.xlsx> [overlay_dir] [flag_note]

  regions.json:    [{"page": 1-based PDF page, "supplier": name,
                     "rect": [x0,y0,x1,y1], "billable": true}, ...]
                   -- target supplier's regions only, same schema as
                   catalog_page_counts.py's `measure` command.
  folio_map.json:  {"1": 198, "2": 199, ...}  (PDF page -> printed page)
  chapter_map.json:{"1": "General Industrial Products", ...}  (PDF page ->
                   the chapter name recovered from that page's own running
                   header banner -- read it off the page, never assume it
                   from the file name or a prior run's chapter list.)
  supplier:        display name for the workbook title, e.g. "Climax Metal"
  source_pdf_name: filename recorded in the Measurements sheet, e.g.
                   "Climax_Metal.pdf"
  overlay_dir:     optional; if given, one audit overlay PNG per measured
                   page, same as catalog_page_counts.py's `measure` command.
  flag_note:       optional free-text explanation for the invariant-flags
                   note (who else is on the flagged pages and why they were
                   out of scope). Write this from what you actually saw
                   rendering the page -- never leave a flag unexplained, and
                   never invent a name for a co-located supplier you didn't
                   identify. If omitted but flags exist, a generic note is
                   used; supplying a specific one is strongly preferred.

Imports the tested area math (measure_page, CONFIG) from catalog_page_counts.py
rather than re-deriving it, exactly as the poppler fallback engine does --
one source of truth for the geometry regardless of which workbook shape sits
on top of it.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from catalog_page_counts import measure_page, render_overlay
from mini_xlsx import Workbook

DRAFT_BANNER = "DRAFT - FOR FINANCE REVIEW - NOT FOR INVOICING"
RED_BOLD = {"color": "FF0000", "bold": True}
GREY = {"color": "555555"}
BOLD = {"bold": True}
HEADER_FILL = {"fill": "D9D9D9", "bold": True}
YELLOW_BOLD = {"fill": "FFFF00", "bold": True}


def _clean(x):
    """3-decimal round that collapses to int when exact, matching the
    reference format (e.g. 3, not 3.0; 4.779 kept as-is)."""
    r = round(x, 3)
    return int(r) if r == int(r) else r


def _folio_range_desc(pdf_pages_sorted, folio_map, chapter_map):
    """Group consecutive (in PDF-page order) same-chapter pages into one
    block and render each as "min_printed-max_printed" (or a single number
    for a one-page block). A chapter's own internal printed-page gaps (a
    page dropped from the middle of an extract) are folded into that
    chapter's min-max shorthand rather than called out here -- the per-page
    tables carry the exact list. >1 block (i.e. the chapters aren't one
    running sequence) => append ", non-contiguous"."""
    blocks = []
    cur = [pdf_pages_sorted[0]]
    cur_chapter = chapter_map[str(pdf_pages_sorted[0])]
    for p in pdf_pages_sorted[1:]:
        if chapter_map[str(p)] == cur_chapter:
            cur.append(p)
        else:
            blocks.append(cur)
            cur = [p]
            cur_chapter = chapter_map[str(p)]
    blocks.append(cur)

    parts = []
    for block in blocks:
        printed = sorted(folio_map[str(p)] for p in block)
        parts.append(str(printed[0]) if len(printed) == 1
                      else f"{printed[0]}-{printed[-1]}")
    desc = ",".join(parts)
    if len(blocks) > 1:
        desc += ", non-contiguous"
    return desc


def build(pdf_path, regions_path, folio_map_path, chapter_map_path,
          supplier, source_pdf_name, out_path, overlay_dir=None, flag_note=""):
    import fitz
    doc = fitz.open(pdf_path)
    with open(regions_path) as f:
        all_regions = json.load(f)
    folio_map = {str(k): v for k, v in json.load(open(folio_map_path)).items()}
    chapter_map = {str(k): v for k, v in json.load(open(chapter_map_path)).items()}

    by_page = {}
    for r in all_regions:
        by_page.setdefault(r["page"], []).append(r)

    all_rows, all_flags = [], []
    for page_no in sorted(by_page):
        page = doc[page_no - 1]
        rows, flags = measure_page(page, by_page[page_no])
        for row in rows:
            row["printed"] = folio_map[str(page_no)]
            row["chapter"] = chapter_map[str(page_no)]
            row["pdf_page"] = page_no
        all_rows.extend(rows)
        all_flags.extend(flags)
        if overlay_dir:
            render_overlay(page, by_page[page_no], rows,
                           f"{overlay_dir}/page-{page_no:04d}-overlay.png")

    all_rows.sort(key=lambda r: r["pdf_page"])

    # chapter totals, in order of first appearance (by pdf page order)
    chapter_order, chapter_totals = [], {}
    for r in all_rows:
        ch = r["chapter"]
        if ch not in chapter_totals:
            chapter_order.append(ch)
            chapter_totals[ch] = 0.0
        chapter_totals[ch] += r["pct_of_content_page"] / 100.0
    grand_total = sum(chapter_totals.values())

    folio_desc = _folio_range_desc(sorted(by_page), folio_map, chapter_map)
    if all_flags:
        flag_clause = (f"{len(all_flags)} invariant flag"
                        f"{'s' if len(all_flags) != 1 else ''} (explained below)")
    else:
        flag_clause = "0 invariant flags"
    provenance = (f"PyMuPDF 1.28.0 (Engine A, offline wheel install), "
                  f"{source_pdf_name} ({doc.page_count} PDF pages / "
                  f"printed pp.{folio_desc}), {flag_clause}")

    wb = Workbook()

    # --- Page Counts -----------------------------------------------------
    ws = wb.add_sheet("Page Counts")
    ws.append([(DRAFT_BANNER, RED_BOLD)])
    ws.append([(provenance, GREY)])
    ws.append([])
    ws.append([(f"{supplier} - AI Page Counts", BOLD)])
    ws.append([])
    ws.append([("Chapter", HEADER_FILL), ("Page Count (fractional pages)", HEADER_FILL)])
    for ch in chapter_order:
        ws.append([ch, _clean(chapter_totals[ch])])
    ws.append([("TOTAL", YELLOW_BOLD), (_clean(grand_total), YELLOW_BOLD)])

    if all_flags:
        ws.append([])
        note = flag_note or (
            "Note on invariant flags: some measured pages show an "
            "unattributed remainder because other suppliers sharing those "
            "pages were out of scope for this run and were not "
            "individually measured. This is expected, not an error."
        )
        ws.append([(note, GREY)])

    ws.append([])
    ws.append([("Chapter", BOLD), ("Catalog Page (printed)", BOLD),
               ("Fraction of Page", BOLD), ("Billable", BOLD)])
    for r in all_rows:
        ws.append([r["chapter"], r["printed"],
                    _clean(r["pct_of_content_page"] / 100.0),
                    "Yes" if r["billable"] else "No"])

    ws.set_col_width(0, 34)
    ws.set_col_width(1, 20)
    ws.set_col_width(2, 16)
    ws.set_col_width(3, 10)

    # --- Per-page detail ---------------------------------------------------
    ws2 = wb.add_sheet("Per-page detail")
    ws2.append([(h, BOLD) for h in
                ["Chapter", "Catalog Page", "Supplier", "Fraction",
                 "Billable", "Region (x0,y0,x1,y1)"]])
    for r in all_rows:
        ws2.append([r["chapter"], r["printed"], supplier,
                    _clean(r["pct_of_content_page"] / 100.0),
                    "Yes" if r["billable"] else "No", r["rect"]])
    ws2.set_col_width(0, 30)
    ws2.set_col_width(1, 14)
    ws2.set_col_width(3, 10)
    ws2.set_col_width(4, 9)
    ws2.set_col_width(5, 26)

    # --- Measurements ------------------------------------------------------
    ws3 = wb.add_sheet("Measurements")
    ws3.append([(h, BOLD) for h in
                ["PDF page (1-based)", "Catalog Page (printed)", "Chapter",
                 "sq pts", "% of content page", "Source PDF"]])
    for r in all_rows:
        ws3.append([r["pdf_page"], r["printed"], r["chapter"],
                    _clean(r["sq_pts"]), _clean(r["pct_of_content_page"]),
                    source_pdf_name])
    ws3.set_col_width(0, 16)
    ws3.set_col_width(1, 18)
    ws3.set_col_width(2, 30)
    ws3.set_col_width(3, 12)
    ws3.set_col_width(4, 16)
    ws3.set_col_width(5, 26)

    wb.save(out_path)
    print(f"saved {out_path} | grand total {_clean(grand_total)} pages | "
          f"{len(chapter_order)} chapter(s) | {len(all_flags)} flag(s)")
    if all_flags:
        print("Flags (expected -- co-located suppliers out of scope):")
        for fl in all_flags:
            print(f"  - {fl}")
    return all_rows, all_flags


if __name__ == "__main__":
    if len(sys.argv) < 8:
        print(__doc__)
        sys.exit(1)
    overlay_dir = sys.argv[8] if len(sys.argv) > 8 and sys.argv[8] else None
    flag_note = sys.argv[9] if len(sys.argv) > 9 else ""
    build(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5],
          sys.argv[6], sys.argv[7], overlay_dir, flag_note)
