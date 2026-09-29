# July 2026 photo registration

The durable source records are:

- `ref/photos/juku-pcb-2/registration.json` — image hashes, acquisition order,
  side/mirror state, dimensions, and global transforms;
- `ref/photos/juku-pcb-2/panorama-board-fiducials.json` — reviewed board
  landmarks;
- `ref/photos/juku-pcb-2/local-package-registration.json` — direct package
  anchors and independent checks;
- `ref/photos/juku-pcb-2/d42-d43-orientation-audit.json` — two owner close-ups
  establish right-facing notches for both fitted К555ИР16 packages; mirrored
  2x7 fields trace their common pin7 strip to marked GND and pin14 strip
  through D58.20 to D26.26/+5 V. The routed copper refresh remains open;
- `ref/photos/juku-pcb-2/d26-d58-plus5-strip-review.json` — native-resolution
  screw-area copper chase connects D26.26/+5 V to D58.20, D43.14 and D42.14;
- `ref/photos/juku-pcb-2/d58-orientation-placement-review.json` — the adjacent
  КР580ИР82 also has a right-facing notch; its same-row photo placement
  conflicts with modeled A56-A58/X9 landing positions;
- `ref/photos/juku-pcb-2/x9-d58-local-row-review.json` — the wider owner
  view puts the X9 cable termination band beneath D26, well right of D58;
  individual A45-A58 solder-hole numbering remains open;
- `ref/photos/juku-pcb-2/x9-fifteen-site-band-review.json` — a full 15-site
  mirrored solder band matches D26 lead pitch. Full site10 reaches an
  intermediate via. A front pin count favors D26.27/DB7 through its likely
  counterpart, but the across-face join and cable membership need meter proof;
  a fourteen-site subtraction remains provisional (see
  `ref/photos/juku-pcb-2/x9-site10-via-review.json`);
- `ref/photos/juku-pcb-2/x9-solder-row-registration.json` — both faces place
  the mixed band below D26; A-number order and exact board coordinates remain
  open;
- `ref/photos/juku-pcb-2/x9-plus5-rail-site-review.json` — full-band sites
  9 and 12 share the registered D26.26 copper traced to marked +5 V. They
  are plausible A53/A54 contacts, with cable membership still open;
- `ref/photos/juku-pcb-2/d59-orientation-audit.json` — two owner close-ups
  establish the right-facing notch of marked КР531ЛН1; a four-corner solder
  fit locates its supply contacts without closing their rail routes. The source
  footprint is corrected and routed copper needs a pin-aware refresh;
- `ref/photos/juku-pcb-2/top-bus-buffer-population-audit.json` — D25/D23/D24
  are marked КР580ВА87 and D29 КР580ВА86; D23/D24/D29 left notches are
  photo-closed, while D25's molded notch is indistinct;
- `ref/photos/juku-pcb-2/d25-ground-strip-orientation-review.json` — common
  lower solder copper with left-notched D23 strongly supports D25's modeled
  left-facing pin sequence; direct rail continuity remains unmeasured;
- `ref/photos/juku-pcb-2/d105-h-registration.json` — native-sheet, `.009`
  placement, and owner-photo closure of X1.107B/-BLOCK/H and R1;
- `ref/photos/juku-pcb-2/endpoints.csv` — original-image endpoint coordinates,
  confidence, reviewer, and disposition.
- `ref/photos/juku-pcb-2/x6-cable-registration.json` — factory wire-table and
  two-angle owner-photo closure of bracket X6 through PCB points A:3/A:4.

Panoramas, overlays, and crop atlases are navigation aids. Electrical evidence
always cites an original JPEG coordinate and a reviewed path.

## Current result

All 28 July grid images are registered into a common 310 x 266 mm
component-side coordinate frame, with the solder side mirrored explicitly. The
endpoint table contains 641 reviewed rows:

| State | Rows | Meaning |
| --- | ---: | --- |
| `accepted` | 39 | reviewed pad/path evidence adopted into the board model or preserved as an explicit test landing |
| `measurement` | 596 | pad/path review is inconclusive; continuity or better local evidence is required |
| `rejected` | 6 | two former D94.5-D93.1 claims and four former R94 endpoint assignments disproved by owner continuity/photo review |

The table's `candidate_net` names the current model net for a registered pad;
on a `measurement` row it does not assert that the owner board follows that
net. All 81 nonblank candidate labels now resolve to their stated pad in
`kicad/juku.board.json`. R102.1 and R108.1, for example, carry the sheet-3
RC net names while their remote owner-board paths remain unproved.

Confidence metadata consists of 429 `local-package-fit`, 155
`registration-only`, and 14 `registration+unique-hole-snap` rows. Eight use
`registration+package-row-snap` after correcting the D29 lower-row probes. Two use
`local-package-pin-count` after correcting the D39 component probes. Two use
`local-package-fit+continuous-copper`, two use `local-package-fit+visible-gap`, four use
`registration+visible-common-landing`, one uses
`registration+separate-cable-joint`, four use
`registration+unique-joint`, three use `registration+three-lead-identity`, four use
`local-cross-face-fit`, seven use `cross-side-registration`, one uses
`cross-side-registration+visible-joint`, and one uses `overlap-trace-topology`.
Four `panorama-projected-region`
observations record photo-exhausted regions without pretending that a
projection is pad identity.
A hole snap or accurate pad projection is not electrical evidence by itself.

Accepted paths and owner corrections:

- D2.1/.3/.5/.6/.7 have locally fitted pads and source-drawn
  `A10/A14/A12/A15/A9` assignments. Their former photo claim of continuous
  routes to D4.1/.3/.5/.6/.7 is withdrawn: the D4 solder fit was one contact
  column left of the marked package and one row low. The corrected D4 opposite
  column is close to the five D2 runs and carries modeled BA addresses, raising
  a raw versus buffered address question. The ROM directly beside D4 in exact
  `.009` sheet-1 detail `101805510` is D6, so its visible D4 routes do not
  answer the D2 question. Rechase each run and follow D2's address lines
  through the adjoining drawing tiles before using the photo as electrical evidence
  (`ref/photos/juku-pcb-2/d2-d4-column-row-audit.json`).
  Native solder detail `200527310` shows D2.1 ending at an open via near
  `(2185,1498)`, about 55 px short of D4.19. The D2.5/.6 lines pass between
  nearby D4 joints. Their apparent row alignment is not a direct backside join.
  The overlapping solder tile `200525009` shows the same D2.1 via near
  `(4005,1465)`, 385 px east of the translated D2.1 pad. Its trace stops at
  the annulus, with a visible gap to the separate D4.19 contact near
  `(4055,1465)`. This confirms the local gap in a second photo; the far end
  of the route remains unknown.
  D2.3 at `(1800,1613)` has no visible solder-face copper departure in either
  tile (approximately `(3620,1580)` in `200525009`). The adjacent D2.4/.5
  joints show clear departures for comparison. D2.3's route must be sought
  on the component face or by continuity; its remote endpoint is still open.
  The July component socket hides the trace beneath its third left contact
  near `(1932,1852)`. The May rotated view puts the same D2.3 contact third
  from the left on the lower row near `(1599,775)`, but also does not expose
  a trace departure. These views locate the probe pad without proving A14.
  Native solder `200527310` shows D2.5 and D2.6 bending north into channels
  that pass above D4.15 and D4.14 without landing on either pad. D2.7 runs
  from `(1800,1844)` to an open via near `(2100,1840)`, about 140 px before
  D4.13. Overlap `200525009` repeats that bent trace and isolated via near
  `(3950,1830)`. A wider native crop follows D2.5 to an open via near
  `(2640,1685)` and D2.6 to another near `(2500,1745)`. All three far
  destinations and modeled address names remain unverified by these local
  solder-face segments.
  Using the corrected CPU two-face fit, the D2.5 via projects under the CPU
  body near front `(1096,1958)`. D2.6 projects into the exposed CPU/D4 gap
  near `(1238,2018)`, about 15–20 px from a visible ring near `(1227,2000)`.
  That ring is a candidate for continuity checking, not an adopted hole match.
  May `201940304` shows the same ring near `(1768,1650)` as part of a
  distinctive three-ring pattern also visible in July. The locally mapped
  D2.6 projection remains about 24 px from it in May, with no separate drill
  exposed at the projected point.
  D4's two-face fit projects the D2.7 via near component `(1661,2064)` in
  `200411500`. No drill is exposed there; the conspicuous ring near
  `(1637,2028)` is about 43 px away and is not a verified match.
  A new D4 component fit projects the D2.1 via near front `(1568,1725)`; the
  exposed hole `(1555,1755)` is about 33 px away and is not an adopted match.
  May component photo `201940304` repeats that separate D4-side hole near
  `(1477,1245)` without exposing a second drill at the via projection.
  The exact `.009` assembly view `114604420` labels D4 above D107 and D2 to
  their right. Both 2×10 buffer fields are now independently registered on
  the component and solder faces, preventing the lower D107 row from being
  reused as a D4 pad.
  The local registration generator now compares every projected contact across
  different packages in each original image; all 90 current fits pass the
  cross-package collision check.
