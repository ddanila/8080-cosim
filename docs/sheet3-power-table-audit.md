# Exact .009 sheet-3 IC power-table audit

Source: `ref/photos/dgsh5-109-009-e3/PXL_20260718_101633062.jpg`, original pixels `(1200,2890)-(2700,3470)`.

Result: **PASS** — 12 fitted devices, 25 table endpoints, checked in board JSON and all three PCB variants; 0 mismatches.

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

This checks source rail assignments and pad net names. It does not prove touching copper or physical-board continuity.
