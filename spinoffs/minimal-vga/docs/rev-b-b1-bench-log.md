# VJUGA rev B — five-card first-article bench log (R5.B1)

Status: **TEMPLATE READY / HARDWARE PENDING**. Start only after the five-board
R5.O1 order has arrived. Populate and power one first-article system in stages;
surplus bare boards do not authorize duplicate builds.

Record measured observations, not expected values. A failed row stops the ladder
until its cause and disposition are recorded. Power down before inserting or
removing any card or IC; the bus uses orientation markings, not foolproof mechanical
keying. Use the qualified Mean Well GST25A05-P1J through the MF-R300-fused,
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
or full ROM SHA-256 before inserting it. The three ROM rows may be three labelled
EPROMs or one erased/reprogrammed device, but only one is fitted at a time.

| Board / ref | Device and exact artifact | Expected identity | Marking / programmer / saved readback / result |
|---|---|---|---|
| Programming media / Memory U1 | 27C256 / `ekta37_z80-27c256.bin` / `EKTA3.7/VJUGA` | SHA-256 `e06dc0ee989d33049ad60c5a182df4d3da8814f206fd19c4f500603c772d9b2f` | pending |
| Programming media / Memory U1 | 27C256 / `netc10_vjuga-27c256.bin` / `NETC10/VJUGA` | SHA-256 `6e84664b4513c1c3f8f2f717bbee5ed15495225636f1b2f2fe8de8924a889f3f` | pending |
| Programming media / Memory U1 | 27C256 / `diag_vjuga-27c256.bin` / `DIAG/VJUGA` | SHA-256 `c220bf654711d8dda13e1e980763c11e00821b38bbdd55bd65c85a2b27f138a7` | pending |
| Memory U3 | ATF22V10C / `memory-u3.jed` | QF5892, C6806, SHA `dbbe74d99400718f2d743b7e02a33291dc1efac68805ea0dd75830b84d06d363` | pending |
| I/O U2 | ATF22V10C / `io-u2.jed` | QF5892, C7FAF, SHA `1874454ca6a44e79fec89f99e97495094c0cdac56ff1ff4b4be866a94f30008e` | pending |
| Video U5 | ATF22V10C / `video-hdec-u5.jed` | QF5892, C81ED, SHA `224e88c3c76a585ed1893665e7333883a6d0fbfebc9dd4bcef8b1d5d43045153` | pending |
| Video U6 | ATF22V10C / `video-vdec-u6.jed` | QF5892, C1DA2, SHA `4884fb645b412a51159560886341c17630aff165e492e08ed0008ed32305675f` | pending |
| Video U7 | ATF22V10C / `video-ctrl-u7.jed` | QF5892, C8809, SHA `0668bcd86c9e7bb59e3e4b99576794c14ac3a676086a89bffd20a260ca3a5d95` | pending |

The older `revb_bringup.bin` remains a regression fixture, not the R5
first-article diagnostic. Use `DIAG/VJUGA` for the measured POST/PIT ladder.

## Staged power and logic ladder

At every powered stage, start with a conservative current limit, record steady and
peak current plus +5 V at the backplane input and farthest active card, and inspect
for heat. Stop immediately for reversed polarity, current-limit operation, smoke,
odor, a hot device, less than 4.5 V at a 5 V logic rail, more than 5.25 V, or an
unexpected rail-to-ground resistance. Increase the current limit only after the
cause of the observed draw is understood.

