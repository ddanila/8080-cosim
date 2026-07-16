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
OUTPUT_JSON = ROOT / "docs/fdc-lower-assembly-placement.json"
OUTPUT_MD = ROOT / "docs/fdc-lower-assembly-placement.md"
OVERLAY = ROOT / "docs/photo-registration/fdc-lower-assembly-placement.jpg"
RESTORED_FACTORY_PARTS = {"C16", "C19", "R92", "R99", "R100", "R102", "R108", "R86"}
EXPECTED_RESISTOR_VALUES = {"R92": "1,3к", "R99": "4,7к", "R100": "12к", "R102": "12к"}
EXPECTED_CAPACITOR_VALUES = {"C20": "1,5 нФ"}


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
if value_evidence.get("values") != {"R92": "1,3к", "R99": "4,7к"}:
    raise SystemExit("FDC LOWER ASSEMBLY PLACEMENT: bad R92/R99 value evidence")
if right_edge_value_evidence.get("values") != {"R100": "12к", "R102": "12к"}:
    raise SystemExit("FDC LOWER ASSEMBLY PLACEMENT: bad right-edge resistor value evidence")
if right_edge_value_evidence.get("unresolved") != ["R108", "R86"]:
    raise SystemExit("FDC LOWER ASSEMBLY PLACEMENT: lower right-edge value boundaries are not guarded")
if c20_value_evidence.get("value") != "1,5 нФ" or c20_value_evidence.get("marking") != "1Н5":
    raise SystemExit("FDC LOWER ASSEMBLY PLACEMENT: bad C20 value evidence")
if "C20.1 endpoint" not in c20_value_evidence.get("unresolved", []) or "C22 value and endpoints" not in c20_value_evidence.get("unresolved", []):
    raise SystemExit("FDC LOWER ASSEMBLY PLACEMENT: C20/C22 boundaries are not guarded")
for evidence in [*value_evidence.get("owner_photos", []), *right_edge_value_evidence.get("owner_photos", [])]:
    image_path = ROOT / evidence.get("source", "")
    if not image_path.is_file() or hashlib.sha256(image_path.read_bytes()).hexdigest() != evidence.get("sha256"):
        raise SystemExit(f"FDC LOWER ASSEMBLY PLACEMENT: value-source hash mismatch for {image_path}")
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
for item in document["targets"]:
    for evidence in item.get("owner_evidence", []):
        image_path = ROOT / evidence["image"]
        joints = evidence.get("joint_px", [])
        if not image_path.is_file() or evidence.get("side") not in {"component", "solder"}:
            raise SystemExit(f"FDC LOWER ASSEMBLY PLACEMENT: invalid owner evidence for {item['refdes']}")
        if len(joints) != 2 or any(len(point) != 2 for point in joints):
            raise SystemExit(f"FDC LOWER ASSEMBLY PLACEMENT: {item['refdes']} needs two owner joint coordinates")
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
                                  "c20_value_evidence": c20_value_evidence,
                                  "checks": checks, "targets": targets}, indent=2) + "\n")
lines = ["# FDC lower assembly placement", "",
         "Status: **FACTORY PLACEMENT EVIDENCE / PARTIAL ELECTRICAL MAPPING**", "",
         "The photographed factory assembly drawing is registered to the five package centres",
         "already fitted in the owner board photograph. D95, D101, and D102 define the affine",
         "fit; D99 and D97 are independent checks. This establishes reference identity and",
         "placement only, except where the owner-evidence records below explicitly close",
         "R92/R99/R100/R102/C20 values or visible copper connectivity.", "",
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
          "at `(303.997,110.024)` and `(306.537,110.024)` mm with 10 mm vertical pad spans. The C63 target site remains an explicit",
          "population/BOM discrepancy: the factory drawing shows its outline, while the raw owner photo shows the exact D41/D40 gap bare, without a body or coherent drilled lead pair.",
          "Owner component photo `PXL_20260710_200418174.jpg` independently shows C19's grey vertical axial body and the four stacked resistor bodies in the same top-to-bottom order;",
          "that corroborates population and orientation. Two independent component angles read R100=`12К` and R102=`12К`; R108/R86 values and all four parts' lead destinations remain continuity tasks. The registered solder view",
          "`PXL_20260710_200522685.jpg` exposes C19's two distinct joints. Its value and both remote destinations remain boundaries. The same owner views",
          "also show populated grey horizontal C16 between the IC rows and the red horizontal R92/R99 pair below D95. Their component-side landings and",
          "backside joints corroborate the factory identities and 12.5/10.16 mm spans. The alternate May angle directly reads R92=`1К3` and R99=`4К7`;",
          "the registered July view independently shows the same strings beneath stronger glare. Uninterrupted component copper closes R92.2-D95.14,",
          "R92.1-R99.2-D101.4, and R99.1-D101.8/GND. Only C16's value and destinations remain boundaries in this row.",
          "Those owner views additionally show the two grey C20/C22 axial bodies and all four solder joints independently of the factory identity drawing. Enhanced C20",
          "pixels read `1Н5` verbatim; GOST 11076-69 Table 1 maps that code exactly to 1500 pF / 1.5 nF, now adopted as C20's value. C20's tolerance, voltage, and endpoints plus C22's marking/value/endpoints remain unpromoted.",
          "The lower drawing also labels the vertical part between D41 and D40 as `C63`, not `C13`.",
          "The owner component view is bracketed by direct fits of both marked packages and contains neither a fitted C63 body nor a coherent two-hole span.",
          "That makes DNP/removal the leading `.009` owner-board disposition, but the old generic array placement is not silently moved or deleted until factory-population intent is reconciled. The unrelated `.006` RF-option C13 is now correctly DNP on the `.009` target and must not be conflated with this C63 site.",
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
