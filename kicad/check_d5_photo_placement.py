#!/usr/bin/env python3
"""Guard the photo-corrected D5 placement and right-facing package notch."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pcbnew


ROOT = Path(__file__).resolve().parents[1]
BOARD = ROOT / "kicad/juku.kicad_pcb"
LOCAL_REPORT = ROOT / "docs/photo-registration/local-packages/report.json"
PANORAMA_REPORT = ROOT / "docs/photo-registration/panorama-registration.json"
BOARD_REGISTRATION = ROOT / "docs/photo-registration/board-registration.json"
IMAGE = "ref/photos/juku-pcb-2/PXL_20260710_200411500.jpg"
MAX_PLACEMENT_ERROR_MM = 0.10


def project(matrix: np.ndarray, point: tuple[float, float]) -> np.ndarray:
    value = matrix @ np.array([point[0], point[1], 1.0])
    return value[:2] / value[2]


local = json.loads(LOCAL_REPORT.read_text(encoding="utf-8"))
d5_fit = next(
    fit
    for fit in local["fits"]
    if fit["refdes"] == "D5" and fit["side"] == "component"
)
errors: list[str] = []
if d5_fit["image"] != IMAGE or d5_fit["model"] != "affine":
    errors.append("D5 component fit does not use the guarded raw image/affine model")
if any(item["error_px"] > 1.0 for item in d5_fit["checks"]):
    errors.append("D5 local package residual exceeds 1 px")

image_points = np.array(list(d5_fit["projected_pins"].values()), dtype=float)
image_centre = image_points.mean(axis=0)
panorama = json.loads(PANORAMA_REPORT.read_text(encoding="utf-8"))
registration = json.loads(BOARD_REGISTRATION.read_text(encoding="utf-8"))
image_h = np.array(
    panorama["groups"]["component_grid"]["images"][IMAGE][
        "original_to_panorama_homography"
    ]
).reshape(3, 3)
board_h = np.array(
    registration["groups"]["component_grid"]["board_to_panorama_homography"]
).reshape(3, 3)
expected = project(np.linalg.inv(board_h), tuple(project(image_h, tuple(image_centre))))

board = pcbnew.LoadBoard(str(BOARD))
d5 = board.FindFootprintByReference("D5")
if d5 is None:
    raise SystemExit("D5 PHOTO PLACEMENT: D5 footprint missing")
pads = list(d5.Pads())
actual = np.array(
    [
        sum(pcbnew.ToMM(pad.GetPosition().x) for pad in pads) / len(pads),
        sum(pcbnew.ToMM(pad.GetPosition().y) for pad in pads) / len(pads),
    ]
)
placement_error = float(np.linalg.norm(actual - expected))
if placement_error > MAX_PLACEMENT_ERROR_MM:
    errors.append(
        f"D5 centre {actual[0]:.3f},{actual[1]:.3f} differs from "
        f"photo projection {expected[0]:.3f},{expected[1]:.3f} by "
        f"{placement_error:.3f} mm"
    )
orientation = d5.GetOrientationDegrees() % 360
if abs(orientation - 270.0) > 0.01:
    errors.append(f"D5 orientation {orientation:.3f} is not notch-right 270 degrees")

if errors:
    raise SystemExit("D5 PHOTO PLACEMENT: FAIL\n- " + "\n- ".join(errors))
print(
    "D5 PHOTO PLACEMENT: PASS — "
    f"centre {actual[0]:.3f},{actual[1]:.3f} mm, orientation 270 degrees; "
    f"panorama residual {placement_error:.3f} mm"
)
