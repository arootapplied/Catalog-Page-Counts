#!/usr/bin/env python3
"""Dependency-free fallback engine for /catalog-page-counts.

Use this ONLY when PyMuPDF (fitz) cannot be installed (locked-down environment,
blocked package index) but the PDF still needs exact-geometry measurement. It
extracts the SAME exact glyph/image coordinates PyMuPDF would, via poppler's
`xpdfimport` binary — the tool that ships inside LibreOffice and is the same
poppler engine behind `pdftoppm`. This is NOT a keyword/text estimate; it is
real PDF geometry, and the numbers are computed with the identical area math
and invariants as the primary engine (imported from catalog_page_counts.py, so
there is one source of truth for the math, never two).

What it CANNOT do that the PyMuPDF path can: rasterize a page to a PNG. So the
audit overlays here are SVG, reconstructed from the exact text/image rectangles.
That lets a human verify every band boundary against real content, but it is not
a picture of the rendered page — so a human eyeball against the actual PDF is
still owed before a number is invoiced (see SKILL.md guardrails 5 and 8).

Finding xpdfimport (no install needed, it ships with LibreOffice):
  common paths: /usr/lib/libreoffice/program/xpdfimport
                /opt/libreoffice*/program/xpdfimport
                (macOS) /Applications/LibreOffice.app/Contents/Resources/xpdfimport

Usage:
  python3 catalog_page_counts_poppler.py probe
      Report whether an exact-geometry engine is available here (fitz? xpdfimport?).

  python3 catalog_page_counts_poppler.py extract <catalog.pdf> <out_geom.json>
      Parse the PDF's exact text/image coordinate layer to per-page geometry
      (points, top-left origin, y down): {page: {w,h,lines:[...],images:[...]}}.

  python3 catalog_page_counts_poppler.py measure <catalog.pdf> <regions.json> <out.csv> [overlay_dir]
      Same regions.json format and same CSV columns as the primary engine, plus
      one SVG overlay per measured page in overlay_dir.
"""
import json, csv, sys, os, shutil, subprocess, html

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from catalog_page_counts import area, measure_page, CONFIG  # ONE source of math truth

XPDF_CANDIDATES = [
    "/usr/lib/libreoffice/program/xpdfimport",
    "/usr/lib64/libreoffice/program/xpdfimport",
    "/opt/libreoffice/program/xpdfimport",
    "/Applications/LibreOffice.app/Contents/Resources/xpdfimport",
]


def find_xpdfimport():
    for p in XPDF_CANDIDATES:
        if os.path.exists(p):
            return p
    for root in ("/opt", "/usr/lib", "/usr/lib64"):
        for base, _dirs, files in os.walk(root):
            if "xpdfimport" in files:
                return os.path.join(base, "xpdfimport")
    hit = shutil.which("xpdfimport")
    return hit


# ---------------------------------------------------------------------------
# xpdfimport trace parser
# ---------------------------------------------------------------------------
def _mat_apply(m, x, y):
    a, b, c, d, e, f = m
    return (a * x + c * y + e, b * x + d * y + f)


def extract(pdf_path):
    """Run xpdfimport and parse its vector trace into per-page geometry.

    Coordinate model (verified against poppler's pdfioutdev output):
      - drawChar coords are already in POINTS, top-left origin, y down.
      - updateCtm / image placement are device units = 1/100 point; /100.
    """
    xpdf = find_xpdfimport()
    if not xpdf:
        raise RuntimeError(
            "xpdfimport not found. It ships with LibreOffice; install libreoffice "
            "or point to the binary. Searched: " + ", ".join(XPDF_CANDIDATES))
    tmp_out = pdf_path + ".xpdfimport.tmp"
    # xpdfimport writes the command trace to stdout, image blobs to stderr.
    proc = subprocess.run([xpdf, pdf_path, tmp_out],
                          capture_output=True, text=True, errors="replace")
    try:
        os.remove(tmp_out)
    except OSError:
        pass
    if not proc.stdout:
        raise RuntimeError(f"xpdfimport produced no trace (rc={proc.returncode}). "
                           f"Is the PDF readable? stderr head: {proc.stderr[:200]!r}")
    return _parse_trace(proc.stdout.splitlines())


