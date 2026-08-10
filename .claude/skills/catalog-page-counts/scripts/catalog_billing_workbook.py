#!/usr/bin/env python3
"""Build the official-format billing workbook for /catalog-page-counts.

Takes the measurement CSV emitted by catalog_page_counts.py and produces the
team's spreadsheet layout: suppliers alphabetical under registry names,
family-grouped rows highlighted with a group subtotal, per-page fraction
entries across columns, blue check total + diff column, grand total, and
excluded ad/promo pages plus house content listed separately.

Usage:
  python3 _tools/catalog_billing_workbook.py <measure.csv> <pages> <out.xlsx> [ad_pages] [note]
    <pages> maps each measured PDF page to the number PRINTED on that page, two forms:
      - an integer offset for a CONTIGUOUS run: printed = PDF page + offset (e.g. 176)
      - a path to a JSON folio map for a NON-CONTIGUOUS extract, e.g. folios.json:
            {"1": 272, "2": 278, "3": 280, ...}   (PDF page -> printed page)
        Use this for supplier extracts (the common case) — CRC, Dodge, etc. pull
        scattered pages (272-306, 380-417, 484...), so a single offset mislabels them.
        If the measurement CSV already carries a `printed_page` column, that wins.
    ad_pages: comma-separated printed pages excluded from the official count
              (full-page supplier ads/promos), e.g. "195,196,197,198,199"
    note:     optional provenance line stamped under the DRAFT banner (engine,
              catalog, page range, flag count) — see DRAFT_NOTE below.

Sheets produced: "Page Counts" (the billing summary), "Per-page detail" (one row
per measured region, brand-as-logo'd vs. official supplier row), and
"Measurements" (the raw geometry behind every number — sq pts, both percentage
bases, and the exact region rectangle, so the CSV never has to ship separately).

Every workbook is stamped DRAFT FOR FINANCE REVIEW on all sheets. That is
deliberate and matches skill guardrail 3: this tool does not finalize supplier
charges, so there is no flag to turn the stamp off.

Dependencies: none beyond the Python standard library. Writes .xlsx via the
bundled mini_xlsx writer, so the Excel deliverable still works in locked-down
environments where openpyxl cannot be installed. (An .xlsx is just zipped XML;
mini_xlsx handles the small subset of formatting this workbook needs.)
"""
import csv
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mini_xlsx import Workbook


def resolve_printed(row, pages_arg, folio_map):
    """Printed page number for a measurement row. Priority:
    1) a printed_page column already in the CSV,
    2) an explicit folio map (non-contiguous extracts),
    3) integer offset (contiguous runs)."""
    if row.get("printed_page") not in (None, ""):
        return row["printed_page"]
    pdf_page = str(int(row["page"]))
    if folio_map is not None:
        return folio_map.get(pdf_page, f"~{pdf_page}?")  # flag unmapped, don't guess silently
    return int(row["page"]) + pages_arg

BOLD = {"bold": True}
YELLOW = {"fill": "FFFF00"}
YELLOW_BOLD = {"fill": "FFFF00", "bold": True}
BLUE = {"color": "0000FF"}
RED_BOLD = {"color": "FF0000", "bold": True}
GREY = {"color": "808080"}

DRAFT_BANNER = "DRAFT - FOR FINANCE REVIEW - NOT FOR INVOICING"


def stamp_draft(ws, note):
    """Put the DRAFT banner (+ optional provenance line) at the top of a sheet.

    Guardrail 3: every billing sheet this skill produces is a draft for finance
    to review, so this is unconditional rather than a flag someone can forget.
    """
    ws.append([(DRAFT_BANNER, RED_BOLD)])
    if note:
        ws.append([(note, GREY)])
    ws.append([])

