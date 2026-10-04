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

The generator checks board-JSON endpoint contracts, recorded photo fits,
and evidence-record fields. It does not reread every schematic wire,
measure continuity, or execute HDL. Structural and runnable HDL coverage
is described in [FDC readiness](fdc-readiness.md).

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
actual joints. Chip-removed owner continuity supersedes the ambiguous `.009`
sheet-1 RES continuation: active-high CPU RESET enters D13.9 and D13.8
drives MR_N/pin19 plus the outer-bus contact. Reset polarity and the
controller endpoint are therefore closed; only the exact connector contact
code awaits X1 orientation reconciliation. Sheet 3 directly ties TEST/pin22
to WF/VFOE/pin33. CLK/pin24 is independently source-closed through D95.
Chip-removed owner continuity supersedes the mirrored photograph reading:
D94.3/.15/.4 drive D93.4/.3/.2, while D94.2 reaches D99.9/R89.
The old D94.1/.2/.3 photograph rows retain registration value only.

## Manufacturer Counter/Separator Constraint

Western Digital's June-1980 application note Figure 11 shows a minimal
FD1791/FD1793 counter/separator made from exactly these logic families:

| Reference function | Manufacturer device | Juku family match | State |
| --- | --- | --- | --- |
| raw-read pulse conditioner | 74123 | D97/D99/D102 К155АГ3 | D97/D102 source-closed; D99 section 1 held clear; section 2 access trigger/timing constrained, remote gates/outputs open |
| recovery counter | 74LS193 | D106 К555ИЕ7 | package family matched |
| read-clock toggle | 74LS74 | D96 КМ555ТМ2 | wiring closed; section-1 restart phase undefined; section-2 clear joins D99 B2, remote source open |

The manufacturer topology was useful as a search constraint, but the
recovered Juku sheet is authoritative for the actual wiring.

D96.8 (/Q2) reaches a proved isolated component-side test landing. Sheet 3
draws section 2 as the local DRQ/INTRQ path: D96.10/.12 share the
wired D28.10/.12/R95 node. D96.9 Q2 feeds D101 A0-A3; D96.11 CLK2 joins the D94.2/D99.9/R89.1 island in the full overview; this is a
physical continuity check. D96.13 /CLR2 joins D99.10 B2 at
a marked junction and shares their unresolved sheet-1 source.
Primary SN74LS74A truth makes the shared /PRE2/D2 node set-only
while /CLR2 is inactive:
condition low presets Q2, while condition high makes a CLK2 edge capture
one. The source-drawn pin13 clear conductor could reset Q2; its
remote source requires continuity and powered capture with pins8-12.
Sheet 3 directly closes section 1
as the active toggle: /Q pin6 feeds D pin2, D28.8 clocks pin3, Q pin5
drives D93.26 RCLK, and WREQ_N drives both asynchronous controls.
The last tie invokes the SN74LS74A both-asserted row, Q1=/Q1=high;
simultaneous release has no deterministic restart phase, although /Q
feedback divides by two after a recovered-clock edge resolves the state.
Exact-revision sheet 3 also restores the active D28 inverter sections
on pins 10-13, while it omits D98 buffer pair 4 (pins 9/10), D97 Q/pin13, and D102
/Q pin4. They are guarded intentional no-connects rather than continuity
requests. D28 and D98 are structural-only HDL cells and LVS-visible, including
all six inverter paths, five enabled status buffers, and the explicit D98 pair-4
no-connect. D99.3
(/CLR1) is physically grounded. D99.2 (B1) reaches a one-sided
component landing; exact sheet 3 draws E12 posts 2-3 selecting
D93.28/D100.3 HLD for B1. Physical E12 population is unproved. The
SN74123 contract holds Q1/pin13 low and
Q1_N/pin4 high, excluding section 1 as an active pulse conditioner.
Physical D94 D1 drives section-2 A_N low on either selected FDC read or
write; B2 retains a sheet-1 source boundary. Exact sheet 3 ties
Q2/pin5 to D100 A7/pin7, Q2_N/pin12 to D100 OE_N/pin9, and
CLR2_N/pin11 to the separate D26 MOTOR EN continuation; physical
continuity and powered timing remain to be checked.
The 4 still-open support devices are D96, D99, D100, and D101.

