#!/usr/bin/env python3
"""Generate a concise inventory of adopted external Juku evidence."""

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "docs/source-coverage-audit.md"

REQUIRED = [
    "ref/schematics/juku_es101_processor_module.pdf",
    "ref/schematics/es101_emaplaat.pdf",
    "ref/Juku_official_chip_BOM.pdf",
    "ref/juku-official-009-ic-census.json",
    "ref/photos/dgsh5-109-009-sb/README.md",
    "ref/photos/dgsh5-109-009-sb/rf-option-disposition.json",
    "docs/assembly-drawing-extraction.md",
    "docs/factory-modification-disposition.md",
    "ref/baltijets-tech-docs/007 ROM and ROM programming.pdf",
    "ref/baltijets-tech-docs/009 FDDs.pdf",
    "ref/ekdos-source/EKDOS30.ASM",
    "ref/mame_juku.cpp",
    "roms/ekta37.bin",
    "roms/jmon33.bin",
    "roms/jbasic11.bin",
    "media/disks/JUKU1.CPM",
    "media/disks/JUKPROG2.CPM",
    "media/disks/J3KUTIL4.JUK",
    "media/system/EKDOS230.BIN",
    "ref/physical-proms/validated/d2_037.raw.bin",
    "ref/physical-proms/validated/d6_038.raw.bin",
    "ref/reconstructed-proms/d8_re3_rom_pager_reconstructed.bin",
    "ref/wd1772-vg93/fd179x-01-datasheet.pdf",
    "ref/wd1772-vg93/fd179x-application-notes-jun1980.pdf",
    "ref/wd1772-vg93/wd1772.pdf",
    "ref/wd1772-vg93/wd1772pla.normalized.json",
    "docs/d2-reconstruction-constraints.md",
    "docs/d94-reconstruction-constraints.md",
    "docs/firmware-gap-ledger.md",
    "docs/vendored-disk-catalog.md",
    "docs/community-prom-media-request.md",
]


def row(values: list[object]) -> str:
    return "| " + " | ".join(str(value).replace("|", "/") for value in values) + " |"


