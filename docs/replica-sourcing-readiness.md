# Replica sourcing readiness

Status: **PARTIAL / PROGRAMMING AND REVIEW BLOCKED**

Source: `docs/replica-dual-config-bom.csv`.

This report classifies BOM rows for sourcing and bench acceptance.
Its status is derived from the presence of populated programming types
and mechanical/circuit-review action rows, including unpopulated rows.
It does not verify firmware contents, purchased stock, or completed tests.
Validated PROM tables are available; programming rows remain gated until
device selection and programming/verify evidence are recorded. Check
prices, live stock, and seller provenance at order time.

Refresh with `python3 kicad/report_replica_sourcing_readiness.py`.

## Summary

- BOM lines: 122
- Populate-now component positions: 273
- Long-lead/source-early lines: 22
- Programming/dump-gated lines: 5
- Mechanical/circuit-review lines: 35
- Order posture: do not treat as a complete kit until the gated rows below are closed

## Action Totals

| Action | BOM lines | Populate-now positions |
| --- | ---: | ---: |
| circuit-review | 23 | 27 |
| leave-empty | 3 | 0 |
| mechanical-review | 12 | 17 |
| program/dump | 5 | 6 |
| source-now | 79 | 223 |

## Buy Early / Acceptance-Test First

| Type | Authentic part | Functional substitute | Populate now | Refs | Acceptance note |
| --- | --- | --- | ---: | --- | --- |
| BUF8286 | КР580ВА86 | Intel 8286 / compatible bus transceiver | 3 | D4, D29, D107 | Continuity/orientation check; verify no bus fight during first ROM fetch. |
| BUF8287 | КР580ВА87 | Intel 8287 / compatible bus transceiver | 1 | D100 | Continuity/orientation check; verify the recovered drive-output channels and shared control before attaching X4. |
| CPU8080 | КР580ИК80А | Intel 8080A / compatible 8080 CPU | 1 | D1 | Run in a known-good 8080 tester or minimal NOP/ROM-fetch jig before seating. |
| IR82 | КР580ИР82 | 8282/8283-class latch; verify polarity/package | 1 | D58 | Verify latch polarity around DRAM write-data path. |
| PIC8259 | КР580ВН59 | 8259A PIC | 1 | D10 | Socket; verify frame interrupt vectoring before FDC IRQs. |
| PIT8253 | КР580ВИ53 | 8253 or 8254 PIT | 3 | D54, D55, D57 | Socket; verify programmed divisors and video-sync outputs. |
| PPI8255 | КР580ВВ55А | 8255A / 82C55 PPI | 2 | D26, D27 | Socket; verify keyboard/Port C mode bits against twin during bring-up. |
| RU5 | К565РУ5Г | Mostek MK4564-12 dual-in-line option; E4 2-3/+5 V required; bench-test received parts | 8 | D84, D85, D86, D87, D88, D89, D90, D91 | MK4564-12 static compatibility is guarded; require E4 2-3/+5 V and buy tested DIP spares only after approval. |
| SYS8238 | КР580ВК38 | 8228/8238-class system controller; verify pinout | 1 | D5 | Verify pin-compatible 8228/8238 behavior; check MEMR/IO strobes in a socketed bring-up. |
| USART8251 | КР580ВВ51А | 8251A / 82C51-class USART | 1 | D11 | Socket; loopback test after clock/reset are proven. |
| VABUS | КР580ВА87 | Intel 8287 / compatible bus transceiver | 3 | D23, D24, D25 | Continuity/orientation check on expansion bus transceivers. |
| VG93_FDC | КР1818ВГ93 | Western Digital FD1793B-01 plastic DIP; bench-verify clocks, strobes, and drive interface | 1 | D93 | FD1793B-01 static compatibility is guarded; socket it and bench-verify clocks, strobes, support logic, and drive interface before approval. |
| XTAL | РК-171 16 MHz crystal 16 МГц | 16 MHz HC-49/metal-can crystal matching footprint/load | 1 | Z1 | Verify 16 MHz oscillation and load-cap fit before debugging timing. |

## Programming / Dump Gate

These rows are required for a complete functional kit, but their contents
must come from validated physical tables or deterministic functional
EPROM images, with programming-disk copies retained as corroboration.

| Type | Authentic part | Populate now | Refs | Gate |
| --- | --- | ---: | --- | --- |
| DEC_PROM | КР556РТ4А | 1 | D6 | Program from the preservation-grade physical D6 `.038` table recovered by three matching reads, including a power-cycled capture; compare with a future programming-disk file when available. |
| EPROM8K | 2764/M2764-class EPROM in .009 build; К573РФ5 on .006 BOM | 2 | D15, D16 | Program D15/D16 for the .009 build; leave D17-D22 empty unless authentic-completeness build is chosen. |
| RE3_PROM | К155РЕ3 | 1 | D8 | Program D8 from the validated physical `.039` table; do not use the superseded reconstruction. |
| RE3_PROM_092 | К155РЕ3 | 1 | D94 | Program D94 from the validated physical `.092` table; its unresolved circuit continuity still blocks hardware release. |
| WAIT_PROM | КР556РТ4А | 1 | D2 | Program from the preservation-grade physical D2 `.037` table recovered by six independent accepted acquisitions, including a power-cycled capture. |

