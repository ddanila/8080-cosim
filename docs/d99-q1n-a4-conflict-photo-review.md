# D99 Q1_N upper rail: exact .009 source correction

The full `.009 Э3` sheet-3 overview
`ref/photos/dgsh5-109-009-e3/PXL_20260718_101633062.jpg`, original-pixel
crop `(1850,520)-(3072,1650)`, separates the two long rails. D99 Q1_N/pin 4
goes right, rises, and turns west on the rail immediately **above** the
D94.14/D101.7 rail. Its bend is near overview pixel `(2564,689)`; the
D94.14/D101.7 rail is near `y≈725` in that area. The earlier two-tile chase
mistook neighboring rail order for a join and incorrectly claimed
D99.4→D94.14. That claim is retracted. The overview also independently
traces D101 Q0/pin 7 to D94 A4/pin 14; see
`docs/d101-output-tie-photo-review.md`.

The same full overview, crop `(1230,590)-(1640,1350)`, follows that
second-lowest rail west to its descent into D93 HLT/pin 23. The HLT
conductor crosses the nearby E11 post-1 vertical without a dot. E11's
center post instead goes to D93 READY/pin 32; post 3 descends to D28.6 and
R84 as seen in overview crop `(580,2400)-(1770,3800)`. The drawn 2-3
bridge selects that separate READY source. Thus D99.4→D93.23 is a
source-drawn connection, not a D99.4→D94.14 connection. The detailed
frames `PXL_20260718_101637906.jpg` and `PXL_20260718_101641055.jpg`
support the rail geometry, but their folded perspective made the wrong
cross-frame match plausible.

E11 post 1 instead follows the uppermost long rail to the marked D99 Q2/pin 5
junction. Its vertical crosses `MOTOR EN` without a dot; see the overview
crops `(1120,500)-(1540,1400)` and `(1850,520)-(3072,1650)`. This is an
unselected alternate READY input in the drawn E11 2-3 position, not a join
to HLT or to `MOTOR EN`.

The registered target solder image
`ref/photos/juku-pcb-2/PXL_20260710_200522685.jpg`
places D99.4 near `(1124.7,901.4)` and shows no visible local B.Cu departure.
The component view `PXL_20260710_200418174.jpg` places it near
`(3074.9,1061.1)`, matching `ref/photos/juku-pcb-2/endpoints.csv`; the
earlier 3048.9-pixel component projection was displaced. Cable and package
obscure the nearby F.Cu, so the target-board remote route remains unknown.

With D99 removed and power off, check D99.4↔D93.23 directly. The registered
D93.23 solder joint is near `(1554,2279)` in `PXL_20260710_200506061.jpg`;
the D99.4 joint is near `(1125,901)` in the separate `200522685` tile.
An optional D99.4↔D94.14 isolation measurement would corroborate the
distinct source rails; D94.14↔D101.7 is already owner-proved. Keep D99.4
separate from the D94.14/D101.7 island.

The corrected replica model joins D99.4 and D93.23 logically. Both routed
PCBs have D93.23 removed from the READY copper, with a local F.Cu bypass
preserving READY's through route. Their D99.4-to-D93.23 HLT link remains
unrouted: each DRC reports 798 existing violations and 56 unconnected items,
one more open than the preceding READY/HLT model. No new short or clearance
violation is reported for the local bypass.
