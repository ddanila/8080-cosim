# Juku machine deployment status

Status date: 2026-08-21

This is the current location/configuration ledger reported after the successful
Arvutimuuseum demonstration. It records deployment state, not a new electrical
diagnosis; detailed bench evidence remains in each machine's service notes.

| Machine | Current location | Firmware / operating state | Open work |
| --- | --- | --- | --- |
| `CS00014` | Arvutimuuseum main exhibition | Stock ROM fitted. Previously passed the CP/Mish `NETROM2` network A:/native game B: demonstration; that test image was network-loaded and did not replace the fitted ROM. | Preserve the exhibition configuration; repeat bench work only when the machine is available. |
| `CS00015` | Home lab | JukuNet C8 / ABI 1.3 D15/D16 pair fitted, exact ROM SHA-256 `a54cb877edfe25e939e05ada0e98783acb53cfc8969071c63928b119c8e09e46`. Repeated automatic V16 boot, A:/B: NetDisk, diagnostics, local/N4 input, ROM sound, snapshot write, warm boot, soak, and live host replacement passed blind qualification. A native arm64 macOS host cold-booted this pair with S21 `07h`, then passed `STATUS`, `DIAG ALL`, `N4BULK`, and `SOAK`. | Retain C6 as the immutable rollback image. Physical display/glyph/cursor observation and safely induced C1--C5 POST tones remain pending. |
| `CS00000` | Home lab | Current firmware and broader boot state were not restated in this update. USART operation is suspected faulty. | Diagnose the serial path before declaring D11 bad: establish local 8251 status/clock behavior, then connector/level-shifter loopback and end-to-end traffic. Treat the USART fault as provisional until isolated. |
| `CS00024` | Not recorded; last handled on the diagnostic bench | T36 `1E/C617` was last reported fitted. Its corrected software refresh completed the full 32 KiB RAM proof; this does not validate the normal raster-refresh path. | Rerun corrected D57 channel 2 with raster armed, then the prepared `none`/`raster`/`raster-syncb` retention matrix. Keep the separate 12 ms parser margin investigation distinct. |

The board identifiers are inventory identities. Do not infer that `CS00000` is
the generic or factory-reference machine from its number, and do not transfer a
fault or repair conclusion between boards without a repeated test.

The authoritative machine-readable forms are in [`machines/`](machines/).
They preserve unknown values as `null` and bind every operational statement to
repository evidence.
