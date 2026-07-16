#!/usr/bin/env python3
"""Fit and report the factory-drawing placement around the lower FDC rows."""
from __future__ import annotations

import json
import hashlib
import math
from pathlib import Path

import pcbnew
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
RECORD = ROOT / "ref/photos/dgsh5-109-009-sb/fdc-lower-placement-registration.json"
BOARD = ROOT / "kicad/juku.kicad_pcb"
BOARD_SPEC = ROOT / "kicad/juku.board.json"
OUTPUT_JSON = ROOT / "docs/fdc-lower-assembly-placement.json"
OUTPUT_MD = ROOT / "docs/fdc-lower-assembly-placement.md"
OVERLAY = ROOT / "docs/photo-registration/fdc-lower-assembly-placement.jpg"
RESTORED_FACTORY_PARTS = {"C16", "C19", "R92", "R99", "R100", "R102", "R108", "R86"}
EXPECTED_RESISTOR_VALUES = {"R92": "1,3к", "R99": "4,7к", "R100": "12к", "R102": "12к", "R108": "12к", "R86": "4,7к"}
EXPECTED_CAPACITOR_VALUES = {"C20": "1,5 нФ", "C22": "1,5 нФ"}


def solve_3x3(matrix: list[list[float]], values: list[float]) -> list[float]:
    augmented = [row[:] + [value] for row, value in zip(matrix, values)]
    for column in range(3):
        pivot = max(range(column, 3), key=lambda row: abs(augmented[row][column]))
        if abs(augmented[pivot][column]) < 1e-12:
            raise SystemExit("FDC LOWER ASSEMBLY PLACEMENT: degenerate anchors")
        augmented[column], augmented[pivot] = augmented[pivot], augmented[column]
        divisor = augmented[column][column]
        augmented[column] = [value / divisor for value in augmented[column]]
        for row in range(3):
            if row == column:
                continue
            multiplier = augmented[row][column]
            augmented[row] = [value - multiplier * basis
                               for value, basis in zip(augmented[row], augmented[column])]
    return [augmented[row][3] for row in range(3)]


def fit_affine(anchors: list[dict]) -> tuple[float, float, float, float, float, float]:
    fit = [item for item in anchors if item["use"] == "fit"]
    if len(fit) != 3:
        raise SystemExit("FDC LOWER ASSEMBLY PLACEMENT: affine fit needs exactly three anchors")
    matrix = [[float(item["drawing_px"][0]), float(item["drawing_px"][1]), 1.0]
              for item in fit]
    x = solve_3x3(matrix, [float(item["board_mm"][0]) for item in fit])
    y = solve_3x3(matrix, [float(item["board_mm"][1]) for item in fit])
    return (*x, *y)


def project(transform: tuple[float, ...], point: list[float]) -> tuple[float, float]:
    a, b, c, d, e, f = transform
    x, y = map(float, point)
    return a*x + b*y + c, d*x + e*y + f


document = json.loads(RECORD.read_text(encoding="utf-8"))
if document.get("schema_version") != 1 or document.get("model") != "affine":
    raise SystemExit("FDC LOWER ASSEMBLY PLACEMENT: unsupported registration schema")
value_evidence = document.get("r92_r99_value_evidence", {})
right_edge_value_evidence = document.get("right_edge_resistor_value_evidence", {})
c20_value_evidence = document.get("c20_value_evidence", {})
c22_value_evidence = document.get("c22_value_evidence", {})
c16_c19_marking_evidence = document.get("c16_c19_marking_evidence", {})
right_edge_common_rail_evidence = document.get("right_edge_resistor_common_rail_evidence", {})
c19_resistor_junction_evidence = document.get("c19_resistor_junction_evidence", {})
right_edge_pin1_photo_exhaustion = document.get("right_edge_pin1_photo_exhaustion", {})
if value_evidence.get("values") != {"R92": "1,3к", "R99": "4,7к"}:
    raise SystemExit("FDC LOWER ASSEMBLY PLACEMENT: bad R92/R99 value evidence")
