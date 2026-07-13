# Baltijets Juku E5104 technical documentation

Source:
`https://elektroonikamuuseum.ee/failid/juku/tech_docs_from_baltijets/`

Fetched: 2026-07-06.
Remote directory rechecked: 2026-07-11; it still listed files `000` through
`015`, matching the 16 mirrored PDFs.

The directory contains 16 PDFs found in the former Baltijets factory building in
Narva and scanned in November 2024. `000 Info.pdf` is text-searchable; the other
PDFs are image scans. The adjacent `.txt` files are `pdftotext` outputs and
contain no useful body OCR for the scan-only PDFs beyond sparse metadata.

`SHA256SUMS` records the fetched PDF hashes.

## Doc 007 ROM/programming triage

`007 ROM and ROM programming.pdf` does not close the small PROM byte-content
blocker. It confirms the existence/type/provenance of several programmed parts,
but the relevant small-PROM tables are referenced as disk-held programming
tables rather than printed in the PDF:

| Page | Drawing | Part | Finding |
|---|---|---|---|
| 16 | `ДГШ5.106.038` | `КР556РТ4` | programming table `ДГШ5.106.038 Д1`; note says `на диске` |
| 17 | `ДГШ5.106.040` | `К573РФ5` | EPROM, table `ДГШ5.106.040 Д1`; `на диске` |
| 18 | `ДГШ5.106.092` | printed `КР556РТ5` crossed out; handwritten amendment `К155РЕ3` | programming table `ДГШ5.106.092 Д1`; `на диске` |
| 19-22 | `ДГШ5.106.106` | `К573РФ2` | printed hex listing `ДГШ5.106.106 Д1`; already low priority because РФ2 ROMs are available elsewhere |
| 23 | `ДГШ5.106.107` | `К573РФ2` | EPROM sheet, no printed byte table on the shown page |

Implication for the replica plan:

- `ДГШ5.106.037/.038` remain dump-or-disk items for the two `КР556РТ4`
  decode PROMs.
- `ДГШ5.106.039` remains the needed D8 `К155РЕ3` content.
- `ДГШ5.106.092` is explicitly amended to `К155РЕ3` in the factory paperwork,
  matching the .009 parts list and the physical D94 package. It is not an
  abstract/removed placeholder; only its programmed bits and incomplete copper
  destinations remain unresolved.
- The owner/community dump request remains necessary unless the referenced
  programming-disk files surface.

## Doc 002 schematics/components first pass

`002 Schematics and components.pdf` is a mixed packet: assembly/mechanical
drawings, component lists, applicability tables, and a few connection schematics.
It does not contain a replacement full processor-module schematic in this scan,
so it does not close the remaining CPU-board net unknowns by itself.

Useful pages identified in the first pass:

| Page | Finding |
|---|---|
| 28 | Power-supply schematic `ДГШ2.087.031 Э3`, showing +5 V/+12 V/GND connector mapping and PSU component values. Useful for later PSU recreation, not processor-board LVS. |
| 29 | Power-supply element list `ДГШ2.087.031 ПЭ3`; confirms PSU capacitors, regulators, diodes, transformer, fuse, and connector types. |
| 32 | Interface-terminal connection schematic `ДГШ3.031.007 Э4`; confirms X8 power pins 62/61/60/59 and X9 signal labels including `K2`, `K0`, `K1`, `-ГК`, `+5V`, `SHIFT`, `CTRL`, `WAIT`, `STB`, `SC0`..`SC3`. Useful for bring-up cabling. |
| 34-35 | Applicability/specification table for `ДГШ5.109.009` processor module. Confirms the .009 module includes programmed microcircuits `ДГШ5.106.037`, `.038`, `.039`, `.041`, `.042`, `.043`, `.087`, `.088`, `.089`, `.090`, `.091`, `.092`, plus related module/enclosure items. |

Implication:

- The repo's .009/FDC processor-module target is corroborated by factory
  applicability tables.
- The table confirms the small PROM drawing numbers already seen in doc 007,
  but still gives no byte contents.
