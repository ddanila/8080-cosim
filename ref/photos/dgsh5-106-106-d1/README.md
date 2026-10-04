# Juku ROM programming table — `ДГШ5.106.106 Д1`

Owner photographs (2026-07-18) of **ДГШ5.106.106 Д1 «Таблица программирования»**
— the factory hex listing of the `ДГШ5.106.106` ROM contents. Three sheets
(«Листов 3»), covering the full **0000–07FF (2 KiB)** address range.

## Artifact scope

The printed bytes identify a 2 KiB BASIC cartridge page. The reconstructed
image is `ref/reconstructed-firmware/dgsh5-106-106-d1.bin`, not a mainboard
PROM table or D15/D16 BIOS half. See the
[reconstruction report](../../../docs/dgsh5-106-106-rom-table.md) for hashes
and the archive/photo adjudication.

The first bytes are `C3 07 01` (`JMP 0107h`), followed later by BASIC
interpreter strings. These content observations do not establish a mainboard
reset mapping or a runnable cartridge entry address.

## Sheets

- `sheet1_PXL_20260718_122548761.jpg` — Лист 1: `0000`–`0320`
- `sheet2_PXL_20260718_122557171.jpg` — Лист 2: `0330`–`05F0`
- `sheet3_PXL_20260718_122601894.jpg` — Лист 3: `0600`–`07FF`

## Reviewed reconstruction

`scripts/reconstruct_dgsh5_106_106.py` reconstructs the complete page from
the archived `BAS0.HEX` transcription and an independent `jbasic11.bin` diff.
They disagree only at `021A`; the photographed row visibly reads `21`, not
the archive's `A1`. The resulting image exactly equals `roms/jbasic11.bin` file offsets
`0000-07FF`; these are file positions, not mapped cartridge addresses.
