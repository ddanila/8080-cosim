# Juku ROM programming table — `ДГШ5.106.106 Д1`

Owner photographs (2026-07-18) of **ДГШ5.106.106 Д1 «Таблица программирования»**
— the factory hex listing of the `ДГШ5.106.106` ROM contents. Three sheets
(«Листов 3»), covering the full **0000–07FF (2 KiB)** address range.

## Why this matters

This is **authoritative factory ground-truth for a Juku ROM image** — printed
byte values, not a re-read of an aged part. Cross-check it against the
reconstructed / physically-read images under `ref/reconstructed-proms/`,
`ref/physical-proms/`, and `ref/eprom-images/`.

Observations from the listing:
- Reset vector at 0000: `C3 07 01` = `JMP 0107h` (8080/Z80).
- Later region contains ASCII BASIC interpreter strings — e.g. `?REDO FROM
  START`, `OUT OF DATA`, `OVERFLOW`, `DIVISION BY ZERO`, `SYNTAX ERROR`,
  `STRING TOO LONG` — i.e. this ROM carries (part of) the BASIC.

## Sheets

- `sheet1_PXL_20260718_122548761.jpg` — Лист 1: `0000`–`0320`
- `sheet2_PXL_20260718_122557171.jpg` — Лист 2: `0330`–`05F0`
- `sheet3_PXL_20260718_122601894.jpg` — Лист 3: `0600`–`07FF`

## TODO

- [ ] OCR/transcribe to a byte image and diff against the repo's reconstructed
      and physically-read PROM dumps; record any divergence with provenance.
