# Exact .009 power-table PCB pad parity

Sources: sheet-1 `PXL_20260718_101827714.jpg`, sheet-2 `PXL_20260718_101927794.jpg`, and sheet-3 `PXL_20260718_101633062.jpg` in `ref/photos/dgsh5-109-009-e3/`.

Result: **PASS** — 87 sheet-1, 108 sheet-2, and 25 sheet-3 adopted table entries; 208 unique package pads after overlap, 0 conflicting source assignments.

## Command

Run from the repository root with KiCad’s `pcbnew` available to the chosen Python.
The command below uses the system Python and overwrites this report.

```sh
/usr/bin/python3 scripts/check_009_power_table_pad_parity.py
```

| PCB | Matching pads | Mismatches |
| --- | ---: | ---: |
| `juku.kicad_pcb` | 208 | 0 |
| `juku_routed.kicad_pcb` | 208 | 0 |
| `juku_routed_candidate.kicad_pcb` | 208 | 0 |

Sheet-1 and sheet-2 entries are selected by the current board JSON chip types;
sheet-3 entries use a fixed reference list. This check imports those
transcriptions without running the individual sheet audits. It does not
validate JSON rail nodes, enforce the full chip census, or hash the images.

The [sheet-1 audit](sheet1-power-table-audit.md) documents the excluded
D104.16 conflict; the [sheet-2 audit](sheet2-power-table-audit.md) documents
the excluded ИР16/РУ4 columns. The [sheet-3 audit](sheet3-power-table-audit.md)
also checks its fixed endpoints against JSON rail nodes. Pad net names
do not establish track contact or original-board continuity.
