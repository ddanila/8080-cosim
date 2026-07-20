# July 2026 photo registration

The durable source records are:

- `ref/photos/juku-pcb-2/registration.json` — image hashes, acquisition order,
  side/mirror state, dimensions, and global transforms;
- `ref/photos/juku-pcb-2/panorama-board-fiducials.json` — reviewed board
  landmarks;
- `ref/photos/juku-pcb-2/local-package-registration.json` — direct package
  anchors and independent checks;
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
endpoint table contains 639 reviewed rows:

| State | Rows | Meaning |
| --- | ---: | --- |
| `accepted` | 42 | reviewed pad/path evidence adopted into the board model or preserved as an explicit test landing |
| `measurement` | 591 | pad/path review is inconclusive; continuity or better local evidence is required |
| `rejected` | 6 | two former D94.5-D93.1 claims plus four former R94 endpoint assignments disproved by owner continuity/review |

Confidence metadata consists of 374 `local-package-fit`, 214
`registration-only`, and 22 `registration+unique-hole-snap` rows. Two use
`local-package-fit+continuous-copper`, two use `local-package-fit+visible-gap`, five use
`registration+visible-common-landing`, four use
`registration+unique-joint`, three use `registration+three-lead-identity`, and
nine use `cross-side-registration`. Four `panorama-projected-region`
observations record photo-exhausted regions without pretending that a
projection is pad identity.
A hole snap or accurate pad projection is not electrical evidence by itself.

Accepted paths and owner corrections:

- D2.1/.3/.5/.6/.7 -> D4.1/.3/.5/.6/.7 ->
  `A10/A14/A12/A15/A9`;
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
  current `D98_Y1_R94` model net is rejected. Owner continuity locates actual
  10k R94 above D28, from D28.11/D93.38 to +5 V. The photographed 220-ohm body
  remains unassigned; source-model correction is pending a routed refresh.
- D106.7 `Q3` -> D93.26 `RCLK` / `FDC_RCLK`.
- D95.14 -> R92.2 / `FDC_DDEN` (sheet-identified `FM/MFM`).
- D101.4 -> R92.1 + R99.2 / `D101_D02_R92_R99`.
- R99.1 -> D101.8 / `GND`.
- VT2.1 -> R65.1 / `VIDEO_OUT`; two registered July angles directly expose
  the emitter's shared landing, while an independent May angle identifies the
  yellow three-lead body as VT2 marked `Б / 8901`. The separately drawn C94 is
  obscured, so both C94 endpoints remain explicit measurement boundaries.
- Factory cable point A:3 -> X6.1 / `SOUND_CLAMP`, visibly coincident with VD3.2,
  while the separately insulated A:4 -> X6.2 / `GND`. Both are
  component-side lap joints; X6 itself is bracket-mounted and has no PCB footprint.

R67.2 remains unaccepted but is now precisely photo-exhausted. Its component
joint is registered at `(3321,1698)` in `200418174`; fourteen paired D102 pins
map it to `(916,988)` in `200522685` with sub-pixel residual. Both that image
and the overlapping `200506061` tile show a bare backside trace corner without
a via, so visual coincidence is explicitly not treated as electrical evidence.

The reviewed package fits also corrected the source placement/orientation of
D2, D10, D40, D41, D94, D100, and D98. A D11 solder fit corrects endpoint
coordinates without changing its source placement. At D98.7, the component
fit also identifies the visible white wire-18 lead; the factory wire table
independently closes that off-board path as А:18 to S1:2. A new affine solder
fit corrects a roughly 330 px global-projection displacement and shows that no
PCB copper departs D98.7; both observations are accepted. The tracked routed PCB and Gerber ZIP intentionally remain the
last clean pre-correction snapshot until the whole D94/D100 bus cluster can be
rerouted coherently.

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
the rail-obscured package end. Pin 7 is the one exception now promoted
electrically: its fitted coordinate lies exactly on an uninterrupted slightly
sloped solder trace that reaches the independently fitted D93.26 joint, with no
gap, via, or branch between them. Pins 8-10 remain non-electrical projections.
Separate component and reflected solder fits now land D28 on the
adjacent К155ЛН3, using its unobscured seven-pad column and coherent solder
rows. The component pin-4 check is exact and the solder pin-5 check is 0.010
px. A close audit distinguishes the small fitted solder joints from the larger
adjacent open vias and their trace departures; this prevents D28 from being
conflated with D106, while the cable-hidden component fanout remains a
continuity boundary. D93, D100, and D98 also have useful local fits, but their unresolved
signals remain measurements where copper is obscured or leaves the visible
layer. The D11 solder fit holds both unused corners out at 2.375 px and
localizes the factory-reworked area beside pins 4-6; it does not establish the
obscured bridge endpoints. The D98 solder fit holds pin 16 out at 0 px on the
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
D41/D40 view resolves the factory C63 label location: the inter-package strip
contains no populated capacitor body or coherent drilled axial lead pair.
The image cannot distinguish omission during assembly from later removal, but
both histories establish the exact target population at that callout as absent.
Separately, the component and reflected solder panoramas fit the complete
inherited 4×8 DRAM-decoupler landing grid, including the older C63 landing at
`(176.1,145.6)` mm. C63 is therefore retained as intended schematic
connectivity and marked assembly DNP, with the bare common-artwork footprint
fabricated but no populate-now BOM entry.

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
D9 `К555ИД7` at `(109.923,113.308)` mm; and the black 2x7 package immediately
right is unambiguously marked `КР1533ЛА3`, placing D7 at
`(131.465,113.308)` mm. All three notches face right (270 degrees), their
held-out corner/contact checks are zero-pixel at recorded precision, and the
independent D50/D51 estimates spread only `0.532`, `0.547`, and `0.560` mm,
respectively. This corrects the former metal-D7 attribution and the stale
vertical D8/D9 seeds.

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
checks. The complete mirrored backside row puts the same pin at
`(2989.5,1193.5)` px in `200537608`, with the independent pins 11 and 1 held
to `1.5` px. The component contact has no insulated-wire termination, and the
solder joint has only its ordinary etched departure; no distinct A12 rework
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
`200418174`, and at `(1382,1949)` and `(1214.333,2004.833)` px in solder image
`200522685`. Component held-outs are at most `2.0` px and solder held-outs at
most `0.5` px. Neither factory-link owner pin has an insulated-wire stub at the
package joint, so both require remote-landing searches; A11B is identified
below, while A13B remains pending. Independent
D38/D39 centre estimates spread `1.864` mm and bracket the source D92 centre
within `1.501` mm; that is inside the local photographic uncertainty, so the
existing `(260.005,159.200)` mm centre and 0-degree posture are retained.
`kicad/check_d92_photo_placement.py` guards both-side identity and placement.

