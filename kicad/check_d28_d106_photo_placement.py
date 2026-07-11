#!/usr/bin/env python3
"""Guard the fitted D106/D28/D96 row's relative placement."""
from __future__ import annotations

import json
import math
from pathlib import Path

import pcbnew

ROOT = Path(__file__).resolve().parents[1]
BOARD = ROOT / "kicad" / "juku.kicad_pcb"
REPORT = ROOT / "docs" / "photo-registration" / "local-packages" / "report.json"


def image_centre(fit: dict) -> tuple[float, float]:
    points = list(fit["projected_pins"].values())
    return (sum(point[0] for point in points) / len(points),
            sum(point[1] for point in points) / len(points))


def board_centre(board: pcbnew.BOARD, refdes: str) -> tuple[float, float]:
    footprint = board.FindFootprintByReference(refdes)
    if footprint is None:
        raise SystemExit(f"{refdes} footprint missing")
    points = [pad.GetPosition() for pad in footprint.Pads()]
    return (sum(pcbnew.ToMM(point.x) for point in points) / len(points),
            sum(pcbnew.ToMM(point.y) for point in points) / len(points))


report = json.loads(REPORT.read_text(encoding="utf-8"))
fits = {(fit["refdes"], fit["side"]): fit for fit in report["fits"]}
board = pcbnew.LoadBoard(str(BOARD))
summaries = []
for left, right in (("D106", "D28"), ("D28", "D96")):
    left_fit = fits[(left, "component")]
    right_fit = fits[(right, "component")]
    scale = (1.0 / left_fit["scale_px_per_mm"] + 1.0 / right_fit["scale_px_per_mm"]) / 2.0
    left_image = image_centre(left_fit)
    right_image = image_centre(right_fit)
    expected = ((right_image[0] - left_image[0]) * scale,
                (right_image[1] - left_image[1]) * scale)
    left_board = board_centre(board, left)
    right_board = board_centre(board, right)
    actual = (right_board[0] - left_board[0], right_board[1] - left_board[1])
    error = math.hypot(actual[0] - expected[0], actual[1] - expected[1])
    if error > 0.03:
        raise SystemExit(
            f"FDC ROW PHOTO PLACEMENT: FAIL {left}->{right} expected {expected}, "
            f"actual {actual}, error {error:.3f} mm"
        )
    summaries.append(f"{left}->{right} ({actual[0]:.3f}, {actual[1]:.3f}) mm")
print("FDC ROW PHOTO PLACEMENT: PASS — " + "; ".join(summaries))