# Supplier registry: logo-level brand -> official supplier row.
# Derived from the billing team's 25/26 Janitorial answer key (2026-07-13).
# Extend as more chapters are calibrated; unmapped brands pass through as-is.
MAP = {
    "Anchor Wiping Cloth": "Anchor Wiping Cloth",
    "CRC": "CRC",
    "CRC (Weld-Aid)": "CRC",
    "Boardwalk": "Essendant (Boardwalk)",
    "Clorox": "Essendant (Clorox)",
    "Clorox (Pine-Sol)": "Essendant (Clorox)",
    "Dart": "Essendant (Dart)",
    "Kimberly-Clark (Kleenex)": "Essendant (Kimberly Clark: Kleenex)",
    "Kimberly-Clark (Scott)": "Essendant (Kimberly Clark: Scott)",
    "Kimberly-Clark (WypAll)": "Essendant (Kimberly Clark: Wypall)",
    "Krystal": "Essendant (Krystal)",
    "P&G Professional (Mr. Clean)": "Essendant (P&G Professional)",
    "P&G Professional (Comet)": "Essendant (P&G Professional)",
    "P&G Professional (Dawn)": "Essendant (P&G Professional)",
    "P&G Professional (Joy)": "Essendant (P&G Professional)",
    "P&G Professional (Ivory)": "Essendant (P&G Professional)",
    "Reckitt Benckiser (LYSOL)": "Essendant (Reckitt Benckiser)",
    "Rubbermaid": "Essendant (Rubbermaid)",
    "Simple Green": "Essendant (Simple Green)",
    "Loctite": "Henkel (Loctite)",
    "Permatex": "ITW Performance Polymers (Permatex)",
    "Osborn": "Osborn",
    "Rust-Oleum": "Rust-Oleum",
    "Concrobium": "Rust-Oleum (Concrobium)",
    "Krud Kutter": "Rust-Oleum (Krud Kutter)",
    "Mean Green": "Rust-Oleum (Mean Green)",
    "Roto-Rooter": "Rust-Oleum (Roto-Rooter)",
    "SC Johnson Professional": "SC Johnson",
    "Drano": "SC Johnson (Drano)",
    "fantastik": "SC Johnson (Fantastik)",
    "OFF!": "SC Johnson (Off)",
    "Raid": "SC Johnson (Raid)",
    "Scrubbing Bubbles": "SC Johnson (Scrubbing Bubbles)",
    "Windex": "SC Johnson (Windex)",
    "Ziploc": "SC Johnson (Ziploc)",
    "Sprayon": "Sherwin Williams (Sprayon)",
    "WD-40": "WD-40",
    # Schaeffler family (bearings) — see references/supplier-registry.md
    "FAG": "Schaeffler (FAG)",
    "INA": "Schaeffler (INA)",
    "Schaeffler": "Schaeffler",
    # Regal Rexnord family (bearings / power transmission)
    "Dodge": "Regal Rexnord (Dodge)",
    "Rexnord": "Regal Rexnord (Rexnord)",
    "McGill (Regal Rexnord)": "Regal Rexnord (McGill)",
    "Thomson": "Regal Rexnord (Thomson)",
    "LEESON (Regal Rexnord)": "Regal Rexnord (LEESON)",
    # Bearings — standalone Japanese manufacturers, NOT Schaeffler/Regal families
    "NTN": "NTN",
    "NSK": "NSK",
    # PIP family (safety/PPE). Bouton Optical is PIP's eyewear brand and shows
    # as its own logo; grouped so the family subtotal and the per-brand rows are
    # both visible. Confirm the rollup with the billing owner before invoicing.
    "PIP": "PIP",
    "Bouton Optical": "PIP (Bouton Optical)",
    # Safety/PPE standalones — see references/supplier-registry.md
    "MCR Safety": "MCR Safety",
    "MSA": "MSA",
    "Master Lock": "Master Lock",
    "Sqwincher": "Sqwincher",
    "KleenGuard (Jackson Safety)": "KleenGuard (Jackson Safety)",
    # Motors chapter (ABB extract). The printed logo is a single combined
    # "ABB BALDOR-RELIANCE" lockup, so the rollup is asserted by the artwork.
    "ABB (Baldor-Reliance)": "ABB (Baldor-Reliance)",
    "WEG": "WEG",
    "Bison Gear": "Bison Gear",
    "Lovejoy": "Lovejoy",
    "JET": "JET",
    # Crescent family (hand tools). Wiss, Nicholson and Lufkin each print the
    # Crescent "C" lockup directly above their own wordmark, so — as with
    # Baldor-Reliance — the family is stated by the page, not inferred.
    # NOTE: Crescent and GEARWRENCH are both Apex Tool Group brands, but no
    # Apex logo or wording appears anywhere in the extract, so GEARWRENCH is
    # deliberately NOT folded in here. Confirm with the billing owner.
    "Crescent": "Crescent",
    "Crescent (Wiss)": "Crescent (Wiss)",
    "Crescent (Nicholson)": "Crescent (Nicholson)",
    "Crescent (Lufkin)": "Crescent (Lufkin)",
    "GEARWRENCH": "GEARWRENCH",
    "Anchor Brand": "Anchor Brand",
    "Empire": "Empire",
    "Precision Brand": "Precision Brand",
    "Milwaukee": "Milwaukee",
    "RIDGID": "RIDGID",
    # Wright Tool — independent US manufacturer, NOT an Apex Tool Group brand
    # despite sharing pages with GEARWRENCH. Keep separate from any Apex rollup.
    "Wright Tool": "Wright Tool",
}
GROUP_PREFIXES = ("Essendant", "Rust-Oleum", "SC Johnson",
                  "Schaeffler", "Regal Rexnord", "PIP", "Crescent")


