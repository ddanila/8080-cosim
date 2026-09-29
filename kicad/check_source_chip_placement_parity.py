#!/usr/bin/env python3
"""Check that the generator's modeled chip placements match the edited source PCB."""
from __future__ import annotations

import runpy
from pathlib import Path

import pcbnew


ROOT = Path(__file__).resolve().parents[1]
GENERATOR = ROOT / "kicad/gen_kicad_pcb.py"
BOARD = ROOT / "kicad/juku.kicad_pcb"
TOLERANCE_MM = 0.02


def main() -> int:
    place = runpy.run_path(str(GENERATOR))["PLACE"]
    board = pcbnew.LoadBoard(str(BOARD))
    footprints = {fp.GetReference(): fp for fp in board.GetFootprints()}
    failures = []
    compared = 0
    for ref, (expected_x, expected_y, expected_angle) in sorted(place.items()):
        footprint = footprints.get(ref)
        if footprint is None:
            continue  # PLACE also includes assembly-only outline references.
        compared += 1
        center = footprint.GetBoundingBox(False, False).GetCenter()
        actual_x, actual_y = pcbnew.ToMM(center.x), pcbnew.ToMM(center.y)
        actual_angle = footprint.GetOrientationDegrees() % 360
        if (abs(actual_x - expected_x) > TOLERANCE_MM
                or abs(actual_y - expected_y) > TOLERANCE_MM
                or abs(actual_angle - expected_angle % 360) > 0.01):
            failures.append(
                f"{ref}: generator ({expected_x:.3f},{expected_y:.3f},{expected_angle % 360:g}°) "
                f"!= source ({actual_x:.3f},{actual_y:.3f},{actual_angle:g}°)"
            )
    for failure in failures:
        print("FAIL:", failure)
    if failures:
        return 1
    print(f"SOURCE CHIP PLACEMENT PARITY: PASS — {compared} modeled footprints match the generator")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
