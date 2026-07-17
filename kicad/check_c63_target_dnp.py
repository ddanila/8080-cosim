#!/usr/bin/env python3
"""Guard the evidence-backed C63 target-board DNP disposition."""
from __future__ import annotations

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BOARD_JSON = ROOT / "kicad/juku.board.json"
PCB = ROOT / "kicad/juku.kicad_pcb"
SCHEMATIC = ROOT / "kicad/juku.kicad_sch"
EVIDENCE = ROOT / "ref/photos/dgsh5-109-009-sb/fdc-lower-placement-registration.json"
GRID_EVIDENCE = ROOT / "ref/photos/dgsh5-109-009-sb/dram-decap-placement-registration.json"


def fail(message: str) -> None:
    raise SystemExit(f"C63 TARGET DNP: FAIL: {message}")


def block_end(text: str, start: int) -> int:
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
            continue
        if char == '"':
            quoted = True
        elif char == "(":
            depth += 1
        elif char == ")":
            depth -= 1
            if depth == 0:
                return index + 1
    fail("unterminated schematic symbol")
    raise AssertionError


def main() -> int:
    board = json.loads(BOARD_JSON.read_text(encoding="utf-8"))
    chip = next((item for item in board["chips"] if item.get("ref") == "C63"), None)
    if chip is None or chip.get("assembly_dnp") is not True or chip.get("pcb_dnp"):
        fail("board JSON must retain C63 artwork as assembly DNP")

    endpoints = {
        name: [str(pin) for ref, pin in net.get("nodes", []) if ref == "C63"]
        for name, net in board["nets"].items()
    }
    endpoints = {name: pins for name, pins in endpoints.items() if pins}
    if endpoints != {"GND": ["1"], "RAIL_H": ["2"]}:
        fail(f"intended schematic endpoints changed: {endpoints}")

    pcb_text = PCB.read_text(encoding="utf-8")
    marker = '(property "Reference" "C63"'
    ref_at = pcb_text.find(marker)
    if ref_at < 0:
        fail("source PCB lost the inherited C63 grid footprint")
    footprint_start = pcb_text.rfind("\n\t(footprint ", 0, ref_at)
    footprint_end = pcb_text.find("\n\t(footprint ", ref_at)
    footprint = pcb_text[footprint_start : len(pcb_text) if footprint_end < 0 else footprint_end]
    position = re.search(
        r"\n\t\t\(at\s+(-?[0-9.]+)\s+(-?[0-9.]+)(?:\s+(-?[0-9.]+))?\)",
        footprint,
    )
    if position is None:
        fail("cannot parse inherited C63 grid footprint position")
    x, y, angle = float(position.group(1)), float(position.group(2)), float(position.group(3) or 0.0)
    if abs(x - 173.6) > 0.01 or abs(y - 145.6) > 0.01 or abs(angle) > 0.01:
        fail(f"inherited C63 footprint moved: {(x, y, angle)}")
    attr = re.search(r"\n\t\t\(attr\s+([^\n)]+)\)", footprint)
    if attr is None or not {"through_hole", "dnp", "exclude_from_pos_files"}.issubset(
        set(attr.group(1).split())
    ):
        fail("inherited C63 footprint is not guarded DNP artwork")

    sch_text = SCHEMATIC.read_text(encoding="utf-8")
    c63_symbol = None
    for match in re.finditer(r'(?m)^\t\(symbol \(lib_id "juku:', sch_text):
        block = sch_text[match.start():block_end(sch_text, match.start() + 1)]
        if '(property "Reference" "C63"' in block:
            c63_symbol = block
            break
    if c63_symbol is None or "(on_board yes) (dnp yes)" not in c63_symbol:
        fail("schematic C63 is not retained on-board as DNP artwork")

    evidence = json.loads(EVIDENCE.read_text(encoding="utf-8"))
    target = next((item for item in evidence["targets"] if item.get("refdes") == "C63"), None)
    if target is None or target.get("drawing_px") != [1570.0, 3045.0]:
        fail("factory C63 target is missing or moved")
    absence = target.get("owner_absence_evidence", [])
    if len(absence) != 1 or absence[0].get("bbox_px") != [2230.0, 1880.0, 2330.0, 2170.0]:
        fail("registered target-board absence box changed")
    if not (ROOT / absence[0].get("image", "")).is_file():
        fail("registered target-board owner image is missing")

    grid = json.loads(GRID_EVIDENCE.read_text(encoding="utf-8"))
    special = grid.get("artwork_grid_photo_fit", {}).get("special_sites", {}).get("C63", {})
    if special.get("board_pad_midpoint_mm") != [176.1, 145.6]:
        fail("inherited C63 grid landing is not photo-registered")
    if "distinct from" not in str(special.get("disposition", "")):
        fail("C63 callout/grid distinction is not explicit")

    print("C63 TARGET DNP: PASS; .009 callout absent, inherited bare grid landing retained")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
