#!/usr/bin/env python3
"""Guard assembly-identified analog/FDC and timing parts in owner photos."""
from pathlib import Path

import numpy as np
import pcbnew

ROOT = Path(__file__).resolve().parents[1]
EXPECTED = {
    # D40 is the marked notch-right КР531ИЕ17 immediately right of D41.
    # Its centre is transferred through D41's exact raw component-side fit.
    "D40": ((258.56, 140.99), 270.0),
    # Reference identities come from СБ photo 114600417; centres come from
    # owner component photo 200418174 registered through the D102 pad field.
    "R65": ((282.21, 125.14), 90.0),
    "R67": ((295.94, 125.39), 90.0),
    "VD3": ((299.38, 128.40), 90.0),
    "R66": ((302.69, 128.46), 90.0),
    "C94": ((287.07, 132.26), 90.0),
    "C19": ((292.893, 93.574), 90.0),
    "C16": ((267.094, 101.055), 0.0),
    "R92": ((253.869, 101.194), 0.0),
    "R99": ((241.207, 103.467), 0.0),
    "C20": ((303.997, 110.024), 90.0),
    "C22": ((306.537, 110.024), 90.0),
}

EXPECTED_PAD_SETS = {
    "D40": {
        (249.67, 137.185), (252.21, 137.185), (254.75, 137.185),
        (257.29, 137.185), (259.83, 137.185), (262.37, 137.185),
        (264.91, 137.185), (267.45, 137.185),
        (249.67, 144.805), (252.21, 144.805), (254.75, 144.805),
        (257.29, 144.805), (259.83, 144.805), (262.37, 144.805),
        (264.91, 144.805), (267.45, 144.805),
    },
    "C16": {(260.844, 101.055), (273.344, 101.055)},
    "C19": {(292.893, 88.574), (292.893, 98.574)},
    "R92": {(248.789, 101.194), (258.949, 101.194)},
    "R99": {(236.127, 103.467), (246.287, 103.467)},
    "C20": {(303.997, 105.024), (303.997, 115.024)},
    "C22": {(306.537, 105.024), (306.537, 115.024)},
}


def main() -> None:
    board = pcbnew.LoadBoard(str(ROOT / "kicad/juku.kicad_pcb"))
    errors = []
    for refdes, (expected, expected_angle) in EXPECTED.items():
        footprint = board.FindFootprintByReference(refdes)
        centre = footprint.GetBoundingBox(False, False).GetCenter()
        actual = np.array([pcbnew.ToMM(centre.x), pcbnew.ToMM(centre.y)])
        residual = float(np.linalg.norm(actual - np.array(expected)))
        angle_error = abs((footprint.GetOrientationDegrees() - expected_angle + 180) % 360 - 180)
        print(f"{refdes}: centre residual {residual:.3f} mm; angle {footprint.GetOrientationDegrees():.1f}")
        if residual > 0.02:
            errors.append(f"{refdes} centre residual {residual:.3f} mm")
        if angle_error > 0.01:
            errors.append(f"{refdes} angle {footprint.GetOrientationDegrees():.1f}, expected {expected_angle:.1f}")
        if refdes in EXPECTED_PAD_SETS:
            actual_pads = {
                (round(pcbnew.ToMM(pad.GetPosition().x), 3),
                 round(pcbnew.ToMM(pad.GetPosition().y), 3))
                for pad in footprint.Pads()
            }
            if actual_pads != EXPECTED_PAD_SETS[refdes]:
                errors.append(
                    f"{refdes} pad centres {sorted(actual_pads)} != "
                    f"{sorted(EXPECTED_PAD_SETS[refdes])}"
                )
    if errors:
        raise SystemExit("analog photo placement FAIL\n- " + "\n- ".join(errors))
    print("analog photo placement PASS")


if __name__ == "__main__":
    main()
