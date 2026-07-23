#!/usr/bin/env python3
"""Guard the exact Littelfuse P4KE6.8A-B candidate used by Rev-A D1."""
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
DATASHEET = ROOT / "ref" / "datasheets" / "littelfuse-p4ke.pdf"
REFERENCE = ROOT / "ref" / "datasheets" / "littelfuse-p4ke6v8a-footprint.txt"
BOARD_JSON = ROOT / "spinoffs" / "minimal-vga" / "kicad" / "rev-a-physical.board.json"
PCB = ROOT / "spinoffs" / "minimal-vga" / "kicad" / "rev-a-physical.kicad_pcb"
GENERATOR = ROOT / "spinoffs" / "minimal-vga" / "kicad" / "gen_rev_a_pcb.py"
BOM = ROOT / "spinoffs" / "minimal-vga" / "kicad" / "rev-a.bom.csv"
CPN = ROOT / "spinoffs" / "minimal-vga" / "kicad" / "rev-a-jlcpcb-cpn-checklist.csv"
DEFAULT_REPORT = ROOT / "spinoffs" / "minimal-vga" / "docs" / "rev-a-tvs-candidate.md"

DATASHEET_SHA256 = "cab61a39ecf2d397cba37e06ec78765050ddfae63687ae4cf4dc3f83c1b7a845"
MPN = "P4KE6.8A-B"
CPN_ID = "C1666224"
FOOTPRINT_NAME = "D_DO-41_SOD81_P7.62mm_Horizontal"
PAD_CENTERS = {"1": (40.64, 34.29), "2": (40.64, 26.67)}
DESIGN_CLEARANCE_MM = 0.20
VCC_RAW_DETOUR = (
    ((47.7212, 43.2554), (42.5, 38.0342)),
    ((42.5, 38.0342), (42.1818, 38.3524)),
    ((42.1818, 38.3524), (36.5818, 32.7524)),
    ((36.5818, 32.7524), (36.9, 32.4342)),
    ((36.9, 32.4342), (23.9117, 19.4458)),
)


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


def footprint_pose(block: str) -> tuple[float, float, float]:
    legacy = re.search(
        r"\n\t\t\(at\s+(-?\d+(?:\.\d+)?)\s+(-?\d+(?:\.\d+)?)"
        r"(?:\s+(-?\d+(?:\.\d+)?))?",
        block,
    )
    if legacy:
        return (
            float(legacy.group(1)),
            float(legacy.group(2)),
            float(legacy.group(3) or 0.0),
        )
    transform = next(iter(forms("\n\t" + block, "\n\t\t(transform")), "")
    translate = pair(transform, "translate")
    rotate = re.search(r"\(rotate\s+(-?\d+(?:\.\d+)?)", transform)
    if not transform or not rotate:
        raise ValueError("footprint pose missing")
    return translate[0], translate[1], float(rotate.group(1))


def parse_pads(block: str) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for pad in forms("\n\t" + block, "\n\t\t(pad "):
        number = re.match(r'\(pad "([^"]+)"', pad)
        net = re.search(r'\(net(?:\s+\d+)?\s+"([^"]+)"\)', pad)
        drill = re.search(r"\(drill\s+(-?\d+(?:\.\d+)?)", pad)
        if not number:
            raise ValueError("unnumbered pad in D1 footprint")
        result[number.group(1)] = {
            "at": pair(pad, "at"),
            "size": pair(pad, "size"),
            "drill": float(drill.group(1)) if drill else 0.0,
            "net": net.group(1) if net else "",
        }
    return result


def point_segment_distance(
    point: tuple[float, float],
    start: tuple[float, float],
    end: tuple[float, float],
) -> float:
    vx, vy = end[0] - start[0], end[1] - start[1]
    wx, wy = point[0] - start[0], point[1] - start[1]
    length_squared = vx * vx + vy * vy
    position = (
        max(0.0, min(1.0, (wx * vx + wy * vy) / length_squared))
        if length_squared
        else 0.0
    )
    closest = (start[0] + position * vx, start[1] + position * vy)
    return math.dist(point, closest)


