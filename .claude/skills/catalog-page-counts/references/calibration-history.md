# Calibration history

A record of what this method has been checked against, and what each check
found. Useful context before starting a new job: if the new catalog resembles
one of these (same publisher, same layout conventions, overlapping brands),
the lessons below likely still apply.

## Origin

Built and first validated against a single catalog page (a two-brand safety
products page: one supplier's stock/custom product line on the left column,
another's emergency-shower line on the right, plus a small in-page house
cross-sell box). That page established the core method: measure exact block
coordinates for logos and product tables, compute region area, exclude
header/footer/house content, report as decimal pages.

## Hardening

The measurement engine was promoted from an ad-hoc session script into a
tested tool with:
- A self-test regression fixture (the origin page above), to catch drift.
- Geometric invariants enforced automatically: no overlapping regions, no
  leakage into header/footer bands, and an automatic flag if more than 15%
  of a page's content area goes unattributed.
- Audit overlay images: every measured page gets rendered with its regions
  boxed and labeled, so any number can be checked against the actual page in
  seconds rather than trusted blind.

This is also where the "don't bundle real catalog content" rule came from —
the origin page is proprietary catalog material and was deliberately kept
out of any portable copy of this skill, which is why the self-test can't run
in its literal form in a fresh environment (see the SKILL.md guardrails for
the workaround).

## Multi-page, multi-supplier calibration

Tested against a 7-8 page bearings-chapter extract with several real-world
complications in one place: continuation sections that carry no logo on the
following page (attributed correctly by following the "continued from
previous page" text marker back to its origin); a three-way page split
between two supplier logos and a house cross-sell box; and both odd/even
page templates a catalog can alternate between. All boundaries verified
clean by overlay; the continuation-attribution rule was confirmed here.

## Blind test against a real answer key

Run against a ~21-page single-supplier extract with a company-internal
"official" page count already computed independently. The engine's total for
that supplier matched the official number exactly. This was a genuine blind
test — the official number wasn't seen until after the engine's number was
already produced — and it substantially raised confidence that the geometric
method reproduces what a careful human count actually intends.

## Full-chapter calibration against a human answer key

Run against a full ~24-page catalog chapter (many suppliers, several
multi-brand pages, a chapter table-of-contents page, a chapter-closer page,
and several full-page third-party ads) against that chapter's official,
human-produced page-count spreadsheet. Result: the large majority of
supplier rows matched within a small tolerance; the chapter-level totals
matched closely once counting conventions were aligned. This run is where
several rules were derived (not assumed) directly from the mismatch pattern:
- Full-page ads and promo pages were absent from the official sheet — i.e.
  excluded from the official count, though still worth measuring and
  reporting separately so nothing silently disappears from view.
- The brand-family rollups now in `supplier-registry.md` came from this
  answer key's own supplier grouping.
- A few individual rows in the official sheet looked internally inconsistent
  on inspection (e.g. one supplier's total not matching the sum of its own
  listed page entries) — these were flagged back to the person who owned
  that answer key rather than silently matched, since an answer key can
  contain human error same as any manual process can.
- The "exact area vs. equal-slot counting" question was surfaced here: this
  engine measures true area, but some human counting historically treats a
  page divided into N roughly-equal sections as exactly 1/N each. The two
  conventions can diverge meaningfully on a lopsided page. Confirm which
  convention a customer actually wants before treating a number as final.

## Repeat-brand consistency check

Two different supplier extracts from the same catalog edition happened to
share one physical page (each extract included that shared page because it
featured both suppliers). Measuring that page independently, from each
extract, produced identical fractional splits both times. This is a useful
sanity check to keep in mind: if a job ever produces two different extracts
that overlap on a page, the two measurements should agree, and if they don't,
that's a sign of a real error worth chasing down rather than dismissing as
noise.

## Family-rollup pattern across bearing-industry catalogs

Several bearing-industry supplier extracts (spanning brands that turned out
to belong to two parent companies) surfaced the same pattern repeatedly:
manufacturer parent companies often show up as multiple, visually distinct
logos with no on-page indication they're related. This is the origin of the
Schaeffler and Regal Rexnord family entries in `supplier-registry.md` — worth
checking explicitly on any new bearings, power-transmission, or linear-motion
catalog, since the rollup can change a billed total substantially.

## Cross-edition stability check

The same supplier's section, pulled from two different catalog editions
(same publisher, different edition/printing), produced closely matching
fractional splits for the shared secondary suppliers on its pages — evidence
that the method is stable across editions rather than fitted to one specific
printing.

## Single-supplier extract in a blocked (no-PyMuPDF) environment — Engine B origin

Run against a 36-page Dodge (Regal Rexnord) chapter extract of the Applied
Industrial Technologies master catalog (printed pp. 272–306 Bearings, 380–417 +
484 Power Transmission), 603×783 pt. Two lessons, both now baked into the skill:

1. **PyMuPDF could not be installed** — the environment (Claude Code on the web)
   blocked the package index (`pip` 403). Rather than hard-stop or fake an
   answer, exact geometry was pulled from poppler's `xpdfimport` (bundled with
   the pre-installed LibreOffice). This became the dependency-free **Engine B**
   (`scripts/catalog_page_counts_poppler.py`), which reuses Engine A's area math
   so the numbers are identical; only the overlays differ (SVG, not PNG), so a
   human eyeball against the real PDF is explicitly owed. Verified end-to-end:
   extract → measure → CSV → real `.xlsx` workbook, all with zero third-party
   packages.
