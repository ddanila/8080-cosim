# R101/R104 and D12 sheet-1 source correction

Status: **SOURCE AND PCB PLACEMENT CORRECTED / ROUTING AND REMOTE CONTINUITY OPEN**

Original-resolution `.009 Э3` sheet 1
`ref/photos/dgsh5-109-009-e3/PXL_20260718_101820818.MP.jpg`, crop
`(2550,1850)–(3072,2650)`, prints **R101 = 120 Ω** from rail A (+5 V)
to board point **21 / PULLUP**. The `.009 СБ` assembly
`PXL_20260711_114556899.jpg` independently labels the horizontal body
under X3 **R101**. Owner component photo `PXL_20260710_200358952.jpg`
shows the populated body beside the printed 21 landing. The replica had
previously labeled its existing 120 Ω A:21/X3.1 footprint **R104**.
That footprint and its source-model refdes are now **R101**; its two PCB
pad nets remain `X3_HARNESS_1` and `P5V`.

A separate exact sheet-1 view
`ref/photos/dgsh5-109-009-e3/PXL_20260718_101817644.jpg`, crop
`(1850,1650)–(3050,2550)`, prints **R104 = 470 Ω** from D12 physical
output pin 5 to rail A. The `.009 СБ` assembly labels a distinct vertical
R104 body left of D12. R104 is now on
`X2_IRQ0` and `P5V` in the source schematic and PCB. The registered owner
photo `PXL_20260710_200418174.jpg` shows an upright resistor immediately
left of D12, matching that assembly position. The package legend reads
К155ЛА18, and a broad tinned front-face branch joins the resistor's
lower joint to D12.8 (the modeled +5 V supply pin). See
`ref/photos/juku-pcb-2/d12-r104-owner-photo-review.json`.
The corresponding solder-side tile `PXL_20260710_200522685.jpg` shows
R104's upper joint joined to D12.5 by a short tinned trace and D12.6/.7
joined by a separate vertical bar. Thus both local R104-to-D12 branches
and the paired `-INT4` gate inputs are photo-closed. The installed
resistance, known +5 V return, X1.114C arrival, and X2.214/D10.IR0
continuation still need owner-board checks.

The D3 local photo fit projects this resistor's two joints near
**(213.94, 59.31)** and **(213.94, 69.55) mm** on the replica board. These
are placement targets from hand-read pixels; confirm the hole centers and
installed value before fabrication.

The same fit exposed a former PCB placement error: the old **R18** pad 1 was
at `(214.493,59.559)` mm, almost on the R104 upper site, while the
assembly and owner photo place the distinct R18 body lower beside D3.
Its actual candidate pad centers are `(211.299,70.945)` and
`(211.635,81.049)` mm. R18 was moved and R104 added on all three PCBs.
Two native owner crops, `200358952` and `200418174`, show **33К** on the
lower R18 body, agreeing with exact sheet-1 R18=33 kΩ. The upper R104
body's print is partly hidden by glare and cable, so its installed 470 Ω
value still needs an isolated measurement. The independent `200402344`
overlap repeats the dark R104 print beneath a specular stripe; its last
digit remains unreadable in all three archived component views.
Twenty obsolete trace segments were removed from each routed variant;
the displaced nets still require routing. See
`ref/photos/juku-pcb-2/r18-r104-footprint-collision-review.json`.
The owner solder tile `PXL_20260710_200522685.jpg` additionally shows
an uninterrupted short bar from R18's lower joint to registered D3.11,
closing that local `SER_TXD` end. The upper R18-to-D12.3 `S_OC` route
still needs physical confirmation: its solder joint departs westward on a
separate run, but that run cannot be followed to D12.3 in the available
registered crop. In the full `200522685` tile, D12.3 near `(2723,200)`
departs to an open hole near `(2837,185)`, while R18 upper near
`(3004,363)` departs to a different open hole near `(2803,367)`. No
continuous B.Cu bridge joins those branches locally; test both holes and
their mutual continuity before assigning any remote/front continuation.
The D3-local inverse cross-face fit places their component-side search
regions near `(1370,547)` under D12 and `(1402,721)` at D3's upper edge in
`200418174`. Both front continuations are body-obscured, so the archived
photos cannot establish a hidden F.Cu join or electrical isolation.

The same electrical crop draws the second D12 К155ЛА18 gate explicitly:
X1.114C `-INT4` joins both D12 inputs 6 and 7. D12 open-collector
output 5 joins R104's signal terminal and the conductor to X2.214,
which the model already connects to D10 IR0 and R105. D12 pins 5–7 and
X1.114C have been assigned these nets in the source and both routed PCB
variants. The HDL and synchronization map now include the second gate.

After the footprint correction, both routed variants have zero electrical
shorts, clearances, and track crossings, with 49 unconnected items.
Schematic ERC and source-PCB endpoint parity report zero errors. The
R104 installed value, remote D12/X1 continuity, and rerouting remain
open. The prior routing DSN predates this source correction and must be
regenerated before use.
