#!/usr/bin/env python3
"""Guard the exact HRO TYPE-C-31-M-17 candidate used by Rev-A J3."""
from __future__ import annotations

import csv
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
DATASHEET = ROOT / "ref" / "datasheets" / "hro-type-c-31-m-17.pdf"
REFERENCE = ROOT / "ref" / "datasheets" / "hro-type-c-31-m-17-footprint.txt"
BOARD_JSON = ROOT / "spinoffs" / "minimal-vga" / "kicad" / "rev-a-physical.board.json"
PCB = ROOT / "spinoffs" / "minimal-vga" / "kicad" / "rev-a-physical.kicad_pcb"
BOM = ROOT / "spinoffs" / "minimal-vga" / "kicad" / "rev-a.bom.csv"
CPN = ROOT / "spinoffs" / "minimal-vga" / "kicad" / "rev-a-jlcpcb-cpn-checklist.csv"
DEFAULT_REPORT = (
    ROOT / "spinoffs" / "minimal-vga" / "docs" / "rev-a-usb-c-candidate.md"
)

DATASHEET_SHA256 = "e38df7ca56f6fa10a78f0c84ee40d26c90af25a1c6c3a692508e46bee2ee11d1"
FOOTPRINT_NAME = "USB_C_Receptacle_HRO_TYPE-C-31-M-17"
CONTACTS = {
    "B12": ((-2.75, -3.18), (0.90, 1.60), "GND"),
    "B9": ((-1.52, -3.18), (0.80, 1.60), "VCC_RAW"),
    "A5": ((-0.50, -3.18), (0.70, 1.60), "USB_CC1"),
    "B5": ((0.50, -3.18), (0.70, 1.60), "USB_CC2"),
    "A9": ((1.52, -3.18), (0.80, 1.60), "VCC_RAW"),
    "A12": ((2.75, -3.18), (0.90, 1.60), "GND"),
}
SHELL_CENTRES = {
    (-4.32, -3.00),
    (-4.32, 0.80),
    (4.32, -3.00),
    (4.32, 0.80),
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def forms(text: str, marker: str) -> list[str]:
    """Extract balanced S-expression forms starting with marker."""
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


def rounded(pair_value: tuple[float, float]) -> tuple[float, float]:
    return tuple(round(value, 3) for value in pair_value)  # type: ignore[return-value]


def parse_pads(block: str) -> list[dict[str, Any]]:
    pads: list[dict[str, Any]] = []
    for pad in forms("\n\t" + block, "\n\t\t(pad "):
        number = re.match(r'\(pad "([^"]+)"', pad)
        net = re.search(r'\(net(?:\s+\d+)?\s+"([^"]+)"\)', pad)
        drill = re.search(
            r"\(drill(?:\s+oval)?\s+(-?\d+(?:\.\d+)?)"
            r"(?:\s+(-?\d+(?:\.\d+)?))?",
            pad,
        )
        if not number:
            raise ValueError("unnumbered pad in J3 footprint")
        drill_pair = (0.0, 0.0)
        if drill:
            first = float(drill.group(1))
            drill_pair = (first, float(drill.group(2) or first))
        pads.append(
            {
                "number": number.group(1),
                "at": rounded(pair(pad, "at")),
                "size": rounded(pair(pad, "size")),
                "drill": rounded(drill_pair),
                "net": net.group(1) if net else "",
            }
        )
    return pads


def nodes(board: dict[str, Any], name: str) -> set[tuple[str, str]]:
    entry = board["nets"][name]
    raw = entry["nodes"] if isinstance(entry, dict) else entry
    return {tuple(item) for item in raw}


def add_check(
    checks: list[tuple[str, bool, str]], name: str, passed: bool, evidence: str
) -> None:
    checks.append((name, passed, evidence))


def csv_row(
    path: Path, value: str, field: str = "Designator"
) -> dict[str, str]:
    with path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    return next(row for row in rows if row.get(field) == value)


def build() -> tuple[list[tuple[str, bool, str]], list[str]]:
    checks: list[tuple[str, bool, str]] = []
    reference = REFERENCE.read_text(encoding="utf-8")
    board = json.loads(BOARD_JSON.read_text(encoding="utf-8"))
    pcb_text = PCB.read_text(encoding="utf-8")
    block = footprint_block(pcb_text, "J3")

    required_reference_markers = (
        "Part number: TYPE-C-31-M-17",
        "Body: 8.94 mm wide x 6.80 mm deep x 3.16 mm high",
        "Rated load: DC 20 V, 5 A",
        "A5   CC1",
        "A9   VBUS",
        "A12  GND",
        "B12  GND",
        "B9   VBUS",
        "B5   CC2",
    )
    add_check(
        checks,
        "Manufacturer drawing and interpretation are pinned",
        sha256(DATASHEET) == DATASHEET_SHA256
        and all(marker in reference for marker in required_reference_markers),
        f"HRO drawing SHA-256 {DATASHEET_SHA256}",
    )

    chip = next(item for item in board["chips"] if item.get("ref") == "J3")
    expected_pins = {
        "A5": "USB_CC1",
        "B5": "USB_CC2",
        "A9": "VCC_RAW",
        "B9": "VCC_RAW",
        "A12": "GND",
        "B12": "GND",
        "S1": "GND",
    }
    add_check(
        checks,
        "Board model uses the exact six-contact power-only contract",
        chip.get("type") == "USB_C_POWER_HRO"
        and chip.get("value") == "USB-C 5V"
        and chip.get("pins") == expected_pins,
        "A5/B5=CC1/CC2, A9/B9=VCC_RAW, A12/B12/shell=GND; no data pins",
    )
    add_check(
        checks,
        "Both configuration-channel inputs have independent Rd pulldowns",
        nodes(board, "USB_CC1") == {("J3", "A5"), ("R30", "1")}
        and nodes(board, "USB_CC2") == {("J3", "B5"), ("R31", "1")}
        and {("R30", "2"), ("R31", "2")} <= nodes(board, "GND")
        and all(
            next(item for item in board["chips"] if item.get("ref") == ref).get(
                "value"
            )
            == "5k1"
            for ref in ("R30", "R31")
        ),
        "R30/R31 are separate 5.1 kΩ CC1/CC2-to-GND USB-C sink pulldowns",
    )

    name = re.match(r'\(footprint "([^"]+)"', block)
    add_check(
        checks,
        "Committed PCB embeds the exact HRO footprint",
        bool(name and name.group(1) == FOOTPRINT_NAME),
        FOOTPRINT_NAME,
    )

    pads = parse_pads(block)
    contact_pads = {pad["number"]: pad for pad in pads if pad["number"] in CONTACTS}
    contacts_ok = set(contact_pads) == set(CONTACTS)
    for number, (at, size, net) in CONTACTS.items():
        actual = contact_pads.get(number, {})
        contacts_ok &= (
            actual.get("at") == at
            and actual.get("size") == size
            and actual.get("drill") == (0.0, 0.0)
            and actual.get("net") == net
        )
    add_check(
        checks,
        "All six contact pads match the recommended component-side layout",
        contacts_ok,
        "centres, 0.70/0.80/0.90 x 1.60 mm copper, and CC/VBUS/GND nets match",
    )

    shell = [pad for pad in pads if pad["number"] in {"SH", "S1"}]
    shell_ok = (
        len(shell) == 4
        and {pad["at"] for pad in shell} == SHELL_CENTRES
        and all(pad["size"] == (1.0, 1.7) for pad in shell)
        and all(set(pad["drill"]) == {0.5, 1.2} for pad in shell)
        and all(pad["net"] == "GND" for pad in shell)
    )
    add_check(
        checks,
        "All four shell tabs match the drawing",
        shell_ok,
        "8.64 x 3.80 mm centre rectangle; 1.00 x 1.70 mm copper; 0.50 x 1.20 mm slots",
    )

    fab_points: set[tuple[float, float]] = set()
    fab_line_count = 0
    for line in forms("\n\t" + block, "\n\t\t(fp_line"):
        if '(layer "F.Fab")' not in line:
            continue
        fab_line_count += 1
        fab_points.add(rounded(pair(line, "start")))
        fab_points.add(rounded(pair(line, "end")))
    expected_fab_points = {
        (-4.47, -3.40),
        (-4.47, 3.40),
        (4.47, -3.40),
        (4.47, 3.40),
    }
    add_check(
        checks,
        "Fabrication outline matches the 8.94 x 6.80 mm body",
        fab_line_count == 4 and fab_points == expected_fab_points,
        "F.Fab rectangle spans x=-4.47..4.47 mm and y=-3.40..3.40 mm",
    )

    bom = csv_row(BOM, "J3")
    cpn = csv_row(CPN, "Power input", "Group")
    add_check(
        checks,
        "Engineering BOM and assembly checklist name the same exact candidate",
        bom.get("Candidate MPN") == "TYPE-C-31-M-17"
        and bom.get("JLCPCB/LCSC CPN") == "C283540"
        and "C283540" in cpn.get("Preferred CPN", "")
        and "TYPE-C-31-M-17" in cpn.get("Notes", ""),
        "J3 = HRO TYPE-C-31-M-17 / C283540 in both ordering artifacts",
    )

    holds = [
        "The connector is eligible only for Rev-A's power-only 5 V sink role; do not infer USB data connectivity from the Type-C shell.",
        "The connector's 5 A contact rating does not negotiate or guarantee source current. Keep the existing power-budget caveat and use one of J1/J3 at a time.",
        "Recheck C283540 live stock, the vendor's current land pattern, and assembly orientation immediately before ordering; inspect a first article before any larger build.",
        "This closes only J3. The Rev-A PTC, TVS, and socketed-part pin-1 review items remain separate.",
    ]
    return checks, holds


def write_report(
    path: Path, checks: list[tuple[str, bool, str]], holds: list[str]
) -> None:
    failures = [name for name, passed, _ in checks if not passed]
    status = (
        "EXACT J3 CANDIDATE GUARDED / ORDER-TIME CHECK OPEN"
        if not failures
        else "FAILED"
    )
    lines = [
        "# Rev A USB-C candidate readiness",
        "",
        "Status date: **2026-07-23**.",
        "",
        f"Status: **{status}**.",
        "",
        "This report guards HRO TYPE-C-31-M-17 as the exact Rev-A J3 candidate.",
        "It checks the preserved manufacturer drawing, board-level power-only",
        "contract, committed KiCad geometry, and ordering identifiers. It is not",
        "a live-stock claim or fabrication authorization.",
        "",
        "## Command",
        "",
        "```sh",
        "python3 spinoffs/minimal-vga/kicad/report_rev_a_usb_c_candidate.py",
        "```",
        "",
        "## Guarded checks",
        "",
        "| Check | Result | Evidence |",
        "| --- | --- | --- |",
    ]
    for name, passed, evidence in checks:
        lines.append(
            f"| {name} | {'PASS' if passed else 'FAIL'} | "
            f"{evidence.replace('|', '/')} |"
        )
    lines.extend(
        [
            "",
            "## Static disposition",
            "",
            "- Eligible part: **HRO TYPE-C-31-M-17**, distributor assembly ID",
            "  **C283540**.",
            "- Exact role: optional six-contact, power-only USB-C 5 V sink feeding",
            "  `VCC_RAW` before F1, with independent 5.1 kΩ CC1/CC2 Rd pulldowns.",
            "- The drawing's contact centres, copper sizes, shell slots, and",
            "  8.94 x 6.80 mm body agree with the committed footprint.",
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
            "- Official HRO product page:",
            "  `https://en.krhro.com/Product-Details/722.html`.",
            "- Preserved HRO drawing:",
            "  `ref/datasheets/hro-type-c-31-m-17.pdf`.",
            f"- Drawing SHA-256: `{DATASHEET_SHA256}`.",
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
        print("REV-A USB-C: FAIL — " + "; ".join(failed))
        return 1
    print("REV-A USB-C: EXACT CANDIDATE PASS / ORDER-TIME CHECK OPEN")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
