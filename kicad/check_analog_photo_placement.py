#!/usr/bin/env python3
"""Guard assembly-identified analog/FDC and timing parts in owner photos."""
import csv
import hashlib
import json
from pathlib import Path

import numpy as np
import pcbnew

ROOT = Path(__file__).resolve().parents[1]
C94_EVIDENCE = ROOT / "ref/photos/juku-pcb-2/c94-endpoint-registration.json"
R67_EVIDENCE = ROOT / "ref/photos/juku-pcb-2/r67-photo-exhaustion.json"
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
    "C94": {(287.07, 129.76), (287.07, 134.76)},
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
    c94 = board.FindFootprintByReference("C94")
    c94_nets = {pad.GetNumber(): pad.GetNetname() for pad in c94.Pads()}
    if c94_nets != {"1": "C94_1_BOUNDARY", "2": "VIDEO_OUT"}:
        errors.append(f"C94 pad nets {c94_nets} do not preserve the photo-proved VIDEO_OUT join")

    evidence = json.loads(C94_EVIDENCE.read_text(encoding="utf-8"))
    if evidence.get("joined_endpoints") != ["C94.2", "R65.1"] or evidence.get("net") != "VIDEO_OUT":
        errors.append("C94 endpoint evidence does not guard the C94.2/R65.1 join")
    if evidence.get("unresolved") != ["C94.1 remote destination"]:
        errors.append("C94 endpoint evidence does not preserve the C94.1 boundary")
    observations = evidence.get("component_observations", [])
    if len(observations) != 3:
        errors.append("C94 endpoint evidence needs three independent component observations")
    for item in [evidence.get("factory_identity", {}), *observations,
                 evidence.get("solder_observation", {})]:
        source = ROOT / item.get("source", "")
        if (not source.is_file() or
                hashlib.sha256(source.read_bytes()).hexdigest() != item.get("sha256")):
            errors.append(f"C94 evidence source/hash mismatch: {source}")
        bbox = item.get("bbox_px")
        if bbox is not None and (len(bbox) != 4 or bbox[0] >= bbox[2] or bbox[1] >= bbox[3]):
            errors.append(f"C94 evidence has invalid review box: {source}")

    r67 = json.loads(R67_EVIDENCE.read_text(encoding="utf-8"))
    if (r67.get("refdes") != "R67" or r67.get("endpoint") != "2" or
            r67.get("unresolved") != ["R67.2 remote destination"]):
        errors.append("R67 photo-exhaustion record does not preserve the R67.2 boundary")
    cross_side = r67.get("cross_side_registration", {})
    if (cross_side.get("projected_solder_joint_px") != [916, 988] or
            cross_side.get("max_anchor_residual_px", 1) > 0.001):
        errors.append("R67 D102-local cross-side registration is stale")
    endpoint_rows = {}
    with (ROOT / "ref/photos/juku-pcb-2/endpoints.csv").open(newline="") as stream:
        for row in csv.DictReader(stream):
            endpoint_rows[row["endpoint_id"]] = row
    pairs = []
    for pin in range(1, 17):
        component = endpoint_rows.get(f"seed-component-D102-{pin}")
        solder = endpoint_rows.get(f"seed-solder-D102-{pin}")
        if component and solder:
            pairs.append((component, solder))
    if len(pairs) != 14:
        errors.append(f"R67 cross-side fit has {len(pairs)} paired D102 anchors, expected 14")
    else:
        component_points = np.array([
            [float(a["x_px"]), float(a["y_px"]), 1.0] for a, _ in pairs
        ])
        solder_points = np.array([
            [float(b["x_px"]), float(b["y_px"])] for _, b in pairs
        ])
        transform, *_ = np.linalg.lstsq(component_points, solder_points, rcond=None)
        residual = float(np.linalg.norm(component_points @ transform - solder_points, axis=1).max())
        recorded = np.array(cross_side.get("transform", []))
        projected = np.array([3321.0, 1698.0, 1.0]) @ transform
        if (recorded.shape != (6,) or not np.allclose(recorded, transform.flatten(), atol=1e-6) or
                residual > 0.001 or not np.allclose(projected, [916, 988], atol=0.5)):
            errors.append("R67 cross-side transform no longer reproduces its D102 anchors/projection")
    r67_items = [*r67.get("component_observations", []), *r67.get("solder_observations", [])]
    if len(r67.get("component_observations", [])) != 2 or len(r67.get("solder_observations", [])) != 2:
        errors.append("R67 photo exhaustion needs two component and two solder observations")
    for item in r67_items:
        source = ROOT / item.get("source", "")
        if (not source.is_file() or
                hashlib.sha256(source.read_bytes()).hexdigest() != item.get("sha256")):
            errors.append(f"R67 evidence source/hash mismatch: {source}")
        bbox = item.get("bbox_px", [])
        if len(bbox) != 4 or bbox[0] >= bbox[2] or bbox[1] >= bbox[3]:
            errors.append(f"R67 evidence has invalid review box: {source}")
    if errors:
        raise SystemExit("analog photo placement FAIL\n- " + "\n- ".join(errors))
    print("analog photo placement PASS")


if __name__ == "__main__":
    main()