2. **The keyword trap, live.** A whole-text scan "found" the brand token "INA"
   34× — every hit a false positive inside words like *combination*. Attribution
   was done from page geometry (logos/product tables), not text search. Result:
   Dodge 33.8 pages billable, Applied ~2.2 pages house/promo (never billed),
   summing to 36.000.

Layout patterns worth reusing on Applied-published catalogs:
- Every product page carried Dodge; there were **no pure-publisher pages**.
  Applied appeared only as **full-width promo strips on the top band** of 11
  pages (Register / The Storeroom / DVA / "All Things Industrial"), split off at
  the geometric midpoint between the promo and the first product row.
- One page (a "Did you know… Applied operates on six continents" blurb) was a
  narrow column **woven beside** Dodge OPTIFY content, not a clean horizontal
  band — correctly caught by the no-overlap invariant and flagged for human
  review rather than force-split.
- The extract's printed folios are **non-contiguous** (pulled Dodge pages only),
  and left-hand pages carry no folio in the text layer. Note this when using
  `catalog_billing_workbook.py`: its single `printed_page_offset` assumes
  contiguous pages, so for a sparse extract cite trace-page numbers (or a
  per-page folio map) rather than a fixed offset.

## Vector-logo discovery — the hidden second supplier (NTN extract)

Run against a 6-page NTN Bearing Corp. extract of the Applied master catalog
(printed pp. 233-238, 603x783 pt), Engine A via an **offline wheel install** of
PyMuPDF 1.28.0 in a network-blocked environment — the decision-order step 1 path
in SKILL.md, verified working end to end. Result: NTN 5.300 pages, NSK 0.502,
Applied house 0.197, summing to exactly 6.000 with zero invariant flags.

The lesson that changed the skill:

- **A supplier logo is usually vector art, and `get_image_info()` cannot see
  it.** Page 238's lower half belongs to **NSK**, not NTN. Nothing in the text
  layer says so: the heading is "7000 Series Super Precision Angular Contact
  Bearing" (no brand token), and the page reports only two raster images
  (a product photo and a lightbulb icon), neither of them a logo. The NSK logo
  is three filled red vector paths. It was found by grouping `get_drawings()`
  by fill color — now a required step in workflow step 3. Had the extract been
  billed on its file name and text layer, NTN would have been overcharged by
  ~0.5 page and NSK billed nothing.
