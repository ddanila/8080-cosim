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
- Primary pin source: `ref/wd1772-vg93/fd179x-01-datasheet.pdf`
- Primary application source: `ref/wd1772-vg93/fd179x-application-notes-jun1980.pdf`
- Primary Soviet device source: Kovalenko et al., `БИС контроллера КР1818ВГ93 для накопителя на гибком диске`, МПСС 1986 No. 3, pp. 3-8
- Historical circuit comparison: `https://atmturbo.nedopc.com/articles/kontroller_diskovoda_shemotehnika_210224.html`
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

## Manufacturer Counter/Separator Constraint

Western Digital's June-1980 application note Figure 11 shows a minimal
FD1791/FD1793 counter/separator made from exactly these logic families:

| Reference function | Manufacturer device | Juku family match | State |
| --- | --- | --- | --- |
| raw-read pulse conditioner | 74123 | D97/D99/D102 К155АГ3 | D99 section 1 excluded; remaining section not identified |
| recovery counter | 74LS193 | D106 К555ИЕ7 | package family matched |
| read-clock toggle | 74LS74 | D96 КМ555ТМ2 | section 2 excluded; target RCLK copper bypasses D96 |

The reference topology makes the following continuity checks high-value:
D106.3 (Q0) to D96.3 (CLK), D96.2 (D) to D96.6 (/Q), D96.5 (Q) to
D93.26 (RCLK), and one AG3 /Q output jointly to D93.27 (RAW READ) and
D106.11 (/LOAD). It also suggests checking D106 preset inputs
15/1 high and 10/9 low, CU pin5 high, CD pin4 to the recovery clock,
and CLR pin14 inactive.

Existing Juku photo constraints narrow, but do not close, that mapping.
D96.8 (/Q2) reaches a proved isolated component-side test landing, so
section 2 cannot supply the reference circuit's required /Q-to-D feedback;
D96 section 1 (pins 2/3/5/6) is the only physically available WD-toggle
section, but the target RCLK closure below proves that Juku did not use it
for that output. D99.3
(/CLR1) is physically grounded and D99.2 (B1) reaches another isolated
test landing, excluding D99 section 1 as the active raw-read conditioner.
The remaining AG3 sections still require continuity identification.

Except for the separately photo-proved Q3-to-RCLK path below, these are
**reference candidates, not promoted Juku nets**. The Juku
cluster contains two К555КП12 muxes and three К155АГ3 one-shots, whereas
Figure 11 contains no mux and only one half of a single 74123. The owner
photos identify the packages but do not prove the candidate paths end to
end; in particular D106 pins 9/10 are rail-obscured. Continuity or a
Juku-specific electrical sheet remains required before board-JSON changes.

## Soviet VG93 Circuit Cross-Check

The original 1986 КР1818ВГ93 paper confirms that this is the actual Soviet
controller device and publishes its pin contract; it does not publish an
external separator schematic. A later technical-history reconstruction
collects period VG93 support circuits. Its Figure 16 shows a second
high-value candidate that uses a К155ИЕ7-class counter without a ТМ2
toggle: raw read loads the counter at pin 11, a 4 MHz recovery clock enters
pin 4, pin 5 is held high, and Q3/pin 7 supplies VG93 RCLK/pin 26. The
parallel inputs are strapped 15/1 high and 10/9 low, while pin 14 is
controlled by WF/VFOE/pin 33.

The target board now chooses this branch: corrected independent package
fits place D106.7 and D93.26 on one uninterrupted solder-side trace in
`PXL_20260710_200506061.jpg`. This excludes the Western Figure-11
D96-toggle output as Juku's RCLK source, though D96 may have another role.
Calibrated review of the same raw solder tile finds no uninterrupted
same-layer path for D106.11-D93.27 or D106.14-D93.33. This rejects a
direct visible merge, not cross-layer continuity: both pairs remain meter
tests for hidden handoffs. In both references
D93.24 is the controller's separate
main clock input; D106 Q3 must not be treated as a candidate for D93.24.

The same historical comparison also shows a К555КП12-class write
precompensation selector: VG93 pins 18/17 reach mux select pins 2/14, mux
pin 1 is enabled low, and mux output pin 7 proceeds through an inverter to
drive write data. Juku's D95 and D101 match the mux family, but the source
of their delay taps and the output inverter are not identified. Check both
muxes against D93.18/.17 and their pin-7 destinations. If either approaches
D28.5/.6, continuity must override the legacy-sheet NC assumption; the
current photographs do not prove that reuse, so no target-board net changes
are made here.

