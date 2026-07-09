#!/usr/bin/env python3
"""Generate the short physical-owner measurement/dump list."""
from __future__ import annotations

import json
from collections import Counter
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "docs" / "owner-measurement-shortlist.md"
BOARD_JSON = ROOT / "kicad" / "juku.board.json"

REQUIRED = [
    BOARD_JSON,
    ROOT / "docs" / "community-prom-media-request.md",
    ROOT / "docs" / "prom-dump-procedure.md",
    ROOT / "docs" / "d2-reconstruction-constraints.md",
    ROOT / "docs" / "d94-reconstruction-constraints.md",
    ROOT / "docs" / "fdc-hardware-handoff.md",
    ROOT / "docs" / "beeper-readiness.md",
    ROOT / "docs" / "serial-handoff.md",
    ROOT / "docs" / "decap-value-fidelity.md",
    ROOT / "docs" / "d41-timing-boundary.md",
    ROOT / "docs" / "replica-bringup-verification-points.md",
    ROOT / "docs" / "reconstructed-prom-fallbacks.md",
    ROOT / "docs" / "source-coverage-audit.md",
    ROOT / "docs" / "basic-cartridge-tail-hypotheses.md",
]

PIN_CLOSURE_REFS = {"D2", "D41", "D93", "D94", "D100", "S4"}


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def marker(path: Path, text: str) -> bool:
    return path.exists() and text in read(path)


def table_rows(text: str) -> list[list[str]]:
    rows: list[list[str]] = []
    for line in text.splitlines():
        line = line.strip()
        if not line.startswith("|") or "---" in line:
            continue
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if cells:
            rows.append(cells)
    return rows


def bringup_categories() -> Counter[str]:
    text = read(ROOT / "docs" / "replica-bringup-verification-points.md")
    counts: Counter[str] = Counter()
    in_checklist = False
    for row in table_rows(text):
        if row[:2] == ["Net", "Category"]:
            in_checklist = True
            continue
        if not in_checklist or len(row) < 5:
            continue
        counts[row[1]] += 1
    return counts


def failed_d94_checks() -> list[str]:
    text = read(ROOT / "docs" / "d94-reconstruction-constraints.md")
    failures: list[str] = []
    for row in table_rows(text):
        if len(row) >= 3 and row[1] == "FAIL":
            failures.append(row[0])
    return failures


def inline(text: str) -> str:
    return text.replace("`", "")


def has_phrase(path: str, phrase: str) -> str:
    return "PASS" if marker(ROOT / path, phrase) else "MISSING"


def pin_sort_key(item: tuple[str, object]) -> object:
    pin = str(item[0])
    return int(pin) if pin.isdigit() else pin


def unnetted_pin_closure_rows() -> list[tuple[str, str, str]]:
    board = json.loads(BOARD_JSON.read_text(encoding="utf-8"))
    netted: dict[str, set[str]] = defaultdict(set)
    for net in board["nets"].values():
        for ref, pin in net.get("nodes", []):
            netted[str(ref)].add(str(pin))

    rows = []
    for chip in board["chips"]:
        ref = str(chip.get("ref", ""))
        if ref not in PIN_CLOSURE_REFS:
            continue
        missing = [
            f"{pin}:{signal}"
            for pin, signal in sorted(chip.get("pins", {}).items(), key=pin_sort_key)
            if str(pin) not in netted.get(ref, set())
        ]
        if not missing:
            continue
        if ref == "D2":
            evidence = "dump/programming disk plus sheet-1 continuity"
        elif ref == "D94":
            evidence = ".092 dump/table plus enable/output continuity"
        elif ref in {"D93", "D100"}:
            evidence = "FDC quadrant continuity"
        elif ref == "D41":
            evidence = "sheet-2 timing-chain continuity"
        else:
            evidence = "sheet-1/SB switch continuity"
        rows.append((ref, ", ".join(missing), evidence))
    return sorted(rows)


