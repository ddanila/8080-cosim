# D41 timing boundary

Status date: 2026-07-13.

Status: **D41 PACKAGE CONNECTIVITY SOURCE-CLOSED**

This generated report isolates the D41 ИР16 timing-chain boundary.
The board model has guarded evidence for D41's two output-side
uses, its fixed straps, and both numbered timing-bundle inputs.

## Command

```sh
python3 scripts/report_d41_timing_boundary.py
```

## Checks

| Check | Result | Evidence |
| --- | --- | --- |
| D41 exists as an ИР16 timing-chain chip | PASS | `kicad/juku.board.json` D41 |
| D41 QA output is wired to both video address mux selects | PASS | D41.13 -> `W10_QA_SEL` -> W10 -> `W10_QA_SEL_D50` -> D50.1 + D51.1 |
| D41 QB output is wired into the latch/preload chain | PASS | `LATCH_A`: D41.12 -> D37.1 |
| D41 LD is source-traced onto timing-bundle rail 17 | PASS | `TIMING_TAG17`: D41.6 + D36.2 |
| D41 CK is source-traced onto timing-bundle rail 8 | PASS | `SHIFT_G` / numbered rail 8: D41.9 + D42.8 + D43.8 |
| Factory tag 7 closes the D40/D37/D54 1 MHz clock net | PASS | sheet 2: tag 7 joins D40.11/D37.2 and tied D54 CLK0/1/2 pins 9/15/18; adjacent `LATCH_PRE`/`LATCH_SIG` retained |
| D41 proved straps, outputs, and timing boundaries are netted | PASS | D41.1, D41.12, D41.13, D41.2, D41.3, D41.4, D41.5, D41.6, D41.8, D41.9 |
| D41 unused QC/QD outputs remain intentional no-connects | PASS | 10:QD, 11:QC |
| D41 package landing is locally registered on both sides | PASS | validated notch-right component fit plus reflected solder fit in `docs/photo-registration/local-packages/report.json` |

## Netted D41 Pins

| Pin | Signal | Net | Evidence |
| --- | --- | --- | --- |
| 12 | QB | LATCH_A | D41.QB feeds D37.1 in the modeled latch/preload chain |
| 13 | QA | W10_QA_SEL -> W10 -> W10_QA_SEL_D50 | D41.QA selects both D50/D51 video/uP mux inputs via documented assembly wire 10 |
| 6 | LD | TIMING_TAG17 | Direct sheet-2 junction to numbered rail 17 shared with D36.2 |
| 9 | CK | SHIFT_G | Direct sheet-2 junction to numbered rail 8 shared with D42.8/D43.8 |

## Intentional No-Connect D41 Pins

| Pin | Signal | Boundary |
| --- | --- | --- |
| 10 | QD | sheet-2 package census shows no external stub |
| 11 | QC | sheet-2 package census shows no external stub |

## Interpretation

- D41 is not a generic unresolved video chip anymore: its output-side
  effects are modeled and route-checked.
- The corrected two-sided package fits replace global projections
  that landed in the parallel-rail field left/right of the actual IC.
- A-D are grounded, DS/G are tied high, and QC/QD have no external
  stubs. LD joins numbered timing rail 17; CK joins numbered rail 8.
- Sheet-2 conductor tag 7 closes D40 QD/pin11 and D37.2 to the tied
  D54 CLK0/CLK1/CLK2 pins 9/15/18 on the labeled 1 MHz rail.
- The complete D41 package pin disposition is now source-closed. The remote
  origin of rail 17 remains a wider timing-chain boundary at D36.2/D41.6.
