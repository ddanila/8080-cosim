# I/O decode boundary

Status date: 2026-07-13.

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
| D7 strobe-NAND output reaches the R17/C99 D9.G1 RC node | PASS | `PROM_EN` -> `V3_RC` |
| D9 region-enable inputs are tied to REV | PASS | `REV`: D6.10 -> D9.4/D9.5 |
| D9 select inputs are BA10..BA12 | PASS | `BA10`, `BA11`, `BA12` into D9.A/B/C |
| D7 input strobes are wired to IOWR/IORD | PASS | `IOWR`/`IORD` fanout |
| D9 chip-select outputs are routed to the modeled peripherals | PASS | `CS_D10`..`CS_FDC` plus private D94-to-D93 controls |
| D25 bus turnaround handoff is guarded | PASS | `D25_T`: D7.6 -> D25.11 |

## Pending Boundary Checks

| Boundary | Result | Current evidence |
| --- | --- | --- |
| D7 fourth-gate strobe inputs are source-proven | PASS | IORD/IOWR are on D7.9/D7.10 from the full-resolution sheet |
| C99 far physical pad is preserved without assuming ground | PASS | C99.1 is on V3_RC; native scan shows C99.2 as a conductor-less plate on singleton C99_FAR |
| D25_T input scan chase is exhausted without inventing a merge | PASS | Native-resolution review leaves D7.5/D7.4 in an unlabeled dense crossing bundle |

## Current Decode Nets

| Net | Endpoints | Source note |
| --- | --- | --- |
| `PROM_EN` | `D7.11, R17.2` | traced sheet-1 (crops r17_west/d7_feed_origins/rc_stack: D7 section 12,13->11 output runs east into R17 200R). The old scan link D7.11->D6.14 is refuted-assumed: D6 V1/V2 feed unread [chase]; D6 modeled always-enabled |
| `V3_RC` | `C99.1, D9.6, R17.1` | traced sheet-1 native 5150x3603 review: R17 top + C99 pin1/left plate + D9.6 share one junction; rail3 crosses above without a dot. RC-deglitched I/O strobe -> D9.G1. The visible C99 pin2/right plate has no outgoing conductor and is kept separately as C99_FAR rather than assumed grounded |
| `C99_FAR` | `C99.2` | sheet-1 native 5150x3603 review: C99 pin2/right plate is visibly present but ends without a drawn conductor; preserve the physical pad as a continuity boundary because an RC deglitch capacitor would not intentionally operate open-circuit |
| `REV` | `D6.10, D9.4, D9.5, R13.2` | traced sheet-1 (crops d9_inputs/v3_junction: D6.10 REV rail code 2, 1k pullup, drops at x~1845 and runs east into the D9 pins-4+5 bridge) = the io-decoder region enable (G2A_N+G2B_N tied). Low for BA13-15=000 -> io ports 00-1F pass, >=20 blocked; +R13 1k pullup (v3_junction; R13/R14 pairing order assumed) |
| `BA10` | `D15.21, D16.21, D17.21, D18.21, D19.21, D20.21, D21.21, D22.21, D24.3, D4.12, ... (+2)` | scan; D6 endpoint removed (drawn: D6 pins 2/1/15 = mode-bundle tags 1/2/3, crop bios_hunt1) |
| `BA11` | `D15.23, D16.23, D17.23, D18.23, D19.23, D20.23, D21.23, D22.23, D24.4, D4.13, ... (+5)` | scan |
| `BA12` | `D15.2, D16.2, D17.2, D18.2, D19.2, D20.2, D21.2, D22.2, D24.5, D4.16, ... (+5)` | scan |
| `IOWR` | `D10.2, D11.10, D26.36, D27.36, D29.8, D5.27, D54.23, D55.23, D57.23, D7.10` | scan sheet-1 full-resolution: D5.27 IOWR runs directly into D7 fourth-gate input pin10; D9.6 is RC-filtered G1, and D93.2 belongs only to D94.3 on the target revision |
| `IORD` | `D10.3, D11.13, D26.5, D27.5, D29.7, D5.25, D54.22, D55.22, D57.22, D7.9` | scan sheet-1 full-resolution: D5.25 IORD runs directly into D7 fourth-gate input pin9; D9.5 is REV enable, and D93.4 belongs only to D94.1 on the target revision |
| `D25_T` | `D25.11, D7.6` | traced sheet-1 native 5150x3603 review (crop s1_egates2): D7 ЛА3 section (pins 5,4 -> 6 with inversion circle) drives D25.T (pin 11) = the data-bus turnaround; both inputs enter the dense westbound crossing bundle without a unique label or junction, so each source remains a deliberate boundary after the 2026-07-13 full-sheet recheck. D25.E (9) -> GND like D23/D24 |
| `CS_D10` | `D10.1, D9.15` | prom |
| `CS_D26` | `D26.6, D9.14` | prom |
| `CS_D11` | `D11.11, D9.13` | prom |
| `CS_D27` | `D27.6, D9.12` | prom |
| `CS_D54` | `D54.21, D9.11` | prom |
| `CS_D55` | `D55.21, D9.10` | prom |
| `CS_D57` | `D57.21, D9.9` | prom |
| `CS_FDC` | `D9.7` | sheet-3 delta/MAME functional decode boundary; D93.3 removed after local photo fit proved its direct D94.2-only branch |

## Interpretation

- D9, not D2, is the physical I/O chip-select decoder in the current
  board model; this report guards that D2-as-I/O-decode is not revived.
- The I/O decoder enable is the traced D7.11 -> R17/C99 -> D9.6 path,
  with REV on D9.4/D9.5 and BA10..BA12 selecting the eight I/O groups.
- Remaining work is now narrow: trace the independent D7.12/D7.13
  boundaries, read or continuity-check C99.2, and trace D7.5/D7.4 for
  D25_T by continuity or stronger imagery. The native 5150x3603 sheet
  was rechecked end-to-end on 2026-07-13; the D25_T inputs enter a dense
  crossing bundle without unique labels or junctions, so further automated
  scan chasing is exhausted. None should be replaced by a simulator-only guess.
