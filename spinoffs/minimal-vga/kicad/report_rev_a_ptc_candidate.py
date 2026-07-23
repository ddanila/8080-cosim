#!/usr/bin/env python3
"""Guard the exact Bourns MF-RG300-0-14 candidate used by Rev-A F1."""
from __future__ import annotations

import csv
import hashlib
import json
import math
import re
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
DATASHEET = ROOT / "ref" / "datasheets" / "bourns-mf-rg.pdf"
REFERENCE = ROOT / "ref" / "datasheets" / "bourns-mf-rg300-footprint.txt"
BOARD_JSON = ROOT / "spinoffs" / "minimal-vga" / "kicad" / "rev-a-physical.board.json"
PCB = ROOT / "spinoffs" / "minimal-vga" / "kicad" / "rev-a-physical.kicad_pcb"
BOM = ROOT / "spinoffs" / "minimal-vga" / "kicad" / "rev-a.bom.csv"
CPN = ROOT / "spinoffs" / "minimal-vga" / "kicad" / "rev-a-jlcpcb-cpn-checklist.csv"
POWER_DOC = ROOT / "spinoffs" / "minimal-vga" / "docs" / "rev-a-power-budget.md"
DEFAULT_REPORT = ROOT / "spinoffs" / "minimal-vga" / "docs" / "rev-a-ptc-candidate.md"

DATASHEET_SHA256 = "7c6cc82e2566fe7ba904d3783122320fa87f043bf7a720467cdfb637c7e803ef"
MPN = "MF-RG300-0-14"
CPN_ID = "C3761779"
FOOTPRINT_NAME = "Fuse_Bourns_MF-RG300"
PLANNING_LOAD_A = 1.81


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def forms(text: str, marker: str) -> list[str]:
    result: list[str] = []
    offset = 0
    while (found := text.find(marker, offset)) >= 0:
        start = found + marker.index("(")
        depth = 0
        quoted = escaped = False
        for index in range(start, len(text)):
            char = text[index]
            if quoted:
                if escaped:
                    escaped = False
                elif char == "\\":
                    escaped = True
                elif char == '"':
                    quoted = False
            elif char == '"':
                quoted = True
            elif char == "(":
                depth += 1
            elif char == ")":
                depth -= 1
                if depth == 0:
                    result.append(text[start : index + 1])
                    offset = index + 1
                    break
        else:
            raise ValueError(f"unterminated form for marker {marker!r}")
    return result


def footprint_block(text: str, ref: str) -> str:
    for block in forms(text, "\n\t(footprint "):
        match = re.search(r'\(property "Reference" "([^"]+)"', block)
        if match and match.group(1) == ref:
            return block
    raise ValueError(f"footprint {ref} not found")


def pair(block: str, name: str) -> tuple[float, float]:
    match = re.search(
        rf"\({name}\s+(-?\d+(?:\.\d+)?)\s+(-?\d+(?:\.\d+)?)", block
    )
    if not match:
        raise ValueError(f"{name} pair missing")
    return float(match.group(1)), float(match.group(2))


def parse_pads(block: str) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for pad in forms("\n\t" + block, "\n\t\t(pad "):
        number = re.match(r'\(pad "([^"]+)"', pad)
        net = re.search(r'\(net(?:\s+\d+)?\s+"([^"]+)"\)', pad)
        drill = re.search(r"\(drill\s+(-?\d+(?:\.\d+)?)", pad)
        if not number:
            raise ValueError("unnumbered pad in F1 footprint")
        result[number.group(1)] = {
            "at": pair(pad, "at"),
            "size": pair(pad, "size"),
            "drill": float(drill.group(1)) if drill else 0.0,
            "net": net.group(1) if net else "",
        }
    return result


def csv_row(path: Path, value: str, field: str) -> dict[str, str]:
    with path.open(newline="", encoding="utf-8") as handle:
        return next(row for row in csv.DictReader(handle) if row.get(field) == value)


def add(
    checks: list[tuple[str, bool, str]], name: str, passed: bool, evidence: str
) -> None:
    checks.append((name, passed, evidence))