The A13 remote search is now bounded on both ends rather than only at D92.
The drawing puts A13A immediately before C95 below D30 and A13B immediately
after D38, before R35. The D13 fit fixes A13A's owner D13.1 at `(1426,906)`
component and `(3051,1193.5)` solder pixels; like D92.1, it has no insulated-wire
termination on either face. Registered component panoramas place the two remote
corridors under the horizontal factory-wire bundle and tied mastic junctions.
The corresponding solder panoramas expose labels 10, 9, 14, 7, and 12, but no
13 or isolated third joint; nearby exposed joints are already assigned to
A8/A9. Both A13 terminals therefore remain null instead of inheriting a joint
by proximity. `kicad/check_a13_factory_wire_boundaries.py` guards the reviewed
regions, owner coordinates, ROE membership, and non-promotion.

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
re-read or direct conductor measurement.

D98 and D94 also bound the horizontal 2x10 D100 КР580ВА87 solder footprint.
An affine fit lands both complete rows in the intervening package and holds
the far pin-20 corner out independently at 1.000 px; D100.9 and D100.11 remain continuity
questions because their visible departures do not reach a second named pad.
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
D96.8 `Q2_N` and D99.2 `B` conductors terminate at visibly separate circular landings;
the overlay explicitly rejects their tempting apparent association. A second,
package-local cross-side transform uses all 16 D99 package holes (maximum fit
residual below 0.001 px) to project those circular endpoints into the solder
photo. Both land on bare substrate immediately above the tinned rail, with no
annulus or continuing copper; they are one-sided test landings, not through-holes.
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

D94.6/D5 is now bounded one step further without assigning a destination. In
the same exposed-socket frame, uninterrupted front copper reaches the plated
handoff at `(2266,1828)` px. Composing that point through the D93-local and
D94-local cross-side fits gives solder-image candidates near
`(1829.9,1447.5)` and `(1797.7,1491.1)` px, a `54.2` px disagreement. The
annotated `d94-d5-layer-handoff.jpg` therefore records the proved handoff and
explicitly rejects a unique solder continuation until continuity or a stronger
cross-side registration is available.

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
former overlapping placeholder grid. D106.7 is promoted only because complete
copper continuity to D93.26 is visible; all other unresolved functional pins
remain measurements.

The registered `PXL_20260710_200402344.jpg` serial-area view also corrects an
older placeholder column. The marked notch-down К170УП2 left of R30 is D104;
the two marked notch-up К170АП2 packages right of R30 are upper D32 and lower
D14. Their fitted body centres are `(195.7,38.9)`, `(211.8,29.5)`, and
`(211.8,41.0)` board mm. This removes the impossible former overlaps of R30
with D104.12 and D32.8. `kicad/check_serial_photo_placement.py` composes the raw
photo and board registrations and guards all three centres and orientations.
The new reflected D104 backside fit uses the complete 2x8 joint field in
`200506061`, with independent pin-9 and pin-10 residuals of `1.000` and
`0.728` px. It places D104.10 at `(2350.714,1249.143)` px, where the joint has
no B.Cu departure; `200509593` independently shows the same isolated backside
joint. Both component overlaps cover the possible F.Cu departure with the
same vertical white wire, so D104.10 remains a targeted continuity request,
not an inferred no-connect. It is modeled as the singleton
`D104_X4_OUT_BOUNDARY`, and the serial placement guard preserves that boundary.
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

## Promotion rule and remaining work

Use `measurement` when a path still needs continuity, `rejected` for a
disproved read, and `accepted` only with a named reviewer, identified refdes/pin,
matching opposite-side evidence, and a unique destination. Only accepted rows
may support a change to `kicad/juku.board.json`.

The automated seed/review queue is complete. Further work should be targeted,
not another broad projection pass:

1. D96.9/.11 sheet-1 continuations and D100 pins 9/11; D93.19/.24/.26/.37
   plus raw D93.38/.39 into D28 are now source-closed.
2. Remaining functional pins of D99 and D101; D28/D95-D98/D102/D106 are
   source-closed by the recovered `.009` electrical sheet, including the
   restored D28.10-.13 interrupt conditioner and explicitly omitted D96.13,
   D97.13, D98.9/.10, and D102.4 NC pins.
3. D94 input pins 10-14, enable pin 15, and output D3 first (D4-D7 are
   invariant released but still need copper-fidelity closure), D30 section B,
   D105 WAIT handoff, and D41 timing boundaries.

`docs/owner-measurement-shortlist.md` is the generated pin-level session list;
`PLAN.md` owns release priority.
