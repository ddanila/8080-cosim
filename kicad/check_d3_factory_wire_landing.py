#!/usr/bin/env python3
"""Guard both A20 factory-wire landings from local and panorama evidence."""
from __future__ import annotations

import cmath
import json
import math
from pathlib import Path

import numpy as np
import pcbnew


ROOT = Path(__file__).resolve().parents[1]
BOARD = ROOT / "kicad/juku.kicad_pcb"
LANDINGS = (
    ROOT / "ref/photos/dgsh5-109-009-sb/factory-wire-landing-registration.json"
)
LOCAL_REPORT = ROOT / "docs/photo-registration/local-packages/report.json"
PANORAMA_REPORT = ROOT / "docs/photo-registration/panorama-registration.json"
BOARD_REGISTRATION = ROOT / "docs/photo-registration/board-registration.json"
MAX_COORDINATE_ERROR_MM = 0.002
MAX_RECORDED_PROJECTION_ERROR_PX = 0.15
MAX_JOINT_PROJECTION_ERROR_PX = 7.0


def pad_centre(board: pcbnew.BOARD, refdes: str) -> complex:
    footprint = board.FindFootprintByReference(refdes)
    if footprint is None:
        raise SystemExit(f"D3 FACTORY LANDING: missing {refdes}")
    pads = list(footprint.Pads())
    return complex(
        sum(pcbnew.ToMM(pad.GetPosition().x) for pad in pads) / len(pads),
        sum(pcbnew.ToMM(pad.GetPosition().y) for pad in pads) / len(pads),
    )


def project(matrix: np.ndarray, point: tuple[float, float]) -> np.ndarray:
    value = matrix @ np.array([point[0], point[1], 1.0])
    return value[:2] / value[2]


landing_document = json.loads(LANDINGS.read_text(encoding="utf-8"))
point_record = next(
    record for record in landing_document["points"] if record["point"] == 20
)
a20a = next(
    item for item in point_record["endpoints"] if item["terminal"] == "A20A"
)
a20b = next(
    item for item in point_record["endpoints"] if item["terminal"] == "A20B"
)
local_document = json.loads(LOCAL_REPORT.read_text(encoding="utf-8"))
d3_fit = next(
    fit
    for fit in local_document["fits"]
    if fit["refdes"] == "D3" and fit["side"] == "component"
)

evidence = a20b.get("board_fit_evidence", {})
errors: list[str] = []
if evidence.get("source_image") != d3_fit["image"]:
    errors.append("board-fit image does not match the D3 component fit")
joint = evidence.get("joint_px")
if not isinstance(joint, list) or joint != [1232, 872]:
    errors.append("raw white-wire joint coordinate is not guarded")
    joint = [0, 0]
if evidence.get("pin_px") != [1296, 858]:
    errors.append("D3.10 trace destination coordinate is not guarded")

image_points = list(d3_fit["projected_pins"].values())
image_centre = complex(
    sum(point[0] for point in image_points) / len(image_points),
    sum(point[1] for point in image_points) / len(image_points),
)
factor = cmath.rect(
    float(d3_fit["scale_px_per_mm"]),
    math.radians(float(d3_fit["rotation_deg"])),
)
board = pcbnew.LoadBoard(str(BOARD))
projected = pad_centre(board, "D3") + (complex(*joint) - image_centre) / factor
a20b_recorded = complex(*map(float, a20b["board_mm"]))
coordinate_error = abs(projected - a20b_recorded)
if coordinate_error > MAX_COORDINATE_ERROR_MM:
    errors.append(f"projected-coordinate error {coordinate_error:.4f} mm")

island = a20b.get("island_assignment", "")
if "D3.10" not in island or "S_TTL" not in island:
    errors.append("island assignment lacks D3.10/S_TTL")
uncertainty = evidence.get("uncertainty_mm")
if not isinstance(uncertainty, (int, float)) or not 0.4 <= uncertainty <= 0.8:
    errors.append("invalid local-fit uncertainty")

pin10 = board.FindFootprintByReference("D3").FindPadByNumber("10")
pin10_position = complex(
    pcbnew.ToMM(pin10.GetPosition().x), pcbnew.ToMM(pin10.GetPosition().y)
)
trace_length = abs(a20b_recorded - pin10_position)
if not 2.5 <= trace_length <= 3.5:
    errors.append(f"joint-to-D3.10 local span {trace_length:.3f} mm is implausible")