def _parse_trace(lines_iter):
    pages, cur, glyphs = [], None, []
    ctm = [100.0, 0.0, 0.0, -100.0, 0.0, 0.0]
    stack = []

    def flush():
        nonlocal glyphs
        if cur is not None:
            cur["lines"] = _cluster_lines(glyphs)
            pages.append(cur)
        glyphs = []

    for line in lines_iter:
        parts = line.split()
        if not parts:
            continue
        cmd = parts[0]
        if cmd == "startPage":
            flush() if cur is not None else None
            w = float(parts[1]) / 100.0
            h = float(parts[2]) / 100.0
            cur = {"w": w, "h": h, "images": []}
            ctm = [100.0, 0.0, 0.0, -100.0, 0.0, h * 100.0]
            stack = []
            glyphs = []
        elif cmd == "endPage":
            flush()
            cur = None
        elif cmd == "saveState":
            stack.append(list(ctm))
        elif cmd == "restoreState":
            if stack:
                ctm = stack.pop()
        elif cmd == "updateCtm":
            try:
                ctm = [float(x) for x in parts[1:7]]
            except ValueError:
                pass
        elif cmd == "drawChar":
            try:
                x0, y0, x1 = float(parts[1]), float(parts[2]), float(parts[3])
                fmD = float(parts[8])
            except (ValueError, IndexError):
                continue
            size = abs(fmD) if fmD else abs(float(parts[5]))
            ch = line.split(None, 10)[10] if len(parts) >= 11 else " "
            glyphs.append((x0, y0, x1, size, ch))
        elif cmd == "drawImage" and cur is not None:
            try:
                wpx, hpx, fmt = int(parts[1]), int(parts[2]), parts[4]
            except (ValueError, IndexError):
                wpx = hpx = 0
                fmt = parts[4] if len(parts) > 4 else "?"
            corners = [_mat_apply(ctm, ux, uy) for ux, uy in ((0, 0), (1, 0), (1, 1), (0, 1))]
            xs = [c[0] / 100.0 for c in corners]
            ys = [c[1] / 100.0 for c in corners]
            cur["images"].append({"x0": min(xs), "y0": min(ys),
                                  "x1": max(xs), "y1": max(ys),
                                  "w_px": wpx, "h_px": hpx, "fmt": fmt})
    flush() if cur is not None else None
    return pages


def _cluster_lines(glyphs):
    if not glyphs:
        return []
    gs = sorted(glyphs, key=lambda g: (round(g[1], 1), g[0]))
    lines, cur, cur_y = [], [], None
    for g in gs:
        y = g[1]
        if cur_y is None or abs(y - cur_y) <= max(2.0, g[3] * 0.4):
            cur.append(g)
            cur_y = y if cur_y is None else (cur_y + y) / 2
        else:
            lines.append(_finalize(cur))
            cur, cur_y = [g], y
    if cur:
        lines.append(_finalize(cur))
    return lines


def _finalize(gs):
    gs = sorted(gs, key=lambda g: g[0])
    text, prev_x1 = "", None
    for x0, y0, x1, size, ch in gs:
        if prev_x1 is not None and x0 - prev_x1 > size * 0.28:
            text += " "
        text += ch
        prev_x1 = x1
    x0 = min(g[0] for g in gs)
    x1 = max(g[2] for g in gs)
    baseline = sum(g[1] for g in gs) / len(gs)
    size = max(g[3] for g in gs)
    return {"text": text, "x0": round(x0, 2), "y0": round(baseline - size * 0.85, 2),
            "x1": round(x1, 2), "y1": round(baseline + size * 0.22, 2), "size": round(size, 2)}


# ---------------------------------------------------------------------------
# measure + SVG overlays  (area math reused from the primary engine)
# ---------------------------------------------------------------------------
class _PageShim:
    """Adapts parsed geometry to the object measure_page() expects."""
    def __init__(self, geom, number):
        self.rect = type("R", (), {"width": geom["w"], "height": geom["h"]})()
        self.number = number


def run_measure(pdf_path, regions_path, out_csv, overlay_dir=None):
    geom = extract(pdf_path)
    all_regions = json.load(open(regions_path))
    by_page = {}
    for r in all_regions:
        by_page.setdefault(r["page"], []).append(r)

    all_rows, all_flags = [], []
    for pg in sorted(by_page):
        if pg - 1 >= len(geom):
            all_flags.append(f"page {pg}: not present in PDF ({len(geom)} pages)")
            continue
        rows, flags = measure_page(_PageShim(geom[pg - 1], pg - 1), by_page[pg])
        all_rows.extend(rows)
        all_flags.extend(flags)
        if overlay_dir:
            os.makedirs(overlay_dir, exist_ok=True)
            open(f"{overlay_dir}/page-{pg:04d}-overlay.svg", "w").write(
                _svg(geom[pg - 1], by_page[pg], rows))

    with open(out_csv, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(all_rows[0].keys()))
        w.writeheader()
        w.writerows(all_rows)

    rollup = {}
    for row in all_rows:
        if row["billable"]:
            rollup[row["supplier"]] = rollup.get(row["supplier"], 0.0) + row["pct_of_content_page"] / 100.0
    print(f"[poppler fallback] measured {len(by_page)} page(s), {len(all_rows)} region(s) -> {out_csv}")
    print("\nPer-supplier rollup (billable, content-page basis):")
    for s, p in sorted(rollup.items(), key=lambda kv: -kv[1]):
        print(f"  {s:30s} {p:8.3f} pages")
    if all_flags:
        print(f"\n*** {len(all_flags)} FLAG(S) FOR HUMAN REVIEW ***")
        for fl in all_flags:
            print("  -", fl)
    else:
        print("\nNo flags. All invariants passed.")
    print("\nNOTE: overlays are SVG (no rasterizer in a no-PyMuPDF environment). "
          "A human eyeball against the real PDF is still owed before invoicing.")
    return all_rows, all_flags


