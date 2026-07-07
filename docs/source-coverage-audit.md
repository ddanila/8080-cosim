# Source coverage audit

Status date: 2026-07-07.

This audit records how the public Juku archives are used by this repository. It
is deliberately conservative: "used" means a source materially affected the
replica board, digital twin, firmware/media probes, manufacturing packet, or
bring-up plan. It does not mean every historical article, manual page, program,
or disk image has been fully mined.

## Summary

| Source | Current coverage | Gap |
| --- | --- | --- |
| `https://arti.ee/juku/` | Main ES101 board drawings, processor-module schematic, component list, keyboard/PSU/case drawings, and legacy ROM/BASIC materials are mirrored or reflected in `ref/`, `roms/`, board placement, BOM, and transcription docs. `tarkvara/JUKU1.7Z` and `JUKU2.7Z` are now vendored under `media/disks/`; `JUKU1.CPM` boots to `A>` in cosim. | The Russian manuals, Estonian user manual, remaining software/game archives, emulator pages, `Noorte_Hääl_1987-04`, and forum links are not exhaustively mined for hardware-critical details. |
| `https://elektroonikamuuseum.ee/failid/juku/` | `tech_docs_from_baltijets/` 000-015 are mirrored with text extraction in `ref/baltijets-tech-docs/` and mined for factory test, ROM-programming, FDD, power, keyboard, and peripheral planning. The `tarkvara/J3KUTIL4.JUK` image has been used as non-vendored EKDOS prompt evidence. The small `tarkvara/JUKUSYS.ZIP` CP/M/EKDOS system binaries are vendored under `media/system/`. | The broader `tarkvara/` disk-image set and `kirjandus/` manuals are not exhaustively classified; Baltijets programming-disk files remain missing. |
| `https://github.com/infoaed/juku3000/tree/master/roms` | The ROM lineage is covered: canonical ROMs are vendored under `roms/`; `jmon22.bin` is vendored from the public museum ROM bundle; legacy `BAS0-3` and `JUKUROM0/1` material is mirrored under `ref/firmware/` and feeds BASIC/ROM-window work. | The repo still needs PROM provenance and HDL disk-backed media work, not more РФ2 ROM coverage. |
| `https://arvutimuuseum.ee/cs00000/` | Used as historical/contextual confirmation for E5104/Baltijets/museum contact and public-preservation context. | Not a primary electrical source. Its exhibit text, photos, and linked historical references are not exhaustively mined into board/twin evidence. |

## Board-critical materials already consumed

- ES101 main-board drawing and processor-module schematics drive the placement,
  netlist, LVS, and routed replica package.
- Component-list material drives `docs/replica-dual-config-bom.*`,
  `docs/replica-sourcing-readiness.md`, and the generated parts/order gates.
- Arti/juku3000 ROM and BASIC files drive the boot, BASIC cartridge, monitor, and
  ROM-window probes.
- Baltijets docs 002/003/007/009/010/014/015 are reflected in `PLAN.md` and the
  FDC/media/PROM/bring-up docs. The key conclusion remains: doc 007 describes
  programmed-part drawings but references small-PROM byte tables on disk, so the
  РЕ3/РТ4 truth still needs the programming disk or hardware dumps.
- Elektroonikamuuseum `tarkvara/JUKUSYS.ZIP` is now vendored under
  `media/system/` as five 10 KiB CP/M/EKDOS system binaries. The same public
  software archive pass found no explicit `ДГШ5.106.037`, `ДГШ5.106.038`,
  `ДГШ5.106.039`, or `ДГШ5.106.092` PROM programming files.

## Not yet exhaustive

- Arti manual PDFs and the Arti `tarkvara/` collection.
- Elektroonikamuuseum `kirjandus/` manuals and the full `tarkvara/` disk-image
  inventory beyond the vendored Arti images, vendored `JUKUSYS.ZIP` binaries,
  and the earlier `J3KUTIL4.JUK` prompt probe.
- Arvutimuuseum photos/articles/linked references beyond project context and
  contact path.
- Forum-linked owner knowledge from Arti/Arvutimuuseum pages, except where
  already captured in `docs/community-prom-media-request.md`.

## Practical implication

The current manufacturing packet does not appear blocked by unused РФ2 ROM
material. The remaining source-risk items are narrower:

- Baltijets programming-disk files or physical РЕ3/РТ4 dumps.
- Disk-backed FDC behavior in `juku_top`; the vendored Arti `JUKU1.CPM`
  image now proves the cosim `JUKU1` boot path.
- Owner/community confirmation for the generated bring-up verification list.
- Optional mining of manuals/software for Tier 2/Tier 3 fidelity, especially
  storage workflows, keyboard/monitor operation, and original user-facing
  software behavior.