# The other end is the existing A23 through-hole cable landing. Three
# component views put the entering white wire over A23 beneath the same mastic
# blob; two reflected solder views independently show the third-from-right
# A23 joint and no alternate copper departure.
a23 = board.FindFootprintByReference("A23")
a23_pad = a23.FindPadByNumber("1") if a23 else None
if a23_pad is None:
    errors.append("A23.1 PCB landing is missing")
    a23_position = 0j
else:
    a23_position = complex(
        pcbnew.ToMM(a23_pad.GetPosition().x),
        pcbnew.ToMM(a23_pad.GetPosition().y),
    )
    if a23_pad.GetNetname() != "S_TTL":
        errors.append(f"A23.1 net {a23_pad.GetNetname()!r} is not S_TTL")

a20a_recorded = complex(*map(float, a20a["board_mm"]))
if abs(a20a_recorded - a23_position) > MAX_COORDINATE_ERROR_MM:
    errors.append("A20A coordinate does not coincide with A23.1")
a20a_island = a20a.get("island_assignment", "")
if not all(token in a20a_island for token in ("A23.1", "X3.3", "S_TTL")):
    errors.append("A20A island assignment lacks A23.1/X3.3/S_TTL")

a20a_evidence = a20a.get("board_fit_evidence", {})
component_records = a20a_evidence.get("component_projections", [])
solder_records = a20a_evidence.get("solder_observations", [])
if len(component_records) != 3 or len(solder_records) != 2:
    errors.append("A20A needs three component and two solder observations")

panorama = json.loads(PANORAMA_REPORT.read_text(encoding="utf-8"))
board_registration = json.loads(BOARD_REGISTRATION.read_text(encoding="utf-8"))
for group, records in (
    ("component_grid", component_records),
    ("solder_grid", solder_records),
):
    board_h = np.array(
        board_registration["groups"][group]["board_to_panorama_homography"]
    ).reshape(3, 3)
    panorama_point = project(
        board_h, (a23_position.real, a23_position.imag)
    )
    for record in records:
        image = record.get("source_image", "")
        image_entry = panorama["groups"][group]["images"].get(image)
        if image_entry is None:
            errors.append(f"A20A references unregistered {group} image {image!r}")
            continue
        image_h = np.array(
            image_entry["original_to_panorama_homography"]
        ).reshape(3, 3)
        expected_px = project(np.linalg.inv(image_h), panorama_point)
        recorded_px = np.array(record.get("projected_px", []), dtype=float)
        if recorded_px.shape != (2,):
            errors.append(f"A20A {image} lacks a two-coordinate projection")
            continue
        projection_error = float(np.linalg.norm(expected_px - recorded_px))
        if projection_error > MAX_RECORDED_PROJECTION_ERROR_PX:
            errors.append(
                f"A20A {image} projection residual {projection_error:.3f} px"
            )
        observation = record.get("observation", "").lower()
        if group == "component_grid":
            if "mastic" not in observation:
                errors.append(f"A20A {image} does not guard the mastic occlusion")
        else:
            joint_px = np.array(record.get("joint_px", []), dtype=float)
            if joint_px.shape != (2,):
                errors.append(f"A20A {image} lacks a solder-joint coordinate")
                continue
            joint_error = float(np.linalg.norm(expected_px - joint_px))
            if joint_error > MAX_JOINT_PROJECTION_ERROR_PX:
                errors.append(
                    f"A20A {image} joint residual {joint_error:.3f} px"
                )
            if "no solder-side copper departure" not in observation:
                errors.append(f"A20A {image} does not guard the isolated joint")

a20a_uncertainty = a20a_evidence.get("uncertainty_mm")
if (
    not isinstance(a20a_uncertainty, (int, float))
    or not 0.4 <= a20a_uncertainty <= 0.8
):
    errors.append("A20A has invalid panorama-fit uncertainty")

if errors:
    raise SystemExit("A20 FACTORY LANDINGS: FAIL\n- " + "\n- ".join(errors))
print(
    "A20 FACTORY LANDINGS: PASS — "
    f"A20A/A23.1 {a20a_recorded.real:.3f},{a20a_recorded.imag:.3f} mm; "
    f"A20B/D3.10 {a20b_recorded.real:.3f},{a20b_recorded.imag:.3f} mm; "
    f"D3 local copper span {trace_length:.3f} mm; 4/20 terminals board-fitted"
)
