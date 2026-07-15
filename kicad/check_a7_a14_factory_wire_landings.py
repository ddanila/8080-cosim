#!/usr/bin/env python3
"""Guard the printed D40-side A7/A14 factory-wire landing coordinates."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pcbnew


ROOT = Path(__file__).resolve().parents[1]
BOARD = ROOT / "kicad/juku.kicad_pcb"
LANDINGS = ROOT / "ref/photos/dgsh5-109-009-sb/factory-wire-landing-registration.json"
REPORT = ROOT / "docs/photo-registration/local-packages/report.json"
EXPECTED = {
    7: {
        "terminal": "A7B",
        "joint": [1774, 552],
        "net": "PHI1",
        "owner_pin": "10",
        "printed": "printed 7",
    },
    14: {
        "terminal": "A14B",
        "joint": [1837, 510],
        "net": "PHI2",
        "owner_pin": "12",
        "printed": "printed 14",
    },
}

board = pcbnew.LoadBoard(str(BOARD))
document = json.loads(LANDINGS.read_text(encoding="utf-8"))
points = {record["point"]: record for record in document["points"]}
report = json.loads(REPORT.read_text(encoding="utf-8"))
fit = next(
    item for item in report["fits"]
    if item["refdes"] == "D40" and item["side"] == "solder-alt"
)
errors: list[str] = []

d40 = board.FindFootprintByReference("D40")
image_points: list[list[float]] = []
board_points: list[list[float]] = []
for pin, image_point in fit["projected_pins"].items():
    pad = d40.FindPadByNumber(pin)
    position = pad.GetPosition()
    image_points.append([*map(float, image_point), 1.0])
    board_points.append([pcbnew.ToMM(position.x), pcbnew.ToMM(position.y)])
image_to_board = np.linalg.lstsq(
    np.array(image_points), np.array(board_points), rcond=None
)[0]

projected: dict[int, np.ndarray] = {}
for number, expected in EXPECTED.items():
    point = points[number]
    endpoint = next(
        item for item in point["endpoints"]
        if item["terminal"] == expected["terminal"]
    )
    value = np.array([*map(float, expected["joint"]), 1.0]) @ image_to_board
    projected[number] = value
    recorded = np.array(endpoint.get("board_mm"), dtype=float)
    if float(np.linalg.norm(value - recorded)) > 0.002:
        errors.append(f"A{number} recorded coordinate drifted")
    evidence = endpoint.get("board_fit_evidence", {})
    if evidence.get("source_image") != fit["image"]:
        errors.append(f"A{number} source image is not guarded")
    if evidence.get("joint_px") != expected["joint"]:
        errors.append(f"A{number} joint pixel is not guarded")
    if evidence.get("local_fit") != "D40/solder-alt":
        errors.append(f"A{number} local fit is not guarded")
    uncertainty = evidence.get("uncertainty_mm")
    if not isinstance(uncertainty, (int, float)) or not 0.4 <= uncertainty <= 0.8:
        errors.append(f"A{number} fitted uncertainty is invalid")
    assignment = endpoint.get("island_assignment", "")
    if expected["printed"] not in assignment or expected["net"] not in assignment:
        errors.append(f"A{number} printed-point/net assignment is absent")
    if point.get("status") != "image-registered/board-fit-pending":
        errors.append(f"A{number} must remain partial until its D1-side terminal is fitted")
    other = next(item for item in point["endpoints"] if item is not endpoint)
    if other.get("board_mm") is not None or other.get("island_assignment") is not None:
        errors.append(f"A{number} D1-side terminal was promoted without this guard")

    owner = board.FindFootprintByReference("D35").FindPadByNumber(expected["owner_pin"])
    if owner is None or owner.GetNetname() != expected["net"]:
        errors.append(
            f"D35.{expected['owner_pin']} is not on {expected['net']}"
        )

separation = float(np.linalg.norm(projected[7] - projected[14]))
if not 3.0 <= separation <= 3.5:
    errors.append(f"A7/A14 printed-joint separation {separation:.3f} mm is implausible")

if errors:
    raise SystemExit("A7/A14 FACTORY LANDINGS: FAIL\n- " + "\n- ".join(errors))
print(
    "A7/A14 FACTORY LANDINGS: PASS — "
    f"A7B {projected[7][0]:.3f},{projected[7][1]:.3f} mm; "
    f"A14B {projected[14][0]:.3f},{projected[14][1]:.3f} mm; "
    f"separation {separation:.3f} mm"
)
