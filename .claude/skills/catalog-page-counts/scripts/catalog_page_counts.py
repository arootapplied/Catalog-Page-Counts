#!/usr/bin/env python3
"""Measurement engine for the /catalog-page-counts skill.

Computes per-supplier page-space shares from exact PDF coordinates,
enforces geometric invariants, and renders visual audit overlays.

Usage:
  python3 _tools/catalog_page_counts.py selftest <sample.pdf>
      Run the regression test against the validated ACCUFORM/Justrite
      Safety Products sample page (catalog p. 66).

  python3 _tools/catalog_page_counts.py measure <catalog.pdf> <regions.json> <out.csv> [overlay_dir]
      regions.json: [{"page": 1-based page no, "supplier": name,
                      "rect": [x0, y0, x1, y1], "billable": true}, ...]
      Writes one CSV row per region plus a per-supplier rollup, and an
      overlay PNG per measured page if overlay_dir is given.

Requires: pymupdf (pip install pymupdf) for the measure/selftest/overlay
commands. The pure area-math + invariant helpers (area, intersect_area,
measure_page, CONFIG) import WITHOUT pymupdf, so the dependency-free poppler
fallback (catalog_page_counts_poppler.py) can reuse the exact same math
rather than re-deriving coordinate arithmetic. `import fitz` is therefore
deferred into the functions that actually rasterize/open the PDF.
"""
import csv
import json
import sys

# Layout constants for the 2025/26 catalog edition (603 x 783 pt pages).
# Re-verify on sample pages before running a new edition (skill guardrail 4).
CONFIG = {
    "header_h": 45.0,    # title banner band: y < header_h is non-billable
    "footer_y": 750.0,   # footer band: y > footer_y is non-billable
    "overlap_tol": 1.0,  # sq pts of region overlap tolerated (rounding slop)
    "unattributed_flag_pct": 15.0,  # flag page if this % of content is unassigned
}

OVERLAY_COLORS = [
    (0.0, 0.48, 0.52),   # teal
    (0.12, 0.18, 0.36),  # navy
    (0.80, 0.33, 0.0),   # orange
    (0.33, 0.55, 0.18),  # green
    (0.55, 0.0, 0.22),   # maroon
]


def area(rect):
    x0, y0, x1, y1 = rect
    return max(0.0, x1 - x0) * max(0.0, y1 - y0)


def intersect_area(a, b):
    x0, y0 = max(a[0], b[0]), max(a[1], b[1])
    x1, y1 = min(a[2], b[2]), min(a[3], b[3])
    return area((x0, y0, x1, y1)) if x1 > x0 and y1 > y0 else 0.0


def measure_page(page, regions, cfg=CONFIG):
    """Measure one page. regions: [{supplier, rect, billable}].
    Returns (rows, flags). Every geometric violation lands in flags."""
    pw, ph = page.rect.width, page.rect.height
    content_rect = (0.0, cfg["header_h"], pw, cfg["footer_y"])
    content_area = area(content_rect)
    flags = []

    for r in regions:
        out = intersect_area(r["rect"], content_rect)
        if area(r["rect"]) - out > cfg["overlap_tol"]:
            flags.append(
                f"{r['supplier']}: region extends outside content band "
                f"(header/footer leak) on page {page.number + 1}"
            )
    for i in range(len(regions)):
        for j in range(i + 1, len(regions)):
            ov = intersect_area(regions[i]["rect"], regions[j]["rect"])
            if ov > cfg["overlap_tol"]:
                flags.append(
                    f"regions overlap by {ov:,.0f} sq pts on page {page.number + 1}: "
                    f"{regions[i]['supplier']} vs {regions[j]['supplier']}"
                )

    billable_total = sum(area(r["rect"]) for r in regions if r.get("billable", True))
    assigned_total = sum(area(r["rect"]) for r in regions)
    unattributed_pct = (content_area - assigned_total) / content_area * 100.0
    if unattributed_pct > cfg["unattributed_flag_pct"]:
        flags.append(
            f"page {page.number + 1}: {unattributed_pct:.1f}% of content area "
            f"unattributed (threshold {cfg['unattributed_flag_pct']}%) - needs review"
        )

    rows = []
    for r in regions:
        a = area(r["rect"])
        rows.append({
            "page": page.number + 1,
            "supplier": r["supplier"],
            "billable": r.get("billable", True),
            "sq_pts": round(a, 1),
            "pct_of_content_page": round(a / content_area * 100.0, 2),
            "pct_of_billable": round(a / billable_total * 100.0, 2)
            if r.get("billable", True) and billable_total else 0.0,
            "rect": ";".join(f"{v:.1f}" for v in r["rect"]),
        })
    return rows, flags


