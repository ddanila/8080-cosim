# D2 .037 reconstruction constraints

Status: **D2 RECONSTRUCTION CONSTRAINED / DUMP REQUIRED**

This generated report records what the repo can currently prove about
the processor-board `D2` К556РТ4 PROM (`ДГШ5.106.037`) before attempting
any reverse-engineered or burnable replacement table.

## Command

```sh
python3 scripts/report_d2_reconstruction_constraints.py
```

## Identity

| Field | Value |
| --- | --- |
| Board type | `DEC_PROM` |
| Programmed drawing | `ДГШ5.106.037` |
| Current role | bus-arbitration/wait PROM, not I/O decode |

## Board JSON Pins

| Pin | Role | Net | Source |
| ---: | --- | --- | --- |
| 1 | A6 | - | not traced/netted |
| 2 | A5 | - | not traced/netted |
| 3 | A4 | - | not traced/netted |
| 4 | A3 | - | not traced/netted |
| 5 | A0 | - | not traced/netted |
| 6 | A1 | - | not traced/netted |
| 7 | A2 | - | not traced/netted |
| 15 | A7 | - | not traced/netted |
| 13 | V1 | - | not traced/netted |
| 14 | V2 | - | not traced/netted |
| 12 | D0 | - | not traced/netted |

## KiCad DSN Cross-check

The routed DSN currently exposes no D2 signal nets. This agrees with
the deferred-net boundary in `kicad/juku.board.json`.

| Pin | Role | DSN Net | Result |
| ---: | --- | --- | --- |
| 1 | A6 | - | missing in DSN |
| 2 | A5 | - | missing in DSN |
| 3 | A4 | - | missing in DSN |
| 4 | A3 | - | missing in DSN |
| 5 | A0 | - | missing in DSN |
| 6 | A1 | - | missing in DSN |
| 7 | A2 | - | missing in DSN |
| 15 | A7 | - | missing in DSN |
| 13 | V1 | - | missing in DSN |
| 14 | V2 | - | missing in DSN |
| 12 | D0 | - | missing in DSN |

## Current Evidence Checks

| Check | Result | Evidence |
| --- | --- | --- |
| Board identity names D2 as `.037` RT4 | PASS | `kicad/juku.board.json` |
| Any D2 signal net is traced | FAIL | no D2 signal nets in board JSON |
| Any D2 signal appears in DSN | FAIL | no D2 pins in DSN nets |
| `.037` firmware artifact exists | FAIL | `ref/firmware/` has no `.037` artifact |
| Old D2-as-I/O-decode path is superseded | PASS | `docs/transcription/io.md` |
| No reconstructed D2 fallback is exported | PASS | `docs/reconstructed-prom-fallbacks.md` |
| Official BOM/photo trail identifies `.037/.038` pair | PASS | `ref/photos/juku-pcb-2/BODGE-TRIAGE.md` |

## Reconstruction Boundary

- Known: D2 is a socketed К556РТ4 PROM and current project evidence
  identifies it as programmed drawing `ДГШ5.106.037`.
- Known: the older behavioral D2 I/O-decode model is not physical D2
  programming truth; D9 is the current chip-select decoder.
- Unknown: D2 address/input rails, V1/V2 handling, D0 destination, and
  `.037` contents are not traced/netted in current board JSON/DSN and
  no programming table or dump is present under `ref/firmware/`.
- Therefore a burnable D2 image is not derivable from current repo
  evidence. The correct automatic action is to keep this constraint
  report fresh; the data-unlocking action is a programming-disk file
  or a repeated physical dump.
