#!/usr/bin/env python3
"""Guard the D5.26-side A19 factory-wire surface landing."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pcbnew


ROOT = Path(__file__).resolve().parents[1]
BOARD = ROOT / "kicad/juku.kicad_pcb"
LANDINGS = ROOT / "ref/photos/dgsh5-109-009-sb/factory-wire-landing-registration.json"
LOCAL_REPORT = ROOT / "docs/photo-registration/local-packages/report.json"
MAX_COORDINATE_ERROR_MM = 0.002


landing_document = json.loads(LANDINGS.read_text(encoding="utf-8"))
point = next(record for record in landing_document["points"] if record["point"] == 19)
endpoint = next(item for item in point["endpoints"] if item["terminal"] == "A19A")
evidence = endpoint.get("board_fit_evidence", {})
local_document = json.loads(LOCAL_REPORT.read_text(encoding="utf-8"))
d5_fit = next(
    fit
    for fit in local_document["fits"]
    if fit["refdes"] == "D5" and fit["side"] == "component"
)
errors: list[str] = []
if evidence.get("source_image") != d5_fit["image"]:
    errors.append("A19A board-fit image does not match the D5 component fit")
if evidence.get("joint_px") != [1218, 1593]:
    errors.append("A19A raw white-wire joint coordinate is not guarded")
if evidence.get("pin_px") != [1214, 1480]:
    errors.append("A19A D5.26 trace-origin coordinate is not guarded")

board = pcbnew.LoadBoard(str(BOARD))
d5 = board.FindFootprintByReference("D5")
if d5 is None:
    raise SystemExit("D5 FACTORY LANDING: D5 footprint missing")
pins = ("1", "14", "15")
image_matrix = np.array(
    [
        [*map(float, d5_fit["projected_pins"][pin]), 1.0]
        for pin in pins
    ]
)
board_x = np.array(
    [pcbnew.ToMM(d5.FindPadByNumber(pin).GetPosition().x) for pin in pins]
)
board_y = np.array(
    [pcbnew.ToMM(d5.FindPadByNumber(pin).GetPosition().y) for pin in pins]
)
image_to_board = np.vstack(
    [np.linalg.solve(image_matrix, board_x), np.linalg.solve(image_matrix, board_y)]
)
joint = np.array([1218.0, 1593.0, 1.0])
projected = image_to_board @ joint
recorded = np.array(endpoint["board_mm"], dtype=float)
coordinate_error = float(np.linalg.norm(projected - recorded))
if coordinate_error > MAX_COORDINATE_ERROR_MM:
    errors.append(f"A19A projected-coordinate error {coordinate_error:.4f} mm")

pin26 = d5.FindPadByNumber("26")
if pin26 is None or pin26.GetNetname() != "MEMW":
    errors.append("D5.26 is missing or is not on MEMW")
    trace_length = 0.0
else:
    pin_position = np.array(
        [pcbnew.ToMM(pin26.GetPosition().x), pcbnew.ToMM(pin26.GetPosition().y)]
    )
    trace_length = float(np.linalg.norm(projected - pin_position))
    if not 5.0 <= trace_length <= 5.3:
        errors.append(f"A19A-to-D5.26 visible span {trace_length:.3f} mm is implausible")
island = endpoint.get("island_assignment", "")
if "D5.26" not in island or "MEMW" not in island:
    errors.append("A19A island assignment lacks D5.26/MEMW")
uncertainty = evidence.get("uncertainty_mm")
if not isinstance(uncertainty, (int, float)) or not 0.5 <= uncertainty <= 0.8:
    errors.append("A19A local-fit uncertainty is invalid")
proof = evidence.get("proof", "")
if "113 px" not in proof or "D5.26" not in proof:
    errors.append("A19A proof does not guard the visible local copper segment")

if errors:
    raise SystemExit("D5 FACTORY LANDING: FAIL\n- " + "\n- ".join(errors))
print(
    "D5 FACTORY LANDING: PASS — A19A/D5.26 board-fitted at "
    f"{recorded[0]:.3f},{recorded[1]:.3f} mm; visible span {trace_length:.3f} mm"
)
