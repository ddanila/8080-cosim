# Replica parts and PROM inventory template

Copy this checklist into the private build record when parts are ordered,
received, tested, and programmed. Do not mark M8 complete until the received
inventory, bench tests, and PROM/EPROM programming records below are filled
with real evidence.

Source gates:

- `docs/replica-dual-config-bom.csv`
- `docs/replica-sourcing-readiness.md`
- `docs/replica-bringup-verification-points.md`
- `docs/prom-dump-procedure.md`
- `docs/community-prom-media-request.md`

## Kit Summary

| Field | Recorded value |
| --- | --- |
| Build target | functional .009 replica |
| Inventory date |  |
| Recorder |  |
| Parts storage location |  |
| Anti-static / handling notes |  |
| Board batch/order reference |  |
| Bring-up verification checklist revision |  |

## Required Functional Groups

| Group | Required evidence | Status |
| --- | --- | --- |
| CPU and system controller | received CPU8080 + SYS8238-class parts, socket fit checked, pre-install test or known-good provenance |  |
| Bus transceivers/latches | received BUF8286/BUF8287/VABUS/IR82 parts, orientation and pinout checked |  |
| DRAM bank | at least 8 tested 4164/К565РУ5-compatible chips plus spares |  |
| PIT/PPI/PIC/USART/FDC | received socketed peripheral ICs, FDC drop-in decision recorded |  |
| Clock/video glue | received fast counters, muxes, gates, oscillator/crystal, and serializer-related ICs |  |
| Passives | received resistor/capacitor/diode/transistor values with circuit-review rows resolved |  |
| Connectors/switches | exact mechanical fit reviewed for X1/X2/X3/X7/X8/X9/S1/S3/S4 |  |
| Sockets | DIP socket quantities and widths checked against footprints before IC seating |  |
| PROM/EPROM blanks | received D2/D6 RT4-class, D8/D94 RE3-class, and D15/D16 EPROM blanks |  |
| Programmed firmware | D15/D16 EPROMs and D2/D6/D8/D94 PROMs programmed or dumped/reconstructed with checksums |  |

## Received Parts Ledger

| Ref/group | Part received | Qty received | Seller/source | Lot/date code | Test method | Result | Notes |
| --- | --- | ---: | --- | --- | --- | --- | --- |
| D1 |  |  |  |  |  |  |  |
| D5 |  |  |  |  |  |  |  |
| D60-D67 |  |  |  |  |  |  |  |
| D93 |  |  |  |  |  |  |  |
| X1/X2/X3/X7/X8/X9 |  |  |  |  | fit check |  |  |
| sockets |  |  |  |  | footprint check |  |  |

## PROM / EPROM Programming Ledger

| Ref | Device class | Source of contents | Input file SHA256 | Program/readback SHA256 | Programmer/method | Result |
| --- | --- | --- | --- | --- | --- | --- |
| D2 | RT4 / 256x4 |  |  |  |  |  |
| D6 | RT4 / 256x4 |  |  |  |  |  |
| D8 | RE3 / 32x8 |  |  |  |  |  |
| D94 | RE3 / 32x8 |  |  |  |  |  |
| D15 | 2764 EPROM |  |  |  |  |  |
| D16 | 2764 EPROM |  |  |  |  |  |

## Acceptance Before Seating ICs

- [ ] Received parts are inventoried against `docs/replica-dual-config-bom.csv`.
- [ ] DRAM parts pass a 4164/К565РУ5-compatible tester, including at least one warm repeat.
- [ ] CPU/system-controller parts pass a known-good tester or minimal fetch jig.
- [ ] FDC choice is recorded as КР1818ВГ93 or WD1793-compatible.
- [ ] Mechanical connector rows are fit-checked against the fabricated board before soldering.
- [ ] PROM/EPROM contents have provenance and readback checksums.
- [ ] `docs/replica-bringup-verification-points.md` has been copied into the build record with owner/measured dispositions for source-risk nets touched by early bring-up.
- [ ] Sockets and passives are installed before any IC is seated.
- [ ] Power rails are checked with no ICs seated.

## Files To Preserve With The Build Record

- Seller invoices or order confirmations.
- Photos of received lots and date codes.
- Tester logs for CPU, DRAM, FDC, and suspicious NOS parts.
- PROM programmer logs and readback binaries/checksums.
- Filled bring-up verification-point checklist with continuity/scope/logic-analyzer evidence.
- Photos of connector/socket fit checks before soldering.
