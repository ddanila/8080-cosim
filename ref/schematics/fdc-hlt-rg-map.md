# D93 HLT and RG source map

The exact-revision `ДГШ5.109.009 Э3` sheet 3 closes the last two anonymous
controller pins. The full-sheet source is
`ref/photos/dgsh5-109-009-e3/PXL_20260718_101633062.jpg`; the factory placement
corroboration is
`ref/photos/dgsh5-109-009-sb/PXL_20260711_114600417.jpg`.

| D93 pin | Sheet-3 disposition | Replica net |
| --- | --- | --- |
| 23 HLT | D99 Q1_N/pin4 reaches HLT on the second-lowest upper rail; the conductor crosses E11 post 1 without a junction | `D99_Q1N_BOUNDARY` (source; physical continuity pending) |
| 25 RG | omitted from the D93 symbol between the explicitly drawn CLK/24 and RCLK/26 paths | `D93_RG_NC` |

The exact `.009` overview `PXL_20260718_101633062.jpg` crop
`(1230,590)-(1640,1350)` corrects the former E11 interpretation. The
HLT/pin23 line arrives from the D99.4 upper rail and passes E11 post 1
without a dot. E11 post 1 itself rises to the **uppermost** long rail,
which has a marked junction at D99 Q2/pin 5; the post-1 vertical crosses
`MOTOR EN` without a dot. This is visible in overview crops
`(1120,500)-(1540,1400)` and `(1850,520)-(3072,1650)`. E11 post 2 runs
to D93 READY/pin32; post 3 continues south
to D28 output pin 6 and the R84 pull-up, visible in the same overview crop
`(580,2400)-(1770,3800)`. The drawn 2-3 bridge selects that READY source.
The old `HLT=READY` claim was a crossing
misread. The E11 placement legend shows its three selector posts. The JSON,
schematic, HDL, and all three PCB pad nets now separate HLT from READY. The
two routed PCBs bypass the former READY pad fanout on F.Cu; D99.4-to-D93.23
remains one unrouted HLT connection in each (DRC 798 violations/56
unconnected items), pending physical continuity and copper routing.

RG is not treated as an unread line. The exact sheet explicitly numbers and
routes the adjacent pins while leaving 25 absent from the drawn package; that
is positive unused-pin evidence for this revision.
