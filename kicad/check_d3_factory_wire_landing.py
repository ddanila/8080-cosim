#!/usr/bin/env python3
"""Guard the D3-side A20 factory-wire surface landing and local projection."""
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
        raise SystemExit(f"D3 FACTORY LANDING: missing {refdes}")
    pads = list(footprint.Pads())
    return complex(
        sum(pcbnew.ToMM(pad.GetPosition().x) for pad in pads) / len(pads),
        sum(pcbnew.ToMM(pad.GetPosition().y) for pad in pads) / len(pads),
    )


landing_document = json.loads(LANDINGS.read_text(encoding="utf-8"))
point_record = next(
    record for record in landing_document["points"] if record["point"] == 20
)
endpoint = next(
    item for item in point_record["endpoints"] if item["terminal"] == "A20B"
)
local_document = json.loads(LOCAL_REPORT.read_text(encoding="utf-8"))
d3_fit = next(
    fit
    for fit in local_document["fits"]
    if fit["refdes"] == "D3" and fit["side"] == "component"
)

evidence = endpoint.get("board_fit_evidence", {})
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
recorded = complex(*map(float, endpoint["board_mm"]))
coordinate_error = abs(projected - recorded)
if coordinate_error > MAX_COORDINATE_ERROR_MM:
    errors.append(f"projected-coordinate error {coordinate_error:.4f} mm")

island = endpoint.get("island_assignment", "")
if "D3.10" not in island or "S_TTL" not in island:
    errors.append("island assignment lacks D3.10/S_TTL")
uncertainty = evidence.get("uncertainty_mm")
if not isinstance(uncertainty, (int, float)) or not 0.4 <= uncertainty <= 0.8:
    errors.append("invalid local-fit uncertainty")

pin10 = board.FindFootprintByReference("D3").FindPadByNumber("10")
pin10_position = complex(
    pcbnew.ToMM(pin10.GetPosition().x), pcbnew.ToMM(pin10.GetPosition().y)
)
trace_length = abs(recorded - pin10_position)
if not 2.5 <= trace_length <= 3.5:
    errors.append(f"joint-to-D3.10 local span {trace_length:.3f} mm is implausible")

if errors:
    raise SystemExit("D3 FACTORY LANDING: FAIL\n- " + "\n- ".join(errors))
print(
    "D3 FACTORY LANDING: PASS — A20B/D3.10 at "
    f"{recorded.real:.3f},{recorded.imag:.3f} mm; "
    f"local copper span {trace_length:.3f} mm; 3/20 terminals board-fitted"
)
