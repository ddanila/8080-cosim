# D93 controller reset and static-pin map

Status: **EXACT-REVISION CONNECTIVITY ADOPTED / RESET POLARITY BENCH CHECK**

The recovered `ДГШ5.109.009 Э3` sheets close three formerly isolated
КР1818ВГ93 pins from primary evidence.

| D93 pin | Sheet evidence | Adopted net |
| ---: | --- | --- |
| 19 `MR` | Sheet 1 drives `RES (3)` from D13.6; sheet 3 continuation `(1) -RES` lands directly on pin 19 | `RESET` |
| 22 `TEST` | Sheet-3 detail draws a local U-shaped conductor directly to pin 33 | `D93_TEST_WF_VFOE` |
| 33 `WF/VFOE` | Same two-endpoint local conductor to pin 22; no third junction is drawn | `D93_TEST_WF_VFOE` |

Primary frames are
`ref/photos/dgsh5-109-009-e3/PXL_20260718_101801729.jpg` for the sheet-1
reset source and `PXL_20260718_101637906.jpg` for the sheet-3 destinations.
The overview independently preserves the same paths.

The reset drawing has an electrical-annotation tension that connectivity alone
does not resolve: sheet 1 names the D13.6/CPU-reset conductor `RES`, while
sheet 3 prints `-RES` beside a bubbled controller input. The replica therefore
preserves the factory conductor exactly but does not use this ambiguity to
change the already guarded behavioral FDC reset sense. Scope D13.6 and D93.19
during reset before physical drive bring-up.

Automatic guards:

```sh
python3 kicad/check_d93_static_paths.py
sync/check.sh
```

The first guard fixes the board-JSON and HDL endpoint contract. The second
round-trips the generated KiCad schematic and proves structural LVS, including
the shared TEST/WF-VFOE net and the D93.19 branch on `RESET`.
