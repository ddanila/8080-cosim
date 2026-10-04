# Juku processor-module `.009` electrical schematic — owner photos

Owner photographs (taken 2026-07-18) of the physical **ДГШ5.109.009 Э3**
«Модуль процессора / Схема электрическая принципиальная» — the **FDC-era
`.009` electrical schematic**, stamped «ДУБЛИКАТ».

## Revision scope

This is a *different drawing* from `ref/schematics/juku_es101_processor_module.pdf`,
which is the earlier **ДГШ5.109.006 Э3**. These photos provide the `.009`
electrical schematic; the related **ДГШ5.109.009 СБ** assembly/wire-table scan
(`ref/schematics/dgsh5_109_009_sb_sheets2-6.pdf`, with sheet-1 photos under
`ref/photos/dgsh5-109-009-sb/`) provides a separate connection-table source.

The decisive difference is **sheet 3**: on the `.006` it is the earlier
tape/serial subsystem; here it is the **floppy controller** built around the
КР1818ВГ93 (VG93) FDC and КР580ВА87 — the FDC-era circuit the `.009` parts list
and physical board actually populate.

Do **not** discard the `.006 Э3` — keep both. The `.006` remains the primary
factory drawing for the circuits it and the `.009` depict identically; the
`.009` outranks it wherever they diverge (sheet 3 FDC, and any post-`.006`
change notes).

## Title-block facts (all three sheets)

- Drawing: `ДГШ5.109.009 Э3` — «Модуль процессора», «Схема электрическая принципиальная».
- Format А1, ГОСТ style, three sheets («Листов 3»).
- Revision note: «Введён с 15.08.88 г.» on sheets 1 and 2; sheet 3 carries a
  later change stamp (perv. primen. `ДГШ5.109.009`, dated entry 13.04.89).
- Stamp: «ДУБЛИКАТ».

## Photo catalog

Each sheet was shot as one **overview** frame followed by **detail tiles in
reading order (left-to-right, top-to-bottom)**. Filenames are the camera's
timestamp order, so they already follow that sequence within each group.

### Sheet 1 — CPU / bus / ROM / interrupt / serial
КР580ВМ80-family CPU, ВК38 clock/controller, ВА86/ВА87 bus transceivers,
РЕ3/РТ4 PROMs, КР580ВМ59 (PIC), USART and connector continuations.

- `PXL_20260718_101754468.jpg` — overview
- `PXL_20260718_101801729.jpg` … `PXL_20260718_101827714.jpg` — 8 detail tiles
  (`_101801729`, `_101805510`, `_101809608`, `_101813438`, `_101817644`,
  `_101820818.MP`, `_101824181.MP`, `_101827714`)

### Sheet 2 — video / DRAM / timing
DRAM array, video counters/timing, VIDEO output stage (VT2 КТ315), and
beeper output stage (VT1 КТ972).

- `PXL_20260718_101901243.jpg` — overview
- `PXL_20260718_101908284.jpg` … `PXL_20260718_101932581.jpg` — 8 detail tiles
  (`_101908284`, `_101911242`, `_101914588`, `_101917240`, `_101921033.MP`,
  `_101924004`, `_101927794`, `_101932581`)

### Sheet 3 — floppy-disk controller (the FDC-era circuit)
КР1818ВГ93 (VG93) FDC D93, КР580ВА87 drive-output buffer D100, ROM D94,
clock MUX D95 (КП12),
data separator (ИЕ7 D106, ТМ2 D96, ЛА3), drive-select/step/direction latches,
X4 drive connector. Power table: К155ЛА3/К555ТМ2 etc. per «Питание микросхем
согласно таблице».
The original-pixel table at overview `(1200,2890)-(2700,3470)` is audited
against 25 rail endpoints on 12 fitted devices in
`docs/sheet3-power-table-audit.md`; board JSON and all three PCB pad sets
agree. This checks rail names, not copper continuity.

- `PXL_20260718_101633062.jpg` — overview (title block: «Лист 3 Листов 3»)
- `PXL_20260718_101637906.jpg` … `PXL_20260718_101648508.jpg` — 4 detail tiles
  (`_101637906`, `_101641055`, `_101644861`, `_101648508`)

## Reviewed interpretation and remaining checks

The [electrical audit](../../schematics/dgsh5-109-009-e3-notes.md)
checksum-guards all 23 source frames and indexes the reviewed sheet-1/2
revision differences and sheet-3 circuit transcriptions. Use those linked
reports for net assignments, source conflicts and physical continuity limits.

The long D40.11–D59.5–D92.2/.3–D95.5/.6 1 MHz route is adopted in the
source model, HDL, schematic and checked routed endpoints. Whole-board
routing release remains held. See
[the route review](../../../docs/d40-d59-d92-d95-1mhz-route.md).

D93 reset polarity is resolved: active-high RESET enters D13.9, and D13.8
supplies D93.19 MR_N. For the remaining D96 continuity/clear checks and
D99/D100 sheet continuations, use [the FDC handoff](../../../docs/fdc-hardware-handoff.md).
D101 input junctions and its selected write-data path are source-closed;
physical continuity and waveform quality remain bring-up checks.

Drawing-derived connectivity, photo registration and modeled behavior do not
prove original-board copper continuity or analog timing. The source frames
remain acquisition evidence.
