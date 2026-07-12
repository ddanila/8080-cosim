#!/usr/bin/env python3
"""Guard the first assembly-identified parts below D102 in the owner photo."""
from pathlib import Path

import numpy as np
import pcbnew

ROOT = Path(__file__).resolve().parents[1]
EXPECTED = {
    # Reference identities come from СБ photo 114600417; centres come from
    # owner component photo 200418174 registered through the D102 pad field.
    "R65": ((287.07, 132.26), 90.0),
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
    if errors:
        raise SystemExit("analog photo placement FAIL\n- " + "\n- ".join(errors))
    print("analog photo placement PASS")


if __name__ == "__main__":
    main()
