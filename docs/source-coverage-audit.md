# Source coverage audit

Status date: **2026-07-10**.

Status: **PASS**

This is the single external-source inventory. It records only material
that affects the board, runnable twin, firmware/media, or current release
blockers. Broad historical link lists and completed search diaries are
deliberately omitted.

## Adopted sources

| Source | Local use | Remaining gap |
| --- | --- | --- |
| [Arti Juku archive](https://arti.ee/juku/) | schematics/assembly material, ROM lineage, EKDOS source, and raw disks under `ref/`, `roms/`, and `media/` | no D2 `.037` or D94 `.092` programming payload; no complete Monitor 3.3 cartridge BASIC image/procedure |
| [Elektroonikamuuseum Juku files](https://elektroonikamuuseum.ee/failid/juku/) | 16 Baltijets factory PDFs, J3K utility disk, and system binaries | doc 007 points to programming data on disk, but those disk files are not public in the mirrored set |
| [infoaed/juku3000](https://github.com/infoaed/juku3000) | ROM/media provenance and MAME/community cross-checks | contact path for hardware dumps; no additional public PROM payload adopted |
| [MAME Juku driver](https://github.com/mamedev/mame/blob/master/src/mame/ussr/juku.cpp) | behavioral oracle, I/O map, floppy geometry, raster constants; current master is vendored byte-for-byte as `ref/mame_juku.cpp` | emulator behavior cannot supply omitted physical nets or PROM truth |
| [MAME PR #14817](https://github.com/mamedev/mame/pull/14817) | real-hardware-tested 241st raster line and corrected JBASIC byte | already reflected in the local reference and video/BASIC guards |
| Arvutimuuseum/community pages | historical context and owner/contact leads only | promote a claim into the repo only when a file, checksum, photo, or measurement is obtained |
| Emu80v4 and public WD1793 HDL/software models | reviewed as implementation checklists; no code adopted | the local boot-scoped FDC model is sufficient until a concrete fidelity requirement justifies a licensed upstream core |
| Local WD1772 transistor/PLA reference | checksum-guarded under `ref/wd1772-vg93/`; PLA normalized for future comparison | deep reference only; not evidence for Juku-specific D93/D94 wiring |

## Current source requests

1. D2 `ДГШ5.106.037` input/output continuity and repeated PROM dump or programming-disk file.
2. D94 `ДГШ5.106.092` enable/output continuity and repeated PROM dump or programming-disk file.
3. Pin-level continuity or explicit redesign/DNP dispositions for all 10 placement-only official ICs: D28, D95-D99, D101, D102, D105, and D106. D105's wait chain, D30 section B, and the FDC cluster are first priority.
4. Complete Monitor 3.3-compatible cartridge BASIC artifact or documented factory loading procedure.
5. Targeted analog/timing measurements listed in `docs/owner-measurement-shortlist.md`.

`docs/community-prom-media-request.md` is the ready-to-send request. New
web/archive work should be tied to one of these named deliverables.

## Required local evidence

| Path | State |
| --- | --- |
| `ref/schematics/juku_es101_processor_module.pdf` | present |
| `ref/schematics/es101_emaplaat.pdf` | present |
| `ref/Juku_official_chip_BOM.pdf` | present |
| `ref/baltijets-tech-docs/007 ROM and ROM programming.pdf` | present |
| `ref/baltijets-tech-docs/009 FDDs.pdf` | present |
| `ref/ekdos-source/EKDOS30.ASM` | present |
| `ref/mame_juku.cpp` | present |
| `roms/ekta37.bin` | present |
| `roms/jmon33.bin` | present |
| `roms/jbasic11.bin` | present |
| `media/disks/JUKU1.CPM` | present |
| `media/disks/JUKPROG2.CPM` | present |
| `media/disks/J3KUTIL4.JUK` | present |
| `media/system/EKDOS230.BIN` | present |
| `ref/reconstructed-proms/d6_rt4_memory_decode_reconstructed.bin` | present |
| `ref/reconstructed-proms/d8_re3_rom_pager_reconstructed.bin` | present |
| `ref/wd1772-vg93/wd1772.pdf` | present |
| `ref/wd1772-vg93/wd1772pla.normalized.json` | present |
| `docs/d2-reconstruction-constraints.md` | present |
| `docs/d94-reconstruction-constraints.md` | present |
| `docs/firmware-gap-ledger.md` | present |
| `docs/vendored-disk-catalog.md` | present |
| `docs/community-prom-media-request.md` | present |
