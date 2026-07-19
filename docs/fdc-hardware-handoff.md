# FDC hardware handoff

Status: **BUS-SIDE GUARDED / OWNER CONTINUITY REQUIRED**

This generated report narrows the physical floppy-controller handoff to
the exact board points that still need owner or bench evidence. It does
not claim D93 interrupt mapping or the remaining support inputs are
hardware-verified; it separates the
wired bus-side facts from the remaining continuity asks.

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
Chip-removed owner continuity supersedes the mirrored photograph reading:
D94.3/.15/.4 drive D93.4/.3/.2, while D94.2 reaches D99.8/GND.
The old D94.1/.2/.3 photograph rows retain registration value only.

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

Except for the factory-proved separator chain below, these are
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

Factory `.009` sheet 1 resolves the apparent crossing: D106.7 reaches
D28.9, D28.8 clocks D96.3, and D96.5 supplies D93.26 RCLK. The older
photograph-only interpretation of a direct D106.7-D93.26 net is retired.
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
of their delay taps and the output inverter are not identified. Target-board
component copper now closes D95.14-R92.2, D101.4-R92.1-R99.2, and
R99.1-D101.8/GND, bounding part of the passive ladder without proving the
historical VG93 select assignment. Check the remaining select candidates
against D93.18/.17 and both pin-7 destinations. If either approaches
D28.5/.6, continuity must override the legacy-sheet NC assumption; the
current photographs do not prove that reuse.

The D106-D28-D96-D93 chain and the three passive-ladder links above are
promoted from primary factory/copper evidence. Remaining reference paths are guarded
candidates, not Juku continuity.

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

### D106 static straps and clock raw-crop disposition

The same calibrated tile was exhausted for the six remaining IE7 setup
checks. Pins 9/10 project beneath crossing rail metal, so apparent overlap
is not continuity. Pins 15/1/5 and pin 4 have identifiable local joints or
departures, but none remains visibly unbroken to a known power or clock
anchor. These are therefore bounded meter probes, not inferred straps.

| Endpoint | Reference expectation | Solder coordinate | Photograph result | Required proof |
| --- | --- | --- | --- | --- |
| D106.15 | HIGH | (1017.851, 1900.087) | LOCAL COPPER ONLY / P5V UNPROVED | continuity to a known P5V anchor |
| D106.1 | HIGH | (1156.155, 1855.000) | LOCAL COPPER ONLY / P5V UNPROVED | continuity to a known P5V anchor |
| D106.5 | HIGH | (1154.937, 2039.000) | LOCAL COPPER ONLY / P5V UNPROVED | continuity to a known P5V anchor |
| D106.10 | LOW | (1016.329, 2130.087) | RAIL-OBSCURED / GND UNPROVED | continuity to a known GND anchor |
| D106.9 | LOW | (1016.024, 2176.087) | RAIL-OBSCURED / GND UNPROVED | continuity to a known GND anchor |
| D106.4 | RECOVERY CLOCK | (1155.242, 1993.000) | LOCAL COPPER ONLY / CLOCK SOURCE UNPROVED | continuity to a known CLOCK SOURCE anchor |

### KP12 passive-network component-copper disposition

The calibrated component tile fixes all four factory-identified R92/R99
landings. A second target-board angle directly reads R92=`1К3` and
R99=`4К7`, corroborated by the registered July view. These values and
visible links are modeled; the mux select/output paths remain open.

| Endpoint | Component coordinate | Modeled net | Disposition |
| --- | --- | --- | --- |
| R92.1 | (2341.000, 1317.000) | D101_D02_R92_R99 | ACCEPTED TARGET COPPER |
| R92.2 | (2564.000, 1314.000) | D95_A0_R92 | ACCEPTED TARGET COPPER |
| R99.1 | (2064.000, 1370.000) | GND | ACCEPTED TARGET COPPER |
| R99.2 | (2287.000, 1367.000) | D101_D02_R92_R99 | ACCEPTED TARGET COPPER |

## Bus-Side Handoff Checks

