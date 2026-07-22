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
| D9 region-enable inputs are tied to REV | PASS | native sheet-1 code-2 branch: D6.10/R13.2 -> D9.4/D9.5 |
| D9 select inputs are BA10..BA12 | PASS | `BA10`, `BA11`, `BA12` into D9.A/B/C |
| D7 fourth-gate inputs are wired to raw IOWR_N/IORD_N | PASS | `IOWR_RAW_N`/`IORD` inputs |
| D9 chip-select outputs are routed to the modeled peripherals | PASS | `CS_D10`..`CS_FDC`; measured D94.15/.3/.4 controls and corrected D94.2-D99.9/R89 node |
| D25 bus turnaround handoff is guarded | PASS | `D25_T`: D7.6 -> D25.11 |

## Pending Boundary Checks

| Boundary | Result | Current evidence |
| --- | --- | --- |
| D7 fourth-gate strobe inputs are source-proven | PASS | IORD_N/IOWR_N are on D7.9/D7.10; raw D5.27 is distinct from qualified D105.3 |
| C99 far physical pad is preserved without assuming ground | PASS | C99.1 is on V3_RC; native scan shows C99.2 as a conductor-less plate on singleton C99_FAR |
| D25_T MEMW input is source-proven without crossing-rail overmerge | PASS | Native sheet proves D7.4 -> MEMW/D29.1; D7.5 remains on the distinct -INHIB junction |
| D7.8 I/O-cycle qualifier and D105.3 qualified /WR are owner-closed | PASS | Owner continuity 2026-07-19 separates raw D5.27 from qualified D105.3 and closes D7.8 to D105.1/D6.15 |

## Current Decode Nets

| Net | Endpoints | Source note |
| --- | --- | --- |
| `PROM_EN` | `D7.11, D7.13, R17.2` | traced sheet-1 native 5150x3603 direct-junction review: D7 section 12,13->11 is a SYNC-gated feedback strobe; pin13 loops directly onto output pin11, and that shared node runs east into R17.2 (200R). The old scan link D7.11->D6.14 is refuted-assumed: D6 V1/V2 feed unread [chase] |
| `SYNC` | `D1.19, D38.12, D7.12` | wire plus sheet-1 native 5150x3603 direct T-junction: CPU D1.19 SYNC reaches D7 first-gate input pin12; WIRE 9 separately continues to D38.12 |
| `V3_RC` | `C99.1, D9.6, R17.1` | traced sheet-1 native 5150x3603 review: R17 top + C99 pin1/left plate + D9.6 share one junction; rail3 crosses above without a dot. RC-deglitched I/O strobe -> D9.G1. The visible C99 pin2/right plate has no outgoing conductor and is kept separately as C99_FAR rather than assumed grounded |
| `C99_FAR` | `C99.2` | sheet-1 native 5150x3603 review: C99 pin2/right plate is visibly present but ends without a drawn conductor; preserve the physical pad as a continuity boundary because an RC deglitch capacitor would not intentionally operate open-circuit |
| `REV` | `D6.10, D9.4, D9.5, R13.2` | native full-resolution sheet 1: D6.10 REV rail code 2 runs into the D9 pins-4+5 bridge and the upper labeled R13 1k pull-up branch. This is the I/O-decoder region enable (G2A_N+G2B_N tied): low for BA13-15=000 -> ports 00-1F pass, >=20 blocked |
| `BA10` | `D15.21, D16.21, D17.21, D18.21, D19.21, D20.21, D21.21, D22.21, D24.3, D4.19, ... (+2)` | scan; D6 endpoint removed (drawn: D6 pins 2/1/15 = mode-bundle tags 1/2/3, crop bios_hunt1) |
| `BA11` | `D15.23, D16.23, D17.23, D18.23, D19.23, D20.23, D21.23, D22.23, D24.4, D4.18, ... (+4)` | scan |
| `BA12` | `D15.2, D16.2, D17.2, D18.2, D19.2, D20.2, D21.2, D22.2, D24.5, D4.15, ... (+4)` | scan |
| `IOWR` | `D10.2, D105.3, D11.10, D26.36, D27.36, D29.5, D54.23, D55.23, D57.23, D94.13` | owner continuity 2026-07-19: D105 NAND output pin3 is the qualified active-low peripheral write rail. Its inputs are D7.8 I/O-cycle-active high and D13.4 CPU-write-active high. Directly confirmed endpoints are D94.13, D29.5, D10.2, D11.10, D26.36, and D27.36; existing sheet-derived PIT write endpoints remain on the same rail. D5.27 is the separate raw IOWR_N source into D7.10 |
| `IORD` | `D10.3, D11.13, D26.5, D27.5, D29.4, D29.8, D5.25, D54.22, D55.22, D57.22, ... (+2)` | scan sheet-1 full-resolution plus direct owner continuity 2026-07-15: D5.25 IORD runs into D7.9; D94.12/A2 joins D27.5/RD_N and D29.4. D29.4 conflicts with the older IOM_STATUS scan interpretation and is adopted from the physical board; recheck D29.4-D7.8, D29.4-D29.8, and D29.8-D27.5 later. D93.4 belongs only to D94.3 |
| `D25_T` | `D25.11, D7.6` | traced sheet-1 native 5150x3603 review: D7 ЛА3 section (pins 5,4 -> 6 with inversion circle) drives D25.T (pin 11) = the data-bus turnaround; pin4 drops past the D29.3 rail without a junction and terminates as a T on MEMW/D29 physical pin1, while pin5 meets D29.3 at an explicit junction whose upstream source remains unread. D25.E (9) -> GND like D23/D24 |
| `CS_D10` | `D10.1, D9.15` | prom |
| `CS_D26` | `D26.6, D9.14` | prom |
| `CS_D11` | `D11.11, D9.13` | prom |
| `CS_D27` | `D27.6, D9.12` | prom |
| `CS_D54` | `D54.21, D9.11` | prom |
| `CS_D55` | `D55.21, D9.10` | prom |
| `CS_D57` | `D57.21, D9.9` | prom |
| `CS_FDC` | `D9.7` | sheet-3 delta/MAME functional decode boundary; D93.3 was separated from this speculative net after local photo fit proved its direct D94.2-only branch; D93 remains the physical КР1818ВГ93 |

## Interpretation

- D9, not D2, is the physical I/O chip-select decoder in the current
  board model; this report guards that D2-as-I/O-decode is not revived.
- The I/O decoder enable is the traced D7.11 -> R17/C99 -> D9.6 path,
  with REV on D9.4/D9.5 and BA10..BA12 selecting the eight I/O groups.
- Remaining work is now narrow: read or continuity-check C99.2 and
  identify the upstream source shared by D7.5/D29.3. Native 5150x3603
  geometry closes D7.12 onto SYNC, D7.13 onto its pin11 feedback node, and D7.4
  onto MEMW/D29.1 without merging the crossed D29.3 rail. None of the
  remaining boundaries should be replaced by a simulator-only guess.
