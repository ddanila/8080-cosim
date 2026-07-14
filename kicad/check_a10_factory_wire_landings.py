#!/usr/bin/env python3
"""Guard both A10/W10_QA_SEL surface joints through two-sided photo fits."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pcbnew


ROOT = Path(__file__).resolve().parents[1]
BOARD = ROOT / "kicad/juku.kicad_pcb"
LANDINGS = ROOT / "ref/photos/dgsh5-109-009-sb/factory-wire-landing-registration.json"
LOCAL_REPORT = ROOT / "docs/photo-registration/local-packages/report.json"
MAX_CROSS_SIDE_ERROR_MM = 0.03
MAX_RECORDED_ERROR_MM = 0.002


board = pcbnew.LoadBoard(str(BOARD))
landing_document = json.loads(LANDINGS.read_text(encoding="utf-8"))
point = next(record for record in landing_document["points"] if record["point"] == 10)
endpoints = {item["terminal"]: item for item in point["endpoints"]}
fits_document = json.loads(LOCAL_REPORT.read_text(encoding="utf-8"))
fits = {
    (fit["refdes"], fit["side"]): fit
    for fit in fits_document["fits"]
    if fit["refdes"] in {"D41", "D50"}
}
errors: list[str] = []


def image_to_board(refdes: str, side: str) -> np.ndarray:
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


def project(transform: np.ndarray, pixel: list[int]) -> np.ndarray:
    return np.array([float(pixel[0]), float(pixel[1]), 1.0]) @ transform


expected = {
    "A10A": {
        "refdes": "D41",
        "pin": "13",
        "component_joint": [2148, 2174],
        "component_pin": [2148, 2124],
        "solder_joint": [1506, 1834],
        "solder_pin": [1506, 1785],
        "copper_span": (2.2, 2.4),
    },
    "A10B": {
        "refdes": "D50",
        "pin": "1",
        "component_joint": [2804, 2266],
        "component_pin": [2709, 2266],
        "solder_joint": [915, 2000],
        "solder_pin": [1010, 2000],
        "copper_span": (4.3, 4.5),
    },
}
projected_terminals: dict[str, np.ndarray] = {}
for terminal, specification in expected.items():
    endpoint = endpoints[terminal]
    evidence = endpoint.get("board_fit_evidence", {})
    refdes = specification["refdes"]
    component_fit = fits[(refdes, "component")]
    solder_fit = fits[(refdes, "solder")]
    guarded = {
        "source_image": component_fit["image"],
        "joint_px": specification["component_joint"],
        "pin_px": specification["component_pin"],
        "solder_image": solder_fit["image"],
        "solder_joint_px": specification["solder_joint"],
        "solder_pin_px": specification["solder_pin"],
    }
    for key, value in guarded.items():
        if evidence.get(key) != value:
            errors.append(f"{terminal}: {key} is not guarded")

    component = project(
        image_to_board(refdes, "component"), specification["component_joint"]
    )
    solder = project(
        image_to_board(refdes, "solder"), specification["solder_joint"]
    )
    cross_side_error = float(np.linalg.norm(component - solder))
    if cross_side_error > MAX_CROSS_SIDE_ERROR_MM:
        errors.append(
            f"{terminal}: component/solder projections differ by "
            f"{cross_side_error:.4f} mm"
        )
    averaged = (component + solder) / 2.0
    recorded = np.array(endpoint["board_mm"], dtype=float)
    recorded_error = float(np.linalg.norm(averaged - recorded))
    if recorded_error > MAX_RECORDED_ERROR_MM:
        errors.append(f"{terminal}: recorded-coordinate error {recorded_error:.4f} mm")
    projected_terminals[terminal] = recorded

    footprint = board.FindFootprintByReference(refdes)
    pad = footprint.FindPadByNumber(specification["pin"])
    if pad is None or pad.GetNetname() != "W10_QA_SEL":
        errors.append(f"{refdes}.{specification['pin']}: missing from W10_QA_SEL")
    else:
        pad_position = np.array(
            [pcbnew.ToMM(pad.GetPosition().x), pcbnew.ToMM(pad.GetPosition().y)]
        )
        copper_span = float(np.linalg.norm(recorded - pad_position))
        low, high = specification["copper_span"]
        if not low <= copper_span <= high:
            errors.append(
                f"{terminal}: local copper span {copper_span:.3f} mm is implausible"
            )
    island = endpoint.get("island_assignment", "")
    if f"{refdes}.{specification['pin']}" not in island or "W10_QA_SEL" not in island:
        errors.append(f"{terminal}: island assignment lacks endpoint/net")
    uncertainty = evidence.get("uncertainty_mm")
    if not isinstance(uncertainty, (int, float)) or not 0.2 <= uncertainty <= 0.5:
        errors.append(f"{terminal}: invalid fitted uncertainty")

wire_chord = float(
    np.linalg.norm(projected_terminals["A10A"] - projected_terminals["A10B"])
)
if not 131.0 <= wire_chord <= 132.0:
    errors.append(f"A10: terminal chord {wire_chord:.3f} mm is implausible")
if wire_chord > 135.0:
    errors.append("A10: terminal chord exceeds corrected 13.5 cm conductor length")
if point.get("status") != "board-fitted":
    errors.append("A10: point status is not board-fitted")
if "13.5 cm" not in point.get("observation", ""):
    errors.append("A10: corrected duplicate-sheet length is not guarded")

if errors:
    raise SystemExit("A10 FACTORY LANDINGS: FAIL\n- " + "\n- ".join(errors))
print(
    "A10 FACTORY LANDINGS: PASS — "
    f"D41/D50 cross-side fits; terminal chord {wire_chord:.3f} mm; "
    "corrected factory length 13.5 cm"
)
