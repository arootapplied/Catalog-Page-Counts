# Supplier registry

Brand-to-billing-entity mapping, built up across real jobs. Measure at the
logo level (whatever brand name is actually printed on the page) and roll up
to the billing entity at report time — this keeps the underlying measurement
honest (it reflects what's literally on the page) while still producing the
number the invoice actually needs.

This file is meant to grow. When a new catalog surfaces a brand not listed
here, add it — either as its own standalone entity or under an existing
family — and note where the mapping came from (a customer's answer key, a
company's own "brands we own" page, etc.) so a future reader can judge how
solid the mapping is.

## Families identified so far

**Essendant** (distributor house-brand family): Boardwalk, Clorox (incl.
Pine-Sol, Formula 409), Dart, Kimberly-Clark (Kleenex / Scott / WypAll),
Krystal, P&G Professional (Mr. Clean, Comet, Dawn, Joy, Ivory, Magic Eraser),
Reckitt Benckiser (LYSOL), Rubbermaid, Simple Green.
— derived from a customer's own answer key for a janitorial-products catalog
chapter; treat as reliable for that customer, re-verify for a different one.

**Rust-Oleum**: Rust-Oleum, Concrobium, Krud Kutter, Mean Green, Roto-Rooter.

**SC Johnson**: SC Johnson Professional (also appears as Kresto, Stokoderm,
AgroBac, InstantFOAM sub-brands), Drano, fantastik, OFF!, Raid, Scrubbing
Bubbles, Windex, Ziploc.

**Sherwin Williams**: Sprayon. (Not a CRC Industries brand, despite frequently
appearing on the same pages as CRC products — a text search for "Sprayon"
near "CRC" would wrongly suggest a relationship; they're independent
companies that happen to share catalog real estate.)

**Henkel**: Loctite.

**ITW Performance Polymers**: Permatex.

**Schaeffler** (bearing manufacturer parent company): FAG, INA. These three
names can appear as separate logos on the same or adjacent pages without any
other visual cue that they're the same company — worth checking explicitly
whenever a bearings catalog is involved, since this rollup materially changes
the billed total for whichever entity name appears on the actual invoice.

**Regal Rexnord** (industrial power transmission parent company): Rexnord,
Dodge, McGill, Thomson (Thomson Industries — linear motion products), LEESON.
Same caveat as Schaeffler above: these show up as visually distinct logos.
Confirmed on a real Dodge-only extract (2026-07, see calibration-history): a
Dodge chapter extract's product lines were all Dodge (P2B/P4B/F4B pillow &
flange blocks, ER/SC/RAO/SFT/RCJ/EPB/ISAF bearing units, TA taper bushings,
S-2000, Quantis 26Q gear reducers) — no sibling Regal Rexnord logo appeared, so
for that extract Dodge == Regal Rexnord for billing.

## Publishers / distributors (house content, NOT a billable supplier)

Some catalogs are published by a distributor whose own name appears throughout
as promos, cross-sell boxes, and running banners. That content is **house
content — excluded, never billed to a product supplier**, even though the
distributor's name is the most frequent "brand" on the page. Do not mistake the
publisher for a supplier taking space.

- **Applied Industrial Technologies** (`Applied.com`, "All Things Industrial",
  "The Storeroom", DVA / Documented Value-Added, "Register With Us"): publisher
  of the Applied master catalog. On a Dodge extract of it, Applied content was
  ~6% of pages as top-of-page promo strips on 11 of 36 pages — measured and
  reported separately as house, not billed to Dodge.
  Applied house content has now appeared in **five different shapes** across
  jobs, so do not pattern-match on just one: (a) top-of-page promo strips
  (Dodge extract), (b) a bordered "Did You Know…" box at the foot of a page
  (NTN extract), (c) a full "Register With Us and Save Time!" panel occupying
  the lower half of a column (PIP extract, printed p.43), (d) an unheaded
  "Protecting your people and facility…" paragraph box with a *Learn more here!*
  link (PIP extract, printed p.49), and (e) a large bordered **"Technical
  Training" / MaintenancePRO** panel filling the bottom ~30% of a page, with a
  `Applied.com/training` call-to-action and a MaintenancePRO logo in navy vector
  art, fill `(0.118, 0.098, 0.415)` (ABB extract, printed p.355). Shape (e) is
  the largest single house block seen so far and is the only one that carries
  its own sub-brand logo — do not mistake MaintenancePRO for a supplier.
  Shape (e) has now been seen on two unrelated extracts (ABB motors printed
  p.355; Apex/Crescent hand tools printed p.6) at different sizes — 0.297 and
  0.177 of a page — so treat it as a recurring fixture of this catalog rather
  than a one-off, and measure its box border each time instead of reusing a
  prior run's rectangle. A sixth shape (f) is a bordered **"Safety is a Big
  Deal!"** *chapter* cross-sell box with a lightbulb icon (Apex/GearWrench
  extract, printed p.5) — note it carries **no applied.com URL at all**, since
  it points at another chapter of the catalog rather than the website, so a
  URL-based house-content test will miss it. Identify it by the bordered box
  plus the absence of any supplier logo. Shape (c) ("Register With Us and Save
  Time!") also recurs as a **full-width bottom band** rather than the
  half-column panel first seen on the PIP extract — same headline and
  applied.com/register link, different geometry (Apex-fastener/Milwaukee
  extract, printed p.16, 0.153 of the page). Match shape (c) by its heading
  text, not by its layout.
  Shape (d) has no promo-style heading at all
  and reads like body copy — identify it by the applied.com call-to-action and
  the absence of any supplier logo. The black running banner carrying the
  APPLIED logo at y 18-45 is the *header band*, already excluded by geometry,
  and is a different thing from all of these.

**PIP — Protective Industrial Products** (safety/PPE): PIP, Bouton Optical.
Bouton Optical is PIP's eyewear brand and appears as its own visually distinct
script logo, frequently on the same page as a PIP-logo'd section — the same
"two logos, one billing entity" pattern as Schaeffler and Regal Rexnord.
Grouped in `MAP` so the family subtotal and the per-brand rows are both
visible; confirm the rollup with the billing owner before invoicing, since it
was derived from brand knowledge rather than a customer answer key.
— Applied master catalog Safety Products chapter, printed pp. 42-49 (2026-07).

**Ashcroft / Weksler**: Weksler Instruments is an Ashcroft Inc. brand
(pressure gauges and instrumentation). They commonly share a single catalog
page (e.g. one supplier's product fills the top two-thirds, the other's
fills the bottom third) — when measuring one of these two brands' pages,
check the same page for the other's logo before assuming full-page
attribution.

**ABB (Baldor-Reliance)** — motors and drives. The logo printed on the page is
a single combined lockup reading `ABB BALDOR·RELIANCE`, so the rollup is
asserted by the artwork itself rather than inferred: measure it as one entity.
Raster wordmark ~103x27 pt, ABB red + black. Baldor and Reliance Electric do
**not** appear as separate logos anywhere in the extract checked.
— Applied master catalog Power Transmission chapter, printed pp. 346-361, 369
plus one Hand/Power Tools page (p.20), 2026-08.

**WEG** (WEG S.A., Brazil — general purpose, ODP and washdown motors). Its own
parent; independent of ABB despite sharing pages with Baldor-Reliance twice in
the same extract. Logo is **vector** art in corporate blue, fill
`(0.0, 0.364, 0.642)`, bbox ~46x32 pt — invisible to `get_image_info()`, found
only by the drawings scan. Same run.

**Bison Gear** (Bison Gear & Engineering — SANIMotor washdown gearmotors).
Raster wordmark ~96x19 pt. Standalone. Same run.

**Lovejoy** (RunRight self-tensioning motor bases). Logo is vector art in
orange, fill `(1.0, 0.514, 0.0)`, bbox ~63x16 pt. Left standalone deliberately:
Lovejoy is widely understood to have been acquired by Timken, but no Timken
logo or wording appears anywhere on the page, and the registry's rule is not to
guess a parent. Ask the billing owner before rolling this into any Timken row.
Same run.

**RIDGID** and **JET** — both appear on the Hand/Power Tools page (printed
p.20) alongside Baldor-Reliance. Left standalone for the same reason as
Lovejoy: RIDGID is commonly associated with Emerson and JET with JPW
Industries, but neither parent is named or logo'd on the page. Confirm before
rolling up. Same run.

**Crescent** (hand tools) — measured as a family. **Wiss**, **Nicholson** and
**Lufkin** each print the Crescent "C" lockup directly above their own
wordmark (`CRESCENT / WISS`, `CRESCENT / NICHOLSON`, `CRESCENT / LUFKIN`), so
the family is stated by the artwork, same justification as ABB Baldor-Reliance.
Crescent's own "C" mark is vector art in red-orange, fill
`(0.785, 0.252, 0.154)`. Grouped in `MAP` under the `Crescent` prefix so the
family subtotal and the per-brand rows are both visible.
— Applied master catalog Hand, Power & Analytical Tools chapter, printed
pp. 6-8, 10, 11 (2026-08).

**GEARWRENCH** — deliberately NOT folded into Crescent. GEARWRENCH and Crescent
are both Apex Tool Group brands and the extract was delivered under the file
name "Apex_Hand_Tool_Crescent", but **no Apex logo or wording appears anywhere
in the extract**, and a file name is not on-page evidence. Logo is a two-part
vector wordmark, orange `(0.929, 0.542, 0.134)` + near-black. If the billing
owner wants an Apex Tool Group roll-up, GEARWRENCH and the whole Crescent
family go into it together — ask before applying.

**Empire** (Empire Level — box levels, I-beam levels). Standalone here; often
associated with Milwaukee Tool, but no Milwaukee branding appears on Empire's
blocks. **Precision Brand** (feeler gages, thickness gages) — standalone.
**Anchor Brand** ("Pure Quality, Pure Value, Since 1963" — adjustable wrenches).
Note this is *not* obviously the same entity as the registry's existing
**Anchor Wiping Cloth**; do not merge the two without confirmation.
**Milwaukee** (tape measures) — standalone. All same run.

**APEX (Assembly & Fabrication Tools)** — bit holders, hex bits, insert bits.
**This is a DIFFERENT COMPANY from Apex Tool Group** (the parent of GEARWRENCH
and Crescent, discussed above and below). The two share nothing but a name:
this APEX's own logo reads "APEX / ASSEMBLY & FABRICATION TOOLS" in orange
vector art, fill `(0.894, 0.328, 0.001)`, and it is a fastening/bit-driving
tool brand, not the GEARWRENCH/Crescent parent. The extract this was found on
was even named with "Apex" in the filename alongside a genuine Apex-Tool-Group
extract from the same job — do not let two same-named brands in one job merge
into a single row. Kept in `MAP` under a name that spells out the distinction
so it can never collide with a future "Apex Tool Group" rollup row.
— Applied master catalog Hand, Power & Analytical Tools chapter, printed p.16
(2026-08).

**Cleco** (Cleco Production Tools — pneumatic impact wrenches, screwdrivers,
grinders, nutrunners). Widely known outside this registry as an **Apex Tool
Group** brand (same corporate family as GEARWRENCH and Crescent, measured
elsewhere in this job) — but that is outside knowledge, not on-page evidence:
no Apex logo or wording appears anywhere in the 3-page extract this was
measured on. Kept standalone for now; ask the billing owner before applying
an Apex Tool Group rollup that would combine it with GEARWRENCH/Crescent.
Logo is vector art in Cleco's house orange, fill `(0.957, 0.475, 0.127)`
(also appears as `(1.0, 0.347, 0.0)` on a colored banner background — same
brand, fill shifts with the substrate it sits on, so match by rendering, not
by exact fill value alone). — Applied master catalog Hand, Power & Analytical
Tools chapter, printed pp. 28, 29, 31 (2026-08).

**Cleco (Dotco)** — Dotco is Cleco's brand for pneumatic die grinders. Prints
as a stacked "Cleco / Dotco™" lockup, same justification as Crescent's
Wiss/Nicholson/Lufkin sub-brands: the family is stated by the artwork.

**Ingersoll Rand** (air tools — impact wrenches, angle grinders). Standalone.
Logo is vector art in red, fill `(0.875, 0.152, 0.111)`. Same run.

**Fluke** (Fluke Corporation — infrared thermometers, test/measurement
instruments). Standalone; appears on a page otherwise all Cleco content, a
reminder to keep scanning to the bottom of a page even when everything above
looks like one supplier's chapter section. Same run.

**Wright Tool** (Wright Tool Company — combination and adjustable wrenches,
"Made in the USA", WrightGrip). Independent US manufacturer; **not** an Apex
Tool Group brand, despite sharing a page with GEARWRENCH. Keep it out of any
Apex rollup. Logo is vector art in dark navy, fill `(0.026, 0.17, 0.283)`,
bbox ~72x12 pt — see the clustering warning below for why it is easy to miss.
— Applied master catalog Hand, Power & Analytical Tools chapter, printed
pp. 3-6, 10 (2026-08).

> **Group vector paths by fill AND spatial proximity, not fill alone.** The
> SKILL.md example groups `get_drawings()` by fill color and then filters the
> per-fill bounding box by size. That silently loses any logo whose fill is
> reused elsewhere on the page: the group bbox stretches to cover every
> same-colored path and blows past the size filter. Wright Tool's logo was
> invisible to a fill-only scan for exactly this reason, on a page where Wright
> owned 0.795 of the billable space. Cluster the rects *within* each fill group
> by proximity (single-link, ~6 pt gap) and test each cluster's bbox. Also do
> not exclude pure black `(0,0,0)` fills as "text" — plenty of wordmark logos
> are black vector art.

> **Fill colors are a search hint, not an identity.** Milwaukee's logo on this
> extract is vector art with fill `(0.890, 0.096, 0.214)` — byte-identical to
> the fill recorded for **MCR Safety** elsewhere in this file. Two unrelated
> brands, one red. Use a recorded fill to *find* candidate logos quickly, then
> confirm what it actually is by rendering the page and looking. Never resolve
> a supplier from a fill match alone.

## Standalone (no known parent/rollup)

Anchor Wiping Cloth, CRC, Osborn, WD-40, JTEKT (formerly sold as Koyo — note
the "Formerly sold as" sub-brand text if it appears; it's the same company
under a legacy name, not two different suppliers), PBC Linear (and its
Simplicity sub-brand), Bishop-Wisecarver, Symmco.

**NTN** (NTN Corporation, Japan — deep groove/radial ball bearings, "made-in-
Japan premium quality" copy). Its own parent; does **not** roll up to
Schaeffler or Regal Rexnord. Logo is vector art in corporate blue,
fill `(0.0, 0.562, 0.834)`, bbox ~75x25 pt.
— confirmed 2026-07 on an Applied master catalog extract, printed pp. 233-238.

**NSK** (NSK Ltd., Japan — super precision angular contact bearings, 7000
series). Independent of NTN despite the two sharing a page and both being
Japanese bearing makers; do not merge them. Logo is vector art in red,
fill `(0.884, 0.158, 0.150)`, bbox ~60x18 pt.
— same run. NSK was found *only* by scanning vector drawings: its section
heading ("7000 Series Super Precision Angular Contact Bearing") contains no
brand token, and the page returns no raster logo image.

Safety / PPE standalones, all confirmed on the Applied Safety Products chapter
(printed pp. 42-49, 2026-07):

**MCR Safety** (Memphis/MCR — safety glasses and coated gloves). Logo is a red
star, part vector `(0.890, 0.096, 0.214)` and part raster wordmark, so it needs
*both* detection paths.

**MSA** (Mine Safety Appliances — V-Gard hard hats). Green raster wordmark.

**Master Lock** (padlocks, lockout/tagout devices).

**Sqwincher** (electrolyte hydration products — Qwik Stik, Sqweeze Pops).
Appears in a safety chapter despite being a beverage brand.

**KleenGuard (Jackson Safety)** — kept standalone deliberately. The catalog's
own footnote says "*Trademark of Kimberly-Clark Worldwide Inc., or its
affiliates," and the registry already maps Kimberly-Clark *janitorial* brands
(Kleenex/Scott/WypAll) under **Essendant** — but that rollup came from a
janitorial distributor's answer key and does not automatically apply to PPE.
Trademark ownership is not the same as the billing entity. Ask before merging
this into any Kimberly-Clark or Essendant row.

## How to use this file on a new catalog

1. Before building region specs for a new catalog, skim this list for any
   brand you already recognize — if the catalog features CRC, Schaeffler
   brands, Regal Rexnord brands, or Essendant's house brands, you likely
   already know the rollup; use it rather than re-deriving it.
2. When you hit a brand not listed here, don't guess at a parent company —
   either treat it as standalone until told otherwise, or ask the user
   directly if a rollup applies. A wrong guess here is a real billing error,
   not just an inconvenience.
3. Add newly-confirmed entries back to this file, in the same format, so the
   next job benefits.
