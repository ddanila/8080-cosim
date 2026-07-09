#!/usr/bin/env python3
"""Generate the public-source coverage audit."""
from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "source-coverage-audit.md"


def exists(path: str) -> bool:
    return (ROOT / path).exists()


REQUIRED_PATHS = [
    "ref/schematics/es101_emaplaat.pdf",
    "ref/schematics/juku_es101_processor_module.pdf",
    "ref/baltijets-tech-docs/007 ROM and ROM programming.pdf",
    "ref/baltijets-tech-docs/007 ROM and ROM programming.txt",
    "ref/baltijets-tech-docs/009 FDDs.pdf",
    "ref/baltijets-tech-docs/015 Floppy disk.txt",
    "ref/ekdos-source/EKDOS30.ASM",
    "media/disks/JUKU1.CPM",
    "media/disks/JUKPROG2.CPM",
    "media/disks/J3KUTIL4.JUK",
    "media/system/EKDOS230.BIN",
    "roms/ekta37.bin",
    "roms/jmon33.bin",
    "roms/jbasic11.bin",
    "ref/firmware/JUKUROM0.HEX",
    "ref/firmware/JUKUROM1.HEX",
    "ref/firmware/re3_dgsh5.106.113.hex",
    "ref/firmware/re3_dgsh5.106.117.hex",
    "ref/reconstructed-proms/d6_rt4_memory_decode_reconstructed.bin",
    "ref/reconstructed-proms/d8_re3_rom_pager_reconstructed.bin",
    "ref/extracted-software/JUKPROG2_JBASIC.COM",
    "ref/extracted-software/JUKPROG2_JBASIC_live_candidate.COM",
    "ref/extracted-software/JUKU1_JBASIC_raw_candidate.COM",
    "ref/wd1772-vg93/wd1772.pdf",
    "ref/wd1772-vg93/wd1772pla.normalized.json",
    "docs/emu80v4-survey.md",
    "docs/fdc-core-survey.md",
    "docs/wd1772-vg93-reference.md",
    "docs/wd1772-pla-inspection.md",
    "docs/d2-reconstruction-constraints.md",
    "docs/d94-reconstruction-constraints.md",
    "docs/vendored-disk-catalog.md",
    "docs/basic-disk-extraction.md",
    "docs/basic-cartridge-tail-hypotheses.md",
    "docs/basic-cartridge-missing-page-constraints.md",
    "docs/public-software-archive-inventory.md",
    "docs/re3-firmware-inspection.md",
    "docs/reconstructed-prom-fallbacks.md",
    "docs/ekdos-source-inspection.md",
    "docs/community-prom-media-request.md",
    "docs/owner-measurement-shortlist.md",
]


