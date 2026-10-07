# D2 .037 reconstruction constraints

Status: **D2 PHYSICAL TABLE ADOPTED / CONNECTIVITY GUARDED**

This generated report records what the repo can currently prove about
the processor-board `D2` К556РТ4 PROM (`ДГШ5.106.037`). It separates
the validated physical table from older reconstruction assumptions.

## Command

Run from the repository root with Python 3. The command overwrites this report.
It compares recorded net assignments and checks evidence text markers;
the physical-image check covers existence and size only. It does not
revalidate captures, measure continuity, or execute the READY simulation.
Inspect the tables as well as the exit code: PCB/model net mismatches
are reported as `FAIL` but do not make this command exit nonzero.

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

Full per-net provenance is retained in [the board model](../kicad/juku.board.json).

| Pin | Role | Net | Source |
| ---: | --- | --- | --- |
| 1 | A6 | `A10` | scan; D2 pad fit retained, former D4 photo trace claim withdrawn |
| 2 | A5 | `IORC_N` | traced sheet-1: D29 physical B6 pin12 and X1.106C are labeled -IORC; D2 A5/pin2 is labeled -XACK at the identical factory edge coordinate 106C, proving the local alias on the same conductor; exact .009 sheet-1 D29 output -IORC is physical pin 16 |
| 3 | A4 | `A14` | scan; D2 pad fit retained, former D4 photo trace claim withdrawn |
| 4 | A3 | `CAS` | traced sheet-2 (array read plus D38 load-gate bundle: per-bank R rails 11/12/13/14; C+W shared); rail15 = the ONE shared CAS: D36.11 (К531ЛА12/SN74S37 high-drive NAND) -> R57 -> all 32 C pins, R58 5.1k pulldown -> grounded rail E, D36.1 feedback, D38.1 load-gate input, and video-cycle branch (2,3). Retired nets CAS0/1/2 dissolved (no per-bank CAS exists) |
| 5 | A0 | `A12` | scan; D2 pad fit retained, former D4 photo trace claim withdrawn |
| 6 | A1 | `A15` | scan; D2 pad fit retained, former D4 photo trace claim withdrawn |
| 7 | A2 | `A9` | scan; D2 pad fit retained, former D4 photo trace claim withdrawn |
| 15 | A7 | `WREQ_N` | traced sheet-1 labels D2 A7/pin15 as -WREQ from edge connector coordinate 107C. Direct owner continuity closes D6.11/D2.15/D92.5/R12.2; recovered .009 sheet 3 continues the same signal to both asynchronous controls D96.1/.4 and to the clear inputs of the D97.1/D97.2/D102.1/D102.2 precompensation one-shots. The sheet's conflicting R86 reset pull-up is not adopted because registered target photos place R86 on the C19/D97.6 node |
| 13 | V1 | `GND` | sheet-1 D2 enable tied low |
| 14 | V2 | `GND` | sheet-1 D2 enable tied low |
| 9 | D3 | NC | factory symbol draws only D0/pin12; explicit no-connect |
| 10 | D2 | NC | factory symbol draws only D0/pin12; explicit no-connect |
| 11 | D1 | NC | factory symbol draws only D0/pin12; explicit no-connect |
| 12 | D0 | `READY_D` | owner continuity 2026-07-13: D2 D0/pin12 and R6 2k pullup feed D30 section-A D input pin2; D2 open-collector output overrides the pullup |

## Exact PROM Address Index

The current modeled physical address byte is:

`{WREQ_N, A10, XACK_N, A14, CAS/VIDEO_CYCLE, A9, A15, A12}`

Therefore `prom_address = (WREQ_N<<7) + (A10<<6) + (XACK_N<<5) +
(A14<<4) + (CAS_VIDEO_CYCLE<<3) + (A9<<2) + (A15<<1) + A12`.
`ref/reconstructed-proms/d2_037_symbolic_truth.csv` enumerates all
256 input vectors. Its D0 cells remain `?` as a topology constraint;
the separately named validated raw programming image carries the
owner-observed values without rewriting this historical constraint file.

The named schematic leads above are pin-level source evidence where
cited; the captured programming table is separate evidence. The five address
labels with scan provenance still need an exact .009 route chase.
D2 pad registration does not close those remote address nets.
6 independent accepted acquisitions, including a
separate power cycle, establish the physical raw table.

## KiCad DSN Cross-check

This checks saved DSN pin assignments, not routed copper connectivity.

