#!/usr/bin/python3
"""Guard the 23 physical X4 cable landings and source-proved FDC contract."""
from __future__ import annotations

import json
from pathlib import Path

import pcbnew


ROOT = Path(__file__).resolve().parents[1]
BOARD = ROOT / "kicad/juku.kicad_pcb"
SPEC = ROOT / "kicad/juku.board.json"
NETS = {
    1: "X4_01_NC_HARNESS", 2: "X4_02_BOUNDARY", 3: "X4_03_BOUNDARY",
    4: "X4_04_BOUNDARY", 5: "X4_05_BOUNDARY", 6: "GND",
    7: "X4_WR_PROTECT_N", 8: "X4_READY_N", 9: "X4_STEP_N",
    10: "X4_TG43", 11: "X4_WR_DATA_N", 12: "P5V", 13: "P5V",
    14: "X4_TR00_N", 15: "X4_INDEX_N", 16: "X4_DIR_N",
    17: "X4_HLOAD_N", 18: "X4_WR_GATE_N", 19: "X4_MOTOR_ON_N",
    20: "X4_SIDE_SEL", 21: "X4_DSEL1_N", 22: "X4_DSEL0_N",
    23: "X4_RD_DATA",
}
CIRCUIT_ENDPOINTS = {
    7: {("D98", "14")}, 8: {("D98", "2")}, 9: {("D100", "18")},
    10: {("D100", "16")}, 11: {("D100", "14")},
    14: {("D98", "12")}, 15: {("D98", "4")}, 16: {("D100", "19")},
    17: {("D100", "17")}, 18: {("D100", "15")},
    19: {("D100", "13")}, 20: {("D100", "12")},
    21: {("D28", "2"), ("D28", "3")}, 22: {("D28", "4")},
    23: {("D98", "6")},
}


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
        net = NETS[number]
        if pad.GetNetname() != net:
            failures.append(f"{refdes}.1 net {pad.GetNetname()!r} != {net!r}")
        nodes = {tuple(node) for node in spec["nets"][net]["nodes"]}
        if ("X4", str(number)) not in nodes:
            failures.append(f"{net} lacks X4.{number}")
        expected = CIRCUIT_ENDPOINTS.get(number, set())
        if not expected.issubset(nodes):
            failures.append(f"{net} lacks source-proved endpoints {sorted(expected - nodes)}")
    if failures:
        for failure in failures:
            print("FAIL:", failure)
        return 1
    print("X4 LANDINGS: PASS — AX401..AX423 and recovered .009 FDC interface")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
