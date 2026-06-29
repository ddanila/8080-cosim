# Juku processor-module schematic — SOURCE OF TRUTH

Authoritative electrical schematic of the Juku processor module. From now on this
**supersedes the MAME-derived map** wherever they disagree (MAME was a stand-in
until we had the real drawing).

- **File:** `juku_es101_processor_module.pdf`
- **Drawing:** ДГШ5.109.006 Э3 — «Модуль процессора. Схема электрическая принципиальная»
- **Source:** https://arti.ee/juku/ (Juku preservation archive)
- **Format:** 3-sheet raster scan, ~A1, ГОСТ style, Russian/Estonian labels
- **Variant:** ES101/E5101 family (NB: our HDL/map were derived from MAME's **E5104** —
  expect real differences, esp. tape-vs-disk and RAM organization; record them).

## Page ↔ sheet mapping (PDF page order is reversed)
| PDF page | sheet | rendered PNG | contents |
|---|---|---|---|
| 3 | Лист 1 | `p3_sheet1.png` | CPU `КР580ВМ80`, 8238 (`БК38`), 8286 (`БА86`) buffers, ROM/EPROM + RAM array, 8251/8255/8259, edge connectors X2–X9 |
| 2 | Лист 2 | `p2_sheet2.png` | counters/timers `ВИ53`, RAM `РУ5` array, video address/sync, baud/tape gen |
| 1 | Лист 3 | `p1_sheet3.png` | USART/SIO, tape interface (`СА3` comparator), serial connectors, glue |

PNGs are 150 DPI renders (`pdftoppm`) kept for close reading + transcription; re-render
specific regions at higher DPI as needed.