if right_edge_value_evidence.get("values") != {"R100": "12к", "R102": "12к", "R108": "12к", "R86": "4,7к"}:
    raise SystemExit("FDC LOWER ASSEMBLY PLACEMENT: bad right-edge resistor value evidence")
if right_edge_value_evidence.get("unresolved") != []:
    raise SystemExit("FDC LOWER ASSEMBLY PLACEMENT: closed right-edge values unexpectedly unresolved")
if c20_value_evidence.get("value") != "1,5 нФ" or c20_value_evidence.get("marking") != "1Н5":
    raise SystemExit("FDC LOWER ASSEMBLY PLACEMENT: bad C20 value evidence")
if "C20.1 endpoint" not in c20_value_evidence.get("unresolved", []) or "C20.2 endpoint" not in c20_value_evidence.get("unresolved", []):
    raise SystemExit("FDC LOWER ASSEMBLY PLACEMENT: C20 endpoint boundaries are not guarded")
if c22_value_evidence.get("value") != "1,5 нФ" or c22_value_evidence.get("marking") != "1Н5":
    raise SystemExit("FDC LOWER ASSEMBLY PLACEMENT: bad C22 value evidence")
if "C22.1 endpoint" not in c22_value_evidence.get("unresolved", []) or "C22.2 endpoint" not in c22_value_evidence.get("unresolved", []):
    raise SystemExit("FDC LOWER ASSEMBLY PLACEMENT: C22 endpoint boundaries are not guarded")
if c16_c19_marking_evidence.get("visible_markings") != {"C16": "27", "C19": "22"}:
    raise SystemExit("FDC LOWER ASSEMBLY PLACEMENT: bad C16/C19 literal marking evidence")
for refdes in ("C16", "C19"):
    if f"{refdes} value/unit" not in c16_c19_marking_evidence.get("unresolved", []):
        raise SystemExit(f"FDC LOWER ASSEMBLY PLACEMENT: {refdes} ambiguous value boundary is not guarded")
expected_rail_endpoints = ["R100.2", "R102.2", "R108.2", "R86.2"]
if (right_edge_common_rail_evidence.get("joined_endpoints") != expected_rail_endpoints or
        right_edge_common_rail_evidence.get("net") != "RIGHT_EDGE_RESISTOR_RAIL_BOUNDARY"):
    raise SystemExit("FDC LOWER ASSEMBLY PLACEMENT: bad right-edge common-rail evidence")
expected_rail_boundaries = ["shared rail remote destination", "R102.1 endpoint", "R108.1 endpoint"]
if right_edge_common_rail_evidence.get("unresolved") != expected_rail_boundaries:
    raise SystemExit("FDC LOWER ASSEMBLY PLACEMENT: right-edge rail boundaries are not guarded")
expected_c19_joins = {
    "C19_1_R100_1_BOUNDARY": ["C19.1", "R100.1"],
    "C19_2_R86_1_BOUNDARY": ["C19.2", "R86.1"],
}
if c19_resistor_junction_evidence.get("joined_endpoints") != expected_c19_joins:
    raise SystemExit("FDC LOWER ASSEMBLY PLACEMENT: bad C19/resistor junction evidence")
if c19_resistor_junction_evidence.get("unresolved") != [
        "C19/R100 common-net remote destination", "C19/R86 common-net remote destination"]:
    raise SystemExit("FDC LOWER ASSEMBLY PLACEMENT: C19/resistor remote boundaries are not guarded")