- The former D94.1/.2/.3-to-D93.4/.3/.2 photograph interpretation is
  invalidated by chip-removed owner continuity; those photograph rows establish
  package registration only, not electrical identity.
- Direct continuity proves D94.15 -> D93.3 / `FDC_CS_N`, D94.2 -> D99.9 + R89,
  D94.3 -> D93.4 + R88 / `FDC_RE_N`, and D94.4 -> D93.2 + R87 / `FDC_WE_N`.
- Direct continuity proves D94.13 is D105.3 qualified peripheral `/WR`; it is
  about 84 kΩ from D104.7 and is not directly connected to raw D5.27.
- Full-resolution review retracts the former D94.5-D93.1 path: D93.1 owns the
  short trace ending at the visible gap, while D94.5 is visibly NC.
- А:17 -> S1.1 / `RES_RC` (dedicated numbered wire landing).
- D98.7 -> А:18 -> S1.2 / `D98_Y3_S1_2`.
- D98.3 -> D28.5 remains drawing-supported, but the former R94 branch on the
  superseded `D98_Y1_R94` model net is rejected. Owner continuity locates actual
  10k R94 above D28, from D28.11/D93.38 to +5 V. The photographed 220-ohm body
  remains unassigned; the source model and promoted zero-open route now preserve
  it separately as `RUNK1` with two explicit measurement boundaries.
- The former photo-only D106.7 `Q3` -> D93.26 `RCLK` join is
  superseded by exact `.009` sheet 1: D106.7 reaches D28.9, D28.8 clocks
  D96.3, and D96.5 drives D93.26 / `FDC_RCLK`. See
  `docs/fdc-hardware-handoff.md`. A raw solder crop `(1050,2020)-(1660,2240)`
  of `PXL_20260710_200506061.jpg` resolves the registration mistake: the
  former D106.7 seed at `(1154,2131)` lies on the bare westbound D93.26 trace,
  without a visible D106 joint. The D93.26 pad remains identifiable, but the
  supposed cross-package endpoint is only a trace projection. Both rows are
  measurement requests; D106.7 needs a new pad fit or continuity check. The
  wider crop `(550,1850)-(1650,2240)` shows the D93.26 trace continuing west
  across the D106 region, but no uninterrupted B.Cu path from it to the
  registered D96.5 joint at `(762,2041)`; that source-drawn join also remains
  a continuity check on the original board.
- D95.14 -> R92.2 / `FDC_DDEN` (sheet-identified `FM/MFM`).
- D101.4 -> R92.1 + R99.2 / `D101_D02_R92_R99`.
- D101.7 and D101.9 have separate registered solder landings without a visible
  local B.Cu bridge in `PXL_20260710_200522685.jpg`. Their drawing-marked
  output tie remains a measurement request because F.Cu and remote copper are
  not fully visible (`docs/d101-output-tie-photo-review.md`).
- D99.4 has no visible local B.Cu departure in the same solder frame. Its
  component-side continuation is cable/package-obscured. The exact sheet-3
  overview places it on the rail above D94.14/D101.7 and traces that rail
  to D93.23/HLT; confirm physical continuity
  (`docs/d99-q1n-a4-conflict-photo-review.md`).
- The D93 socket registrations identify individual pad positions. Only the
  D93.23 pair records the source-drawn HLT/D99.4 relation; 31 other D93 pad
  notes had inherited that sentence by copy and have been corrected. Their
  remote nets still require their own source or continuity evidence.
- R99.1 -> D101.8 / `GND`.
- VT2.1 -> R65.1 / `VIDEO_OUT`; two registered July angles directly expose
  the emitter's shared landing, while an independent May angle identifies the
  yellow three-lead body as VT2 marked `Б / 8901`. The separately drawn C94 is
  obscured, so both C94 endpoints remain explicit measurement boundaries.
- Factory cable point A:3 -> X6.1 is an electrical boundary beside VT2/R65;
  its earlier claimed coincidence with VD3.2 is rejected by original-resolution
  photo review. The separately insulated A:4 reaches X6.2 / `GND`. Both are
  component-side lap joints; X6 itself is bracket-mounted and has no PCB footprint.

R67.2's former no-via conclusion is withdrawn. The upper component lead is
near `(3365,1730)` in `200418174`, not `(3321,1698)` on adjacent bare board.
The D102-local cross-face fit projects it near `(874,956)` in `200522685`,
within about 5 px of a real solder joint `(869,953)`. A visible B.Cu line
continues east to open annulus `(1295,958)`, also repeated in overlapping
`200506061`. This accepts the local two-face R67.2 joint and trace, while the
far annulus's front counterpart and VT2-base continuity remain open. D102 and neighboring D97 inverse fits place that back hole near front `(2937,1739)` and `(2905,1736)` respectively; neither is a unique visible drill, so nearby front annuli must not be snapped to it.

The reviewed package fits also corrected the source placement/orientation of
D2, D10, D40, D41, D94, D100, and D98. A D11 solder fit corrects endpoint
coordinates without changing its source placement. At D98.7, the component
fit also identifies the visible white wire-18 lead; the factory wire table
independently closes that off-board path as А:18 to S1:2. A new affine solder
fit corrects a roughly 330 px global-projection displacement and shows that no
PCB copper departs D98.7; both observations are accepted. The promoted routed
PCB carries the registered placement/source topology with exact pad identity,
and its Gerber ZIP is package-verified. D94/D100 functional boundaries still
hold design release independently of route/package integrity.

The D93 component fit uses `PXL_20260710_202708344.jpg`, a close-up taken with
the known КР1818ВГ93 removed from its socket, rather than the populated-board
panorama. All 40 socket contacts and the printed pin-40 end are visible there,
giving a direct
pin-row orientation and stronger pad landings for the unresolved reset and
clock endpoints. A reflected fit in `PXL_20260710_200506061.jpg` places the
same pins on the actual solder joints. Their far destinations remain
measurement requests; package registration alone is not continuity evidence.
The same rule now covers D94 A0-A4 explicitly: validated component and reflected
solder fits preserve exact original-image coordinates for pins 10-14. Raw-crop
review cannot follow any of the five to a unique remote source, so all ten rows
remain measurement requests and no address-bus assignment is inferred.
The registered `.009` factory assembly drawing now also fixes the socket centre
at `(235.941,73.335)` mm. This replaces the former `(248,70)` approximation,
which physically overlapped D95. The same drawing moves C10 from the lower FDC
row to its depicted position immediately right of D93 at `(252.361,73.163)` mm.

## Reproduce the registration aids

```sh
python3 scripts/photo_registration.py validate
python3 scripts/photo_registration.py solve
python3 scripts/photo_registration.py contact-sheets
python3 scripts/photo_registration.py panoramas
python3 scripts/photo_registration.py rectify
/usr/bin/python3 kicad/render_photo_endpoint_overlay.py
/usr/bin/python3 kicad/report_photo_placement_residuals.py
/usr/bin/python3 kicad/render_endpoint_crop_atlas.py
/usr/bin/python3 kicad/render_d96_d99_cross_registration.py
/usr/bin/python3 kicad/render_d93_clock_isolation.py
/usr/bin/python3 kicad/render_d94_d5_layer_handoff.py
/usr/bin/python3 kicad/check_serial_photo_placement.py
```

The panorama stitcher requires every declared source tile to join its
homography graph. `rectify` produces common-coordinate review images and a
held-out error record under `docs/photo-registration/`. To map a panorama point
back to every covering original image:

```sh
python3 scripts/photo_registration.py project --group solder_grid --x 506 --y 338
```

Do not cite a panorama seam or rectified pixel as endpoint provenance; use the
projected original-image coordinate.

The broad `component_grid` board registration is unsafe as a D9/DRAM cross-region
coordinate bridge. Its inverse sends photographed D9.1 in original
`PXL_20260710_200411500.jpg` `(2977,1318)` to approximately
`(132.79,107.60)` mm, while the independent D8/D7 local fit places D9.1 at
`(116.77,109.4)` mm. D7.7 shows almost the same ≈16 mm horizontal offset.
The historical 4×8 measurements have regular spacing, but native-image
registration identifies the measured features as DRAM package contacts.
Their small local fit residual does not establish capacitor landings or
absolute alignment with D9. See
`docs/d9-owner-footprint-photo-audit.md` before assigning C35/C88 holes.
The native D9 component photo also shows D67’s top contacts about
`(-113,+143)` px and adjacent D66’s about `(-109,+143)` px from their
D9-local source-PCB projections. Those independent four-corner package fits
point to a DRAM-row alignment issue, not a C35-only move.
The four historical row centres at y≈631.5, 760.3, 890.4, and 1021.0 px
match the four DRAM top-contact rows near y≈633, 761, 890, and 1019 px in
the rectified solder view. The first purported capacitor-grid midpoint
`(579.9,631.5)` is within ≈1.7 px of the midpoint of registered D67.16 and
D66.1. The 28 inherited DNP footprint sites require a distinct-hole audit.

## Local package fitting

When global board projection misses a physical pad row, add direct anchors to
`local-package-registration.json` and run:

```sh
/usr/bin/python3 kicad/local_package_registration.py
/usr/bin/python3 kicad/apply_local_package_registration.py REF
```