- The P0 connectivity blockers in `PLAN.md` still need either the original
  processor schematic pages, the referenced programming disk, or hardware
  continuity/dump sessions.

## Doc 010 parts-list first pass

`010 Parts list.pdf` is a parts-list/kit packet rather than the adjustment
instructions anticipated in PLAN's `010-class` placeholder. It is still useful
for sourcing:

| Page | Finding |
|---|---|
| 20 | Group комплект/BOM page includes `ДГШ5.109.009`, `КР1818ВГ93`, `КР556РТ4`, and the КР580-family logic mix. This supports the long-lead sourcing list and the .009 FDC revision target. |

Implication:

- Treat doc 010 as sourcing/census evidence, not timing/adjustment evidence.
- RAS/CAS/refresh and RF/video adjustment data still need to come from another
  adjustment document in the Baltijets set, not this parts-list PDF.

## Doc 003 adjustment-instructions pass

`003 Adjustment instructions.pdf` is the expected E5104 adjustment/check packet
(`ДГШ3.031.011 Д2`). It is a factory bring-up and acceptance document, not a
processor schematic, so it does not close PROM contents or hidden copper nets. It
does provide useful system-level oracles for digital-twin and physical bring-up work:

| Page | Finding |
|---|---|
| 2 | Contents list confirms sections for processor module `ДГШ5.109.009`, main PSU `ДГШ5.087.019`, FDD PSU `ДГШ2.087.031`, manipulator `ДГШ3.049.040`, keyboard module `ДГШ3.104.015`, complete E5104 terminal check, and burn-in/vibration. |
| 3 | Adjustment object list includes processor module `.009`, PSU, FDD PSU, manipulator, keyboard module, and removable memory expander `ДГШ5.106.102`; bench setup includes setup stand `ДГШ3.058.002`, two `МС6105-04` monitors, oscilloscope `C1-114`, and supply `ГН-09-01`. |
| 4 | FDD PSU check gives concrete voltages: set +12 V to `12.1 +/- 0.05 V`; check +5 V at `5 +/- 0.25 V`; idle +12 V on X1/X2 pins 1/2 should be `12 +/- 1 V`; insulation test is 1 minute at 750 V AC. |
| 5 | System check starts with video warm-up, then auto-tests system RAM/video RAM from `D300H` to `FFFFH`; normal monitor-ready message is `ROMBIOS 3.43` followed by `*`. EKDOS boot uses disk `JUKU-1 ДГШ5.106.105` in left drive A and key sequence `<T>, <D>, <D>`; normal result is prompt `A>`. |
| 5 | Factory software checks also include QRUN diagnostics, printer check via `CTRL+F` and `D000/003F`, manipulator check using EKDOS and editor `GR`, and BASIC launch from the removable memory expander by command `A`, expecting the BASIC banner and `READY`. |
| 6-6a | Local-network check uses at least four terminals, network switches per the appendix, NETD/NET boot prompts, and visible `ARVUTUSTEHNIKA EKB` / `EKDOS 1.0` / `JANET 1.2` style messages. |
| 6b | Factory burn-in is 100 hours at `(25 +/- 10) C`, with the last 4 hours at `+35 C`; QRUN is run before, every 24 hours, and at the end. Vibration is 10 minutes at 30 Hz and 20 m/s^2 with equipment off. |

Implication:

- The FDC/EKDOS oracle should use the factory key sequence and prompt:
  `ROMBIOS 3.43` -> `*` -> `<T>, <D>, <D>` -> `A>`, with `JUKU-1` as the
  first disk target.
- Physical bring-up can reference factory acceptance strings and QRUN/burn-in
  cadence instead of inventing its own final smoke test.
- RAS/CAS timing and PROM byte contents are still not printed here.

## Doc 009 FDD-unit pass

`009 FDDs.pdf` is the floppy unit packet `ДГШ3.065.008`: assembly drawing,
schematic, element list, and technical description. It is useful for the Tier-2
storage path and Gotek/real-drive cabling.