- **The keyword trap, again.** Searching the same extract for `INA` returned
  two hits, both inside the word "combinations". A text-based count would have
  handed Schaeffler half a page it does not own on a page where Schaeffler
  has no presence at all.
- Pages 235 and 237 carry no logo but chain back via "Continued from previous
  page" inside the same product family — the continuation rule applied cleanly,
  and the overlays confirmed the boundaries.
- The publisher's running banner (APPLIED logo, y 18-45) sits inside the
  excluded header band, so it needed no special handling — but note it is a
  *banner*, not the promo-strip pattern seen on the Dodge extract, which does
  eat billable content space. Same publisher, two different house-content
  shapes; check which one a given page has.
- `selftest` reports PASSED against any 603x783 pt PDF: it asserts page size,
  then computes from hardcoded rects without ever reading page content. It is a
  genuine check that the *area arithmetic* has not drifted, but it is **not**
  the fixture regression unless the original Accuform page is the file you hand
  it. Say which of the two you actually ran when reporting.

## Dense multi-supplier, multi-column chapter (PIP extract)

Run against a 7-page PIP extract of the Applied master catalog, Safety Products
chapter (printed pp. 42, 43, 45, 46, 47, 48, 49 — 603x783 pt), Engine A. Eight
distinct suppliers plus two house boxes across seven pages; 20 regions, zero
invariant flags, all regions summing to exactly 7.000. Result: PIP 3.920
(4.100 with Bouton Optical), MCR Safety 1.038, Master Lock 0.502, Sqwincher
0.408, KleenGuard/Jackson 0.342, MSA 0.328, Bouton Optical 0.181, Applied house
0.281 (not billed).

This is the densest layout the method has been run against, and it added three
techniques worth reusing:

- **The upload banner lied about page count.** The session banner announced
  "19 pages"; the PDF's own `/Count` was **7**. SKILL.md already says to trust
  the parser over the banner — this is the live confirmation. Never seed a
  folio map or a page loop from the banner number.
- **Folios can be non-contiguous inside a short run.** The extract's printed
  pages are 42, 43, **45**, 46, 47, 48, 49 — p.44 is absent. A 7-page extract
  looks contiguous enough to tempt an integer offset, which would have
  mislabelled five of the seven pages. Always recover folios from the footers
  and pass a JSON map.
- **Multi-column pages need column rects, and the page's own separator rules
  are the boundaries.** Left column x0≈36 with x1≈290, right column x0≈305 —
  gutter at **x=300**. Regions were written full-bleed to the page edges
  (left `0→300`, right `300→603`) rather than to the text margins, so the two
  columns tile the content band exactly and nothing lands in the >15%
  unattributed flag. Vertically, the thin horizontal stroked rules the designer
  already draws between sections (`type=="s"`, width>150, height<2) are better
  boundary anchors than a computed midpoint — they are where the layout itself
  says one supplier stops and the next begins. Use a midpoint only where no
  rule exists (e.g. against a house box border).
- Pages mix full-width bands and two-column tiers on the *same* page (printed
  p.42: one full-width MCR band on top, then a two-column tier where the left
  column is PIP throughout and the right column splits MCR over PIP). Build the
  spec tier by tier rather than assuming one layout for the whole page.

## Seven-supplier motor chapter (ABB / Baldor-Reliance extract)

Run against a 15-page ABB/Baldor-Reliance extract of the Applied master catalog
(printed pp. 346-361 and 369 from Power Transmission, **plus one page from a
different chapter** — printed p.20, Hand, Power & Analytical Tools), 603x783 pt,
Engine A via offline wheel install of PyMuPDF 1.28.0. Seven billable suppliers
plus one house box across 15 pages; 34 regions, zero invariant flags, every page
tiling to exactly 1.000 and the run summing to exactly 15.000. Result: ABB
(Baldor-Reliance) 11.074, LEESON 1.327 (Regal Rexnord family), WEG 1.114, JET
0.353, RIDGID 0.299, Lovejoy 0.284, Bison Gear 0.253, Applied house 0.297.

