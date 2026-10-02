# C1 can and footprint review

The exact `.009` assembly view
`ref/photos/dgsh5-109-009-sb/PXL_20260711_114604420.jpg` draws C1
vertically right of R3 and left of D13/D105, with `+` beside its lower lead.
The owner component view
`ref/photos/juku-pcb-2/PXL_20260710_200439607.jpg` shows a fitted metal can
in the same neighborhood. One lead exits each end; its case has `+` near the
lower lead. The marked can is the leading physical C1 identification, while
its numbered pad nets and installed capacitance are still unverified. Exact
electrical sheet 1 specifies a 47.0 nominal for C1 in the reset RC network.

The current source PCB uses `CP_Radial_D5.0mm_P2.00mm` for C1, with 2.00 mm
between pads. That footprint does not represent the photographed opposite-end
lead arrangement. Hold C1 footprint and part selection until the two owner
drill centres are registered. Then confirm the marked lower positive lead's
reset-net identity and choose a matching physical footprint. The nearby R36
trace disappears under a white wire; the photograph does not close it to C1.

Source crops, hashes, and remaining checks are recorded in
`ref/photos/juku-pcb-2/c1-can-polarity-review.json`.
