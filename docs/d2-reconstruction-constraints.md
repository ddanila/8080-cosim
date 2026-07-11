# D2 .037 reconstruction constraints

Status: **D2 INPUTS TRACED / DUMP REQUIRED**

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
| 1 | A6 | `A10` | scan + July-2026 D2/D4 solder local fits |
| 2 | A5 | `XACK_N` | traced sheet-1: label -XACK enters D2 A5/pin 2 from edge code 106C; the existing X1.106C transcription says IORC_N, so the connector merge remains an explicit conflict boundary |
| 3 | A4 | `A14` | scan + July-2026 D2/D4 solder local fits |
| 4 | A3 | `CAS` | traced sheet-2 (array read, crop arr_col1_locator: per-bank R rails 11/12/13/14; C+W shared); rail 15 = the ONE shared CAS: D36.11 (7437) -> R57 -> all 32 C pins, R58 5.1k pullup -> rail E, D36.1 feedback, video-cycle branch (2,3). Retired nets CAS0/1/2 dissolved (no per-bank CAS exists) |
| 5 | A0 | `A12` | scan + July-2026 D2/D4 solder local fits |
| 6 | A1 | `A15` | scan + July-2026 D2/D4 solder local fits |
| 7 | A2 | `A9` | scan + July-2026 D2/D4 solder local fits |
| 15 | A7 | `WREQ_N` | traced sheet-1: label -WREQ enters D2 A7/pin 15 from edge code 107C; target connector destination remains unmodeled |
| 13 | V1 | `GND` | scan; sheet-1 explicitly grounds CPU HOLD D1.13, system-controller BUSEN D5.22, and both always-enabled address-buffer OE pins D4.9/D107.9 |
| 14 | V2 | `GND` | scan; sheet-1 explicitly grounds CPU HOLD D1.13, system-controller BUSEN D5.22, and both always-enabled address-buffer OE pins D4.9/D107.9 |
| 12 | D0 | `D2_WAIT_RAW` | traced sheet-1: D2 D0/pin 12 enters D105 NAND input pin 9 |

## Exact PROM Address Index

The traced physical address byte is:

`{WREQ_N, A10, XACK_N, A14, VIDEO_CYCLE, A9, A15, A12}`

Therefore `prom_address = (WREQ_N<<7) + (A10<<6) + (XACK_N<<5) +
(A14<<4) + (VIDEO_CYCLE<<3) + (A9<<2) + (A15<<1) + A12`.
`ref/reconstructed-proms/d2_037_symbolic_truth.csv` enumerates all
256 input vectors. Every D0 cell is deliberately `?`; the CSV is a
constraint artifact, not a programmer image.

The named schematic leads above are pin-level source evidence, not a
claim that the D2 truth table is known. Each proved pin is promoted
independently; the July-2026 paired D2/D4 local fits close all eight
inputs while the programmed contents remain a separate boundary.

## KiCad DSN Cross-check

The saved routed DSN predates the five photo-traced address inputs.
Its missing rows are a reroute boundary, not missing source evidence.

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

The authoritative PCB source exposes every proved D2 input and adds
one idempotent solder-side segment for each D2-to-D4 address route.

| Pin | Role | PCB Net | Result |
| ---: | --- | --- | --- |
| 1 | A6 | `A10` | present |
| 2 | A5 | `XACK_N` | present |
| 3 | A4 | `A14` | present |
| 4 | A3 | `CAS` | present |
| 5 | A0 | `A12` | present |
| 6 | A1 | `A15` | present |
| 7 | A2 | `A9` | present |
| 15 | A7 | `WREQ_N` | present |
| 13 | V1 | `GND` | present |
| 14 | V2 | `GND` | present |
| 12 | D0 | `D2_WAIT_RAW` | present |

## Current Evidence Checks

| Check | Result | Evidence |
| --- | --- | --- |
| Board identity names D2 as `.037` RT4 | PASS | `kicad/juku.board.json` |
| Any D2 signal net is traced | PASS | `A10`, `XACK_N`, `A14`, `CAS`, `A12`, `A15`, `A9`, `WREQ_N`, `GND`, `GND`, `D2_WAIT_RAW` |
| Any D2 signal appears in DSN | PASS | `12`=`D2_WAIT_RAW`, `13`=`GND`, `14`=`GND`, `15`=`WREQ_N`, `2`=`XACK_N`, `4`=`CAS` |
| Any D2 signal appears in PCB | PASS | `1`=`A10`, `12`=`D2_WAIT_RAW`, `13`=`GND`, `14`=`GND`, `15`=`WREQ_N`, `2`=`XACK_N`, `3`=`A14`, `4`=`CAS`, `5`=`A12`, `6`=`A15`, `7`=`A9` |
| 256-row symbolic address table is non-burnable | PASS | all D0 values are `?` |
| `.037` firmware artifact exists | FAIL | `ref/firmware/` has no `.037` artifact |
| Old D2-as-I/O-decode path is superseded | PASS | `kicad/juku.board.json` D9 identity and provenance |
| No reconstructed D2 fallback is exported | PASS | `docs/reconstructed-prom-fallbacks.md` |
| Official BOM/photo trail identifies `.037/.038` pair | PASS | `ref/photos/juku-pcb-2/BODGE-TRIAGE.md` |
| Evidence summary preserves the traced D2 pin table | PASS | `ref/photos/juku-pcb-2/BODGE-TRIAGE.md` |

## Evidence Reconciliation

- The official `.009` BOM/photo reconciliation identifies D2 as `.037`
  and D6 as `.038`.
- The surviving sheet-1 evidence records the physical D2 pin table
  `A0-A7=5/6/7/4/3/2/1/15`, `V1/V2=13/14`, `DO=12`, but explicitly
  originally deferred the other five input nets.
- The July-2026 two-sided D2 fit plus an independent D4 solder-row fit
  now traces D2.1/.3/.5/.6/.7 to D4.1/.3/.5/.6/.7, closing all
  physical inputs without claiming a burnable `.037` image.

## Reconstruction Boundary

- Known: D2 is a socketed К556РТ4 PROM and current project evidence
  identifies it as programmed drawing `ДГШ5.106.037`.
- Known: the older behavioral D2 I/O-decode model is not physical D2
  programming truth; D9 is the current chip-select decoder.
- Known: all eight D2 inputs and D0/pin 12 to D105.9 are routed in the
  authoritative board model/source PCB. The saved routed snapshot
  still predates the five new D2-to-D4 routes.
- Unknown: the `.037` truth table; no programming table or dump is present
  under `ref/firmware/`.
- The factory sheet draws only D0/pin 12 from the four-output RT4
  package; unused output pins 9-11 are explicit no-connects in the
  board model and do not add unknown truth-table destinations.
- Therefore a burnable D2 image is not derivable from current repo
  evidence. The correct automatic action is to keep this constraint
  report fresh; the data-unlocking action is a programming-disk file
  or a repeated physical dump.
