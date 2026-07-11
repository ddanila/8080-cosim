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

## Photograph Applicability

The July owner-photo batches under `ref/photos/juku-pcb-2/` clearly show a
populated КР1818ВГ93, add an overlapping 3x3 solder-side grid, and include
a later component-side view with the known КР1818ВГ93 temporarily removed
from its socket to expose the footprint copper. The board is therefore
applicable physical evidence for the
FDC handoff. The grids are registered and D94/D93 have package-local fits.
The guarded D93 component fit specifically uses `PXL_20260710_202708344.jpg`,
taken with the known КР1818ВГ93 removed from its socket. It exposes all 40
contacts and the pin-40 end marking. A reflected solder fit then lands on the
actual joints; together they localize MR_N/pin19 and CLK/pin24 without
claiming their far destinations.
Continuous copper promotes the private D94.1/.2/.3 to D93.4/.3/.2 control
nets; no photographed branch supports the former global I/O-rail assumption.

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
| `FDC_RE_N` / `FDC_CS_N` / `FDC_WE_N` | WIRED | D94 D0-D2 private controls to D93 RE/CS/WE | two-sided local fits + continuous component copper |
| `BA0` / `BA1` | WIRED | register select to D93 A0/A1 | scan |
| `FDC_DDEN` | OWNER-VERIFY | density control to D93 DDEN | MAME-derived PC4; cross-check on hardware |
| `FDC_INTRQ` | OWNER-VERIFY | D93 INTRQ to PIC IR0 | MAME-era assumption; owner continuity required |
| `FDC_DRQ` | OWNER-VERIFY | D93 DRQ to PIC IR1 | MAME-era assumption; owner continuity required |

## D93 Source-Risk Pad Review

The two-sided package fits make the controller-end pad identity exact.
The available photographs do not show an unbroken path from these pads
to the modeled remote endpoints.

| Signal | D93 pin | Solder-image coordinate | Photograph result |
| --- | ---: | --- | --- |
| `FDC_DDEN` | 37 | `(1276.300, 1618.983) px` | pad and local copper identified; no photographed unbroken path to D26.13 / D6.15 |
| `FDC_DRQ` | 38 | `(1276.622, 1571.944) px` | pad and local copper identified; no photographed unbroken path to D10.19 |
| `FDC_INTRQ` | 39 | `(1276.944, 1524.906) px` | pad and local copper identified; no photographed unbroken path to D10.18 |

## Remaining Owner Continuity Points

| Pin | Status | Needed fact | Current boundary |
| --- | --- | --- | --- |
| D93.19 `MR_N` | MISSING | master reset source | photo with ВГ93 removed from its socket plus solder fit localizes the pad/departure; source remains unproved |
| D93.24 `CLK` | MISSING | 1 MHz FDC clock rail | photo with ВГ93 removed from its socket plus solder fit localizes the pad/fanout; clock source remains unproved |
| D100.9 `OE_N` | MISSING | 8287 output-enable gating | not netted in board JSON; owner continuity item |
| D100.11 `T` | MISSING | 8287 direction gating | not netted in board JSON; owner continuity item |

## Netted FDC Endpoints

| Net | Source | Endpoints |
| --- | --- | --- |
| `CS_FDC` | sheet-3 delta/MAME functional decode boundary; D93.3 removed after local photo fit proved its direct D94.2-only branch | `D9.7` |
| `FDC_CS_N` | July-2026 two-sided local fit + continuous component copper | `D94.2, D93.3` |
| `FDC_DAL0` | datasheet (8287 B-side -> ВГ93 DAL) | `D100.19, D93.7` |
| `FDC_DAL1` | datasheet (8287 B-side -> ВГ93 DAL) | `D100.18, D93.8` |
| `FDC_DAL2` | datasheet (8287 B-side -> ВГ93 DAL) | `D100.17, D93.9` |
| `FDC_DAL3` | datasheet (8287 B-side -> ВГ93 DAL) | `D100.16, D93.10` |
| `FDC_DAL4` | datasheet (8287 B-side -> ВГ93 DAL) | `D100.15, D93.11` |
| `FDC_DAL5` | datasheet (8287 B-side -> ВГ93 DAL) | `D100.14, D93.12` |
| `FDC_DAL6` | datasheet (8287 B-side -> ВГ93 DAL) | `D100.13, D93.13` |
| `FDC_DAL7` | datasheet (8287 B-side -> ВГ93 DAL) | `D100.12, D93.14` |
| `FDC_DDEN` | cross-source: sheet-1 D26 PC4/pin13 -> mode-bundle tag3 -> D6 A7/pin15; .009/MAME PC4 is also FDC density -> D93.37. July-2026 two-sided local D93 fit identifies pin37 and its local copper, but does not prove the far D26/D6 continuity | `D26.13, D93.37, D6.15` |
| `FDC_DRQ` | MAME-era IR1 mapping; July-2026 two-sided local D93 fit identifies pin38 and its local copper, but the available photos do not show an unbroken path to D10.19, so owner continuity remains required | `D93.38, D10.19` |
| `FDC_INTRQ` | MAME-era IR0 mapping; July-2026 two-sided local D93 fit identifies pin39 and its local copper, but the available photos do not show an unbroken path to D10.18, so owner continuity remains required | `D93.39, D10.18` |
| `FDC_RE_N` | July-2026 two-sided local fit + continuous component copper | `D94.1, D93.4` |
| `FDC_WE_N` | July-2026 two-sided local fit + continuous component copper | `D94.3, D93.2` |
| `IORD` | scan; D9.5 detached (enable = REV, traced); D7.13 added (strobe-NAND input; 12/13 order assumed); D93.4 removed after local photo fit proved its direct D94.1-only branch | `D5.25, D26.5, D27.5, D11.13, D54.22, D55.22, D57.22, D10.3, ... (+2)` |
| `IOWR` | scan; D9.6 detached (G1 = RC-filtered D7.11, traced); D7.12 added (strobe-NAND input; order assumed); D93.2 removed after local photo fit proved its direct D94.3-only branch | `D5.27, D26.36, D27.36, D11.10, D54.23, D55.23, D57.23, D10.2, ... (+2)` |

## Disposition

- The system data bus, D100 B-side, D93 DAL bus, register select, and
  private D94-to-D93 RE/CS/WE controls are present in board JSON and
  guarded by this report. Functional I/O decode into D94 remains blocked
  on pin 15, D3-D7 destinations, and the `.092` truth table.
- Before real FDC bring-up, continuity-check D93.39/38 to D10.18/19 to
  confirm INTRQ/DRQ ordering, then identify D93.19, D93.24, D100.9, and
  D100.11.
- Keep `docs/fdc-readiness.md` as the HDL/media behavior guard; this
  report is only the physical-board handoff checklist.
