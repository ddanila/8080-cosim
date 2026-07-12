# D41 timing boundary

Status date: 2026-07-11.

Status: **D41 STRAPS/OUTPUTS GUARDED / LD-CK SOURCES PENDING**

This generated report isolates the D41 ИР16 timing-chain boundary.
The board model has guarded evidence for D41's two output-side
uses, its fixed straps, and its two remaining timing-source boundaries.

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
| D41 proved straps, outputs, and timing boundaries are netted | PASS | D41.1, D41.12, D41.13, D41.2, D41.3, D41.4, D41.5, D41.6, D41.8, D41.9 |
| D41 unused QC/QD outputs remain intentional no-connects | PASS | 10:QD, 11:QC |
| D41 package landing is locally registered on both sides | PASS | validated notch-right component fit plus reflected solder fit in `docs/photo-registration/local-packages/report.json` |

## Netted D41 Pins

| Pin | Signal | Net | Evidence |
| --- | --- | --- | --- |
| 12 | QB | LATCH_A | D41.QB feeds D37.1 in the modeled latch/preload chain |
| 13 | QA | W10_QA_SEL | D41.QA selects both D50/D51 video/uP mux inputs via documented wire 10 |

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
  stubs. LD and CK are preserved as distinct timing-bundle boundaries.
- Do not infer the LD/CK remote drivers from the runnable raster model;
  they still need a readable source or continuity pass.
