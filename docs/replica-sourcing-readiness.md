# Replica sourcing readiness

Status: **PARTIAL / PROGRAMMING AND REVIEW BLOCKED**

Source: `docs/replica-dual-config-bom.csv`.

This report turns the dual-config BOM into an ordering and acceptance
gate. It is not a vendor cart: prices, live stock, and seller trust must be
checked at order time. It defines what can be sourced early, what needs
bench acceptance, and what must wait for PROM/media truth or mechanical
review before being treated as build-ready.

## Summary

- BOM lines: 113
- Populate-now component positions: 269
- Long-lead/source-early lines: 22
- Programming/dump-gated lines: 5
- Mechanical/circuit-review lines: 22
- Order posture: do not treat as a complete kit until the gated rows below are closed

## Action Totals

| Action | BOM lines | Populate-now positions |
| --- | ---: | ---: |
| circuit-review | 10 | 23 |
| leave-empty | 3 | 0 |
| mechanical-review | 12 | 17 |
| program/dump | 5 | 6 |
| source-now | 83 | 223 |

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
| RU5 | К565РУ5Г | 4164-family 64Kx1 DRAM candidate; verify pinout, refresh, speed, and rails | 8 | D84, D85, D86, D87, D88, D89, D90, D91 | Verify exact 4164/565RU5 pinout, refresh, speed, and rails; buy tested spares only after approval. |
| SYS8238 | КР580ВК38 | 8228/8238-class system controller; verify pinout | 1 | D5 | Verify pin-compatible 8228/8238 behavior; check MEMR/IO strobes in a socketed bring-up. |
| USART8251 | КР580ВВ51А | 8251A / 82C51-class USART | 1 | D11 | Socket; loopback test after clock/reset are proven. |
| VABUS | КР580ВА87 | Intel 8287 / compatible bus transceiver | 3 | D23, D24, D25 | Continuity/orientation check on expansion bus transceivers. |
| VG93_FDC | КР1818ВГ93 | WD1793 pin-compatible candidate; verify clock, rails, and interface timing | 1 | D93 | Prefer a socket; verify the exact WD1793/VG93 candidate's pinout, clock, rails, and timing before approval. |
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
| WAIT_PROM | КР556РТ4А | 1 | D2 | Program from the preservation-grade physical D2 `.037` table recovered by three matching reads, including a power-cycled capture. |

## Review Before Buying Blind

These rows should not be converted directly into a vendor cart. They need
exact mechanical fit, interface-voltage, circuit-role, or value confirmation
against drawings/board photos before ordering final quantities.

| Action | Type | Authentic part | Populate now | Refs | Note |
| --- | --- | --- | ---: | --- | --- |
| circuit-review | AP2 | К170АП2 | 2 | D14, D32 | RS-232/line-driver substitute required; verify +/-12 V interface |
| circuit-review | C_ELEC | radial electrolytic | 3 | C31, C32, C33 | modern radial electrolytic with matching value/voltage/polarity |
| circuit-review | C_KM | КМ ceramic capacitor | 9 | C9, C10, C11, C12, C15, C16, C19, C34, C94 | modern ceramic capacitor with matching value/voltage/lead spacing |
| circuit-review | C_KM 0,047 | КМ ceramic capacitor 0,047 | 4 | C38, C42, C46, C50 | Factory placement/population is closed, but exact target capacitance, tolerance, and voltage remain unread; do not source the final part from the functional 0,047 model value. |
| circuit-review | C_KM 0,047 | КМ ceramic capacitor 0,047 | 0 | C51, C52, C53, C70, C71, C72 | Target placement, population, capacitance, tolerance, and voltage remain unresolved; do not fabricate or source this position from the retired fit-to-space coordinate or functional 0,047 model value. |
| circuit-review | C_KM 1,5 нФ | КМ ceramic capacitor 1,5 нФ | 2 | C20, C22 | Capacitance is source-closed, but tolerance and voltage rating remain unread; do not source the final part from value alone. |
| circuit-review | Q_KT13 | КТ315 | 1 | VT2 | modern E-C-B transistor selected for the video role and KT-13 pad row |
| circuit-review | Q_KT27 | КТ972 | 1 | VT1 | modern E-C-B TO-126 transistor selected for the beeper role |
| circuit-review | R_AXIAL 2к | axial resistor 2к | 0 | R8 | The measured value and D94.1/+5 V endpoints are closed, but R8's physical placement is not registered; do not fabricate or source its final body/lead spacing until that placement is recovered. |
| circuit-review | UP2 | К170УП2 | 1 | D104 | RS-232/line-receiver substitute required; verify +/-12 V interface |
| mechanical-review | EXPANSION_CONN | СНП59-96 Р-20-2-В | 1 | X1 | select exact substitute after circuit review |
| mechanical-review | JUMPER2 | wire/link | 1 | E5 | select exact substitute after circuit review |
| mechanical-review | JUMPER3 | wire/link | 4 | E1, E2, E3, E4 | select exact substitute after circuit review |
| mechanical-review | JUMPER4 | wire/link | 2 | E13, E14 | select exact substitute after circuit review |
| mechanical-review | KBD_CONN | keyboard connector | 1 | X9 | select exact substitute after circuit review |
| mechanical-review | PAR_CONN | parallel/interface connector | 1 | X2 | select exact substitute after circuit review |
| mechanical-review | POWER_CONN | СНО51-30/56х9В-23 power connector | 1 | X8 | select exact substitute after circuit review |
| mechanical-review | RF_CONN | RF connector | 1 | X6 | select exact substitute after circuit review |
| mechanical-review | SERIAL_CONN | СНП59-30-23-В / serial connector | 1 | X3 | select exact substitute after circuit review |
| mechanical-review | SW | switch | 2 | S1, S4 | select exact substitute after circuit review |
| mechanical-review | SW_DIP6 | DIP switch | 1 | S3 | select exact substitute after circuit review |
| mechanical-review | VIDEO_CONN | BNC/composite video connector | 1 | X7 | select exact substitute after circuit review |

## Minimum Acceptance Ladder

1. Inventory received parts against `docs/replica-dual-config-bom.csv` by type and refdes group.
2. Test DRAM and CPU-family spares before installation; reject intermittent or hot-running parts.
3. Program or dump PROM/EPROM rows only after provenance is recorded; keep checksums with the programmer log.
4. Install sockets first, then passives/connectors, then power-rail checks with no ICs seated.
5. Carry `docs/replica-bringup-verification-points.md` into the private build record and close its source-risk nets as they are reached.
6. Seat only the clock/reset/ROM-fetch minimum set first; compare bus behavior against `sync/boot_check.sh` and cosim traces.
7. Add RAM, video, keyboard, and FDC in staged groups, never as one full-board power-on.

## Related Gates

- `docs/replica-dual-config-bom.md` / `.csv`: source-of-truth BOM split.
- `docs/replica-parts-inventory-template.md`: received-parts, acceptance-test, and PROM/EPROM programming evidence template.
- `docs/replica-bringup-verification-points.md`: source-risk net checklist to carry into assembly and staged bring-up.
- `docs/prom-dump-procedure.md`: PROM/EPROM dump and programming provenance.
- `docs/community-prom-media-request.md`: owner/community request for PROMs and `JUKU-1` media.
- `docs/replica-fab-drc-disposition.md`: fabrication review posture before board order.
