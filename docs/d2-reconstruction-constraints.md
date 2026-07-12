# D2 .037 reconstruction constraints

Status: **D2 PHYSICAL TABLE ADOPTED / CONNECTIVITY GUARDED**

This generated report records what the repo can currently prove about
the processor-board `D2` К556РТ4 PROM (`ДГШ5.106.037`). It separates
the validated physical table from older reconstruction assumptions.

## Command

```sh
python3 scripts/report_d2_reconstruction_constraints.py
```

## Identity

| Field | Value |
| --- | --- |
| Board type | `WAIT_PROM` |
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
| 13 | V1 | `GND` | scan; sheet-1 explicitly grounds CPU HOLD D1.13, system-controller BUSEN D5.22, and both always-enabled address-buffer OE pins D4.9/D107.9; July-2026 cross-photo full-package registration identifies the adjacent КМ555ТМ2 as D96 and continuous component copper directly ties D99.3 CLR_N to D96.7 GND |
| 14 | V2 | `GND` | scan; sheet-1 explicitly grounds CPU HOLD D1.13, system-controller BUSEN D5.22, and both always-enabled address-buffer OE pins D4.9/D107.9; July-2026 cross-photo full-package registration identifies the adjacent КМ555ТМ2 as D96 and continuous component copper directly ties D99.3 CLR_N to D96.7 GND |
| 9 | D3 | NC | factory symbol draws only D0/pin12; explicit no-connect |
| 10 | D2 | NC | factory symbol draws only D0/pin12; explicit no-connect |
| 11 | D1 | NC | factory symbol draws only D0/pin12; explicit no-connect |
| 12 | D0 | `READY_D` | owner continuity 2026-07-13: D2 D0/pin12 and R6 2k pullup feed D30 section-A D input pin2; D2 open-collector output overrides the pullup |

## Exact PROM Address Index

The traced physical address byte is:

`{WREQ_N, A10, XACK_N, A14, CAS/VIDEO_CYCLE, A9, A15, A12}`

Therefore `prom_address = (WREQ_N<<7) + (A10<<6) + (XACK_N<<5) +
(A14<<4) + (CAS_VIDEO_CYCLE<<3) + (A9<<2) + (A15<<1) + A12`.
`ref/reconstructed-proms/d2_037_symbolic_truth.csv` enumerates all
256 input vectors. Its D0 cells remain `?` as a topology constraint;
the separately named validated raw programming image carries the
owner-observed values without rewriting this historical constraint file.

The named schematic leads above are pin-level source evidence, not a
claim that the D2 truth table is known. Each proved pin is promoted
independently; the July-2026 paired D2/D4 local fits close all eight
inputs. Three validated owner captures, including a separate power cycle,
now establish the physical raw table.

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
| 9 | D3 | - | intentional NC in source |
| 10 | D2 | - | intentional NC in source |
| 11 | D1 | - | intentional NC in source |
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
| 9 | D3 | - | intentional NC |
| 10 | D2 | - | intentional NC |
| 11 | D1 | - | intentional NC |
| 12 | D0 | `READY_D` | present |

## Current Evidence Checks

| Check | Result | Evidence |
| --- | --- | --- |
| D2 unused outputs are explicit no-connects | PASS | pins 9, 10, 11; factory symbol draws only D0/pin12 |
| Board identity names D2 as `.037` RT4 | PASS | `kicad/juku.board.json` |
| Any D2 signal net is traced | PASS | `A10`, `XACK_N`, `A14`, `CAS`, `A12`, `A15`, `A9`, `WREQ_N`, `GND`, `GND`, `READY_D` |
| Any D2 signal appears in DSN | PASS | `12`=`D2_WAIT_RAW`, `13`=`GND`, `14`=`GND`, `15`=`WREQ_N`, `2`=`XACK_N`, `4`=`CAS` |
| Any D2 signal appears in PCB | PASS | `1`=`A10`, `12`=`READY_D`, `13`=`GND`, `14`=`GND`, `15`=`WREQ_N`, `2`=`XACK_N`, `3`=`A14`, `4`=`CAS`, `5`=`A12`, `6`=`A15`, `7`=`A9` |
| 256-row symbolic address table is non-burnable | PASS | all D0 values are `?` |
| Validated physical `.037` raw programming image exists | PASS | `ref/physical-proms/validated/d2_037.raw.bin` |
| Old D2-as-I/O-decode path is superseded | PASS | `kicad/juku.board.json` D9 identity and provenance |
| D2 physical-table provenance is preserved | PASS | `docs/reconstructed-prom-fallbacks.md` |
| Owner dump and corrected continuity are recorded | PASS | `docs/d2-physical-dump-and-continuity.md` |
| Official BOM/photo trail identifies `.037/.038` pair | PASS | `ref/photos/juku-pcb-2/BODGE-TRIAGE.md` |
| Evidence summary preserves the traced D2 pin table | PASS | `ref/photos/juku-pcb-2/BODGE-TRIAGE.md` |

## Evidence Reconciliation

- The official `.009` BOM/photo reconciliation identifies D2 as `.037`
  and D6 as `.038`.
- The surviving sheet-1 evidence records the physical D2 pin table
  `A0-A7=5/6/7/4/3/2/1/15`, `V1/V2=13/14`, `DO=12`, but explicitly
  originally deferred the other five input nets.
- Direct owner continuity supersedes the false D2.12->D105.9 path:
  D2.12 joins D30.2 and R6 in the READY latch input.
- Two complete same-session reads matched at every address with zero
  unstable rows; all four outputs agreed. A third separately power-cycled
  capture validates to the same authoritative raw SHA256.

## Reconstruction Boundary

- Known: D2 is a socketed К556РТ4 PROM and current project evidence
  identifies it as programmed drawing `ДГШ5.106.037`.
- Known: the older behavioral D2 I/O-decode model is not physical D2
  programming truth; D9 is the current chip-select decoder.
- Known: all eight inputs are traced and D0/pin12 feeds D30 READY data.
  The factory symbol draws only D0; pins9-11 are explicit no-connects.
- Known: D105.10 is the pulled-up edge-bus `H` net shared with D13.13;
  it gates CPU DBIN through D105 into D5 and is not the −5 V supply.
- Known: `ref/physical-proms/validated/d2_037.raw.bin` is the 256-byte
  authoritative raw low-nibble image, reproduced from all three captures.
- Remaining closure is historical comparison against a programming-disk
  file or independent future read, not recovery of the current chip table.