for evidence in [*value_evidence.get("owner_photos", []), *right_edge_value_evidence.get("owner_photos", [])]:
    image_path = ROOT / evidence.get("source", "")
    if not image_path.is_file() or hashlib.sha256(image_path.read_bytes()).hexdigest() != evidence.get("sha256"):
        raise SystemExit(f"FDC LOWER ASSEMBLY PLACEMENT: value-source hash mismatch for {image_path}")
    with Image.open(image_path) as evidence_image:
        if list(evidence_image.size) != evidence.get("dimensions_px"):
            raise SystemExit(f"FDC LOWER ASSEMBLY PLACEMENT: value-source dimensions mismatch for {image_path}")
        width, height = evidence_image.size
    for refdes, bbox in evidence.get("body_bboxes_px", {}).items():
        if (refdes not in EXPECTED_RESISTOR_VALUES or len(bbox) != 4 or
                not (0 <= bbox[0] < bbox[2] <= width and 0 <= bbox[1] < bbox[3] <= height)):
            raise SystemExit(f"FDC LOWER ASSEMBLY PLACEMENT: invalid {refdes} value-source body box")
c20_photo = c20_value_evidence.get("owner_photo", {})
c20_image_path = ROOT / c20_photo.get("source", "")
if not c20_image_path.is_file() or hashlib.sha256(c20_image_path.read_bytes()).hexdigest() != c20_photo.get("sha256"):
    raise SystemExit(f"FDC LOWER ASSEMBLY PLACEMENT: C20 value-source hash mismatch for {c20_image_path}")
with Image.open(c20_image_path) as c20_image:
    if list(c20_image.size) != c20_photo.get("dimensions_px"):
        raise SystemExit("FDC LOWER ASSEMBLY PLACEMENT: C20 value-source dimensions mismatch")
c20_bbox = c20_photo.get("body_bbox_px", [])
if len(c20_bbox) != 4 or c20_bbox[0] >= c20_bbox[2] or c20_bbox[1] >= c20_bbox[3]:
    raise SystemExit("FDC LOWER ASSEMBLY PLACEMENT: invalid C20 value-source body box")
c20_standard = ROOT / c20_value_evidence.get("marking_standard", {}).get("source", "")
if not c20_standard.is_file() or "1Н5" not in c20_standard.read_text(encoding="utf-8"):
    raise SystemExit("FDC LOWER ASSEMBLY PLACEMENT: C20 marking-standard evidence missing")
c22_photo = c22_value_evidence.get("owner_photo", {})
c22_image_path = ROOT / c22_photo.get("source", "")
if not c22_image_path.is_file() or hashlib.sha256(c22_image_path.read_bytes()).hexdigest() != c22_photo.get("sha256"):
    raise SystemExit(f"FDC LOWER ASSEMBLY PLACEMENT: C22 value-source hash mismatch for {c22_image_path}")
with Image.open(c22_image_path) as c22_image:
    if list(c22_image.size) != c22_photo.get("dimensions_px"):
        raise SystemExit("FDC LOWER ASSEMBLY PLACEMENT: C22 value-source dimensions mismatch")
c22_bbox = c22_photo.get("body_bbox_px", [])
if len(c22_bbox) != 4 or c22_bbox[0] >= c22_bbox[2] or c22_bbox[1] >= c22_bbox[3]:
    raise SystemExit("FDC LOWER ASSEMBLY PLACEMENT: invalid C22 value-source body box")
c22_standard = ROOT / c22_value_evidence.get("marking_standard", {}).get("source", "")
if not c22_standard.is_file() or "1Н5" not in c22_standard.read_text(encoding="utf-8"):
    raise SystemExit("FDC LOWER ASSEMBLY PLACEMENT: C22 marking-standard evidence missing")
c16_c19_photo = c16_c19_marking_evidence.get("owner_photo", {})
c16_c19_image_path = ROOT / c16_c19_photo.get("source", "")
if (not c16_c19_image_path.is_file() or
        hashlib.sha256(c16_c19_image_path.read_bytes()).hexdigest() != c16_c19_photo.get("sha256")):
    raise SystemExit(f"FDC LOWER ASSEMBLY PLACEMENT: C16/C19 marking-source hash mismatch for {c16_c19_image_path}")
