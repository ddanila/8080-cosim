#!/usr/bin/env python3
"""Guard the D5-side A8/STSTB joint and the explicit cut-length hold."""
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


board = pcbnew.LoadBoard(str(BOARD))
landing_document = json.loads(LANDINGS.read_text(encoding="utf-8"))
point = next(record for record in landing_document["points"] if record["point"] == 8)
endpoints = {item["terminal"]: item for item in point["endpoints"]}
fit = next(
    item
    for item in json.loads(LOCAL_REPORT.read_text(encoding="utf-8"))["fits"]
    if item["refdes"] == "D5" and item["side"] == "component"
)
d5 = board.FindFootprintByReference("D5")
errors: list[str] = []

image_points: list[list[float]] = []
board_points: list[list[float]] = []
for pin, image_point in fit["projected_pins"].items():
    pad = d5.FindPadByNumber(pin)
    position = pad.GetPosition()
    image_points.append([*map(float, image_point), 1.0])
    board_points.append([pcbnew.ToMM(position.x), pcbnew.ToMM(position.y)])
transform = np.linalg.lstsq(
    np.array(image_points), np.array(board_points), rcond=None
)[0]

a8a = endpoints["A8A"]
evidence = a8a.get("board_fit_evidence", {})
guarded = {
    "source_image": fit["image"],
    "joint_px": [1335, 1103],
    "pin_px": [1322, 1145],
}
for key, value in guarded.items():
    if evidence.get(key) != value:
        errors.append(f"A8A: {key} is not guarded")
uncertainty = evidence.get("uncertainty_mm")
if not isinstance(uncertainty, (int, float)) or not 0.4 <= uncertainty <= 0.8:
    errors.append("A8A: invalid fitted uncertainty")
if "42 px" not in evidence.get("proof", "") or "D5.1" not in evidence.get("proof", ""):
    errors.append("A8A: proof does not guard the visible D5.1 copper spur")
projected = np.array([1335.0, 1103.0, 1.0]) @ transform
recorded = np.array(a8a["board_mm"], dtype=float)
coordinate_error = float(np.linalg.norm(projected - recorded))
if coordinate_error > MAX_COORDINATE_ERROR_MM:
    errors.append(f"A8A: recorded-coordinate error {coordinate_error:.4f} mm")

pad = d5.FindPadByNumber("1")
if pad is None or pad.GetNetname() != "STSTB":
    errors.append("D5.1 is missing from STSTB")
else:
    position = pad.GetPosition()
    pad_position = np.array([pcbnew.ToMM(position.x), pcbnew.ToMM(position.y)])
    copper_span = float(np.linalg.norm(recorded - pad_position))
    if not 1.9 <= copper_span <= 2.1:
        errors.append(f"A8A: local copper span {copper_span:.3f} mm is implausible")
if "D5.1" not in a8a.get("island_assignment", "") or "STSTB" not in a8a.get("island_assignment", ""):
    errors.append("A8A: island assignment lacks D5.1/STSTB")

a8b = np.array(endpoints["A8B"]["board_mm"], dtype=float)
wire_chord = float(np.linalg.norm(a8b - recorded))
if not 195.0 <= wire_chord <= 197.0:
    errors.append(f"A8: fitted terminal chord {wire_chord:.3f} mm is unexpected")
if "cut length" not in point.get("observation", ""):
    errors.append("A8: 19 cm cut-length discrepancy is not explicit")
if point.get("status") != "board-fitted":
    errors.append("A8: point status is not board-fitted")

if errors:
    raise SystemExit("A8 FACTORY LANDINGS: FAIL\n- " + "\n- ".join(errors))
print(
    "A8 FACTORY LANDINGS: PASS — A8A/D5.1 board-fitted; "
    f"terminal chord {wire_chord:.3f} mm; 19 cm cut length remains held"
)
