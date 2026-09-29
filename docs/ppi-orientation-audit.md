# PPI physical orientation audit

Status: **HOLD** for both routed variants; source PCB orientation corrected.

The factory `.009 СБ` assembly views and owner board photos agree on the two
8255 packages. D27 is horizontal under X2, with a right-edge notch: factory
`PXL_20260711_114556899.jpg`; owner
`PXL_20260710_200358952.jpg` crop `(1050,1200)`–`(2300,1700)`, marked
`КР580ВВ55А` and `8907`. D26 is horizontal beside D54/D55/D57, also
right-notched: factory `PXL_20260711_114611058.jpg`; owner
`PXL_20260710_200455512.jpg`, marked `КР580ВВ55А` and `8907`.

The vertical chip near X2 previously called D27 in this audit is **D11**.
The overlapping owner tiles `PXL_20260710_200358952.jpg` and
`PXL_20260710_200402344.jpg` both show its `КР580ВВ51А` 8251 USART
marking and `8906` date code. Its existing local registration places a
fourteen-pad solder row at `x≈2705`, `y=1610..2211` in
`PXL_20260710_200506061.jpg`. Cross-aligning the D11 and D27 two-face
landmarks exposed the former D11 solder row selection four joints too
high: a shared homography gave about 58 px RMS error before correction
and about 5 px afterward. The lower fourteen-row field also terminates
above the broad rail. Earlier claims that owner D27 is vertical,
that its position differs by roughly 45 mm from the factory drawing, or
that a D27-specific revision must explain that difference are **retracted**.
Those calculations used D11's photograph as D27 evidence.

An independent 2026-09-27 `pcbnew` read found D26 and D27 at 90° in all three
board files, with identical pad centers and nets for pins 1, 7, 26, and 27.
The source generator and `juku.kicad_pcb` were then changed to 270° while
preserving both package centers. This puts the right-edge notch and numbered
pads at the photographed ends. An isolated source-board trial and the applied
board both retain 173 error-level DRC violations and 499 unconnected items,
the same counts as the pre-rotation source board. The two routed variants
still carry the old orientation and copper; their repair requires local
rerouting, not a footprint rotation alone.
The generated `docs/ppi-physical-pin-mapping.json` now checks the notch
orientation in all three PCB variants while retaining the complete 40-pin
hole/net permutation for the routed board. This prevents an ERC/parity pass,
which checks net names but not package orientation, from being mistaken for
physical pin correctness.

A disposable routed-board trial rotated both footprints at their existing
centers. Error-level DRC rose from 176 existing courtyard/hole violations
and 54 unconnected items to 524 violations and 132 unconnected items. The
added electrical findings were 160 shorts, 20 clearances, and 8 hole
clearances; the trial also showed 160 solder-mask bridges. Running the
source-aware copper salvage on that trial removed 176 conflicting migrated
tracks/vias in one round and cleared the electrical blockers, but left 153
unconnected items. This identifies the scope of the reroute. Neither trial
board was adopted: both routed project boards retain the lower-open baseline
until the package fanouts can be rebuilt against the corrected physical pins.

The current routed PCBs place both D26 and D27 at 90° using
standard DIP-40 footprints. In this KiCad convention 90° makes a horizontal
body with a **left-edge** notch. Both photographed 8255 packages and both
factory outlines have **right-edge** notches. Their body axes and coarse
neighborhoods agree with the drawing; their footprint orientation and
physical pin-to-hole mapping remain on hold. On the current routed D26
footprint, pad 1 is `(207.875,258.620)` mm and pad 21 is
`(256.135,243.380)` mm. Rotating the package 180° while preserving its
forty-hole array would exchange physical pin numbers by 20. D27 has the
same DIP-40 orientation issue; its current pad 1 is
`(127.575,43.320)` mm. Simply rotating the routed footprints would
invalidate their existing copper connections.
The generated `docs/ppi-physical-pin-mapping.json` applies that exact
20-position permutation to the current routed PCB. **All 40 of 40 pin
locations on each PPI carry a different net** from the net intended for
the photographed physical pin. On both devices, photographed pin 7/GND
falls at the current pad 27/DB7 hole, while pin 26/+5 V falls at the
current pad 6/CS_D26 or CS_D27 hole. This is a concrete copper-equivalence
failure, not merely a silkscreen notch difference. Reproduce it with
`/usr/bin/python3 kicad/report_ppi_physical_pin_mapping.py`.

