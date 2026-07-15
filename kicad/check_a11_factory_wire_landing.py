#!/usr/bin/env python3
"""Guard the D92-side A11/MEMR surface landing through two local fits."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pcbnew


ROOT = Path(__file__).resolve().parents[1]
BOARD = ROOT / "kicad/juku.kicad_pcb"
LANDINGS = ROOT / "ref/photos/dgsh5-109-009-sb/factory-wire-landing-registration.json"
REPORT = ROOT / "docs/photo-registration/local-packages/report.json"
JOINT_A = [1825, 1706]
JOINT_B = [2620, 1764]

board = pcbnew.LoadBoard(str(BOARD))
landing_document = json.loads(LANDINGS.read_text(encoding="utf-8"))
point = next(record for record in landing_document["points"] if record["point"] == 11)
endpoints = {item["terminal"]: item for item in point["endpoints"]}
endpoint = endpoints["A11B"]
report = json.loads(REPORT.read_text(encoding="utf-8"))
fits = {
    (fit["refdes"], fit["side"]): fit
    for fit in report["fits"]
    if (fit["refdes"], fit["side"])
    in {("D7", "component-alt"), ("D40", "component"), ("D41", "component")}
}
errors: list[str] = []
w11 = board.FindFootprintByReference("W11")


def image_to_board(refdes: str, side: str = "component") -> np.ndarray:
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


def project(refdes: str, joint: list[int], side: str = "component") -> np.ndarray:
    return np.array([float(joint[0]), float(joint[1]), 1.0]) @ image_to_board(refdes, side)


d40 = project("D40", JOINT_B)
d41 = project("D41", JOINT_B)
spread = float(np.linalg.norm(d40 - d41))
if spread > 0.02:
    errors.append(f"D40/D41 projections spread {spread:.4f} mm")
averaged = (d40 + d41) / 2.0
recorded = np.array(endpoint.get("board_mm"), dtype=float)
recorded_error = float(np.linalg.norm(averaged - recorded))
if recorded_error > 0.002:
    errors.append(f"recorded-coordinate error {recorded_error:.4f} mm")

evidence = endpoint.get("board_fit_evidence", {})
if evidence.get("source_image") != fits[("D40", "component")]["image"]:
    errors.append("A11B source image is not guarded")
if evidence.get("joint_px") != JOINT_B:
    errors.append("A11B joint pixel is not guarded")
uncertainty = evidence.get("uncertainty_mm")
if not isinstance(uncertainty, (int, float)) or not 0.2 <= uncertainty <= 0.5:
    errors.append("A11B fitted uncertainty is invalid")
if "printed 11" not in endpoint.get("island_assignment", ""):
    errors.append("A11B printed board-point identity is absent")
if "D92.13" not in endpoint.get("island_assignment", "") or "MEMR" not in endpoint.get("island_assignment", ""):
    errors.append("A11B island assignment lacks D92.13/MEMR")

d92 = board.FindFootprintByReference("D92")
pad = d92.FindPadByNumber("13") if d92 is not None else None
if pad is None or pad.GetNetname() != "MEMR":
    errors.append("D92.13 is not on MEMR")
endpoint_a = endpoints["A11A"]
projected_a = project("D7", JOINT_A, "component-alt")
recorded_a = np.array(endpoint_a.get("board_mm"), dtype=float)
if float(np.linalg.norm(projected_a - recorded_a)) > 0.002:
    errors.append("A11A recorded coordinate drifted")
evidence_a = endpoint_a.get("board_fit_evidence", {})
if evidence_a.get("source_image") != fits[("D7", "component-alt")]["image"]:
    errors.append("A11A source image is not guarded")
if evidence_a.get("joint_px") != JOINT_A:
    errors.append("A11A joint pixel is not guarded")
uncertainty_a = evidence_a.get("uncertainty_mm")
if not isinstance(uncertainty_a, (int, float)) or not 0.4 <= uncertainty_a <= 0.8:
    errors.append("A11A fitted uncertainty is invalid")
if "D7.1" not in endpoint_a.get("island_assignment", "") or "MEMR" not in endpoint_a.get("island_assignment", ""):
    errors.append("A11A island assignment lacks D7.1/MEMR")
d7 = board.FindFootprintByReference("D7")
d7_pad = d7.FindPadByNumber("1") if d7 is not None else None
if d7_pad is None or d7_pad.GetNetname() != "MEMR_D7":
    errors.append("D7.1 is not on its MEMR_D7 wire island")

wire_chord = float(np.linalg.norm(recorded - recorded_a))
if not 118.5 <= wire_chord <= 120.0:
    errors.append(f"A11 terminal chord {wire_chord:.3f} mm is implausible")
if "11.5 cm" not in point.get("observation", "") or "cut length" not in point.get("observation", ""):
    errors.append("A11 approximate-length discrepancy is not explicit")
if point.get("status") != "board-fitted":
    errors.append("A11 point status is not board-fitted")

if w11 is None:
    errors.append("A11: W11 assembly-wire footprint is missing")
else:
    expected_pads = {
        "1": (recorded, "MEMR"),
        "2": (recorded_a, "MEMR_D7"),
    }
    for number, (expected_position, expected_net) in expected_pads.items():
        wire_pad = w11.FindPadByNumber(number)
        if wire_pad is None:
            errors.append(f"A11: W11.{number} landing is missing")
            continue
        position = np.array([
            pcbnew.ToMM(wire_pad.GetPosition().x),
            pcbnew.ToMM(wire_pad.GetPosition().y),
        ])
        if float(np.linalg.norm(position - expected_position)) > 0.002:
            errors.append(f"A11: W11.{number} coordinate drifted")
        if wire_pad.GetNetname() != expected_net:
            errors.append(f"A11: W11.{number} is on {wire_pad.GetNetname()}, expected {expected_net}")
        layers = wire_pad.GetLayerSet()
        if wire_pad.GetAttribute() != pcbnew.PAD_ATTRIB_SMD or not layers.Contains(pcbnew.F_Cu) or layers.Contains(pcbnew.B_Cu):
            errors.append(f"A11: W11.{number} must remain a top-side surface landing")

if errors:
    raise SystemExit("A11 FACTORY LANDING: FAIL\n- " + "\n- ".join(errors))
print(
    "A11 FACTORY LANDING: PASS — two surface islands modeled through W11; "
    f"A11A {recorded_a[0]:.3f},{recorded_a[1]:.3f} mm; "
    f"A11B {recorded[0]:.3f},{recorded[1]:.3f} mm; "
    f"D40/D41 spread {spread:.4f} mm; chord {wire_chord:.3f} mm"
)
