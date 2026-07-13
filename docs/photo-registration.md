# July 2026 photo registration

The durable source records are:

- `ref/photos/juku-pcb-2/registration.json` — image hashes, acquisition order,
  side/mirror state, dimensions, and global transforms;
- `ref/photos/juku-pcb-2/panorama-board-fiducials.json` — reviewed board
  landmarks;
- `ref/photos/juku-pcb-2/local-package-registration.json` — direct package
  anchors and independent checks;
- `ref/photos/juku-pcb-2/endpoints.csv` — original-image endpoint coordinates,
  confidence, reviewer, and disposition.

Panoramas, overlays, and crop atlases are navigation aids. Electrical evidence
always cites an original JPEG coordinate and a reviewed path.

## Current result

All 28 July grid images are registered into a common 310 x 266 mm
component-side coordinate frame, with the solder side mirrored explicitly. The
endpoint table contains 626 reviewed rows:

| State | Rows | Meaning |
| --- | ---: | --- |
| `accepted` | 36 | reviewed pad/path evidence adopted into the board model or preserved as an explicit test landing |
| `measurement` | 590 | pad/path review is inconclusive; continuity or better local evidence is required |

Confidence metadata consists of 363 `local-package-fit`, 241
`registration-only`, and 22 `registration+unique-hole-snap` rows. A hole snap
or accurate pad projection is not electrical evidence by itself.

Accepted paths:

- D2.1/.3/.5/.6/.7 -> D4.1/.3/.5/.6/.7 ->
  `A10/A14/A12/A15/A9`;
- D94.1 -> D93.4 / `FDC_RE_N`;
- D94.2 -> D93.3 / `FDC_CS_N`;
- D94.3 -> D93.2 / `FDC_WE_N`.
- А:17 -> S1.1 / `RES_RC` (dedicated numbered wire landing).
- D98.7 -> А:18 -> S1.2 / `D98_Y3_S1_2`.
- D98.3 -> R94.1 / `D98_Y1_R94` (R94.2 remains unresolved).
- D106.7 `Q3` -> D93.26 `RCLK` / `FDC_RCLK`.
- D95.14 -> R92.2 / `D95_A0_R92`.
- D101.4 -> R92.1 + R99.2 / `D101_D02_R92_R99`.
- R99.1 -> D101.8 / `GND`.

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
Factory intent versus owner-board DNP/removal remains explicit rather than
moving the unrelated generic C63 seed into the IC body/gap.

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

D93.19 `MR_N` remains unresolved, but its boundary is narrower. The corrected
solder joint reaches a through-hole near `(1743,2320)` pixels. Composing the
D93 solder and exposed-socket fits maps that hole to `(950,1909)` component
pixels, where the same trace is visible before it returns beneath the socket
body. The available photographs therefore prove the layer handoff but not the
far reset source.

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
The same check identifies the marked notch-down К531ЛН3 in
`PXL_20260710_200418174.jpg` as D3 at `(220.434,80.356)` mm. Its former
`(205.8,96.4)` placeholder landed on a cable and physically overlapped D10.

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

1. D93 pins 19/24/37/38/39 and D100 pins 9/11; D93.26 RCLK is now closed.
2. Functional pins of D28, D95-D99, D101, D102, and D106.
3. D94 input pins 10-14, enable pin 15, and output D3 first (D4-D7 are
   invariant released but still need copper-fidelity closure), D30 section B,
   D105 WAIT handoff, and D41 timing boundaries.

`docs/owner-measurement-shortlist.md` is the generated pin-level session list;
`PLAN.md` owns release priority.
