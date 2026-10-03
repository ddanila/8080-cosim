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
    "ref/photos/dgsh5-109-009-sb/factory-wire-landing-registration.json",
    "ref/photos/dgsh5-109-009-sb/dram-decap-placement-registration.json",
    "docs/assembly-drawing-extraction.md",
    "docs/factory-modification-disposition.md",
    "docs/factory-wire-route-fidelity.md",
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
    "ref/physical-proms/validated/d8_039.raw.bin",
    "ref/physical-proms/validated/d94_092.raw.bin",
    "ref/wd1772-vg93/fd179x-01-datasheet.pdf",
    "ref/wd1772-vg93/fd179x-application-notes-jun1980.pdf",
    "ref/wd1772-vg93/wd1772.pdf",
    "ref/wd1772-vg93/wd1772pla.normalized.json",
    "ref/datasheets/k555lp5-eandc.pdf",
    "ref/datasheets/sn74ls86a-ti.pdf",
    "ref/datasheets/k555lp5-output-reference.txt",
    "ref/datasheets/kt315-family-promelec.pdf",
    "ref/datasheets/kt315b-output-reference.txt",
    "ref/datasheets/sn54s138-ti.pdf",
    "ref/datasheets/kr531id7-timing-reference.txt",
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
        f"Status: **{status}**",
        "",
        "This inventory records adopted sources and remaining recovery inputs.",
        "`PASS` means the required local paths below exist. This generator does",
        "not validate their contents/checksums, repeat image review, or recheck",
        "remote archives. Source dates and identities describe recorded reviews.",
        "",
        "Regenerate with `python3 scripts/report_source_coverage_audit.py`.",
        "Remote-source findings below describe the recorded reviews, not a current",
        "availability check. Follow the owning evidence reports for review details.",
        "",
        "## Adopted sources",
        "",
        "| Source | Local use | Remaining gap |",
        "| --- | --- | --- |",
        row([
            "[Arti Juku archive](https://arti.ee/juku/)",
            "schematics/assembly material, ROM lineage, EKDOS source, and raw disks under `ref/`, `roms/`, and `media/`",
            "No validated PROM table was recovered by the [local disk audit](vendored-disk-catalog.md); transformed encodings remain possible. The [cartridge BASIC boundary](cartridge-basic-boundary.md) remains open.",
        ]),
        row([
            "[Elektroonikamuuseum Juku files](https://elektroonikamuuseum.ee/failid/juku/)",
            "16 Baltijets factory PDFs, J3K utility disk, and system binaries",
            "Doc 007 refers to disk programming data; the recorded July 2026 archive review did not recover those files. Adopted PROM contents are available independently from physical reads.",
        ]),
        row([
            "[infoaed/juku3000](https://github.com/infoaed/juku3000)",
            "ROM/media provenance and MAME/community cross-checks; full tree and Git object history audited at commit `be8bf9e53a6702299b9c0221d7c486fce1f25b0f` (2026-07-09)",
            "No labeled PROM payload was found in the recorded tree/history review. Recovered deleted `prog1.juk` blob `ed7fc2e3a289f25da5006143c9f45d9ac20ed3c2` duplicates local `JUKPROG1.CPM` (SHA256 `94670f3333b29e205c1586a0f52882aaa0f8cff2d45c3493676ce3ab263ae269`); use the [disk catalog](vendored-disk-catalog.md) for the local content audit.",
        ]),
        row([
            "[Juku software catalog](https://j3k.infoaed.ee/tarkvara-kataloog/)",
            "The recorded 2026-07-22 catalog review listed `JBASIC11.BIN` as 8K. See [cartridge lineage](cartridge-basic-firmware-lineage.md) for the bootstrap length and missing-page evidence.",
            "That review did not recover the missing `0x2100..0x21FF` page. A complete artifact or loading procedure remains required.",
        ]),
        row([
            "[MAME Juku driver](https://github.com/mamedev/mame/blob/master/src/mame/ussr/juku.cpp)",
            "behavioral oracle, I/O map, floppy geometry, raster constants; the recorded 2026-07-11 snapshot is vendored as `ref/mame_juku.cpp` (SHA256 `3b9dde3d3bc5eefd1271cd7a29266165d86f41882443f210437020d230a6202e`)",
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
            "Guarded component references under `ref/datasheets/`",
            "exact-device К555ЛП5 and period КТ315-family sheets constrain D34/VT2 electrical corners; TI SN74LS86A independently compares the XOR output conditions; the primary TI SN54S138 sheet bounds a pin/function-compatible D53 decoder at 12 ns maximum under its published test point",
            "К555ЛП5 still lacks a nonlinear output I/V curve; SN54S138 timing is a compatible-device comparison rather than an exact КР531ИД7 process guarantee; Juku loading, decoder enables, and CPU/video slot timing still require measurements or stronger primary evidence",
        ]),
        row([
            "Western Digital FD179X references, the original 1986 КР1818ВГ93 paper, a historical Soviet circuit comparison, and the local WD1772 transistor/PLA reference",
            'Device/PLA references under `ref/wd1772-vg93/`; see [FDC handoff](fdc-hardware-handoff.md) for the adopted device contracts and separator/precompensation boundaries.',
            'Juku-specific separator, shared-clear and powered asynchronous behavior remain qualification boundaries in the [FDC handoff](fdc-hardware-handoff.md); component references alone do not close them.',
        ]),
        row([
            "Owner photographs of exact `ДГШ5.109.009 Э3` sheets 1-3",
            "the exact FDC-era electrical revision is checksum-guarded under `ref/photos/dgsh5-109-009-e3/` and is the primary schematic source; owner continuity on 2026-07-21 confirms its D54/D55/D56 sheet-2 timing paths and the D94/D104 NC dispositions",
            "retain the older `.006 Э3` as secondary evidence only where it agrees; exact `.009` imagery and physical-board continuity outrank it wherever they differ",
        ]),
        row([
            "Owner photographs of `ДГШ5.109.009 СБ`",
            'Factory placement, mounting and modifications under `ref/photos/dgsh5-109-009-sb/`; see [assembly extraction](assembly-drawing-extraction.md), [modification disposition](factory-modification-disposition.md), and [decoupling fidelity](decap-value-fidelity.md).',
            'Remaining capacitance/population, auxiliary annulus and modification-wire endpoints are tracked by the linked reports. Photo registration does not prove electrical continuity or programmable-part truth.',
        ]),
        "",
        "## Current source requests",
        "",
        '1. D94 D0 hidden-branch continuity and optional live port-1F steering capture; see [D94 constraints](d94-reconstruction-constraints.md).',
        '2. Remaining D93 drive-interface and the 4 still-open FDC-support devices (D96, D99, D100, D101) require continuity/powered checks in [FDC handoff](fdc-hardware-handoff.md), including the shared D96/D99 clear source and D96 restart behavior.',
        "3. Complete Monitor 3.3-compatible cartridge BASIC artifact or documented factory loading procedure.",
        "4. Targeted analog/timing measurements listed in `docs/owner-measurement-shortlist.md`.",
        "5. Optionally compare all four adopted small-PROM tables against Baltijets programming-disk files if those surface; preserve differences as board/program variants.",
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
