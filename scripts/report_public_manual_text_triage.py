#!/usr/bin/env python3
"""Generate targeted text triage for large public Juku manuals."""
from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "docs" / "public-manual-text-triage.md"


def table_row(values: list[object]) -> str:
    return "| " + " | ".join(str(value).replace("|", "/") for value in values) + " |"


PDF_ROWS = [
    (
        "juku_e5104_rus_1.pdf",
        "https://elektroonikamuuseum.ee/failid/juku/kirjandus/juku_e5104_rus_1.pdf",
        "6,569,347",
        "244,642",
        "Russian operating/installation manual text; mentions ROMBIOS, ROM self-test indication, FDD unit setup, BASIC, and ROM/EPROM context.",
        "No `ДГШ5.106.037`, `.039`, `.092`, `К556РТ4`, `К155РЕ3`, or PLM table hit.",
    ),
    (
        "juku_e5104_rus_2.pdf",
        "https://elektroonikamuuseum.ee/failid/juku/kirjandus/juku_e5104_rus_2.pdf",
        "2,455,931",
        "82,725",
        "Russian passport/specification text; names the accessory disk set `ДГШ5.106.105`, `-01`, `-02`, E6502 FDD unit, ROM capacity, and BASIC cartridge memory context.",
        "Useful media-provenance cross-check only; no PROM byte table or pin/net evidence.",
    ),
    (
        "juku_e5104_rus_3.pdf",
        "https://elektroonikamuuseum.ee/failid/juku/kirjandus/juku_e5104_rus_3.pdf",
        "48,766,062",
        "2,148,316",
        "Large Russian software/programmer packet; mentions ROMBIOS, EKDOS/NETOS/diagnostics, FDD/no-FDD station starts, ROM carrier context, and BASIC/software procedures.",
        "No exact small-PROM programmed drawing or dump evidence found in text extraction.",
    ),
    (
        "Mikroarvuti_JUKU_kasutamisjuhend_1988.pdf",
        "https://elektroonikamuuseum.ee/failid/juku/kirjandus/Mikroarvuti_JUKU_kasutamisjuhend_1988.pdf",
        "17,572,476",
        "290,290",
        "Estonian user manual text; mostly LOS/BASIC/user operation context.",
        "No board/PROM/FDC electrical source evidence found in targeted keyword triage.",
    ),
    (
        "juku_e5104_rus_sisukord.txt",
        "https://elektroonikamuuseum.ee/failid/juku/kirjandus/juku_e5104_rus_sisukord.txt",
        "1,668",
        "1,659",
        "Table-of-contents text; confirms ROMBIOS, EKDOS 2.29, NETOS, diagnostics, utility, BASIC, DBMS, Pascal, and assembler/software sections.",
        "TOC only; no board/PROM payload.",
    ),
]


KEYWORD_ROWS = [
    ("`ДГШ5.106.037` / `.038` / `.039` / `.092`", "no relevant hits", "Missing small-PROM tables remain external."),
    ("`К556РТ4`, `КР556`, `К155РЕ3`, `КР155`, `ПЛМ`", "no useful hits", "No RT4/RE3/PLM programming data was found in the manual text extraction."),
    ("`ДГШ5.106.105`", "one passport/spec hit", "Confirms the `JUKU-1`/disk-label family already tracked in PLAN and media docs."),
    ("`ВГ93`, `1772`, `1793`", "no controller implementation payload", "Does not improve the WD1793/VG93 HDL model or D93/D100 continuity evidence."),
    ("`ROMBIOS`, `ПЗУ`, `БЕЙСИК`, `BASIC`, `НГМД`", "many operating-context hits", "Useful for user/service procedures, but not primary electrical or firmware truth."),
]


def main() -> int:
    lines = [
        "# Public manual text triage",
        "",
        "Status date: 2026-07-09.",
        "",
        "Status: **PUBLIC MANUAL TEXT TRIAGED**",
        "",
        "This generated report records a targeted text pass over the large",
        "public Juku manuals from the Elektroonikamuuseum `kirjandus/` listing.",
        "The pass used `pdftotext -layout` outside the repository and searched",
        "for the current board-critical terms: small-PROM drawing numbers,",
        "RT4/RE3/PLM names, FDC controller names, ROMBIOS, disk labels, BASIC,",
        "and FDD terminology.",
        "",
        "It does not vendor the large PDFs because they are optional procedure",
        "and historical context, not required build inputs. If a future task",
        "needs a specific procedure page, promote that exact source artifact",
        "with checksum and a focused inspection report.",
        "",
        "## Source Files",
        "",
        "| File | URL | PDF bytes | Extracted text chars | Useful hits | Board/PROM result |",
        "| --- | --- | ---: | ---: | --- | --- |",
    ]
    lines.extend(table_row(list(row)) for row in PDF_ROWS)
    lines.extend(
        [
            "",
            "## Keyword Outcome",
            "",
            "| Search target | Result | Disposition |",
            "| --- | --- | --- |",
        ]
    )
    lines.extend(table_row(list(row)) for row in KEYWORD_ROWS)
    lines.extend(
        [
            "",
            "## Boundary",
            "",
            "- The manuals improve operating/service context, especially ROMBIOS,",
            "  EKDOS/NETOS/diagnostics/BASIC, FDD/no-FDD workflows, and the",
            "  `ДГШ5.106.105` disk-kit reference.",
            "- They do not close D2/D6/D8/D94 PROM truth, D94 output nets, FDC",
            "  continuity, or any routed PCB source-risk net.",
            "- The next automatic source task is not more manual scanning; it is",
            "  acting on new external evidence if a programming disk, dump, photo,",
            "  or continuity measurement appears.",
            "",
        ]
    )
    REPORT.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {REPORT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