with Image.open(c16_c19_image_path) as c16_c19_image:
    if list(c16_c19_image.size) != c16_c19_photo.get("dimensions_px"):
        raise SystemExit("FDC LOWER ASSEMBLY PLACEMENT: C16/C19 marking-source dimensions mismatch")
    width, height = c16_c19_image.size
for refdes, bbox in c16_c19_photo.get("body_bboxes_px", {}).items():
    if (refdes not in {"C16", "C19"} or len(bbox) != 4 or
            not (0 <= bbox[0] < bbox[2] <= width and 0 <= bbox[1] < bbox[3] <= height)):
        raise SystemExit(f"FDC LOWER ASSEMBLY PLACEMENT: invalid {refdes} literal-marking body box")
c16_c19_standard = ROOT / c16_c19_marking_evidence.get("marking_standard", {}).get("source", "")
if not c16_c19_standard.is_file() or "bare numeric" not in c16_c19_standard.read_text(encoding="utf-8"):
    raise SystemExit("FDC LOWER ASSEMBLY PLACEMENT: C16/C19 marking-standard guard missing")
rail_photo = right_edge_common_rail_evidence.get("component_photo", {})
rail_image_path = ROOT / rail_photo.get("source", "")
if (not rail_image_path.is_file() or
        hashlib.sha256(rail_image_path.read_bytes()).hexdigest() != rail_photo.get("sha256")):
    raise SystemExit(f"FDC LOWER ASSEMBLY PLACEMENT: right-edge rail-source hash mismatch for {rail_image_path}")
with Image.open(rail_image_path) as rail_image:
    if list(rail_image.size) != rail_photo.get("dimensions_px"):
        raise SystemExit("FDC LOWER ASSEMBLY PLACEMENT: right-edge rail-source dimensions mismatch")
    width, height = rail_image.size
component_bbox = rail_photo.get("rail_bbox_px", [])
if len(component_bbox) != 4 or not (0 <= component_bbox[0] < component_bbox[2] <= width and 0 <= component_bbox[1] < component_bbox[3] <= height):
    raise SystemExit("FDC LOWER ASSEMBLY PLACEMENT: invalid component rail box")
component_joints = rail_photo.get("endpoint_joint_px", {})
if sorted(component_joints) != sorted(expected_rail_endpoints):
    raise SystemExit("FDC LOWER ASSEMBLY PLACEMENT: right-edge endpoint joint set mismatch")
if any(len(point) != 2 or not (component_bbox[0] <= point[0] <= component_bbox[2] and
                               component_bbox[1] <= point[1] <= component_bbox[3])
       for point in component_joints.values()):
    raise SystemExit("FDC LOWER ASSEMBLY PLACEMENT: right-edge endpoint joint lies outside rail box")
for index, evidence in enumerate(c19_resistor_junction_evidence.get("owner_photos", [])):
    image_path = ROOT / evidence.get("source", "")
    if (not image_path.is_file() or
            hashlib.sha256(image_path.read_bytes()).hexdigest() != evidence.get("sha256")):
        raise SystemExit(f"FDC LOWER ASSEMBLY PLACEMENT: C19 junction-source hash mismatch for {image_path}")
    with Image.open(image_path) as evidence_image:
        if list(evidence_image.size) != evidence.get("dimensions_px"):
            raise SystemExit("FDC LOWER ASSEMBLY PLACEMENT: C19 junction-source dimensions mismatch")
        width, height = evidence_image.size
    bbox = evidence.get("bbox_px", [])
    if len(bbox) != 4 or not (0 <= bbox[0] < bbox[2] <= width and 0 <= bbox[1] < bbox[3] <= height):
        raise SystemExit("FDC LOWER ASSEMBLY PLACEMENT: invalid C19 junction-source box")
    junctions = evidence.get("junction_px")
    if index == 0:
        if sorted(junctions or {}) != sorted(expected_c19_joins):
            raise SystemExit("FDC LOWER ASSEMBLY PLACEMENT: C19 junction coordinate set mismatch")
        if any(len(point) != 2 or not (bbox[0] <= point[0] <= bbox[2] and bbox[1] <= point[1] <= bbox[3])
               for point in junctions.values()):
            raise SystemExit("FDC LOWER ASSEMBLY PLACEMENT: C19 junction lies outside evidence box")