| Pin | Role | DSN Net | Result |
| ---: | --- | --- | --- |
| 1 | A6 | `A10` | present |
| 2 | A5 | `IORC_N` | present |
| 3 | A4 | `A14` | present |
| 4 | A3 | `CAS` | present |
| 5 | A0 | `A12` | present |
| 6 | A1 | `A15` | present |
| 7 | A2 | `A9` | present |
| 15 | A7 | `WREQ_N` | present |
| 13 | V1 | `GND` | present |
| 14 | V2 | `GND` | present |
| 9 | D3 | - | intentional NC in source |
| 10 | D2 | - | intentional NC in source |
| 11 | D1 | - | intentional NC in source |
| 12 | D0 | `READY_D` | present |

## KiCad PCB Cross-check

The PCB pad table exposes every modeled D2 input. The source also retains
five legacy D2-to-D4 solder segments whose endpoint pins require
review against the corrected package fit.

| Pin | Role | PCB Net | Result |
| ---: | --- | --- | --- |
| 1 | A6 | `A10` | present |
| 2 | A5 | `IORC_N` | present |
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
| D2 net assignments are present in JSON | PASS | `A10`, `IORC_N`, `A14`, `CAS`, `A12`, `A15`, `A9`, `WREQ_N`, `GND`, `GND`, `READY_D` |
| Any D2 signal appears in DSN | PASS | `1`=`A10`, `12`=`READY_D`, `13`=`GND`, `14`=`GND`, `15`=`WREQ_N`, `2`=`IORC_N`, `3`=`A14`, `4`=`CAS`, `5`=`A12`, `6`=`A15`, `7`=`A9` |
| Any D2 signal appears in PCB | PASS | `1`=`A10`, `12`=`READY_D`, `13`=`GND`, `14`=`GND`, `15`=`WREQ_N`, `16`=`P5V`, `2`=`IORC_N`, `3`=`A14`, `4`=`CAS`, `5`=`A12`, `6`=`A15`, `7`=`A9`, `8`=`GND` |
| D2 PCB pad nets match the logical model | PASS | all modeled pins agree; pins 9–11 remain NC |
| 256-row symbolic address table is non-burnable | PASS | all D0 values are `?` |
| Validated physical `.037` raw programming image exists | PASS | `ref/physical-proms/validated/d2_037.raw.bin` |
| Old D2-as-I/O-decode path is superseded | PASS | `kicad/juku.board.json` D9 identity and provenance |
| D2 physical-table provenance is preserved | PASS | `ref/physical-proms/README.md` |
| D2 READY polarity guard markers are present | PASS | `sync/d2_ready_path_check.sh`; D0 reader channel Nano D10 |
| Owner dump and corrected continuity are recorded | PASS | `docs/d2-physical-dump-and-continuity.md` |
| Official BOM/photo trail identifies `.037/.038` pair | PASS | `ref/photos/juku-pcb-2/BODGE-TRIAGE.md` |
| Evidence summary preserves the traced D2 pin table | PASS | `ref/photos/juku-pcb-2/BODGE-TRIAGE.md` |

## Evidence Reconciliation

The [physical truth record](d2-physical-truth.md) and
[dump/continuity record](d2-physical-dump-and-continuity.md) own reader
wiring, repeated-read provenance and corrected READY connectivity.
The validated manifest records 6 independent accepted acquisitions,
including power-cycled reads. Filename aliases are not additional acquisitions.

## Reconstruction Boundary

- Known: D2 is a socketed К556РТ4 PROM and current project evidence
  identifies it as programmed drawing `ДГШ5.106.037`.
- Known: D2 supplies READY data; D9 is the chip-select decoder.
- Known: all eight inputs have modeled net assignments, but the five
  scan-provenance address routes still need an exact .009 chase.
  D0/pin12 feeds D30 READY data; the factory symbol draws only D0,
  and pins 9-11 are explicit no-connects.
- Known: X1.107B/-BLOCK, R1.2, D13.13, and D105.10 form the pulled-up
  edge-bus `H`; R1 is 2 kΩ to +5 V. H gates CPU DBIN through D105
  into D5 and is not the −5 V supply.
- Known: `ref/physical-proms/validated/d2_037.raw.bin` is the 256-byte
  authoritative raw low-nibble image, reproduced from 6 independent acquisitions.
- Remaining closure: the five scan-provenance address routes, legacy
  D2-to-D4 segment endpoints, and complete WAIT/READY cycle timing.
  D2 content and raw electrical polarity are validated.