| Stage | Configuration and required evidence | Current / rail / logic observations | Result / disposition |
|---|---|---|---|
| 1. Bare boards | Inspect five designs; verify outline/drill registration, orientation silk, the complete no-DNP first-system population contract, +5 V-to-GND resistance, and connector continuity | pending | pending |
| 2. Mechanical fit | Unpowered cards seat without force in marked orientation; record adjacent clearance; reserve slot 5 for Video and leave slot 4 empty when Video is fitted | pending | pending |
| 3. Backplane and supply | No cards: verify polarity, MF-R300 identity, fuse/reverse path, rails at all slots, and RESET_N assertion/release. Separately load the adapter at 1.655 A at its plug: require >=4.90 V average and <=80 mVpp before full-system use. | pending | pending |
| 4. CPU clock/reset | CPU card only with socketed 2.000 MHz oscillator; verify clock frequency/duty and reset at CPU and every slot | pending | pending |
| 5. NOP free-run | Power off; add the unpopulated Memory card with ROM/RAM/GAL absent and fit eight roughly 1 kΩ resistors from `J_NOP` pins 1–8 (`D0`–`D7`) to pin 9 (GND); verify plausible binary A0–A15 count plus M1/RD/RFSH/control activity | pending | pending |
| 6. Memory | Insert verified Memory card and ROM/GAL; verify ROM/RAM selects, no overlap, reset fetch, and stable reads before booting | pending | pending |
| 7. I/O direct recovery | Insert the complete I/O card and verified U2. Confirm `J_TTL` pinout/crossover and `TTL ONLY`; adapter VCC disconnected. Set `JP_CLK_SRC=DIRECT`; test bidirectional 19,200 8N1, then `JP_BAUD` 9,600 fallback. Confirm POST clears to `00` on reset and is read-silent. | pending | pending |
| 8. DIAG early POST | Fit `DIAG/VJUGA`, retain `DIRECT`, and cold boot. Observe ordered retained codes `10,20,21,30,31,40,41`; deliberately stop/reset where practical and prove the last code survives a halted CPU but clears on reset. No serial output is required before stage `61`. | pending | pending |
| 9. D57 normal clock/count | Power off and set `JP_CLK_SRC=PIT`. Scope U7 /4 / `CLK0` at 1.2288 MHz and `OUT0` / 8251 RxC+TxC at 307.2 kHz after DIAG programs mode 2/count 4. Record a latched count read consistent with a decrementing count of four; `50` must advance to `51`. | pending | pending |
| 10. D57 sound and late DIAG | Scope channel 1 input at 2.000 MHz and verify a controlled tone then silence at `J_SOUND`/BZ1. Continue through `60,61,70,71,80,81,FF`; record the exact 60-byte TTL diagnostic transcript. | pending | pending |
| 11. NETC10 without Video | Fit `NETC10/VJUGA` with `JP_CLK_SRC=PIT`; prove the real D57 count-four path, 8251 clock, POF release, initial `C7` target-ready indication and stable serial behavior. | pending | pending |
| 12. EKTA without Video | Fit `EKTA3.7/VJUGA`; record repeatable cold/reset behavior before adding Video. | pending | pending |
| 13. Video power-only | Power off; put Video in slot 5 with slot 4 empty; attach VGA before power; check card current, local rails, 25.175 MHz dot clock, sync, and abnormal heat. | pending | pending |
| 14. DIAG VGA/bus | Refit `DIAG/VJUGA`; confirm stage `80`/`81`, the 40-byte framebuffer pattern and final `FF`. Exercise framebuffer reads/writes, `WAIT_N` ownership and divide-six frame tick; capture contention or timing margin. | pending | pending |
| 15. EKTA VGA | Refit `EKTA3.7/VJUGA`; confirm stable 640x480 timing and visible output. Record monitor/mode, image evidence, RGB/sync observations and repeated cold/reset boots. | pending | pending |
| 16. Full NETC10 system | Refit `NETC10/VJUGA`; with VGA active, complete the exact bidirectional ABI 1.4 PROBE/DATA request/reply at PIT-derived 19,200 8N1. Record exact bytes/log, final POST state and the direct 9,600 recovery result separately. | pending | pending |

## D57 and POST measurement record

Complete this table from stages 7–10 and 14; a visual “seems alive” is not a pass.

| Checkpoint | Expected | Measured instrument / node / value | Result |
|---|---|---|---|
| POST after RESET_N | `00` | pending | pending |
| Ordered early POST | `10,20,21,30,31,40,41` | pending | pending |
| U7 /4 → PIT CLK0 | 1.2288 MHz | pending | pending |
| PIT OUT0 → RxC/TxC | 307.2 kHz, mode 2, count 4 | pending | pending |
| PIT count latch/read | valid decrementing four-count sequence | pending | pending |
| PIT CLK1 | 2.000 MHz | pending | pending |
| PIT OUT1 / sound | controlled tone followed by silence | pending | pending |
| USART stages and transcript | `60,61`; exact 60 bytes | pending | pending |
| PPI/PIC stages | `70,71` | pending | pending |
| VGA/frame stages | `80,81`; 40-byte pattern | pending | pending |
| Final ready | `FF`, retained | pending | pending |

## First-article release decision

| Decision | Recorded value |
|---|---|
| All 16 stages pass | pending |
| EKTA boots repeatably on VGA | pending |
| Bidirectional NETC10 passes with Video installed | pending |
| Worst total current / lowest measured +5 V | pending |
| Discrepancies and dispositions | pending |
| Duplicate population released | **no — pending first-article pass** |
| R5.B1 result | pending |
| Owner / reviewer / ISO timestamp | pending |

R5.B1 is complete only when all stages and every D57/POST row contain measured
evidence, every discrepancy has a disposition, EKTA is visible on VGA, and the
bidirectional NETC10 transaction passes with the complete five-card system.
