# Juku machine deployment status

Latest incorporated physical record: 2026-09-05

This summarizes the latest recorded location and fitted configuration for
each machine. It does not imply a new inventory inspection; detailed bench
evidence remains in the linked machine profiles and service records.

| Machine | Recorded location | Firmware / operating state | Open work |
| --- | --- | --- | --- |
| `CS00014` | Arvutimuuseum main exhibition | Stock ROM fitted. Previously passed the CP/Mish `NETROM2` network A:/native game B: demonstration; that test image was network-loaded and did not replace the fitted ROM. Later stock JF17 boot, T → N reset recovery and passive host replacement passed at 9600/8O1; see [the physical record](evidence/juku-serial/cs00014-stock-jf17-20260905/README.md). | Preserve the exhibition configuration; repeat bench work only when the machine is available. |
| `CS00015` | Home lab | JukuNet C8 / ABI 1.3 D15/D16 pair fitted, exact ROM SHA-256 `a54cb877edfe25e939e05ada0e98783acb53cfc8969071c63928b119c8e09e46`. Repeated automatic V16 boot, A:/B: NetDisk, diagnostics, local/N4 input, ROM sound, snapshot write, warm boot, soak, and live host replacement passed blind qualification. A native arm64 macOS host cold-booted this pair with S21 `07h`, then passed `STATUS`, `DIAG ALL`, `N4BULK`, and `SOAK`. A 2026-08-21 two-machine control subsequently proved stable sync and CPU-visible framebuffer RAM but no pixel output in 40x24, 53x24, or 80x24; the identical corrected raw pattern was visible on CS00014. | Diagnose the board-local video-data path after framebuffer storage. Retain C6 as the immutable rollback image; safely induced C1--C5 POST tones remain pending. |
| `CS00000` | Home lab | Corrected JukuNet C12 / ABI 1.4 D15/D16 pair installed on 2026-09-05, combined SHA-256 `b1a8152c0b4684d9d5608bd8bb60a06a21393c3bd7e7894cd8b7b61c494350d6`. Focused 80x24 glyph, warm-boot override, RESET and power-cycle cold-state checks passed. The reset checks started the host after the checkerboard appeared. See [C12 qualification](c12-runtime-console.md). | Broader corrected-pair video/endurance checks and continuous-host physical reset recovery remain open. Preserve the removed stock `#0031` pair and investigate it separately from the original PSU failure; see [the service record](cs00000-service-record.md). |
| `CS00024` | Not recorded; last handled on the diagnostic bench | T36 `1E/C617` was last reported fitted. Its corrected software refresh completed the full 32 KiB RAM proof; this does not validate the normal raster-refresh path. It is also an owner-observed construction variant: speaker fixed to the PSU, keyboard PCB lacking the comparison machines' central reverse-side designation, and a PSU-socket bracket mechanically incompatible with CS00000. | Rerun corrected D57 channel 2 with raster armed, then the prepared `none`/`raster`/`raster-syncb` retention matrix. Photograph and identify the physical variant before assuming PSU or keyboard interchangeability. Keep the separate 12 ms parser margin investigation distinct. |

The board identifiers are inventory identities. Do not infer that `CS00000` is
the generic or factory-reference machine from its number, and do not transfer a
fault or repair conclusion between boards without a repeated test.

The authoritative machine-readable forms are in [`machines/`](machines/).
They preserve unknown values as `null` and bind every operational statement to
repository evidence.