Each fit needs at least two anchors plus an independent held-out check. Applying
a fit updates coordinates and confidence only; it preserves `measurement`
state until visible copper or continuity establishes a destination.

Current held-out errors are sub-2.2 px for the accepted D2/D4/D94 package-row
fits. Direct component and reflected solder fits now replace D106 projections
that landed left of the vertical К555ИЕ7 package or on its body. The corrected
solder anchors use the centers of visible joints rather than adjacent trace
departures; the independent pin-5 check is 0.001 px. Pins 7-10 extrapolate into
the rail-obscured package end and remain non-electrical projections. The
former pin-7 projection lands on D93.26's trace, without a visible D106
solder joint; see the RCLK review above.
Separate component and reflected solder fits now land D28 on the
adjacent К155ЛН3, using its unobscured seven-pad column and coherent solder
rows. The component pin-4 check is exact and the solder pin-5 check is 0.010
px. A close audit distinguishes the small fitted solder joints from the larger
adjacent open vias and their trace departures; this prevents D28 from being
conflated with D106, while the cable-hidden component fanout remains a
continuity boundary. D93, D100, and D98 also have useful local fits, but their unresolved
signals remain measurements where copper is obscured or leaves the visible
layer. The corrected D11 solder fit holds both unused corners out at
2.375 px. Its old fourteen-row assignment began four joints too high;
D11/D27 cross-side alignment now puts D11 at `y=1610..2211` in
`PXL_20260710_200506061.jpg`. The conspicuous scar is near the
corrected upper D11 rows, but it does not establish the obscured factory
bridge endpoints. The corrected factory landing projections were checked
in two complete D11 solder tiles and two partial overlaps: the upper
point approaches the top edge in the partial views, and none of the four
shows a unique four-hole match. The D98 solder fit holds pin 16 out at 0 px on the
complete affine 2x8 row. Its remaining measurement records now describe
unresolved copper destinations rather than retaining the obsolete claim that
two-side package registration is still required. Component-side records likewise
use the validated contact coordinates and limit uncertainty to wire/body-hidden
remote fanout, rather than calling the fitted contacts body projections.

The marked `КР531ИЕ17` immediately right of D41 is D40. Its raw component-side
row shares D41's scale and baseline: pins 1/8 span `(2756,1956)` to
`(2361,1956)` px and held-out pin 9 lands at `(2361,2126)` px. This moves D40
from the old `(258.0,125.6)` mm drawing seed to `(258.56,140.99)` mm and rotates
its notch to the photographed right-facing orientation. The same bracketed
D41/D40 view resolves the factory C83 label location: the inter-package strip
contains no populated capacitor body, but has two plausible bare front sites.
The image cannot distinguish omission during assembly from later removal, but
both histories establish the photographed C83 callout population as absent.
The promoted D41 solder fit at x1999..2329, rather than its obsolete
x1451..1781 wrong-package seed, projects candidate C83 front sites
`(2283,1923)`/`(2283,2153)` near visible solder crowns
`(1920,1585)`/`(1920,1813)`. Those are strong geometric matches,
but direct continuity and the lower rail remain open; see
`ref/photos/juku-pcb-2/c83-d41-d40-gap-pair-review.json`.
The same seed reconciliation updates directly anchored D38, D40, D51,
D54, D13, and D11 endpoint rows in `endpoints.csv`. These changes identify
physical package contacts; they do not prove the outgoing nets. Run
`python3 scripts/check_photo_endpoint_registration.py` after changing a
package fit or endpoint row. It compares all matching endpoint seeds to
promoted component and solder anchors plus complete D40/D11/D13 rows;
the current run checks 75 anchors and 25 grid pins.
The historical 4×8 panorama pattern matches DRAM package contacts rather
than independent decoupler pads. The inherited C63 model slot at
`(176.1,145.6)` mm retains schematic rail-bypass intent and assembly DNP
status; its modeled PCB footprint is provisional until distinct holes are
identified. It has no populate-now BOM entry.

The same array panorama closes the adjacent R49-R56 RAS resistor bank. The
common `.006` assembly drawing supplies the refdes order and the target-board
component overlaps expose every populated body: R56/R52, R55/R51, R54/R50,
and R53/R49 from top to bottom in one vertical column. Four red bodies read
`75Ω`; four tan bodies read `5K1`. Clear R50/R53 lead joints select the
10.16 mm vertical footprint, and the reflected panorama corroborates the
drilled column. The durable fit and rounded board coordinates live in
`ref/photos/juku-pcb-2/ras-resistor-bank-registration.json`; electrical nets
remain the separately traced sheet-2 D53/RAS/GND result.

The marked `КР580ВК38` D5 now has a direct affine component fit in raw
image `200411500`. Its complete 2x14 contact field and right-facing notch move
the pad-row centre from the old drawing seed `(31.20,99.20)` mm to
`(23.69,109.52)` mm and correct the PCB orientation from 90 to 270 degrees.
Pins 26 and 28 are independent zero-pixel checks. Fitted D5.26 lies at
`(1214,1480)` px; one straight visible copper segment reaches the distinct
white-wire surface joint at `(1218,1593)` px. Package registration alone is
placement evidence, while that separately reviewed copper departure proves
the D5-side A19/MEMW landing at `(35.308,122.281)` mm.

The same owner tile and factory drawing now resolve the complete horizontal
decode row rather than relying on order guesses. Socketed D8 is the marked
`К155РЕ3` PROM at `(83.332,113.308)` mm; the adjacent metal 2x8 package is
D9 `К555ИД7` at the later D8/D7-relative corrected source center
`(107.88,113.205)` mm; and the black 2x7 package immediately
right is unambiguously marked `КР1533ЛА3`, placing D7 at
`(131.465,113.308)` mm. All three notches face right (270 degrees), their
held-out corner/contact checks are zero-pixel at recorded precision for the
original local package fit (D9's subsequent correction is in
`docs/d9-owner-footprint-photo-audit.md`), and the
independent D50/D51 estimates spread only `0.532`, `0.667`, and `0.560` mm,
respectively. This corrects the former metal-D7 attribution and the stale
vertical D8/D9 seeds.

The opposite-face tile `PXL_20260710_200525009.jpg` now registers the same
decode row directly: D7's complete 2x7 solder field lies immediately left of
D9's 2x8 and D8's 2x8 fields after mirroring. D7.3 is the top joint near
`(2190,1029)` and D7.11 the bottom joint near `(2245,1193)`. Their annuli
are locally separate with no visible solder bridge. The corrected exact drawing ties D7.11 to D105.3, not D7.3;
that unusual source output tie still requires continuity; see
`docs/d7-gates-source-review.md`.

The complete D8 2x8 solder field is now directly fitted to the right of D9
in the same tile. Its mirrored top row runs D8.1 `(3120,1030)` through
D8.8 `(3505,1030)` at 55-pixel pitch; the bottom-right joint is D8.9
`(3505,1193)`. Independent pin-6 and pin-9 checks both have zero error at
rounded-pixel precision. This fixes the D8 package pads for the R21–R28
bank review, but the R28 resistor landing above the row is still only a
cross-face search projection; see
`ref/photos/juku-pcb-2/r21-r28-bank-pin-order-review.json`.

The adjoining D9 2x8 solder field is independently fitted in the same tile,
with held-out pin-6 error below one pixel. Extrapolation from that fit puts
the provisional C99 component pair near `(3093,1487)`/`(2916,1487)` on the
solder face. A soldered pair near `(3040,1492)`/`(2875,1495)` has the right
separation but remains 40-55 pixels offset. The western solder joint is also
only about 11 pixels from projected R17 lower lead, so it may be R17 itself.
These joints are probe targets, not adopted C99 through-hole matches; see
`ref/photos/juku-pcb-2/c99-assembly-photo-review.json`.

The uninterrupted white A19 lead from the proved D5-side joint ends at the
distinct `(3255,1585)` px surface joint below the marked black D7. Its fitted
`(130.027,121.736)` mm position is `94.721` mm from A19A, matching the
factory's approximately 9.5 cm conductor and closing the D7.2-side MEMW
landing without inferring identity from an unrelated nearby white wire.
The same fit moves assembly-labeled horizontal R13 and the lower R14 of the
R11/R14 pair to `(50.123,101.273)` and `(59.460,125.041)` mm. R14's body is
partly hidden by A19, but the drawing order and both landing regions remain
visible. These six row fits restore zero source-PCB short, clearance, and
crossing violations.

D50 and D51 now have direct component and reflected-solder fits in the same
raw photo pair as validated D2. Their markings and bottom-facing notches both
require 180-degree PCB orientation. D50's component checks are `0.143`/`2.857`
px and its solder checks are `0.429`/`5.571` px; D51's corresponding checks are
`0.286`/`2.286` and `0.286`/`4.286` px. Component and solder estimates place
D50 relative to D2 with a `2.238` mm spread, while the much more local D50-D51
spacing agrees within `1.125` mm. Their midpoint pad centres are
`(100.685,143.923)` and `(100.685,169.057)` mm. The source PCB uses these
centres and `kicad/check_d50_d51_photo_placement.py` guards the pair.

