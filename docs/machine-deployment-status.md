# Juku machine deployment status

Status date: 2026-08-16

This is the current location/configuration ledger reported after the successful
Arvutimuuseum demonstration. It records deployment state, not a new electrical
diagnosis; detailed bench evidence remains in each machine's service notes.

| Machine | Current location | Firmware / operating state | Open work |
| --- | --- | --- | --- |
| `CS00014` | Arvutimuuseum main exhibition | Stock ROM fitted. Previously passed the CP/Mish `NETROM2` network A:/native game B: demonstration; that test image was network-loaded and did not replace the fitted ROM. | Preserve the exhibition configuration; repeat bench work only when the machine is available. |
| `CS00015` | Home lab | Ekta4402 D15/D16 service-ROM pair fitted. Its direct `N` boot, CP/M Plus NetDisk-v3/N4 operation and live host reconnect are physically qualified. Its inherited `J` service entry passed two API-v2 attaches, PROBE, refresh query and READ with zero transport mismatch on 2026-08-16. | Use as the working Jukuravi/reference machine; retain the frozen Ekta4401 image as its historical service-ROM baseline and preserve fitted-ROM/component provenance from `cs00015-service-record.md`. |
| `CS00000` | Home lab | Current firmware and broader boot state were not restated in this update. USART operation is suspected faulty. | Diagnose the serial path before declaring D11 bad: establish local 8251 status/clock behavior, then connector/level-shifter loopback and end-to-end traffic. Treat the USART fault as provisional until isolated. |

The board identifiers are inventory identities. Do not infer that `CS00000` is
the generic or factory-reference machine from its number, and do not transfer a
fault or repair conclusion between boards without a repeated test.
