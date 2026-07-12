#!/usr/bin/python3
"""Guard the photo-proved R94 load at D98.3."""
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
    r94 = board.FindFootprintByReference("R94")
    d98 = board.FindFootprintByReference("D98")
    if r94 is None:
        failures.append("R94 footprint is missing")
    else:
        position = r94.GetPosition()
        actual = (mm(position.x), mm(position.y), r94.GetOrientationDegrees())
        expected = (297.6, 51.32, -90.0)
        if any(abs(got - want) > 0.002 for got, want in zip(actual, expected)):
            failures.append(f"R94 placement {actual} != {expected}")
        if r94.GetValue() != "220":
            failures.append(f"R94 value {r94.GetValue()!r} != '220'")
        pad1 = r94.FindPadByNumber("1")
        pad2 = r94.FindPadByNumber("2")
        if pad1 is None or pad1.GetNetname() != "D98_Y1_R94":
            failures.append("R94.1 is not assigned to D98_Y1_R94")
        if pad2 is None or pad2.GetNetname() != "R94_P2_BOUNDARY":
            failures.append("R94.2 must remain on its explicit measurement boundary")
        if pad1 is not None:
            position1 = pad1.GetPosition()
            actual1 = (mm(position1.x), mm(position1.y))
            if any(abs(got - want) > 0.002 for got, want in zip(actual1, (297.6, 51.32))):
                failures.append(f"R94.1 position {actual1} != (297.6, 51.32)")
        if pad2 is not None:
            position2 = pad2.GetPosition()
            actual2 = (mm(position2.x), mm(position2.y))
            if any(abs(got - want) > 0.002 for got, want in zip(actual2, (297.6, 61.48))):
                failures.append(f"R94.2 position {actual2} != (297.6, 61.48)")

    d98_pad3 = d98.FindPadByNumber("3") if d98 is not None else None
    if d98_pad3 is None or d98_pad3.GetNetname() != "D98_Y1_R94":
        failures.append("D98.3 is not assigned to D98_Y1_R94")

    if failures:
        for failure in failures:
            print("FAIL:", failure)
        return 1
    print("R94 LANDING: PASS — 220 ohm from D98.3; far terminal is an explicit measurement boundary")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
