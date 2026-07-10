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
| 2 | A5 | `XACK_N` (not netted) | sheet 1 label `-XACK` enters D2 A5/pin 2 |
| 3 | A4 | - | not traced/netted |
| 4 | A3 | `VIDEO_CYCLE` (not netted) | sheet 1 label `VIDEO CYCLE` enters D2 A3/pin 4 |
| 5 | A0 | - | not traced/netted |
| 6 | A1 | - | not traced/netted |
| 7 | A2 | - | not traced/netted |
| 15 | A7 | `WREQ_N` (not netted) | sheet 1 label `-WREQ` enters D2 A7/pin 15 |
| 13 | V1 | `GND` (not netted) | sheet 1 D2 V1/pin 13 is tied low |
| 14 | V2 | `GND` (not netted) | sheet 1 D2 V2/pin 14 is tied low |
| 12 | D0 | `D2_WAIT_RAW` (not netted) | sheet 1 D2 D0/pin 12 enters D105 pin 9 |

The named schematic leads above are pin-level source evidence, not a
claim that their complete PCB nets or D2 truth table are known. They
must be promoted only with the remaining address inputs and destination
continuity so a regenerated PCB does not encode a partial circuit.

## KiCad DSN Cross-check

The routed DSN currently exposes no D2 signal nets. The factory-sheet
leads above therefore remain an unrouted reconstruction boundary.

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

## KiCad PCB Cross-check

The final PCB source currently exposes no D2 signal pad nets. This
agrees with the deferred-net boundary in `kicad/juku.board.json`
and `kicad/juku.dsn`.

| Pin | Role | PCB Net | Result |
| ---: | --- | --- | --- |
| 1 | A6 | - | unnetted in PCB |
| 2 | A5 | - | unnetted in PCB |
| 3 | A4 | - | unnetted in PCB |
| 4 | A3 | - | unnetted in PCB |
| 5 | A0 | - | unnetted in PCB |
| 6 | A1 | - | unnetted in PCB |
| 7 | A2 | - | unnetted in PCB |
| 15 | A7 | - | unnetted in PCB |
| 13 | V1 | - | unnetted in PCB |
| 14 | V2 | - | unnetted in PCB |
| 12 | D0 | - | unnetted in PCB |

## Current Evidence Checks

| Check | Result | Evidence |
| --- | --- | --- |
| Board identity names D2 as `.037` RT4 | PASS | `kicad/juku.board.json` |
| Any D2 signal net is traced | FAIL | no D2 signal nets in board JSON |
| Any D2 signal appears in DSN | FAIL | no D2 pins in DSN nets |
| Any D2 signal appears in PCB | FAIL | no D2 pins in PCB nets |
| `.037` firmware artifact exists | FAIL | `ref/firmware/` has no `.037` artifact |
| Old D2-as-I/O-decode path is superseded | PASS | `kicad/juku.board.json` D9 identity and provenance |
| No reconstructed D2 fallback is exported | PASS | `docs/reconstructed-prom-fallbacks.md` |
| Official BOM/photo trail identifies `.037/.038` pair | PASS | `ref/photos/juku-pcb-2/BODGE-TRIAGE.md` |
| Evidence summary preserves D2 pin table but defers nets | PASS | `ref/photos/juku-pcb-2/BODGE-TRIAGE.md` |

## Evidence Reconciliation

- The official `.009` BOM/photo reconciliation identifies D2 as `.037`
  and D6 as `.038`.
- The surviving sheet-1 evidence records the physical D2 pin table
  `A0-A7=5/6/7/4/3/2/1/15`, `V1/V2=13/14`, `DO=12`, but explicitly
  says the nets are deferred until the PROM table and output
  destination are read.
- Therefore these notes prove D2 identity and pin roles, not a burnable
  `.037` image and not a board-net closure. The board JSON/DSN/PCB
  no-net boundary remains authoritative until a stronger trace,
  programming-disk file, or repeated physical dump exists.

## Reconstruction Boundary

- Known: D2 is a socketed К556РТ4 PROM and current project evidence
  identifies it as programmed drawing `ДГШ5.106.037`.
- Known: the older behavioral D2 I/O-decode model is not physical D2
  programming truth; D9 is the current chip-select decoder.
- Unknown: D2 address/input rails, V1/V2 handling, D0 destination, and
  `.037` contents are not traced/netted in current board JSON, DSN,
  or final PCB source, and no programming table or dump is present
  under `ref/firmware/`.
- Therefore a burnable D2 image is not derivable from current repo
  evidence. The correct automatic action is to keep this constraint
  report fresh; the data-unlocking action is a programming-disk file
  or a repeated physical dump.
