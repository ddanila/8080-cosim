# R101/R104 and D12 sheet-1 source correction

Status: **SOURCE AND PCB PLACEMENT CORRECTED / ROUTING AND REMOTE CONTINUITY OPEN**

Original-resolution `.009 Э3` sheet 1
`ref/photos/dgsh5-109-009-e3/PXL_20260718_101820818.MP.jpg`, crop
`(2550,1850)–(3072,2650)`, prints **R101 = 120 Ω** from rail A (+5 V)
to board point **21 / PULLUP**. The `.009 СБ` assembly
`PXL_20260711_114556899.jpg` independently labels the horizontal body
under X3 **R101**. Owner component photo `PXL_20260710_200358952.jpg`
shows the populated body beside the printed 21 landing. R101's two PCB
pad nets are `X3_HARNESS_1` and `P5V`.

A separate exact sheet-1 view
`ref/photos/dgsh5-109-009-e3/PXL_20260718_101817644.jpg`, crop
`(1850,1650)–(3050,2550)`, prints **R104 = 470 Ω** from D12 physical
output pin 5 to rail A. The `.009 СБ` assembly labels a distinct vertical
R104 body left of D12. R104 is on
`X2_IRQ0` and `P5V` in the source schematic and PCB. The registered owner
photo `PXL_20260710_200418174.jpg` shows an upright resistor immediately
left of D12, matching that assembly position. The package legend reads
К155ЛА18, and a broad tinned front-face branch joins the resistor's
lower joint to D12.8 (the modeled +5 V supply pin). See
[the D12/R104 photo review](../ref/photos/juku-pcb-2/d12-r104-owner-photo-review.json).
The corresponding solder-side tile `PXL_20260710_200522685.jpg` shows
R104's upper joint joined to D12.5 by a short tinned trace and D12.6/.7
joined by a separate vertical bar. Thus both local R104-to-D12 branches
and the paired `-INT4` gate inputs are photo-closed. The installed
resistance, known +5 V return, X1.114C arrival, and X2.214/D10.IR0
continuation still need owner-board checks.

The D3-local photo fit places R104 beside D12 and R18 separately beside D3.
The source and both routed PCBs retain both footprints. These placements come
from hand-read pixels; confirm the holes and installed values before fabrication.
Coordinates and source controls are in
[the R18/R104 placement review](../ref/photos/juku-pcb-2/r18-r104-footprint-collision-review.json).

Two native owner crops, `200358952` and `200418174`, show **33К** on the
lower R18 body, agreeing with exact sheet-1 R18=33 kΩ. R104's print remains unreadable in the archived component views; its installed
470 Ω value requires an isolated measurement. The displaced nets require routing.
The owner solder tile `PXL_20260710_200522685.jpg` additionally shows
an uninterrupted short bar from R18's lower joint to registered D3.11,
closing that local `SER_TXD` end. The upper R18-to-D12.3 `S_OC` route
still needs physical confirmation: its solder joint departs westward on a
separate run, but that run cannot be followed to D12.3 in the available
registered crop. D12.3 and R18's upper lead depart to separate open holes with no visible local
B.Cu bridge. Their front continuations are body-obscured, so the photos establish
neither a hidden join nor electrical isolation. Test each lead to its hole and
the two branches to each other; the placement review retains the probe coordinates.

The same electrical crop draws the second D12 К155ЛА18 gate explicitly:
X1.114C `-INT4` joins both D12 inputs 6 and 7. D12 open-collector
output 5 joins R104's signal terminal and the conductor to X2.214,
which the model already connects to D10 IR0 and R105. D12 pins 5–7 and
X1.114C carry these nets in the source and both routed PCB variants.
The HDL and synchronization map include the second gate.

The correction does not establish whole-board routed parity or DRC readiness.
Current findings are in [the routed audit](routed-refresh-audit.md) and
[factory-wire fidelity](factory-wire-route-fidelity.md). The
R104 installed value, remote D12/X1 continuity, and rerouting remain
open. The prior routing DSN predates this source correction and must be
regenerated before use.
