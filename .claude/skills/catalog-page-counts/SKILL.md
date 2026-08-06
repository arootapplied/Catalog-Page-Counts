---
name: catalog-page-counts
description: Measures how much page space each supplier or brand occupies in a product catalog PDF using exact PDF geometry (not OCR or keyword search), and produces a supplier space billing workbook. Use this whenever a catalog PDF is uploaded and the user wants it analyzed, measured, or broken down by supplier - including requests like "how much space does X have in this catalog", "bill by supplier", "co-op advertising space", "page counts", "supplier billing sheet", "which brands are on these pages", or any variant of auditing how many pages or fractions of pages a brand occupies. Trigger even if the user doesn't say "catalog" explicitly - e.g. they just attach a PDF and ask for "page counts" or "space calculations" or "who's on this page". Also useful for pulling verified item numbers, specs, or product lineups off catalog pages for other downstream work. Always self-test and produce audit overlay images before delivering billing numbers - never estimate supplier space from text alone.
---

# Catalog Page Counts — Supplier Space Billing

Catalogs bill suppliers for the physical space their products occupy on the printed page (co-op advertising space, page-count billing). Doing this by eye across a large catalog is slow and error-prone; doing it by searching the text for brand names is actively misleading, because a brand name can appear in comparison copy, footnotes, or a neighboring section without that brand actually owning any billable space there.

This skill measures the real thing: every page in a digitally-produced catalog PDF has an embedded text and image layer with exact coordinates. A supplier's billable region is a geometric area on the page — position and size, not word count — and can be computed precisely, verified visually, and reproduced identically on a rerun. That is the whole method: read coordinates, not keywords.

## Setup

The method needs exactly one thing: **exact PDF coordinate geometry.** There are
two engines that provide it, and the skill is designed so that if the preferred
one can't install, the other still runs — with **no network and no package
install at all**. What is *never* acceptable is producing a number without exact
geometry (a keyword/text estimate of supplier space); that is the one true
hard-stop. Everything else — the Excel workbook included — is standard library.

**Engine A (primary): PyMuPDF (`fitz`) + poppler-utils.** Best when it installs:
exact geometry *and* real rasterized page images, so audit overlays are PNGs of
the actual page. Use it whenever `pip install pymupdf` succeeds.

**Engine B (fallback, dependency-free): poppler's `xpdfimport`.** Ships *inside
LibreOffice*, which is pre-installed in many locked-down environments (including
Claude Code on the web). It parses the same exact glyph/image coordinates from
the same poppler engine behind `pdftoppm` — this is real geometry, not OCR and
not a text guess. It cannot rasterize a page, so its overlays are **SVG**
reconstructed from the exact coordinates, and a human eyeball against the real
PDF is explicitly owed before invoicing. The area math and invariants are
*imported from Engine A's module*, so both engines compute numbers identically —
one source of truth, never two.

Probe what's available before doing anything else:

```bash
python3 -c "import fitz; print('fitz OK')" 2>&1        # Engine A available?
python3 scripts/catalog_page_counts_poppler.py probe   # reports fitz AND xpdfimport
which pdftoppm                                          # PNG rasterizing for Engine A overlays
```

Install for Engine A if the index is reachable:

```bash
pip install pymupdf
apt-get install -y poppler-utils   # or: brew install poppler
```

**Offline install of Engine A (no network needed).** PyMuPDF ships as a self-contained `abi3` wheel (~26 MB) that works on any CPython 3.10+ on Linux x86_64 and needs *no* other packages and *no* internet to install. So in a network-blocked environment, if the user has attached the wheel file to the session (or it's otherwise on disk), install it directly and you get the full primary engine — exact geometry **and** PNG overlays (PyMuPDF renders its own pages via `get_pixmap`; it does **not** need poppler for the skill's overlays):

```bash
# find an attached wheel anywhere on disk, then install it with no index/network:
WHL=$(find / -name 'pymupdf-*.whl' 2>/dev/null | head -1)
pip install --no-index "$WHL"
python3 -c "import fitz; print('Engine A ready offline:', fitz.VersionBind)"
```