What this run added:

- **The upload banner lied again, in the other direction.** The session banner
  announced "20 pages"; the PDF's own `/Count` was **15**. The PIP run saw the
  banner overstate by 12; this one overstated by 5. Treat the banner as noise
  every time.
- **An extract can silently contain a page from a different chapter.** Printed
  p.20 sits in the Hand, Power & Analytical Tools chapter (its running banner
  says so) while every other page is Power Transmission. It is also the densest
  page in the run — three suppliers (RIDGID full-width, JET in the left column,
  Baldor-Reliance in the right). Nothing in the file name or the folio sequence
  hints at it; only reading the running banner per page catches it. Worth
  flagging to the billing owner rather than silently folding into the chapter
  total.
- **Two of the seven suppliers were vector-only logos** (WEG, Lovejoy),
  reconfirming that the drawings scan is not optional. A raster-only pass would
  have handed WEG's 1.114 pages and Lovejoy's 0.284 to whichever neighbour owned
  the rest of the page.
- **Continuation chains ran three deep and crossed a logo-less page boundary
  twice** (printed 347→348, 356→357, 360→361). Each following page carries
  "Continued from previous page." with no logo; all three attributed cleanly to
  Baldor-Reliance by the continuation rule. Note that p.361's own "Continued on
  next page." points at printed p.362, which is *not in the extract* — a dangling
  chain end is normal for a supplier extract and is not an error.
- **The NEMA Premium / IP55 / IP69 badges are certification marks, not logos.**
  A ~57x24 pt raster at x≈505-511 recurs on eight pages and looks exactly like a
  logo to a size-based filter. Filter it out by position and by the fact that it
  never sits above a product block.
- Separator rules did nearly all the vertical boundary work (13 of 15 pages had
  usable rules); the geometric midpoint was needed exactly once, on printed
  p.355, between the last Baldor-Reliance table note (y=513.77) and the Applied
  Technical Training box border (y=567.50).

## Ten-brand hand-tool chapter with drawn column rules (Apex/Crescent extract)

Run against a 5-page Apex/Crescent extract of the Applied master catalog, Hand,
Power & Analytical Tools chapter (printed pp. 6, 7, 8, 10, 11 — p.9 absent),
603x783 pt, Engine A. Ten billable brands plus one house box across five pages;
25 regions, zero invariant flags, every page tiling to 1.000 and the run summing
to exactly 5.000. Result: RIDGID 1.473, Crescent family 1.802 (Crescent 1.092 +
Lufkin 0.334 + Wiss 0.278 + Nicholson 0.098), Precision Brand 0.530, GEARWRENCH
0.412, Empire 0.366, Anchor Brand 0.121, Milwaukee 0.118, Applied house 0.177.

This is the highest brand-density run so far — ten brands on five pages — and it
added three things:

- **This chapter draws explicit vertical column-divider rules.** Every
  multi-column page carries a real stroked vertical line (`height>80`,
  `width<2.5`) at the column boundary: x=214.00, 389.00, 393.37, 213.87, 209.63
  on the five pages. That is strictly better than the histogram-derived gutter
  the earlier runs used — it is the layout stating its own boundary. Collect
  vertical rules alongside the horizontal ones before falling back to a
  histogram. Note the divider x differs page to page (209.63 to 393.37), so it
  cannot be treated as an edition constant.
- **A recorded fill color is not an identity.** Milwaukee's logo here is vector
  art filled `(0.890, 0.096, 0.214)` — byte-identical to the fill this registry
  had already recorded for **MCR Safety** from the PIP safety chapter. Had the
  fill fingerprint been trusted as a lookup, the run would have billed a safety
  brand for a tape measure. Fills are a fast way to *find* candidate logos;
  identity still requires rendering the page. The registry now says so
  explicitly.