def point_box_distance(
    point: tuple[float, float],
    center: tuple[float, float],
    half_extent: float,
) -> float:
    dx = max(abs(point[0] - center[0]) - half_extent, 0.0)
    dy = max(abs(point[1] - center[1]) - half_extent, 0.0)
    return math.hypot(dx, dy)


def segment_intersects_box(
    start: tuple[float, float],
    end: tuple[float, float],
    center: tuple[float, float],
    half_extent: float,
) -> bool:
    minimum = (center[0] - half_extent, center[1] - half_extent)
    maximum = (center[0] + half_extent, center[1] + half_extent)
    lower, upper = 0.0, 1.0
    for origin, delta, low, high in (
        (start[0], end[0] - start[0], minimum[0], maximum[0]),
        (start[1], end[1] - start[1], minimum[1], maximum[1]),
    ):
        if abs(delta) < 1e-12:
            if origin < low or origin > high:
                return False
            continue
        enter, leave = (low - origin) / delta, (high - origin) / delta
        if enter > leave:
            enter, leave = leave, enter
        lower, upper = max(lower, enter), min(upper, leave)
        if lower > upper:
            return False
    return True


def segment_box_distance(
    start: tuple[float, float],
    end: tuple[float, float],
    center: tuple[float, float],
    half_extent: float,
) -> float:
    if segment_intersects_box(start, end, center, half_extent):
        return 0.0
    corners = (
        (center[0] - half_extent, center[1] - half_extent),
        (center[0] - half_extent, center[1] + half_extent),
        (center[0] + half_extent, center[1] - half_extent),
        (center[0] + half_extent, center[1] + half_extent),
    )
    return min(
        point_box_distance(start, center, half_extent),
        point_box_distance(end, center, half_extent),
        *(point_segment_distance(corner, start, end) for corner in corners),
    )


def minimum_unrelated_track_clearance(
    pcb_text: str, center: tuple[float, float], own_net: str, pad_number: str
) -> tuple[float, str]:
    clearances: list[tuple[float, str]] = []
    # KiCad's pad 1 is a 2.2 mm rounded square with a 0.25 mm corner radius:
    # an inner 1.7 mm square swept by that radius. Pad 2 is a 2.2 mm circle.
    inner_half_extent, corner_radius = (
        (0.85, 0.25) if pad_number == "1" else (0.0, 1.10)
    )
    for segment in forms("\n" + pcb_text, "\n\t(segment"):
        net = re.search(r'\(net\s+"([^"]+)"\)', segment)
        width = re.search(r"\(width\s+(\d+(?:\.\d+)?)", segment)
        if not net or not width or net.group(1) == own_net:
            continue
        distance = segment_box_distance(
            pair(segment, "start"),
            pair(segment, "end"),
            center,
            inner_half_extent,
        )
        edge_clearance = distance - corner_radius - float(width.group(1)) / 2
        clearances.append((edge_clearance, net.group(1)))
    if not clearances:
        return float("inf"), "none"
    return min(clearances)


def segment_key(
    start: tuple[float, float], end: tuple[float, float]
) -> tuple[tuple[float, float], tuple[float, float]]:
    return tuple(sorted((start, end)))  # type: ignore[return-value]