| Page | Finding |
|---|---|
| 1 | Documentation list names `ДГШ3.065.008 СБ`, `Э3`, `ПЭ3`, and `ТО`; assembly units include FDD PSU `ДГШ2.087.031` plus chassis/mechanical/cable parts. |
| 5 | The FDD-unit electrical sheet includes a 23-contact interface table. Legible signal rows are 8 READY, 9 STEP, 11 WRITE DATA, 14 TRACK 0, 15 INDEX, 16 DIRECTION, 18 WRITE GATE, 19 MOTOR ON, 20 SIDE SELECT, 21 SELECT 1, 22 SELECT 0, and 23 READ DATA; pins 1-6 are shown as ground. The scan does not expose a complete processor-X4-to-FDD pin permutation. |
| 6/8 | Drive power connector table: drive X1 pin 1 = +12 V, pins 2/3 = ground, pin 4 = +5 V. PSU-side output table shows +5 V on pin 1, +12 V on pin 3, ground on pins 2/4. |
| 6/8 | 34-pin FDD signal mapping is Shugart-style: INDEX 8, SEL0 10, SEL1 12, MOTOR ON 16, DIR 18, STEP 20, WRITE DATA 22, WRITE GATE 24, TRACK 0 26, WRITE PROTECT 28, READ DATA 30, SIDE SELECT 32, READY 34. Odd pins 1,3,5,7 / 9,11,13,15 / 17,19,21,23 / 25,27,29,31,33 are ground. |
| 8 | The drawing labels the drive as `НГМД ЕС 5323.01`. |

Implication:

- A Gotek/HxC adapter for the first EKDOS boot should preserve the standard
  active-low 34-pin control/data map above and provide READY on pin 34.
- The real-drive path needs +5 V/+12 V power with the drive connector polarity
  checked against the original drawing before use.

## Doc 011 cable pass

`011 Cable.pdf` contains three cable assemblies rather than one processor-board
pinout. Pages 4-5 describe `ДГШ4.853.042`: a 1.5 m cable with two identical
23-contact `РП15-23` plugs. The assembly drawing shows the physical cable and
strain relief, but no conductor-by-conductor connection table. Pages 6-8 are
`ДГШ4.853.043`, whose connection diagram is the printer interface
(`DATA1`-`DATA8`, `STROBE`, `SELECT`, `ERROR`, `PE`, and `ACKNLG`), not the FDD
interface.

Implication:

- The `.042` hardware is consistent with a 23-contact inter-unit cable, but the
  scan does not prove that its contacts are straight-through or that either end
  is processor connector X4. It therefore cannot yet promote X4.6-X4.23 from
  explicit harness boundaries to named FDD signals.
- A cable continuity measurement, an explicit `.042` connection schematic, or
  another factory interconnection table is still required before applying the
  FDD-unit page-5 names to processor X4.

## Doc 014 removable-memory-expander pass

`014 External storage.pdf` is not floppy storage. It is the removable 32K memory
expander (`Сменный расширитель`) packet `ДГШ5.106.102`, with module
`ДГШ5.106.103`.

| Page | Finding |
|---|---|
| 1 | Packet contains assembly drawing `ДГШ5.106.102 СБ`, passport `ДГШ5.106.102 ПС`, and assembly unit `ДГШ5.106.103` (`Модуль ЗУ-32К`). |
| 10 | Schematic page shows ROM/RAM devices marked `573 РФ4` and `РУ8`, with jumpers/switches selecting memory content/banks. |

Implication:

- This document feeds the BASIC/removable-memory path and physical cartridge
  recreation, not the FDD cable plan.

## Doc 015 floppy-disk label pass

`015 Floppy disk.pdf` is a one-page assembly drawing for disk label `ДГШ5.106.105
СБ`. The table maps the base designation to `JUKU-1`, suffix `-01` to `JUKU-2`,
and suffix `-02` to `JUKU-3`.

Implication:

- Doc 003's EKDOS boot disk `JUKU-1 ДГШ5.106.105` is a factory-named disk label
  family, not a dumped image by itself. The actual disk image still needs to come
  from MAME/juku3000 media or a physical disk dump.
