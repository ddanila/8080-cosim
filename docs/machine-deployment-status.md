# Juku machine deployment status

Status date: 2026-08-22

This is the current location/configuration ledger reported after the successful
Arvutimuuseum demonstration. It records deployment state, not a new electrical
diagnosis; detailed bench evidence remains in each machine's service notes.

| Machine | Current location | Firmware / operating state | Open work |
| --- | --- | --- | --- |
| `CS00014` | Arvutimuuseum main exhibition | Stock ROM fitted. Previously passed the CP/Mish `NETROM2` network A:/native game B: demonstration; that test image was network-loaded and did not replace the fitted ROM. | Preserve the exhibition configuration; repeat bench work only when the machine is available. |
| `CS00015` | Home lab | JukuNet C8 / ABI 1.3 D15/D16 pair fitted, exact ROM SHA-256 `a54cb877edfe25e939e05ada0e98783acb53cfc8969071c63928b119c8e09e46`. Repeated automatic V16 boot, A:/B: NetDisk, diagnostics, local/N4 input, ROM sound, snapshot write, warm boot, soak, and live host replacement passed blind qualification. A native arm64 macOS host cold-booted this pair with S21 `07h`, then passed `STATUS`, `DIAG ALL`, `N4BULK`, and `SOAK`. A 2026-08-21 two-machine control subsequently proved stable sync and CPU-visible framebuffer RAM but no pixel output in 40x24, 53x24, or 80x24; the identical corrected raw pattern was visible on CS00014. | Diagnose the board-local video-data path after framebuffer storage. Retain C6 as the immutable rollback image; safely induced C1--C5 POST tones remain pending. |
| `CS00000` | Home lab | EktaSoft 3.7 / Serial `#0037` is currently fitted and remained 100% stable across the owner's repeated cold starts after the original PSU failure and subsequent no-display starts with the removed stock `#0031` pair. Earlier, `#0031` RomBios 3.43 / Janet 1.2 passed stock Janet, CPU/RAM/PIT/D11 diagnostics, 19,200-baud V15 reception, CP/M Plus, and sustained NetDisk-v3. With EK37 fitted, portable C host `0.3.0-m6` subsequently completed the one-command stock-assisted V15 path, reached `A>`, and served 22 clean NetDisk requests with zero retries/UART errors. A later truncated Janet frame exposed a host-only resynchronization defect; `0.3.1-m6` fixes it and the exact physical pattern is now a regression. | Preserve and repeatedly dump the removed `#0031` pair, inspect its sockets, and perform a controlled comparison before diagnosing ROM failure; that comparison can also repeat the C-host path on the exact pair. Repair/verify the original PSU separately. |
| `CS00024` | Not recorded; last handled on the diagnostic bench | T36 `1E/C617` was last reported fitted. Its corrected software refresh completed the full 32 KiB RAM proof; this does not validate the normal raster-refresh path. It is also an owner-observed construction variant: speaker fixed to the PSU, keyboard PCB lacking the comparison machines' central reverse-side designation, and a PSU-socket bracket mechanically incompatible with CS00000. | Rerun corrected D57 channel 2 with raster armed, then the prepared `none`/`raster`/`raster-syncb` retention matrix. Photograph and identify the physical variant before assuming PSU or keyboard interchangeability. Keep the separate 12 ms parser margin investigation distinct. |

The board identifiers are inventory identities. Do not infer that `CS00000` is
the generic or factory-reference machine from its number, and do not transfer a
fault or repair conclusion between boards without a repeated test.

The authoritative machine-readable forms are in [`machines/`](machines/).
They preserve unknown values as `null` and bind every operational statement to
repository evidence.
