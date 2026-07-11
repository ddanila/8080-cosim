#!/usr/bin/python3
"""Guard the factory X8 power-cable PCB landings and remote pins."""
from __future__ import annotations

import json
from pathlib import Path

import pcbnew


ROOT = Path(__file__).resolve().parents[1]
BOARD = ROOT / "kicad/juku.kicad_pcb"
SPEC = ROOT / "kicad/juku.board.json"
EXPECTED = {
    59: (34.0, "M12V", ("8",)),
    60: (29.0, "P12V", ("3",)),
    61: (24.0, "P5V", ("2", "6")),
    62: (19.0, "GND", ("1", "5")),
}


def mm(value: int) -> float:
    return pcbnew.ToMM(value)


def main() -> int:
    board = pcbnew.LoadBoard(str(BOARD))
    spec = json.loads(SPEC.read_text(encoding="utf-8"))
    failures: list[str] = []
    if board.FindFootprintByReference("X8") is not None:
        failures.append("off-board X8 still has a PCB footprint")
    for number, (expected_x, net, remote_pins) in EXPECTED.items():
        refdes = f"A{number}"
        footprint = board.FindFootprintByReference(refdes)
        pad = footprint.FindPadByNumber("1") if footprint is not None else None
        if pad is None:
            failures.append(f"{refdes}.1 landing is missing")
            continue
        position = pad.GetPosition()
        actual = (mm(position.x), mm(position.y))
        if abs(actual[0] - expected_x) > 0.002 or abs(actual[1] - 252.6) > 0.002:
            failures.append(f"{refdes}.1 position {actual} != ({expected_x}, 252.6)")
        if pad.GetNetname() != net:
            failures.append(f"{refdes}.1 net {pad.GetNetname()!r} != {net!r}")
        nodes = {tuple(node) for node in spec["nets"][net]["nodes"]}
        expected_nodes = {(refdes, "1")} | {("X8", pin) for pin in remote_pins}
        if not expected_nodes <= nodes:
            failures.append(f"{net} lacks harness nodes {sorted(expected_nodes - nodes)}")

    if failures:
        for failure in failures:
            print("FAIL:", failure)
        return 1
    print("X8 LANDINGS: PASS — A59..A62 feed six remote conductors on X8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
