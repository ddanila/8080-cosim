# Juku machine deployment status

Status date: 2026-08-18

This is the current location/configuration ledger reported after the successful
Arvutimuuseum demonstration. It records deployment state, not a new electrical
diagnosis; detailed bench evidence remains in each machine's service notes.

| Machine | Current location | Firmware / operating state | Open work |
| --- | --- | --- | --- |
| `CS00014` | Arvutimuuseum main exhibition | Stock ROM fitted. Previously passed the CP/Mish `NETROM2` network A:/native game B: demonstration; that test image was network-loaded and did not replace the fitted ROM. | Preserve the exhibition configuration; repeat bench work only when the machine is available. |
| `CS00015` | Home lab | JukuNet C6 / ABI 1.2 D15/D16 pair fitted, exact ROM SHA-256 `0487d5150f9b662a193b3f031aadd90002ee232477d355d3877a757a247c2f09`. Repeated automatic V16 boot, A:/B: NetDisk, diagnostics, local keyboard, ROM sound, snapshot write, warm boot, soak, and two live host replacements passed blind qualification. | Use as the C6 physical reference. A working monitor is still needed only for exact resident geometry/glyph/pseudographic/cursor observation. |
| `CS00000` | Home lab | Current firmware and broader boot state were not restated in this update. USART operation is suspected faulty. | Diagnose the serial path before declaring D11 bad: establish local 8251 status/clock behavior, then connector/level-shifter loopback and end-to-end traffic. Treat the USART fault as provisional until isolated. |
| `CS00024` | Not recorded; last handled on the diagnostic bench | T36 `1E/C617` was last reported fitted. Its corrected software refresh completed the full 32 KiB RAM proof; this does not validate the normal raster-refresh path. | Rerun corrected D57 channel 2 with raster armed, then the prepared `none`/`raster`/`raster-syncb` retention matrix. Keep the separate 12 ms parser margin investigation distinct. |

The board identifiers are inventory identities. Do not infer that `CS00000` is
the generic or factory-reference machine from its number, and do not transfer a
fault or repair conclusion between boards without a repeated test.

The authoritative machine-readable forms are in [`machines/`](machines/).
They preserve unknown values as `null` and bind every operational statement to
repository evidence.