## Review Before Buying Blind

These rows should not be converted directly into a vendor cart. They need
exact mechanical fit, interface-voltage, circuit-role, or value confirmation
against drawings/board photos before ordering final quantities.

| Action | Type | Authentic part | Populate now | Refs | Note |
| --- | --- | --- | ---: | --- | --- |
| circuit-review | AP2 | К170АП2 | 2 | D14, D32 | RS-232/line-driver substitute required; verify +/-12 V interface |
| circuit-review | C_ELEC | axial electrolytic | 3 | C31, C32, C33 | modern electrolytic matching measured body, lead spacing, value, voltage, and polarity |
| circuit-review | C_KM | КМ ceramic capacitor | 1 | C20 | Sheet 3 specifies 22 pF nominal; owner angles show bare 22 and ±5% on the body, but the unit is unverified. Confirm capacitance before sourcing. |
| circuit-review | C_KM | КМ ceramic capacitor | 1 | C22 | Sheet 3 specifies 22 pF nominal; later owner angles show bare 22 and ±10% on the body, but the unit is unverified. The May face reads М75, the negative 75 ppm/°C ceramic temperature-stability group. Confirm capacitance before sourcing. |
| circuit-review | C_KM | КМ ceramic capacitor | 0 | C4 | Fitted gray C4 beside C73; body value, lower lead net, and exact owner holes require measurement. |
| circuit-review | C_KM | КМ ceramic capacitor | 9 | C9, C10, C11, C12, C15, C16, C19, C34, C94 | modern ceramic capacitor with matching value/voltage/lead spacing |
| circuit-review | C_KM 0,047 | КМ ceramic capacitor 0,047 | 4 | C38, C42, C46, C50 | Factory placement/population is closed, but exact target capacitance, tolerance, and voltage remain unread; do not source the final part from the functional 0,047 model value. |
| circuit-review | C_KM 0,047 | КМ ceramic capacitor 0,047 | 0 | C51, C52, C53, C70, C71, C72 | Target placement, population, capacitance, tolerance, and voltage remain unresolved; do not fabricate or source this position from the retired fit-to-space coordinate or functional 0,047 model value. |
| circuit-review | C_KM 56 | КМ ceramic capacitor 56 | 0 | C29 | Exact source prints bare 56 without a unit; the native-sheet convention reads values below 1000 as pF, giving nominal 56 pF. Owner population and pads remain open. |
| circuit-review | C_KM 560 | КМ ceramic capacitor 560 | 1 | C5 | Exact source nominal 560 pF; no body is visible at the factory C5 site in May/July owner photos, and native photo reread separates the upper D34.2/R33-left and lower D34.6 joints. Identify C5 pads and population history before fitting. |
| circuit-review | C_TRIM | trimmer capacitor | 1 | C73 | modern trimmer capacitor matching footprint/value |
| circuit-review | Q_KT13 | КТ315 | 1 | VT2 | modern E-C-B transistor selected for the video role and KT-13 pad row |
| circuit-review | Q_KT27 | КТ972 | 1 | VT1 | modern E-C-B TO-126 transistor selected for the beeper role |
| circuit-review | R_AXIAL 12к | axial resistor 12к | 0 | R15, R16 | Source 12 kOhm and ground return; owner return rail and isolated body value require measurement. |
| circuit-review | R_AXIAL 1к | axial resistor 1к | 0 | R21, R22, R23, R24, R25, R26, R27, R28 | Eight owner bodies read 1K0; individual R-to-D8 output mapping and common bar rail need continuity. |
| circuit-review | R_AXIAL 20к | axial resistor 20к | 0 | R2 | PCB pad locations and target-body continuity are pending; exact .009 value and drawn branch are captured in the source model. |
| circuit-review | R_AXIAL 2к | axial resistor 2к | 0 | R7 | PCB pad locations and target-body continuity are pending; exact .009 value and drawn branch are captured in the source model. |
| circuit-review | R_AXIAL 330 | axial resistor 330 | 0 | R35 | Source 330 ohms and owner 330R body agree; calibrated owner pad geometry is pending. |
| circuit-review | R_AXIAL 360 | axial resistor 360 | 0 | R36, R37 | Exact .009 360-ohm phase pull-up; owner body begins 360, but pad nets and isolated value need measurement. |
| circuit-review | R_AXIAL 470 | axial resistor 470 | 1 | R104 | Exact .009 R104 470-ohm D12.5 open-collector pull-up; owner photos close both local D12 links and locate the footprint; installed resistance, known +5 V rail, and remote X2 continuity pending. |
| circuit-review | R_AXIAL 620 | axial resistor 620 | 1 | R33 | Exact source and two independent К62 owner marking reads agree on 620 ohms, but native photos separate the D34.2/R33-left upper joint from the D34.6 lower joint. Meter R33 and inspect the bare C5 site before fitting the pulse shaper. |
| circuit-review | R_AXIAL 910 | axial resistor 910 | 0 | R106 | Exact source prints 910 ohms; owner body in this position reads 510R on two dates. Measure before physical-value adoption. |
| circuit-review | UP2 | К170УП2 | 1 | D104 | RS-232/line-receiver substitute required; verify +/-12 V interface |
| mechanical-review | C_ELEC 47,0 | opposite-end-lead metal-can electrolytic (owner candidate) 47,0 | 1 | C1 | Owner C1 is an opposite-end-lead metal can with about 20 mm vertical joint span; upper lead photo-joins D13.7/GND, lower lead is marked +. Source PCB still uses a 2 mm radial footprint. Confirm hole coordinates and lower reset-net path, then select a matching footprint and part before sourcing. |
| mechanical-review | DISPLAY_CONN | bracket display connector X6; exact mechanical fit pending | 1 | X6 | select exact substitute after circuit review |
| mechanical-review | EXPANSION_CONN | СНП59-96 Р-20-2-В | 1 | X1 | select exact substitute after circuit review |
| mechanical-review | JUMPER2 | wire/link | 1 | E5 | select exact substitute after circuit review |
| mechanical-review | JUMPER3 | wire/link | 4 | E1, E2, E3, E4 | select exact substitute after circuit review |
| mechanical-review | JUMPER4 | wire/link | 2 | E13, E14 | select exact substitute after circuit review |
| mechanical-review | KBD_CONN | keyboard connector | 1 | X9 | select exact substitute after circuit review |
| mechanical-review | PAR_CONN | СНП59-30-23-В / parallel connector | 1 | X2 | select exact substitute after circuit review |
| mechanical-review | POWER_CONN | СНО51-30/56х9В-23 power connector | 1 | X8 | select exact substitute after circuit review |
| mechanical-review | SERIAL_CONN | РГ1Н-1-4 12-contact serial socket (cable mate РШ2Н-1-23/-24) | 1 | X3 | select exact substitute after circuit review |
| mechanical-review | SW | switch | 2 | S1, S4 | select exact substitute after circuit review |
| mechanical-review | SW_DIP6 | DIP switch | 1 | S3 | select exact substitute after circuit review |