def main() -> int:
    missing = [path for path in REQUIRED if not (ROOT / path).exists()]
    status = "PASS" if not missing else "MISSING REQUIRED LOCAL EVIDENCE"
    lines = [
        "# Source coverage audit",
        "",
        "Status date: **2026-07-13**.",
        "",
        f"Status: **{status}**",
        "",
        "This is the single external-source inventory. It records only material",
        "that affects the board, runnable twin, firmware/media, or current release",
        "blockers. Broad historical link lists and completed search diaries are",
        "deliberately omitted.",
        "",
        "## Adopted sources",
        "",
        "| Source | Local use | Remaining gap |",
        "| --- | --- | --- |",
        row([
            "[Arti Juku archive](https://arti.ee/juku/)",
            "schematics/assembly material, ROM lineage, EKDOS source, and raw disks under `ref/`, `roms/`, and `media/`",
            "no D2 `.037` or D94 `.092` programming payload; guarded `JUKPROG1/2/X` active/deleted-name and raw-marker audit finds no labeled PROM candidate (an unidentified binary remains possible); no complete Monitor 3.3 cartridge BASIC image/procedure",
        ]),
        row([
            "[Elektroonikamuuseum Juku files](https://elektroonikamuuseum.ee/failid/juku/)",
            "16 Baltijets factory PDFs, J3K utility disk, and system binaries",
            "doc 007 points to programming data on disk, but those files are not public; the 2026-07-11 recheck found only duplicate `JUKUROMS.ZIP` ROMs and out-of-scope cassette utilities in new `CASTOOLS.JUK` media",
        ]),
        row([
            "[infoaed/juku3000](https://github.com/infoaed/juku3000)",
            "ROM/media provenance and MAME/community cross-checks; full tree and Git object history audited at commit `be8bf9e53a6702299b9c0221d7c486fce1f25b0f` (2026-07-09)",
            "no `ДГШ5.106.037`/`.092`, RT4/RE3 table, or factory PROM-programming payload; deleted `prog1.juk` blob `ed7fc2e3a289f25da5006143c9f45d9ac20ed3c2` is byte-identical to local `JUKPROG1.CPM` (SHA256 `94670f3333b29e205c1586a0f52882aaa0f8cff2d45c3493676ce3ab263ae269`)",
        ]),
        row([
            "[MAME Juku driver](https://github.com/mamedev/mame/blob/master/src/mame/ussr/juku.cpp)",
            "behavioral oracle, I/O map, floppy geometry, raster constants; 2026-07-11 master is vendored byte-for-byte as `ref/mame_juku.cpp` (SHA256 `3b9dde3d3bc5eefd1271cd7a29266165d86f41882443f210437020d230a6202e`)",
            "emulator behavior cannot supply omitted physical nets or PROM truth",
        ]),
        row([
            "[MAME PR #14817](https://github.com/mamedev/mame/pull/14817)",
            "real-hardware-tested 241st raster line and corrected JBASIC byte",
            "already reflected in the local reference and video/BASIC guards",
        ]),
        row([
            "Arvutimuuseum/community pages",
            "historical context and owner/contact leads only",
            "promote a claim into the repo only when a file, checksum, photo, or measurement is obtained",
        ]),
        row([
            "Emu80v4 and public WD1793 HDL/software models",
            "reviewed as implementation checklists; no code adopted",
            "the local boot-scoped FDC model is sufficient until a concrete fidelity requirement justifies a licensed upstream core",
        ]),
        row([
            "Western Digital FD179X-01 datasheet and June-1980 application notes plus local WD1772 transistor/PLA reference",
            "checksum-guarded under `ref/wd1772-vg93/`; primary 40-pin FD1793 contract adopted, manufacturer counter/separator topology retained as a guarded continuity constraint, and PLA normalized for future comparison",
            "manufacturer references prove package functions and a plausible counter/separator scaffold, not Juku-specific D93 support-net continuity or D94 truth",
        ]),
        row([
            "Owner photographs of `ДГШ5.109.009 СБ`",
            "26 checksum/LFS-guarded views under `ref/photos/dgsh5-109-009-sb/` establish factory placement, mounting details, and the D56/D15/D14/D11 solder-side cut/patch instructions",
            "assembly detail proves intended modifications and locality, not every copper endpoint or programmable-part truth",
        ]),
        "",
        "## Current source requests",
        "",
        "1. Compare the validated physical D2 `.037` and D6 `.038` raw tables against Baltijets programming-disk files if those surface; D6 would benefit from an additional separately power-cycled confirmation.",
        "2. D94 `ДГШ5.106.092` enable/output continuity and repeated PROM dump or programming-disk file.",
        "3. Pin-level continuity for D93's complete drive interface and +12 V supply, plus explicit dispositions for the 9 power-routed FDC-support boundaries: D28, D95-D99, D101, D102, and D106. The owner-measured D2/D30/D105/D13/D6 corrections are synchronized.",
        "4. Complete Monitor 3.3-compatible cartridge BASIC artifact or documented factory loading procedure.",
        "5. Targeted analog/timing measurements listed in `docs/owner-measurement-shortlist.md`.",
        "",
        "`docs/community-prom-media-request.md` is the ready-to-send request. New",
        "web/archive work should be tied to one of these named deliverables.",
        "",
        "## Required local evidence",
        "",
        "| Path | State |",
        "| --- | --- |",
    ]
    for path in REQUIRED:
        lines.append(row([f"`{path}`", "present" if (ROOT / path).exists() else "MISSING"]))
    if missing:
        lines.extend(["", "## Missing", ""])
        lines.extend(f"- `{path}`" for path in missing)
    lines.append("")
    REPORT.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {REPORT.relative_to(ROOT)}")
    return 0 if not missing else 1


if __name__ == "__main__":
    raise SystemExit(main())