The same registered component/solder pair now fits the vertical `КР531ЛА1`
D38 below D41. On the component side, pins 1/7 define the fit while pins 4/8
hold out at `0.000` px; the reflected solder fit holds pins 4/8 out at `0.500`
and `1.118` px. The independently fitted D41 cross-side transform predicts
the D38 corner rows before this fit, so the two nearby white-wire joints can
now be investigated against real package geometry instead of the coarse board
panorama. These fits establish pad identity only; no wire joint or copper path
is promoted by package registration alone. Their independent centre offsets
from D41 agree within `1.117` mm; the midpoint moves D38's pad-row centre from
the inherited `(233.405,156.600)` mm seed to `(234.563,159.619)` mm. The source
PCB now uses that midpoint and `kicad/check_d38_photo_placement.py` guards it.

The marked `КР1533ЛА3` below D40 is D39, matching the official-census owner
substitution and the `.006` assembly order. Its component fit uses pins 1/7
and holds pins 4/8 out at `2.000` and `5.385` px. The photographed top-facing
notch also corrects the inherited 180-degree orientation. Independent
projections from the already fitted D40 and D41 packages agree within `0.024`
mm and place D39's pad-row centre at `(273.972,159.582)` mm. D38 is deliberately
only a held-out, longer-baseline check; it predicts the centre within `1.940`
mm. A visually regular backside 2x7 joint group near `(885,1945)` px was tested
and rejected: composing it through D41's two-sided registration misses the
component-side D39 position by `9.37` mm, proving that it belongs to a
neighboring DIP. That former candidate is not used. The correct D39 backside
group is locally fitted at pins 1/7, with pins 4/8/14 held out at `0.500` px
each, immediately left of the established D38 footprint. The earlier D37 label
was therefore an identity error, not a second placement candidate; this upper,
top-notched device is D39. Its solder fit is retained as package evidence but
does not constrain the lower D37 or the A12 chase. The source PCB uses the
component-derived centre and `kicad/check_d39_photo_placement.py` guards
both-side identity, placement, and orientation.

The later native component tile `200445914` exposes D39's same top notch.
Its former D39.10/.9 endpoint seeds were on the left row; the counted
right-row contacts are near `(3038,655)/(3038,710)`. The older solder
coordinates near `(1218,2172)/(1220,2228)` were already on the correct
left-column caps, despite stale notes that said they missed the joints.
`ref/photos/juku-pcb-2/d39-pin9-pin10-photo-review.json` records this
pin-by-pin correction. Source nets `XTAL16M` and `LATCH_SIG` still need
owner continuity for the remote paths.

The actual D37 is the separate bottom-notched `КР1533ЛА3` in the lower
`D36–R57–D37–D33` row. The target component view fits pins 1/7 and holds pins
4/8/14 to `0.500` px; bracketing D36/D33 centres and the held-out D103 row
confirm the assembly-order registration. The same view fixes the intervening
R57 vertically at `(236.7,177.6)` mm with its standard 10.16 mm lead span,
while electrical sheet 2 identifies it as 20 ohms. D37 is now centred at
`(245.5,180.1)` mm with the photographed bottom notch represented by a
180-degree footprint. The same raw frame moves the separately visible vertical
200-ohm R46 out of that package and into its real D33/D103 gap at
`(266.6,184.0)` mm, eliminating four source-PCB pad collisions. No lower-row
solder fit or new electrical continuity is claimed.
`kicad/check_d37_photo_placement.py` guards the source hashes, bracketing
registration, package fit, R57/R46 values, and all three placements.

The marked `К555ТЛ2` D13 now has direct component and reflected-solder fits.
The right-facing notch and complete component contact field put D13.2 at
`(1369,906)` px in raw image `200450127`; pins 4 and 14 are exact held-out
checks. The corrected backside field puts the same pin at
`(2743.6,825.0)` px in `200537608`, with independent pins 4/11/14 held
to `1.5` px. The former fit combined D13's lower row at y1009 with D105's
upper row at y1192, assigning one solder joint to two packages. The component
contact has no insulated-wire termination, and the corrected solder joint
has only its ordinary etched departure; no distinct A12 rework
stub is visible at either face. This rules out a direct D13.2 pad landing but
does not identify the remote `RAM_OUT_EN` surface joint, so A12A remains
board-fit pending. `kicad/check_d13_photo_placement.py` guards the two-sided
identity and coordinates.

The same component view closes the adjacent WAIT cluster mechanically. D13
and D105 both have right-facing notches, so their source footprints are now
270-degree placements rather than the former left-facing 90-degree posture.
The populated red-black-red R1 body sits between them on two component-side
surface landings; native sheet 1 identifies it as the 2 kΩ pull-up from
X1.107B/-BLOCK/H to +5 V. `docs/d105-h-boundary.md` guards the source hashes,
R1 pad positions/construction, connector contact, and both package orientations.

The overlapping raw component tile `200439607` independently holds D13 pins 4
and 14 at zero-pixel residual and exposes a tempting white-wire end at
`(1405,1479)` px east of the package. It is not a landing: the second component
view maps it to `(1627.8,1070.1)` px and shows the tinned end resting on bare
substrate, while the D13 backside basis maps it to `(3268.7,1031.5)` px, again
bare between etched features. The D13 guard preserves both cross-view
projections. This rejects the conspicuous loose end as A12A without using its
proximity to D13/R20 as connectivity evidence.

The owner survey's nominally missing LE4 is the decapped D92 between the
already fitted D38 and D39 packages: its die and bond wires are exposed, but
both complete 2x7 contact fields remain intact. Direct affine fits place D92.1
and D92.13 at `(2484,2290)` and `(2654.333,2345.833)` px in component image
`200418174`, and at `(1719,1951)` and `(1552.167,2007)` px in solder image
`200522685`. Component held-outs are at most `2.0` px and solder held-outs at
most `0.5` px. A broad cross-face check using the upper FDC row found that
the former D41/D38/D92/D39 solder registrations shared an approximately
500-pixel x displacement. Locally valid DIP grids had been paired to
neighboring fields. Their corrected solder fields align with the upper-row
packages: D102–D41 normalized separation is `62.07/61.90` mm on
component/solder photos, D38–D92 is `24.08/23.86` mm, and D92's normalized
D38-to-D39 position is `0.619/0.609`. The corrected D41, D38, D92, and
D39 solder held-outs are at most 0, 1.118, 0.5, and 0.5 px. Neither
factory-link owner pin has an insulated-wire stub at the
package joint, so both require remote-landing searches; A11B is identified
below, while A13B has a strong remote candidate but remains formally pending. Independent
D38/D39 centre estimates spread `1.864` mm and bracket the source D92 centre
within `1.501` mm; that is inside the local photographic uncertainty, so the
existing `(260.005,159.200)` mm centre and 0-degree posture are retained.
`kicad/check_d92_photo_placement.py` guards both-side identity and placement.

The former A9B white-wire candidate at `(2286,2450)` runs on front copper
to annulus `(2288,2298)`. The corrected D38 fit projects that annulus to
`(1907,1982)` on the solder photo; a four-package fit gives `(1914,1964)`,
and the nearer D92-local fit gives `(1912.9,1959.0)`. The visible solder
annulus `(1916,1950)` is about 9.5 px from the last projection and has
uninterrupted copper to registered D92.1/ROE `(1719,1951)`. This strongly
favors A13B over A9B; the through-hole pairing still needs continuity.
Corrected D38.12/SYNC instead has a short solder spur west to bare annulus
`(2025,2063)`, with no visible wire on its plausible front counterpart.
`ref/photos/juku-pcb-2/a9b-corrected-trace-review.json` records both
paths; A9B remains a continuity hold, guarded by
`kicad/check_a9b_corrected_trace_review.py`.

The A13 remote search is now bounded on both ends rather than only at D92.
The drawing puts A13A immediately before C95 below D50 and A13B immediately
after D38, before R35. The D13 fit fixes A13A's owner D13.1 at `(1426,906)`
component and `(2682,825)` solder pixels; like D92.1, it has no insulated-wire
termination at the package pad. At C95, a distinct lower white-wire joint
`(2400,2330)` runs on front copper to annulus `(2430,2377)`; its solder
counterpart and ROE net are unresolved. At D38, the white joint `(2286,2450)`
has the D92.1/ROE trace evidence above, but its through-hole pairing and cable
identity still need a meter check. The candidate ends are about 157 mm apart
in a straight line, slightly more than the table's approximate 15 cm A13
length before routing slack. Both formal A13 terminals remain null pending
continuity and cable-length measurement. `kicad/check_a13_factory_wire_boundaries.py`
guards owner coordinates, ROE pin identities, and non-promotion.

The same raw component tile exposes a distinct white-wire surface joint at
`(2620,1764)` px beside the printed board-point number `11`. D40- and
D41-derived image-to-board transforms place it at `(261.328,128.543)` and
`(261.322,128.553)` mm, only `0.0127` mm apart. Their midpoint promotes A11B
at `(261.325,128.548)` mm on the factory-table D92.13/MEMR island; it is a
remote component-side landing, not the D92.13 package pad. The D7-side A11A
coordinate is closed below, and `kicad/check_a11_factory_wire_landing.py`
guards both terminals.

