#!/usr/bin/python3
"""Guard the factory X9 reversed-ribbon PCB landings."""
from __future__ import annotations

import json
from pathlib import Path

import pcbnew


ROOT = Path(__file__).resolve().parents[1]
BOARD = ROOT / "kicad/juku.kicad_pcb"
SPEC = ROOT / "kicad/juku.board.json"
EXPECTED = {
    45: "KBD_SC3", 46: "KBD_SC2", 47: "KBD_SC1", 48: "KBD_SC0",
    49: "KBD_STB", 50: "KBD_CONTRDAT", 51: "KBD_CTRL", 52: "KBD_SHIFT",
    53: "P5V", 54: "P5V", 55: "KBD_FK", 56: "KBD_K1",
    57: "KBD_K0", 58: "KBD_K2",
}


def mm(value: int) -> float:
    return pcbnew.ToMM(value)


def main() -> int:
    board = pcbnew.LoadBoard(str(BOARD))
    spec = json.loads(SPEC.read_text(encoding="utf-8"))
    failures: list[str] = []
    if board.FindFootprintByReference("X9") is not None:
        failures.append("off-board X9 still has a PCB footprint")
    for number, net in EXPECTED.items():
        refdes = f"A{number}"
        footprint = board.FindFootprintByReference(refdes)
        if footprint is None:
            failures.append(f"{refdes} landing is missing")
            continue
        pad = footprint.FindPadByNumber("1")
        expected_x = 224.5 - (number - 45) * 2.5
        if pad is None:
            failures.append(f"{refdes}.1 is missing")
            continue
        position = pad.GetPosition()
        actual = (mm(position.x), mm(position.y))
        if abs(actual[0] - expected_x) > 0.002 or abs(actual[1] - 262.0) > 0.002:
            failures.append(f"{refdes}.1 position {actual} != ({expected_x}, 262.0)")
        if pad.GetNetname() != net:
            failures.append(f"{refdes}.1 net {pad.GetNetname()!r} != {net!r}")
        nodes = {tuple(node) for node in spec["nets"][net]["nodes"]}
        expected_nodes = {(refdes, "1"), ("X9", str(59 - number))}
        if not expected_nodes <= nodes:
            failures.append(
                f"{net} lacks harness nodes {sorted(expected_nodes - nodes)}"
            )

    if failures:
        for failure in failures:
            print("FAIL:", failure)
        return 1
    print("X9 LANDINGS: PASS — A45..A58 reverse onto off-board X9.14..X9.1")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