## Soviet VG93 Circuit Cross-Check

The original 1986 КР1818ВГ93 paper confirms that this is the actual Soviet
controller device and publishes its pin contract; it does not publish an
external separator schematic. A later technical-history reconstruction
collects period VG93 support circuits. Its Figure 16 shows a second
useful comparison circuit, but its preset and clear straps are not reused
where the primary Juku sheet differs.

Factory `.009` sheet 3 joins D106.7 to D28.9; D28.8 clocks
D96.3, and D96.5 supplies D93.26 RCLK. Sheet 3 joins D97.4/D93.27
RAW READ to D106.11 /LOAD and grounds D106.14 CLR.
D95.7 supplies D93.24 with selected 1/2 MHz, while D95.9 independently
supplies D106.4 with selected 4/8 MHz. D106 Q3 is not a D93.24 source.
See `ref/schematics/fdc-clock-mux-map.md` and
`ref/schematics/fdc-recovery-counter-map.md` plus
`ref/schematics/fdc-read-clock-toggle-map.md` for the exact tables.
The same full-resolution region restores the local interrupt path:
D93 DRQ/INTRQ drive D28.11/.13, wired open-collector outputs D28.10/.12
feed D96.10/.12 through the R95 pull-up, and R93 pulls INTRQ high.
D96.9 Q2 feeds D101 A0-A3; D96.11 CLK2 is source-joined to D94.2, while D96.13
shares D99.10 B2's sheet-1 boundary and needs its source identified.
D96.9 has no exposed local B.Cu departure. A later solder review identifies
a conditional D96.11-to-D28.11/DRQ route that conflicts with the drawing;
direct continuity must resolve it before changing either net. See
[D96 clock source review](d96-clock2-source-review.md).

Recovered `.009` Э3 sheet 3 closes Juku's write-precompensation chain:
D93.31 drives D97.10; D97 and D102 provide three delay taps to D101.10/.11/.12;
D93.17 EARLY and D93.18 LATE select them on D101.2/.14; D101.9 then drives
D100.6. The associated C16/C19/C20/C22 timing networks and R100/R102/R108
+5 V rail are also closed. Direct target copper remains authoritative for
D101.4-R92-R99, D101.7-D94.14 (R88 is separately owner-closed on
D94.3/D93.4), and physical R86=4.7 kΩ on C19.2/D97.6;
these override the electrical sheet's duplicated R99 reference, conflicting
R86=470 annotation, and tied-D101 drafting. See
`ref/schematics/fdc-write-precomp-map.md` for the exact source hierarchy and
`ref/schematics/fdc-unused-pin-dispositions.md` for the omitted outputs.

D106 setup is source-closed: R78 pulls pins 15/1/10/9 and UP/pin5 high;
D95.9 clocks DOWN/pin4, RAW READ loads pin11, and CLR/pin14 is grounded.
See [recovery counter map](../ref/schematics/fdc-recovery-counter-map.md).

### KP12 passive-network component-copper disposition

The calibrated component tile fixes all four factory-identified R92/R99
landings. A second target-board angle directly reads R92=`1К3` and
R99=`4К7`, corroborated by the registered July view. These values and
visible links are modeled; only D101 first-half `/OE0` and D00/D01/D03
remain open. Its selects and both outputs are source/owner-closed.

| Endpoint | Component coordinate | Modeled net | Disposition |
| --- | --- | --- | --- |
| R92.1 | (2341.000, 1317.000) | D101_D02_R92_R99 | ACCEPTED TARGET COPPER |
| R92.2 | (2564.000, 1314.000) | FDC_DDEN | ACCEPTED TARGET COPPER |
| R99.1 | (2064.000, 1370.000) | GND | ACCEPTED TARGET COPPER |
| R99.2 | (2287.000, 1367.000) | D101_D02_R92_R99 | ACCEPTED TARGET COPPER |

## Bus-Side Handoff Checks

