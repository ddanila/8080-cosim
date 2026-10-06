# Source coverage audit

Status: **PASS**

This inventory records adopted sources and remaining recovery inputs.
`PASS` means all paths in the generator’s `REQUIRED` list exist. It does
not validate their contents/checksums, repeat image review, or recheck
remote archives. Source dates and identities describe recorded reviews,
not current availability; follow the linked reports for review details.

Run from the repository root with Python 3 (standard library only):
`python3 scripts/report_source_coverage_audit.py`.
The writer replaces this report even when required paths are missing;
it exits 0 when all paths exist and 1 when any are missing.

## Adopted sources

| Source | Local use | Remaining gap |
| --- | --- | --- |
| [Arti Juku archive](https://arti.ee/juku/) | schematics/assembly material, ROM lineage, EKDOS source, and raw disks under `ref/`, `roms/`, and `media/` | No validated PROM table was recovered by the [local disk audit](vendored-disk-catalog.md); transformed encodings remain possible. The [cartridge BASIC boundary](cartridge-basic-boundary.md) remains open. |
| [Elektroonikamuuseum Juku files](https://elektroonikamuuseum.ee/failid/juku/) | 16 Baltijets factory PDFs, J3K utility disk, and system binaries | Doc 007 refers to disk programming data; the recorded July 2026 archive review did not recover those files. Adopted PROM contents are available independently from physical reads. |
| [infoaed/juku3000](https://github.com/infoaed/juku3000) | ROM/media provenance and MAME/community cross-checks; full tree and Git object history audited at commit `be8bf9e53a6702299b9c0221d7c486fce1f25b0f` (2026-07-09) | No labeled PROM payload was found in the recorded tree/history review. The recovered `prog1.juk` duplicates local `JUKPROG1.CPM`; see the [disk identities](../media/disks/README.md) and [content audit](vendored-disk-catalog.md). |
| [Juku software catalog](https://j3k.infoaed.ee/tarkvara-kataloog/) | The recorded 2026-07-22 catalog review listed `JBASIC11.BIN` as 8K. See [cartridge lineage](cartridge-basic-firmware-lineage.md) for the bootstrap length and missing-page evidence. | That review did not recover the missing `0x2100..0x21FF` page. A complete artifact or loading procedure remains required. |
| [Vendored MAME Juku driver](../ref/mame_juku.cpp) | behavioral oracle, I/O map, floppy geometry, raster constants; the recorded 2026-07-11 snapshot is vendored as `ref/mame_juku.cpp` (SHA256 `3b9dde3d3bc5eefd1271cd7a29266165d86f41882443f210437020d230a6202e`) | emulator behavior cannot supply omitted physical nets or PROM truth |
| [MAME PR #14817](https://github.com/mamedev/mame/pull/14817) | real-hardware-tested 241st raster line and corrected JBASIC byte | already reflected in the local reference and video/BASIC guards |
| Arvutimuuseum/community pages | historical context and owner/contact leads only | promote a claim into the repo only when a file, checksum, photo, or measurement is obtained |
| Emu80v4 and public WD1793 HDL/software models | reviewed as implementation checklists; no code adopted | The local model’s exercised behavior and unresolved hardware boundaries are documented in [FDC readiness](fdc-readiness.md) and [FDC handoff](fdc-hardware-handoff.md). |
| Guarded component references under `ref/datasheets/` | exact-device К555ЛП5 and period КТ315-family sheets constrain D34/VT2 electrical corners; TI SN74LS86A independently compares the XOR output conditions; the primary TI SN54S138 sheet bounds a pin/function-compatible D53 decoder at 12 ns maximum under its published test point | К555ЛП5 still lacks a nonlinear output I/V curve; SN54S138 timing is a compatible-device comparison rather than an exact КР531ИД7 process guarantee; Juku loading, decoder enables, and CPU/video slot timing still require measurements or stronger primary evidence |
| Western Digital FD179X references, the original 1986 КР1818ВГ93 paper, a historical Soviet circuit comparison, and the local WD1772 transistor/PLA reference | Device/PLA references under `ref/wd1772-vg93/`; see [FDC handoff](fdc-hardware-handoff.md) for the adopted device contracts and separator/precompensation boundaries. | Juku-specific separator, shared-clear and powered asynchronous behavior remain qualification boundaries in the [FDC handoff](fdc-hardware-handoff.md); component references alone do not close them. |
| Owner photographs of exact `ДГШ5.109.009 Э3` sheets 1-3 | the exact FDC-era electrical revision is checksum-guarded under `ref/photos/dgsh5-109-009-e3/` and is the primary schematic source; owner continuity on 2026-07-21 confirms its D54/D55/D56 sheet-2 timing paths and the D94/D104 NC dispositions | retain the older `.006 Э3` as secondary evidence only where it agrees; exact `.009` imagery and physical-board continuity outrank it wherever they differ |
| Owner photographs of `ДГШ5.109.009 СБ` | Factory placement, mounting and modifications under `ref/photos/dgsh5-109-009-sb/`; see [assembly extraction](assembly-drawing-extraction.md), [modification disposition](factory-modification-disposition.md), and [decoupling fidelity](decap-value-fidelity.md). | Remaining capacitance/population, auxiliary annulus and modification-wire endpoints are tracked by the linked reports. Photo registration does not prove electrical continuity or programmable-part truth. |

## Current source requests

1. D94 D0 hidden-branch continuity and optional live port-1F steering capture; see [D94 constraints](d94-reconstruction-constraints.md).
2. Remaining D93 drive-interface and the 4 still-open FDC-support devices (D96, D99, D100, D101) require continuity/powered checks in [FDC handoff](fdc-hardware-handoff.md), including the shared D96/D99 clear source and D96 restart behavior.
3. Complete Monitor 3.3-compatible cartridge BASIC artifact or documented factory loading procedure.
4. Targeted analog/timing measurements listed in `docs/owner-measurement-shortlist.md`.
5. Optionally compare all four adopted small-PROM tables against Baltijets programming-disk files if those surface; preserve differences as board/program variants.

`docs/community-prom-media-request.md` is the ready-to-send request. New
web/archive work should be tied to one of these named deliverables.

## Required local evidence

Present: **42/42** required paths.
The complete checked list is `REQUIRED` in the
[generator](../scripts/report_source_coverage_audit.py). Any missing paths are listed below.