if len(c19_resistor_junction_evidence.get("owner_photos", [])) != 2:
    raise SystemExit("FDC LOWER ASSEMBLY PLACEMENT: C19 joins need two independent component angles")
expected_pin1_joints = {
    "R100.1": [3294, 1064], "R102.1": [3317, 1142],
    "R108.1": [3325, 1217], "R86.1": [3320, 1276],
}
for key in ("component_photo", "corroborating_photo", "solder_photo"):
    evidence = right_edge_pin1_photo_exhaustion.get(key, {})
    image_path = ROOT / evidence.get("source", "")
    if (not image_path.is_file() or
            hashlib.sha256(image_path.read_bytes()).hexdigest() != evidence.get("sha256")):
        raise SystemExit(f"FDC LOWER ASSEMBLY PLACEMENT: pin1 exhaustion-source hash mismatch for {image_path}")
    with Image.open(image_path) as evidence_image:
        if list(evidence_image.size) != evidence.get("dimensions_px"):
            raise SystemExit("FDC LOWER ASSEMBLY PLACEMENT: pin1 exhaustion-source dimensions mismatch")
        width, height = evidence_image.size
    bbox = evidence.get("bbox_px")
    if bbox is not None and (len(bbox) != 4 or not
            (0 <= bbox[0] < bbox[2] <= width and 0 <= bbox[1] < bbox[3] <= height)):
        raise SystemExit("FDC LOWER ASSEMBLY PLACEMENT: invalid pin1 exhaustion-source box")
component_pin1 = right_edge_pin1_photo_exhaustion["component_photo"]
if component_pin1.get("joint_px") != expected_pin1_joints:
    raise SystemExit("FDC LOWER ASSEMBLY PLACEMENT: right-edge pin1 joint set mismatch")
pin1_bbox = component_pin1["bbox_px"]
if any(not (pin1_bbox[0] <= point[0] <= pin1_bbox[2] and pin1_bbox[1] <= point[1] <= pin1_bbox[3])
       for point in expected_pin1_joints.values()):
    raise SystemExit("FDC LOWER ASSEMBLY PLACEMENT: right-edge pin1 joint lies outside evidence box")
if right_edge_pin1_photo_exhaustion["solder_photo"].get("c19_joint_px_by_pad") != {
        "1": [875, 712], "2": [823, 893]}:
    raise SystemExit("FDC LOWER ASSEMBLY PLACEMENT: corrected C19 solder-pad ordering mismatch")
if right_edge_pin1_photo_exhaustion.get("unresolved") != [
        "R102.1 remote destination", "R108.1 remote destination",
        "C19/R100 common-net remote destination", "C19/R86 common-net remote destination"]:
    raise SystemExit("FDC LOWER ASSEMBLY PLACEMENT: photo-exhausted pin1 boundaries are not guarded")
for item in document["targets"]:
    for evidence in item.get("owner_evidence", []):
        image_path = ROOT / evidence["image"]
        joints = evidence.get("joint_px", [])
        if not image_path.is_file() or evidence.get("side") not in {"component", "solder"}:
            raise SystemExit(f"FDC LOWER ASSEMBLY PLACEMENT: invalid owner evidence for {item['refdes']}")
        if len(joints) != 2 or any(len(point) != 2 for point in joints):
            raise SystemExit(f"FDC LOWER ASSEMBLY PLACEMENT: {item['refdes']} needs two owner joint coordinates")
        if (item["refdes"] == "C19" and evidence.get("side") == "solder" and
                evidence.get("joint_order") != ["pad1", "pad2"]):
            raise SystemExit("FDC LOWER ASSEMBLY PLACEMENT: C19 solder joints need explicit pad order")
    for evidence in item.get("owner_absence_evidence", []):
        image_path = ROOT / evidence["image"]
        bbox = evidence.get("bbox_px", [])
        if not image_path.is_file() or evidence.get("side") not in {"component", "solder"}:
            raise SystemExit(f"FDC LOWER ASSEMBLY PLACEMENT: invalid absence evidence for {item['refdes']}")
        if len(bbox) != 4 or bbox[0] >= bbox[2] or bbox[1] >= bbox[3]:
            raise SystemExit(f"FDC LOWER ASSEMBLY PLACEMENT: invalid absence box for {item['refdes']}")
