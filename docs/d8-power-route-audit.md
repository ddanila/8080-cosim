# D8.16 +5 V route audit

The routed-board D8 PROM has pin 16 at `(92.222,117.118)` mm, named `P5V`
but without a same-net track endpoint. Both routed variants have the same
local copper geometry and five remaining named conventional supply pads
without track endpoints (`D2.8/.16`, `D52.8/.16`, and `D8.16`).

The nearest **existing P5V copper endpoint** in the routed board is R12.1 at
`(73.500,104.810)` mm, 22.405 mm from D8.16. The next local P5V branch is
D9.16 at `(118.813,117.118)` mm, 26.591 mm away. D2.16 lies 19.402 mm away
at `(77.630,129.905)` mm and is named P5V, but its supply copper is also
missing, so connecting those two pads alone would not close the rail.

Nearby signal copper constrains a direct feed: `BA5` passes to the east on
F.Cu near `(94.000,117.000)`, while `DB7` passes west of the pad on B.Cu
near `(91.125,116.875)`. The local F.Cu ground line from
`(88.725,121.625)` to `(102.550,112.875)` is another crossing to account
for when routing toward D9. The +5 V feed should therefore be designed with
the remaining D2 supply routing rather than inferred from pad proximity.

These distances and nets come from the current
`kicad/juku_routed.kicad_pcb` track and pad geometry. They establish the
replica routing problem; they do not prove original-board copper. Confirm
owner-board D8.16 and D2.16 to a known +5 V point with power off before
claiming physical continuity.
