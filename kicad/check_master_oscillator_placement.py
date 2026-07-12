#!/usr/bin/env python3
"""Guard the assembly/photo-backed Z1/D59 oscillator placement."""
from __future__ import annotations

import sys
from pathlib import Path

import pcbnew


ROOT = Path(__file__).resolve().parents[1]
BOARD = ROOT / "kicad" / "juku.kicad_pcb"
EXPECTED = {
    "Z1": (79.4, 243.5, 90.0),
    "R31": (94.0, 257.0, 90.0),
    "D59": (106.6, 257.0, 90.0),
    "R32": (109.5, 246.0, 0.0),
    "C73": (58.0, 241.5, 0.0),
}


def main() -> int:
    board = pcbnew.LoadBoard(str(BOARD))
    failures: list[str] = []
    for ref, (want_x, want_y, want_angle) in EXPECTED.items():
        fp = board.FindFootprintByReference(ref)
        if fp is None:
            failures.append(f"{ref}: missing")
            continue
        center = fp.GetBoundingBox(False, False).GetCenter()
        x, y = pcbnew.ToMM(center.x), pcbnew.ToMM(center.y)
        angle = fp.GetOrientationDegrees() % 360
        residual = ((x - want_x) ** 2 + (y - want_y) ** 2) ** 0.5
        print(f"{ref}: centre=({x:.3f},{y:.3f}) residual={residual:.3f} mm angle={angle:.1f}")
        if residual > 0.05 or abs(angle - want_angle) > 0.1:
            failures.append(f"{ref}: placement drift")
    if failures:
        print("master oscillator placement FAIL: " + "; ".join(failures))
        return 1
    print("master oscillator placement PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