An overlapping D7 component fit in raw image `200415237` holds the alternate
package row exactly and separates two nearby insulated-wire joints. The
below-left joint cross-registers to the already proved D7.2/A19 endpoint; the
distinct below-right joint at `(1825,1706)` px is therefore the factory-table
D7.1/A11 end. Its fitted coordinate is `(142.256,123.468)` mm, completing A11
to the printed D92-side joint above. The 119.177 mm endpoint chord is about
4.2 mm longer than the table's approximate 11.5 cm entry. As with A8, physical
endpoint geometry is adopted while fabrication cut length stays held for a
direct conductor measurement or examination of a physical original.

D98 and D94 also bound the horizontal 2x10 D100 КР580ВА87 solder footprint.
An affine fit lands both complete rows in the intervening package and holds
the far pin-20 corner out independently at 1.000 px. Native `.009` sheet 3
joins D100.9 OE_N to D99.12 Q2_N and sends D100.11 T to a separate sheet-1
continuation; both are original-board continuity questions because the
photographed departures do not reach a second named pad.
Composing D100's component and solder fits projects the circular endpoint near
`(2625,1900)` component pixels to `(1204,830)` solder pixels. That region is
bare substrate with no via or annulus, so the feature is an isolated
component-side landing/test pad rather than the previously suspected layer
handoff. This closes the false solder chase without assigning OE_N's source.

The corrected D93.24 solder joint has no same-layer copper departure. The raw
tile shows a clean gap between its solder cap and the nearby horizontal trace;
the component-side contact disappears beneath the physical КР1818ВГ93 socket.
The former westbound chase to D99.13 was therefore a panorama-alignment error,
not merely a functionally implausible connection. D99.13's raw tile likewise
shows a capped joint without a same-layer departure. Independent component-side
topology still supplies a contradiction check: uninterrupted copper ties D99.3
`CLR_N` directly to D96.7 `GND`. The identity is no longer inferred merely from the package type:
all 14 contacts of D96's validated fit in `PXL_20260710_200402344.jpg` project
onto the same photographed КМ555ТМ2 in the overlapping
`PXL_20260710_200418174.jpg`, with the notch and both rows aligned. The adjacent
D96.8 `Q2_N` and D99.2 `B` conductors reach visibly separate circular landings;
the overlay explicitly rejects their tempting apparent association. A second,
package-local cross-side transform uses all 16 D99 package holes (maximum fit
residual below 0.001 px) to project those circular endpoints into the solder
photo. Both land on bare substrate immediately above the tinned rail, with no
annulus or continuing solder-side copper; they are one-sided component landings,
not through-holes. This does not exclude a further front-side branch from
D99.2: exact `.009 Э3` sheet 3 draws B1 through E12 post 2, selected to
the D93.28/D100.3 HLD line on post 3. Physical
E12 population and continuity remain to be checked
(`docs/d99-e12-selector-source-review.md`).
The native D99 component-row recheck shifts its package fit 26 px right.
The corrected D99.2 top-row contact near `(3187,1060)` still has an exposed
front trace to its circular landing near `(3185,953)`; reflecting through the
corrected D99 package corners moves that landing's solder-side search to about
`(1018,1004)` in `PXL_20260710_200522685.jpg`. The native solder crop there
is bare substrate, preserving the one-sided-landing observation after the
registration correction. The adjacent D99.3 contact near `(3131,1060)` still
has its separate visible front run toward D96.7/GND. These local paths do not
establish the unmeasured E12 selector continuity.
The already-proved neighboring D99.3 ground path is shown alongside as a local
orientation check. D99 section
1 is therefore held cleared and its pin-13 `Q`
cannot be the live КР1818ВГ93 clock source. No physical `FDC_CLK_1M` source is
accepted from the photographed layers.

The exposed-socket `202708344` view also supplies an independent affine D94
fit: pins 1/8/16 are fit anchors and pins 4/9 hold out at `0.714`/`0.000` px.
It places D94.5 at `(2477,1768.714)` px in the same raw frame that places
D93.1 at `(2215,1810)` px. The earlier review incorrectly read across a break.
Owner inspection and the clearly readable factory E3 frame
`ref/photos/dgsh5-109-009-e3/PXL_20260718_101633062.jpg` close the corrected
interpretation: D94.5 is NC, while D93.1 alone owns a short open stub.

D94.6/D5 is photo-bounded one step further. In
the same exposed-socket frame, uninterrupted front copper reaches the plated
handoff at `(2266,1828)` px. Composing that point through the D93-local and
D94-local cross-side fits gives solder-image candidates near
`(1829.9,1447.5)` and `(1797.7,1491.1)` px, a `54.2` px disagreement. The
annotated `d94-d5-layer-handoff.jpg` records the local handoff. Direct owner
continuity on 2026-07-21 and the exact-revision `.009 E3` drawing now close
D94.6, D94.7, and D94.9 as electrically NC; the photographed departure is a
local floating stub rather than evidence for a remote load.

D93.19 `MR_N` is now owner-closed with D93 removed.
The corrected solder joint reaches a through-hole near `(1743,2320)` pixels;
composing the D93 solder and exposed-socket fits maps that hole to `(950,1909)`
component pixels, where the same trace is visible before it returns beneath
the socket body. Continuity proves D93.19 reaches D13.8 and the outer-bus
rightmost middle-row contact (top view), while D13.9 reaches D1.12 RESET. The
photographs remain useful route evidence. This resolves the former polarity
ambiguity; board-JSON/KiCad/HDL adoption remains pending the routed refresh.

The adjacent D96 КМ555ТМ2 now has a separate component fit with an exact
pin-4 held-out check. Its reflected solder fit identifies the two small-joint
columns left of D28 with a 0.632 px pin-4 check; pins 7-8 extrapolate beneath
the broad rail and are explicitly not electrical evidence. Together the D106,
D28, and D96 fits guard the physical row spacing rather than preserving the
former overlapping placeholder grid. D106.7 remains a physical measurement
request; the trace under its former projection does not establish a joint.

The registered `PXL_20260710_200402344.jpg` serial-area view also corrects an
older placeholder column. The marked notch-down К170УП2 left of R30 is D104;
the two marked notch-up К170АП2 packages right of R30 are upper D32 and lower
D14. Their fitted body centres are `(195.7,38.9)`, `(211.8,29.5)`, and
`(211.8,41.0)` board mm. This removes the impossible former overlaps of R30
with D104.12 and D32.8. `kicad/check_serial_photo_placement.py` composes the raw
photo and board registrations and guards all three centres and orientations.
The former D104 backside fit in `200506061` has been retired. Enlarged source
pixels show that its supposed 2x8 anchors fall on bare copper, open annuli, or
between soldered-joint columns; sub-pixel algebraic residuals did not prove
physical pad identity. The component package placement remains registered,
and direct owner continuity on 2026-07-21 plus the exact `.009 E3` drawing
close D104.10 as NC. A separate D11-local front-to-solder fit now identifies
the D104 two-column solder field and pin16 joint near `(2710,1480)` in
`200506061`, while its rail remains unknown. The old fit's D104.10 copper
claim remains retired. Direct component copper traces D104.7 to
the lower R30 pad. The source model assigns that pad to ground; physical rail
polarity remains a meter check. A panorama cross-check rejects the earlier
D11-based absolute D104 move estimate and flags D11 placement instead. See
`docs/d104-solder-registration-audit.md`.
Both July owner component views agree on D11's top contacts in the panorama
board frame within about 0.66 mm. Four corners from `200358952` centre D11
near `(201.012,71.486)` mm versus the former `(185.500,65.700)` mm in all
three PCBs. The source PCB now uses the photo position; both routed boards
retain the old position. This routed placement hold is separate from the D11-local pixel fit
that registers D104 solder contacts; see
`ref/photos/juku-pcb-2/d11-placement-crossview-audit.json`.
The source correction places D11's broad box at `(192.32,49.68)`–
`(209.70,89.56)` mm. The source PCB has no tracks in that box, but its R18
box starts only about 0.04 mm beyond the trial D11 box. A direct D11-image
cross-check of four R18/R104 joint centers agrees within roughly 1 mm with
their independent D3-local source positions; the broad box includes more
than the visible body clearance. Source KiCad DRC improved from 168 to 165
errors with unchanged 499 unconnected items. Both routed PCBs still put D12
inside the corrected D11 box and carry dense copper through it. Their
placements and routes remain unrepaired.
The same check identifies the marked notch-down К561ЛН2 in
`PXL_20260710_200418174.jpg` as D3 at `(220.434,80.356)` mm. Its former
`(205.8,96.4)` placeholder landed on a cable and physically overlapped D10.
A direct package fit now holds D3.10 and D3.1 out at `0.333` and `2.236` px.
It also calibrates the distinct white-wire surface joint at `(1232,872)` px:
the short uninterrupted tinned departure reaches D3.10, identifying the
D3-side `А:20`/`S_TTL` terminal at `(213.571,78.499)` mm. The remote end is
independently bounded: three component overlaps project A23 beneath the same
mastic-covered wire entry, while two solder overlaps identify A23 as the
third-from-right joint in the twelve-pad row and show no PCB-copper departure.
Together with the factory A20 endpoint map, this proves the shared A20/A23/X3.3
through-hole joint at `(178.780,15.200)` mm rather than inferring it from net
equality alone.