SOURCE_ROWS = [
    (
        "`https://arti.ee/juku/`",
        "Main ES101 board drawings, processor-module schematic, component list, "
        "keyboard/PSU/case drawings, ROM/BASIC lineage, EKDOS source, and "
        "Arti-derived raw disks are mirrored or reflected in `ref/`, `roms/`, "
        "`media/disks/`, the board placement, generated BOM, transcription "
        "docs, and FDC/BASIC probes.",
        "Russian manuals, Estonian user manual, remaining software/game "
        "archives, emulator pages, newspaper scan, and forum links are not "
        "exhaustively mined for hardware-critical details.",
    ),
    (
        "`https://elektroonikamuuseum.ee/failid/juku/`",
        "`tech_docs_from_baltijets/` 000-015 are mirrored with text extraction "
        "under `ref/baltijets-tech-docs/` and mined for factory test, ROM "
        "programming, FDD, power, keyboard, and peripheral planning. Public "
        "system binaries from `JUKUSYS.ZIP` are vendored under `media/system/`; "
        "`J3KUTIL4.JUK` is vendored under `media/disks/`; the public software "
        "listing is classified in `docs/public-software-archive-inventory.md`.",
        "Additional museum `kirjandus/` manuals are not exhaustively classified. "
        "The Baltijets programming disk files referenced by doc 007 remain missing.",
    ),
    (
        "`https://github.com/infoaed/juku3000/tree/master/roms`",
        "ROM lineage is covered: canonical monitor/BIOS ROMs are vendored "
        "under `roms/`; legacy `BAS0-3` and `JUKUROM0/1` material is mirrored "
        "under `ref/firmware/` and feeds BASIC/ROM-window work.",
        "The project now needs PROM provenance and uninterrupted HDL "
        "disk-backed media work, not more РФ2 ROM coverage.",
    ),
    (
        "`https://arvutimuuseum.ee/cs00000/`",
        "Used as historical/contextual confirmation for E5104/Baltijets, "
        "museum contact, and public-preservation context.",
        "Not a primary electrical source. Exhibit text, photos, and linked "
        "historical references are not exhaustively mined into board/twin "
        "evidence.",
    ),
    (
        "`https://github.com/vpyk/emu80v4`",
        "Surveyed as an emulator reference. No Juku-specific driver/config "
        "was found, but its GPL-3 `Fdc1793` model is recorded as a behavior "
        "checklist in `docs/emu80v4-survey.md` and `docs/fdc-core-survey.md`.",
        "GPL-3 code is not vendored or copied. It does not close any "
        "Juku-specific PROM/media/netlist gap.",
    ),
    (
        "Local WD1772 transistor/PLA files from `~/Downloads`",
        "`wd1772.pdf` and `wd1772pla.txt` are vendored under "
        "`ref/wd1772-vg93/`; the PLM table is normalized to JSON/CSV and "
        "guarded by `docs/wd1772-pla-inspection.md`.",
        "Reference material only. It supports future ВГ93/FD1773 fidelity "
        "work but is not translated into HDL and does not add Juku-specific "
        "media, PROM contents, or board connectivity.",
    ),
]


def evidence_table() -> list[str]:
    lines = [
        "| Evidence path | Status |",
        "| --- | --- |",
    ]
    for path in REQUIRED_PATHS:
        lines.append(f"| `{path}` | {'present' if exists(path) else 'MISSING'} |")
    return lines