- **A whole multi-section region can be one supplier.** Printed p.7 is a
  three-column grid whose entire left region (two columns, six separate RIDGID
  sections with their own internal rules) is RIDGID top to bottom, with only the
  right column splitting RIDGID over Crescent Wiss. Writing the left region as a
  single region rather than six is both simpler and identical in area — check
  whether adjacent sections share a supplier before subdividing.
- The banner overstated again: it announced "16 pages" against a real `/Count`
  of **5**. Three for three across the last three runs.
- **A file name is not on-page evidence.** The extract arrived as
  "Apex_Hand_Tool_Crescent" and both Crescent and GEARWRENCH are Apex Tool Group
  brands, but no Apex logo or wording appears anywhere in it. GEARWRENCH was
  left standalone and the Apex roll-up question handed to the billing owner
  rather than silently applied — it would move 0.412 pages.

## Sibling extract, two shared pages — cross-extract agreement (GearWrench)

Run against a 5-page Apex/GearWrench extract of the same chapter (printed pp. 3,
4, 5, 6, 10), Engine A. 18 regions, zero flags, sums to exactly 5.000.
Result: GEARWRENCH 2.528, Wright Tool 0.795, Empire 0.366, Crescent family 0.669
(Crescent 0.347 + Lufkin 0.224 + Nicholson 0.098), Precision Brand 0.185, Anchor
Brand 0.121, RIDGID 0.069, Applied house 0.267.

- **The repeat-brand consistency check fired for real, and passed.** Printed
  pp. 6 and 10 are the *same physical pages* as this chapter's Crescent extract
  (PDF p1 and p4 there). Their region specs were rebuilt independently from this
  file's own recovered geometry — the rules matched to the hundredth of a point —
  and every one of the eleven shared regions produced a byte-identical
  `pct_of_content_page`. Worth doing deliberately whenever two extracts overlap:
  it is a free end-to-end check that the geometry recovery is deterministic.
  A quick way to spot the overlap before measuring: identical
  `(text length, image count, drawing count)` triples across the two files.
- **A fill-only logo scan lost a supplier worth 0.795 pages.** See the
  clustering warning now in `supplier-registry.md`. Wright Tool's navy vector
  wordmark shares its fill with other art on printed p.3, so grouping
  `get_drawings()` by fill alone produced a page-spanning bbox that the size
  filter discarded — the page looked like it had one supplier (GEARWRENCH, whose
  logo sits at the *bottom*) when in fact Wright owned the top two of three
  bands. Fixed by clustering spatially inside each fill group; a reusable
  implementation is in the run's `logo_scan.py`. Excluding black fills as
  "probably text" was the second half of the same mistake.
- **Whole-page single-supplier pages still need the scan.** Printed p.4 is
  100.0% GEARWRENCH across a full-width band plus a three-column tier — the one
  page in three runs that is genuinely one region. That was established by
  scanning it, not by assuming it from the extract's name.
- Banner overstated a fourth time: "15 pages" against a real `/Count` of **5**.
- A sixth Applied house-content shape: a bordered **"Safety is a Big Deal!"**
  chapter cross-sell box with a lightbulb icon, bottom of a column
  (printed p.5, 0.0895 of the page). No `applied.com` URL at all — it points at
  another *chapter* rather than the website, so a URL-based house-content test
  would miss it. Identify it by the bordered box + no supplier logo.

## Single page, two brands sharing an "Apex" name (Apex-fastener/Milwaukee)

Run against a 1-page extract of the same Hand, Power & Analytical Tools
chapter (printed p.16), Engine A. 4 regions, zero flags, sums to exactly
1.000. Result: APEX (Assembly & Fabrication Tools) 0.610, Milwaukee 0.238,
Applied house 0.153.

