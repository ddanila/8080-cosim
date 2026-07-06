# Replica sourcing readiness

Status: **SOURCING READY / PROGRAMMING BLOCKED**

Source: `docs/replica-dual-config-bom.csv`.

This report turns the WS-E dual-config BOM into an ordering and acceptance
gate. It is not a vendor cart: prices, live stock, and seller trust must be
checked at order time. It defines what can be sourced early, what needs
bench acceptance, and what must wait for PROM/media truth or mechanical
review before being treated as build-ready.

## Summary

- BOM lines: 68
- Populate-now component positions: 196
- Long-lead/source-early lines: 21
- Programming/dump-gated lines: 4
- Mechanical/circuit-review lines: 22
- Order posture: do not treat as a complete kit until the gated rows below are closed

## Action Totals

| Action | BOM lines | Populate-now positions |
| --- | ---: | ---: |
| circuit-review | 10 | 68 |
| mechanical-review | 12 | 17 |
| program/dump | 4 | 6 |
| source-now | 41 | 97 |
| source-populated-now | 1 | 8 |

## Buy Early / Acceptance-Test First

| Type | Authentic part | Functional substitute | Populate now | Refs | Acceptance note |
| --- | --- | --- | ---: | --- | --- |
| BUF8286 | КР580ВА86 | Intel 8286 / compatible bus transceiver | 2 | D4, D107 | Continuity/orientation check; verify no bus fight during first ROM fetch. |
| BUF8287 | КР580ВА87 | Intel 8287 / compatible bus transceiver | 1 | D100 | Continuity/orientation check; verify direction/OE before attaching FDC data path. |
| CPU8080 | КР580ИК80А | Intel 8080A / compatible 8080 CPU | 1 | D1 | Run in a known-good 8080 tester or minimal NOP/ROM-fetch jig before seating. |
| IR82 | КР580ИР82 | 8282/8283-class latch; verify polarity/package | 1 | D58 | Verify latch polarity around DRAM write-data path. |
| PIC8259 | КР580ВН59 | 8259A PIC | 1 | D10 | Socket; verify frame interrupt vectoring before FDC IRQs. |
| PIT8253 | КР580ВИ53 | 8253 or 8254 PIT | 3 | D54, D55, D57 | Socket; verify programmed divisors and video-sync outputs. |
| PPI8255 | КР580ВВ55А | 8255A / 82C55 PPI | 2 | D26, D27 | Socket; verify keyboard/Port C mode bits against twin during bring-up. |
| SYS8238 | КР580ВК38 | 8228/8238-class system controller; verify pinout | 1 | D5 | Verify pin-compatible 8228/8238 behavior; check MEMR/IO strobes in a socketed bring-up. |
| USART8251 | КР580ВВ51А | 8251A / 82C51-class USART | 1 | D11 | Socket; loopback test after clock/reset are proven. |
| VABUS | КР580ВА87 | Intel 8287 / compatible bus transceiver | 4 | D23, D24, D25, D29 | Continuity/orientation check on expansion bus transceivers. |
| VG93_FDC | КР1818ВГ93 | WD1793-compatible FDC | 1 | D93 | Prefer socket; WD1793 drop-in acceptable for functional config. |
| XTAL | РК-171 16 MHz crystal 16 МГц | 16 MHz HC-49/metal-can crystal matching footprint/load | 1 | Z1 | Verify 16 MHz oscillation and load-cap fit before debugging timing. |
| RU5 | К565РУ5Г / 565РУ5Г | 4164-compatible 64Kx1 DRAM | 8 | D60, D61, D62, D63, D64, D65, D66, D67 | Buy spares; run 4164/565RU5 tester before installation. |

## Programming / Dump Gate

These rows are required for a complete functional kit, but their contents
must come from the Baltijets programming disk, an owner dump, or the
boot-validated reconstructed tables in that preference order.

| Type | Authentic part | Populate now | Refs | Gate |
| --- | --- | ---: | --- | --- |
| DEC_PROM | КР556РТ4А | 2 | D2, D6 | Need D2/D6 RT4 maps or accepted reconstructed decode tables before programming. |
| EPROM8K | 2764/M2764-class EPROM in .009 build; К573РФ5 on .006 BOM | 2 | D15, D16 | Program D15/D16 for the .009 build; leave D17-D22 empty unless authentic-completeness build is chosen. |
| RE3_PROM | К155РЕ3 | 1 | D8 | Need D8 RE3 dump/table or accepted reconstructed table. |
| RE3_PROM_113 | К155РЕ3 | 1 | D94 | Need D94/FDC-era RE3 dump/table or accepted reconstructed table. |

## Review Before Buying Blind

These rows should not be converted directly into a vendor cart. They need
exact mechanical fit, interface-voltage, circuit-role, or value confirmation
against drawings/board photos before ordering final quantities.

| Action | Type | Authentic part | Populate now | Refs | Note |
| --- | --- | --- | ---: | --- | --- |
| circuit-review | AP2 | К170АП2 | 2 | D14, D32 | RS-232/line-driver substitute required; verify +/-12 V interface |
| circuit-review | C_ELEC | radial electrolytic | 3 | C31, C32, C33 | modern radial electrolytic with matching value/voltage/polarity |
| circuit-review | C_KM | КМ ceramic capacitor | 10 | C7, C8, C9, C10, C11, C13, C14, C15, C34, C99 | modern ceramic capacitor with matching value/voltage/lead spacing |
| circuit-review | C_TRIM | trimmer capacitor | 1 | C12 | modern trimmer capacitor matching footprint/value |
| circuit-review | D_DIODE | Soviet diode/zener per value | 2 | VD3, VD4 | modern diode/zener matching value and power |
| circuit-review | L_RADIAL | radial inductor/choke | 1 | L1 | modern radial choke/inductor after value confirmation |
| circuit-review | Q_TO92 | КТ315/КТ972-class transistor per position | 4 | VT1, VT2, VT3, VT4 | modern transistor selected per exact circuit role |
| circuit-review | R_AXIAL | axial resistor | 43 | R11, R12, R13, R14, R17, R40, R41, R42, R43, R44, R45, R47, R48, R49, R50, R51, R52, R53, ... (+25) | modern axial resistor, matching value and power rating |
| circuit-review | R_TRIM | СП3-22б trimmer | 1 | R73 | modern vertical trimmer matching footprint/value |
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
5. Seat only the clock/reset/ROM-fetch minimum set first; compare bus behavior against `sync/boot_check.sh` and cosim traces.
6. Add RAM, video, keyboard, and FDC in staged groups, never as one full-board power-on.

## Related Gates

- `docs/replica-dual-config-bom.md` / `.csv`: source-of-truth BOM split.
- `docs/replica-parts-inventory-template.md`: received-parts, acceptance-test, and PROM/EPROM programming evidence template.
- `docs/prom-dump-procedure.md`: PROM/EPROM dump and programming provenance.
- `docs/community-prom-media-request.md`: owner/community request for PROMs and `JUKU-1` media.
- `docs/replica-fab-drc-disposition.md`: fabrication review posture before board order.
