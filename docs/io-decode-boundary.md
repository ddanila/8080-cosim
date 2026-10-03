# I/O decode boundary

Status date: 2026-07-22.

Status: **IO DECODE GUARDED / SMALL SOURCE BOUNDARIES PENDING**

This generated report isolates the sheet-1 I/O decode cluster.
It guards the current D9 К555ИД7 decoder model and the D7/R17/C99
strobe-enable path while keeping the small remaining source boundaries
visible.

## Command

```sh
python3 scripts/report_io_decode_boundary.py
```

## Guarded Checks

| Check | Result | Evidence |
| --- | --- | --- |
| D5 system-controller power contract is routed | PASS | D5.14 GND / D5.28 +5V |
| D9 is the physical К555ИД7 I/O decoder | PASS | `kicad/juku.board.json` D9 provenance |
| Runnable HDL and LVS use the physical D9 identity and traced pins | PASS | U_D9: BA10/11/12, G1=V3_RC, G2A/G2B=REV; no placeholder refdes |
| D7 strobe-NAND output reaches the R17/C99 D9.G1 RC node | PASS | `PROM_EN` -> `V3_RC` |
| D7 first-gate SYNC/feedback topology is source-proven | PASS | D1.19 SYNC -> D7.12; D7.11 -> D7.13 feedback before R17 |
| D7 second-gate provenance preserves the owner-disproved D29.5 split | PASS | exact .009 joins D7.3 to D29.2; owner continuity separates D29.5 on qualified IOWR |
| D9 region-enable inputs are tied to REV | PASS | native sheet-1 code-2 branch: D6.10/R13.2 -> D9.4/D9.5 |
| D9 select inputs are BA10..BA12 | PASS | `BA10`, `BA11`, `BA12` into D9.A/B/C |
| D7 fourth-gate inputs are wired to raw IOWR_N/IORD_N | PASS | `IOWR_RAW_N`/`IORD` inputs |
| D9 chip-select outputs are routed to the modeled peripherals | PASS | `CS_D10`..`FDC_CS_N`; exact .009 CS7 path D9.7→D94.15/D93.3, owner-confirmed D94.15-D93.3, and corrected D94.2-D99.9/R89 node |
| D25 bus turnaround handoff is guarded | PASS | `D25_T`: D7.6 -> D25.11 |

## Pending Boundary Checks

| Boundary | Result | Current evidence |
| --- | --- | --- |
| D7 fourth-gate strobe inputs are source-proven | PASS | IORD_N/IOWR_N are on D7.9/D7.10; raw D5.27 is distinct from qualified D105.3 |
| C99 far plate uses the exact-sheet ground symbol | PASS | C99.1 is on V3_RC; C99.2 ground bar matches R16's ground symbol in the exact .009 sheet |
| D25_T MEMW input is source-proven without crossing-rail overmerge | PASS | Native sheet proves D7.4 -> MEMW/D29.8; D7.5 remains on the distinct -INHIB junction |
| D7.8 I/O-cycle qualifier and D105.3 qualified /WR are owner-closed | PASS | Owner continuity 2026-07-19 separates raw D5.27 from qualified D105.3 and closes D7.8 to D105.1/D6.15 |

## Current Decode Nets