def main() -> int:
    missing = [path for path in REQUIRED_PATHS if not exists(path)]
    status = "PASS" if not missing else "MISSING REQUIRED SOURCE EVIDENCE"

    lines = [
        "# Source coverage audit",
        "",
        "Status date: 2026-07-09.",
        "",
        f"Status: **{status}**",
        "",
        "This generated audit records how the public Juku archives are used by",
        "this repository. It is deliberately conservative: \"used\" means a",
        "source materially affected the replica board, digital twin,",
        "firmware/media probes, manufacturing packet, or bring-up plan. It does",
        "not mean every historical article, manual page, program, or disk image",
        "has been fully mined.",
        "",
        "## Summary",
        "",
        "| Source | Current coverage | Gap |",
        "| --- | --- | --- |",
    ]
    for source, coverage, gap in SOURCE_ROWS:
        lines.append(f"| {source} | {coverage} | {gap} |")

    lines.extend(
        [
            "",
            "## Required local evidence",
            "",
            *evidence_table(),
            "",
            "## Board-critical materials already consumed",
            "",
            "- ES101 main-board drawing and processor-module schematics drive the",
            "  placement, netlist, LVS, and routed replica package.",
            "- Component-list material drives `docs/replica-dual-config-bom.*`,",
            "  `docs/replica-sourcing-readiness.md`, and the generated parts/order",
            "  gates.",
            "- Arti/juku3000 ROM and BASIC files drive the boot, BASIC cartridge,",
            "  monitor, and ROM-window probes.",
            "- Arti EKDOS source files are vendored under `ref/ekdos-source/`.",
            "  `docs/ekdos-source-inspection.md` guards the monitor-call, disk",
            "  parameter, and floppy-handler constants used by the `TDD`/FDC work.",
            "- `scripts/report_vendored_disk_catalog.py` indexes the vendored Arti",
            "  and museum raw disk images and records disk-side BASIC candidates.",
            "  `J3KUTIL4.JUK` is cataloged alongside the CP/M images; `JUKU1.CPM`",
            "  contains `JBASIC.COM`; `JUKPROG2.CPM` contains `JBASIC.COM`,",
            "  `B80.COM`, `BRUN.COM`, `BASCOM.COM`, `BASCOM.DOK`, and",
            "  `BASLIB.REL`.",
            "- `scripts/report_public_software_archive_inventory.py` classifies the",
            "  observed Arti and Elektroonikamuuseum software listings. It keeps",
            "  required binaries/images vendored and marks classroom/game/tape",
            "  collections as optional Tier 2/Tier 3 preservation inputs.",
            "- `scripts/extract_basic_disk_files.py` extracts and vendors the",
            "  strongest disk-side BASIC candidates under `ref/extracted-software/`.",
            "- `scripts/report_basic_cartridge_missing_page_constraints.py` records",
            "  the static constraints on the missing Monitor 3.3 BASIC cartridge",
            "  page and confirms no current vendored artifact supplies a page donor.",
            "- Baltijets docs 002/003/007/009/010/014/015 are reflected in",
            "  `PLAN.md` and the FDC/media/PROM/bring-up docs. Doc 007 describes",
            "  programmed-part drawings but references small-PROM byte tables on",
            "  disk, so РЕ3/РТ4 truth still needs the programming disk or hardware",
            "  dumps.",
            "- `scripts/export_reconstructed_proms.py` exports boot-validated",
            "  reconstructed D6 and D8 fallback images under",
            "  `ref/reconstructed-proms/`. These close the reproducible Tier 1/2",
            "  programming fallback path, not the Tier 3 dump/provenance requirement.",
            "- `scripts/report_re3_firmware_inspection.py` guards the tracked",
            "  owner-scan К155РЕ3 `.113`/`.117` excerpts and the current conclusion",
            "  that these `.106.103`-family tables are not the processor-module",
            "  D8 `.039` or D94 `.092` contents.",
            "- Elektroonikamuuseum `tarkvara/JUKUSYS.ZIP` is vendored under",
            "  `media/system/` as five 10 KiB CP/M/EKDOS system binaries.",
            "  `J3KUTIL4.JUK` is vendored under `media/disks/` because earlier FDC",
            "  docs cite it as a prompt-proof disk. The public software archive pass",
            "  found no explicit `ДГШ5.106.037`, `ДГШ5.106.038`, `ДГШ5.106.039`,",
            "  or `ДГШ5.106.092` PROM programming files.",
            "- The local WD1772 schematic/PLA files are useful below the emulator-core",
            "  abstraction: they can cross-check ВГ93/FD1773-compatible signal names",
            "  and PLA behavior if a full controller model becomes necessary.",
            "",
            "## Not yet exhaustive",
            "",
            "- Arti manual PDFs beyond the hardware-critical schematics/component",
            "  lists and EKDOS/software source files.",
            "- Elektroonikamuuseum `kirjandus/` manuals beyond the Baltijets technical",
            "  document mirror.",
            "- Arvutimuuseum photos/articles/linked references beyond project context",
            "  and contact path.",
            "- Forum-linked owner knowledge from Arti/Arvutimuuseum pages, except",
            "  where already captured in `docs/community-prom-media-request.md`.",
            "",
            "## Practical implication",
            "",
            "The current manufacturing packet does not appear blocked by unused РФ2",
            "ROM material. The remaining source-risk items are narrower:",
            "",
            "- Baltijets programming-disk files or physical РЕ3/РТ4 dumps.",
            "- Diff any eventual D6/D8 dumps against `ref/reconstructed-proms/` before",
            "  replacing the current boot-validated reconstruction in HDL.",
            "- Disk-backed FDC behavior stays guarded by vendored `JUKU1.CPM` and",
            "  `J3KUTIL4.JUK`; no unvendored public disk is required for current",
            "  EKDOS/JBASIC evidence.",
            "- Owner/community confirmation for the generated bring-up verification",
            "  list, now compressed into `docs/owner-measurement-shortlist.md`.",
            "- Optional mining of manuals/software for Tier 2/Tier 3 fidelity,",
            "  especially storage workflows, keyboard/monitor operation, and original",
            "  user-facing software behavior.",
        ]
    )

    if missing:
        lines.extend(["", "## Missing evidence", ""])
        lines.extend(f"- `{path}`" for path in missing)

    OUT.write_text("\n".join(lines) + "\n")
    print(f"Wrote {OUT.relative_to(ROOT)}")
    return 1 if missing else 0


if __name__ == "__main__":
    raise SystemExit(main())
