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
    ROOT / "docs" / "memory-timing-boundary.md",
    ROOT / "docs" / "io-decode-boundary.md",
    ROOT / "docs" / "video-analog-boundary.md",
    ROOT / "docs" / "s4-interrupt-boundary.md",
    ROOT / "docs" / "unmodeled-footprint-inventory.md",
    ROOT / "docs" / "replica-bringup-verification-points.md",
    ROOT / "docs" / "reconstructed-prom-fallbacks.md",
    ROOT / "docs" / "source-coverage-audit.md",
    ROOT / "docs" / "cartridge-basic-boundary.md",
    ROOT / "docs" / "assembly-drawing-extraction.md",
    ROOT / "docs" / "factory-modification-disposition.md",
]

FDC_SUPPORT_REFS = {"D28", "D95", "D96", "D97", "D98", "D99", "D101", "D102", "D106"}
PIN_CLOSURE_REFS = {"D2", "D3", "D10", "D11", "D35", "D41", "D53", "D59", "D93", "D94", "D100", "S4"} | FDC_SUPPORT_REFS


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
        elif ref in {"D10", "D93", "D100"} | FDC_SUPPORT_REFS:
            evidence = "continuity from an actual `.009` FDC-populated board"
        elif ref == "D11":
            evidence = "sheet-1 continuity plus `docs/serial-handoff.md`"
        elif ref in {"D35", "D41", "D59"}:
            evidence = "sheet-2 timing-chain continuity"
        elif ref == "D3":
            evidence = "sheet-1 serial/interrupt continuity or source-proved NC"
        elif ref == "D53":
            evidence = "sheet-2 memory-timing continuity or source-proved NC"
        elif ref == "S4":
            evidence = "`docs/s4-interrupt-boundary.md` plus sheet-1/SB switch continuity"
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
        ("D2 constraint report generated", "PASS" if marker(ROOT / "docs/d2-reconstruction-constraints.md", "Status: **D2 RECONSTRUCTION CONSTRAINED / DUMP REQUIRED**") or marker(ROOT / "docs/d2-reconstruction-constraints.md", "Status: **D2 RECONSTRUCTION PARTIALLY TRACED / DUMP REQUIRED**") or marker(ROOT / "docs/d2-reconstruction-constraints.md", "Status: **D2 INPUTS TRACED / DUMP REQUIRED**") else "MISSING"),
        ("D94 constraint report generated", has_phrase("docs/d94-reconstruction-constraints.md", "Status: **D94 RECONSTRUCTION CONSTRAINED / DUMP REQUIRED**")),
        ("FDC hardware handoff generated", has_phrase("docs/fdc-hardware-handoff.md", "Status: **BUS-SIDE GUARDED / OWNER CONTINUITY REQUIRED**")),
        ("Beeper source/handoff guarded", has_phrase("docs/beeper-readiness.md", "Status: **DIGITAL BEEPER SOURCE + BOARD HANDOFF READY**")),
        ("Serial USART behavior guarded", has_phrase("docs/serial-handoff.md", "Status: **SERIAL CORE GUARDED / AUXILIARY PIN CONTINUITY PENDING**")),
        ("Decap value boundary guarded", has_phrase("docs/decap-value-fidelity.md", "Status: **DECAP CONNECTIVITY GUARDED / PER-POSITION VALUE PENDING**")),
        ("D41 timing boundary guarded", has_phrase("docs/d41-timing-boundary.md", "Status: **D41 OUTPUTS GUARDED / INPUT TIMING BUS PENDING**")),
        ("Memory timing boundary guarded", has_phrase("docs/memory-timing-boundary.md", "Status: **MEMORY TIMING GUARDED / CAS-MEMCYC SOURCE BOUNDARY PENDING**")),
        ("I/O decode boundary guarded", has_phrase("docs/io-decode-boundary.md", "Status: **IO DECODE GUARDED / SMALL SOURCE BOUNDARIES PENDING**")),
        ("Video/RF analog boundary guarded", has_phrase("docs/video-analog-boundary.md", "Status: **ANALOG VIDEO/RF HANDOFF GUARDED / BENCH MEASUREMENT PENDING**")),
        ("S4 interrupt boundary guarded", has_phrase("docs/s4-interrupt-boundary.md", "Status: **S4 INTERRUPT PATH GUARDED / SWITCH CONTINUITY PENDING**")),
        ("FDC functional-pin design hold is visible", has_phrase("docs/unmodeled-footprint-inventory.md", "Status: **DESIGN HOLD / FDC FUNCTIONAL PINS UNTRACED**")),
        (
            "Bring-up verification points generated",
            "PASS" if any(
                marker(ROOT / "docs/replica-bringup-verification-points.md", status)
                for status in (
                    "Status: **EVIDENCE INDEX READY / RISKS UNRESOLVED**",
                    "Status: **ENDPOINT COVERAGE FAILED**",
                    "Status: **DESIGN RELEASE RISKS CLOSED**",
                )
            ) else "MISSING",
        ),
        ("Source coverage audit current", has_phrase("docs/source-coverage-audit.md", "Status: **PASS**")),
        ("Cartridge BASIC boundary documented", has_phrase("docs/cartridge-basic-boundary.md", "Status: **ARTIFACT OR DOCUMENTED PROCEDURE REQUIRED**")),
        (".009 assembly drawing extraction guarded", has_phrase("docs/assembly-drawing-extraction.md", "Status: **SHEETS 1-6 ADOPTED / WIRE-TABLE PIN MAPPING PENDING**")),
        ("Factory Вид В modifications guarded", has_phrase("docs/factory-modification-disposition.md", "Status: **FACTORY MODIFICATIONS GUARDED / PAD MAPPING REQUIRED**")),
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
            "P2",
            "JUKU-1 media provenance",
            "independent `JUKU-1` / `ДГШ5.106.105` disk image or checksum/provenance for `media/disks/JUKU1.CPM`",
            "`docs/community-prom-media-request.md`; `docs/ekdos-media-acquisition.md`",
            "turns the public EKDOS boot image into stronger physical-media evidence",
        ),
        (
            "P2",
            "cartridge BASIC truth",
            "larger/different removable-memory BASIC cartridge image, programming artifact, or hardware-confirmed Monitor 3.3 launch procedure to BASIC `READY`",
            "`docs/community-prom-media-request.md`; `docs/cartridge-basic-boundary.md`",
            "closes the remaining Monitor 3.3 cartridge BASIC compatibility boundary",
        ),
        (
            "P0",
            "D94 .092 continuity",
            "D94 pin 15 enable, pins 4-7/9 destinations, and every branch from D93.2/D93.4 beyond the visible D94.3/D94.1 segments on a .009 processor board",
            "`docs/d94-reconstruction-constraints.md`",
            "required to resolve the PROM-only read/write-strobe impossibility before any defensible D94 replacement",
        ),
        (
            "P1",
            "FDC interrupt/buffer continuity",
            "WD1793 DRQ/INTRQ to 8259 inputs, D93 MR/CLK, plus D100 OE/T if accessible",
            "`docs/fdc-hardware-handoff.md`; `docs/replica-bringup-verification-points.md`; `PLAN.md` P0/P1 gates",
            "reduces first EKDOS-on-hardware debug risk",
        ),
        (
            "P0",
            "memory-decode stragglers",
            "D6 V1/V2 feed, C99 far plate, D7/D25_T source inputs, D36/D39/D53 RAM-strobe ambiguous feeds, and D41 timing-bus input/control pins",
            "`docs/io-decode-boundary.md`; `docs/memory-timing-boundary.md`; `docs/d41-timing-boundary.md`; `docs/replica-bringup-verification-points.md`; `PLAN.md` P0 connectivity gate",
            "tightens the as-built netlist around RAM/video timing before netlist freeze",
        ),
        (
            "P1",
            "wire-18 220-ohm local branch",
            "A:17/A:18 and both S1 endpoints are now photo/document proved; identify only the separately reported 220-ohm branch near D98.7 and state whether it is part of D98_Y3_S1_2 or another local FDC net",
            "`ref/schematics/dgsh5-109-009-sb-wire-table.md` rows 11/12; `docs/assembly-drawing-extraction.md`; `ref/photos/juku-pcb-2/BODGE-TRIAGE.md`",
            "prevents an unproved resistor from being folded into the now-closed S1 harness nets",
        ),
        (
            "P0",
            "factory Вид В pad mapping",
            "for D56, D15, D14, and D11 identify every position-150/159 cut pad/via, removed copper segment, and replacement connection; at D15 identify the auxiliary vertical segment cut between its second/third shown vias (roughly pad levels 8/9); at D14 identify the position-159 auxiliary hole, three long replacement traces, and right-row dogleg; at D11 use the validated solder fit that localizes rework beside pins 4-6 to map the four-hole auxiliary field and obscured bridge; the acquired sheets 2-5 wire table covers wires/cables only, so use registered solder-side imagery plus continuity",
            "`docs/factory-modification-disposition.md`; `ref/photos/dgsh5-109-009-sb/PXL_20260711_114626340.jpg`",
            "proves that the clean source-PCB topology is electrically equivalent to the factory-modified artwork before reroute/release",
        ),
        (
            "P0",
            "FDC support signal dispositions",
            "pin-level continuity or an explicit redesign/DNP decision for D28, D95-D99, D101, D102, and D106; prioritize the FDC cluster",
            "`docs/unmodeled-footprint-inventory.md`; `PLAN.md` P0 connectivity gate; `.009` assembly evidence",
            "closes the functional signals on the 9 now-pin-modeled, power-routed FDC support devices",
        ),
        (
            "P0",
            "D2/D105 wait-chain revision handoff",
            "reconcile the older-sheet D95 inverter after D105.6 with the `.009` D95 FDC-multiplexer assignment and obtain the `.037` truth table; all D2 inputs are now traced",
            "`docs/unmodeled-footprint-inventory.md`; `ref/schematics/p3_sheet1.png`; `ref/photos/juku-pcb-2/BODGE-TRIAGE.md`",
            "closes the remaining target-revision WAIT handoff without undoing the now-modeled and routed D105 gates",
        ),
        (
            "P2",
            "analog/video/sound/serial bring-up captures",
            "composite/RF/sync/audio nodes plus X3 serial loopback while running the staged bring-up ladder",
            "`docs/video-analog-boundary.md`; `docs/replica-bringup-verification-points.md`; `docs/beeper-readiness.md`; `docs/video-readout-readiness.md`; `docs/serial-handoff.md`",
            "bench evidence only; does not block PCB fabrication",
        ),
        (
            "P2",
            "photos and passive values",
            "macro photos for the FDC/top-center quadrant, C35-C72 bypass-cap values by refdes/position, sound/video analog corner passives",
            "`docs/decap-value-fidelity.md`; `PLAN.md`; generated BOM/sourcing docs",
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