_COLORS = ["#0d7a82", "#1f2e5c", "#cc5500", "#547d2e", "#8c0038"]


def _svg(geom, regions, rows):
    W, H = geom["w"], geom["h"]
    ca = area([0.0, CONFIG["header_h"], W, CONFIG["footer_y"]])
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
         f'viewBox="0 0 {W} {H}" font-family="Helvetica,Arial,sans-serif">',
         f'<rect x="0" y="0" width="{W}" height="{H}" fill="white" stroke="#333"/>',
         f'<rect x="0" y="0" width="{W}" height="{CONFIG["header_h"]}" fill="#444" opacity="0.28"/>',
         f'<rect x="0" y="{CONFIG["footer_y"]}" width="{W}" height="{H-CONFIG["footer_y"]}" fill="#444" opacity="0.28"/>']
    for im in geom["images"]:
        o.append(f'<rect x="{im["x0"]:.1f}" y="{im["y0"]:.1f}" width="{im["x1"]-im["x0"]:.1f}" '
                 f'height="{im["y1"]-im["y0"]:.1f}" fill="#6aa" opacity="0.20" stroke="#488" stroke-width="0.3"/>')
    for l in geom["lines"]:
        o.append(f'<rect x="{l["x0"]:.1f}" y="{l["y0"]:.1f}" width="{max(0.5,l["x1"]-l["x0"]):.1f}" '
                 f'height="{max(1.0,l["y1"]-l["y0"]):.1f}" fill="#bbb" opacity="0.35"/>')
    ci = {}
    for i, r in enumerate(regions):
        ci.setdefault(r["supplier"], _COLORS[len(ci) % len(_COLORS)])
        col = ci[r["supplier"]]
        x0, y0, x1, y1 = r["rect"]
        dash = ' stroke-dasharray="6 3"' if not r.get("billable", True) else ""
        o.append(f'<rect x="{x0:.1f}" y="{y0:.1f}" width="{x1-x0:.1f}" height="{y1-y0:.1f}" '
                 f'fill="{col}" opacity="0.14" stroke="{col}" stroke-width="1.8"{dash}/>')
        pct = area(r["rect"]) / ca * 100
        tag = f'{r["supplier"]}  {pct:.1f}% ({area(r["rect"])/ca:.3f} pg)' + \
              ("" if r.get("billable", True) else "  [HOUSE - not billed]")
        o.append(f'<text x="{x0+5:.1f}" y="{y0+14:.1f}" font-size="11" font-weight="bold" '
                 f'fill="{col}">{html.escape(tag)}</text>')
    o.append("</svg>")
    return "\n".join(o)


if __name__ == "__main__":
    if len(sys.argv) >= 2 and sys.argv[1] == "probe":
        try:
            import fitz  # noqa
            print("PyMuPDF (fitz): AVAILABLE  -> use the primary engine catalog_page_counts.py")
        except ImportError:
            print("PyMuPDF (fitz): NOT available")
        xp = find_xpdfimport()
        print(f"poppler xpdfimport: {'AVAILABLE at ' + xp if xp else 'NOT found'}")
        if not xp:
            print("  (install libreoffice to get it; it needs no network for the parse itself)")
    elif len(sys.argv) >= 4 and sys.argv[1] == "extract":
        geom = extract(sys.argv[2])
        json.dump(geom, open(sys.argv[3], "w"))
        print(f"extracted {len(geom)} pages -> {sys.argv[3]}")
    elif len(sys.argv) >= 5 and sys.argv[1] == "measure":
        run_measure(sys.argv[2], sys.argv[3], sys.argv[4],
                    sys.argv[5] if len(sys.argv) > 5 else None)
    else:
        print(__doc__)
        sys.exit(1)