| Net / path | Status | Endpoint / purpose | Evidence boundary |
| --- | --- | --- | --- |
| `DB0` | WIRED | system DB directly to `D93.7` | factory `.009` sheet 1 + WD1793 datasheet |
| `DB1` | WIRED | system DB directly to `D93.8` | factory `.009` sheet 1 + WD1793 datasheet |
| `DB2` | WIRED | system DB directly to `D93.9` | factory `.009` sheet 1 + WD1793 datasheet |
| `DB3` | WIRED | system DB directly to `D93.10` | factory `.009` sheet 1 + WD1793 datasheet |
| `DB4` | WIRED | system DB directly to `D93.11` | factory `.009` sheet 1 + WD1793 datasheet |
| `DB5` | WIRED | system DB directly to `D93.12` | factory `.009` sheet 1 + WD1793 datasheet |
| `DB6` | WIRED | system DB directly to `D93.13` | factory `.009` sheet 1 + WD1793 datasheet |
| `DB7` | WIRED | system DB directly to `D93.14` | factory `.009` sheet 1 + WD1793 datasheet |
| `FDC_RE_N` / `FDC_CS_N` / `FDC_WE_N` | WIRED | D94 D2/D3 to D93 RE/WE; D94 enable pin15 to D93 CS; D94 D1 grounded via D99.8 | direct owner continuity for all three controls and grounded D1 |
| `D94_D4` / D93.1 back-bias landing | WIRED | D94 output D4 to the wired D93 socket contact whose controller pin is internally NC/back-bias | exposed-socket component photograph with independent affine D94/D93 fits |
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
| `FDC_DDEN` | 37 | `(1558.533, 1620.917) px` | not locally fitted | pad and local copper identified; no photographed unbroken path to D26.13 (D6.15 explicitly excluded by continuity) |
| `FDC_DRQ` | 38 | `(1558.856, 1573.878) px` | `D10.19 (2622.154, 1305.000) px` | pad and local copper identified; no photographed unbroken path to D10.19 |
| `FDC_INTRQ` | 39 | `(1559.178, 1526.839) px` | `D10.18 (2677.615, 1305.000) px` | pad and local copper identified; no photographed unbroken path to D10.18 |

## Remaining Owner Continuity Points

| Pin | Status | Needed fact | Current boundary |
| --- | --- | --- | --- |
| D10.12/.13/.15/.20/.21/.22 | BOUNDARY | 8259 CAS0-2 and IR2-IR4 dispositions | standard КР580ВН59 contract and affine package fit are proved; CAS0-2 pins12/13/15 are explicit NCs, IR2/IR3 connect directly to D11 RXRDY/TXRDY, and only IR4 remains an off-sheet boundary |
| D93.15-.18/.22/.23/.25-.36 | BOUNDARY | step/precompensation, separator, head-load, drive status, and write interface | primary FD179X-01 contract and two-sided socket fits are proved; target-board support circuit remains untraced |
| D93.19 `MR_N` | BOUNDARY | master reset source | photo with the physical КР1818ВГ93 temporarily removed from its socket plus solder fit localizes the pad/departure; source remains unproved |
| D93.24 `CLK` | BOUNDARY | 1 MHz FDC clock rail | corrected D93 fit identifies pin24 and local westbound copper; both WD and Soviet VG93 references keep this main controller clock separate from the D106 recovered-clock path, but its upstream source remains unproved |
| D100.9/.11 continuation `1` | CONNECTED | shared drive-output-buffer control source | factory sheet proves pins 9/11 joined; upstream continuation remains untraced |

## Netted FDC Endpoints