| Net / path | Status | Endpoint / purpose | Evidence boundary |
| --- | --- | --- | --- |
| `DB0` | WIRED | system DB directly to `D93.7` | factory `.009` sheet 3 + WD1793 datasheet |
| `DB1` | WIRED | system DB directly to `D93.8` | factory `.009` sheet 3 + WD1793 datasheet |
| `DB2` | WIRED | system DB directly to `D93.9` | factory `.009` sheet 3 + WD1793 datasheet |
| `DB3` | WIRED | system DB directly to `D93.10` | factory `.009` sheet 3 + WD1793 datasheet |
| `DB4` | WIRED | system DB directly to `D93.11` | factory `.009` sheet 3 + WD1793 datasheet |
| `DB5` | WIRED | system DB directly to `D93.12` | factory `.009` sheet 3 + WD1793 datasheet |
| `DB6` | WIRED | system DB directly to `D93.13` | factory `.009` sheet 3 + WD1793 datasheet |
| `DB7` | WIRED | system DB directly to `D93.14` | factory `.009` sheet 3 + WD1793 datasheet |
| `FDC_RE_N` / `FDC_CS_N` / `FDC_WE_N` | WIRED | D94 D2/D3 to D93 RE/WE with R88/R87 pull-ups; D94 enable pin15 to D93 CS; D94 D1 to D99.9/R89 | direct owner continuity for all three controls and corrected D1 destination |
| D94.5 no-connect / `D93_1_OPEN_STUB` | WIRED | D94 output D4 is a PCB no-connect; D93.1 owns the short open stub | owner continuity plus full-resolution exposed-socket photograph recheck |
| `BA0` / `BA1` | WIRED | register select to D93 A0/A1 | scan |
| `FDC_DDEN` | OWNER-VERIFY | density control to D93 DDEN | exact .009 sheets 1 and 3; target-board continuity pending |
| `FDC_INTRQ` | WIRED | D93 INTRQ into local D28/R93 conditioner | exact .009 sheet 3 |
| `FDC_DRQ` | WIRED | D93 DRQ into local D28 conditioner and 10k R94 pull-up | exact .009 sheet 3 plus owner continuity/identification |
| `X2_IRQ0` / `X2_PB7` | WIRED | source-closed D10 IR0/IR1 external inputs (not assigned to FDC) | exact .009 sheet 1; retired as inferred FDC destinations |

## D93 Source-Risk Pad Review

The two-sided package fits make the controller-end pad identity exact.
DRQ/INTRQ feed the local D28/D96 conditioner, not D10 directly.

| Signal | D93 pin | D93 solder coordinate | Source endpoint | Physical boundary |
| --- | ---: | --- | --- | --- |
| `FDC_DDEN` | 37 | `(1558.533, 1620.917) px` | D26.13 | pad and local copper identified; source connection requires continuity |
| `FDC_DRQ` | 38 | `(1558.856, 1573.878) px` | D28.11/R94 | owner-closed DRQ to D28.11/R94 |
| `FDC_INTRQ` | 39 | `(1559.178, 1526.839) px` | D28.13/R93 | pad and local copper identified; source connection requires continuity |

## Remaining Owner Continuity Points

| Pin | Status | Needed fact | Current boundary |
| --- | --- | --- | --- |
| D10.22 `IR4` | BOUNDARY | stale tape-run continuation disposition | exact .009 sheet 1 labels (3) TAPE RUN INT, but replacement FDC sheet 3 has no matching continuation; ekta37 mask 0xDF keeps IR4 masked |
| D93.23 HLT / D93.25 RG | SOURCE-CLOSED | selected head-load timing and unused read-gate output | exact .009 sheet-3 overview traces D99.4 Q1_N to HLT/pin23 on a rail distinct from D94.14/D101.7 and E11; RG/pin25 is omitted between the explicit pin24/pin26 paths |
| D93.24 `CLK` | CONNECTED | source-selected 1/2 MHz FDC clock rail | recovered .009 sheet 3 closes D95.7 to D93.24; FM/MFM and 5-inch/8-inch select D40's traced 1/2 MHz divider rails independently of the D106 separator clock |
| D100.9 OE_N / D100.11 T | PARTIAL: OE_N SOURCE-CLOSED; T REMOTE UNKNOWN | separate drive-output-buffer controls | native .009 sheet 3 ties OE_N/pin9 to D99 Q2_N/pin12; T/pin11 has its own quoted sheet-1 continuation and crosses the OE_N path without a junction dot |

