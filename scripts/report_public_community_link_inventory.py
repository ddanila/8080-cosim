#!/usr/bin/env python3
"""Generate a classified inventory of public community Juku links."""
from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "docs" / "public-community-link-inventory.md"


def table_row(values: list[object]) -> str:
    return "| " + " | ".join(str(value).replace("|", "/") for value in values) + " |"


THREAD_ROWS = [
    (
        "Elfafoorum `Arvuti \"Juku\"` thread",
        "https://www.elfafoorum.eu/forum/tehnikafoorumid/tark-ja-riistvara-foorum/64851-",
        "owner/contact path",
        "Identifies a Juku E5101 owner and a long-running public discussion seeking manuals, games, programs, and hardware knowledge.",
        "Useful as a contact route for the ready PROM/media request; no extracted post supplies PROM byte tables, pin continuity, or board nets.",
    ),
    (
        "ZX-PK `Juku E5101` page 2",
        "https://zx-pk.ru/threads/27298-juku-e5101/page2.html",
        "historical/community context",
        "Discusses scarce software, CP/M disk needs, E5101/E5104/E6502/E4701/E6201 naming, ROM population variants, and uncertainty about FDC placement.",
        "Matches already-known reference-base questions; superseded for board truth by Baltijets docs, board photos, and current FDC-revision PCB evidence.",
    ),
    (
        "Elfafoorum member profiles",
        "https://www.elfafoorum.eu/member/5098-dieter; https://www.elfafoorum.eu/member/6430-pehka1985",
        "blocked profile pages",
        "Profile pages are access-controlled from this environment.",
        "Do not treat as evidence; use public thread links or GitHub/community contacts instead.",
    ),
    (
        "Arvutimuuseum contact path",
        "https://arvutimuuseum.ee/kontakt/",
        "institution contact path",
        "Museum page records a working Juku artifact and public exhibit context.",
        "Useful for asking about disk/PROM/media provenance; not a continuity or dump record by itself.",
    ),
]


KEYWORD_ROWS = [
    (
        "PROM/programming tables",
        "No public thread snippet found a `ДГШ5.106.037`, `.039`, or `.092` byte table.",
        "PROM truth still needs Baltijets programming-disk files or physical dumps.",
    ),
    (
        "FDC placement/history",
        "ZX-PK discussion speculates about whether the ВГ93 controller was in the drive unit or a board variant.",
        "Current repo evidence uses the .009 processor-board FDC revision, Baltijets docs, owner photos, board JSON, and routed PCB; speculation is not promoted.",
    ),
    (
        "Disk/software provenance",
        "Threads discuss missing CP/M/Juku software and requests for disk images.",
        "Useful context, but vendored Arti/museum disk images and guarded EKDOS/JBASIC probes are the current executable evidence.",
    ),
    (
        "Owner measurements",
        "No new pin-level continuity or PROM dump evidence was extracted from the public snippets.",
        "`docs/owner-measurement-shortlist.md` remains the actionable measurement/dump ask.",
    ),
]


def main() -> int:
    lines = [
        "# Public community link inventory",
        "",
        "Status date: 2026-07-09.",
        "",
        "Status: **PUBLIC COMMUNITY LINKS CLASSIFIED**",
        "",
        "This generated report classifies the public community/forum links",
        "referenced from the Juku public-source trail. It intentionally records",
        "only disposition-level facts: forum posts are useful for contacts and",
        "historical context, but board/PROM claims still require primary",
        "artifacts, dumps, photos, or measured continuity before they can enter",
        "the electrical model.",
        "",
        "## Link Disposition",
        "",
        "| Link | URL | Disposition | Observed content | Project use |",
        "| --- | --- | --- | --- | --- |",
    ]
    lines.extend(table_row(list(row)) for row in THREAD_ROWS)
    lines.extend(
        [
            "",
            "## Keyword Triage",
            "",
            "| Topic | Public-thread finding | Project disposition |",
            "| --- | --- | --- |",
        ]
    )
    lines.extend(table_row(list(row)) for row in KEYWORD_ROWS)
    lines.extend(
        [
            "",
            "## Boundary",
            "",
            "- The useful automatic result is classification, not importing forum",
            "  HTML or treating recollections as schematics.",
            "- Community links should now be used to send the exact request in",
            "  `docs/community-prom-media-request.md`.",
            "- Any reply with files, checksums, photos, continuity measurements, or",
            "  PROM dumps must be promoted into a specific generated inspection",
            "  report before it changes the board or firmware model.",
            "",
        ]
    )

    REPORT.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {REPORT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