| Net | Source | Endpoints |
| --- | --- | --- |
| `CS_FDC` | sheet-3 delta/MAME functional decode boundary; D93.3 was separated from this speculative net after local photo fit proved its direct D94.2-only branch; D93 remains the physical КР1818ВГ93 | `D9.7` |
| `FDC_CS_N` | direct owner continuity 2026-07-15 proves D94 enable pin15 reaches D93 chip-select pin3, and explicitly proves D94 output pin2 is isolated from this conductor. The upstream source is retained separately for later continuity | `D94.15, D93.3` |
| `FDC_DDEN` | recovered .009 Э3 sheet 1 continuation 3 labels D26 PC4/pin13 FM/MFM and sheet 3 joins that conductor directly to D93 DDEN/pin37; the same sheet proves D28.9 belongs to the separator and is not a DDEN branch | `D26.13, D93.37` |
| `FDC_DIR_TO_D100` | recovered .009 Э3 sheet 3: D93 DIR/pin16 directly drives D100 A2/pin1 | `D93.16, D100.1` |
| `FDC_DRIVE_SIZE_5_8_BOUNDARY` | recovered .009 Э3 sheet 1 continuation 2 identifies D26 PC3/pin17 as 5-inch/8-inch selection; the target-revision destination is not shown on sheet 3 | `D26.17` |
| `FDC_DRQ` | MAME-era IR1 mapping; July-2026 two-sided local D93 fit identifies pin38 and its local copper, but the available photos do not show an unbroken path to D10.19, so owner continuity remains required | `D93.38, D10.19` |
| `FDC_DSEL_IN` | recovered .009 Э3 sheet 1 continuation 4 and sheet 3 directly join D26 PC5/pin12 D_SEL to D28 input pin1 | `D26.12, D28.1` |
| `FDC_HLD_TO_D100` | recovered .009 Э3 sheet 3: D93 HLD/pin28 directly drives D100 A6/pin3 | `D93.28, D100.3` |
| `FDC_INDEX_STATUS` | recovered .009 Э3 sheet 3: D98 output pin5 directly drives D93 INDEX/pin35 | `D98.5, D93.35` |
| `FDC_INTRQ` | MAME-era IR0 mapping; July-2026 two-sided local D93 fit identifies pin39 and its local copper, but the available photos do not show an unbroken path to D10.18, so owner continuity remains required | `D93.39, D10.18` |
| `FDC_MOTOR_EN` | recovered .009 Э3 sheet 1 continuation 1 and sheet 3: D26 PC2/pin16 drives D100 A7/pin7 MOTOR EN | `D26.16, D100.7` |
| `FDC_RAW_READ` | recovered .009 Э3 sheet 3: D97 Q_N/pin4 directly drives D93 RAW READ/pin27 | `D97.4, D93.27` |
| `FDC_RCLK` | recovered .009 Э3 sheet 3: D96 Q/pin5 directly drives D93 RCLK/pin26 | `D96.5, D93.26` |
| `FDC_READY` | recovered .009 Э3 sheet 3: D28 READY inverter output pin6 directly drives D93 READY/pin32; the drawn R84 pull-up remains an unmodeled passive endpoint | `D28.6, D93.32` |
| `FDC_RE_N` | direct owner continuity 2026-07-15 proves D94 output pin3 reaches D93 read-enable pin4, superseding the mirrored-pin photo interpretation | `D94.3, D93.4` |
| `FDC_SIDE_SEL` | recovered .009 Э3 sheet 1 continuation 5 and sheet 3: D26 PC6/pin11 drives D100 A8/pin8 S.SEL | `D26.11, D100.8` |
| `FDC_STEP_TO_D100` | recovered .009 Э3 sheet 3: D93 STEP/pin15 directly drives D100 A3/pin2 | `D93.15, D100.2` |
| `FDC_TG43_TO_D100` | recovered .009 Э3 sheet 3: D93 TG43/pin29 directly drives D100 A1/pin4 | `D93.29, D100.4` |
| `FDC_TR00_STATUS` | recovered .009 Э3 sheet 3: D98 output pin11 directly drives D93 TR00/pin34 | `D98.11, D93.34` |
| `FDC_WE_N` | direct owner continuity 2026-07-15 proves D94 output pin4 reaches D93 write-enable pin2, superseding the mirrored-pin photo interpretation; D93 pin1 is internally NC/back-bias but its separate socket pad is routed from D94.5 | `D94.4, D93.2` |
| `FDC_WG_TO_D100` | recovered .009 Э3 sheet 3: D93 WG/pin30 directly drives D100 A5/pin5 | `D93.30, D100.5` |
| `FDC_WPRT_STATUS` | recovered .009 Э3 sheet 3: D98 output pin13 directly drives D93 WPRT/pin36 | `D98.13, D93.36` |
| `IORD` | scan sheet-1 full-resolution plus direct owner continuity 2026-07-15: D5.25 IORD runs into D7.9; D94.12/A2 joins D27.5/RD_N and D29.4. D29.4 conflicts with the older IOM_STATUS scan interpretation and is adopted from the physical board; recheck D29.4-D7.8, D29.4-D29.8, and D29.8-D27.5 later. D93.4 belongs only to D94.3 | `D5.25, D26.5, D27.5, D11.13, D54.22, D55.22, D57.22, D10.3, ... (+4)` |
| `IOWR` | scan sheet-1 full-resolution: D5.27 IOWR runs directly into D7 fourth-gate input pin10; D9.6 is RC-filtered G1; direct owner continuity assigns D93.2 only to D94.4 on the target revision | `D5.27, D26.36, D27.36, D11.10, D54.23, D55.23, D57.23, D10.2, ... (+1)` |

## Disposition

- The direct system-data-bus to D93 DAL route, register select, and
  private D94-to-D93 RE/CS/WE controls are present in board JSON and
  guarded by this report. All D94 A0-A4 inputs and the private D93
  controls are owner-mapped; remaining decode boundaries are the upstream
  pin-15 enable source, pull-up identities, D3-D7 destinations, and the
  recorded D29.4/IORD recheck. The `.092` table is physically captured.
- Before real FDC bring-up, continuity-check D93.39/38 to D10.18/19 to
  confirm INTRQ/DRQ ordering, then identify D93.19 and D93.24. First dump
  D15/D16 and identify its guarded CMA/NOP profile; the recovered direct
  D93 bus means physical D100 is not the profile selector. Separately trace
  shared D100.9/.11 continuation `1` and D100.6's write-data input; see
  `docs/fdc-bus-polarity.md`.
  Disposition D10 CAS0-2 and IR2-IR4 as connected or intentional
  NCs; SP/EN pin16 is already source-proved and modeled at +5 V.
- Trace every restored D93 drive-interface pin through D28/D95-D99/
  D101/D102/D106. D93.40 to `P12V` is already owner-confirmed.
  Pin 40 is a power-safety
  blocker, not an optional functional refinement.
  The existing photographs have been exhausted for this path: they prove
  local copper but not an unbroken connection to a known +12 V node.
- Keep `docs/fdc-readiness.md` as the HDL/media behavior guard; this
  report is only the physical-board handoff checklist.
