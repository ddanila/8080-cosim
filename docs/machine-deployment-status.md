# Juku machine deployment status

Latest incorporated physical record: 2026-09-05

This summarizes the latest recorded location and fitted configuration for
each machine. It does not imply a new inventory inspection; detailed bench
evidence remains in the linked machine profiles and service records.

| Machine | Recorded location | Firmware / operating state | Open work |
| --- | --- | --- | --- |
| [CS00014](machines/CS00014.json) | Arvutimuuseum main exhibition | Stock ROM fitted; network-loaded CP/Mish and stock JF17 paths qualified in the profile's evidence. | Preserve the exhibition configuration; repeat bench work only when available. |
| [CS00015](machines/CS00015.json) | Home lab | JukuNet C8 / ABI 1.3 D15/D16 fitted. Network, diagnostics and host recovery are qualified; CPU-visible framebuffer storage works, but pixels remain absent with stable sync. | Diagnose the board-local video-data path. Retain C6 for rollback; controlled C1–C5 POST-tone checks remain pending. See [the service record](cs00015-service-record.md). |
| [CS00000](machines/CS00000.json) | Home lab | Corrected JukuNet C12 / ABI 1.5 pair fitted. Focused glyph, warm-boot and cold-state checks passed with the host started after the checkerboard. | Broader video/endurance and continuous-host reset recovery; preserve and investigate removed stock #0031 ROMs, sockets and original PSU separately. See [the service record](cs00000-service-record.md). |
| [CS00024](machines/CS00024.json) | Not recorded; last used on the diagnostic bench | T36 `1E/C617` last reported fitted; complete 32 KiB RAM proof under software refresh. Normal raster refresh remains unqualified. | Corrected D57 rerun, raster-retention matrix, separate parser-margin investigation and construction-variant identification. See [the diagnosis](cs00024-t36-diagnosis.md). |

The board identifiers are inventory identities. Do not infer that `CS00000` is
the generic or factory-reference machine from its number, and do not transfer a
fault or repair conclusion between boards without a repeated test.

The authoritative machine-readable forms are in [`machines/`](machines/).
They preserve unknown values as `null` and bind every operational statement to
repository evidence.
