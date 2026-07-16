#!/usr/bin/env python3
"""Report factory-drawing placement evidence in the upper FDC row."""
from __future__ import annotations

import json
import hashlib
import math
from pathlib import Path

import pcbnew
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
RECORD = ROOT / "ref/photos/dgsh5-109-009-sb/fdc-upper-placement-registration.json"
BOARD = ROOT / "kicad/juku.kicad_pcb"
OUTPUT_JSON = ROOT / "docs/fdc-upper-assembly-placement.json"
OUTPUT_MD = ROOT / "docs/fdc-upper-assembly-placement.md"
OVERLAY = ROOT / "docs/photo-registration/fdc-upper-assembly-placement.jpg"

document = json.loads(RECORD.read_text(encoding="utf-8"))
if document.get("schema_version") != 1:
    raise SystemExit("FDC UPPER ASSEMBLY PLACEMENT: unsupported registration schema")
anchors = {item["refdes"]: item for item in document["anchors"]}
pullups = document.get("d94_pullups", [])
value_evidence = document.get("d94_pullup_value_evidence", {})

expected_pullups = {
    "R87": ("D94_A3_D104_X4_PULLUP", [["D94", "13"], ["D104", "7"]]),
    "R88": ("D94_A4_D101_Q0_PULLUP", [["D94", "14"], ["D101", "7"]]),
    "R89": ("D94_D0_BOUNDARY", [["D94", "1"]]),
}
if [item.get("refdes") for item in pullups] != ["R87", "R88", "R89"]:
    raise SystemExit("FDC UPPER ASSEMBLY PLACEMENT: D94 pull-up order is not R87/R88/R89")
for item in pullups:
    signal, nodes = expected_pullups[item["refdes"]]
    if item.get("signal") != signal or item.get("signal_nodes") != nodes:
        raise SystemExit(f"FDC UPPER ASSEMBLY PLACEMENT: bad {item['refdes']} electrical mapping")
if value_evidence.get("value") != "6,2к" or value_evidence.get("resistance_ohms") != 6200:
    raise SystemExit("FDC UPPER ASSEMBLY PLACEMENT: bad D94 pull-up value evidence")
for source in [value_evidence.get("factory_bom", {}), *value_evidence.get("owner_photos", [])]:
    path = ROOT / source.get("source", "")
    if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != source.get("sha256"):
        raise SystemExit(f"FDC UPPER ASSEMBLY PLACEMENT: source hash mismatch for {path}")


def interpolate(left: dict, right: dict, drawing_x: float) -> tuple[float, float, float]:
    denominator = float(right["drawing_px"][0]) - float(left["drawing_px"][0])
    fraction = (drawing_x - float(left["drawing_px"][0])) / denominator
    x = float(left["board_mm"][0]) + fraction * (float(right["board_mm"][0]) - float(left["board_mm"][0]))
    y = float(left["board_mm"][1]) + fraction * (float(right["board_mm"][1]) - float(left["board_mm"][1]))
    return x, y, fraction


# D94 and D98 form an independent full-row interpolation; D100 is held out.
check_x, check_y, _ = interpolate(anchors["D94"], anchors["D98"],
                                  float(anchors["D100"]["drawing_px"][0]))
observed = anchors["D100"]["board_mm"]
check_error = math.hypot(check_x - float(observed[0]), check_y - float(observed[1]))
if check_error > 1.5:
    raise SystemExit(f"FDC UPPER ASSEMBLY PLACEMENT: D100 check error {check_error:.3f} mm")

board = pcbnew.LoadBoard(str(BOARD))
targets = []
for item in document["targets"]:
    left, right = (anchors[refdes] for refdes in item["between"])
    x, y, fraction = interpolate(left, right, float(item["drawing_px"][0]))
    footprint = board.FindFootprintByReference(item["refdes"])
    current = None
    delta = None
    if footprint is not None:
        pads = [pad.GetPosition() for pad in footprint.Pads()]
        current = [round(sum(pcbnew.ToMM(point.x) for point in pads) / len(pads), 3),
                   round(sum(pcbnew.ToMM(point.y) for point in pads) / len(pads), 3)]
        delta = [round(x-current[0], 3), round(y-current[1], 3)]
    targets.append({"refdes": item["refdes"], "between": item["between"],
                    "fraction": round(fraction, 6),
                    "projected_board_mm": [round(x, 3), round(y, 3)],
                    "current_footprint_mm": current, "projected_delta_mm": delta,
                    "observation": item["observation"], "electrical_evidence": False})

