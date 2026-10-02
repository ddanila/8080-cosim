# C1 can and footprint review

The exact `.009` assembly view
`ref/photos/dgsh5-109-009-sb/PXL_20260711_114604420.jpg` draws C1
vertically right of R3 and left of D13/D105, with `+` beside its lower lead.
The owner component view
`ref/photos/juku-pcb-2/PXL_20260710_200439607.jpg` shows a fitted metal can
in the same neighborhood. One lead exits each end; its case has `+` near the
lower lead. D13-local registration projects the owner's upper and lower joints
to solder joints near `(3200,822)` and `(3200,1305)` in
`PXL_20260710_200537608.jpg`. The upper joint has an uninterrupted solder-side
strip to registered D13.7/GND. A separate `+` is printed beside the lower
solder joint. Its B.Cu run goes east to about `(3365,1305)`, then south
through visible joints near `(3365,1398)`, `(3365,1460)`, and `(3365,1520)`
in the same solder photo. The sharper overlapping component image
`PXL_20260710_200450127.jpg` puts the three corresponding left contacts at
about `(802,1480)`, `(802,1540)`, and `(802,1600)`. D13-local reflection
projects them within about 10–16 pixels of that solder column. Their bodies
and the exact `.009` assembly identify the rows as R4 `100`, R2 `20K`, and
VD1, top to bottom. C1 positive, R4 left, R2 left, and VD1 left therefore
share one physical copper branch, matching their `RES_RC` source grouping.
This registration does not independently establish the resistor pad numbers or
VD1 polarity. The opposite right contacts are separately visible in the solder
photo: R4 near `(3115,1398)` departs southwest on a thin trace, with a
clear gap before the broad strip joining R2 near `(3115,1460)` and VD1 near
`(3115,1520)`. This reproduces the drawing's local R4 versus R2/VD1
separation. The R4 trace runs southwest and west to an otherwise
unidentified solder contact near `(2380,1440)` in the same image. The R2/VD1
strip descends to the broad east-west trunk near `y≈1600`. The remote identity
of that R4 contact and the trunk rail polarity remain unverified. The factory
assembly independently identifies the nearby vertical green body below R20
as C21. Projecting its lower joint from either July component view misses the
R4 trace endpoint by roughly 40 pixels horizontally, so no C21–R4 join is
promoted; such a join would also conflict with the drawn RESIN-to-ground
C21 branch. See `ref/photos/juku-pcb-2/c21-r4-crossview-review.json`. R3 is the vertical red body partly hidden behind C1 in the
component photo, at the position labelled R3 by the assembly drawing. The
May photo `PXL_20260519_201940304.jpg` independently shows `100` on
that body, agreeing with exact sheet 1. Its actual lead holes cannot be
matched securely in the solder view, so the R3 and off-board S1/A17 branches
still need tracing. The installed capacitance is still unverified. Exact
electrical sheet 1 specifies a 47.0 nominal for C1 in the reset RC network.

The current source PCB uses `CP_Radial_D5.0mm_P2.00mm` for C1, with 2.00 mm
between pads. The photographed solder joints are about 483 pixels apart;
the registered D13 DIP row spacing gives an approximate **20 mm vertical hole
span**. This is a photo estimate, not a fabrication measurement. Hold C1
footprint and part selection until the two owner holes and their board
coordinates are confirmed. Then choose a matching physical footprint. The nearby R36
trace disappears under a white wire; the photograph does not close it to C1.

Transferring the two solder joints through the *current* source-PCB D13 package
frame gives search points near `(18.13,201.37)` mm for C1.2/GND and
`(18.13,221.37)` mm for the marked C1.1/positive end. These coordinates depend
on D13's absolute placement and must be checked against a separate board
registration before changing copper.

Source crops, hashes, and remaining checks are recorded in
`ref/photos/juku-pcb-2/c1-can-polarity-review.json`.
