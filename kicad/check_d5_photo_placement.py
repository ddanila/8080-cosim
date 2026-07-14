#!/usr/bin/env python3
"""Guard the D5/D7/D8/D9 photo placements against fitted D50/D51 anchors."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pcbnew


ROOT = Path(__file__).resolve().parents[1]
BOARD = ROOT / "kicad/juku.kicad_pcb"
LOCAL_REPORT = ROOT / "docs/photo-registration/local-packages/report.json"
IMAGE = "ref/photos/juku-pcb-2/PXL_20260710_200411500.jpg"
MAX_ANCHOR_SPREAD_MM = 0.75
MAX_PLACEMENT_ERROR_MM = 0.01


document = json.loads(LOCAL_REPORT.read_text(encoding="utf-8"))
fits = {(fit["refdes"], fit["side"]): fit for fit in document["fits"]}
required = {
    (refdes, "component")
    for refdes in ("D5", "D7", "D8", "D9", "R13", "R14", "D50", "D51")
}
missing = required - fits.keys()
if missing:
    raise SystemExit(f"D5/D7-D9 PHOTO PLACEMENT: missing fits {sorted(missing)}")
if {fits[key]["image"] for key in required} != {IMAGE}:
    raise SystemExit("D5/D7-D9 PHOTO PLACEMENT: fits do not share the guarded raw image")

board = pcbnew.LoadBoard(str(BOARD))


def geometry(refdes: str) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    footprint = board.FindFootprintByReference(refdes)
    if footprint is None:
        raise SystemExit(f"D5/D7-D9 PHOTO PLACEMENT: missing footprint {refdes}")
    fit = fits[(refdes, "component")]
    board_points: list[list[float]] = []
    image_points: list[list[float]] = []
    for pad in footprint.Pads():
        position = pad.GetPosition()
        board_points.append(
            [pcbnew.ToMM(position.x), pcbnew.ToMM(position.y)]
        )
        image_points.append(fit["projected_pins"][pad.GetNumber()])
    board_array = np.array(board_points, dtype=float)
    image_array = np.array(image_points, dtype=float)
    board_centre = board_array.mean(axis=0)
    image_centre = image_array.mean(axis=0)
    board_to_image = np.linalg.lstsq(
        board_array - board_centre,
        image_array - image_centre,
        rcond=None,
    )[0]
    return board_centre, image_centre, board_to_image


geometries = {
    refdes: geometry(refdes)
    for refdes in ("D5", "D7", "D8", "D9", "R13", "R14", "D50", "D51")
}
errors: list[str] = []
summaries: list[str] = []
for target in ("D5", "D7", "D8", "D9", "R13", "R14"):
    target_centre, target_image, target_matrix = geometries[target]
    target_fit = fits[(target, "component")]
    expected_model = "similarity" if target.startswith("R") else "affine"
    if target_fit["model"] != expected_model:
        errors.append(f"{target}: component fit is not {expected_model}")
    if any(item["error_px"] > 1.0 for item in target_fit["checks"]):
        errors.append(f"{target}: local package residual exceeds 1 px")
    estimates: list[np.ndarray] = []
    for anchor in ("D50", "D51"):
        anchor_centre, anchor_image, anchor_matrix = geometries[anchor]
        average_matrix = (
            anchor_matrix
            if target.startswith("R")
            else (target_matrix + anchor_matrix) / 2.0
        )
        estimate = anchor_centre + (target_image - anchor_image) @ np.linalg.inv(
            average_matrix
        )
        estimates.append(estimate)
    spread = float(np.linalg.norm(estimates[0] - estimates[1]))
    expected = np.mean(estimates, axis=0)
    placement_error = float(np.linalg.norm(target_centre - expected))
    if spread > MAX_ANCHOR_SPREAD_MM:
        errors.append(f"{target}: D50/D51 estimates spread {spread:.3f} mm")
    if placement_error > MAX_PLACEMENT_ERROR_MM:
        errors.append(
            f"{target}: centre {target_centre[0]:.3f},{target_centre[1]:.3f}; "
            f"expected {expected[0]:.3f},{expected[1]:.3f}; "
            f"error {placement_error:.3f} mm"
        )
    orientation = board.FindFootprintByReference(target).GetOrientationDegrees() % 360
    expected_orientation = 0.0 if target.startswith("R") else 270.0
    if abs(orientation - expected_orientation) > 0.01:
        errors.append(
            f"{target}: orientation {orientation:.3f} is not {expected_orientation:.0f}"
        )
    summaries.append(
        f"{target} {target_centre[0]:.3f},{target_centre[1]:.3f} mm "
        f"(anchor spread {spread:.3f} mm)"
    )

if errors:
    raise SystemExit("D5/D7-D9 PHOTO PLACEMENT: FAIL\n- " + "\n- ".join(errors))
print("D5/D7-D9 PHOTO PLACEMENT: PASS — " + "; ".join(summaries))
