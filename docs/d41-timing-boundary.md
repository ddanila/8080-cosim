# D41 timing boundary

Status: **D41 PACKAGE CONNECTIVITY SOURCE-CLOSED**

This generated report isolates the D41 ИР16 timing-chain boundary.
The board model has guarded evidence for D41's two output-side
uses, its fixed straps, and both numbered timing-bundle inputs.

## Command

Run from the repository root with Python 3 (standard library only).
The generator overwrites this report with its check results, including
failed results, then returns exit status 1 if any check fails.

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
| Factory tag 7 and owner continuity close the complete 1 MHz clock net | PASS | sheets 2/3 and owner continuity join D40.11/D37.2/D54.9/.15/.18/D59.5/D92.2/.3/D95.5/.6; adjacent `LATCH_PRE`/`LATCH_SIG` retained |
| D41 proved straps, outputs, and timing boundaries are netted | PASS | D41.1, D41.12, D41.13, D41.14, D41.2, D41.3, D41.4, D41.5, D41.6, D41.7, D41.8, D41.9 |
| D41 unused QC/QD outputs remain intentional no-connects | PASS | 10:QD, 11:QC |
| D41 photo-fit records cover both sides with the expected models | PASS | component `similarity` and solder `similarity_reflected` entries in `docs/photo-registration/local-packages/report.json` |

## Netted D41 Pins

| Pin | Signal | Net | Evidence |
| --- | --- | --- | --- |
| 12 | QB | LATCH_A | D41.QB feeds D37.1 in the modeled latch/preload chain |
| 13 | QA | W10_QA_SEL -> W10 -> W10_QA_SEL_D50 | D41.QA selects both D50/D51 video/uP mux inputs via documented assembly wire 10 |
| 6 | LD_SH | TIMING_TAG17 | Direct sheet-2 junction to numbered rail 17 shared with D36.2 |
| 9 | CLK | SHIFT_G | Direct sheet-2 junction to numbered rail 8 shared with D42.8/D43.8 |

## Intentional No-Connect D41 Pins

| Pin | Signal | Boundary |
| --- | --- | --- |
| 10 | QD | sheet-2 package census shows no external stub |
| 11 | QC | sheet-2 package census shows no external stub |

## Interpretation

- This guard checks source-model endpoints, provenance markers and the
  presence of two photo-fit records with the expected sides and models.
  It does not inspect routed copper, rerun image registration, or measure
  dynamic timing. See the [video-slot audit](video-slot-timing-audit.md)
  for the remaining arbitration boundary.
- The source model grounds A-D, ties DS/G high, and leaves QC/QD
  unconnected. LD joins rail 17 and CK rail 8. The remote origin of
  rail 17 remains unresolved at D36.2/D41.6.
- The 1 MHz source-net check preserves the factory tag-7 and owner
  continuity attribution. The [clock-route report](d40-d59-d92-d95-1mhz-route.md)
  owns the corresponding source/routed migration evidence.