The one thing this run exists to flag:

- **The job handed two genuinely different companies both named "Apex" in the
  same batch of extracts.** This page's own logo reads "APEX / ASSEMBLY &
  FABRICATION TOOLS" (bit holders, hex bits) — unrelated to **Apex Tool
  Group**, the parent of GEARWRENCH and Crescent measured in the two prior
  extracts of this same job. The uploaded file names made this worse, not
  better: "Apex_Power_Tool_Apex_Industrial_Fastener" reads like it could be
  Apex Tool Group again. It is not. The registry now names this brand
  `APEX (Assembly & Fabrication Tools)` in full every time specifically so it
  can never collide with an "Apex Tool Group" rollup row if the billing owner
  later asks for one. When a job spans multiple extracts, re-derive each
  brand's identity from its own logo — a shared filename token across extracts
  is exactly the kind of thing that causes a false merge.
- Milwaukee reconfirmed independently here (raster+vector on the earlier hand
  tool runs, raster wordmark here) — three-for-three on being a real,
  independent brand rather than a fixture of one extract.
- The "Register With Us and Save Time!" house block (registry shape (c))
  recurred in a new geometry: a full-width band at the bottom of the page
  rather than the half-column panel seen on the PIP extract. Matched by
  heading text, not layout — a reminder that a house shape's *identity* is its
  wording and lack of a supplier logo, not any specific rectangle.
- Single-page extracts are still worth the full pipeline: this one page still
  needed the fill+cluster logo scan, a midpoint split (no rule separates
  Milwaukee from the house box), and a full overlay review before the numbers
  were trustworthy.

## Cleco/Ingersoll Rand air-tool chapter — Apex Tool Group rollup withheld

Run against a 3-page Apex(-power-tool)/Cleco extract of the same Hand, Power &
Analytical Tools chapter (printed pp. 28, 29, 31 — p.30 absent), Engine A.
15 regions, zero flags, sums to exactly 3.000 with no house content at all.
Result: Ingersoll Rand 1.502, Cleco 0.935, Fluke 0.218, Osborn 0.207,
Cleco (Dotco) 0.138.

- **Cleco is the clearest case yet of outside knowledge vs. on-page evidence.**
  Cleco is genuinely, factually an Apex Tool Group brand — this is common
  knowledge, unlike the APEX-Assembly-&-Fabrication-Tools mixup two extracts
  ago, which really is unrelated. But the rule this skill runs on is the same
  either way: **no Apex logo or wording appears anywhere in this extract**, so
  no rollup was applied. Being confident an outside fact is *true* is not the
  same as it being *on the page*, and the billing convention this method
  serves bills off what a page states, not off a Wikipedia-level fact about
  who owns whom. Handed to the billing owner as an open question rather than
  applied unilaterally.
- **A fill value can shift with its background and still be the same logo.**
  Cleco's orange reads as `(0.957, 0.475, 0.127)` on white product pages but
  `(1.0, 0.347, 0.0)` on the colored "Tame the Line" banner — a visibly
  different RGB triple for the same brand mark. A fill-match search is still
  useful for finding candidates fast, but two different fills belonging to one
  brand is exactly the same lesson as one fill belonging to two brands
  (Milwaukee/MCR Safety, four extracts ago) — confirm by rendering either way.
- **A bordered intro banner can flow straight into its own product section
  with no rule between them.** Printed p.31's "Cleco | Tame the Line" banner
  and the 12LF Series Right Angle Grinder section that follows it share no
  separator — both are Cleco, so they were written as one region bounded by
  the next real rule, per the "adjacent same-supplier sections merge" pattern
  from the Crescent extract.
- **Fluke sits at the bottom of an otherwise all-Cleco page.** Nothing about
  the page's first four sections predicts it; only scanning to the very
  bottom of p.31 caught it. A habit worth repeating on every page regardless
  of how uniform the top looks.