Only D106.7-D93.26 is promoted from target-board copper. The remaining
Soviet-reference paths are guarded candidates, not Juku continuity.

### Separator candidate raw-crop disposition

All coordinates below are validated local-package fits in
`PXL_20260710_200506061.jpg`. The negative result prevents topology-only
promotion while preserving the exact cross-layer continuity request.

| Endpoint | Solder coordinate | Candidate peer | Disposition |
| --- | --- | --- | --- |
| D106.11 | (1016.633, 2084.087) | D93.27 | DIRECT PATH REJECTED / LAYER HANDOFF OPEN |
| D93.27 | (1555.311, 2091.306) | D106.11 | DIRECT PATH REJECTED / LAYER HANDOFF OPEN |
| D106.14 | (1017.546, 1946.087) | D93.33 | DIRECT PATH REJECTED / LAYER HANDOFF OPEN |
| D93.33 | (1557.244, 1809.072) | D106.14 | DIRECT PATH REJECTED / LAYER HANDOFF OPEN |

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

The D10 affine fit independently localizes the КР580ВН59 interrupt-input
contacts at the other end of the modeled DRQ/INTRQ nets.

| Signal | D93 pin | D93 solder coordinate | Remote component coordinate | Photograph result |
| --- | ---: | --- | --- | --- |
| `FDC_DDEN` | 37 | `(1558.533, 1620.917) px` | not locally fitted | pad and local copper identified; no photographed unbroken path to D26.13 / D6.15 |
| `FDC_DRQ` | 38 | `(1558.856, 1573.878) px` | `D10.19 (2622.154, 1305.000) px` | pad and local copper identified; no photographed unbroken path to D10.19 |
| `FDC_INTRQ` | 39 | `(1559.178, 1526.839) px` | `D10.18 (2677.615, 1305.000) px` | pad and local copper identified; no photographed unbroken path to D10.18 |

## Remaining Owner Continuity Points

| Pin | Status | Needed fact | Current boundary |
| --- | --- | --- | --- |
| D10.12/.13/.15/.20/.21/.22 | BOUNDARY | 8259 CAS0-2 and IR2-IR4 dispositions | standard КР580ВН59 contract and affine package fit are proved; CAS0-2 pins12/13/15 are explicit NCs, IR2/IR3 connect directly to D11 RXRDY/TXRDY, and only IR4 remains an off-sheet boundary |
| D93.15-.18/.22/.23/.25-.36 | BOUNDARY | step/precompensation, separator, head-load, drive status, and write interface | primary FD179X-01 contract and two-sided socket fits are proved; target-board support circuit remains untraced |
| D93.40 `VDD_12V` | BOUNDARY | +12 V controller supply continuity | primary datasheet requires +12 V; corrected two-sided fits identify pin 40; generated geometry ranks D14.8 and D32.8 as the closest proved P12V meter anchors, but continuity remains unproved |
| D93.19 `MR_N` | BOUNDARY | master reset source | photo with the physical КР1818ВГ93 temporarily removed from its socket plus solder fit localizes the pad/departure; source remains unproved |
| D93.24 `CLK` | BOUNDARY | 1 MHz FDC clock rail | corrected D93 fit identifies pin24 and local westbound copper; both WD and Soviet VG93 references keep this main controller clock separate from the D106 recovered-clock path, but its upstream source remains unproved |
| D100.9 `OE_N` | BOUNDARY | 8287 output-enable gating | singleton D100_OE_BOUNDARY in board JSON; owner continuity item |
| D100.11 `T` | BOUNDARY | 8287 direction gating | singleton D100_T_BOUNDARY in board JSON; owner continuity item |

## Netted FDC Endpoints