transform = fit_affine(document["anchors"])
checks = []
for item in document["anchors"]:
    predicted = project(transform, item["drawing_px"])
    observed = tuple(map(float, item["board_mm"]))
    error = math.hypot(predicted[0] - observed[0], predicted[1] - observed[1])
    checks.append({"refdes": item["refdes"], "use": item["use"],
                   "error_mm": round(error, 3)})
check_errors = [item["error_mm"] for item in checks if item["use"] == "check"]
if not check_errors or max(check_errors) > 1.0:
    raise SystemExit(f"FDC LOWER ASSEMBLY PLACEMENT: held-out error {max(check_errors):.3f} mm")

board = pcbnew.LoadBoard(str(BOARD))
board_spec = json.loads(BOARD_SPEC.read_text(encoding="utf-8"))
c63_chip = next((chip for chip in board_spec["chips"] if chip.get("ref") == "C63"), None)
if c63_chip is None or c63_chip.get("pcb_dnp") is not True:
    raise SystemExit("FDC LOWER ASSEMBLY PLACEMENT: C63 target DNP is not encoded")
if board.FindFootprintByReference("C63") is not None:
    raise SystemExit("FDC LOWER ASSEMBLY PLACEMENT: target-DNP C63 footprint is still present")
targets = []
for item in document["targets"]:
    x, y = project(transform, item["drawing_px"])
    footprint = board.FindFootprintByReference(item["refdes"])
    current = None
    delta = None
    if footprint is not None:
        pads = [pad.GetPosition() for pad in footprint.Pads()]
        current = [round(sum(pcbnew.ToMM(point.x) for point in pads) / len(pads), 3),
                   round(sum(pcbnew.ToMM(point.y) for point in pads) / len(pads), 3)]
        delta = [round(x - current[0], 3), round(y - current[1], 3)]
        expected_value = {**EXPECTED_RESISTOR_VALUES, **EXPECTED_CAPACITOR_VALUES}.get(item["refdes"])
        if expected_value is not None and footprint.GetValue() != expected_value:
            raise SystemExit(f"FDC LOWER ASSEMBLY PLACEMENT: {item['refdes']} value {footprint.GetValue()!r} != {expected_value!r}")
        expected_pad_nets = {
            "C19": {"1": "C19_1_R100_1_BOUNDARY", "2": "C19_2_R86_1_BOUNDARY"},
            "R100": {"1": "C19_1_R100_1_BOUNDARY", "2": "RIGHT_EDGE_RESISTOR_RAIL_BOUNDARY"},
            "R102": {"1": "R102_1_BOUNDARY", "2": "RIGHT_EDGE_RESISTOR_RAIL_BOUNDARY"},
            "R108": {"1": "R108_1_BOUNDARY", "2": "RIGHT_EDGE_RESISTOR_RAIL_BOUNDARY"},
            "R86": {"1": "C19_2_R86_1_BOUNDARY", "2": "RIGHT_EDGE_RESISTOR_RAIL_BOUNDARY"},
        }
        if item["refdes"] in expected_pad_nets:
            pad_nets = {pad.GetNumber(): pad.GetNetname() for pad in footprint.Pads()}
            if pad_nets != expected_pad_nets[item["refdes"]]:
                raise SystemExit(f"FDC LOWER ASSEMBLY PLACEMENT: {item['refdes']} local-join endpoint mismatch")
    targets.append({"refdes": item["refdes"], "drawing_px": item["drawing_px"],
                    "projected_board_mm": [round(x, 3), round(y, 3)],
                    "current_footprint_mm": current, "projected_delta_mm": delta,
                    "observation": item["observation"],
                    "owner_evidence": item.get("owner_evidence", []),
                    "owner_absence_evidence": item.get("owner_absence_evidence", []),
                    "electrical_evidence": item.get("electrical_evidence", False)})