The two populated upright axial resistors left of D3 are labeled R10 (outer)
and R9 (inner) in the exact `.009` assembly view, and sheet 1 gives each 2 kΩ.
The D3-local owner-photo fit locates their lead centers and the source PCB now
places both footprints. R15 is a separate upright body right of D3 and R16
is a horizontal body below D3; their far rail still requires continuity. See
`docs/d6-input-continuity.md` and
`ref/photos/juku-pcb-2/r9-r10-r15-r16-identity-review.json`.

The eight-pin D12 directly above D3 is also registered with the same D3-local
fit. Its visible bottom-right pin-one dot and four corner joints put the DIP-8
center at `(220.73, 63.82)` mm, rotated 180°. The previous `(206.3, 80.9)`
estimate intruded into R10's photographed field. The source PCB now clears both
parts with zero DRC clearance errors; electrical continuity and routed copper
remain separate checks. The corner pixels and image hashes are in
`ref/photos/juku-pcb-2/d12-d3-local-placement.json`.

The horizontal notch-right D95 К555КП12 is also component-fitted. A review of
both photographed rows corrects the earlier row-label error: standard top-view
DIP numbering places pins 1-to-8 on the upper row and pins 16-to-9 on the lower
row. The source PCB now also applies the required 270-degree physical footprint
orientation; the former 90-degree placement had the right centre but reversed
every numbered landing relative to the visible notch. D99 and D101 share that
right-facing posture, while D97/D102 remain left-facing at 90 degrees. The
independent pin-13 check is 0.582 px. D95's solder fit now
correctly selects the right-hand package below the broad rail; backside reversal
places D99 on the left and D95 on the right. The former left-group D95 assignment
is withdrawn. D95's opposite-row pin-1 check is 0.915 px, while D99's independent
pin-1 check is 1.030 px. The separate, upside-down
8812-marked D101 К555КП12 below-left of D95 now has the same physically
consistent registration, with its pin-13 check at 0.755 px. All 16 projected
pads of each mux land on their photographed contacts; their inputs, selects,
enables, and outputs remain explicit FDC continuity questions.

The same original photograph and the factory assembly drawing now identify
the complete two-row cluster: D95/D99 above and D101/D97/D102 below. D97 and
D102 visibly read `К155АГ3 8901`; D99's body and middle pins are cable-covered,
but its two exposed row ends, right-facing notch, and drawing position fix its
identity. Held-out errors are 0.214 px for D97, exactly 0 px at the recorded
precision for D102, and 0.571 px for D99.

The solder-side board edge independently fixes the reversed lower-row order:
D102 is the leftmost physical package, followed by D97 and D101. D102's
single-image solder fit lands all 16 joints and holds opposite-row pin 9 out at
2.531 px; a trial D97 label here was rejected because it would place D102
beyond the physical PCB edge.

Using D102's fitted pitch rather than the displaced global seeds then lands
D97 on the immediately adjacent middle package. Its two solder rows hold
opposite-row pin 9 out at 4.143 px and leave the rightmost package for D101, as
required by the reversed physical order.

The same order and pitch identify D101 as the rightmost lower-row solder
package. Its fitted upper row spans pins 16-to-9 and the independent opposite
pin-1 joint checks the two-row posture at 1.666 px; the former D101 seeds landed on rails
farther right rather than package joints.

Package-local pitch converts shared raw-image offsets directly: D95->D99 is
`(23.895,+0.451)` mm; D95->D101 is `(-11.190,+17.380)` mm; D101->D97 is
`(23.794,-0.117)` mm; and D97->D102 is `(23.963,-0.249)` mm. The visible
right board edge independently constrains the row's absolute x position. The
source PCB guards all four relations; remaining collisions are stale passive
and transistor placements, not IC-to-IC overlaps.

The factory assembly drawing is now locally registered to the same row. D95,
D101, and D102 define an affine fit while D99 and D97 remain held-out checks at
0.910 and 0.851 mm. This fixes the reference identity and physical posture of
vertical C11 between D95/D99 and vertical C15 between D97/D102. Ten more named
passives are projected in `docs/fdc-lower-assembly-placement.md`, but remain
explicit omissions until their packages and `.009` electrical endpoints are
proved.

The upper factory row is handled separately because its three IC centres are
nearly collinear. C12 is interpolated 48.6906% from D94 to D100, and C9 is
56.1111% from D100 to D98; the independent D94-to-D98 line predicts D100
within 1.309 mm. Both capacitors are now vertical at y~34 mm instead of the
former false y~95 mm analog placeholder row. The C12 owner site lacks an
unambiguous body and C9 is cable-hidden, so the inherited analog nets remain
unverified.

The owner component close-up `PXL_20260710_200402344.jpg` puts the
assembly-projected C9 site in the gap between D100 and D98, directly under the
white cable sleeve and black cable. The matching solder close-up
`PXL_20260710_200506061.jpg` exposes the two IC rows and broad supply copper,
but no uniquely paired C9 holes can be assigned from that view. Nearby D98.1
and D98.16 are identified ground and +5 V contacts, respectively; proximity
to those contacts does not establish which C9 lead reaches which rail. C9
population and both physical pad assignments therefore remain open despite
the exact sheet-1 bypass-pair proof. A displaced-cable component photograph or
continuity at an identified C9 lead is needed to close them.

## Promotion rule and remaining work

The D56 local registration has a later correction: the old
`PXL_20260710_200445914.jpg` component anchors at x2865..3050 were on the
adjacent marked D103 К555ИЕ10. The actual D56 К155АГ3 is at x3215..3415.
Its four outer contacts cross-align with the independently fitted reflected
solder columns x807/990 and rows y89/536. The solder pad identity and
D56.1/D56.9 ground promotion therefore survive the component correction;
`ref/photos/juku-pcb-2/d56-fit-correction.json` records the paired evidence.
The neighboring marked D103 К555ИЕ10 now has its own component and reflected
solder fits in the same tiles. Its pins 12, 13, and 14 show separate pad metal
on both faces with no visible copper departure from the joints; the parallel
horizontal solder traces pass between those pad rows. This independently
corroborates the exact-sheet no-connect treatment of the three lower outputs
without assigning a remote net from nearby, unjoined copper.
The separate `33К` body between D103 and D56 has two exposed component-side
landing pools. Cross-side projection from both fitted packages finds no paired
solder annuli under those leads. Its value matches source R59, but the photo
does not establish the physical ref or either rail. The `.009` assembly puts
R59 to D56's right, whereas this body is to its left; it may be relocated or
may be another 33 kΩ part. The single upright body to D56's right spans the
nearby R47/R59 callout levels and has no readable value, so it cannot be
assigned to either reference from position alone. The candidate and lead
coordinates are retained in `ref/photos/juku-pcb-2/r59-candidate-registration.json`.

