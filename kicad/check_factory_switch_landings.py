#!/usr/bin/python3
"""Guard the PCB-side landings of bracket-mounted factory switch S1."""
from __future__ import annotations

from pathlib import Path

import pcbnew


ROOT = Path(__file__).resolve().parents[1]
BOARD = ROOT / "kicad/juku.kicad_pcb"


def mm(value: int) -> float:
    return pcbnew.ToMM(value)


def main() -> int:
    board = pcbnew.LoadBoard(str(BOARD))
    failures: list[str] = []
    if board.FindFootprintByReference("S1") is not None:
        failures.append("off-board S1 still has a PCB footprint")

    a17 = board.FindFootprintByReference("A17")
    if a17 is None:
        failures.append("dedicated А:17 landing A17 is missing")
    else:
        position = a17.GetPosition()
        actual = (mm(position.x), mm(position.y))
        if abs(actual[0] - 115.8) > 0.002 or abs(actual[1] - 27.1) > 0.002:
            failures.append(f"A17 position {actual} != (115.8, 27.1)")
        pad = a17.FindPadByNumber("1")
        if pad is None or pad.GetNetname() != "RES_RC":
            failures.append("A17.1 is not assigned to RES_RC")

    d98 = board.FindFootprintByReference("D98")
    pad7 = d98.FindPadByNumber("7") if d98 is not None else None
    if pad7 is None or pad7.GetNetname() != "D98_Y3_S1_2":
        failures.append("D98.7 is not assigned to the wire-18/S1.2 net")

    if failures:
        for failure in failures:
            print("FAIL:", failure)
        return 1
    print("FACTORY SWITCH LANDINGS: PASS — A17.1/RES_RC and D98.7/S1.2; S1 off-board")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
