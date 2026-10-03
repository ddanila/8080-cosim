# D99 E12 selector source review

The native `.009 Э3` sheet-3 detail
`ref/photos/dgsh5-109-009-e3/PXL_20260718_101641055.jpg` (SHA256
`86740a80fb494cdb08f4de3a120cab83e4f6638cf5885d4c83418a4a94c881a7`)
draws a three-post selector E12 below D99. The bridge is drawn between posts
2 and 3. D99 section-1 B/pin2 runs to E12 post 2. D99 section-2 Q/pin5
branches at a filled dot to E12 post 1, making Q2 the alternate B1 input.
That same Q2 conductor descends to D100 A7/pin7, whose B7/pin13 output is
labeled `-MOTOR ON` at X4.419. The separately labeled `MOTOR EN (1)` line
from D26.16 enters D99 `/CLR2`/pin11; it does not join D100.7.
The conductor from post 3 goes left, then down through the lower rail bundle
to a filled dot on D93 HLD/pin28's line to D100 A6/pin3. The crossing at
D100 OE_N/pin9 has no dot. Thus the drawn 2-3 setting selects HLD for D99
B1/pin2; post 1 offers Q2/pin5 as the alternate setting. D99 Q2_N/pin12
crosses the Q2 vertical without a junction dot.

The original-board component photo
`ref/photos/juku-pcb-2/PXL_20260710_200418174.jpg` and registered solder
photo `PXL_20260710_200522685.jpg` show D99.2 running to a circular
component-side landing whose projection has no solder-side annulus. That
proves it is not a through-hole via. It does **not** prove D99.2 is electrically
isolated: a front-side branch or an unregistered E12 post remains possible.
No E12 footprint, post coordinates, or installed bridge has yet been proved
on this board.

The exact `.009 СБ` assembly photo `PXL_20260711_114600417.jpg` gives a
bounded physical search region: its native crop `(2100,1900)-(2550,2350)`
prints `1` above `2E12` near drawing pixel `(2400,2120)`, just above C19 and
to the right of D99. The annotation is separate from the schematic's E12
three-post electrical symbol. This assembly crop does not draw three
individually numbered drilled centres or show an installed shunt, and the
owner component corridor is partly covered by the black cable. Treat this as
E12's assembly locality only; register the actual holes and check the shunt
on the owner board before assigning post numbers or asserting the 2–3 choice.
Native owner component crop `(3150,750)-(3770,1520)` of
`PXL_20260710_200418174.jpg` covers the D99-right/C18-C19 corridor suggested
by the drawing. It shows the gray axial body, the resistor group and several
separate open annuli, but no uniquely identifiable three-post shunt; the black
cable covers D99's middle pins and part of the adjacent gap. The mirrored
solder crop `(700,760)-(1150,1180)` of `PXL_20260710_200522685.jpg` likewise
contains package rows and open holes without a distinctive three-post pattern.
These crops bound the first bench search but do not select E12 holes by
proximity to the printed callout.

The source board model now puts D99.2 on `FDC_HLD_TO_D100` with D93.28 and
D100.3, reflecting the drawn E12 2-3 setting. D99.5 is modeled with D100.7
on `D99_Q2_BOUNDARY`, while still feeding unselected E12 post 1. Next unpowered
checks are D99.2 to D93.28/D100.3, D99.5 to D100.7 and the alternate E12 post, and
the installed bridge state. The
grounded D99.3 `/CLR1` still fixes section-1 Q low and Q_N high regardless
of which B1 source the selector uses.