This is the best outcome for a locked-down environment: it's the same trustworthy engine used everywhere else, just installed from a file instead of the internet. Prefer it over Engine B whenever the wheel is available.

- **openpyxl is NOT required, ever.** The billing workbook is written by the bundled `scripts/mini_xlsx.py` (standard library only), so the Excel deliverable works in locked-down environments. Never downgrade the workbook to HTML/CSV because "openpyxl won't install" — it isn't needed.
- **poppler-utils (`pdftoppm`)** only matters for Engine A's PNG overlays. Engine B doesn't use it (it renders SVG overlays instead).

**Decision order when `pip install pymupdf` fails** (blocked index, 403, no network):
1. **Look for an attached PyMuPDF wheel and install it offline** (the block above). If it installs, you have the full primary engine — the best result — and can stop here. This is the recommended way to run in a locked-down environment.
2. If there's no wheel, run the `probe`. If `xpdfimport` is found, **use Engine B** — you still get exact geometry and a real `.xlsx` workbook; flag that overlays are SVG and a human visual pass is owed. This is a legitimate run, not a downgrade.
3. If *none* of fitz / an installable wheel / xpdfimport is available, **then** stop: name what failed, quote the actual error, and tell the user plainly how to fix it (attach the PyMuPDF wheel, or have their environment's network policy allow PyPI, or run on Claude Code desktop where installs work). Getting the environment unblocked is the user's call — don't route around it with a text/keyword estimate.

**The one thing never to do:** produce a supplier-space number from text/keyword matching instead of geometry, or ship an HTML/CSV stand-in *as if it were* the workbook deliverable. A wrong-or-unverifiable billing number wearing a plausible disguise is worse than an honest "can't run here." (This skill has been handed to locked-down environments before; the correct response there is Engine B, not a keyword guess and not a hard stop when Engine B was available all along.)

## Workflow

### 1. Ingest & verify
- Open the PDF with the available engine (PyMuPDF if installed, else `catalog_page_counts_poppler.py extract`), report page count and file size back to the user. Report the *PDF's own* page count (`/Count` / what the parser emits), not an upload-banner estimate, which can be wrong.
- Confirm a text layer exists (sample a few pages). Modern product catalogs are digitally produced and have real text layers with exact glyph coordinates — this is more precise than OCR, not a downgrade from it. OCR (e.g. tesseract) is only a fallback for genuinely scanned pages with no text layer.
- Visually read 1-2 sample pages and confirm tables and logos are legible before doing anything else. If the file arrived split into parts (zip volumes, page-range chunks), reassemble first and confirm the printed page numbering is continuous.

### 2. Text index
- Dump the full text layer to a per-page index (grep-able navigation layer): part numbers, supplier names, section headings, and the printed page number recovered from the footer.
- Use this index to navigate a large catalog. Never visually read every page of a long catalog — visually read only the specific pages where a supplier boundary needs verifying.

### 3. Layout measurement
- For each page needing measurement, extract block coordinates. Engine A: `page.get_text("blocks")` for text, `page.get_image_info()` for images. Engine B: `catalog_page_counts_poppler.py extract <pdf> geom.json` gives the same per-page `lines` (text with x0/y0/x1/y1 in points) and `images` (logos, product photos) — same coordinate space, so region specs are built the same way regardless of engine.
- **Logos are often vector art, not raster images — `get_image_info()` will not see them.** On a professionally-produced catalog the supplier logo is typically embedded as filled vector paths, so a page can return *zero* images and still carry two supplier logos. Always also scan `page.get_drawings()` and group the paths by `fill` color: a tight cluster of same-colored paths 50-120 pt wide sitting just above a product block is a logo, and its brand-blue/brand-red fill is a reliable fingerprint for finding that same supplier elsewhere in the run. Do this on **every** page before concluding a page is single-supplier — this is the check that catches a second supplier the text layer never names.

```python
from collections import defaultdict
groups = defaultdict(list)                       # fill color -> [rects]
for dr in page.get_drawings():
    r, f = dr["rect"], dr.get("fill")
    if f in (None, (1.0, 1.0, 1.0)):  continue   # ignore unfilled + white
    if r.y0 < HEADER_H or r.y1 > FOOTER_Y: continue
    groups[tuple(round(c, 3) for c in f)].append(r)
# a logo = several same-fill paths with a combined bbox ~50-120 pt wide
```
- Establish this edition's page dimensions and exclusion zones from the first few sample pages, then hold them constant for the run: header/title banner band, footer band (page number + contact info), and any two-column gutter. Different catalog editions have different page sizes and margins — re-derive these from the actual PDF, never assume a value from a prior job.
- **Let the page's own separator rules set the vertical boundaries.** Designers already draw a thin horizontal rule between sections; those are exactly where one supplier's space ends and the next begins, and they beat a computed midpoint because they're the layout's own intent. Collect them with `page.get_drawings()` filtered to `dr["type"]=="s"` and `rect.width>150 and rect.height<2`. Fall back to the geometric midpoint only where no rule exists (typically against a house-box border).
- **On multi-column pages, write column rects that run full-bleed to the page edges**, not to the text margins — e.g. with a gutter at x=300 on a 603 pt page, use `0→300` and `300→603`. The columns then tile the content band exactly, so incidental margin whitespace is attributed rather than piling up against the 15%-unattributed flag. Find the gutter by histogramming block `x0`/`x1` across the run. A single page can carry a full-width band *and* a two-column tier (a full-width supplier header section on top, two independent column stacks beneath) — build the spec tier by tier instead of assuming one layout governs the whole page.
- House content (in-page cross-sell boxes, "did you know" callouts, chapter dividers, full-page third-party ads) is identified by its heading text or lack of a supplier logo, and is excluded from billing — see Business rules.

### 4. Supplier attribution
- A supplier's region starts at its logo image or brand-name heading and extends to the end of its last table or product block, bounded by the next supplier's logo (within the same column, if the page is multi-column).
- **A section heading naming a product family is not evidence of who owns it.** Headings like "7000 Series Super Precision Angular Contact Bearing" carry no brand token at all, so the *only* thing that identifies the supplier is the logo physically above the block — which is frequently vector art invisible to both text extraction and `get_image_info()` (see step 3). Never conclude "this whole extract is supplier X" from the file name, the first page, or the text layer; confirm per page against the drawings scan and a rendered image.
- **Continuation content** — a section that carries on to the next page or column with a "Continued from previous page" marker and no repeated logo — bills to the *originating* supplier. Follow the heading/marker chain in the text layer rather than requiring a logo on every page; note the chain explicitly in the per-page output so the attribution is traceable.
- **Identical headings under different logos** (two suppliers happen to use the same generic section title) are disambiguated by position — which logo is physically above which table — never by the heading text alone.
- A page with a generic heading, no logo, and no continuation chain back to a logo is genuinely ambiguous: flag it for human review rather than guessing (see Guardrails). Don't let a plausible-looking guess become a silent billing decision.

### 5. Billing computation
- Compute each supplier's region area in square points; report both **% of content page** (the page minus header/footer) and **% of billable space** (supplier regions only, excluding house content). Which one drives the actual invoice is a business decision — see Business rules — not something to assume.
- Output as decimal pages, `1.000` = one full page, three decimal places. A supplier owning an entire page is `1.000`, including any incidental whitespace on that page — space isn't reassigned between suppliers just because one page runs looser than another, unless the business rules say otherwise.

### 6. Output & spot-check
- Deliver a CSV or table: `page, supplier, sq_pts, pct_of_content_page, pct_of_billable, billable, region_coordinates`, plus a per-supplier rollup.
- Visually spot-check a meaningful sample of pages (at minimum every page with a multi-supplier split or an ambiguous call) against the computed regions and report the result of that check. A billing sheet that hasn't been spot-checked is not a finished billing sheet.
- On a large catalog, fan work out by page range across subagents if available — the measurement script is deterministic, so results from different ranges merge cleanly without reconciliation.

## Measurement engine — `scripts/catalog_page_counts.py`

The area math lives in a tested script; use it rather than re-deriving coordinate arithmetic inline in conversation, since that's exactly the kind of thing that's easy to get subtly wrong under time pressure and hard to notice afterward.

```bash
# Self-test (see below for what this checks without a bundled sample file):
python3 scripts/catalog_page_counts.py selftest <sample.pdf>

# Measure pages from a hand-built regions spec -> CSV + rollup + audit overlay PNGs:
python3 scripts/catalog_page_counts.py measure <catalog.pdf> <regions.json> <out.csv> [overlay_dir]
```

`regions.json` format: `[{"page": N, "supplier": "Name", "rect": [x0,y0,x1,y1], "billable": true}, ...]` (1-based page numbers, coordinates in points). Build this by reading each page's text/image block coordinates (step 3-4 above) and writing out the region boundaries — either directly, or with a small helper script for a multi-page job with a repeating layout.

**Invariants the engine enforces automatically:** regions on a page may not overlap, may not extend into the header/footer bands, and any page where more than 15% of the content area is unattributed gets flagged. A run that produces flags is not a finished run — resolve every flag or hand it to the user, never suppress it.

**Self-test, without a bundled fixture:** the script ships with a hardcoded regression fixture (a specific calibration page from the catalog it was originally built against), but that source PDF is proprietary catalog content and is deliberately *not* bundled with this skill (see Guardrails — catalog content stays with its owner, not shipped in a portable package). If that exact file isn't available in the current environment, the self-test can't run in its original form. Validate the engine another way instead before a real billing run:
1. Confirm the current catalog's actual page dimensions with `fitz.open(pdf)[0].rect` and use that as this run's baseline — don't assume a size from a different catalog or a prior job.
2. Build a `regions.json` for one representative page, run `measure`, and confirm the tool reports zero invariant violations.
3. Open the audit overlay for that page and visually confirm every drawn boundary lands in whitespace, not mid-table or mid-logo.

If the original fixture PDF *is* available (e.g. re-running in the same environment where this skill was first built), running the literal `selftest` command is still the fastest check and should be preferred when possible.

**Audit overlays:** Engine A's `measure` renders each page as a PNG with every supplier region boxed and labeled with its computed share, exclusion bands grayed out, and non-billable regions marked. Every delivered billing figure must have its overlay available — this is what lets anyone downstream verify a number in seconds instead of trusting a black box.

## Dependency-free fallback engine — `scripts/catalog_page_counts_poppler.py`

Use this when `pip install pymupdf` fails but the job still has to run (see Setup's decision order). It uses poppler's `xpdfimport` — bundled with LibreOffice, no network required — to extract the *same exact* glyph/image coordinates, and imports the area math + invariants from `catalog_page_counts.py` so the numbers are computed identically.

```bash
python3 scripts/catalog_page_counts_poppler.py probe                       # is fitz / xpdfimport here?
python3 scripts/catalog_page_counts_poppler.py extract <catalog.pdf> geom.json
python3 scripts/catalog_page_counts_poppler.py measure <catalog.pdf> <regions.json> <out.csv> [overlay_dir]
```

- Same `regions.json` input and same CSV output columns as Engine A, so the CSV feeds `catalog_billing_workbook.py` unchanged — the deliverable is still the real `.xlsx`.
- **Overlays are SVG, not PNG.** They reconstruct every real text/image rectangle plus the billed region boxes from exact coordinates, so boundaries are checkable — but they are *not* a picture of the rendered page. Because Engine B cannot rasterize, the mandatory visual spot-check (Guardrails 5 & 8) is only *partially* satisfied: state plainly in the delivery that a human eyeball against the actual PDF is still owed before any number is invoiced.
- Everything else (flags, the 15%-unattributed rule, no-overlap / no-leak invariants) behaves exactly as Engine A because it *is* Engine A's code.

## Excel deliverable — `scripts/catalog_billing_workbook.py`

Turns the measurement CSV into a billing workbook in one command:

```bash
python3 scripts/catalog_billing_workbook.py <measure.csv> <pages> <out.xlsx> [ad_pages] [note]
# contiguous run (offset):   ... measurements.csv 176 billing.xlsx "195,196,197"
# non-contiguous extract:    ... measurements.csv folios.json billing.xlsx
# with provenance stamp:     ... measurements.csv folios.json billing.xlsx "" "PyMuPDF 1.28.0, 0 flags"
```

- `<pages>` — how each measured PDF page maps to the number PRINTED on it:
  - an **integer offset** for a contiguous run (printed = PDF page + offset), or
  - a path to a **folio-map JSON** for a non-contiguous extract: `{"1": 272, "2": 278, ...}`.
  Use the folio map for supplier extracts, which are the *common* case — they pull scattered pages (e.g. 272-306, 380-417, 484), so a single offset mislabels them. Build the map from the printed page numbers recovered from each page's footer during the text-index step. Unmapped pages come out flagged as `~N?` rather than silently wrong.
- `ad_pages`: comma-separated printed page numbers to report separately rather than folding into the main total (full-page third-party ads and promo pages are commonly excluded from the official page-count convention — confirm this with whoever owns the billing convention before assuming it for a new catalog).
- **Supplier registry**: the script's `MAP` dictionary maps logo-level brand names to the billing entity they roll up to (a catalog often shows several house brands under one distributor's or manufacturer's logo). Extend `MAP` as new brand families are identified — this is the piece most worth building up over time, since re-deriving it from scratch on every catalog is wasted effort.
- **Workbook layout**: three sheets — **Page Counts** (supplier, total pages, per-page entries, family subtotals, house/excluded rows, grand total), **Per-page detail** (brand-as-logo'd vs. the official supplier row it rolls up to), and **Measurements** (the raw geometry behind every number: sq pts, both percentage bases, and each region's exact rectangle). The Measurements sheet means the measurement CSV does **not** need to ship as a separate file — one workbook carries the billing numbers and their full audit trail. If the user has an existing house format for this report (column order, family-grouping, a prior-year comparison column), match it exactly rather than defaulting to this script's layout — ask to see an example if one exists and isn't already reflected in `references/supplier-registry.md`.
- **Every sheet is stamped `DRAFT - FOR FINANCE REVIEW - NOT FOR INVOICING`**, with an optional provenance line (engine + version, catalog, page range, flag count). This is unconditional by design — guardrail 3 says this skill never finalizes supplier charges, so there is no switch to turn it off. Pass the `note` argument so the stamp records which engine produced the numbers (guardrail 10).
- **No openpyxl needed**: this script writes the `.xlsx` via the bundled `scripts/mini_xlsx.py` (standard library only). That is deliberate — the Excel file is the actual deliverable, so it must not depend on a package that a locked-down environment might refuse to install. Never downgrade the deliverable to HTML or CSV-only because "openpyxl isn't available"; it isn't needed. (Overlay PNGs ship alongside the .xlsx as the visual audit trail; the measurement CSV is an intermediate the workbook already absorbs as its Measurements sheet, so there's no need to hand it over as a separate file unless the user asks.)

## Business rules

These are the assumptions the math runs on. Get explicit confirmation before assuming any of these for a *new* catalog or customer — what's below reflects one calibration history, not a universal standard:

| Rule | Default assumption |
|------|----------------|
| Output unit | Decimal pages, `1.000` = one full page, 3 decimals |
| Billing basis | Full-width horizontal bands of the content page (header/footer excluded); a supplier owning a whole page = `1.000` including incidental whitespace |
| House content (cross-sell boxes, index pages, covers, dividers) | Excluded, not billed, not redistributed to neighboring suppliers |
| Whitespace between supplier sections | Split at the geometric midpoint between the two regions |
| Continuation pages/sections (no logo, but a text marker chains back to one) | Bill to the originating supplier; note the chain explicitly in the per-page output |
| Page with no logo and no continuation chain | Flag for human review — never guess |
| Multi-supplier tables (one table, mixed listings) | Flag for human review |
| Full-page supplier ads / promo pages | Commonly excluded from the official count, but this varies by customer — confirm rather than assume |
| Area vs. slot convention | This engine measures exact area. Some human-run billing processes instead count equal slots (a 6-section page = 1/6 each regardless of each section's actual size) — the two conventions can diverge on lopsided layouts. Ask which convention applies before reporting a number as final. |

Record any new rule discovered during a real job (see Calibration procedure) in `references/supplier-registry.md` alongside the family mapping, so the next run inherits it.

## Supplier registry & calibration history

See **`references/supplier-registry.md`** for the brand-to-billing-entity mapping accumulated so far (which logos roll up to which invoiced entity) and **`references/calibration-history.md`** for the specific catalogs this method has been checked against and what was learned from each. Read both before a new run on a catalog family that might already be represented there — reusing a known family mapping is faster and more reliable than re-deriving it from the page.

## Calibration against a human-produced answer key

When a prior edition of the catalog plus its human-produced page counts are available, calibrate before trusting the engine's output on a live billing run:

1. Run the engine on the prior edition and diff against the human numbers, supplier by supplier (page by page if the human output has that detail).
2. For every mismatch, open the actual page and work out which rule the humans were actually applying — don't assume the engine is right just because it's more precise. Record newly-discovered rules in the Business rules section and `references/supplier-registry.md`, annotated with where they came from.
3. Some mismatches will turn out to be human inconsistency or outright error, not a rule to encode. Flag these to the user rather than bending the engine's logic to match an inconsistent answer key — the user decides which behavior is actually correct.
4. Iterate until the two agree within the user's tolerance, then record the match rate and what was learned in `references/calibration-history.md`.
5. Build the supplier registry for this catalog (canonical names, brand aliases, which logos belong to which billing entity) from the catalog's own brand index plus the answer key's supplier list — attribution should become a lookup, not a fresh judgment call each time.

## Guardrails

1. **No invented numbers.** Every item number, spec, or measurement in any output must trace back to something actually in the PDF. If a value is unreadable, say so — never infer or round it.
2. **Ambiguity goes to a human.** A page where supplier attribution is genuinely unclear gets flagged and listed, not silently assigned to whichever supplier seems most likely.
3. **Billing output is a draft.** Every billing sheet produced is a draft for the accounting or finance team's review before it's used to invoice anyone. This skill does not finalize supplier charges.
4. **Re-verify a new edition.** Page dimensions, header/footer bands, and column layout can all change between catalog editions or between different catalogs entirely. Re-derive them from the actual file at hand; never reuse a prior job's geometry blind.
5. **Spot-check is mandatory.** No billing sheet ships without the visual sample check from workflow step 6.
6. **Catalog content stays with its owner.** Don't push catalog PDFs, extracted product images, or proprietary catalog content into a shared or externally-facing location, and don't bundle real catalog pages into a portable copy of this skill (that's why this skill's own self-test fixture is described rather than bundled — see the measurement engine section above).
7. **Self-test before every run.** Verify the engine hasn't drifted before trusting its output on a real job — see the self-test guidance under the measurement engine section for how to do this without the original fixture file.
8. **No billed number without an overlay.** Every figure in a delivered billing sheet must have its audit overlay image available, and every flag the engine raises must be resolved or handed to the user — never quietly dropped.
9. **Geometry or nothing — but try both engines first.** The only acceptable basis for a supplier-space number is exact PDF coordinate geometry. When PyMuPDF won't install, fall through to the dependency-free poppler engine (`catalog_page_counts_poppler.py`, Engine B) — that is still exact geometry and still produces the real `.xlsx`. Only if *neither* engine is available do you stop: say so directly, quote the actual error, and hand it back. What you must never do at any point is substitute a keyword/text guess at supplier space, or ship an HTML/CSV/text summary *as though it were* the workbook deliverable. A missing tool with a working fallback is a run, not a stop; a missing tool with no fallback is an honest stop; a plausible-looking wrong number is neither.
10. **Name the engine and what's owed.** Every delivery states which engine produced it. An Engine B (poppler) run must say, in plain words, that overlays are SVG reconstructions and a human visual check against the real PDF is still owed before invoicing — don't let a fallback run read as if it were fully spot-checked.
