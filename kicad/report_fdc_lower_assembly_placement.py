#!/usr/bin/env python3
"""Fit and report the factory-drawing placement around the lower FDC rows."""
from __future__ import annotations

import json
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
    targets.append({"refdes": item["refdes"], "drawing_px": item["drawing_px"],
                    "projected_board_mm": [round(x, 3), round(y, 3)],
                    "current_footprint_mm": current, "projected_delta_mm": delta,
                    "observation": item["observation"], "electrical_evidence": False})

OUTPUT_JSON.write_text(json.dumps({"schema_version": 1,
                                  "source": RECORD.relative_to(ROOT).as_posix(),
                                  "transform": [round(value, 12) for value in transform],
                                  "checks": checks, "targets": targets}, indent=2) + "\n")
lines = ["# FDC lower assembly placement", "",
         "Status: **FACTORY PLACEMENT EVIDENCE / ELECTRICAL MAPPING PENDING**", "",
         "The photographed factory assembly drawing is registered to the five package centres",
         "already fitted in the owner board photograph. D95, D101, and D102 define the affine",
         "fit; D99 and D97 are independent checks. This establishes reference identity and",
         "placement only, not component value or connectivity.", "",
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
lines += ["", "D93, C10, C11, and C15 have source-PCB footprints at their projected",
          "factory-drawing positions. The other named parts remain explicit physical/BOM omissions until their package and electrical endpoints",
          "are reconciled with the `.009` board; do not silently merge them with `.006` analog parts.",
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
