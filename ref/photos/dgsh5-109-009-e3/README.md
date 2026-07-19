# Juku processor-module `.009` electrical schematic — owner photos

Owner photographs (taken 2026-07-18) of the physical **ДГШ5.109.009 Э3**
«Модуль процессора / Схема электрическая принципиальная» — the **FDC-era
`.009` electrical schematic**, stamped «ДУБЛИКАТ».

## Why this matters

This is a *different drawing* from `ref/schematics/juku_es101_processor_module.pdf`,
which is the earlier **ДГШ5.109.006 Э3**. Until these photos, the `.009 Э3`
electrical revision was a documented gap: a 2026-07-14 web sweep confirmed it
was not public anywhere (see `PLAN.md`, "Document gap"), and the repo held the
`.009` family only as the **ДГШ5.109.009 СБ** assembly/wire-table scan
(`ref/schematics/dgsh5_109_009_sb_sheets2-6.pdf`, sheet-1 photos under
`ref/photos/dgsh5-109-009-sb/`) — a connection table, not an electrical
schematic. These photos are the `.009` electrical schematic itself.

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
РЕ3/РТ4 PROMs, КР580ВМ59 (PIC), USART + RS-232 serial (X3/X5/X6).

- `PXL_20260718_101754468.jpg` — overview
- `PXL_20260718_101801729.jpg` … `PXL_20260718_101827714.jpg` — 8 detail tiles
  (`_101801729`, `_101805510`, `_101809608`, `_101813438`, `_101817644`,
  `_101820818.MP`, `_101824181.MP`, `_101827714`)

### Sheet 2 — video / DRAM / timing
DRAM array, video counters/timing, VIDEO output stage (КТ972).

- `PXL_20260718_101901243.jpg` — overview
- `PXL_20260718_101908284.jpg` … `PXL_20260718_101932581.jpg` — 8 detail tiles
  (`_101908284`, `_101911242`, `_101914588`, `_101917240`, `_101921033.MP`,
  `_101924004`, `_101927794`, `_101932581`)

### Sheet 3 — floppy-disk controller (the FDC-era circuit)
КР1818ВГ93 (VG93) FDC (D100), КР580ВА87, ROM D94, clock MUX D95 (КП12),
data separator (ИЕ7 D106, ТМ2 D96, ЛА3), drive-select/step/direction latches,
X4 drive connector. Power table: К155ЛА3/К555ТМ2 etc. per «Питание микросхем
согласно таблице».

- `PXL_20260718_101633062.jpg` — overview (title block: «Лист 3 Листов 3»)
- `PXL_20260718_101637906.jpg` … `PXL_20260718_101648508.jpg` — 4 detail tiles
  (`_101637906`, `_101641055`, `_101644861`, `_101648508`)

## Status / TODO

- [x] Targeted sheet-1 D6 polarity read: D6.12/D0 is drawn directly to
      D8.15/E through R11, and D6.9/D3 directly to D13.1 through R14; D13 is
      the only drawn inverter (`docs/d6-physical-decode.md`).
- [x] Sheet-3 X4 connector read and НГМД reconciliation: all used signal
      contacts are mapped, and the drawing identifies D100 as the drive-output
      buffer rather than the inferred FDC data-bus buffer
      (`ref/schematics/fdc-x4-ngmd-wire-map.md`).
- [ ] Transcribe each sheet into a reviewed net/wire interpretation and
      reconcile against `kicad/juku.board.json` and the `.006 Э3`; record any
      `.006`→`.009` divergences (esp. sheet-3 FDC vs tape).
- [ ] Cross-check the sheet-3 FDC nets against `ref/wd1772-vg93/` predictions
      and the physical-board evidence in `ref/photos/dgsh5-109-009-sb/`.