def exact_vcc_raw_detour_present(pcb_text: str) -> bool:
    actual = set()
    for segment in forms("\n" + pcb_text, "\n\t(segment"):
        if '(net "VCC_RAW")' not in segment or '(layer "F.Cu")' not in segment:
            continue
        actual.add(segment_key(pair(segment, "start"), pair(segment, "end")))
    return all(segment_key(start, end) in actual for start, end in VCC_RAW_DETOUR)


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
    pcb_text = PCB.read_text(encoding="utf-8")
    generator_text = GENERATOR.read_text(encoding="utf-8")
    board = json.loads(BOARD_JSON.read_text(encoding="utf-8"))
    block = footprint_block(pcb_text, "D1")

    required = (
        "Part number: P4KE6.8A-B",
        "Reverse stand-off voltage: 5.80 V",
        "Breakdown voltage at 10 mA: 6.45 V minimum, 7.14 V maximum",
        "Maximum clamping voltage at 39 A: 10.5 V",
        "Peak pulse power, 10/1000 us waveform: 400 W",
        "Body length: 4.10 mm minimum, 5.20 mm maximum",
        "Lead diameter: 0.71 mm minimum, 0.86 mm maximum",
        "-B = bulk packaging, 500 pieces per box",
    )
    add(
        checks,
        "Manufacturer datasheet and interpretation are pinned",
        sha256(DATASHEET) == DATASHEET_SHA256
        and all(marker in reference for marker in required),
        f"Littelfuse P4KE datasheet SHA-256 {DATASHEET_SHA256}",
    )

    chip = next(item for item in board["chips"] if item.get("ref") == "D1")
    add(
        checks,
        "Board model preserves exact value, polarity, and fused-rail topology",
        chip.get("type") == "D_TVS_THT"
        and chip.get("value") == MPN
        and chip.get("pins") == {"1": "K", "2": "A"},
        "D1=P4KE6.8A-B; pad 1=cathode/VCC and pad 2=anode/GND",
    )
    vcc_nodes = board["nets"]["VCC"]["nodes"]
    gnd_nodes = board["nets"]["GND"]["nodes"]
    add(
        checks,
        "Unidirectional TVS is reverse-biased across fused VCC",
        ["D1", "1"] in vcc_nodes and ["D1", "2"] in gnd_nodes,
        "cathode on VCC after F1; anode on GND",
    )

    name = re.match(r'\(footprint "([^"]+)"', block)
    pose = footprint_pose(block)
    pads = parse_pads(block)
    expected_pads = {
        "1": {"at": (0.0, 0.0), "size": (2.2, 2.2), "drill": 1.1, "net": "VCC"},
        "2": {"at": (7.62, 0.0), "size": (2.2, 2.2), "drill": 1.1, "net": "GND"},
    }
    add(
        checks,
        "Committed PCB embeds the corrected DO-41 footprint and pad contract",
        bool(name and name.group(1) == FOOTPRINT_NAME)
        and pose == (40.64, 34.29, 90.0)
        and pads == expected_pads,
        "DO-41/SOD81 P7.62; 2.20 mm pads and 1.10 mm drills; pad centers unchanged",
    )
    add(
        checks,
        "PCB generator preserves the exact D1 footprint and value",
        f'"D_TVS_THT": ("Diode_THT.pretty", "{FOOTPRINT_NAME}")'
        in generator_text
        and '"D1": "P4KE6.8A"' in generator_text,
        "regeneration maps D_TVS_THT to DO-41/SOD81 P7.62 and silk P4KE6.8A",
    )

    fab = next(
        item
        for item in forms("\n\t" + block, "\n\t\t(fp_rect")
        if '(layer "F.Fab")' in item
    )
    courtyard = next(
        item
        for item in forms("\n\t" + block, "\n\t\t(fp_rect")
        if '(layer "F.CrtYd")' in item
    )
    fab_start, fab_end = pair(fab, "start"), pair(fab, "end")
    court_start, court_end = pair(courtyard, "start"), pair(courtyard, "end")
    fab_size = (
        abs(fab_end[0] - fab_start[0]),
        abs(fab_end[1] - fab_start[1]),
    )
    court_size = (
        abs(court_end[0] - court_start[0]),
        abs(court_end[1] - court_start[1]),
    )
    add(
        checks,
        "Fabrication and courtyard envelopes carry the DO-41 maximum body",
        all(abs(actual - expected) < 0.001 for actual, expected in zip(fab_size, (5.2, 2.7)))
        and all(abs(actual - expected) < 0.001 for actual, expected in zip(court_size, (10.32, 3.2))),
        "F.Fab=5.20 x 2.70 mm; F.CrtYd=10.32 x 3.20 mm",
    )

    minimum_clearance = min(
        minimum_unrelated_track_clearance(
            pcb_text, PAD_CENTERS[number], net, number
        )
        for number, net in (("1", "VCC"), ("2", "GND"))
    )
    add(
        checks,
        "Larger DO-41 pads retain routed-copper clearance",
        minimum_clearance[0] >= DESIGN_CLEARANCE_MM,
        f"nearest unrelated track is {minimum_clearance[1]} with {minimum_clearance[0]:.3f} mm edge clearance",
    )
    add(
        checks,
        "Bounded VCC_RAW detour preserves the replaced segment endpoints",
        exact_vcc_raw_detour_present(pcb_text),
        "five connected F.Cu segments join (47.7212,43.2554) to (23.9117,19.4458)",
    )

    bom = csv_row(BOM, "D1", "Designator")
    cpn = csv_row(CPN, "TVS", "Group")
    add(
        checks,
        "Engineering BOM and assembly checklist name the exact catalogued part",
        bom.get("Candidate MPN") == f"Littelfuse {MPN}"
        and bom.get("JLCPCB/LCSC CPN") == CPN_ID
        and cpn.get("Preferred CPN") == CPN_ID
        and MPN in cpn.get("Notes", ""),
        f"D1 = Littelfuse {MPN} / {CPN_ID} in both ordering artifacts",
    )

    holds = [
        "The 10.5 V maximum clamp is the 39 A pulse point, not a 5 V rail ceiling. Define and review the accepted EFT/ESD/surge environment against every protected device's limits.",
        "D1 is not sustained wrong-supply or USB-C source-fault protection. Use a current-limited bench supply for bring-up and never infer USB-PD behavior from this shunt.",
        "Verify the 7.62 mm lead forming, cathode-band orientation, body seating, nearby clearance, and rail waveform on the first assembled article.",
        "C1666224 was out of stock during this static review. Recheck live stock, exact manufacturer identity, and manual/factory through-hole assembly capability immediately before ordering.",
        "This closes the exact D1 variant and copper-fit contract only. Socketed-part pin-1 orientation and the existing F1/J3 first-article gates remain separate.",
    ]
    return checks, holds


