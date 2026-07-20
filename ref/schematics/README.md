# Juku processor-module factory drawings

Two electrical-schematic revisions of the processor module exist; **keep both**:

- **`.006 Э3`** — `juku_es101_processor_module.pdf` (below). Earlier revision;
  its sheet 3 is the tape/serial subsystem.
- **`.009 Э3`** — the later FDC-era revision, photographed by the owner under
  `ref/photos/dgsh5-109-009-e3/` (2026-07-18). Its sheet 3 is the КР1818ВГ93
  floppy controller. This closes the "Document gap" tracked in `PLAN.md`: the
  `.009 Э3` was not public anywhere. Where the two diverge (sheet-3 FDC vs
  tape, and post-`.006` change notes), the `.009` wins; elsewhere they agree
  and the `.006` scan is the higher-resolution source. See that folder's
`README.md` for the per-sheet photo catalog.
The checksum-guarded reviewed transcription/divergence index is
`dgsh5-109-009-e3-notes.md`.

`juku_es101_processor_module.pdf` is the primary factory electrical schematic
for the ДГШ5.109.006 processor module. It outranks emulator inference for the
circuits it depicts, but it is not the complete `.009` FDC-era target by
itself: sheet 3 shows the earlier tape subsystem, while the official `.009`
parts list, the `.009 Э3` photos, and physical-board evidence establish the
later FDC population.

- Drawing: `ДГШ5.109.006 Э3` — processor module electrical schematic.
- Source: https://arti.ee/juku/
- Format: three-sheet raster scan, approximately A1, ГОСТ style.
- Related evidence: `es101_emaplaat.pdf` assembly/placement drawing,
  `es101_nimekiri_komponendid.pdf`, `ref/Juku_official_chip_BOM.pdf`, and the
  owner photographs under `ref/photos/`.

`dgsh5_109_009_sb_sheets2-6.pdf` is the owner-supplied «ДУБЛИКАТ» scan of
sheets 2-6 of the `ДГШ5.109.009 СБ` assembly drawing: the таблица соединений
(wire/cable connection table, sheets 2-5) and the change-registration sheet 6.
Sheet 1 of the same document is photographed in
`ref/photos/dgsh5-109-009-sb/`. The reviewed transcription is
`dgsh5-109-009-sb-wire-table.md`.

## PDF page mapping

| PDF page | Sheet | Rendered PNG | Main contents |
| ---: | ---: | --- | --- |
| 3 | 1 | `p3_sheet1.png` | CPU, controller/buffers, ROM, RAM interface, PPI/PIC/USART, connectors |
| 2 | 2 | `p2_sheet2.png` | PITs, DRAM array/timing, video counters and output timing |
| 1 | 3 | `p1_sheet3.png` | earlier tape/serial subsystem; do not map its reused D94-D108 refdes onto `.009` FDC parts |

The PNGs are 150-DPI working renders. Electrical claims should cite the
factory sheet plus any `.009` BOM/photo/continuity evidence needed to resolve
revision differences. The normalized current interpretation lives in
`kicad/juku.board.json` with provenance and explicit boundaries.
