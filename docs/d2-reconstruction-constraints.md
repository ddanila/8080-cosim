# D2 .037 reconstruction constraints

Status: **D2 RECONSTRUCTION PARTIALLY TRACED / DUMP REQUIRED**

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
| 2 | A5 | `XACK_N` | traced sheet-1: label -XACK enters D2 A5/pin 2 from edge code 106C; the existing X1.106C transcription says IORC_N, so the connector merge remains an explicit conflict boundary |
| 3 | A4 | - | not traced/netted |
| 4 | A3 | `CAS` | traced sheet-2 (array read, crop arr_col1_locator: per-bank R rails 11/12/13/14; C+W shared); rail 15 = the ONE shared CAS: D36.11 (7437) -> R57 -> all 32 C pins, R58 5.1k pullup -> rail E, D36.1 feedback, video-cycle branch (2,3). Retired nets CAS0/1/2 dissolved (no per-bank CAS exists) |
| 5 | A0 | - | not traced/netted |
| 6 | A1 | - | not traced/netted |
| 7 | A2 | - | not traced/netted |
| 15 | A7 | `WREQ_N` | traced sheet-1: label -WREQ enters D2 A7/pin 15 from edge code 107C; target connector destination remains unmodeled |
| 13 | V1 | `GND` | scan |
| 14 | V2 | `GND` | scan |
| 12 | D0 | `D2_WAIT_RAW` | traced sheet-1: D2 D0/pin 12 enters D105 NAND input pin 9 |

The named schematic leads above are pin-level source evidence, not a
claim that the remaining address inputs or D2 truth table are known.
Each proved pin is promoted independently; unresolved pins remain
explicit rather than being filled by behavioral inference.

## KiCad DSN Cross-check

The routed DSN exposes every currently proved D2 lead. The five
untraced address inputs remain an explicit reconstruction boundary.

| Pin | Role | DSN Net | Result |
| ---: | --- | --- | --- |
| 1 | A6 | - | missing in DSN |
| 2 | A5 | `XACK_N` | present |
| 3 | A4 | - | missing in DSN |
| 4 | A3 | `CAS` | present |
| 5 | A0 | - | missing in DSN |
| 6 | A1 | - | missing in DSN |
| 7 | A2 | - | missing in DSN |
| 15 | A7 | `WREQ_N` | present |
| 13 | V1 | `GND` | present |
| 14 | V2 | `GND` | present |
| 12 | D0 | `D2_WAIT_RAW` | present |

## KiCad PCB Cross-check

The final PCB source exposes every currently proved D2 lead and
leaves only the five untraced address-input pads unnetted.

| Pin | Role | PCB Net | Result |
| ---: | --- | --- | --- |
| 1 | A6 | - | unnetted in PCB |
| 2 | A5 | `XACK_N` | present |
| 3 | A4 | - | unnetted in PCB |
| 4 | A3 | `CAS` | present |
| 5 | A0 | - | unnetted in PCB |
| 6 | A1 | - | unnetted in PCB |
| 7 | A2 | - | unnetted in PCB |
| 15 | A7 | `WREQ_N` | present |
| 13 | V1 | `GND` | present |
| 14 | V2 | `GND` | present |
| 12 | D0 | `D2_WAIT_RAW` | present |

## Current Evidence Checks

| Check | Result | Evidence |
| --- | --- | --- |
| Board identity names D2 as `.037` RT4 | PASS | `kicad/juku.board.json` |
| Any D2 signal net is traced | PASS | `XACK_N`, `CAS`, `WREQ_N`, `GND`, `GND`, `D2_WAIT_RAW` |
| Any D2 signal appears in DSN | PASS | `12`=`D2_WAIT_RAW`, `13`=`GND`, `14`=`GND`, `15`=`WREQ_N`, `2`=`XACK_N`, `4`=`CAS` |
| Any D2 signal appears in PCB | PASS | `12`=`D2_WAIT_RAW`, `13`=`GND`, `14`=`GND`, `15`=`WREQ_N`, `2`=`XACK_N`, `4`=`CAS` |
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
- Partially known: D2 D0/pin 12 is routed to D105.9. The remaining
  address/input rails and `.037` truth table are not yet closed, and
  no programming table or dump is present
  under `ref/firmware/`.
- Therefore a burnable D2 image is not derivable from current repo
  evidence. The correct automatic action is to keep this constraint
  report fresh; the data-unlocking action is a programming-disk file
  or a repeated physical dump.