def _pk(printed):
    """Sort key that keeps page order sane whether printed is an int or a
    string like '~305?' (unmapped page) — sort by the leading number."""
    if isinstance(printed, int):
        return printed
    import re
    m = re.search(r"\d+", str(printed))
    return int(m.group()) if m else 10 ** 9


def build(csv_path, pages_arg, out_path, ad_pages, folio_map=None, note=""):
    rows = list(csv.DictReader(open(csv_path)))
    for r in rows:
        r["printed"] = resolve_printed(r, pages_arg, folio_map)
        r["fraction"] = float(r["pct_of_content_page"]) / 100.0
        r["billable"] = r["billable"] == "True"

    entries, ads = {}, []
    house_total = 0.0
    for r in rows:
        if not r["billable"]:
            house_total += r["fraction"]
            continue
        if r["printed"] in ad_pages:
            ads.append(r)
            continue
        sup = MAP.get(r["supplier"], r["supplier"])
        entries.setdefault(sup, {})
        entries[sup][r["printed"]] = entries[sup].get(r["printed"], 0.0) + r["fraction"]

    merged = {sup: sorted(per.items(), key=lambda kv: _pk(kv[0]))
              for sup, per in entries.items()}

    wb = Workbook()
    ws = wb.add_sheet("Page Counts")
    stamp_draft(ws, note)

    maxpg = max((len(v) for v in merged.values()), default=1)
    header = (["Supplier", "Prior Yr Pages", "Pages", "Total Page Counts"] +
              [f"Entry {i+1}" for i in range(maxpg)] + ["Check Total", "Diff"])
    ws.append([(h, BOLD) for h in header])

    # group subtotals: total per family prefix, placed on the family's first row
    group_totals = {}
    for sup, pages in merged.items():
        grp = next((g for g in GROUP_PREFIXES if sup.startswith(g)), None)
        if grp:
            group_totals.setdefault(grp, 0.0)
            group_totals[grp] += sum(f for _, f in pages)
    group_seen = set()

    grand = 0.0
    for sup in sorted(merged):
        pages = merged[sup]
        tot = round(sum(f for _, f in pages), 2)
        grand += tot
        grp = next((g for g in GROUP_PREFIXES if sup.startswith(g)), None)
        cellstyle = YELLOW if grp else None
        gcell = ""
        if grp and grp not in group_seen:
            gcell = round(group_totals[grp], 2)
            group_seen.add(grp)
        row = [(sup, cellstyle), ("", cellstyle), (tot, cellstyle),
               ((gcell, YELLOW_BOLD) if (grp and gcell != "") else ("", cellstyle))]
        row += [(round(f, 2), cellstyle) for _, f in pages]
        row += [("", cellstyle)] * (maxpg - len(pages))
        row += [(tot, BLUE), (0.0, cellstyle)]
        ws.append(row)
    grand = round(grand, 2)

    ws.append([])
    ws.append([("TOTAL (excl. full-page ads/promos, per official convention)", None),
               "", (grand, RED_BOLD)])
    ws.append([])
    if ads:
        ws.append([("Full-page ads & promos (excluded above; measured separately)", BOLD)])
        for r in sorted(ads, key=lambda r: _pk(r["printed"])):
            ws.append([f'p{r["printed"]}: {r["supplier"]}', "", round(r["fraction"], 3)])
    ws.append(["House pages/boxes (never billed)", "", round(house_total, 2)])

    ws.set_col_width(0, 52)
    for col in (1, 2, 3):
        ws.set_col_width(col, 14)
    for i in range(maxpg + 2):
        ws.set_col_width(4 + i, 9)

    ws2 = wb.add_sheet("Per-page detail")
    stamp_draft(ws2, note)
    ws2.append([(h, BOLD) for h in
                ["Catalog Page", "Official Supplier Row", "Brand as logo'd",
                 "Fraction", "Billable"]])
    for r in sorted(rows, key=lambda r: (_pk(r["printed"]), -r["fraction"])):
        ws2.append([r["printed"], MAP.get(r["supplier"], r["supplier"]),
                    r["supplier"], round(r["fraction"], 3),
                    "Yes" if r["billable"] else "No"])
    for col, w in ((0, 13), (1, 40), (2, 34), (3, 10), (4, 9)):
        ws2.set_col_width(col, w)

    # Raw measurement geometry, so the CSV never has to ship as a separate file.
    ws3 = wb.add_sheet("Measurements")
    stamp_draft(ws3, note)
    ws3.append([(h, BOLD) for h in
                ["Catalog Page", "PDF Page", "Brand as logo'd", "Billable",
                 "Sq Pts", "% of Content Page", "% of Billable",
                 "Region x0", "Region y0", "Region x1", "Region y1"]])
    for r in sorted(rows, key=lambda r: (_pk(r["printed"]), -r["fraction"])):
        x0, y0, x1, y1 = (float(v) for v in r["rect"].split(";"))
        ws3.append([r["printed"], int(r["page"]), r["supplier"],
                    "Yes" if r["billable"] else "No",
                    float(r["sq_pts"]), float(r["pct_of_content_page"]),
                    float(r["pct_of_billable"]), x0, y0, x1, y1])
    for col, w in ((0, 13), (1, 10), (2, 34), (3, 9), (4, 12),
                   (5, 17), (6, 14), (7, 10), (8, 10), (9, 10), (10, 10)):
        ws3.set_col_width(col, w)

    wb.save(out_path)
    print(f"saved {out_path} | grand total {grand} | "
          f"{len(ads)} ad page(s) excluded | house {house_total:.2f}")


if __name__ == "__main__":
    if len(sys.argv) < 4:
        print(__doc__)
        sys.exit(1)
    ads = set()
    if len(sys.argv) > 4 and sys.argv[4]:
        ads = {int(x) for x in sys.argv[4].split(",")}
    # arg 2 is either an integer offset (contiguous) or a path to a folio-map JSON
    pages_arg, folio_map = 0, None
    raw = sys.argv[2]
    try:
        pages_arg = int(raw)
    except ValueError:
        folio_map = {str(k): v for k, v in json.load(open(raw)).items()}
    note = sys.argv[5] if len(sys.argv) > 5 else ""
    build(sys.argv[1], pages_arg, sys.argv[3], ads, folio_map, note)
