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

## Current Evidence Checks

| Check | Result | Evidence |
| --- | --- | --- |
| Board identity names D94 as `.092`, not stale `.113` | PASS | `kicad/juku.board.json` type `RE3_PROM_092` |
| Address pins D94.10-D94.14 are traced | PASS | board JSON nets |
| DSN agrees on D94 power/address and lacks output nets | PASS | `kicad/juku.dsn` D94 pins |
| Enable pin D94.15 is traced | FAIL | board JSON nets |
| Any D94 output net is traced | FAIL | no D94 output nets in board JSON |
| `.092` firmware artifact exists | FAIL | `ref/firmware/` has no `.092` artifact |
| `.113/.117` scans are guarded as not-D94 | PASS | `docs/re3-firmware-inspection.md` |
| HDL placeholder is explicitly inert | PASS | `hdl/devices.v::re3_prom_092` |
| `juku_top` leaves D94 data outputs unconnected | PASS | `hdl/juku_top.v` |
| Video slot audit is still D94-pending | PASS | `docs/video-slot-timing-audit.md` |

## Reconstruction Boundary

- Known: D94 is present in the .009 FDC quadrant and its five address
  inputs are wired to `BA11..BA15`.
- Unknown: D94 pin 15 (`E_N`) and the eight D94 output destinations are
  not traced/netted in `kicad/juku.board.json` or `kicad/juku.dsn`, and no
  `ДГШ5.106.092` programming table or dump is present under
  `ref/firmware/`.
- Therefore a burnable D94 image is not derivable from current repo
  evidence. The correct next automatic action is to keep this constraint
  report fresh; the next data-unlocking action is an owner dump or a
  recovered programming-disk `.092` table.
- Do not reuse `.113` or `.117` as D94: those scans are guarded as
  `.106.103`-family evidence, not the processor-module `.092` content.