def build() -> tuple[list[tuple[str, bool, str]], list[str]]:
    checks: list[tuple[str, bool, str]] = []
    reference = REFERENCE.read_text(encoding="utf-8")
    power_doc = POWER_DOC.read_text(encoding="utf-8")
    board = json.loads(BOARD_JSON.read_text(encoding="utf-8"))
    block = footprint_block(PCB.read_text(encoding="utf-8"), "F1")

    required = (
        "Part number: MF-RG300-0-14",
        "Maximum voltage: 16 V",
        "Hold current: 3.0 A",
        "Trip current: 5.1 A",
        "Lead span C: 5.1 mm nominal, plus or minus 0.7 mm",
        "Lead diameter F: 0.81 mm nominal",
        "-14 = kinked leads where straight leads are standard",
    )
    add(
        checks,
        "Manufacturer datasheet and interpretation are pinned",
        sha256(DATASHEET) == DATASHEET_SHA256
        and all(marker in reference for marker in required),
        f"Bourns MF-RG datasheet SHA-256 {DATASHEET_SHA256}",
    )

    chip = next(item for item in board["chips"] if item.get("ref") == "F1")
    add(
        checks,
        "Board model preserves raw-to-fused power topology",
        chip.get("type") == "FUSE_THT"
        and chip.get("pins") == {"1": "VCC_RAW", "2": "VCC"},
        "F1.1=VCC_RAW and F1.2=VCC",
    )

    name = re.match(r'\(footprint "([^"]+)"', block)
    pads = parse_pads(block)
    expected_pads = {
        "1": {"at": (0.0, 0.0), "size": (2.01, 2.01), "drill": 1.01, "net": "VCC_RAW"},
        "2": {"at": (5.1, 1.2), "size": (2.01, 2.01), "drill": 1.01, "net": "VCC"},
    }
    add(
        checks,
        "Committed PCB embeds the guarded Bourns footprint and pad contract",
        bool(name and name.group(1) == FOOTPRINT_NAME) and pads == expected_pads,
        "Fuse_Bourns_MF-RG300; pads 1/2 are VCC_RAW/VCC with 1.01 mm drills",
    )

    separation = math.dist(pads["1"]["at"], pads["2"]["at"])
    horizontal_span = abs(pads["1"]["at"][0] - pads["2"]["at"][0])
    stagger = abs(pads["1"]["at"][1] - pads["2"]["at"][1])
    add(
        checks,
        "Nominal lead span and drill match the kinked radial part",
        abs(horizontal_span - 5.1) <= 0.001 and pads["1"]["drill"] >= 0.81,
        f"{horizontal_span:.3f} mm span matches C; {stagger:.3f} mm undimensioned stagger; 1.01 mm drill for 0.81 mm lead",
    )

    fab = next(
        item
        for item in forms("\n\t" + block, "\n\t\t(fp_rect")
        if '(layer "F.Fab")' in item
    )
    start, end = pair(fab, "start"), pair(fab, "end")
    fab_size = (abs(end[0] - start[0]), abs(end[1] - start[1]))
    add(
        checks,
        "Fabrication outline carries the maximum body width and depth",
        all(abs(actual - expected) < 0.001 for actual, expected in zip(fab_size, (7.1, 3.0))),
        "F.Fab is 7.1 x 3.0 mm, matching data-sheet A max and E max",
    )

    bom = csv_row(BOM, "F1", "Designator")
    cpn = csv_row(CPN, "Fuse", "Group")
    add(
        checks,
        "Engineering BOM and assembly checklist name the exact orderable part",
        MPN in bom.get("Candidate MPN", "")
        and bom.get("JLCPCB/LCSC CPN") == CPN_ID
        and cpn.get("Preferred CPN") == CPN_ID
        and MPN in cpn.get("Notes", ""),
        f"F1 = Bourns {MPN} / {CPN_ID} in both ordering artifacts",
    )

    power_markers = (
        "**1.81 A**",
        "3.0 A at 23 C",
        "5.1 A at 23 C",
        "16 V",
        "2.6 A at 40 C",
        "2.1 A at 60 C",
        "gross short / wiring fault protection",
    )
    add(
        checks,
        "Electrical and thermal planning facts are explicit",
        all(marker in power_doc for marker in power_markers),
        "16 V; 3.0 A hold and 5.1 A trip at 23 C; 2.6 A at 40 C; 2.1 A at 60 C",
    )
    add(
        checks,
        "Room-temperature hold current exceeds the planning load",
        3.0 / PLANNING_LOAD_A >= 1.5,
        f"3.0 A / {PLANNING_LOAD_A:.2f} A = {3.0 / PLANNING_LOAD_A:.2f}x at 23 C",
    )

    holds = [
        "The pad-2 stagger is a stock KiCad fit accommodation, not a manufacturer-dimensioned coordinate. Verify insertion, body seating, and solder fillets on the first assembled article.",
        "The 3.0 A rating is specified at 23 C. Confirm actual enclosure/board ambient and load margin; the data-sheet hold current falls to 2.6 A at 40 C and 2.1 A at 60 C.",
        "Recheck C3761779 live stock, assembly availability, and the current manufacturer datasheet immediately before ordering.",
        "Review source capability, J1/J3 and trace current/temperature rise, and nearby-part clearance. F1 is gross-fault protection, not a precise current limiter.",
        "This closes the exact F1 variant contract only. The Rev-A TVS and socketed-part pin-1 reviews remain separate.",
    ]
    return checks, holds