def main() -> int:
    missing = [path for path in REQUIRED if not path.exists()]
    d94_failures = failed_d94_checks() if not missing else []
    categories = bringup_categories() if not missing else Counter()
    pin_closure_rows = unnetted_pin_closure_rows() if not missing else []

    checks = [
        ("Community request packet ready", has_phrase("docs/community-prom-media-request.md", "Status: **READY TO SEND**")),
        ("PROM dump procedure exists", has_phrase("docs/prom-dump-procedure.md", "Bipolar PROMs")),
        ("D6/D8 reconstructed fallback exported", has_phrase("docs/reconstructed-prom-fallbacks.md", "d6_rt4_memory_decode_reconstructed")),
        ("D2 constraint report generated", has_phrase("docs/d2-reconstruction-constraints.md", "Status: **D2 RECONSTRUCTION CONSTRAINED / DUMP REQUIRED**")),
        ("D94 constraint report generated", has_phrase("docs/d94-reconstruction-constraints.md", "Status: **D94 RECONSTRUCTION CONSTRAINED / DUMP REQUIRED**")),
        ("FDC hardware handoff generated", has_phrase("docs/fdc-hardware-handoff.md", "Status: **BUS-SIDE GUARDED / OWNER CONTINUITY REQUIRED**")),
        ("Beeper source/handoff guarded", has_phrase("docs/beeper-readiness.md", "Status: **DIGITAL BEEPER SOURCE + BOARD HANDOFF READY**")),
        ("Serial USART behavior guarded", has_phrase("docs/serial-handoff.md", "Status: **SERIAL USART BEHAVIOR GUARDED / EXTERNAL LOOPBACK PENDING**")),
        ("Decap value boundary guarded", has_phrase("docs/decap-value-fidelity.md", "Status: **DECAP CONNECTIVITY GUARDED / PER-POSITION VALUE PENDING**")),
        ("D41 timing boundary guarded", has_phrase("docs/d41-timing-boundary.md", "Status: **D41 OUTPUTS GUARDED / INPUT TIMING BUS PENDING**")),
        ("Bring-up verification points generated", has_phrase("docs/replica-bringup-verification-points.md", "Status: **READY**")),
        ("Source coverage audit current", has_phrase("docs/source-coverage-audit.md", "Status: **PASS**")),
        ("Cartridge BASIC boundary documented", has_phrase("docs/basic-cartridge-tail-hypotheses.md", "Status: **SIMPLE TAIL HYPOTHESES REJECTED**")),
    ]
    failed_checks = [name for name, state in checks if state != "PASS"]

    priority_rows = [
        (
            "P0",
            "programming disk / PROM truth",
            "Baltijets doc 007 disk files, or dumps of D2/D6 RT4, D8 RE3, D94 RE3, D15/D16 EPROMs",
            "`docs/community-prom-media-request.md`; `docs/prom-dump-procedure.md`; `docs/d2-reconstruction-constraints.md`",
            "unblocks preservation-grade PROM truth and validates/replaces reconstructed D6/D8 fallbacks",
        ),
        (
            "P0",
            "JUKU-1 media provenance",
            "independent `JUKU-1` / `ДГШ5.106.105` disk image or checksum/provenance for `media/disks/JUKU1.CPM`",
            "`docs/community-prom-media-request.md`; `docs/ekdos-media-acquisition.md`",
            "turns the public EKDOS boot image into stronger physical-media evidence",
        ),
        (
            "P0",
            "cartridge BASIC truth",
            "larger/different removable-memory BASIC cartridge image, programming artifact, or hardware-confirmed Monitor 3.3 launch procedure to BASIC `READY`",
            "`docs/community-prom-media-request.md`; `docs/basic-launch-probe.md`; `docs/basic-cartridge-tail-hypotheses.md`",
            "closes the remaining Monitor 3.3 cartridge BASIC compatibility boundary",
        ),
        (
            "P1",
            "D94 .092 continuity",
            "D94 pin 15 enable and pins 1-7/9 output destinations on a .009 processor board",
            "`docs/d94-reconstruction-constraints.md`",
            "required before any defensible D94 reverse-engineered burnable table",
        ),
        (
            "P1",
            "FDC interrupt/buffer continuity",
            "WD1793 DRQ/INTRQ to 8259 inputs, D93 MR/CLK, plus D100 OE/T if accessible",
            "`docs/fdc-hardware-handoff.md`; `docs/replica-bringup-verification-points.md`; `PLAN.md` WS-F",
            "reduces first EKDOS-on-hardware debug risk",
        ),
        (
            "P1",
            "memory-decode stragglers",
            "D6 V1/V2 feed, C99 far plate, D36/D39/D53 RAM-strobe ambiguous feeds, and D41 timing-bus input/control pins",
            "`docs/d41-timing-boundary.md`; `docs/replica-bringup-verification-points.md`; `PLAN.md` WS-A/WS-F",
            "tightens the as-built netlist around RAM/video timing before netlist freeze",
        ),
        (
            "P2",
            "analog/video/sound/serial bring-up captures",
            "composite/RF/sync/audio nodes plus X3 serial loopback while running the staged bring-up ladder",
            "`docs/replica-bringup-verification-points.md`; `docs/beeper-readiness.md`; `docs/video-readout-readiness.md`; `docs/serial-handoff.md`",
            "bench evidence only; does not block PCB fabrication",
        ),
        (
            "P2",
            "photos and passive values",
            "macro photos for the FDC/top-center quadrant, C35-C72 bypass-cap values by refdes/position, sound/video analog corner passives",
            "`docs/decap-value-fidelity.md`; `PLAN.md` WS-F; generated BOM/sourcing docs",
            "improves authenticity and reduces assembly substitutions",
        ),
    ]

    lines = [
        "# Owner measurement shortlist",
        "",
        "Status: **READY**" if not missing and not failed_checks else "Status: **SOURCE REPORTS MISSING**",
        "",
        "This generated report compresses the remaining physical-owner asks into",
        "the shortest useful list. It is not a bench log and does not claim any",
        "measurement has been performed; it records what still cannot be derived",
        "automatically from the current repo evidence.",
        "",
        "## Command",
        "",
        "```sh",
        "python3 scripts/report_owner_measurement_shortlist.py",
        "```",
        "",
        "## Evidence freshness",
        "",
        "| Check | Status |",
        "| --- | --- |",
    ]
    lines.extend(f"| {name} | {state} |" for name, state in checks)
    if missing:
        lines.extend(["", "Missing required inputs:", ""])
        lines.extend(f"- `{path.relative_to(ROOT)}`" for path in missing)

    lines.extend(
        [
            "",
            "## Highest-value physical asks",
            "",
            "| Priority | Ask | Exact deliverable | Evidence source | Why it matters |",
            "| --- | --- | --- | --- | --- |",
        ]
    )
    lines.extend(f"| {priority} | {ask} | {deliverable} | {source} | {why} |" for priority, ask, deliverable, source, why in priority_rows)

    lines.extend(
        [
            "",
            "## Current D94 blockers",
            "",
            f"- D94 failed evidence checks: `{', '.join(inline(item) for item in d94_failures) if d94_failures else 'none'}`",
            "- D94 address pins are already traced to `BA11..BA15`; the useful physical",
            "  work is enable/output continuity plus a real `.092` dump/table.",
            "",
            "## Pin-Level Closure",
            "",
            "These rows mirror the unnetted functional pins exposed by",
            "`docs/board-fidelity-gap-ledger.md`. They are the exact pin-level",
            "closures that endpoint coverage cannot prove because the pins are not",
            "yet modeled as nets.",
            "",
            "| Ref | Unnetted functional pins | Needed evidence |",
            "| --- | --- | --- |",
        ]
    )
    lines.extend(f"| `{ref}` | `{pins}` | {evidence} |" for ref, pins, evidence in pin_closure_rows)

    lines.extend(
        [
            "",
            "## Bring-up verification scope",
            "",
            f"- Generated bring-up verification nets: `{sum(categories.values())}`",
        ]
    )
    lines.extend(f"- `{category}`: `{count}` net(s)" for category, count in sorted(categories.items()))
    lines.extend(
        [
            "",
            "## Practical sequencing",
            "",
            "1. Ask for programming disk files and BASIC cartridge artifacts first;",
            "   they can close PROM/software truth without touching fragile sockets.",
            "2. If a board owner can help, dump socketed PROM/EPROM parts before",
            "   continuity probing; repeated reads plus socket photos are enough to",
            "   compare against the reconstructed fallbacks.",
            "3. Use continuity only for the P1 nets above; broad bring-up checklist",
            "   probes are deferred until a replica or owner board is already on the",
            "   bench.",
        ]
    )

    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {REPORT.relative_to(ROOT)}")
    if missing:
        return 1
    if failed_checks:
        print("Missing evidence markers: " + ", ".join(failed_checks))
        return 1
    if "Enable pin D94.15 is traced" not in d94_failures:
        print("Unexpected D94 status: enable is no longer a blocker; review shortlist")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