| Net | Endpoints | Source note |
| --- | --- | --- |
| `PROM_EN` | `D7.11, D7.13, R17.2` | traced sheet-1 native 5150x3603 direct-junction review: D7 section 12,13->11 is a SYNC-gated feedback strobe; pin13 loops directly onto output pin11, and that shared node runs east into R17.2 (200R). The old scan link D7.11->D6.14 is refuted-assumed: D6 V1/V2 feed unread [chase]; exact .009 detail 101805510 shows D7.11 and D105.3 on distinct local strokes, correcting the earlier false output-output tie; PROM_EN remains separate from qualified IOWR |
| `SYNC` | `D1.19, D38.12, D7.12` | wire plus sheet-1 native 5150x3603 direct T-junction: CPU D1.19 SYNC reaches D7 first-gate input pin12; WIRE 9 separately continues to D38.12 |
| `V3_RC` | `C99.1, D9.6, R17.1` | traced exact .009 sheet-1: R17 top + C99 pin1/left plate + D9.6 share one junction; rail3 crosses above without a dot. C99 pin2/right plate ends in the same perpendicular ground-bar symbol as R16. RC-deglitched I/O strobe -> D9.G1 |
| `REV` | `D6.10, D9.4, D9.5, R13.2` | native full-resolution sheet 1: D6.10 REV rail code 2 runs into the D9 pins-4+5 bridge and the upper labeled R13 1k pull-up branch. This is the I/O-decoder region enable (G2A_N+G2B_N tied): low for BA13-15=000 -> ports 00-1F pass, >=20 blocked |
| `BA10` | `D15.21, D16.21, D17.21, D18.21, D19.21, D20.21, D21.21, D22.21, D24.3, D4.19, ... (+2)` | scan; D6 endpoint removed (drawn: D6 pins 2/1/15 = mode-bundle tags 1/2/3, crop bios_hunt1) |
| `BA11` | `D15.23, D16.23, D17.23, D18.23, D19.23, D20.23, D21.23, D22.23, D24.4, D4.18, ... (+4)` | scan |
| `BA12` | `D15.2, D16.2, D17.2, D18.2, D19.2, D20.2, D21.2, D22.2, D24.5, D4.15, ... (+4)` | scan |
| `IOWR` | `D10.2, D105.3, D11.10, D26.36, D27.36, D29.5, D54.23, D55.23, D57.23, D94.13` | owner continuity 2026-07-19: D105 NAND output pin3 is the qualified active-low peripheral write rail. Exact .009 detail 101805510 shows D7.11/PROM_EN and D105.3 on distinct local strokes; the former output-output join claim was a tracing error. Its inputs are D7.8 I/O-cycle-active high and D13.4 CPU-write-active high. Directly confirmed endpoints are D94.13, D29.5, D10.2, D11.10, D26.36, and D27.36; existing sheet-derived PIT write endpoints remain on the same rail. D5.27 is the separate raw IOWR_N source into D7.10 |
| `IORD` | `D10.3, D11.13, D26.5, D27.5, D29.4, D5.25, D54.22, D55.22, D57.22, D7.9, ... (+1)` | scan sheet-1 full-resolution plus direct owner continuity 2026-07-15: D5.25 IORD runs into D7.9; D94.12/A2 joins D27.5/RD_N and D29.4. D29.4 conflicts with the older IOM_STATUS scan interpretation and is adopted from the physical board; recheck D29.4-D7.8, D29.4-D29.8, and D29.8-D27.5 later. D93.4 belongs only to D94.3 |
| `D25_T` | `D25.11, D7.6` | traced sheet-1 native 5150x3603 review: D7 ЛА3 section (pins 5,4 -> 6 with inversion circle) drives D25.T (pin 11) = the data-bus turnaround; pin4 drops past the D29.3 rail without a junction and terminates as a T on MEMW/D29 physical pin8, while pin5 meets D29.3 at an explicit junction whose upstream source remains unread. D25.E (9) -> GND like D23/D24 |
| `CS_D10` | `D10.1, D9.15` | prom |
| `CS_D26` | `D26.6, D9.14` | prom |
| `CS_D11` | `D11.11, D9.13` | prom |
| `CS_D27` | `D27.6, D9.12` | prom |
| `CS_D54` | `D54.21, D9.11` | prom |
| `CS_D55` | `D55.21, D9.10` | prom |
| `CS_D57` | `D57.21, D9.9` | prom |
| `FDC_CS_N` | `D9.7, D93.3, D94.15` | exact .009 sheet 1 draws D9.7 as CS7 to sheet 3; exact sheet 3 draws CS7 to D94 enable pin15 and D93 chip-select pin3. Direct owner continuity 2026-07-15 confirms D94.15 to D93.3 and isolates D94 output pin2 from this conductor |

## Interpretation

- D9, not D2, is the physical I/O chip-select decoder in the current
  board model; this report guards that D2-as-I/O-decode is not revived.
- The I/O decoder enable is the traced D7.11 -> R17/C99 -> D9.6 path,
  with REV on D9.4/D9.5 and BA10..BA12 selecting the eight I/O groups.
- The exact `.009` assembly view `PXL_20260711_114556899.jpg` places a
  horizontal C99 immediately below D9 and left of upright R17. Both
  May close-up `201933909` and overlapping July component views
  (`200411500` and `200415237`) show no fitted C99 body. A plausible
  bare horizontal pair repeats below D9 and left of R17: May joints near
  `(1440,1990)`/`(1600,1990)`, July joints near `(2508,1782)`/
  `(2680,1782)`. The right joint visibly links to R17's lower physical
  lead; the upper lead runs under D9 without a visible numbered pin
  junction. Corrected native D9 package anchors project the July C99
  left/right candidates near `(3038,1497)`/`(2868,1497)` in solder tile
  `200525009`, within about 5–7 px of separate joints `(3040,1492)`/
  `(2875,1495)`. A third joint near `(2818,1515)` matches R17 lower
  and has a short visible B.Cu link to the right C99 candidate. The
  older 40–55 px mismatch came from retired D9 component anchors.
  The left solder candidate has an uninterrupted B.Cu route to the
  third contact of D2's reflected left row, pin14, grounded by exact
  `.009` sheet 1. Three-feature geometry strongly favors the pair, but
  front-to-back same-hole identity and population need confirmation;
  owner ground continuity has not been metered.
  See `ref/photos/juku-pcb-2/c99-assembly-photo-review.json`.
- Remaining work is now narrow: identify the C99 physical landing and
  identify the upstream source shared by D7.5/D29.3. Native 5150x3603
  geometry closes D7.12 onto SYNC, D7.13 onto its pin11 feedback node, and D7.4
  onto MEMW/D29.8 without merging the crossed D29.3 rail. None of the
  remaining boundaries should be replaced by a simulator-only guess.