def write_report(
    path: Path, checks: list[tuple[str, bool, str]], holds: list[str]
) -> None:
    failures = [name for name, passed, _ in checks if not passed]
    status = (
        "EXACT D1 CANDIDATE GUARDED / SURGE AND FIRST-ARTICLE CHECK OPEN"
        if not failures
        else "FAILED"
    )
    lines = [
        "# Rev A TVS candidate readiness",
        "",
        "Status date: **2026-07-23**.",
        "",
        f"Status: **{status}**.",
        "",
        "This report guards Littelfuse P4KE6.8A-B as the exact Rev-A D1",
        "candidate. It checks the preserved manufacturer datasheet, fused-rail",
        "polarity, corrected DO-41 geometry, local routed clearance, and ordering",
        "identifiers. It is not a surge qualification, live-stock claim, or",
        "fabrication authorization.",
        "",
        "## Command",
        "",
        "```sh",
        "python3 spinoffs/minimal-vga/kicad/report_rev_a_tvs_candidate.py",
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
            f"- Exact catalogued candidate: **Littelfuse {MPN}**, distributor ID",
            f"  **{CPN_ID}**.",
            "- Exact role: unidirectional 400 W pulse TVS from fused `VCC`",
            "  (cathode) to `GND` (anode), after F1.",
            "- The corrected standard DO-41 footprint keeps the original 7.62 mm",
            "  centers, expands the holes for the 0.86 mm maximum leads, and",
            "  represents the full 5.20 x 2.70 mm maximum body.",
            "- A bounded local `VCC_RAW` detour preserves at least the board's",
            "  0.20 mm copper-clearance contract around the larger pad.",
            "- 5.80 V stand-off is above the nominal 5.0 V rail. Breakdown begins",
            "  at 6.45 V minimum; the rated 39 A pulse clamps at 10.5 V maximum.",
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
            "- Official Littelfuse product page:",
            "  `https://www.littelfuse.com/products/overvoltage-protection/tvs-diodes/leaded/p4ke/p4ke6-8a`.",
            "- Preserved Littelfuse P4KE series datasheet:",
            "  `ref/datasheets/littelfuse-p4ke.pdf`.",
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
        print("REV-A TVS: FAIL — " + "; ".join(failed))
        return 1
    print("REV-A TVS: EXACT CANDIDATE PASS / SURGE AND FIRST-ARTICLE CHECK OPEN")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