restored_errors = []
for item in targets:
    if item["refdes"] not in RESTORED_FACTORY_PARTS:
        continue
    if item["current_footprint_mm"] is None:
        restored_errors.append(f"{item['refdes']} footprint missing")
    elif math.hypot(*item["projected_delta_mm"]) > 0.02:
        restored_errors.append(
            f"{item['refdes']} placement residual {math.hypot(*item['projected_delta_mm']):.3f} mm"
        )
if restored_errors:
    raise SystemExit("FDC LOWER ASSEMBLY PLACEMENT: restored-row mismatch\n- " + "\n- ".join(restored_errors))

OUTPUT_JSON.write_text(json.dumps({"schema_version": 1,
                                  "source": RECORD.relative_to(ROOT).as_posix(),
                                  "transform": [round(value, 12) for value in transform],
                                  "r92_r99_value_evidence": value_evidence,
                                  "right_edge_resistor_value_evidence": right_edge_value_evidence,
                                  "right_edge_resistor_common_rail_evidence": right_edge_common_rail_evidence,
                                  "c19_resistor_junction_evidence": c19_resistor_junction_evidence,
                                  "right_edge_pin1_photo_exhaustion": right_edge_pin1_photo_exhaustion,
                                  "c16_c19_marking_evidence": c16_c19_marking_evidence,
                                  "c20_value_evidence": c20_value_evidence,
                                  "c22_value_evidence": c22_value_evidence,
                                  "checks": checks, "targets": targets}, indent=2) + "\n")
lines = ["# FDC lower assembly placement", "",
         "Status: **FACTORY PLACEMENT EVIDENCE / PARTIAL ELECTRICAL MAPPING**", "",
         "The photographed factory assembly drawing is registered to the five package centres",
         "already fitted in the owner board photograph. D95, D101, and D102 define the affine",
         "fit; D99 and D97 are independent checks. This establishes reference identity and",
         "placement only, except where the owner-evidence records below explicitly close",
         "R92/R99/R100/R102/R108/R86/C20/C22 values or visible copper connectivity.", "",
         f"Held-out errors: D99 `{next(x['error_mm'] for x in checks if x['refdes']=='D99'):.3f}` mm; "
         f"D97 `{next(x['error_mm'] for x in checks if x['refdes']=='D97'):.3f}` mm.", "",
         "| Ref | Projected x,y mm | Current x,y mm | Delta mm | Drawing observation |", 
         "| --- | ---: | ---: | ---: | --- |"]
for item in targets:
    projected = ", ".join(f"{value:.3f}" for value in item["projected_board_mm"])
    current = "absent" if item["current_footprint_mm"] is None else ", ".join(
        f"{value:.3f}" for value in item["current_footprint_mm"])
    delta = "-" if item["projected_delta_mm"] is None else ", ".join(
        f"{value:+.3f}" for value in item["projected_delta_mm"])
    lines.append(f"| {item['refdes']} | {projected} | {current} | {delta} | {item['observation']} |")
