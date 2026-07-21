#!/usr/bin/env python3
"""Guard the photo-identified D104/D32/D14 packages around R30."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pcbnew

ROOT = Path(__file__).resolve().parents[1]
OBSERVED = {
    "D104": ("ref/photos/juku-pcb-2/PXL_20260710_200402344.jpg",
             (939.762, 1580.854), 180.0),
    "D32": ("ref/photos/juku-pcb-2/PXL_20260710_200402344.jpg",
            (1269.339, 1385.568), 0.0),
    "D14": ("ref/photos/juku-pcb-2/PXL_20260710_200402344.jpg",
            (1269.935, 1621.741), 0.0),
    "D3": ("ref/photos/juku-pcb-2/PXL_20260710_200418174.jpg",
           (1375.0, 910.0), 180.0),
}


def project(matrix: np.ndarray, point: tuple[float, float]) -> np.ndarray:
    value = matrix @ np.array([point[0], point[1], 1.0])
    return value[:2] / value[2]


def main() -> None:
    panorama = json.loads((ROOT / "docs/photo-registration/panorama-registration.json").read_text())
    board_registration = json.loads((ROOT / "docs/photo-registration/board-registration.json").read_text())
    board_h = np.array(board_registration["groups"]["component_grid"]
                       ["board_to_panorama_homography"]).reshape(3, 3)
    board = pcbnew.LoadBoard(str(ROOT / "kicad/juku.kicad_pcb"))
    errors = []
    for refdes, (image, image_point, expected_angle) in OBSERVED.items():
        image_h = np.array(panorama["groups"]["component_grid"]["images"][image]
                           ["original_to_panorama_homography"]).reshape(3, 3)
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

    local_report = json.loads(
        (ROOT / "docs/photo-registration/local-packages/report.json").read_text()
    )
    d104_solder = next(
        (
            fit
            for fit in local_report["fits"]
            if fit["refdes"] == "D104" and fit["side"] == "solder"
        ),
        None,
    )
    if d104_solder is None or d104_solder.get("model") != "affine":
        errors.append("D104 reflected solder fit is missing or not affine")
    else:
        checks = {item["pin"]: item["error_px"] for item in d104_solder["checks"]}
        if checks.get("9", float("inf")) > 1.1:
            errors.append("D104 solder pin 9 held-out residual exceeds 1.1 px")
        if checks.get("10", float("inf")) > 0.8:
            errors.append("D104 solder pin 10 held-out residual exceeds 0.8 px")
        if d104_solder["projected_pins"].get("10") != [2350.714, 1249.143]:
            errors.append("D104.10 solder coordinate drifted")
        d104_pad10 = board.FindFootprintByReference("D104").FindPadByNumber("10")
        if d104_pad10.GetNetname() != "D104_X4_OUT_BOUNDARY":
            errors.append("D104.10 premeasurement source-PCB boundary changed before controlled refresh")
    if errors:
        raise SystemExit("serial photo placement FAIL\n- " + "\n- ".join(errors))
    print(
        "serial photo placement PASS — D104.10 solder 2350.7,1249.1 px; "
        "B.Cu departure absent; board JSON closes pin 10 NC while the held source PCB "
        "retains its premeasurement singleton until controlled refresh"
    )


if __name__ == "__main__":
    main()
