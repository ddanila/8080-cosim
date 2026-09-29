#!/usr/bin/env python3
"""Guard A12 drawing marks and unpromoted C96-area solder candidates."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
LANDINGS = ROOT / "ref/photos/dgsh5-109-009-sb/factory-wire-landing-registration.json"
PANORAMA = ROOT / "docs/photo-registration/panorama-registration.json"
BOARD_REGISTRATION = ROOT / "docs/photo-registration/board-registration.json"
IMAGE = "ref/photos/juku-pcb-2/PXL_20260710_200530933.MP.jpg"
JOINT = [2075, 600]
OTHER_JOINT = [2170, 605]

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
other = project(OTHER_JOINT)
if endpoint.get("board_mm") is not None or endpoint.get("island_assignment") is not None:
    errors.append("A12B candidate was promoted without a visible wire landing")
if not projected[0] > other[0]:
    errors.append("mirrored joint ordering no longer puts the raw-left joint board-right")
joint_spacing = float(np.linalg.norm(projected - other))
if not 3.8 <= joint_spacing <= 4.4:
    errors.append(f"candidate joint spacing {joint_spacing:.3f} mm is implausible")

evidence = endpoint.get("candidate_joint_evidence", {})
if evidence.get("source_image") != IMAGE:
    errors.append("A12B candidate source image is not guarded")
if evidence.get("joint_px") != JOINT or evidence.get("other_candidate_joint_px") != OTHER_JOINT:
    errors.append("A12B candidate joint pixels are not guarded")
uncertainty = evidence.get("uncertainty_mm")
if not isinstance(uncertainty, (int, float)) or not 1.5 <= uncertainty <= 2.2:
    errors.append("A12B global-fit uncertainty is invalid")
if "neither has a visible wire termination" not in evidence.get("observation", ""):
    errors.append("candidate evidence omits the visible-wire limitation")

endpoint_a = endpoints["A12A"]
if endpoint_a.get("board_mm") is not None or endpoint_a.get("island_assignment") is not None:
    errors.append("A12A was promoted despite the guarded D13-side rejection")
observation = point.get("observation", "")
if "loose tinned wire end" not in observation or "A12A remains unidentified" not in observation:
    errors.append("A12A false-candidate disposition is absent")
if point.get("status") != "image-registered/board-fit-pending":
    errors.append("A12 must remain partial until both board landings are located")

if errors:
    raise SystemExit("A12 FACTORY LANDING: FAIL\n- " + "\n- ".join(errors))
print(
    "A12 FACTORY LANDING: PASS — "
    f"candidate joints {projected[0]:.3f},{projected[1]:.3f} and "
    f"{other[0]:.3f},{other[1]:.3f} mm; "
    f"spacing {joint_spacing:.3f} mm; both A12 ends held"
)