def write_report(
    path: Path, checks: list[tuple[str, bool, str]], holds: list[str]
) -> None:
    failures = [name for name, passed, _ in checks if not passed]
    status = (
        "EXACT F1 CANDIDATE GUARDED / THERMAL AND FIRST-ARTICLE CHECK OPEN"
        if not failures
        else "FAILED"
    )
    lines = [
        "# Rev A PTC candidate readiness",
        "",
        "Status date: **2026-07-23**.",
        "",
        f"Status: **{status}**.",
        "",
        "This report guards Bourns MF-RG300-0-14 as the exact Rev-A F1",
        "candidate. It checks the preserved manufacturer datasheet, board",
        "topology, committed KiCad fit geometry, electrical planning facts, and",
        "ordering identifiers. It is not a thermal qualification, live-stock",
        "claim, or fabrication authorization.",
        "",
        "## Command",
        "",
        "```sh",
        "python3 spinoffs/minimal-vga/kicad/report_rev_a_ptc_candidate.py",
        "```",
        "",
        "## Guarded checks",
        "",
        "| Check | Result | Evidence |",
        "| --- | --- | --- |",
    ]
    for name, passed, evidence in checks:
        lines.append(
            f"| {name} | {'PASS' if passed else 'FAIL'} | {evidence.replace('|', '/')} |"
        )
    lines.extend(
        [
            "",
            "## Static disposition",
            "",
            f"- Eligible exact part: **Bourns {MPN}**, distributor assembly ID",
            f"  **{CPN_ID}**.",
            "- Exact role: radial resettable PTC between `VCC_RAW` and `VCC` for",
            "  gross short and wiring-fault protection.",
            "- The committed horizontal span is the drawing's nominal 5.1 mm",
            "  and the total hole separation is 5.239 mm; the 1.01 mm",
            "  drill accepts the 0.81 mm nominal lead. The stock 1.2 mm",
            "  undimensioned stagger remains a first-article fit check.",
            f"- At 23 C, 3.0 A hold is {3.0 / PLANNING_LOAD_A:.2f}x the",
            f"  {PLANNING_LOAD_A:.2f} A planning load. Thermal derating remains",
            "  explicit rather than being hidden by that room-temperature ratio.",
            "",
            "## Remaining gates",
            "",
        ]
    )
    lines.extend(f"- {hold}" for hold in holds)
    lines.extend(
        [
            "",
            "## Primary evidence",
            "",
            "- Official Bourns product page:",
            "  `https://www.bourns.com/products/circuit-protection/resettable-fuses-multifuse-pptc-aec-q200-compliant/product/MF-RG`.",
            "- Preserved Bourns series datasheet:",
            "  `ref/datasheets/bourns-mf-rg.pdf`.",
            f"- Datasheet SHA-256: `{DATASHEET_SHA256}`.",
            "",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    report = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_REPORT
    checks, holds = build()
    write_report(report, checks, holds)
    print(f"Wrote {report.relative_to(ROOT) if report.is_relative_to(ROOT) else report}")
    failed = [name for name, passed, _ in checks if not passed]
    if failed:
        print("REV-A PTC: FAIL — " + "; ".join(failed))
        return 1
    print("REV-A PTC: EXACT CANDIDATE PASS / THERMAL AND FIRST-ARTICLE CHECK OPEN")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
