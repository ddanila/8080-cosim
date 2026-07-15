#!/usr/bin/env python3
"""Guard both printed A7/A14 factory-wire landing pairs."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pcbnew


ROOT = Path(__file__).resolve().parents[1]
BOARD = ROOT / "kicad/juku.kicad_pcb"
LANDINGS = ROOT / "ref/photos/dgsh5-109-009-sb/factory-wire-landing-registration.json"
REPORT = ROOT / "docs/photo-registration/local-packages/report.json"
PANORAMA = ROOT / "docs/photo-registration/panorama-registration.json"
BOARD_REGISTRATION = ROOT / "docs/photo-registration/board-registration.json"
D1_IMAGE = "ref/photos/juku-pcb-2/PXL_20260710_200527310.jpg"
EXPECTED = {
    7: {
        "net": "PHI1",
        "owner_pins": (("D1", "22"), ("D35", "10")),
        "chord_range": (246.0, 249.0),
        "endpoints": {
            "A7A": {"joint": [3151, 2671], "fit": "D1/global", "uncertainty": (1.5, 2.2)},
            "A7B": {"joint": [1774, 552], "fit": "D40/local", "uncertainty": (0.4, 0.8)},
        },
    },
    14: {
        "net": "PHI2",
        "owner_pins": (("D1", "15"), ("D35", "12")),
        "chord_range": (235.0, 238.0),
        "endpoints": {
            "A14A": {"joint": [2961, 2672], "fit": "D1/global", "uncertainty": (1.5, 2.2)},
            "A14B": {"joint": [1837, 510], "fit": "D40/local", "uncertainty": (0.4, 0.8)},
        },
    },
}

board = pcbnew.LoadBoard(str(BOARD))
document = json.loads(LANDINGS.read_text(encoding="utf-8"))
points = {record["point"]: record for record in document["points"]}
report = json.loads(REPORT.read_text(encoding="utf-8"))
fits = {
    (item["refdes"], item["side"]): item
    for item in report["fits"]
    if (item["refdes"], item["side"]) in {("D1", "solder"), ("D40", "solder-alt")}
}
errors: list[str] = []


def package_image_to_board(refdes: str, side: str) -> np.ndarray:
    footprint = board.FindFootprintByReference(refdes)
    fit = fits[(refdes, side)]
    image_points: list[list[float]] = []
    board_points: list[list[float]] = []
    for pin, image_point in fit["projected_pins"].items():
        pad = footprint.FindPadByNumber(pin)
        position = pad.GetPosition()
        image_points.append([*map(float, image_point), 1.0])
        board_points.append([pcbnew.ToMM(position.x), pcbnew.ToMM(position.y)])
    return np.linalg.lstsq(
        np.array(image_points), np.array(board_points), rcond=None
    )[0]


def d1_global_image_to_board() -> np.ndarray:
    panorama = json.loads(PANORAMA.read_text(encoding="utf-8"))
    registration = json.loads(BOARD_REGISTRATION.read_text(encoding="utf-8"))
    original_to_panorama = np.array(
        panorama["groups"]["solder_grid"]["images"][D1_IMAGE][
            "original_to_panorama_homography"
        ]
    ).reshape(3, 3)
    board_to_panorama = np.array(
        registration["groups"]["solder_grid"]["board_to_panorama_homography"]
    ).reshape(3, 3)
    held_out = registration["groups"]["solder_grid"]["max_held_out_error_px"]
    if not 7.0 <= held_out <= 7.8:
        errors.append(f"solder-grid held-out error drifted to {held_out:.3f} px")
    return np.linalg.inv(board_to_panorama) @ original_to_panorama


d40_transform = package_image_to_board("D40", "solder-alt")
d1_transform = d1_global_image_to_board()
projected: dict[str, np.ndarray] = {}

for number, expected in EXPECTED.items():
    point = points[number]
    endpoints = {item["terminal"]: item for item in point["endpoints"]}
    if point.get("status") != "board-fitted":
        errors.append(f"A{number} point is not fully board-fitted")
    if "cut length" not in point.get("observation", ""):
        errors.append(f"A{number} approximate-length disposition is absent")

    for terminal, endpoint_expected in expected["endpoints"].items():
        endpoint = endpoints[terminal]
        joint = endpoint_expected["joint"]
        if endpoint_expected["fit"] == "D1/global":
            homogeneous = d1_transform @ np.array([*map(float, joint), 1.0])
            value = homogeneous[:2] / homogeneous[2]
            source_image = D1_IMAGE
            local_fit = "D1/solder + solder-grid global registration"
        else:
            value = np.array([*map(float, joint), 1.0]) @ d40_transform
            source_image = fits[("D40", "solder-alt")]["image"]
            local_fit = "D40/solder-alt"
        projected[terminal] = value
        recorded = np.array(endpoint.get("board_mm"), dtype=float)
        if float(np.linalg.norm(value - recorded)) > 0.002:
            errors.append(f"{terminal} recorded coordinate drifted")
        evidence = endpoint.get("board_fit_evidence", {})
        if evidence.get("source_image") != source_image:
            errors.append(f"{terminal} source image is not guarded")
        if evidence.get("joint_px") != joint:
            errors.append(f"{terminal} joint pixel is not guarded")
        if evidence.get("local_fit") != local_fit:
            errors.append(f"{terminal} fit provenance is not guarded")
        low, high = endpoint_expected["uncertainty"]
        uncertainty = evidence.get("uncertainty_mm")
        if not isinstance(uncertainty, (int, float)) or not low <= uncertainty <= high:
            errors.append(f"{terminal} fitted uncertainty is invalid")
        assignment = endpoint.get("island_assignment", "")
        if f"printed {number}" not in assignment or expected["net"] not in assignment:
            errors.append(f"{terminal} printed-point/net assignment is absent")

    for refdes, pin in expected["owner_pins"]:
        owner = board.FindFootprintByReference(refdes).FindPadByNumber(pin)
        if owner is None or owner.GetNetname() != expected["net"]:
            errors.append(f"{refdes}.{pin} is not on {expected['net']}")

    chord = float(np.linalg.norm(
        projected[f"A{number}A"] - projected[f"A{number}B"]
    ))
    low, high = expected["chord_range"]
    if not low <= chord <= high:
        errors.append(f"A{number} terminal chord {chord:.3f} mm is implausible")

left_separation = float(np.linalg.norm(projected["A7A"] - projected["A14A"]))
right_separation = float(np.linalg.norm(projected["A7B"] - projected["A14B"]))
if not 8.5 <= left_separation <= 9.0:
    errors.append(f"D1-side printed-joint separation {left_separation:.3f} mm is implausible")
if not 3.0 <= right_separation <= 3.5:
    errors.append(f"D35-side printed-joint separation {right_separation:.3f} mm is implausible")

if errors:
    raise SystemExit("A7/A14 FACTORY LANDINGS: FAIL\n- " + "\n- ".join(errors))
print(
    "A7/A14 FACTORY LANDINGS: PASS — "
    f"A7 {np.linalg.norm(projected['A7A']-projected['A7B']):.3f} mm; "
    f"A14 {np.linalg.norm(projected['A14A']-projected['A14B']):.3f} mm; "
    f"left/right separation {left_separation:.3f}/{right_separation:.3f} mm"
)
