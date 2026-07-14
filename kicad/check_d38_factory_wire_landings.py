#!/usr/bin/env python3
"""Guard the two D38-side factory-wire surface joints and local projection."""
from __future__ import annotations

import cmath
import json
import math
from pathlib import Path

import pcbnew


ROOT = Path(__file__).resolve().parents[1]
BOARD = ROOT / "kicad/juku.kicad_pcb"
LANDINGS = (
    ROOT / "ref/photos/dgsh5-109-009-sb/factory-wire-landing-registration.json"
)
LOCAL_REPORT = ROOT / "docs/photo-registration/local-packages/report.json"
MAX_COORDINATE_ERROR_MM = 0.002


def pad_centre(board: pcbnew.BOARD, refdes: str) -> complex:
    footprint = board.FindFootprintByReference(refdes)
    if footprint is None:
        raise SystemExit(f"D38 FACTORY LANDINGS: missing {refdes}")
    pads = list(footprint.Pads())
    return complex(
        sum(pcbnew.ToMM(pad.GetPosition().x) for pad in pads) / len(pads),
        sum(pcbnew.ToMM(pad.GetPosition().y) for pad in pads) / len(pads),
    )


landing_document = json.loads(LANDINGS.read_text(encoding="utf-8"))
point_records = {record["point"]: record for record in landing_document["points"]}
local_document = json.loads(LOCAL_REPORT.read_text(encoding="utf-8"))
d38_fit = next(
    fit
    for fit in local_document["fits"]
    if fit["refdes"] == "D38" and fit["side"] == "component"
)
image_points = list(d38_fit["projected_pins"].values())
image_centre = complex(
    sum(point[0] for point in image_points) / len(image_points),
    sum(point[1] for point in image_points) / len(image_points),
)
factor = cmath.rect(
    float(d38_fit["scale_px_per_mm"]),
    math.radians(float(d38_fit["rotation_deg"])),
)
board = pcbnew.LoadBoard(str(BOARD))
d38_centre = pad_centre(board, "D38")

expected = {
    8: ("A8B", "D38.8", "STSTB"),
    9: ("A9B", "D38.12", "SYNC"),
}
errors: list[str] = []
for point, (terminal, pin, net) in expected.items():
    endpoint = next(
        item for item in point_records[point]["endpoints"] if item["terminal"] == terminal
    )
    evidence = endpoint.get("board_fit_evidence", {})
    if evidence.get("source_image") != d38_fit["image"]:
        errors.append(f"{terminal}: board-fit image does not match D38 component fit")
        continue
    joint = evidence.get("joint_px")
    if not isinstance(joint, list) or len(joint) != 2:
        errors.append(f"{terminal}: missing raw joint coordinate")
        continue
    projected = d38_centre + (complex(*map(float, joint)) - image_centre) / factor
    recorded = complex(*map(float, endpoint["board_mm"]))
    error = abs(projected - recorded)
    if error > MAX_COORDINATE_ERROR_MM:
        errors.append(f"{terminal}: projected-coordinate error {error:.4f} mm")
    island = endpoint.get("island_assignment", "")
    if pin not in island or net not in island:
        errors.append(f"{terminal}: island assignment lacks {pin}/{net}")
    uncertainty = evidence.get("uncertainty_mm")
    if not isinstance(uncertainty, (int, float)) or not 0.5 <= uncertainty <= 1.0:
        errors.append(f"{terminal}: invalid local-fit uncertainty")

a9_evidence = next(
    item
    for item in point_records[9]["endpoints"]
    if item["terminal"] == "A9B"
)["board_fit_evidence"]
if a9_evidence.get("via_px") != [2288, 2298]:
    errors.append("A9B: component-side via coordinate is not guarded")
if a9_evidence.get("solder_via_px") != [1374, 1984]:
    errors.append("A9B: cross-side solder-via coordinate is not guarded")

if errors:
    raise SystemExit("D38 FACTORY LANDINGS: FAIL\n- " + "\n- ".join(errors))
print(
    "D38 FACTORY LANDINGS: PASS — A8B/D38.8 and A9B/D38.12; "
    "2/20 factory terminals board-fitted"
)
