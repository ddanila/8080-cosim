# FDC hardware handoff

Status: **BUS-SIDE GUARDED / OWNER CONTINUITY REQUIRED**

This generated report narrows the physical floppy-controller handoff to
the exact board points that still need owner or bench evidence. It does
not claim D93 interrupt mapping or D100 enable/direction gating are
hardware-verified; it separates the wired bus-side facts from the
remaining continuity asks.

## Command

```sh
python3 scripts/report_fdc_hardware_handoff.py
```

## Source

- Board JSON: `kicad/juku.board.json`
- D93 package: `КР1818ВГ93` / WD1793-compatible FDC
- D100 package: `КР580ВА87` / Intel 8287-compatible bus transceiver

## Bus-Side Handoff Checks

| Net / path | Status | Endpoint / purpose | Evidence boundary |
| --- | --- | --- | --- |
| `DB0` / `FDC_DAL0` | WIRED | `D100.1` <-> system DB; `D100.19` <-> `D93.7` | scan + WD1793/8287 datasheets |
| `DB1` / `FDC_DAL1` | WIRED | `D100.2` <-> system DB; `D100.18` <-> `D93.8` | scan + WD1793/8287 datasheets |
| `DB2` / `FDC_DAL2` | WIRED | `D100.3` <-> system DB; `D100.17` <-> `D93.9` | scan + WD1793/8287 datasheets |
| `DB3` / `FDC_DAL3` | WIRED | `D100.4` <-> system DB; `D100.16` <-> `D93.10` | scan + WD1793/8287 datasheets |
| `DB4` / `FDC_DAL4` | WIRED | `D100.5` <-> system DB; `D100.15` <-> `D93.11` | scan + WD1793/8287 datasheets |
| `DB5` / `FDC_DAL5` | WIRED | `D100.6` <-> system DB; `D100.14` <-> `D93.12` | scan + WD1793/8287 datasheets |
| `DB6` / `FDC_DAL6` | WIRED | `D100.7` <-> system DB; `D100.13` <-> `D93.13` | scan + WD1793/8287 datasheets |
| `DB7` / `FDC_DAL7` | WIRED | `D100.8` <-> system DB; `D100.12` <-> `D93.14` | scan + WD1793/8287 datasheets |
| `CS_FDC` | WIRED | D9.Y7 decode to D93 CS | sheet-3 delta plus board JSON |
| `IORD` / `IOWR` | WIRED | host read/write strobes to D93 | scan |
| `BA0` / `BA1` | WIRED | register select to D93 A0/A1 | scan |
| `FDC_DDEN` | OWNER-VERIFY | density control to D93 DDEN | MAME-derived PC4; cross-check on hardware |
| `FDC_INTRQ` | OWNER-VERIFY | D93 INTRQ to PIC IR0 | MAME-era assumption; owner continuity required |
| `FDC_DRQ` | OWNER-VERIFY | D93 DRQ to PIC IR1 | MAME-era assumption; owner continuity required |

## Remaining Owner Continuity Points

| Pin | Status | Needed fact | Current boundary |
| --- | --- | --- | --- |
| D93.19 `MR_N` | MISSING | master reset source | not netted in board JSON; owner continuity item |
| D93.24 `CLK` | MISSING | 1 MHz FDC clock rail | not netted in board JSON; owner continuity item |
| D100.9 `OE_N` | MISSING | 8287 output-enable gating | not netted in board JSON; owner continuity item |
| D100.11 `T` | MISSING | 8287 direction gating | not netted in board JSON; owner continuity item |

## Netted FDC Endpoints

| Net | Source | Endpoints |
| --- | --- | --- |
| `CS_FDC` | sheet-3 delta: CS7 (io 1C) -> ВГ93 on .009 | `D9.7, D93.3` |
| `FDC_DAL0` | datasheet (8287 B-side -> ВГ93 DAL) | `D100.19, D93.7` |
| `FDC_DAL1` | datasheet (8287 B-side -> ВГ93 DAL) | `D100.18, D93.8` |
| `FDC_DAL2` | datasheet (8287 B-side -> ВГ93 DAL) | `D100.17, D93.9` |
| `FDC_DAL3` | datasheet (8287 B-side -> ВГ93 DAL) | `D100.16, D93.10` |
| `FDC_DAL4` | datasheet (8287 B-side -> ВГ93 DAL) | `D100.15, D93.11` |
| `FDC_DAL5` | datasheet (8287 B-side -> ВГ93 DAL) | `D100.14, D93.12` |
| `FDC_DAL6` | datasheet (8287 B-side -> ВГ93 DAL) | `D100.13, D93.13` |
| `FDC_DAL7` | datasheet (8287 B-side -> ВГ93 DAL) | `D100.12, D93.14` |
| `FDC_DDEN` | mame (PC4 = density) | `D26.13, D93.37` |
| `FDC_DRQ` | assumed (MAME-era IR1; owner-verify) | `D93.38, D10.19` |
| `FDC_INTRQ` | assumed (MAME-era IR0; owner-verify) | `D93.39, D10.18` |
| `IORD` | scan; D9.5 detached (enable = REV, traced); D7.13 added (strobe-NAND input; 12/13 order assumed) | `D5.25, D26.5, D27.5, D11.13, D54.22, D55.22, D57.22, D10.3, ... (+3)` |
| `IOWR` | scan; D9.6 detached (G1 = RC-filtered D7.11, traced); D7.12 added (strobe-NAND input; order assumed) | `D5.27, D26.36, D27.36, D11.10, D54.23, D55.23, D57.23, D10.2, ... (+3)` |

## Disposition

- The system data bus, D100 B-side, D93 DAL bus, register select, I/O
  strobes, and CS7 decode are present in the board JSON and are guarded
  by this report.
- Before real FDC bring-up, continuity-check D93.39/38 to D10.18/19 to
  confirm INTRQ/DRQ ordering, then identify D93.19, D93.24, D100.9, and
  D100.11.
- Keep `docs/fdc-readiness.md` as the HDL/media behavior guard; this
  report is only the physical-board handoff checklist.
