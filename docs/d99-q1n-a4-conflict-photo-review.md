# D99 Q1_N upper rail: source and physical route review

The full `.009 Э3` sheet-3 overview
`ref/photos/dgsh5-109-009-e3/PXL_20260718_101633062.jpg`, original-pixel
crop `(1850,520)-(3072,1650)`, separates the two long rails. D99 Q1_N/pin 4
goes right, rises, and turns west on the rail immediately **above** the
D94.14/D101.7 rail. Its bend is near overview pixel `(2564,689)`; the
D94.14/D101.7 rail is near `y≈725` in that area. The overview also independently
traces D101 Q0/pin 7 to D94 A4/pin 14; see
[the D101 output review](d101-output-tie-photo-review.md).

The same full overview, crop `(1230,590)-(1640,1350)`, follows that
second-lowest rail west to its descent into D93 HLT/pin 23. The HLT
conductor crosses the nearby E11 post-1 vertical without a dot. E11's
center post instead goes to D93 READY/pin 32; post 3 descends to D28.6 and
R84 as seen in overview crop `(580,2400)-(1770,3800)`. The drawn 2-3
bridge selects that separate READY source. The source therefore joins D99.4 to D93.23. The detailed
frames `PXL_20260718_101637906.jpg` and `PXL_20260718_101641055.jpg`
support the rail geometry; the full overview establishes the rail order.

E11 post 1 instead follows the uppermost long rail to the marked D99 Q2/pin 5
junction. Its vertical crosses `MOTOR EN` without a dot; see the overview
crops `(1120,500)-(1540,1400)` and `(1850,520)-(3072,1650)`. This is an
unselected alternate READY input in the drawn E11 2-3 position, not a join
to HLT or to `MOTOR EN`.

The registered target solder image
`ref/photos/juku-pcb-2/PXL_20260710_200522685.jpg`
places D99.4 near `(1124.7,901.4)` and shows no visible local B.Cu departure.
The component view `PXL_20260710_200418174.jpg` places it near
`(3074.9,1061.1)`, matching `ref/photos/juku-pcb-2/endpoints.csv`. Cable and package
obscure the nearby F.Cu, so the target-board remote route remains unknown.

With D99 removed and power off, check D99.4↔D93.23 directly. The registered
D93.23 solder joint is near `(1554,2279)` in `PXL_20260710_200506061.jpg`;
the D99.4 joint is near `(1125,901)` in the separate `200522685` tile.
An optional D99.4↔D94.14 isolation measurement would corroborate the
distinct source rails; D94.14↔D101.7 is already owner-proved. Keep D99.4
separate from the D94.14/D101.7 island.

## Model and routing status

The canonical board model joins D99.4 and D93.23 separately from
`FDC_READY` and D94.14/D101.7. These model connections do not establish
original-board continuity or routed copper completion. Current routing
holds and DRC totals belong in [factory-wire fidelity](factory-wire-route-fidelity.md)
and [the routed audit](routed-refresh-audit.md).

```sh
python3 kicad/check_d99_source_paths.py
python3 kicad/check_d93_hlt_rg.py
```
