#!/usr/bin/env python3
"""Guard the C96-side A12 landing and the still-rejected D13-side end."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pcbnew


ROOT = Path(__file__).resolve().parents[1]
BOARD = ROOT / "kicad/juku.kicad_pcb"
LANDINGS = ROOT / "ref/photos/dgsh5-109-009-sb/factory-wire-landing-registration.json"
PANORAMA = ROOT / "docs/photo-registration/panorama-registration.json"
BOARD_REGISTRATION = ROOT / "docs/photo-registration/board-registration.json"
IMAGE = "ref/photos/juku-pcb-2/PXL_20260710_200530933.MP.jpg"
JOINT = [2075, 600]
OTHER_LEAD = [2170, 605]

landing_document = json.loads(LANDINGS.read_text(encoding="utf-8"))
point = next(item for item in landing_document["points"] if item["point"] == 12)
endpoints = {item["terminal"]: item for item in point["endpoints"]}
endpoint = endpoints["A12B"]
errors: list[str] = []

panorama = json.loads(PANORAMA.read_text(encoding="utf-8"))
registration = json.loads(BOARD_REGISTRATION.read_text(encoding="utf-8"))
original_to_panorama = np.array(
    panorama["groups"]["solder_grid"]["images"][IMAGE][
        "original_to_panorama_homography"
    ]
).reshape(3, 3)
board_to_panorama = np.array(
    registration["groups"]["solder_grid"]["board_to_panorama_homography"]
).reshape(3, 3)
image_to_board = np.linalg.inv(board_to_panorama) @ original_to_panorama


def project(pixel: list[int]) -> np.ndarray:
    value = image_to_board @ np.array([*map(float, pixel), 1.0])
    return value[:2] / value[2]


projected = project(JOINT)
other = project(OTHER_LEAD)
recorded = np.array(endpoint.get("board_mm"), dtype=float)
if float(np.linalg.norm(projected - recorded)) > 0.002:
    errors.append("A12B recorded coordinate drifted")
if not projected[0] > other[0]:
    errors.append("mirrored C96 lead ordering no longer puts the raw-left lead board-right")
lead_spacing = float(np.linalg.norm(projected - other))
if not 3.8 <= lead_spacing <= 4.4:
    errors.append(f"C96 lead spacing {lead_spacing:.3f} mm is implausible")

evidence = endpoint.get("board_fit_evidence", {})
if evidence.get("source_image") != IMAGE:
    errors.append("A12B source image is not guarded")
if evidence.get("joint_px") != JOINT or evidence.get("other_c96_lead_px") != OTHER_LEAD:
    errors.append("A12B C96 lead pixels are not guarded")
uncertainty = evidence.get("uncertainty_mm")
if not isinstance(uncertainty, (int, float)) or not 1.5 <= uncertainty <= 2.2:
    errors.append("A12B global-fit uncertainty is invalid")
assignment = endpoint.get("island_assignment", "")
if "D37.4" not in assignment or "RAM_OUT_EN" not in assignment or "printed 12" not in assignment:
    errors.append("A12B island assignment lacks D37.4/RAM_OUT_EN/printed-12 identity")

endpoint_a = endpoints["A12A"]
if endpoint_a.get("board_mm") is not None or endpoint_a.get("island_assignment") is not None:
    errors.append("A12A was promoted despite the guarded D13-side rejection")
observation = point.get("observation", "")
if "loose tinned wire end" not in observation or "A12A remains unidentified" not in observation:
    errors.append("A12A false-candidate disposition is absent")
if point.get("status") != "image-registered/board-fit-pending":
    errors.append("A12 must remain partial until A12A is located")

board = pcbnew.LoadBoard(str(BOARD))
owner = board.FindFootprintByReference("D37").FindPadByNumber("4")
if owner is None or owner.GetNetname() != "RAM_OUT_EN":
    errors.append("D37.4 is not on RAM_OUT_EN")

if errors:
    raise SystemExit("A12 FACTORY LANDING: FAIL\n- " + "\n- ".join(errors))
print(
    "A12 FACTORY LANDING: PASS — "
    f"A12B {projected[0]:.3f},{projected[1]:.3f} mm; "
    f"C96 lead spacing {lead_spacing:.3f} mm; A12A held"
)
