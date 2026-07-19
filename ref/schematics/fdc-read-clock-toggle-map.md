# FDC read-clock toggle map

This is the reviewed transcription of D96.1 (КМ555ТМ2 / 74LS74 section 1)
from ДГШ5.109.009 Э3 sheet 3. It closes the toggle between the D106/D28
recovery counter and the КР1818ВГ93 read-clock input.

| Function | Sheet-3 endpoints | Board model |
| --- | --- | --- |
| write inhibit/reset | WREQ_N, D96.1 /CLR1, D96.4 /PRE1 | `WREQ_N` |
| toggle feedback | D96.6 /Q1, D96.2 D1 | `D96_TOGGLE_FEEDBACK` |
| recovered clock input | D28.8, R85.1, D96.3 CLK1 | `SEP_D28_CLK` |
| controller read clock | D96.5 Q1, D93.26 RCLK | `FDC_RCLK` |
| separate section 2 | D96.9 Q2, D96.10 /PRE2, D96.11 CLK2, D96.12 D2 | DRQ/INTRQ conditioner; see `fdc-irq-conditioner-map.md` |
| unused section-2 clear | D96.13 /CLR2 | no-connect |
| physical test landing | D96.8 /Q2 | `D96_Q2_N_TEST_LANDING` |

The quoted `"1"` arrow on both section-1 asynchronous controls is a continuation
to sheet 1 already closed as `WREQ_N`; it is not a literal logic-high
annotation. A separate full-resolution sheet-3 region draws D96 section 2 in
the DRQ/INTRQ conditioner. Its `/Q2` pin8 nevertheless reaches an independently
photo-proved one-sided component test landing, while `/CLR2` pin13 is the only
explicitly unused section-2 pin.

## Evidence

- `ref/photos/dgsh5-109-009-e3/PXL_20260718_101633062.jpg` — complete sheet-3
  overview, SHA-256
  `5f58dff9c2e1f8237f1c54e44a7ff5db2381b7c503d5e25466fcd219915f7047`.
- `ref/photos/dgsh5-109-009-e3/PXL_20260718_101644861.jpg` — close D106/D28/D96
  view, SHA-256
  `8b8ad8abdf5cdf8c235cc942592ebe6c0019ec8ad90ae9958267fbc154bb0e67`.
- `ref/photos/juku-pcb-2/endpoints.csv` accepted rows
  `seed-component-D96-8` and `seed-solder-D96-8` — isolated pin-8 landing.

This closes logical connectivity and the runnable divide-by-two contract.
Clock amplitude, pull-up rise time, duty cycle, and separator lock margin remain
bench bring-up measurements.
