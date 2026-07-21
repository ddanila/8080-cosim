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
| separate section 2 | D96.9 Q2, D96.10 /PRE2, D96.11 CLK2, D96.12 D2 | exact DRQ/INTRQ wiring with a set-only functional contradiction; see `fdc-irq-conditioner-map.md` |
| unused section-2 clear | D96.13 /CLR2 | no-connect |
| physical test landing | D96.8 /Q2 | `D96_Q2_N_TEST_LANDING` |

The quoted `"1"` arrow on both section-1 asynchronous controls is a continuation
to sheet 1 already closed as `WREQ_N`; it is not a literal logic-high
annotation. A separate full-resolution sheet-3 region draws D96 section 2 in
the DRQ/INTRQ conditioner. Its `/Q2` pin8 nevertheless reaches an independently
photo-proved one-sided component test landing, while `/CLR2` pin13 is the only
explicitly unused section-2 pin.

Tying WREQ_N to both `/CLR1` and `/PRE1` invokes the SN74LS74A simultaneous-
assertion row: Q1 and `/Q1` are both high while WREQ_N is low. The old HDL
clear-priority reset was not device-accurate and is retired. Simultaneous
release does not define restart phase; once a recovered-clock edge resolves
the state, `/Q1` feedback still provides phase-independent divide-by-two
behavior.

The SN74LS74A truth table exposes a functional contradiction in that exact
section-2 drawing: the conditioned node drives both `/PRE2` and D2. Low
asynchronously sets Q2; high makes a rising CLK2 edge capture one. With
`/CLR2` inactive, neither documented path can clear Q2 after it has been set.
The sheet-omitted pin13 disposition and remote pins9/11 therefore require
continuity plus a powered capture before this half can be called a complete
conditioner. This constraint is guarded by `sync/d96_check.sh` and does not
invent a missing pin13 connection.

## Evidence

- `ref/photos/dgsh5-109-009-e3/PXL_20260718_101633062.jpg` — complete sheet-3
  overview, SHA-256
  `5f58dff9c2e1f8237f1c54e44a7ff5db2381b7c503d5e25466fcd219915f7047`.
- `ref/photos/dgsh5-109-009-e3/PXL_20260718_101644861.jpg` — close D106/D28/D96
  view, SHA-256
  `8b8ad8abdf5cdf8c235cc942592ebe6c0019ec8ad90ae9958267fbc154bb0e67`.
- `ref/photos/juku-pcb-2/endpoints.csv` accepted rows
  `seed-component-D96-8` and `seed-solder-D96-8` — isolated pin-8 landing.

This closes logical connectivity and the runnable section-1 divide-by-two
contract while explicitly holding section 2 for functional verification.
Clock amplitude, pull-up rise time, duty cycle, and separator lock margin remain
bench bring-up measurements.
