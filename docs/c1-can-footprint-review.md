# C1 can and footprint review

The exact `.009` assembly view
`ref/photos/dgsh5-109-009-sb/PXL_20260711_114604420.jpg` draws C1
vertically right of R3 and left of D13/D105, with `+` beside its lower lead.
The owner component view
`ref/photos/juku-pcb-2/PXL_20260710_200439607.jpg` shows a fitted metal can
in the same neighborhood. One lead exits each end; its case has `+` near the
lower lead. The [C1 polarity review](../ref/photos/juku-pcb-2/c1-can-polarity-review.json)
records the D13-local registration and visible copper:

- The upper joint joins D13.7/GND.
- The marked lower positive joint shares a branch with the left contacts of
  R4, R2, and VD1, consistent with the source `RES_RC` grouping.
- The opposite R4 contact is separate from the shared R2/VD1 strip and
  photo-traces to C21's lower physical lead. Remote D13.5 continuity,
  resistor pad numbering, VD1 polarity, and the R2/VD1 strip's supply polarity
  remain unverified.

The [reset series-branch guide](reset-c21-r20-source-correction.md) covers
C21/R20 topology and routed repair. The evidence review retains pixel waypoints and cross-face fit residuals.

R3 is the vertical red body partly hidden behind C1 in the
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
