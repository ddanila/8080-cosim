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
    if chip is None or chip.get("pcb_dnp") is not True:
        fail("board JSON must mark C63 pcb_dnp=true")

    endpoints = {
        name: [str(pin) for ref, pin in net.get("nodes", []) if ref == "C63"]
        for name, net in board["nets"].items()
    }
    endpoints = {name: pins for name, pins in endpoints.items() if pins}
    if endpoints != {"GND": ["1"], "RAIL_H": ["2"]}:
        fail(f"intended schematic endpoints changed: {endpoints}")

    pcb_text = PCB.read_text(encoding="utf-8")
    if '(property "Reference" "C63"' in pcb_text:
        fail("source PCB still contains a C63 footprint")

    sch_text = SCHEMATIC.read_text(encoding="utf-8")
    c63_symbol = None
    for match in re.finditer(r'(?m)^\t\(symbol \(lib_id "juku:', sch_text):
        block = sch_text[match.start():block_end(sch_text, match.start() + 1)]
        if '(property "Reference" "C63"' in block:
            c63_symbol = block
            break
    if c63_symbol is None or "(on_board no) (dnp yes)" not in c63_symbol:
        fail("schematic C63 is not marked on_board=no and dnp=yes")

    evidence = json.loads(EVIDENCE.read_text(encoding="utf-8"))
    target = next((item for item in evidence["targets"] if item.get("refdes") == "C63"), None)
    if target is None or target.get("drawing_px") != [1570.0, 3045.0]:
        fail("factory C63 target is missing or moved")
    absence = target.get("owner_absence_evidence", [])
    if len(absence) != 1 or absence[0].get("bbox_px") != [2230.0, 1880.0, 2330.0, 2170.0]:
        fail("registered target-board absence box changed")
    if not (ROOT / absence[0].get("image", "")).is_file():
        fail("registered target-board owner image is missing")

    print("C63 TARGET DNP: PASS; schematic intent retained, target PCB footprint absent")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
