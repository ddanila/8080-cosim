#!/usr/bin/env python3
"""Generate a classified inventory of Arvutimuuseum Juku context."""
from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "docs" / "arvutimuuseum-context-inventory.md"


def table_row(values: list[object]) -> str:
    return "| " + " | ".join(str(value).replace("|", "/") for value in values) + " |"


FACT_ROWS = [
    (
        "Museum item identity",
        "Juku E5104, museum ID CS00000, producer lineage EKTA/Estron/Baltijets, year 1989",
        "context",
        "Matches the project scope and Baltijets/EKTA production trail; not a netlist source.",
    ),
    (
        "CPU/RAM/ROM headline",
        "KR580VM80A / Intel 8080A-class CPU, 64 KiB RAM, 16 KiB ROM",
        "cross-check",
        "Consistent with the modeled vm80a, DRAM array, and two 2764-class ROM sockets.",
    ),
    (
        "Video headline",
        "Monochrome video with 24x40 / 20x64 text modes and 320x240 / 384x200 headline resolutions",
        "cross-check",
        "Consistent with the current 320x241/40-byte raster guard and broader MAME/manual context; not precise timing evidence.",
    ),
    (
        "Storage/peripherals",
        "External 5.25-inch floppy unit, cassette path, serial/parallel/floppy-tape/bus expansion ports",
        "context",
        "Matches PLAN Tier-2/Tier-3 peripherals and out-of-scope tape/network/mouse decisions.",
    ),
    (
        "Reference kit",
        "E5101 main module, MC6105 monitor, E6502 dual floppy unit, E4701 mouse, optional E6201 RAM disk, D2-36-1 PSU, printer, cables/docs",
        "Tier-3 context",
        "Useful as a faithful-system shopping/checklist reference, not required for current PCB fabrication.",
    ),
    (
        "Operating systems",
        "LOS or EKDOS/CP-M based system software",
        "cross-check",
        "Consistent with the repo's EKDOS media and the explicit tape/network out-of-scope boundary.",
    ),
    (
        "Historical software list",
        "ROMBIOS tooling, LOS, file manager, graphics editor, text editor, network manager, Xonix, Snake, synthesizer, CP/M tools and languages",
        "optional software context",
        "Useful for future preservation, but no listed item supplies the missing PROM tables or cartridge BASIC page.",
    ),
    (
        "Working museum artifact",
        "Museum notes the surviving Juku E5101 is preserved in good working condition",
        "owner/community path",
        "Supports community/owner-contact strategy; it is not a measured dump or continuity record.",
    ),
]


LINK_ROWS = [
    ("Baltijets technical documentation", "already mirrored", "ref/baltijets-tech-docs/", "Primary factory packet already consumed."),
    ("Mikroarvuti JUKU kasutamisjuhend", "classified", "docs/public-manual-archive-inventory.md", "Large user manual stays optional until a procedure-specific task needs it."),
    ("Russian user manual", "classified", "docs/public-manual-archive-inventory.md", "Large user/service manual stays optional unless a new clue is needed."),
    ("Juku E5104 manuals/files page", "classified", "docs/public-manual-archive-inventory.md; docs/public-software-archive-inventory.md", "Arti public archive listings now classified."),
    ("Kooliarvuti Juku article PDF", "historical context", "external link only", "Background article; no board connectivity, PROM byte tables, or bring-up procedure extracted."),
    ("Domestic PC Production in the Soviet Baltic States PDF", "historical context", "external link only", "Background article; useful for production history but not electrical evidence."),
    ("Harno/Tiigrihupe pages and legacy hot.ee link", "historical context", "external link only", "Education-program context; no current board/twin dependency."),
    ("Elfafoorum / ZX-PK topics", "community path", "docs/community-prom-media-request.md", "Potential owner knowledge source; not automatically mined into board truth."),
]


PHOTO_ROWS = [
    (
        "2019 exhibit overview photos",
        "Exterior machine, monitor, floppy units, signage",
        "Tier-3 visual context",
        "Useful for final-system presentation and peripheral checklist; not required for current PCB fabrication.",
    ),
    (
        "2024/2025 exterior photos",
        "Keyboard case, back-panel ports, bottom plate and serial labels",
        "Tier-3 visual context",
        "Useful for enclosure/label/cabling comparison; does not replace connector drawings or continuity checks.",
    ),
    (
        "2019/2025 interior board photos",
        "Top-side board overviews and close-ups of ROM, DRAM, wiring, and Soviet IC population",
        "visual cross-check",
        "Useful to sanity-check placement, sockets, bodge wires, and parts style; resolution/angles are insufficient to close hidden nets or PROM contents.",
    ),
    (
        "Manual-cover photos",
        "E5104 guide covers and document packet photos",
        "manual context",
        "Covered by the manual archive classifier; images are not separately required by the current electrical model.",
    ),
]


def main() -> int:
    lines = [
        "# Arvutimuuseum context inventory",
        "",
        "Status date: 2026-07-09.",
        "",
        "Status: **ARVUTIMUUSEUM CONTEXT CLASSIFIED**",
        "",
        "This generated report records the useful facts from",
        "`https://arvutimuuseum.ee/cs00000/` without promoting museum/exhibit",
        "text to primary electrical evidence. The scanned schematic, Baltijets",
        "factory packet, board JSON, KiCad PCB, and executable twin remain the",
        "authoritative sources for connectivity and firmware behavior.",
        "",
        "## Classified Facts",
        "",
        "| Topic | Page fact | Disposition | Project use |",
        "| --- | --- | --- | --- |",
    ]
    lines.extend(table_row(list(row)) for row in FACT_ROWS)
    lines.extend(
        [
            "",
            "## Linked-Material Disposition",
            "",
            "| Linked material | Disposition | Local evidence | Note |",
            "| --- | --- | --- | --- |",
        ]
    )
    lines.extend(table_row(list(row)) for row in LINK_ROWS)
    lines.extend(
        [
            "",
            "## Gallery Photo Disposition",
            "",
            "| Photo group | Visible material | Disposition | Project use |",
            "| --- | --- | --- | --- |",
        ]
    )
    lines.extend(table_row(list(row)) for row in PHOTO_ROWS)
    lines.extend(
        [
            "",
            "## Boundary",
            "",
            "- Arvutimuuseum is useful for provenance, exhibit context, kit composition,",
            "  photo-based visual cross-checks, and contact/community paths.",
            "- It does not provide the missing `ДГШ5.106.037`, `.039`, or `.092`",
            "  PROM byte tables, FDC continuity measurements, D94 output nets, or",
            "  vendor/order evidence.",
            "- Any future hardware claim still needs to land in the generated board,",
            "  firmware, bring-up, or owner-measurement reports before it counts as",
            "  proof.",
            "",
        ]
    )

    REPORT.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {REPORT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
