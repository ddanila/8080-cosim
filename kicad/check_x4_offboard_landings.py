#!/usr/bin/python3
"""Guard the 23 physical X4 cable landings and remote connector contract."""
from __future__ import annotations

import json
from pathlib import Path

import pcbnew


ROOT = Path(__file__).resolve().parents[1]
BOARD = ROOT / "kicad/juku.kicad_pcb"
SPEC = ROOT / "kicad/juku.board.json"
ACTIVE = {1: "X4_FF_N", 2: "X4_REC_N", 3: "X4_PLAY_N", 4: "X4_RN_N", 5: "X4_STOP_N"}


def mm(value: int) -> float:
    return pcbnew.ToMM(value)


def main() -> int:
    board = pcbnew.LoadBoard(str(BOARD))
    spec = json.loads(SPEC.read_text(encoding="utf-8"))
    failures: list[str] = []
    if board.FindFootprintByReference("X4") is not None:
        failures.append("off-board X4 still has a PCB footprint")
    for number in range(1, 24):
        refdes = f"AX4{number:02d}"
        footprint = board.FindFootprintByReference(refdes)
        pad = footprint.FindPadByNumber("1") if footprint else None
        if pad is None:
            failures.append(f"{refdes}.1 is missing")
            continue
        expected_x = 221.5 + (number - 1) * 2.54
        position = pad.GetPosition()
        if abs(mm(position.x) - expected_x) > 0.002 or abs(mm(position.y) - 15.2) > 0.002:
            failures.append(f"{refdes}.1 has wrong position")
        net = ACTIVE.get(number, f"X4_{number:02d}_BOUNDARY")
        if pad.GetNetname() != net:
            failures.append(f"{refdes}.1 net {pad.GetNetname()!r} != {net!r}")
        nodes = {tuple(node) for node in spec["nets"][net]["nodes"]}
        if ("X4", str(number)) not in nodes:
            failures.append(f"{net} lacks X4.{number}")
        if number > 5 and nodes != {(refdes, "1"), ("X4", str(number))}:
            failures.append(f"{net} is not a landing-to-connector-only boundary")
    for number, net in ACTIVE.items():
        expected_pin = {1: "8", 2: "10", 3: "12", 4: "4", 5: "2"}[number]
        nodes = {tuple(node) for node in spec["nets"][net]["nodes"]}
        if ("D28", expected_pin) not in nodes:
            failures.append(f"{net} lacks D28.{expected_pin}")
    if failures:
        for failure in failures:
            print("FAIL:", failure)
        return 1
    print("X4 LANDINGS: PASS — AX401..AX423 harness and five guarded D28 controls")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
