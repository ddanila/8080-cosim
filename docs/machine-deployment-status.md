# Juku machine deployment status

Status date: 2026-08-18

This is the current location/configuration ledger reported after the successful
Arvutimuuseum demonstration. It records deployment state, not a new electrical
diagnosis; detailed bench evidence remains in each machine's service notes.

| Machine | Current location | Firmware / operating state | Open work |
| --- | --- | --- | --- |
| `CS00014` | Arvutimuuseum main exhibition | Stock ROM fitted. Previously passed the CP/Mish `NETROM2` network A:/native game B: demonstration; that test image was network-loaded and did not replace the fitted ROM. | Preserve the exhibition configuration; repeat bench work only when the machine is available. |
| `CS00015` | Home lab | JukuNet C5 D15/D16 pair fitted, exact ROM SHA-256 `9ed6273f44c1b09dcb5fcd3ca94e5a1aad813b285607558a7d8cb98b1a5e6e7a`. Automatic CP/M Plus boot, A:/B: NetDisk, diagnostics, local keyboard, snapshot write, warm boot, and live host reconnect passed blind qualification. | Use as the C5 physical reference. A working monitor is still needed only for exact resident display/cursor observation; C6 remains simulator-only until separately promoted. |
| `CS00000` | Home lab | Current firmware and broader boot state were not restated in this update. USART operation is suspected faulty. | Diagnose the serial path before declaring D11 bad: establish local 8251 status/clock behavior, then connector/level-shifter loopback and end-to-end traffic. Treat the USART fault as provisional until isolated. |
| `CS00024` | Not recorded; last handled on the diagnostic bench | T36 `1E/C617` was last reported fitted. Its corrected software refresh completed the full 32 KiB RAM proof; this does not validate the normal raster-refresh path. | Rerun corrected D57 channel 2 with raster armed, then the prepared `none`/`raster`/`raster-syncb` retention matrix. Keep the separate 12 ms parser margin investigation distinct. |

The board identifiers are inventory identities. Do not infer that `CS00000` is
the generic or factory-reference machine from its number, and do not transfer a
fault or repair conclusion between boards without a repeated test.

The authoritative machine-readable forms are in [`machines/`](machines/).
They preserve unknown values as `null` and bind every operational statement to
repository evidence.
