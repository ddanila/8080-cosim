#!/usr/bin/env python3
"""Guard both A19 factory-wire surface landings and its physical span."""
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
endpoints = {item["terminal"]: item for item in point["endpoints"]}
local_document = json.loads(LOCAL_REPORT.read_text(encoding="utf-8"))
fits = {
    fit["refdes"]: fit
    for fit in local_document["fits"]
    if fit["side"] == "component" and fit["refdes"] in {"D5", "D7"}
}
board = pcbnew.LoadBoard(str(BOARD))
errors: list[str] = []
w19 = board.FindFootprintByReference("W19")


def project_joint(
    terminal: str,
    refdes: str,
    fit_pins: tuple[str, str, str],
    expected_joint: list[int],
    expected_pin: list[int],
) -> np.ndarray:
    endpoint = endpoints[terminal]
    evidence = endpoint.get("board_fit_evidence", {})
    fit = fits[refdes]
    if evidence.get("source_image") != fit["image"]:
        errors.append(f"{terminal}: board-fit image does not match {refdes} fit")
    if evidence.get("joint_px") != expected_joint:
        errors.append(f"{terminal}: raw white-wire joint coordinate is not guarded")
    if evidence.get("pin_px") != expected_pin:
        errors.append(f"{terminal}: package endpoint coordinate is not guarded")
    footprint = board.FindFootprintByReference(refdes)
    image_matrix = np.array(
        [[*map(float, fit["projected_pins"][pin]), 1.0] for pin in fit_pins]
    )
    board_x = np.array(
        [pcbnew.ToMM(footprint.FindPadByNumber(pin).GetPosition().x) for pin in fit_pins]
    )
    board_y = np.array(
        [pcbnew.ToMM(footprint.FindPadByNumber(pin).GetPosition().y) for pin in fit_pins]
    )
    transform = np.vstack(
        [np.linalg.solve(image_matrix, board_x), np.linalg.solve(image_matrix, board_y)]
    )
    projected = transform @ np.array([*map(float, expected_joint), 1.0])
    recorded = np.array(endpoint["board_mm"], dtype=float)
    coordinate_error = float(np.linalg.norm(projected - recorded))
    if coordinate_error > MAX_COORDINATE_ERROR_MM:
        errors.append(f"{terminal}: projected-coordinate error {coordinate_error:.4f} mm")
    uncertainty = evidence.get("uncertainty_mm")
    if not isinstance(uncertainty, (int, float)) or not 0.5 <= uncertainty <= 0.8:
        errors.append(f"{terminal}: local-fit uncertainty is invalid")
    island = endpoint.get("island_assignment", "")
    if refdes + "." not in island or "MEMW" not in island:
        errors.append(f"{terminal}: island assignment lacks {refdes}/MEMW")
    return projected


a19a = project_joint("A19A", "D5", ("1", "14", "15"), [1218, 1593], [1214, 1480])
a19b = project_joint("A19B", "D7", ("1", "7", "8"), [3255, 1585], [3391, 1320])

d5 = board.FindFootprintByReference("D5")
d7 = board.FindFootprintByReference("D7")
for refdes, footprint, pin, expected_net in (("D5", d5, "26", "MEMW"), ("D7", d7, "2", "MEMW_D7P2")):
    pad = footprint.FindPadByNumber(pin) if footprint else None
    if pad is None or pad.GetNetname() != expected_net:
        errors.append(f"{refdes}.{pin} is missing or is not on {expected_net}")

d5_pin = d5.FindPadByNumber("26").GetPosition()
d5_pin_position = np.array([pcbnew.ToMM(d5_pin.x), pcbnew.ToMM(d5_pin.y)])
d5_trace_length = float(np.linalg.norm(a19a - d5_pin_position))
if not 5.0 <= d5_trace_length <= 5.3:
    errors.append(f"A19A-to-D5.26 visible span {d5_trace_length:.3f} mm is implausible")

wire_span = float(np.linalg.norm(a19b - a19a))
if not 94.5 <= wire_span <= 95.5:
    errors.append(f"A19 terminal span {wire_span:.3f} mm does not match ~9.5 cm")
a19b_proof = endpoints["A19B"].get("board_fit_evidence", {}).get("proof", "")
if "uninterrupted white lead" not in a19b_proof or "9.5 cm" not in a19b_proof:
    errors.append("A19B proof does not guard wire continuity/factory length")
if point.get("status") != "board-fitted":
    errors.append("A19 point status is not board-fitted")

if w19 is None:
    errors.append("A19: W19 assembly-wire footprint is missing")
else:
    for number, expected_position, expected_net in (
        ("1", a19a, "MEMW"),
        ("2", a19b, "MEMW_D7P2"),
    ):
        wire_pad = w19.FindPadByNumber(number)
        if wire_pad is None:
            errors.append(f"A19: W19.{number} landing is missing")
            continue
        position = np.array([pcbnew.ToMM(wire_pad.GetPosition().x), pcbnew.ToMM(wire_pad.GetPosition().y)])
        if float(np.linalg.norm(position - expected_position)) > MAX_COORDINATE_ERROR_MM:
            errors.append(f"A19: W19.{number} coordinate drifted")
        if wire_pad.GetNetname() != expected_net:
            errors.append(f"A19: W19.{number} is on {wire_pad.GetNetname()}, expected {expected_net}")
        size = wire_pad.GetSize()
        if abs(pcbnew.ToMM(size.x) - 1.5) > 0.001 or size.x != size.y:
            errors.append(f"A19: W19.{number} clearance-safe pad geometry drifted")
        layers = wire_pad.GetLayerSet()
        if wire_pad.GetAttribute() != pcbnew.PAD_ATTRIB_SMD or not layers.Contains(pcbnew.F_Cu) or layers.Contains(pcbnew.B_Cu):
            errors.append(f"A19: W19.{number} must remain a top-side surface landing")

if errors:
    raise SystemExit("A19 FACTORY LANDINGS: FAIL\n- " + "\n- ".join(errors))
print(
    "A19 FACTORY LANDINGS: PASS — two surface islands modeled through W19; "
    f"A19A {a19a[0]:.3f},{a19a[1]:.3f} mm; "
    f"A19B {a19b[0]:.3f},{a19b[1]:.3f} mm; "
    f"D5 local copper {d5_trace_length:.3f} mm; terminal span {wire_span:.3f} mm"
)