## Netted FDC Endpoints

| Net | Source | Endpoints |
| --- | --- | --- |
| `FDC_CLK` | recovered .009 Э3 sheet 3 directly joins D95 clock-mux output A/pin7 to D93 CLK/pin24; 5-inch/8-inch select A1=0 chooses the tied 1 MHz inputs and A1=1 chooses the tied 2 MHz inputs | `D95.7, D93.24` |
| `FDC_CS_N` | exact .009 sheet 1 draws D9.7 as CS7 to sheet 3; exact sheet 3 draws CS7 to D94 enable pin15 and D93 chip-select pin3. Direct owner continuity 2026-07-15 confirms D94.15 to D93.3 and isolates D94 output pin2 from this conductor | `D9.7, D94.15, D93.3` |
| `FDC_DDEN` | recovered .009 Э3 sheet 1 continuation 3 labels D26 PC4/pin13 FM/MFM; sheet 3 joins it to D93 DDEN/pin37 and D95 select A0/pin14. Registered target copper additionally closes R92.2 on the same pin14 node; D28.9 belongs to the separator and is not a DDEN branch | `D26.13, D93.37, D95.14, R92.2` |
| `FDC_DIR_TO_D100` | recovered .009 Э3 sheet 3: D93 DIR/pin16 directly drives D100 A2/pin1 | `D93.16, D100.1` |
| `FDC_DRIVE_SIZE_5_8` | recovered .009 Э3 sheet 1 continuation 2 identifies D26 PC3/pin17 as 5-inch/8-inch selection; sheet 3 directly joins it to D95 clock-mux select A1/pin2 | `D26.17, D95.2` |
| `FDC_DRQ` | recovered .009 Э3 sheet 3 and owner continuity 2026-07-20 directly join D93 DRQ/pin38, D28 open-collector inverter input pin11, and R94.1; physical R94 is the 10-kohm pull-up immediately above D28 and its other terminal joins +5 V. Owner solder photo 200506061 has a candidate D28.11-to-D96.11 B.Cu line conflicting with the exact-source separate DRQ and CLK2 nets; check the two pins directly before a model merge | `D93.38, D28.11, R94.1` |
| `FDC_DSEL_IN` | recovered .009 Э3 sheet 1 continuation 4 and sheet 3 directly join D26 PC5/pin12 D_SEL to D28 input pin1 | `D26.12, D28.1` |
| `FDC_EARLY_SEL` | recovered .009 Э3 sheet 3 directly joins D93 EARLY/pin17 to the common D101 select input A1/pin2 | `D93.17, D101.2` |
| `FDC_HLD_TO_D100` | recovered .009 Э3 sheet 3 photo PXL_20260718_101641055.jpg: D93 HLD/pin28 drives D100 A6/pin3 and E12 post 3; drawn E12 2-3 bridge connects D99 B1/pin2. Original-board E12 population and continuity are pending direct measurement. | `D93.28, D100.3, D99.2` |
| `FDC_IMDRG` | Exact .009 Э3 sheet-1 native PXL_20260718_101824181.MP.jpg labels D26 PA6/pin38 IMDRG with sheet-3 continuation (3); sheet-3 PXL_20260718_101648508.jpg labels the arriving conductor IMDRG (1) into D101 К555КП12 VA/OE0_N pin1. Original-board D26.38-D101.1 continuity is pending measurement. | `D26.38, D101.1` |
| `FDC_INDEX_STATUS` | recovered .009 Э3 sheet 3: D98 output pin5 directly drives D93 INDEX/pin35 | `D98.5, D93.35` |
| `FDC_INTRQ` | recovered .009 Э3 sheet 3 directly joins D93 INTRQ/pin39, D28 open-collector inverter input pin13, and R93=10k; R93's other terminal is +5 V | `D93.39, D28.13, R93.1` |
| `FDC_IRQ_CONDITIONED_N` | recovered .009 Э3 sheet 3 wires the open-collector D28 outputs pins10/12 together, pulls the node up through R95=2k, and feeds both D96 section-2 PRE_N/pin10 and D/pin12 | `D28.10, D28.12, D96.10, D96.12, R95.1` |
| `FDC_LATE_SEL` | recovered .009 Э3 sheet 3 directly joins D93 LATE/pin18 to the common D101 select input A0/pin14 | `D93.18, D101.14` |
| `FDC_MOTOR_EN` | Exact .009 Э3 sheet 1 MOTOR EN continuation from D26 PC2/pin16 enters D99 CLR2_N/pin11 on sheet 3; D100 A7/pin7 is driven separately by D99 Q2/pin5. Original-board D26.16-D99.11 continuity is pending measurement. | `D26.16, D99.11` |
| `FDC_PRECOMP_WRDATA` | exact .009 Э3 sheet 3 joins D101 Q1/pin9 to D100 A4/pin6 as the selected precompensated write-data channel; native crop of PXL_20260718_101648508 shows Q1/pin9 crossing Q0/pin7 without a dot near (1550,620), so the outputs are separate in the source; owner continuity closes Q0 to D94.14, while R88 is separately on D94.3/D93.4 | `D101.9, D100.6` |
| `FDC_RAW_READ` | recovered .009 Э3 sheet 3: D97 Q_N/pin4 directly drives D93 RAW READ/pin27 and D106 parallel-load input pin11 | `D97.4, D93.27, D106.11` |
| `FDC_RCLK` | recovered .009 Э3 sheet 3: D96 Q/pin5 directly drives D93 RCLK/pin26 | `D96.5, D93.26` |
| `FDC_READY` | Exact .009 Э3 sheet 3: D28 open-collector READY output pin6 drives D93 READY/pin32 and R84=470 pulls the node to +5 V through drawn E11 2-3 selection. D93 HLT/pin23 is on the separate D99.4 Q1_N rail, crossing E11 post 1 without a dot. | `D28.6, D93.32, R84.1` |
| `FDC_RESET_N` | chip-removed owner continuity 2026-07-20: D13 Schmitt inverter output pin8 drives D93 MR_N/pin19 and the physical outer-bus rightmost middle-row contact; exact connector code remains deliberately unassigned until X1 orientation is reconciled | `D13.8, D93.19` |
| `FDC_RE_N` | owner continuity 2026-07-19 proves D94 output pin3 reaches D93 read-enable pin4 and R88.1; R88.2 is +5 V | `D94.3, D93.4, R88.1` |
| `FDC_SEPARATOR_CLOCK` | recovered .009 Э3 sheet 3 directly joins D95 clock-mux output B/pin9 to D106 IE7 DOWN/pin4; the mux selects 8 MHz only for FM/MFM=0 and 5-inch/8-inch=0, otherwise 4 MHz | `D95.9, D106.4` |
| `FDC_SIDE_SEL` | recovered .009 Э3 sheet 1 continuation 5 and sheet 3: D26 PC6/pin11 drives D100 A8/pin8 S.SEL | `D26.11, D100.8` |
| `FDC_STEP_TO_D100` | recovered .009 Э3 sheet 3: D93 STEP/pin15 directly drives D100 A3/pin2 | `D93.15, D100.2` |
| `FDC_TG43_TO_D100` | recovered .009 Э3 sheet 3: D93 TG43/pin29 directly drives D100 A1/pin4 | `D93.29, D100.4` |
| `FDC_TR00_STATUS` | recovered .009 Э3 sheet 3: D98 output pin11 directly drives D93 TR00/pin34 | `D98.11, D93.34` |
| `FDC_WDATA_DELAY_IN` | recovered .009 Э3 sheet 3 directly joins D93 WDATA/pin31 to the first write-precomp delay stage D97 B2/pin10 | `D93.31, D97.10` |
| `FDC_WE_N` | owner continuity 2026-07-19 proves D94 output pin4 reaches D93 write-enable pin2 and R87.1; R87.2 is +5 V | `D94.4, D93.2, R87.1` |
| `FDC_WG_TO_D100` | recovered .009 Э3 sheet 3: D93 WG/pin30 directly drives D100 A5/pin5 | `D93.30, D100.5` |
| `FDC_WPRT_STATUS` | recovered .009 Э3 sheet 3: D98 output pin13 directly drives D93 WPRT/pin36 | `D98.13, D93.36` |
| `IORD` | scan sheet-1 full-resolution plus direct owner continuity 2026-07-15: D5.25 IORD runs into D7.9; D94.12/A2 joins D27.5/RD_N and D29.4. D29.4 conflicts with the older IOM_STATUS scan interpretation and is adopted from the physical board; recheck D29.4-D7.8, D29.4-D29.8, and D29.8-D27.5 later. D93.4 belongs only to D94.3 | `D5.25, D26.5, D27.5, D11.13, D54.22, D55.22, D57.22, D10.3, ... (+3)` |
| `IOWR` | owner continuity 2026-07-19: D105 NAND output pin3 is the qualified active-low peripheral write rail. Exact .009 detail 101805510 shows D7.11/PROM_EN and D105.3 on distinct local strokes; the former output-output join claim was a tracing error. Its inputs are D7.8 I/O-cycle-active high and D13.4 CPU-write-active high. Directly confirmed endpoints are D94.13, D29.5, D10.2, D11.10, D26.36, and D27.36; existing sheet-derived PIT write endpoints remain on the same rail. D5.27 is the separate raw IOWR_N source into D7.10 | `D105.3, D94.13, D29.5, D10.2, D11.10, D26.36, D27.36, D54.23, ... (+2)` |

