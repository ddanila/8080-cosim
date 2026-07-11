#!/usr/bin/env python3
"""Guard the D95/D99 and D101/D97/D102 rows from one raw owner photo."""
from __future__ import annotations

import json
import math
from pathlib import Path

import pcbnew

ROOT = Path(__file__).resolve().parents[1]
BOARD = ROOT / "kicad/juku.kicad_pcb"
REPORT = ROOT / "docs/photo-registration/local-packages/report.json"
RIGHT_BOARD_EDGE_X_PX = 3682.0
BOARD_WIDTH_MM = 310.0


def image_centre(fit: dict) -> tuple[float, float]:
    points = list(fit["projected_pins"].values())
    return (sum(point[0] for point in points) / len(points),
            sum(point[1] for point in points) / len(points))


def pad_centre(board: pcbnew.BOARD, refdes: str) -> tuple[float, float]:
    footprint = board.FindFootprintByReference(refdes)
    if footprint is None:
        raise SystemExit(f"D95/D101 PHOTO PLACEMENT: missing {refdes}")
    points = [pad.GetPosition() for pad in footprint.Pads()]
    return (sum(pcbnew.ToMM(point.x) for point in points) / len(points),
            sum(pcbnew.ToMM(point.y) for point in points) / len(points))


report = json.loads(REPORT.read_text(encoding="utf-8"))
fits = {(fit["refdes"], fit["side"]): fit for fit in report["fits"]}
refs = ("D95", "D99", "D101", "D97", "D102")
component = {ref: fits[(ref, "component")] for ref in refs}
if len({component[ref]["image"] for ref in refs}) != 1:
    raise SystemExit("D95/D101 PHOTO PLACEMENT: row fits do not share one source photo")
board = pcbnew.LoadBoard(str(BOARD))
summaries = []
for left, right in (("D95", "D99"), ("D95", "D101"),
                    ("D101", "D97"), ("D97", "D102")):
    left_fit, right_fit = component[left], component[right]
    scale = (1.0 / left_fit["scale_px_per_mm"] +
             1.0 / right_fit["scale_px_per_mm"]) / 2.0
    left_image, right_image = image_centre(left_fit), image_centre(right_fit)
    expected = ((right_image[0] - left_image[0]) * scale,
                (right_image[1] - left_image[1]) * scale)
    left_board, right_board = pad_centre(board, left), pad_centre(board, right)
    actual = (right_board[0] - left_board[0], right_board[1] - left_board[1])
    error = math.hypot(actual[0] - expected[0], actual[1] - expected[1])
    if error > 0.03:
        raise SystemExit(
            f"D95/D101 PHOTO PLACEMENT: FAIL {left}->{right} expected {expected}, "
            f"actual {actual}, error {error:.3f} mm"
        )
    summaries.append(f"{left}->{right} ({actual[0]:.3f}, {actual[1]:.3f}) mm")

# The board edge is directly visible beside both end packages. Its pixel
# coordinate and each package's own pitch provide an absolute-x cross-check,
# independent of the panorama's 27 px held-out board-registration residual.
for ref in ("D95", "D99", "D102"):
    fit = component[ref]
    expected_x = BOARD_WIDTH_MM - ((RIGHT_BOARD_EDGE_X_PX - image_centre(fit)[0]) /
                                   fit["scale_px_per_mm"])
    actual_x = pad_centre(board, ref)[0]
    if abs(actual_x - expected_x) > 0.6:
        raise SystemExit(
            f"D95/D101 PHOTO PLACEMENT: FAIL {ref} edge-derived x {expected_x:.3f}, "
            f"actual {actual_x:.3f} mm"
        )
print("D95/D101 PHOTO PLACEMENT: PASS — " + "; ".join(summaries))
