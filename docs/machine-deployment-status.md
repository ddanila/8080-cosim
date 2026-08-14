# Juku machine deployment status

Status date: 2026-08-14

This is the current location/configuration ledger reported after the successful
Arvutimuuseum demonstration. It records deployment state, not a new electrical
diagnosis; detailed bench evidence remains in each machine's service notes.

| Machine | Current location | Firmware / operating state | Open work |
| --- | --- | --- | --- |
| `CS00014` | Arvutimuuseum main exhibition | Stock ROM fitted. Previously passed the CP/Mish `NETROM2` network A:/native game B: demonstration; that test image was network-loaded and did not replace the fitted ROM. | Preserve the exhibition configuration; repeat bench work only when the machine is available. |
| `CS00015` | Home lab | Ekta4401 D15/D16 service-ROM pair fitted, including the Jukuravi API-v2 entry and the other recorded service-ROM changes. The board passed Jukuravi, 19200-mode-2 network disk, and CP/Mish A:/B:/`TETRIS.COM` checks. | Use as the working Jukuravi/reference machine; retain fitted-ROM and component provenance from `cs00015-service-record.md`. |
| `CS00000` | Home lab | Current firmware and broader boot state were not restated in this update. USART operation is suspected faulty. | Diagnose the serial path before declaring D11 bad: establish local 8251 status/clock behavior, then connector/level-shifter loopback and end-to-end traffic. Treat the USART fault as provisional until isolated. |

The board identifiers are inventory identities. Do not infer that `CS00000` is
the generic or factory-reference machine from its number, and do not transfer a
fault or repair conclusion between boards without a repeated test.
