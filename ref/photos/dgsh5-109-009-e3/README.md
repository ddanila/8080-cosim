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
КР1818ВГ93 (VG93) FDC D93, КР580ВА87 drive-output buffer D100, ROM D94,
clock MUX D95 (КП12),
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
- [x] Sheet-1/3 FDC source read: D93 DAL0-DAL7 join D0-D7 directly; D26
      PC2/PC4/PC5/PC6 supply MOTOR EN/FM-MFM/D_SEL/S.SEL; D28.2 cascades to
      D28.3 to generate the complementary drive selects.
- [x] Sheet-3 input/open-collector pull-ups reconciled with the `.009 СБ`
      assembly drawing: R79-R85 and R98 are modeled at their registered
      positions with exact values and endpoints.
- [x] Sheet-3 D97/D102/D101 write-precompensation chain transcribed with all
      timing passives; target copper resolves the drawing's duplicated R99,
      conflicting R86, and D101 junctions
      (`ref/schematics/fdc-write-precomp-map.md`).
- [x] Sheet-3 D95 clock mux completely transcribed: D40's 1/2 MHz rails feed
      D93 CLK, its 4/8 MHz rails feed D106 DOWN, FM/MFM and 5-inch/8-inch are
      the shared selects, and both enables are grounded
      (`ref/schematics/fdc-clock-mux-map.md`).
- [x] Sheet-3 D106 recovery counter completely transcribed: R78 pulls UP and
      all four preset inputs high, D95 clocks DOWN, RAW READ drives /LOAD,
      CLR is grounded, Q3 drives D28.9, and the five undrawn outputs are NC
      (`ref/schematics/fdc-recovery-counter-map.md`). R78 value and placement
      remain explicitly unresolved.
- [x] Sheet-3 D96 read-clock toggle completely transcribed: WREQ_N drives both
      asynchronous controls, /Q feeds D, D28.8 clocks section 1, Q drives
      D93 RCLK, and the undrawn second half is NC except for its independently
      photo-proved pin-8 test landing
      (`ref/schematics/fdc-read-clock-toggle-map.md`).
- [x] Exact-revision unused sections reconciled: the drawing omits D28's last
      two inverter pairs, D98 buffer pair 4, D97 Q/pin13, and D102 /Q/pin4.
      Those eight pads are guarded NCs, while live D28 READY pins5/6 are no
      longer contradicted by stale NC metadata
      (`ref/schematics/fdc-unused-pin-dispositions.md`).
- [x] Sheet-1/3 D93 static paths reconciled: `RES (3)` lands on D93.19, and
      sheet 3 directly ties TEST/pin22 to WF/VFOE/pin33. The drawn reset-polarity
      tension remains an explicit scope check
      (`ref/schematics/fdc-controller-static-map.md`).
- [x] Sheet-3 D93 HLT/RG paths reconciled: E11's drawn 2-3 selection straps
      HLT/pin23 to READY/pin32 (MOTOR EN is the alternate source), and RG/pin25
      is deliberately omitted between the explicit pin-24 and pin-26 paths
      (`ref/schematics/fdc-hlt-rg-map.md`).
- [x] Sheet-3 D99 timing paths reconciled: grounded A1/CLR1,
      C17/C18/R97/R103 timing networks, and unused pin13 are modeled and
      structurally guarded. D99.10 and joined D100.9/.11 are correctly retained
      as distinct sheet-1 continuations, not logic-high markers
      (`ref/schematics/fdc-d99-timing-map.md`).
- [x] Sheet-3 DRQ/INTRQ conditioner reconciled: D28 sections 5/6, R93/R95,
      and D96 section 2 are restored; D96.9/.11 remain sheet-1 boundaries
      (`ref/schematics/fdc-irq-conditioner-map.md`).
- [ ] Transcribe each sheet into a reviewed net/wire interpretation and
      reconcile against `kicad/juku.board.json` and the `.006 Э3`; record any
      `.006`→`.009` divergences (esp. sheet-3 FDC vs tape).
- [ ] Cross-check the sheet-3 FDC nets against `ref/wd1772-vg93/` predictions
      and the physical-board evidence in `ref/photos/dgsh5-109-009-sb/`.