OUTPUT_JSON.write_text(json.dumps({"schema_version": 1,
                                  "source": RECORD.relative_to(ROOT).as_posix(),
                                  "held_out": {"refdes": "D100", "error_mm": round(check_error, 3)},
                                  "targets": targets,
                                  "d94_pullup_value_evidence": value_evidence,
                                  "d94_pullups": pullups}, indent=2) + "\n")
lines = ["# FDC upper assembly placement", "",
         "Status: **FACTORY PLACEMENT EVIDENCE / D94 PULL-UPS IDENTIFIED**", "",
         "The factory drawing places C12 between photo-fitted D94/D100 and C9 between",
         "photo-fitted D100/D98. Each target is interpolated only between its adjacent",
         "package centres. An independent D94-to-D98 interpolation predicts held-out",
         f"D100 within `{check_error:.3f}` mm.", "",
         "| Ref | Bracket | Fraction | Projected x,y mm | Current x,y mm | Delta mm | Observation |",
         "| --- | --- | ---: | ---: | ---: | ---: | --- |"]
for item in targets:
    projected = ", ".join(f"{value:.3f}" for value in item["projected_board_mm"])
    current = "absent" if item["current_footprint_mm"] is None else ", ".join(
        f"{value:.3f}" for value in item["current_footprint_mm"])
    delta = "-" if item["projected_delta_mm"] is None else ", ".join(
        f"{value:+.3f}" for value in item["projected_delta_mm"])
    lines.append(f"| {item['refdes']} | {'/'.join(item['between'])} | {item['fraction']:.6f} | "
                 f"{projected} | {current} | {delta} | {item['observation']} |")
lines += ["", "Neither owner-photo site exposes a complete electrical path: C12 has no",
          "unambiguous visible body and C9 is cable-obscured. These remain placement-only",
          "records and do not validate the inherited `.006` analog net assignments.", "",
          "## D94 pull-up row", "",
          "The same factory view labels the three vertical bodies immediately left of D94",
          "as R87, R88, and R89 from left to right. The owner component photograph preserves",
          "that order. Its reflected solder mate exposes three non-crossing signal traces and",
          "the common tinned +5 V rail, closing the resistor identities without inferring a",
          "hidden D94.1 consumer. A second, alternate-angle owner photo reads `6К2` on",
          "R87 and R88. R89 is partly socket-obscured but visually identical; the factory",
          "equipment list also assigns exactly three МЛТ-0,125 6.2 kΩ ±5% resistors",
          "to `ДГШ5.087.009`. Because that designation differs from the target",
          "`ДГШ5.109.009`, it is corroboration only; the photo-readable pair and identical",
          "third body are the target-board value evidence.", "",
          "| Ref | Value | Signal side | Proved nodes | Component signal px | Solder signal px |",
          "| --- | ---: | --- | --- | ---: | ---: |"]
for item in pullups:
    nodes = ", ".join(f"{ref}.{pin}" for ref, pin in item["signal_nodes"])
    component = ", ".join(f"{value:.1f}" for value in item["component_signal_px"])
    solder = ", ".join(f"{value:.1f}" for value in item["solder_signal_px"])
    lines.append(f"| {item['refdes']} | 6.2 kΩ | `{item['signal']}` | {nodes} | {component} | {solder} |")
lines += ["", "All three opposite resistor pads enter the same visibly tinned +5 V rail.",
          "R89 identifies the pull-up on D94.1, but the absence of an additional hidden",
          "branch remains a continuity/operating-capture boundary."]
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
print(f"FDC UPPER ASSEMBLY PLACEMENT: PASS; D100 check {check_error:.3f} mm")