def render_overlay(page, regions, rows, out_png, cfg=CONFIG, dpi=150):
    """Render the page with billed regions, labels, and exclusion bands drawn on."""
    import fitz
    pw = page.rect.width
    shape = page.new_shape()
    shape.draw_rect(fitz.Rect(0, 0, pw, cfg["header_h"]))
    shape.draw_rect(fitz.Rect(0, cfg["footer_y"], pw, page.rect.height))
    shape.finish(fill=(0.3, 0.3, 0.3), fill_opacity=0.35)
    shape.commit()

    by_supplier = {}
    for i, r in enumerate(regions):
        key = r["supplier"]
        if key not in by_supplier:
            by_supplier[key] = OVERLAY_COLORS[len(by_supplier) % len(OVERLAY_COLORS)]
        color = by_supplier[key]
        rect = fitz.Rect(*r["rect"])
        shape = page.new_shape()
        shape.draw_rect(rect)
        shape.finish(color=color, fill=color, fill_opacity=0.16, width=1.6)
        shape.commit()
        row = rows[i]
        label = (f"{r['supplier']}  {row['pct_of_content_page']}% of page"
                 + ("" if r.get("billable", True) else "  [NOT BILLED]"))
        page.insert_text(fitz.Point(rect.x0 + 4, rect.y0 + 12), label,
                         fontsize=9, color=color,
                         render_mode=0, fill_opacity=1)
    page.get_pixmap(dpi=dpi).save(out_png)


def run_measure(pdf_path, regions_path, out_csv, overlay_dir=None):
    import fitz
    doc = fitz.open(pdf_path)
    with open(regions_path) as f:
        all_regions = json.load(f)
    by_page = {}
    for r in all_regions:
        by_page.setdefault(r["page"], []).append(r)

    all_rows, all_flags = [], []
    for page_no in sorted(by_page):
        page = doc[page_no - 1]
        rows, flags = measure_page(page, by_page[page_no])
        all_rows.extend(rows)
        all_flags.extend(flags)
        if overlay_dir:
            render_overlay(page, by_page[page_no], rows,
                           f"{overlay_dir}/page-{page_no:04d}-overlay.png")

    with open(out_csv, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(all_rows[0].keys()))
        w.writeheader()
        w.writerows(all_rows)

    rollup = {}
    for row in all_rows:
        if row["billable"]:
            rollup[row["supplier"]] = rollup.get(row["supplier"], 0.0) \
                + row["pct_of_content_page"] / 100.0
    print(f"Measured {len(by_page)} page(s), {len(all_rows)} region(s) -> {out_csv}")
    print("\nPer-supplier rollup (billable pages, content-page basis):")
    for s, pages in sorted(rollup.items(), key=lambda kv: -kv[1]):
        print(f"  {s:30s} {pages:8.3f} pages")
    if all_flags:
        print(f"\n*** {len(all_flags)} FLAG(S) FOR HUMAN REVIEW ***")
        for fl in all_flags:
            print(f"  - {fl}")
    else:
        print("\nNo flags. All invariants passed.")
    return all_rows, all_flags


# Regression fixture: ACCUFORM/Justrite Safety Products page (catalog p. 66),
# validated by visual inspection 2026-07-10. Page size 603 x 783 pts.
SELFTEST_REGIONS = [
    {"page": 1, "supplier": "Accuform NMC",
     "rect": [40.5, 53.0, 300.0, 392.3], "billable": True},
    {"page": 1, "supplier": "Accuform NMC",
     "rect": [40.5, 402.4, 300.0, 620.4], "billable": True},
    {"page": 1, "supplier": "Justrite/Hughes",
     "rect": [303.0, 52.3, 568.1, 619.9], "billable": True},
    {"page": 1, "supplier": "House (Did You Know)",
     "rect": [40.5, 638.0, 562.3, 737.0], "billable": False},
]
SELFTEST_EXPECT = {  # pct_of_content_page per supplier, +/- 0.05
    "Accuform NMC": 34.02,
    "Justrite/Hughes": 35.40,
    "House (Did You Know)": 12.15,
}


def run_selftest(pdf_path):
    import fitz
    doc = fitz.open(pdf_path)
    page = doc[0]
    assert abs(page.rect.width - 603.0) < 0.5 and abs(page.rect.height - 783.0) < 0.5, \
        f"unexpected page size {page.rect.width} x {page.rect.height}"
    rows, flags = measure_page(page, SELFTEST_REGIONS)
    header_footer_flags = [f for f in flags if "leak" in f or "overlap" in f]
    assert not header_footer_flags, f"invariant violations: {header_footer_flags}"
    got = {}
    for row in rows:
        got[row["supplier"]] = got.get(row["supplier"], 0.0) + row["pct_of_content_page"]
    failures = []
    for supplier, expect in SELFTEST_EXPECT.items():
        if abs(got.get(supplier, 0.0) - expect) > 0.05:
            failures.append(f"{supplier}: expected {expect}, got {got.get(supplier)}")
    if failures:
        print("SELFTEST FAILED:")
        for f in failures:
            print(f"  - {f}")
        sys.exit(1)
    print("SELFTEST PASSED")
    for supplier, pct in got.items():
        print(f"  {supplier:25s} {pct:6.2f}% of content page")


if __name__ == "__main__":
    if len(sys.argv) >= 3 and sys.argv[1] == "selftest":
        run_selftest(sys.argv[2])
    elif len(sys.argv) >= 5 and sys.argv[1] == "measure":
        run_measure(sys.argv[2], sys.argv[3], sys.argv[4],
                    sys.argv[5] if len(sys.argv) > 5 else None)
    else:
        print(__doc__)
        sys.exit(1)
