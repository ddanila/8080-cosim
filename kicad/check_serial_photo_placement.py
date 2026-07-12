#!/usr/bin/env python3
"""Guard the photo-identified D104/D32/D14 packages around R30."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pcbnew

ROOT = Path(__file__).resolve().parents[1]
IMAGE = "ref/photos/juku-pcb-2/PXL_20260710_200402344.jpg"
OBSERVED = {
    "D104": ((939.762, 1580.854), 180.0),
    "D32": ((1269.339, 1385.568), 0.0),
    "D14": ((1269.935, 1621.741), 0.0),
}


def project(matrix: np.ndarray, point: tuple[float, float]) -> np.ndarray:
    value = matrix @ np.array([point[0], point[1], 1.0])
    return value[:2] / value[2]


def main() -> None:
    panorama = json.loads((ROOT / "docs/photo-registration/panorama-registration.json").read_text())
    board_registration = json.loads((ROOT / "docs/photo-registration/board-registration.json").read_text())
    image_h = np.array(panorama["groups"]["component_grid"]["images"][IMAGE]
                       ["original_to_panorama_homography"]).reshape(3, 3)
    board_h = np.array(board_registration["groups"]["component_grid"]
                       ["board_to_panorama_homography"]).reshape(3, 3)
    board = pcbnew.LoadBoard(str(ROOT / "kicad/juku.kicad_pcb"))
    errors = []
    for refdes, (image_point, expected_angle) in OBSERVED.items():
        expected = project(np.linalg.inv(board_h), project(image_h, image_point))
        footprint = board.FindFootprintByReference(refdes)
        centre = footprint.GetBoundingBox(False, False).GetCenter()
        actual = np.array([pcbnew.ToMM(centre.x), pcbnew.ToMM(centre.y)])
        residual = float(np.linalg.norm(actual - expected))
        angle_error = abs((footprint.GetOrientationDegrees() - expected_angle + 180) % 360 - 180)
        if residual > 0.02:
            errors.append(f"{refdes} centre residual {residual:.3f} mm")
        if angle_error > 0.01:
            errors.append(f"{refdes} angle {footprint.GetOrientationDegrees():.1f}, expected {expected_angle:.1f}")
        print(f"{refdes}: centre residual {residual:.3f} mm; angle {footprint.GetOrientationDegrees():.1f}")
    if errors:
        raise SystemExit("serial photo placement FAIL\n- " + "\n- ".join(errors))
    print("serial photo placement PASS")


if __name__ == "__main__":
    main()
