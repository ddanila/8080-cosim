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
JOINT = [2620, 1764]

board = pcbnew.LoadBoard(str(BOARD))
landing_document = json.loads(LANDINGS.read_text(encoding="utf-8"))
point = next(record for record in landing_document["points"] if record["point"] == 11)
endpoints = {item["terminal"]: item for item in point["endpoints"]}
endpoint = endpoints["A11B"]
report = json.loads(REPORT.read_text(encoding="utf-8"))
fits = {
    fit["refdes"]: fit
    for fit in report["fits"]
    if fit["side"] == "component" and fit["refdes"] in {"D40", "D41"}
}
errors: list[str] = []


def image_to_board(refdes: str) -> np.ndarray:
    footprint = board.FindFootprintByReference(refdes)
    fit = fits[refdes]
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


def project(refdes: str) -> np.ndarray:
    return np.array([float(JOINT[0]), float(JOINT[1]), 1.0]) @ image_to_board(refdes)


d40 = project("D40")
d41 = project("D41")
spread = float(np.linalg.norm(d40 - d41))
if spread > 0.02:
    errors.append(f"D40/D41 projections spread {spread:.4f} mm")
averaged = (d40 + d41) / 2.0
recorded = np.array(endpoint.get("board_mm"), dtype=float)
recorded_error = float(np.linalg.norm(averaged - recorded))
if recorded_error > 0.002:
    errors.append(f"recorded-coordinate error {recorded_error:.4f} mm")

evidence = endpoint.get("board_fit_evidence", {})
if evidence.get("source_image") != fits["D40"]["image"]:
    errors.append("A11B source image is not guarded")
if evidence.get("joint_px") != JOINT:
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
if endpoints["A11A"].get("board_mm") is not None:
    errors.append("A11A must remain board-fit pending")
if point.get("status") != "image-registered/board-fit-pending":
    errors.append("A11 must remain partially unresolved")

if errors:
    raise SystemExit("A11 FACTORY LANDING: FAIL\n- " + "\n- ".join(errors))
print(
    "A11 FACTORY LANDING: PASS — "
    f"A11B {recorded[0]:.3f},{recorded[1]:.3f} mm; "
    f"D40/D41 spread {spread:.4f} mm; A11A remains pending"
)