The D54/D55/D57/X9 area needs local placement fits. Factory assembly
`PXL_20260711_114611058.jpg` puts three КР580ВИ53 timers in top-to-bottom
order D57, D55, D54 beside the long D26 КР580ВВ55А PPI and C84 below D54.
Owner component `PXL_20260710_200455512.jpg` shows the same three marked
timer packages beside the X9 clamp. Approximate raw-pixel body boxes in that
4080×3072 image are D57 `(2775,840)`–`(3500,1170)`, D55
`(2775,1370)`–`(3500,1700)`, and D54 `(2780,1915)`–`(3500,2250)`.
The individual-pad fits are recorded below; these boxes alone locate bodies.
Their approximate vertical
center separations are 530 and 548 pixels. The routed board's corresponding
center separations are 22.60 and 21.80 mm (D57 `y=214.22`, D55
`y=236.82`, D54 `y=258.62` mm in `kicad/juku.dsn`). Both sources therefore
have the same top-to-bottom order and comparable local pitch; this does not
validate the board's absolute position. The marked D26 КР580ВВ55А body in
the same owner tile spans approximately `(1510,1925)`–`(2725,2250)`;
its right edge lies only about 55 raw pixels left of D54's body. Body centers
are about 1020 pixels apart at the same height. Nearby DIP lead pitch is
approximately 62 pixels per 2.54 mm, so that corresponds to roughly 42 mm
and the body gap to roughly 2 mm. KiCad placement coordinates are **pad-1
origins**, not body centers: `pcbnew` gives D26 pad x extent
`207.875..256.135` mm and D54 `260.730..288.670` mm. Their pad-array
centers are therefore `232.005` and `274.700` mm, separated by
**42.695 mm**, consistent with the owner photo. The raw 52.855 mm
pad-1-origin difference must not be interpreted as package-center spacing.
A local pin-center fit alone does not establish absolute board placement.
Applying the archived component-tile/panorama/board homographies to the
four photographed body centers gives coarse board coordinates D26
`(251.64,252.55)`, D54 `(297.28,252.22)`, D55 `(296.97,227.73)`, and
D57 `(296.79,203.87)` mm. The current routed pad-array centers are D26
`(232.005,251.00)`, D54 `(274.700,251.00)`, D55 `(274.900,229.20)`,
and D57 `(274.900,206.60)` mm. All four therefore share an approximate
**+20 to +23 mm x residual**, while that broad fit's y residuals are within
about 3 mm. The direct bottom-edge check below contradicts its y estimate.
The coherent shift explains why the broad D54 projection falls on D26
despite their locally correct separation. A direct same-tile edge check
favors **registration bias**: the visible right board edge is near raw
`x=3920`, about 780 pixels from D54's body center `x≈3140`. At the
nearby DIP lead pitch of roughly 24.4 px/mm, this is about 32 mm from
the edge, implying `x≈278` mm on the 310 mm board, close to the routed
D54 center `x=274.7` mm and far from the panorama's `x≈297.3` mm.
Perspective and body-center uncertainty keep this an approximate check;
it does not establish absolute placement from the local pin-center fit.
The completed local fits permit a more specific edge check. In the owner
component tile, the right board/material transition is near raw x `3908`
at D57 pin-12 y `1190`, `3919` at D55 pin-12 y `1720`, and `3932` at
D54 pin-12 y `2270`; the edge visibly slopes across the three rows.
Each fitted pin-12 center is x `3478`, and the twelve-pin span is
`673` pixels over 11 × 2.54 mm. Taking the routed outline's right edge
as x `310.075` mm gives edge-derived pin-12 x positions of about
`292.2`, `291.8`, and `291.2` mm for D57/D55/D54 respectively. The
routed pin-12 x positions are `288.87`, `288.87`, and `288.67` mm,
giving approximate residuals of `+3.4`, `+2.9`, and `+2.6` mm. This
same-photo check strongly rejects the broad panorama's 20–23 mm shift,
but its local-scale and edge-datum assumptions do not justify moving
the footprints by 2–3 mm. Retain the absolute-placement hold pending
shared board fiducials or direct mechanical measurement.
The same owner tile exposes the physical bottom edge. At D54 pin-1 x
`2805`, its board/material transition is near raw y `2813`; D54's fitted
lower row is y `2270`, and its two lead rows span `360` pixels for the
15.24 mm DIP row spacing. This places the lower row about `23.0` mm above
the photographed edge, or near board y `243.0` if the measured 266 mm
height and rectangular bottom datum apply. The opposing solder tile gives
an independent check: D54's lower row is y `2185`, the bottom edge near
x `1526` is about y `2750`, and the two solder rows span `370` pixels;
that also puts the row about `23.3` mm above the edge (board y about
`242.7`). The routed D54 pin 1 is y `258.62`, only `7.38` mm above
its y `266` outline. Thus both face photos indicate a roughly **15–16 mm
vertical placement conflict** for D54. D55/D57 maintain the photographed
row spacing above it, so their whole column needs a mechanical placement
review. The owner tile also shows a large lower mounting hole near raw
`(1305,2446)`, compatible with the modeled `(199,251.2)` mm hole by its
distance from the photographed bottom edge; it reinforces the bottom-edge
datum. Keep the replica timer/PPI placement on fabrication hold and do not
apply an automatic translation: final coordinates require an explicit
mechanical fit including the bottom edge, mounting holes, and package rows.
The raw edge/pin observations are in
`ref/photos/juku-pcb-2/timer-bottom-edge-registration.json`; run
`/usr/bin/python3 kicad/check_timer_bottom_edge_placement.py` to compare
them with the current PCB. Its generated report is
`docs/photo-registration/timer-bottom-edge-placement.json`.
The same lower strip shows two large board holes on both faces, apart from
X9's two clamp screws. The hole near owner raw `(1305,2446)` corresponds
to the routed Edge.Cuts circle at `(199.0,251.2)` mm. The second hole is
near owner `(3703,2450)` and mirrored solder `(610,2364)`; its right-edge
and bottom-edge offsets put it near `(300.3,250.7)` mm. No Edge.Cuts hole
exists in that lower-right region of the routed PCB. The raw observations
are in the timer bottom-edge registration JSON. Its center and diameter
need a dimensioned mechanical fit before adding a drill; the two-face
photo evidence makes the omission a separate fabrication hold.
Combining the modeled `(199.0,251.2)` mm lower hole, the raw right/bottom
edge observations, and D54's measured pin pitch gives two complementary
component-photo estimates of D54 pin 1: x `262.38` or `263.21` mm and
y `243.75` or `243.01` mm. The within-axis method spreads are `0.83`
and `0.74` mm; perspective, lead-center selection, and hole/edge datum
uncertainty are larger than those spreads. The routed pin is
`(260.73,258.62)` mm. Treat the photo values as a **candidate region near
`x=262–263, y=243–244` mm**, not drill or routing coordinates. The
generated timer bottom-edge report retains each method and its inputs.
The adjacent D26 package independently confirms the **cluster-wide y
conflict**. Its physical lower row is pin 40 in the right-notched owner
orientation; the current left-notched routed footprint uses different pin
numbers on that row, so this comparison uses row position only. Component
and solder D26 rows are `23.029` and `23.066` mm above their photographed
bottom edges, giving board y `242.971` and `242.934` mm. The routed lower
D26 row is y `258.620` mm. Both faces therefore agree with D54's physical
lower row near y `243` and independently show about `15.7` mm of vertical
misplacement. The raw D26 edge points and computed values are included in
the timer bottom-edge registration and report.
Using each photographed timer's own 15.24 mm row spacing to scale the
inter-package gaps, the two faces give D55 pin-1 y estimates `219.730`
and `219.789` mm, and D57 estimates `196.977` and `197.443` mm. Their
routed pin-1 rows are y `236.820` and `214.220` mm: both are about
`17.0` mm lower than the photo estimates. Component/solder disagreement
is only `0.059` mm for D55 and `0.466` mm for D57 at recorded precision.
The method uses local scale interpolation and the D54 bottom-edge datum;
those small face disagreements do not bound perspective or mechanical
landmark error. The report retains the per-face calculations as candidate
placement evidence, with no footprint translation applied.
The reflected solder board edge supplies a separate horizontal check.
At the D57/D55/D54 pin-12 rows, the component-edge estimates are x
`292.148/291.692/291.152` mm and the solder-edge estimates are
`290.518/290.204/290.023` mm. The face-to-face spreads are `1.63/1.49/1.13`
mm, larger than the vertical spreads; perspective and edge selection
matter at this level. The routed pin-12 x positions are
`288.87/288.87/288.67` mm. Both photo faces support only a modest
eastward candidate offset of roughly 1–3 mm, rather than the broad
panorama's 20–23 mm. The raw edge points and per-face arithmetic are in
the timer bottom-edge registration and generated report; no x placement
is accepted for fabrication.
There is a separate orientation conflict: the factory assembly outline in
`PXL_20260711_114611058.jpg` draws D26's notch on its **right** edge,
while all three timers have left-edge notches. The owner component photo
corroborates this: D26's body marking is inverted relative to the timers
and its notch is at the right end. The source `kicad/juku.kicad_pcb`
now places D26 at 270° with a right-edge notch; all three timers remain
at 90°. Both routed variants still place D26 and the timers at 90°, so
their D26 pad numbers and copper endpoints remain on hold. Changing a
routed footprint angle without remapping its copper would be unsafe.
On the current routed PCB, `pcbnew` locates D26 pad 1 at
`(207.875,258.620)` mm (lower left of the horizontal array) and pad 21
at `(256.135,243.380)` mm (upper right). A 180° rotation about the array
center while keeping the same forty holes would put physical pin 1 at
the current pad-21 location and swap each physical pin with the pad numbered
20 higher modulo 40. This is a testable pin-map warning, not yet a copper
correction: a trace/net comparison is needed before remapping copper.
The component and reflected solder 2×20 fits now supply that pin-1
landmark: D26.1 is `(2690,1910)` in
`PXL_20260710_200455512.jpg` and `(1650,1815)` in
`PXL_20260710_200530933.MP.jpg`. All forty projected pad centers align
with the visible contacts; held-out corner errors are 0 and 0.803 px.
The remaining comparison is electrical for ground and signal pins; the
photographed D26.26 power path is traced below.
The opposing solder tile `PXL_20260710_200530933.MP.jpg` crop
`(1400,1850)`–`(3100,2550)` contains the long D26 two-row joint field
adjacent to the timer rows and several broad-rail taps. The routed model
calls D26.7 `GND` and D26.26 `P5V`; these are the two power orientation
controls. The visible taps alone do not prove rail identity.
The fitted D26 physical pin-26 solder location is `(2511,2185)` raw
pixels for the factory right-notch orientation. The joint there has a
wide vertical connection into the lower broad rail. Its tinned path
bends around the screw visible in the same tile, continues through the
overlap with `PXL_20260710_200534267.jpg` using that screw and the
`7.102.158` inscription as landmarks, then continues in overlapping
`PXL_20260710_200537608.jpg` to the third power landing marked `+5V`.
This is a photographed D26.26-to-`+5V` board-landing connection; the
external cable contact is outside this trace. Physical pin 7 is near
`(2019,1815)` and has no comparable solder-face rail in its crop. Its
ground route still needs a front-side trace or continuity measurement.
The factory assembly also draws the other 8255 PPI, D27, with its notch
on the right in `PXL_20260711_114556899.jpg` (the horizontal D27 beside
X2 and D11). `pcbnew` reports D27 at 90° using the same DIP-40 footprint:
its pad 1 is `(127.575,43.320)` mm and pad 21 is
`(175.835,28.080)` mm, so its generated notch faces left too.
The owner D27 is the **horizontal** КР580ВВ55А under X2 in
`PXL_20260710_200358952.jpg`, crop `(1050,1200)`–`(2300,1700)`; its
marking, `8907` code, and right-edge notch are directly readable. Its
approximate body center `(1675,1450)` projects through the broad panorama
to `(162.7,38.4)` mm, versus the routed pad-array center
`(151.705,35.700)` mm. The roughly 11 mm x residual is comparable to
other local panorama bias and does not prove a gross placement error.
The **vertical** КР580ВВ51А marked `8906` in overlapping tiles
`PXL_20260710_200358952.jpg` and `PXL_20260710_200402344.jpg` is D11,
not D27. Earlier D27 placement, top-notch, pin-1, and revision claims
based on that vertical chip are retracted. Both owner PPIs and both
factory PPI outlines are horizontal and right-notched. Their replica
footprints are horizontal but left-notched at 90°; a standard KiCad DIP-40
right-notch orientation would be 270°. Both PPIs now have local pad fits;
both need corrected pad maps and routing before factory-equivalence
can be claimed.
The D27 package-local component and reflected solder fits now cover both
complete twenty-contact rows in
`ref/photos/juku-pcb-2/local-package-registration.json`. The owner
component pin-1 landmark is `(2180,1305)` in
`PXL_20260710_200358952.jpg`; the reflected solder pin 1 is
`(2806,1195)` in `PXL_20260710_200506061.jpg`. Held-out corner errors
are 0 px and 0.452 px respectively. This closes D27 pad identity in the
photographs, while copper connectivity and replica orientation/routing
remain open.
The D27 component fit originally used `x=1215` for the left row ends;
zoomed inspection of all forty lead tips showed its middle projections
were biased left. Those two anchors are corrected to `x=1235` in the
registration. The numerical held-out corner check remained zero under
both choices; an independent interior D27.26 observation at
`(1485,1623)` checks the corrected fit at 1.316 px and rejects the
former fit. The full-row overlay remains the decisive visual check.
The owner D27 tile also exposes the physical top board edge beside X2
near `(2180,737)`, at the same x as physical D27 pin 1 `(2180,1305)`.
With the photographed 318-pixel spacing between the two 15.24 mm DIP
rows, this gives upper-row board y `27.221` mm versus routed y `28.080`
mm. The vertical residual is about `−0.86` mm. The recorded edge point
and checker are `ref/photos/juku-pcb-2/d27-top-edge-placement.json` and
`kicad/check_d27_top_edge_placement.py`. An independent solder-face
measurement in `PXL_20260710_200506061.jpg` puts the top edge near
`(2806,680)` and the registered upper joint at `(2806,1195)`. Its
285-pixel row spacing gives y `27.539` mm, a `−0.66` mm residual to the
routed row and `0.32` mm difference between face estimates. This confirms
the absence of a gross y shift but does not repair the confirmed 20-pin
orientation/net mismatch.
The overlapping top-left tile `PXL_20260710_200354648.jpg` supplies the
missing same-photo x check. The left board edge is near `(170,1120)`,
while physical D27 pins 20 and 1 sit near `(2824,1120)` and
`(3833,1120)`. All twenty projected contacts align in
`docs/photo-registration/d27-left-edge-row.jpg`; the edge mark is in
`docs/photo-registration/d27-left-edge-edge.jpg`. The 1009-pixel span
represents 48.26 mm, placing the left array end at x `126.940` mm,
versus routed x `127.575` mm. This `−0.64` mm local estimate rejects
the broad panorama's apparent 11 mm D27 x shift; perspective and edge
selection still limit exact placement. The raw observations and checker
are `ref/photos/juku-pcb-2/d27-left-edge-placement.json` and
`kicad/check_d27_left_edge_placement.py`.
With the corrected front fit, D27.26 is near `(1484,1623)` in
`PXL_20260710_200358952.jpg`. Its uninterrupted front copper runs to
the plated via near `(1467,1993)` in that tile. The package-local fit
does not identify that via in the opposing solder photo; no +5 V
destination is accepted from the projection alone. The corrected D11
and D27 package corners support a shared homography with about 5 px RMS
landmark error, but its D27.26-via projection near `(3480,1819)` in
`PXL_20260710_200506061.jpg` lies on a trace between vias. The closest
visible via is about 40 px west, beyond the landmark residual; that
candidate remains unassigned.
The current broad
board-to-panorama projection of model D54 `(260.73,258.62)` mm lands near
`(2320,2225)` raw pixels, on the visible PPI body rather than any timer;
D26's model coordinate projects farther left. The broad transform is therefore
unsuitable for assigning timer/C84 pads or validating those placement seeds.
All three timers now have local package fits on both faces. Absolute board
placement still needs validation before changing board coordinates. The
package fits do not establish C84 population or its landing pads.

