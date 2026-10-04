# I/O decode boundary

Status: **IO DECODE GUARDED / SMALL SOURCE BOUNDARIES PENDING**

This generated report isolates the sheet-1 I/O decode cluster.
It guards the current D9 К555ИД7 decoder model and the D7/R17/C99
strobe-enable path while keeping the small remaining source boundaries
visible.

## Command

Run from the repository root with Python 3 (standard library only).
The generator reads board JSON, HDL source, and the LVS map. It
overwrites this report with check results and exits with status 1
if any listed check fails.

```sh
python3 scripts/report_io_decode_boundary.py
```

## Guarded Checks

| Check | Result | Evidence |
| --- | --- | --- |
| D5 system-controller power endpoints are present in the source model | PASS | D5.14 GND / D5.28 +5V |
| D9 is the physical К555ИД7 I/O decoder | PASS | `kicad/juku.board.json` D9 provenance |
| Runnable HDL and LVS use the physical D9 identity and traced pins | PASS | U_D9: BA10/11/12, G1=V3_RC, G2A/G2B=REV; no placeholder refdes |
| D7 strobe-NAND output reaches the R17/C99 D9.G1 RC node | PASS | `PROM_EN` -> `V3_RC` |
| D7 first-gate SYNC/feedback topology is source-proven | PASS | D1.19 SYNC -> D7.12; D7.11 -> D7.13 feedback before R17 |
| D7 second-gate provenance preserves the owner-disproved D29.5 split | PASS | exact .009 joins D7.3 to D29.2; owner continuity separates D29.5 on qualified IOWR |
| D9 region-enable inputs are tied to REV | PASS | native sheet-1 code-2 branch: D6.10/R13.2 -> D9.4/D9.5 |
| D9 select inputs are BA10..BA12 | PASS | `BA10`, `BA11`, `BA12` into D9.A/B/C |
| D7 fourth-gate inputs are wired to raw IOWR_N/IORD_N | PASS | `IOWR_RAW_N`/`IORD` inputs |
| D9 chip-select outputs join the modeled peripheral source nets | PASS | `CS_D10`..`FDC_CS_N`; exact .009 CS7 path D9.7→D94.15/D93.3, owner-confirmed D94.15-D93.3, and corrected D94.2-D99.9/R89 node |
| D25 bus turnaround handoff is guarded | PASS | `D25_T`: D7.6 -> D25.11 |

## Boundary Evidence

| Boundary | Result | Current evidence |
| --- | --- | --- |
| D7 fourth-gate strobe inputs are source-proven | PASS | IORD_N/IOWR_N are on D7.9/D7.10; raw D5.27 is distinct from qualified D105.3 |
| C99 far plate uses the exact-sheet ground symbol | PASS | C99.1 is on V3_RC; C99.2 ground bar matches R16's ground symbol in the exact .009 sheet |
| D25_T MEMW input is source-proven without crossing-rail overmerge | PASS | Native sheet proves D7.4 -> MEMW/D29.8; D7.5 remains on the distinct -INHIB junction |
| D7.8 I/O-cycle qualifier and D105.3 qualified /WR are owner-closed | PASS | Owner continuity 2026-07-19 separates raw D5.27 from qualified D105.3 and closes D7.8 to D105.1/D6.15 |

## Current Decode Nets

Address rows show only the D9 decoder endpoint; other rows show all net
endpoints. Complete address nets and per-net provenance are retained in
[the board model](../kicad/juku.board.json).

| Net | Endpoints |
| --- | --- |
| `PROM_EN` | `D7.11, D7.13, R17.2` |
| `SYNC` | `D1.19, D38.12, D7.12` |
| `V3_RC` | `C99.1, D9.6, R17.1` |
| `REV` | `D6.10, D9.4, D9.5, R13.2` |
| `BA10` | `D9.1` |
| `BA11` | `D9.2` |
| `BA12` | `D9.3` |
| `IOWR` | `D10.2, D105.3, D11.10, D26.36, D27.36, D29.5, D54.23, D55.23, D57.23, D94.13` |
| `IORD` | `D10.3, D11.13, D26.5, D27.5, D29.4, D5.25, D54.22, D55.22, D57.22, D7.9, D94.12` |
| `D25_T` | `D25.11, D7.6` |
| `CS_D10` | `D10.1, D9.15` |
| `CS_D26` | `D26.6, D9.14` |
| `CS_D11` | `D11.11, D9.13` |
| `CS_D27` | `D27.6, D9.12` |
| `CS_D54` | `D54.21, D9.11` |
| `CS_D55` | `D55.21, D9.10` |
| `CS_D57` | `D57.21, D9.9` |
| `FDC_CS_N` | `D9.7, D93.3, D94.15` |

## Interpretation

- This generator checks source-model endpoints, provenance markers, HDL
  text and LVS mapping entries. It does not run LVS or simulation, inspect
  routed copper, or measure RC timing.
- D9 is the physical К555ИД7 I/O decoder; D2 is the separate bus/wait PROM.
  D7.11 feeds R17/C99 and D9.6, with REV on D9.4/.5 and BA10..BA12
  selecting the eight I/O groups.
- Structural HDL preserves D7.12=SYNC and D7.13 feedback from D7.11.
  Runnable HDL instead drives that gate with raw IOWR/IORD strobes to
  avoid a zero-delay feedback loop. R17 is modeled as a direct link;
  this simulation does not reproduce the physical strobe or RC delay.
- The [C99 photo review](../ref/photos/juku-pcb-2/c99-assembly-photo-review.json)
  preserves image identities, fit coordinates and the candidate bare pair.
  No fitted body is visible. The proposed solder hole has a visible route
  to source-grounded D2.14, but same-hole identity, population and metered
  ground continuity remain unconfirmed.
- D7.5/D29.3's upstream source remains unresolved. D7.12 joins SYNC,
  D7.13 feeds back from D7.11, and D7.4 joins MEMW/D29.8. Crossed rails
  without source or continuity evidence must remain separate.
