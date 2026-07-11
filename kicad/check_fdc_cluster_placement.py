#!/usr/bin/python3
"""Guard the final source-PCB placement of photo/drawing-proved FDC packages."""
from __future__ import annotations

from pathlib import Path

import pcbnew


ROOT = Path(__file__).resolve().parents[1]
BOARD = ROOT / "kicad/juku.kicad_pcb"
EXPECTED = {
    "D94": (229.275, 38.110, "1", "8"),
    "D100": (257.650, 37.400, "1", "10"),
    "D98": (290.000, 37.400, "1", "8"),
}


def mm(value: int) -> float:
    return pcbnew.ToMM(value)


def main() -> int:
    board = pcbnew.LoadBoard(str(BOARD))
    failures: list[str] = []
    for ref, (want_x, want_y, left_pin, right_pin) in EXPECTED.items():
        footprint = board.FindFootprintByReference(ref)
        if footprint is None:
            failures.append(f"{ref} missing")
            continue
        position = footprint.GetPosition()
        actual = (mm(position.x), mm(position.y), footprint.GetOrientationDegrees() % 360)
        if abs(actual[0] - want_x) > 0.002 or abs(actual[1] - want_y) > 0.002 or abs(actual[2] - 90.0) > 0.01:
            failures.append(f"{ref} posture {actual} != ({want_x}, {want_y}, 90)")
        pads = {pad.GetNumber(): pad.GetPosition() for pad in footprint.Pads()}
        left, right = pads[left_pin], pads[right_pin]
        if mm(left.x) >= mm(right.x) or abs(mm(left.y - right.y)) > 0.002:
            failures.append(f"{ref} notch-left lower-row order {left_pin}->{right_pin} is wrong")
        print(f"{ref}: centre=({actual[0]:.3f},{actual[1]:.3f}) rot={actual[2]:.1f} pin{left_pin}.x={mm(left.x):.3f} pin{right_pin}.x={mm(right.x):.3f}")
    if failures:
        for failure in failures:
            print("FAIL:", failure)
        return 1
    print("FDC CLUSTER PLACEMENT: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
