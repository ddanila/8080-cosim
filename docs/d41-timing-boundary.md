# D41 timing boundary

Status date: 2026-07-11.

Status: **D41 OUTPUTS GUARDED / INPUT TIMING BUS PENDING**

This generated report isolates the D41 ИР16 timing-chain boundary.
The board model has guarded evidence for D41's two output-side
uses, but it still lacks historical-source-complete nets for the
serial/parallel inputs and control pins that come from the sheet-2 timing bus.

## Command

```sh
python3 scripts/report_d41_timing_boundary.py
```

## Checks

| Check | Result | Evidence |
| --- | --- | --- |
| D41 exists as an ИР16 timing-chain chip | PASS | `kicad/juku.board.json` D41 |
| D41 QA output is wired to both video address mux selects | PASS | `W10_QA_SEL`: D41.13 -> D50.1 + D51.1 |
| D41 QB output is wired into the latch/preload chain | PASS | `LATCH_A`: D41.12 -> D37.1 |
| Adjacent latch chain context is modeled | PASS | `LATCH_B`/`LATCH_PRE`/`LATCH_SIG` around D37/D40/D33/D39 |
| Only D41 output pins are currently netted | PASS | D41.12, D41.13 |
| D41 input/control pins remain an explicit source boundary | PASS | 1:DS, 2:A, 3:B, 4:C, 5:D, 6:LD, 8:G, 9:CK, 10:QD, 11:QC |
| D41 package landing is locally registered on both sides | PASS | validated notch-right component fit plus reflected solder fit in `docs/photo-registration/local-packages/report.json` |

## Netted D41 Pins

| Pin | Signal | Net | Evidence |
| --- | --- | --- | --- |
| 12 | QB | LATCH_A | D41.QB feeds D37.1 in the modeled latch/preload chain |
| 13 | QA | W10_QA_SEL | D41.QA selects both D50/D51 video/uP mux inputs via documented wire 10 |

## Pending D41 Pins

| Pin | Signal | Boundary |
| --- | --- | --- |
| 1 | DS | sheet-2 timing-bus continuity/source read required |
| 2 | A | sheet-2 timing-bus continuity/source read required |
| 3 | B | sheet-2 timing-bus continuity/source read required |
| 4 | C | sheet-2 timing-bus continuity/source read required |
| 5 | D | sheet-2 timing-bus continuity/source read required |
| 6 | LD | sheet-2 timing-bus continuity/source read required |
| 8 | G | sheet-2 timing-bus continuity/source read required |
| 9 | CK | sheet-2 timing-bus continuity/source read required |
| 10 | QD | parallel-output destination/NC source read required |
| 11 | QC | parallel-output destination/NC source read required |

## Interpretation

- D41 is not a generic unresolved video chip anymore: its output-side
  effects are modeled and route-checked.
- The corrected two-sided package fits replace global projections
  that landed in the parallel-rail field left/right of the actual IC.
- The remaining D41 gap is specific to pins 1-6/8-11: serial input,
  unresolved QC/QD parallel outputs,
  parallel inputs, load, gate, and clock from the timing-wire bus.
- Do not infer these input/control nets from the runnable raster model;
  they need a readable sheet-2 timing-chain source, macro photo, or
  continuity pass before D41 can leave the board-fidelity gap ledger.
