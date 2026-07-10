# D94 .092 reconstruction constraints

Status: **D94 RECONSTRUCTION CONSTRAINED / DUMP REQUIRED**

This generated report records what the repo can currently prove about
the .009 FDC-era `D94` К155РЕ3 PROM (`ДГШ5.106.092`) before attempting
any reverse-engineered or burnable replacement table.

## Command

```sh
python3 scripts/report_d94_reconstruction_constraints.py
```

## Address / Enable Pins

Board identity: D94 type is `RE3_PROM_092`.

Address summary: D94.10-D94.14 map to `BA11..BA15` in the board JSON.

| Pin | Role | Net | Source |
| ---: | --- | --- | --- |
| 10 | A0 | `BA11` | scan |
| 11 | A1 | `BA12` | scan |
| 12 | A2 | `BA13` | scan |
| 13 | A3 | `BA14` | scan |
| 14 | A4 | `BA15` | scan |
| 15 | E_N | - | MISSING |

## Output Pins

| Pin | Role | Net | Source |
| ---: | --- | --- | --- |
| 1 | D0 | - | not traced/netted |
| 2 | D1 | - | not traced/netted |
| 3 | D2 | - | not traced/netted |
| 4 | D3 | - | not traced/netted |
| 5 | D4 | - | not traced/netted |
| 6 | D5 | - | not traced/netted |
| 7 | D6 | - | not traced/netted |
| 9 | D7 | - | not traced/netted |

## KiCad DSN Cross-check

The routed DSN independently exposes only D94 power/ground and address
connections. It does not provide the missing enable/output nets.

| Pin | Role | DSN Net | Result |
| ---: | --- | --- | --- |
| 1 | D0 | - | missing in DSN |
| 2 | D1 | - | missing in DSN |
| 3 | D2 | - | missing in DSN |
| 4 | D3 | - | missing in DSN |
| 5 | D4 | - | missing in DSN |
| 6 | D5 | - | missing in DSN |
| 7 | D6 | - | missing in DSN |
| 8 | GND | `GND` | PASS |
| 9 | D7 | - | missing in DSN |
| 10 | A0 | `BA11` | PASS |
| 11 | A1 | `BA12` | PASS |
| 12 | A2 | `BA13` | PASS |
| 13 | A3 | `BA14` | PASS |
| 14 | A4 | `BA15` | PASS |
| 15 | E_N | - | missing in DSN |
| 16 | VCC | `P5V` | PASS |

## KiCad PCB Cross-check

The authoritative PCB file agrees with the DSN: D94 has power/ground and
address nets only; enable and all data outputs remain unnetted there too.

| Pin | Role | PCB Net | Result |
| ---: | --- | --- | --- |
| 1 | D0 | - | unnetted in PCB |
| 2 | D1 | - | unnetted in PCB |
| 3 | D2 | - | unnetted in PCB |
| 4 | D3 | - | unnetted in PCB |
| 5 | D4 | - | unnetted in PCB |
| 6 | D5 | - | unnetted in PCB |
| 7 | D6 | - | unnetted in PCB |
| 8 | GND | `GND` | PASS |
| 9 | D7 | - | unnetted in PCB |
| 10 | A0 | `BA11` | PASS |
| 11 | A1 | `BA12` | PASS |
| 12 | A2 | `BA13` | PASS |
| 13 | A3 | `BA14` | PASS |
| 14 | A4 | `BA15` | PASS |
| 15 | E_N | - | unnetted in PCB |
| 16 | VCC | `P5V` | PASS |

## Current Evidence Checks

| Check | Result | Evidence |
| --- | --- | --- |
| Board identity names D94 as `.092`, not stale `.113` | PASS | `kicad/juku.board.json` type `RE3_PROM_092` |
| Address pins D94.10-D94.14 are traced | PASS | board JSON nets |
| DSN agrees on D94 power/address and lacks output nets | PASS | `kicad/juku.dsn` D94 pins |
| PCB agrees on D94 power/address and lacks output nets | PASS | `kicad/juku.kicad_pcb` D94 footprint pads |
| `V3_RC` is present but not D94 enable/output evidence | PASS | board nodes `R17.1`, `C99.1`, `D9.6`; DSN/PCB D94 signal pins are not on `V3_RC` |
| Enable pin D94.15 is traced | FAIL | board JSON nets |
| Any D94 output net is traced | FAIL | no D94 output nets in board JSON |
| `.092` firmware artifact exists | FAIL | `ref/firmware/` has no `.092` artifact |
| Repository-wide `.092` artifact filename exists | FAIL | no `.092` / `106.092` artifact filename under ref/roms/media/docs/hdl/kicad/scripts/sync |
| Official .009 BOM/photo notes identify D94 as `.092` | PASS | `ref/photos/juku-pcb-2/BODGE-TRIAGE.md` |
| Reused D94 refdes/tape-cluster history is guarded | PASS | `ref/photos/juku-pcb-2/BODGE-TRIAGE.md` |
| `.113/.117` scans are guarded as not-D94 | PASS | `docs/re3-firmware-inspection.md` |
| HDL placeholder is explicitly inert | PASS | `hdl/devices.v::re3_prom_092` |
| `juku_top` leaves D94 data outputs unconnected | PASS | `hdl/juku_top.v` |
| Video slot audit is still D94-pending | PASS | `docs/video-slot-timing-audit.md` |

