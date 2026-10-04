# D93 HLT and RG source map

The exact-revision `ДГШ5.109.009 Э3` sheet 3 establishes the HLT connection
and RG disposition. The full-sheet source is
`ref/photos/dgsh5-109-009-e3/PXL_20260718_101633062.jpg`; the factory placement
corroboration is
`ref/photos/dgsh5-109-009-sb/PXL_20260711_114600417.jpg`.

| D93 pin | Sheet-3 disposition | Replica net |
| --- | --- | --- |
| 23 HLT | D99 Q1_N/pin4 reaches HLT on the second-lowest upper rail; the conductor crosses E11 post 1 without a junction | `D99_Q1N_BOUNDARY` (source; physical continuity pending) |
| 25 RG | omitted from the D93 symbol between the explicitly drawn CLK/24 and RCLK/26 paths | `D93_RG_NC` |

The exact `.009` overview `PXL_20260718_101633062.jpg` crop
`(1230,590)-(1640,1350)` shows the E11 crossing. The
HLT/pin23 line arrives from the D99.4 upper rail and passes E11 post 1
without a dot. E11 post 1 itself rises to the **uppermost** long rail,
which has a marked junction at D99 Q2/pin 5; the post-1 vertical crosses
`MOTOR EN` without a dot. This is visible in overview crops
`(1120,500)-(1540,1400)` and `(1850,520)-(3072,1650)`. E11 post 2 runs
to D93 READY/pin32; post 3 continues south
to D28 output pin 6 and the R84 pull-up, visible in the same overview crop
`(580,2400)-(1770,3800)`. The drawn 2-3 bridge selects that READY source.
The E11 placement legend shows its three selector posts. The canonical model
keeps HLT separate from READY. Source connectivity does not establish
original-board continuity or routed copper completion; current routing holds
and DRC totals are recorded in
[factory-wire fidelity](../../docs/factory-wire-route-fidelity.md).

RG is not treated as an unread line. The exact sheet explicitly numbers and
routes the adjacent pins while leaving 25 absent from the drawn package; that
is positive unused-pin evidence for this revision.

## Model guard

Run from the repository root with Python 3 (standard library only):

```sh
python3 kicad/check_d93_hlt_rg.py
```

The guard checks the D99.4–D93.23 HLT net, separation from D93.32 READY,
the singleton D93.25 RG net, retired boundary names and literal HDL connection
markers. It does not check source-photo hashes, the complete E11 selector,
physical continuity or routing.