The opposing solder tile `PXL_20260710_200530933.MP.jpg` shows six
successive twelve-joint rows at approximately raw `y=720, 1090, 1270,
1630, 1815, 2185`, with the timer joints mainly between `x=850` and
`1550`. The approximately 370-pixel separation within each footprint and
180-pixel separation between adjacent footprints pair the rows as
`720/1090` (D57), `1270/1630` (D55), and `1815/2185` (D54). This
supersedes the earlier mistaken pairing of adjacent rows as D57 and D55
24-pad fields. The three-footprint solder-side assignment is supported by
row spacing, mirrored position, and factory order. All three timer packages
are now registered on both faces, with each complete twelve-contact row
aligning to its projected pin sequence. The held-out pin-24 corner differs
by 1.1, 1.9, and 1.1 raw pixels for D57, D55, and D54 solder fits; each
component-side held-out corner is exact to the selected pixel. See
`ref/photos/juku-pcb-2/local-package-registration.json` and the six
`docs/photo-registration/local-packages/D5[457]-*.jpg` overlays. The local
fits do not identify C84's pad pair, timer copper nets, or absolute board
coordinates.
The .009 assembly draws C84 horizontally below D54. July and May owner
component photos both leave that strip bare of a capacitor body; this
does not establish original DNP status. In the July component tile, two
annuli near `(3167,2475)` and `(3496,2475)` project through the D54
local fit near solder holes `(1160,2400)` and `(820,2400)`. They are a
geometric pair only: the left annulus has a continuous front trace to
fitted D54.10/OUT0, so this pair is rejected as the +5 V/GND bypass C84.
Both solder holes also continue on separate narrow routes around X9 without
a visible join to the adjacent wide power rail. Other nearby sites remain
unassigned. A wider owner crop shows an additional annulus `(2988,2475)`
left of the hand mark, with a direct front trace to fitted D54.4/D4; its
pairing with the D54.10 annulus is rejected too. The two-face review is recorded in
`ref/photos/juku-pcb-2/c84-region-review.json`; leave C84 population,
value, and landing nets held pending direct continuity or clearer
component evidence.
The overlapping solder tile `PXL_20260710_200534267.jpg` carries the
same three narrow lower-edge routes onward; one ends at a small via near
the `7.102.158` marking, while the others continue. Panorama alignment
does not uniquely map either C84 candidate hole to that branch. No
identified +5 V or ground destination is established by the overlap.

Use `measurement` when a path still needs continuity, `rejected` for a
disproved read, and `accepted` only with a named reviewer, identified refdes/pin,
matching opposite-side evidence, and a unique destination. Only accepted rows
may support a change to `kicad/juku.board.json`.

The automated seed/review queue is complete. Further work should be targeted,
not another broad projection pass:

1. D96.9-to-D101 input continuity and D96.11-to-D94.2 continuity and D100 pins 9/11; D93.19/.24/.26/.37
   plus raw D93.38/.39 into D28 are now source-closed.
2. Remaining functional pins of D99 and D101. D28/D95/D97/D98/D102/D106 are
   source-closed by the recovered `.009` electrical sheet. D96's section-1
   toggle and exact local section-2 wiring are also closed, while its pin9/pin11
   remote continuations remain the distinct asks in item 1. D96.13 is joined
   to D99.10 at a marked sheet-3 junction; their common sheet-1 source is
   unread. Primary device truth makes the shared `/PRE2`/D2 wiring set-only
   while `/CLR2` is inactive.
   The omitted D97.13, D98.9/.10, and D102.4 pins remain guarded NCs.
3. D94's shared upstream chip-select source and D0 hidden branch. Its five
   address inputs, D1-D3 steering outputs, static NC outputs, and physical table
   are already closed. D30 section B, the D105 WAIT edge handoff, and D41 timing
   boundaries are likewise closed. Direct continuity plus the exact sheet close
   D30.1/.4/.10/.12 and R5 as one D38-driven conductor; there is no remaining
   D30.4 continuity boundary.

`docs/owner-measurement-shortlist.md` is the generated pin-level session list;
`PLAN.md` owns release priority.