| Net | Source | Endpoints |
| --- | --- | --- |
| `CS_FDC` | sheet-3 delta/MAME functional decode boundary; D93.3 was separated from this speculative net after local photo fit proved its direct D94.2-only branch; D93 remains the physical КР1818ВГ93 | `D9.7` |
| `FDC_CS_N` | July-2026 two-sided local fit + continuous component copper | `D94.2, D93.3` |
| `FDC_DAL0` | datasheet (8287 B-side -> ВГ93 DAL) | `D100.19, D93.7` |
| `FDC_DAL1` | datasheet (8287 B-side -> ВГ93 DAL) | `D100.18, D93.8` |
| `FDC_DAL2` | datasheet (8287 B-side -> ВГ93 DAL) | `D100.17, D93.9` |
| `FDC_DAL3` | datasheet (8287 B-side -> ВГ93 DAL) | `D100.16, D93.10` |
| `FDC_DAL4` | datasheet (8287 B-side -> ВГ93 DAL) | `D100.15, D93.11` |
| `FDC_DAL5` | datasheet (8287 B-side -> ВГ93 DAL) | `D100.14, D93.12` |
| `FDC_DAL6` | datasheet (8287 B-side -> ВГ93 DAL) | `D100.13, D93.13` |
| `FDC_DAL7` | datasheet (8287 B-side -> ВГ93 DAL) | `D100.12, D93.14` |
| `FDC_DDEN` | cross-source: sheet-1 D26 PC4/pin13 -> mode-bundle tag3 -> D6 A7/pin15 and directly into D28 input pin9, whose paired open-collector output pin8 is labeled -FF/X4.1; .009/MAME PC4 is also FDC density -> D93.37. July-2026 two-sided local D93 fit identifies pin37 and its local copper, but does not prove the far D26/D6 continuity; the D28 output destination remains a target-board continuity boundary | `D26.13, D93.37, D6.15, D28.9` |
| `FDC_DRQ` | MAME-era IR1 mapping; July-2026 two-sided local D93 fit identifies pin38 and its local copper, but the available photos do not show an unbroken path to D10.19, so owner continuity remains required | `D93.38, D10.19` |
| `FDC_INTRQ` | MAME-era IR0 mapping; July-2026 two-sided local D93 fit identifies pin39 and its local copper, but the available photos do not show an unbroken path to D10.18, so owner continuity remains required | `D93.39, D10.18` |
| `FDC_RCLK` | July-2026 cross-package solder-photo closure: the corrected D106 К555ИЕ7 fit projects Q3/pin7 at (1154.329,2131.000) px and the independent D93 socket fit projects RCLK/pin26 at (1554.989,2138.344) px in PXL_20260710_200506061.jpg; one uninterrupted slightly sloped solder-side copper trace passes through both fitted contacts with no via, branch, or gap. The literal VG93 IE7-only reference independently matches Q3->RCLK, but the visible target-board copper is the promotion evidence | `D106.7, D93.26` |
| `FDC_RE_N` | July-2026 two-sided local fit + continuous component copper | `D94.1, D93.4` |
| `FDC_WE_N` | July-2026 two-sided local fit + continuous component copper | `D94.3, D93.2` |
| `IORD` | scan sheet-1 full-resolution: D5.25 IORD runs directly into D7 fourth-gate input pin9; D9.5 is REV enable, and D93.4 belongs only to D94.1 on the target revision | `D5.25, D26.5, D27.5, D11.13, D54.22, D55.22, D57.22, D10.3, ... (+2)` |
| `IOWR` | scan sheet-1 full-resolution: D5.27 IOWR runs directly into D7 fourth-gate input pin10; D9.6 is RC-filtered G1, and D93.2 belongs only to D94.3 on the target revision | `D5.27, D26.36, D27.36, D11.10, D54.23, D55.23, D57.23, D10.2, ... (+2)` |

## Disposition

- The system data bus, D100 B-side, D93 DAL bus, register select, and
  private D94-to-D93 RE/CS/WE controls are present in board JSON and
  guarded by this report. Functional I/O decode into D94 remains blocked
  on A0-A4/pins 10-14, pin 15, and D3-D7 destinations; the `.092`
  truth table itself is physically captured.
- Before real FDC bring-up, continuity-check D93.39/38 to D10.18/19 to
  confirm INTRQ/DRQ ordering, then identify D93.19, D93.24, D100.9, and
  D100.11. Disposition D10 CAS0-2 and IR2-IR4 as connected or intentional
  NCs; SP/EN pin16 is already source-proved and modeled at +5 V.
- Trace every restored D93 drive-interface pin through D28/D95-D99/
  D101/D102/D106, and prove D93.40 to `P12V`; start with the nearest
  proved anchors D14.8/D32.8, then confirm against A60.1 or X8.3.
  Pin 40 is a power-safety
  blocker, not an optional functional refinement.
  The existing photographs have been exhausted for this path: they prove
  local copper but not an unbroken connection to a known +12 V node.
- Keep `docs/fdc-readiness.md` as the HDL/media behavior guard; this
  report is only the physical-board handoff checklist.