The actual D27 owner body center is roughly raw `(1675,1450)` in
`PXL_20260710_200358952.jpg`. The archived broad panorama fit maps it
near `(162.7,38.4)` mm in the board frame, compared with routed D27's
pad-array center `(151.705,35.700)` mm. This roughly 11 mm x residual is
comparable to the nearby D94 broad-fit bias and is **not** evidence of a
gross D27 placement error. Exact board coordinates still need a local
registration from photo pads to board landmarks. The same broad fit puts
the D26/timer cluster about 20–23 mm east of
its routed centers, but a raw board-edge/pin-pitch check puts D54 near
x≈278 mm, close to its routed x=274.7 mm; this is a separate panorama
registration bias in x, not proof that the whole cluster moved east.
The direct bottom-edge check in `docs/photo-registration.md` separately
places the photographed D26 lower row near y `243` mm while the routed
lower row is y `258.62` mm, a roughly 15.7 mm vertical placement conflict.
An isolated source-board placement trial shifted D26 by −15.67 mm and the
adjacent D54/D55/D57 timers by about −15 to −17 mm to match those photo-row
estimates. DRC rose from 173 errors to 248, including 12 new shorts and
6 new clearances. In particular, translated D57 pads overlap D33, D56,
C8, and D103; D26's courtyard overlaps R49. The trial is not a viable
placement update by itself. A local fit must reconcile the whole lower-right
cluster and its passives before the y correction is applied to the source or
routed board.
D27 has a separate same-tile vertical check: the physical top edge is
exposed beside X2 near raw `(2180,737)`, directly above the registered
physical pin-1 row `(2180,1305)`. The two D27 rows span 318 pixels for
15.24 mm, placing the photographed upper row at y `27.221` mm. The routed
upper row is y `28.080` mm, an approximately `−0.86` mm residual. See
`ref/photos/juku-pcb-2/d27-top-edge-placement.json` and the generated
`docs/photo-registration/d27-top-edge-placement.json`. This rules out a
gross vertical D27 shift at photo accuracy. The independent solder tile
`PXL_20260710_200506061.jpg` gives upper-row y `27.539` mm from its
own top edge, only `0.32` mm from the component-face estimate. The
overlapping top-left
owner tile `PXL_20260710_200354648.jpg` exposes the physical left edge
and D27's complete upper 20-contact row in one image. Its pin-20/pin-1
centers are near x `2824/3833`, and the left edge is near x `170` at
that row. The measured 1009-pixel span over 48.26 mm gives a photographed
left array end x `126.940` mm versus routed x `127.575` mm, an approximate
`−0.64` mm residual. See `ref/photos/juku-pcb-2/d27-left-edge-placement.json`,
its generated report, and the row/edge overlays under
`docs/photo-registration/`. This rules out a gross horizontal shift too;
exact placement and the physical pin-net mapping remain held.

The package-local fits in
`ref/photos/juku-pcb-2/local-package-registration.json` now identify
**all forty D27 pad centers** on both faces. In the component tile above,
the right-edge notch puts pin 1 at `(2180,1305)` raw pixels; pins 20, 21,
and 40 are `(1235,1305)`, `(1235,1623)`, and `(2180,1623)`. In the
opposing solder tile `PXL_20260710_200506061.jpg`, reflection puts those
corners at `(2806,1195)`, `(3707,1195)`, `(3707,1480)`, and
`(2806,1480)` respectively. The overlaid 2×20 grids align with every
visible lead tip; the independent fourth-corner check is 0 px on the
component affine fit and 0.452 px on the reflected solder fit. The
mirrored X2 connector and adjacent registered D11 field confirm the row
assignment. These fits establish pad identity, not copper connectivity or
absolute board coordinates. The old D11 solder registration must not be
repurposed as D27 pad evidence.
The earlier D27 component fit used `x=1215` for its two left corners.
It passed the four-corner calculation while projecting the middle pads
left of their visible leads. Full-row overlay inspection corrected both
left corners to `x=1235`. An independently observed interior D27.26
lead at `(1485,1623)` now checks the corrected fit at 1.316 px; it
would reject the old fit. A corner residual alone cannot detect a shared
anchor bias.