## Disposition

- The direct system-data-bus to D93 DAL route, register select, and
  private D94-to-D93 RE/CS/WE controls are present in board JSON and
  guarded by this report. All D94 A0-A4 inputs and the private D93
  controls are owner-mapped. CS7 is source-closed from D9.7 to
  D94.15/D93.3; D0's hidden load remains unresolved. R87/R88/R89 and D3-D7 are
  owner/drawing-closed; the recorded D29.4/IORD recheck is optional
  corroboration. The `.092` table is physically captured.
- Before real FDC bring-up, confirm physical D96.9 Q2-to-D101 A0-A3
  continuity, D96.11 CLK2-to-D94.2/D99.9 continuity, and the source-drawn
  D96.13 /CLR2-to-D99.10 B2 join; identify the shared clear/B2 source separately. Capture WREQ_N at pins1/4 with Q1/pin5
  and /Q1/pin6 because simultaneous async release leaves restart phase
  undefined. Check the photographed D96.11-to-D28.11/DRQ candidate
  against the separate source nets; D96.9's onward physical route remains
  unproved. Sheet 3 establishes the local
  D28/R93/R95/D96 path. Primary device truth makes the shared
  /PRE2/D2 wiring set-only while /CLR2 is inactive; capture
  pins8-13 during request and acknowledge. D93.19 is source-connected to
  D13.8; active-high RESET enters D13.9 and is inverted for MR_N.
  D93.24 is
  source-closed through D95's selected 1/2 MHz clock section. The adopted
  archival D15/D16 pair fixes the replica to the direct-bus/NOP profile;
  physical D100 is not the profile selector. D99.10 and
  D100.11 have separate unresolved sheet-1 continuations, while
  D100.9 OE_N is source-closed to D99.12 Q2_N; D100.6's selected write-data input
  is source-closed through D101.9. See
  `docs/fdc-bus-polarity.md`.
- D93.23 HLT is source-joined to D99.4 Q1_N, separate from E11/READY; D93.25
  RG is source-proved unused/open. The remaining support-device boundaries
  are D96.9-to-D101 continuity, D96.11-to-D94.2 continuity, and the listed D99/D101 pins; D96.13 joins D99.10
  on a common sheet-1 boundary. D93.22/.33 are directly tied on sheet 3,
  and D93.15-.19/.26-.32/.34-.36 are source-connected.
  D28/D95/D97/D98/D102/D106 are source-closed. D96's local read-clock
  and drawn section-2 connections are source-closed. D96.9-to-D101 and
  D96.11-to-D94.2 physical continuity remain unverified, and the shared
  D96.13/D99.10 remote clear source is unresolved. Physical waveform quality
  remains a bring-up check.
  D93.40 to `P12V` is already owner-confirmed.
- Keep `docs/fdc-readiness.md` as the HDL/media behavior guard; this
  report is only the physical-board handoff checklist.
