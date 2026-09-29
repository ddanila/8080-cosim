# Exact .009 power-table PCB pad parity

Sources: sheet-1 `PXL_20260718_101827714.jpg`, sheet-2 `PXL_20260718_101927794.jpg`, and sheet-3 `PXL_20260718_101633062.jpg` in `ref/photos/dgsh5-109-009-e3/`.

Result: **PASS** — 87 sheet-1, 108 sheet-2, and 25 sheet-3 adopted table entries; 208 unique package pads after overlap, 0 conflicting source assignments.

| PCB | Matching pads | Mismatches |
| --- | ---: | ---: |
| `juku.kicad_pcb` | 208 | 0 |
| `juku_routed.kicad_pcb` | 208 | 0 |
| `juku_routed_candidate.kicad_pcb` | 208 | 0 |

This checks adopted table entries against pad net names in the saved PCB files. Sheet-1 D104.16 and sheet-2 ИР16/РУ4 conflicts remain outside the adopted entry sets. The reports for each sheet document those limits. Pad names do not establish track contact or original-board continuity.
