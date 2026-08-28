# VJUGA rev B — five-card first-article bench log (R5.B1)

Status: **TEMPLATE READY / HARDWARE PENDING**. Start only after the five-board
R5.O1 order has arrived. Populate and power one first-article system in stages;
surplus bare boards do not authorize duplicate builds.

Record measured observations, not expected values. A failed row stops the ladder
until its cause and disposition are recorded. Power down before inserting or
removing any card or IC; the bus uses orientation markings, not foolproof mechanical
keying. Use the qualified regulated 5 V supply rated at least 2 A through the fused,
reverse-protected center-positive `J_PWR`. The USB-TTL adapter is data-only and must
not power the machine.

## Receipt and build identity

| Field | Recorded value |
|---|---|
| JLCPCB order ID / received date | pending |
| Order-record reference | `rev-b-five-board-order-record.md` — pending completion |
| Board lot markings: CPU / Memory / I/O / Backplane / Video | pending |
| Quantity and visible shipping damage per design | pending |
| Bare-board dimensions, thickness, finish, registration | pending |
| Continuity/open checks and discrepancy references | pending |
| Bench supply / current limit / DMM / scope or analyzer | pending |
| Builder / independent checker / date | pending |

Before assembly, compare all five boards to their accepted production-file previews,
inspect both sides under magnification, and meter +5 V to ground on every bare board.
Socket all programmed devices. Fit only the parts required by the active stage.

## Programmed-device identity and independent readback

Rebuild with `pld/revb/build_revb_gals.sh` and `roms/build_revb_rom.py --check`.
Program out of circuit with security/fuse lock disabled. After programmer verify,
power-cycle the programmer, read each part again, and compare its fuse count/checksum
or full ROM SHA-256 before inserting it.

| Board / ref | Device and exact artifact | Expected identity | Marking / programmer / saved readback / result |
|---|---|---|---|
| Memory U1 | 27C256 / `ekta37_z80-27c256.bin` | SHA-256 `e06dc0ee989d33049ad60c5a182df4d3da8814f206fd19c4f500603c772d9b2f` | pending |
| Memory U3 | ATF22V10C / `memory-u3.jed` | QF5892, C6806, SHA `dbbe74d99400718f2d743b7e02a33291dc1efac68805ea0dd75830b84d06d363` | pending |
| I/O U2 | ATF16V8B / `io-u2.jed` | QF2194, C3676, SHA `703412427efff890ebfc0e7d430b4a7cf016f3abdc9ad2f90bc3d9aac980e6e7` | pending |
| Video U5 | ATF22V10C / `video-hdec-u5.jed` | QF5892, C81ED, SHA `224e88c3c76a585ed1893665e7333883a6d0fbfebc9dd4bcef8b1d5d43045153` | pending |
| Video U6 | ATF22V10C / `video-vdec-u6.jed` | QF5892, C1DA2, SHA `4884fb645b412a51159560886341c17630aff165e492e08ed0008ed32305675f` | pending |
| Video U7 | ATF22V10C / `video-ctrl-u7.jed` | QF5892, C8809, SHA `0668bcd86c9e7bb59e3e4b99576794c14ac3a676086a89bffd20a260ca3a5d95` | pending |

The minimum diagnostic alternative is `revb_bringup.bin`, SHA-256
`edfdabda362cefd6716acd2fe70b8befa500cb5983afe097ccd2d4a0e8447892`.
If it is used instead of EKTA, record the separate programmed ROM/readback here:
pending.

## Staged power and logic ladder

At every powered stage, start with a conservative current limit, record steady and
peak current plus +5 V at the backplane input and farthest active card, and inspect
for heat. Stop immediately for reversed polarity, current-limit operation, smoke,
odor, a hot device, less than 4.5 V at a 5 V logic rail, more than 5.25 V, or an
unexpected rail-to-ground resistance. Increase the current limit only after the
cause of the observed draw is understood.

| Stage | Configuration and required evidence | Current / rail / logic observations | Result / disposition |
|---|---|---|---|
| 1. Bare boards | Inspect five designs; verify outline/drill registration, orientation silk, intended DNPs, +5 V-to-GND resistance, and connector continuity | pending | pending |
| 2. Mechanical fit | Unpowered cards seat without force in marked orientation; record adjacent clearance; reserve slot 5 for Video and leave slot 4 empty when Video is fitted | pending | pending |
| 3. Bare backplane | No cards; current-limited `J_PWR`; verify polarity, fuse/reverse path, +5 V/GND at all five slots, and RESET_N assertion/release | pending | pending |
| 4. CPU clock/reset | CPU card only with socketed 2.000 MHz oscillator; verify clock frequency/duty and reset at CPU and every slot | pending | pending |
| 5. NOP free-run | Power off; add the unpopulated Memory card with ROM/RAM/GAL absent and fit eight roughly 1 kΩ resistors from `J_NOP` pins 1–8 (`D0`–`D7`) to pin 9 (GND); verify plausible binary A0–A15 count plus M1/RD/RFSH/control activity | pending | pending |
| 6. Memory | Insert verified Memory card and ROM/GAL; verify ROM/RAM selects, no overlap, reset fetch, and stable reads before booting | pending | pending |
| 7. I/O and TTL serial | Insert minimum I/O population and verified GAL; confirm header pinout/crossover and `TTL ONLY`; adapter VCC disconnected; test TX/RX at 19,200 8N1, then 9,600 fallback | pending | pending |
| 8. Diagnostic boot | If used, `revb_bringup.bin` emits exactly `VJUGA rev B bring-up`, `RAM PASS`, `ROM OK`, `READY` (47 bytes) over the real 8251 | pending | pending |
| 9. EKTA without Video | Boot the released EKTA ROM; record repeatable cold/reset behavior and serial evidence before adding Video | pending | pending |
| 10. Video power-only | Power off; put Video in slot 5 with slot 4 empty; attach VGA before power; check card current, local rails, 25.175 MHz dot clock, sync, and abnormal heat | pending | pending |
| 11. VGA function | Confirm stable 640x480 timing and visible EKTA output on the monitor; record monitor/mode, image evidence, RGB/sync observations, and cold/reset repeats | pending | pending |
| 12. Bus interaction | Exercise framebuffer writes/reads, `WAIT_N` ownership, and divide-six frame tick; capture any contention or timing margins | pending | pending |
| 13. Full-system serial | With VGA active, complete bidirectional ABI 1.4 C10 PROBE/DATA request/reply at 19,200 8N1; record exact bytes/log and 9,600 fallback result | pending | pending |

## First-article release decision

| Decision | Recorded value |
|---|---|
| All 13 stages pass | pending |
| EKTA boots repeatably on VGA | pending |
| Bidirectional C10 passes with Video installed | pending |
| Worst total current / lowest measured +5 V | pending |
| Discrepancies and dispositions | pending |
| Duplicate population released | **no — pending first-article pass** |
| R5.B1 result | pending |
| Owner / reviewer / ISO timestamp | pending |

R5.B1 is complete only when all stages contain measured evidence, every discrepancy
has a disposition, EKTA is visible on VGA, and the bidirectional C10 transaction
passes with the complete five-card system.
