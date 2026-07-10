# I/O decode boundary

Status date: 2026-07-10.

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
| D9 is the physical К555ИД7 I/O decoder | PASS | `kicad/juku.board.json` D9 provenance |
| D7 strobe-NAND output reaches the R17/C99 D9.G1 RC node | PASS | `PROM_EN` -> `V3_RC` |
| D9 region-enable inputs are tied to REV | PASS | `REV`: D6.10 -> D9.4/D9.5 |
| D9 select inputs are BA10..BA12 | PASS | `BA10`, `BA11`, `BA12` into D9.A/B/C |
| D7 input strobes are wired to IOWR/IORD | PASS | `IOWR`/`IORD` fanout |
| D9 chip-select outputs are routed to the modeled peripherals | PASS | `CS_D10`..`CS_FDC` |
| D25 bus turnaround handoff is guarded | PASS | `D25_T`: D7.6 -> D25.11 |

## Pending Boundary Checks

| Boundary | Result | Current evidence |
| --- | --- | --- |
| D7 strobe input order is still assumed | PASS | IOWR/ IORD are on D7.12/D7.13; source note keeps order assumed |
| C99 far plate is still not source-proven | PASS | C99.1 is on V3_RC; C99.2 is electrically implied return but drawn far end is ambiguous |
| D25_T source inputs remain unread | PASS | D7.5/D7.4 input source is not promoted by this report |

## Current Decode Nets

| Net | Endpoints | Source note |
| --- | --- | --- |
| `PROM_EN` | `D7.11, R17.2` | traced sheet-1 (crops r17_west/d7_feed_origins/rc_stack: D7 section 12,13->11 output runs east into R17 200R). The old scan link D7.11->D6.14 is refuted-assumed: D6 V1/V2 feed unread [chase]; D6 modeled always-enabled |
| `V3_RC` | `C99.1, D9.6, R17.1` | traced sheet-1 (rc_stack 6x: R17 top + C99 left plate + the D9.6 vertical share one junction; rail-3 crosses above WITHOUT a dot). RC-deglitched io-strobe -> D9.G1. C99.2 -> GND [electrically-implied deglitch return; drawn far end ambiguous at (4335,2120-2500)/300dpi, crop s1_c99_east — flagged] |
| `REV` | `D6.10, D9.4, D9.5, R13.2` | traced sheet-1 (crops d9_inputs/v3_junction: D6.10 REV rail code 2, 1k pullup, drops at x~1845 and runs east into the D9 pins-4+5 bridge) = the io-decoder region enable (G2A_N+G2B_N tied). Low for BA13-15=000 -> io ports 00-1F pass, >=20 blocked; +R13 1k pullup (v3_junction; R13/R14 pairing order assumed) |
| `BA10` | `D15.21, D16.21, D17.21, D18.21, D19.21, D20.21, D21.21, D22.21, D24.3, D4.12, ... (+2)` | scan; D6 endpoint removed (drawn: D6 pins 2/1/15 = mode-bundle tags 1/2/3, crop bios_hunt1) |
| `BA11` | `D15.23, D16.23, D17.23, D18.23, D19.23, D20.23, D21.23, D22.23, D24.4, D4.13, ... (+5)` | scan |
| `BA12` | `D15.2, D16.2, D17.2, D18.2, D19.2, D20.2, D21.2, D22.2, D24.5, D4.16, ... (+5)` | scan |
| `IOWR` | `D10.2, D11.10, D26.36, D27.36, D29.8, D5.27, D54.23, D55.23, D57.23, D7.12, ... (+1)` | scan; D9.6 detached (G1 = RC-filtered D7.11, traced); D7.12 added (strobe-NAND input; order assumed) |
| `IORD` | `D10.3, D11.13, D26.5, D27.5, D29.7, D5.25, D54.22, D55.22, D57.22, D7.13, ... (+1)` | scan; D9.5 detached (enable = REV, traced); D7.13 added (strobe-NAND input; 12/13 order assumed) |
| `D25_T` | `D25.11, D7.6` | traced sheet-1 300dpi (crop s1_egates2): D7 ЛА3 section (pins 5,4 -> 6 with inversion circle) drives D25.T (pin 11) = the data-bus turnaround; section inputs = next hop west [unread]. D25.E (9) -> GND like D23/D24 |
| `CS_D10` | `D10.1, D9.15` | prom |
| `CS_D26` | `D26.6, D9.14` | prom |
| `CS_D11` | `D11.11, D9.13` | prom |
| `CS_D27` | `D27.6, D9.12` | prom |
| `CS_D54` | `D54.21, D9.11` | prom |
| `CS_D55` | `D55.21, D9.10` | prom |
| `CS_D57` | `D57.21, D9.9` | prom |
| `CS_FDC` | `D9.7, D93.3` | sheet-3 delta: CS7 (io 1C) -> ВГ93 on .009 |

## Interpretation

- D9, not D2, is the physical I/O chip-select decoder in the current
  board model; this report guards that D2-as-I/O-decode is not revived.
- The I/O decoder enable is the traced D7.11 -> R17/C99 -> D9.6 path,
  with REV on D9.4/D9.5 and BA10..BA12 selecting the eight I/O groups.
- Remaining work is now narrow: confirm D7.12/D7.13 order if needed,
  read or continuity-check C99.2, and trace the D7.5/D7.4 sources for
  D25_T. None of those should be replaced by a simulator-only guess.