The corrected D27.26 component lead is near `(1484,1623)` in
`PXL_20260710_200358952.jpg`. A continuous narrow front-side trace
leaves that lead, runs south, and ends at a plated via near
`(1467,1993)` in the same tile. This closes the visible front-side
segment of the VCC pin. The via's solder-side identity and onward
destination remain open: projecting it from the package fit into
`PXL_20260710_200506061.jpg` does not land on a unique matching via.
After correcting D11's solder fit, a shared eight-corner D11/D27
homography has about 5 px RMS landmark error and projects this via near
`(3480,1819)` on the solder face. That point lies on a trace **between**
visible vias; the closest candidate is roughly 40 px west. Extrapolation
from the IC pads is insufficient to select it, so the transform must not
be used as a cross-photo copper connection.
An enlarged full-resolution solder crop `(3400,1740)–(3620,1900)` likewise
shows no distinct drilled landing at the projected point. The nearest west solder annulus around `(3438,1811)` is about 43 px from
the projection. Inverting the same eight-corner homography puts it near
`(1511,1988)` on the component face, which is visibly bare board about
44 px east of the actual front via `(1467,1993)`. Retire that annulus as
a D27.26 photo match or targeted probe; the solder landing is still open.
See `ref/photos/juku-pcb-2/d27-pin26-via-review.json`.

D26 likewise has complete package-local 2×20 fits on both faces. Its
component photo `PXL_20260710_200455512.jpg` places pins 1, 20, 21,
and 40 at `(2690,1910)`, `(1550,1910)`, `(1550,2270)`, and
`(2690,2270)` raw pixels. The reflected solder photo
`PXL_20260710_200530933.MP.jpg` puts them at `(1650,1815)`,
`(2819,1815)`, `(2819,2185)`, and `(1650,2185)`. The fourth-corner
check is 0 px on the component affine fit and 0.803 px on the solder
similarity fit; the overlays align across both complete rows. Fitted
physical pin 26 lies near `(2511,2185)` on the solder face, at a visible
wide vertical copper tap into the lower broad rail. The trace can be
followed from that joint through the broad bend around the nearby
mounting screw in `PXL_20260710_200530933.MP.jpg`, across the same
screw and `7.102.158` inscription in overlapping
`PXL_20260710_200534267.jpg`, then past that inscription in
`PXL_20260710_200537608.jpg` to the **third of four power landings**, whose
mask label reads `+5V`. This closes the photographed D26.26 to marked
`+5V` landing on the solder layer and independently supports the
right-notch pin sequence. It does not by itself verify the cable contact
or every branch of the supply rail. Pin 7, the 8255 ground pin,
projects near `(2019,1815)`; its ground path remains untraced.
An enlarged two-face review at that exact pin is recorded in
`ref/photos/juku-pcb-2/d26-pin7-ground-chase.json`. The solder joint sits
between two bright horizontal traces without a visible join to either;
the exposed component lead similarly has no uniquely followable outward
branch among the adjacent fine traces. A continuation beneath the package
is possible. Direct continuity from D26.7 to an independently marked
ground landing is required; the neighboring bright traces must not be
promoted as its ground route.
The older owner component view `PXL_20260519_201907078.jpg` independently
shows the full D26 lead row from a different angle. Counting from its
right-notch end again finds no exposed outward branch at the seventh
contact while adjacent contacts carry visible traces. That view has no
independent pin-center fit, so it corroborates the visual limit without
closing the hidden under-package route.

D27 physical pin 7 has a separate two-face hold. Its package-local fits put
the lead near `(1882,1305)` in component photo `200358952` and the matching
solder joint near `(3091,1195)` in solder photo `200506061`. At full
resolution neither face exposes a trace from that pin to the nearby bright
conductors or broad rail; a route under the body remains possible. The 8255
pin contract calls pin 7 GND, but the photographed copper path needs direct
continuity to an independently marked ground landing. See
`ref/photos/juku-pcb-2/d27-pin7-ground-chase.json`.

To close this gate, verify D26.7 ground and D27's power and selected
signal routes
against the `.009` electrical drawing and the photographed copper, then
correct the footprint orientations with associated pad identities and
copper routing. Repeat electrical DRC, zero-open,
source-pad parity, and visual package checks on the resulting boards. Set
this status to **READY** only after the corrected routed PCB has been
independently reviewed.
