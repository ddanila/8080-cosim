# Source coverage audit

Status date: **2026-07-16**.

Status: **PASS**

This is the single external-source inventory. It records only material
that affects the board, runnable twin, firmware/media, or current release
blockers. Broad historical link lists and completed search diaries are
deliberately omitted.

## Adopted sources

| Source | Local use | Remaining gap |
| --- | --- | --- |
| [Arti Juku archive](https://arti.ee/juku/) | schematics/assembly material, ROM lineage, EKDOS source, and raw disks under `ref/`, `roms/`, and `media/` | no labeled PROM-programming payload; guarded `JUKPROG1/2/X` active/deleted-name, raw-marker, and exact byte/ASCII/Intel-hex/packed-nibble audit finds no validated table (a proprietary/permuted/compressed encoding remains possible); no complete Monitor 3.3 cartridge BASIC image/procedure |
| [Elektroonikamuuseum Juku files](https://elektroonikamuuseum.ee/failid/juku/) | 16 Baltijets factory PDFs, J3K utility disk, and system binaries | doc 007 points to programming data on disk, but those files are not public; the 2026-07-11 recheck found only duplicate `JUKUROMS.ZIP` ROMs and out-of-scope cassette utilities in new `CASTOOLS.JUK` media |
| [infoaed/juku3000](https://github.com/infoaed/juku3000) | ROM/media provenance and MAME/community cross-checks; full tree and Git object history audited at commit `be8bf9e53a6702299b9c0221d7c486fce1f25b0f` (2026-07-09) | no labeled RT4/RE3 table or factory PROM-programming payload; deleted `prog1.juk` blob `ed7fc2e3a289f25da5006143c9f45d9ac20ed3c2` is byte-identical to local `JUKPROG1.CPM` (SHA256 `94670f3333b29e205c1586a0f52882aaa0f8cff2d45c3493676ce3ab263ae269`) |
| [MAME Juku driver](https://github.com/mamedev/mame/blob/master/src/mame/ussr/juku.cpp) | behavioral oracle, I/O map, floppy geometry, raster constants; 2026-07-11 master is vendored byte-for-byte as `ref/mame_juku.cpp` (SHA256 `3b9dde3d3bc5eefd1271cd7a29266165d86f41882443f210437020d230a6202e`) | emulator behavior cannot supply omitted physical nets or PROM truth |
| [MAME PR #14817](https://github.com/mamedev/mame/pull/14817) | real-hardware-tested 241st raster line and corrected JBASIC byte | already reflected in the local reference and video/BASIC guards |
| Arvutimuuseum/community pages | historical context and owner/contact leads only | promote a claim into the repo only when a file, checksum, photo, or measurement is obtained |
| Emu80v4 and public WD1793 HDL/software models | reviewed as implementation checklists; no code adopted | the local boot-scoped FDC model is sufficient until a concrete fidelity requirement justifies a licensed upstream core |
| Western Digital FD179X references, the original 1986 КР1818ВГ93 paper, a historical Soviet circuit comparison, and the local WD1772 transistor/PLA reference | WD artifacts are checksum-guarded under `ref/wd1772-vg93/`; the literal Soviet-device pin contract, photo-closed IE7 Q3-to-RCLK path, remaining separator probes, a KP12 precompensation candidate, and normalized PLA are documented | target copper now proves D106.7-to-D93.26; device/manufacturer references narrow the remaining probes but do not prove other Juku-specific support nets or D94 connectivity |
| Owner photographs of `ДГШ5.109.009 СБ` | 26 checksum/LFS-guarded views under `ref/photos/dgsh5-109-009-sb/` establish factory placement, mounting details, and local D56/D15/D14/D11 assembly work; note 11 proves position 150 is tubing rather than a cut, owner-board registration closes D15 as an A2/A1 bridge cut and the D14 local D32.4/GND-to-D14.1 link, the D56 callout row is fixed at D56.12/D56.5, and target component/solder registration closes the complete 4x8 inherited DRAM-decoupler artwork as four factory-fitted plus 28 footprint-retained assembly-DNP positions | C51-C53/C70-C72 placement/population and every exact factory capacitance remain unresolved; the six former non-field fit-to-space coordinates are retired from the generator/source PCB until evidence closes them. The bare .009 C63 callout remains distinct from its inherited DRAM-grid verification landing, and C69 is restored to the photographed eighth column. D56's three physical callout locations are fixed as the separate left annulus plus D56.5/D56.12, but the installed item-159 conductor/material still requires continuity or its missing specification row; D14's registered fifth-landing conductor/remaining drawn traces still require exact mapping; position 159 marks solder locations and does not prove replacement conductors; D11's four solder locations are component-photo registered and two-sided package-local projection exhausts four solder views without a unique through-hole match, so their electrical endpoints require direct continuity; assembly detail does not prove every copper endpoint or programmable-part truth |

## Current source requests

1. Compare all four validated physical D2 `.037`, D6 `.038`, D8 `.039`, and D94 `.092` raw tables against Baltijets programming-disk files if those surface.
2. D94 `ДГШ5.106.092` input/enable/output continuity; the repeated content dump is already adopted.
3. Pin-level continuity for D93's complete drive interface, plus explicit dispositions for the 9 power-routed FDC-support boundaries: D28, D95-D99, D101, D102, and D106. D93.40->+12 V and the owner-measured D2/D30/D105/D13/D6 corrections are synchronized.
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
| `ref/juku-official-009-ic-census.json` | present |
| `ref/photos/dgsh5-109-009-sb/README.md` | present |
| `ref/photos/dgsh5-109-009-sb/rf-option-disposition.json` | present |
| `ref/photos/dgsh5-109-009-sb/factory-wire-landing-registration.json` | present |
| `ref/photos/dgsh5-109-009-sb/dram-decap-placement-registration.json` | present |
| `docs/assembly-drawing-extraction.md` | present |
| `docs/factory-modification-disposition.md` | present |
| `docs/factory-wire-route-fidelity.md` | present |
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
| `ref/physical-proms/validated/d2_037.raw.bin` | present |
| `ref/physical-proms/validated/d6_038.raw.bin` | present |
| `ref/physical-proms/validated/d8_039.raw.bin` | present |
| `ref/physical-proms/validated/d94_092.raw.bin` | present |
| `ref/wd1772-vg93/fd179x-01-datasheet.pdf` | present |
| `ref/wd1772-vg93/fd179x-application-notes-jun1980.pdf` | present |
| `ref/wd1772-vg93/wd1772.pdf` | present |
| `ref/wd1772-vg93/wd1772pla.normalized.json` | present |
| `docs/d2-reconstruction-constraints.md` | present |
| `docs/d94-reconstruction-constraints.md` | present |
| `docs/firmware-gap-ledger.md` | present |
| `docs/vendored-disk-catalog.md` | present |
| `docs/community-prom-media-request.md` | present |