## Minimum Acceptance Ladder

1. Inventory received parts against `docs/replica-dual-config-bom.csv` by type
   and refdes group, recording seller/lot, markings, quantity, and disposition
   in the parts-inventory and first-article records.
2. Keep static-sensitive parts in appropriate protective packaging and use a
   grounded ESD-controlled work area for incoming test, programming, handling,
   and installation.
3. Test DRAM and CPU-family spares before installation; quarantine counterfeit,
   intermittent, mismarked, or hot-running parts rather than silently moving
   them into the build stock.
4. Program or dump PROM/EPROM rows only after provenance is recorded; keep
   checksums, device settings, adapter identity, and confidence/verify results
   with the programmer log.
5. Install sockets first, then passives/connectors, then power-rail checks with
   no ICs seated. Independently review polarized parts, connectors, and pin-1
   orientation before power.
6. Close design-release risks before fabrication and assembly. Carry the
   released `docs/replica-bringup-verification-points.md` checks into each
   `docs/replica-first-article-record.md` and verify the assembled unit.
7. Seat only the clock/reset/ROM-fetch minimum set first; compare bus behavior
   against `sync/boot_check.sh` and cosim traces.
8. Add RAM, video, keyboard, and FDC in staged groups, never as one full-board
   power-on. Stop and record a discrepancy before changing a failed setup.

## Related Gates

- `docs/replica-dual-config-bom.md` / `.csv`: source-of-truth BOM split.
- `docs/replica-parts-inventory-template.md`: received-parts, acceptance-test, and PROM/EPROM programming evidence template.
- `docs/replica-first-article-record.md`: per-unit released configuration,
  instruments, physical acceptance, discrepancy, rework, and sign-off record.
- `docs/replica-candidate-parts-readiness.md`: guarded MK4564-12 and FD1793B-01 static compatibility plus remaining physical gates.
- `docs/replica-bringup-verification-points.md`: source-risk net checklist to carry into assembly and staged bring-up.
- `docs/prom-dump-procedure.md`: PROM/EPROM dump and programming provenance.
- `docs/community-prom-media-request.md`: owner/community request for PROMs and `JUKU-1` media.
- `docs/replica-fab-drc-disposition.md`: fabrication review posture before board order.
