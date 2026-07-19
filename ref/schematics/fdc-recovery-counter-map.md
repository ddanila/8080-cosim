# FDC recovery-counter map

This is the reviewed transcription of D106 (К555ИЕ7 / 74LS193) from
ДГШ5.109.009 Э3 sheet 3. It replaces the earlier topology-based meter-probe
candidates with primary-source connectivity.

| Function | Sheet-3 endpoints | Board model |
| --- | --- | --- |
| preset and unused up clock high | R78.1, D106.1 D1, D106.5 UP, D106.9 D3, D106.10 D2, D106.15 D0 | `D106_PRESET_HIGH` |
| pull-up supply | R78.2, +5 V | `P5V` |
| recovery clock | D95.9, D106.4 DOWN | `FDC_SEPARATOR_CLOCK` |
| asynchronous preset load | D97.4 /Q, D93.27 RAW READ, D106.11 /LOAD | `FDC_RAW_READ` |
| clear inactive | D106.14 CLR, ground | `GND` |
| recovered-count output | D106.7 Q3, D28.9 | `SEP_D106_Q3` |
| explicitly undrawn | D106.2 Q1, D106.3 Q0, D106.6 Q2, D106.12 /CO, D106.13 /BO | no-connects |

R78's electrical role is explicit, but its value, body, and physical placement
are not readable in the recovered source set. It therefore remains a
placement-pending, circuit-review BOM item rather than receiving a guessed
value or footprint location.

## Evidence

- `ref/photos/dgsh5-109-009-e3/PXL_20260718_101633062.jpg` — complete sheet-3
  overview, SHA-256
  `5f58dff9c2e1f8237f1c54e44a7ff5db2381b7c503d5e25466fcd219915f7047`.
- `ref/photos/dgsh5-109-009-e3/PXL_20260718_101644861.jpg` — closer D106/D96
  view, SHA-256
  `8b8ad8abdf5cdf8c235cc942592ebe6c0019ec8ad90ae9958267fbc154bb0e67`.

The sheet closes logical connectivity. Physical clock amplitude, edge quality,
and recovery timing remain bench bring-up measurements.
