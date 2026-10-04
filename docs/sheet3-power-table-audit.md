# Exact .009 sheet-3 IC power-table audit

Source: `ref/photos/dgsh5-109-009-e3/PXL_20260718_101633062.jpg`, original pixels `(1200,2890)-(2700,3470)`.

Result: **PASS** — 12 fitted devices, 25 table endpoints, checked in board JSON and all three PCB variants; 0 mismatches.

## Command

Run from the repository root with KiCad’s `pcbnew` available to the chosen Python.
The command below uses the system Python; adjust its path for your KiCad installation.
The command overwrites this report.

```sh
/usr/bin/python3 scripts/check_sheet3_power_table.py
```

| Ref | Model type | Table pin:rail entries |
| --- | --- | --- |
| `D28` | `LN3_OC_INV` | `7:GND, 14:P5V` |
| `D93` | `VG93_FDC` | `20:GND, 21:P5V, 40:P12V` |
| `D94` | `RE3_PROM_092` | `8:GND, 16:P5V` |
| `D95` | `KP12_MUX` | `8:GND, 16:P5V` |
| `D96` | `TM2_DFF` | `7:GND, 14:P5V` |
| `D97` | `AG3_ONESHOT` | `8:GND, 16:P5V` |
| `D98` | `LP11_BUF` | `8:GND, 16:P5V` |
| `D99` | `AG3_ONESHOT` | `8:GND, 16:P5V` |
| `D100` | `BUF8287` | `10:GND, 20:P5V` |
| `D101` | `KP12_MUX` | `8:GND, 16:P5V` |
| `D102` | `AG3_ONESHOT` | `8:GND, 16:P5V` |
| `D106` | `IE7_CTR` | `8:GND, 16:P5V` |

## Scope boundary

The script checks the 12 fixed references and 25 transcribed endpoints
against board JSON nodes and pad net names in `juku.kicad_pcb`,
`juku_routed.kicad_pcb`, and `juku_routed_candidate.kicad_pcb`.
Model types are displayed, not validated. The source image is cited for
the transcription; its pixels and hash are not checked here.
The audit does not prove copper connectivity or physical-board continuity.
