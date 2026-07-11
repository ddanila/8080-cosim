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
    "ref/reconstructed-proms/d6_rt4_memory_decode_reconstructed.bin",
    "ref/reconstructed-proms/d8_re3_rom_pager_reconstructed.bin",
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
        "Status date: **2026-07-11**.",
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
            "no D2 `.037` or D94 `.092` programming payload; no complete Monitor 3.3 cartridge BASIC image/procedure",
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
            "Local WD1772 transistor/PLA reference",
            "checksum-guarded under `ref/wd1772-vg93/`; PLA normalized for future comparison",
            "deep reference only; not evidence for Juku-specific D93/D94 wiring",
        ]),
        "",
        "## Current source requests",
        "",
        "1. D2 `ДГШ5.106.037` repeated PROM dump or programming-disk file; all physical inputs and the used D0 output are already traced.",
        "2. D94 `ДГШ5.106.092` enable/output continuity and repeated PROM dump or programming-disk file.",
        "3. Pin-level continuity or explicit redesign/DNP dispositions for the 9 power-routed FDC-support boundaries: D28, D95-D99, D101, D102, and D106. D105 is now modeled and routed.",
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