lines += ["", "D93, C10, C11, C15, C16, C19, R92, R99, and the populated R100/R102/R108/R86 right-edge row have source-PCB footprints at their projected",
          "factory-drawing positions. C20/C22 are also restored, but their table deltas are intentional: the drawing points identify the",
          "overlapping body labels, whereas registered owner component and solder photos prove the actual adjacent 2.54 mm drill columns",
          "at `(303.997,110.024)` and `(306.537,110.024)` mm with 10 mm vertical pad spans. C63 is now an explicit target-board DNP:",
          "the factory drawing shows its intended outline, while the raw owner photo shows the exact D41/D40 gap bare without a body or coherent drilled lead pair, and the source PCB therefore has no fabricated footprint.",
          "Owner component photo `PXL_20260710_200418174.jpg` independently shows C19's grey vertical axial body and the four stacked resistor bodies in the same top-to-bottom order;",
          "that corroborates population and orientation. Two independent component angles read R100/R102/R108=`12К` and R86=`4К7`. Uninterrupted component copper joins all four right-hand pin-2 leads to one perimeter rail; its remote destination and R102/R108 pin-1 destinations remain continuity tasks. The same two angles directly show C19's upper lead and R100.1 sharing one landing, and C19's lower lead and R86.1 sharing another; only the two joined nets' remote destinations remain open. The registered solder view",
          "`PXL_20260710_200522685.jpg` exposes C19's two distinct joints; cross-side review corrects their recorded order to upper pad1 `(875,712)` and lower pad2 `(823,893)`. The July view also registers all four resistor pin-1 joints, while the independent May angle and solder field expose no unique remote continuation for R102.1/R108.1. An oblique May view literally reads `22` on C19's exposed face, but no unambiguous unit/decimal glyph; its value/unit remains a boundary. The same owner views",
          "also show populated grey horizontal C16 between the IC rows and the red horizontal R92/R99 pair below D95. Their component-side landings and",
          "backside joints corroborate the factory identities and 12.5/10.16 mm spans. The alternate May angle directly reads R92=`1К3` and R99=`4К7`;",
          "the registered July view independently shows the same strings beneath stronger glare. Uninterrupted component copper closes R92.2-D95.14,",
          "R92.1-R99.2-D101.4, and R99.1-D101.8/GND. The May view likewise literally reads bare `27` on C16, but GOST 11076-69 Table 1 requires a unit/decimal letter for a coded capacitance; C16's value/unit and destinations therefore remain boundaries.",
          "Those owner views additionally show the two grey C20/C22 axial bodies and all four solder joints independently of the factory identity drawing. Enhanced July pixels",
          "read C20=`1Н5`, and an independent May angle directly reads the outer C22 body as `1Н5`; GOST 11076-69 Table 1 maps both codes exactly to 1500 pF / 1.5 nF, now adopted for both parts. Their tolerances, voltages, and endpoints remain unpromoted.",
          "The lower drawing also labels the vertical part between D41 and D40 as `C63`, not `C13`.",
          "The owner component view is bracketed by direct fits of both marked packages and contains neither a fitted C63 body nor a coherent two-hole span.",
          "Whether the part was omitted at assembly or removed later is not recoverable from the image, but both histories yield the same exact target population: absent. The schematic retains the intended GND-to-RAIL_H bypass connection while C63 is excluded from the target PCB and populate-now BOM. The unrelated `.006` RF-option C13 is also DNP on the `.009` target and must not be conflated with this C63 site.",
          "The owner component view does not expose a complete electrical path at either corrected",
          "site: C11's landings are visible without an unambiguous body, while C15 is hidden by the",
          "factory cable. Neither placement is connectivity evidence."]
OUTPUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")

image = Image.open(ROOT / document["source_image"]).convert("RGB")
draw = ImageDraw.Draw(image)
font = ImageFont.load_default()
for item in document["anchors"] + document["targets"]:
    x, y = map(float, item["drawing_px"])
    colour = "#00e5ff" if item in document["anchors"] else "#ff1744"
    draw.ellipse((x-10, y-10, x+10, y+10), outline=colour, width=3)
    draw.text((x+13, y-10), item["refdes"], fill=colour, font=font,
              stroke_width=2, stroke_fill="black")
OVERLAY.parent.mkdir(parents=True, exist_ok=True)
image.save(OVERLAY, quality=94, subsampling=0)
print(f"FDC LOWER ASSEMBLY PLACEMENT: PASS; {len(targets)} targets; max check {max(check_errors):.3f} mm")