## Textual / Photo Survey Leads

- The official .009 BOM trail identifies the FDC-era D94 as the second
  К155РЕ3, programmed as `ДГШ5.106.092`.
- Earlier D94 references in the sheet-3/tape-cluster survey are known
  refdes reuse history, not evidence for the FDC-era timing PROM.
- The guarded firmware inspection establishes that `.113/.117` belong
  to the `.106.103`-family owner-scan evidence and are not a burnable
  D94 `.092` substitute.
- These textual leads establish identity and negative evidence only. They
  do not provide D94 pin 15, D0-D7 destinations, or PROM contents.
- The nearby `V3_RC` RC node is traced as `R17.1`, `C99.1`, and `D9.6`
  in board JSON/DSN, but D94 pin 15 and D0-D7 are not tied to it in
  board JSON, DSN, or PCB evidence. It cannot substitute for the missing
  D94 enable/output continuity.

## Address Space

D94 is a 32 x 8 PROM. The address pins are traced, so the reachable
rows are mechanically known, but every row byte is still unknown because
the D0-D7 destinations and `.092` programming table/dump are absent.

| Row | BA15 | BA14 | BA13 | BA12 | BA11 | D7..D0 |
| ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 00 | 0 | 0 | 0 | 0 | 0 | unknown |
| 01 | 0 | 0 | 0 | 0 | 1 | unknown |
| 02 | 0 | 0 | 0 | 1 | 0 | unknown |
| 03 | 0 | 0 | 0 | 1 | 1 | unknown |
| 04 | 0 | 0 | 1 | 0 | 0 | unknown |
| 05 | 0 | 0 | 1 | 0 | 1 | unknown |
| 06 | 0 | 0 | 1 | 1 | 0 | unknown |
| 07 | 0 | 0 | 1 | 1 | 1 | unknown |
| 08 | 0 | 1 | 0 | 0 | 0 | unknown |
| 09 | 0 | 1 | 0 | 0 | 1 | unknown |
| 10 | 0 | 1 | 0 | 1 | 0 | unknown |
| 11 | 0 | 1 | 0 | 1 | 1 | unknown |
| 12 | 0 | 1 | 1 | 0 | 0 | unknown |
| 13 | 0 | 1 | 1 | 0 | 1 | unknown |
| 14 | 0 | 1 | 1 | 1 | 0 | unknown |
| 15 | 0 | 1 | 1 | 1 | 1 | unknown |
| 16 | 1 | 0 | 0 | 0 | 0 | unknown |
| 17 | 1 | 0 | 0 | 0 | 1 | unknown |
| 18 | 1 | 0 | 0 | 1 | 0 | unknown |
| 19 | 1 | 0 | 0 | 1 | 1 | unknown |
| 20 | 1 | 0 | 1 | 0 | 0 | unknown |
| 21 | 1 | 0 | 1 | 0 | 1 | unknown |
| 22 | 1 | 0 | 1 | 1 | 0 | unknown |
| 23 | 1 | 0 | 1 | 1 | 1 | unknown |
| 24 | 1 | 1 | 0 | 0 | 0 | unknown |
| 25 | 1 | 1 | 0 | 0 | 1 | unknown |
| 26 | 1 | 1 | 0 | 1 | 0 | unknown |
| 27 | 1 | 1 | 0 | 1 | 1 | unknown |
| 28 | 1 | 1 | 1 | 0 | 0 | unknown |
| 29 | 1 | 1 | 1 | 0 | 1 | unknown |
| 30 | 1 | 1 | 1 | 1 | 0 | unknown |
| 31 | 1 | 1 | 1 | 1 | 1 | unknown |

## Reconstruction Boundary

- Known: D94 is present in the .009 FDC quadrant and its five address
  inputs are wired to `BA11..BA15`.
- Unknown: D94 pin 15 (`E_N`) and the eight D94 output destinations are
  not traced/netted in `kicad/juku.board.json`, `kicad/juku.dsn`,
  `kicad/juku.kicad_pcb`, or the audited text/photo notes, and no
  `ДГШ5.106.092` programming table or dump is present under the
  repository artifact scan.
- The traced `V3_RC` RC network is a negative cross-check here, not a
  replacement source for D94: its current nodes are `R17.1`, `C99.1`,
  and `D9.6`, with no D94 signal endpoint in JSON, DSN, or PCB.
- Content ambiguity alone is 256 unknown bits (`2^256` possible 32-byte
  PROM tables) before even assigning those bits to physical destination
  nets or enable timing.
- Therefore a burnable D94 image is not derivable from current repo
  evidence. The correct next automatic action is to keep this constraint
  report fresh; the next data-unlocking action is an owner dump or a
  recovered programming-disk `.092` table.
- Do not reuse `.113` or `.117` as D94: those scans are guarded as
  `.106.103`-family evidence, not the processor-module `.092` content.
