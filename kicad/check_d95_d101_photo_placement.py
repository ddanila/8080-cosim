#!/usr/bin/env python3
"""Guard D101's package-centre offset from D95 in their shared owner photo."""
from __future__ import annotations

import json
import math
from pathlib import Path

import pcbnew

ROOT = Path(__file__).resolve().parents[1]
BOARD = ROOT / "kicad/juku.kicad_pcb"
REPORT = ROOT / "docs/photo-registration/local-packages/report.json"
PANORAMA = ROOT / "docs/photo-registration/panorama-registration.json"
BOARD_REGISTRATION = ROOT / "docs/photo-registration/board-registration.json"
GROUP = "component_grid"


def transform(matrix: list[float], point: tuple[float, float]) -> tuple[float, float]:
    x, y = point
    denominator = matrix[6] * x + matrix[7] * y + matrix[8]
    return ((matrix[0] * x + matrix[1] * y + matrix[2]) / denominator,
            (matrix[3] * x + matrix[4] * y + matrix[5]) / denominator)


def inverse(matrix: list[float]) -> list[float]:
    a, b, c, d, e, f, g, h, i = matrix
    cofactors = [e*i-f*h, c*h-b*i, b*f-c*e,
                 f*g-d*i, a*i-c*g, c*d-a*f,
                 d*h-e*g, b*g-a*h, a*e-b*d]
    determinant = a*cofactors[0] + b*cofactors[3] + c*cofactors[6]
    if abs(determinant) < 1e-12:
        raise SystemExit("D95/D101 PHOTO PLACEMENT: singular board registration")
    return [value / determinant for value in cofactors]


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
d95, d101 = fits[("D95", "component")], fits[("D101", "component")]
if d95["image"] != d101["image"]:
    raise SystemExit("D95/D101 PHOTO PLACEMENT: fits do not share one source photo")
panorama = json.loads(PANORAMA.read_text(encoding="utf-8"))["groups"][GROUP]
image_to_panorama = panorama["images"][d95["image"]]["original_to_panorama_homography"]
board_to_panorama = json.loads(BOARD_REGISTRATION.read_text(encoding="utf-8"))["groups"][GROUP]["board_to_panorama_homography"]
panorama_to_board = inverse(board_to_panorama)


def registered_centre(fit: dict) -> tuple[float, float]:
    return transform(panorama_to_board, transform(image_to_panorama, image_centre(fit)))


d95_registered, d101_registered = registered_centre(d95), registered_centre(d101)
expected = (d101_registered[0] - d95_registered[0],
            d101_registered[1] - d95_registered[1])
board = pcbnew.LoadBoard(str(BOARD))
d95_board, d101_board = pad_centre(board, "D95"), pad_centre(board, "D101")
actual = (d101_board[0] - d95_board[0], d101_board[1] - d95_board[1])
error = math.hypot(actual[0] - expected[0], actual[1] - expected[1])
if error > 0.03:
    raise SystemExit(
        f"D95/D101 PHOTO PLACEMENT: FAIL expected {expected}, actual {actual}, "
        f"error {error:.3f} mm"
    )
print(f"D95/D101 PHOTO PLACEMENT: PASS — D101 offset ({actual[0]:.3f}, {actual[1]:.3f}) mm")
