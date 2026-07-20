# FDC clock-mux source map

Status: **REVIEWED PRIMARY-SOURCE TRANSCRIPTION / SOURCE MODEL ALIGNED**

Recovered `ДГШ5.109.009 Э3` sheet 3 closes every functional pin of D95
К555КП12. D95 is the dual clock selector for the ВГ93 controller and the ИЕ7
read separator; it is no longer an owner-continuity boundary.

## Exact circuit

| D95 section | Select `A1:A0` | Input selected | Source rail | Output |
| --- | --- | --- | --- | --- |
| A / pin 7 | `00` | D00 / pin 6 | 1 MHz, D40 Q3/pin 11 | D93 CLK/pin 24 |
| A / pin 7 | `01` | D01 / pin 5 | 1 MHz, D40 Q3/pin 11 | D93 CLK/pin 24 |
| A / pin 7 | `10` | D02 / pin 4 | 2 MHz, D40 Q2/pin 12 | D93 CLK/pin 24 |
| A / pin 7 | `11` | D03 / pin 3 | 2 MHz, D40 Q2/pin 12 | D93 CLK/pin 24 |
| B / pin 9 | `00` | D10 / pin 10 | 8 MHz, D40 Q0/pin 14 | D106 DOWN/pin 4 |
| B / pin 9 | `01` | D11 / pin 11 | 4 MHz, D40 Q1/pin 13 | D106 DOWN/pin 4 |
| B / pin 9 | `10` | D12 / pin 12 | 4 MHz, D40 Q1/pin 13 | D106 DOWN/pin 4 |
| B / pin 9 | `11` | D13 / pin 13 | 4 MHz, D40 Q1/pin 13 | D106 DOWN/pin 4 |

The common select inputs are `A0`/pin 14 = `FM/MFM` from D26 PC4/pin 13
(also D93 DDEN/pin 37) and `A1`/pin 2 = `5″/8″` from D26 PC3/pin 17. Both
active-low enables, pins 1 and 15, are grounded. Registered target copper also
places R92.2 on the pin-14 `FM/MFM` node; R92 carries that control toward the
separate D101 precompensation mux input.

The literal level mapping is `5″/8″=0` -> controller 1 MHz and
`5″/8″=1` -> controller 2 MHz. The separator receives 8 MHz only at
`FM/MFM=0`, `5″/8″=0`; every other combination selects 4 MHz. The drawing
does not annotate the software-level meanings beyond those signal names, so
the model preserves the levels without inventing a mode convention.

## Evidence hierarchy

| Drawing region | Primary frame | SHA256 |
| --- | --- | --- |
| D95 inputs, selects, enables, and D93 CLK output | `ref/photos/dgsh5-109-009-e3/PXL_20260718_101637906.jpg` | `ba6f618ea610f05617cde668660a767c103116bcd55f46862a36cbe385ee26e4` |
| D95 output-B continuation into D106 pin 4 | `ref/photos/dgsh5-109-009-e3/PXL_20260718_101644861.jpg` | `8b8ad8abdf5cdf8c235cc942592ebe6c0019ec8ad90ae9958267fbc154bb0e67` |
| Independent whole-sheet topology check | `ref/photos/dgsh5-109-009-e3/PXL_20260718_101633062.jpg` | `5f58dff9c2e1f8237f1c54e44a7ff5db2381b7c503d5e25466fcd219915f7047` |

The sheet-2 1 MHz rail had already been source-closed as `LATCH_B`; D40's
other counter taps were already traced at pins 12, 13, and 14. This
transcription therefore extends existing clock conductors and does not invent
new oscillator sources. `kicad/check_fdc_clock_mux.py` guards the complete
board-JSON mapping, retired boundary names, structural HDL mux, and LVS map.

The complete D106 digital contract is now transcribed separately in
`fdc-recovery-counter-map.md`. Exact analog timing at D93/D106 remains a
bring-up boundary: closing the clock conductors does not claim measured edge
rate, duty cycle, oscillator accuracy, or separator lock margin.
