#!/usr/bin/env python3
"""Guard the upper-row D39 package formerly mislabeled as D37."""
from __future__ import annotations

import cmath
import json
import math
from pathlib import Path

import pcbnew


ROOT = Path(__file__).resolve().parents[1]
BOARD = ROOT / "kicad/juku.kicad_pcb"
REPORT = ROOT / "docs/photo-registration/local-packages/report.json"
EVIDENCE = ROOT / "ref/photos/juku-pcb-2/cas-timing-row-registration.json"


def image_centre(fit: dict) -> complex:
    points = list(fit["projected_pins"].values())
    return complex(
        sum(point[0] for point in points) / len(points),
        sum(point[1] for point in points) / len(points),
    )


def pad_centre(board: pcbnew.BOARD, refdes: str) -> complex:
    footprint = board.FindFootprintByReference(refdes)
    if footprint is None:
        raise SystemExit(f"D39 PHOTO PLACEMENT: missing {refdes}")
    pads = list(footprint.Pads())
    return complex(
        sum(pcbnew.ToMM(pad.GetPosition().x) for pad in pads) / len(pads),
        sum(pcbnew.ToMM(pad.GetPosition().y) for pad in pads) / len(pads),
    )


document = json.loads(REPORT.read_text(encoding="utf-8"))
fits = {(fit["refdes"], fit["side"]): fit for fit in document["fits"]}
required = {(refdes, "component") for refdes in ("D39", "D38", "D40", "D41")}
required |= {("D39", "solder"), ("D38", "solder")}
missing = required - fits.keys()
if missing:
    raise SystemExit(f"D39 PHOTO PLACEMENT: missing fits {sorted(missing)}")

component_fits = {
    refdes: fits[(refdes, "component")] for refdes in ("D39", "D38", "D40", "D41")
}
if len({fit["image"] for fit in component_fits.values()}) != 1:
    raise SystemExit("D39 PHOTO PLACEMENT: component fits do not share a raw photo")

board = pcbnew.LoadBoard(str(BOARD))
d39_fit = component_fits["D39"]
d39_solder = fits[("D39", "solder")]
d38_solder = fits[("D38", "solder")]
if d39_solder["image"] != d38_solder["image"]:
    raise SystemExit("D39 PHOTO PLACEMENT: D39/D38 solder fits do not share a raw photo")
checks = {item["pin"]: item["error_px"] for item in d39_solder["checks"]}
for pin in ("4", "8", "14"):
    if checks.get(pin, float("inf")) > 0.6:
        raise SystemExit(f"D39 PHOTO PLACEMENT: solder pin {pin} residual drifted")


def estimate_from(anchor: str) -> complex:
    anchor_fit = component_fits[anchor]
    scale = (float(anchor_fit["scale_px_per_mm"]) + float(d39_fit["scale_px_per_mm"])) / 2
    axis = cmath.rect(1.0, math.radians(float(anchor_fit["rotation_deg"])))
    delta = (image_centre(d39_fit) - image_centre(anchor_fit)) / (scale * axis)
    return pad_centre(board, anchor) + delta


d40_estimate = estimate_from("D40")
d41_estimate = estimate_from("D41")
spread = abs(d40_estimate - d41_estimate)
if spread > 0.05:
    raise SystemExit(f"D39 PHOTO PLACEMENT: D40/D41 estimates spread {spread:.3f} mm")
expected = (d40_estimate + d41_estimate) / 2
if abs(estimate_from("D38") - expected) > 2.0:
    raise SystemExit("D39 PHOTO PLACEMENT: D38 held-out residual exceeds 2 mm")

registered = json.loads(EVIDENCE.read_text(encoding="utf-8"))["upper_row_reclassification"]
if registered["correct_refdes"] != "D39":
    raise SystemExit("D39 PHOTO PLACEMENT: reclassification evidence drifted")
actual = pad_centre(board, "D39")
if abs(actual - expected) > 0.02:
    raise SystemExit(
        f"D39 PHOTO PLACEMENT: centre {actual.real:.3f},{actual.imag:.3f} mm; "
        f"expected {expected.real:.3f},{expected.imag:.3f} mm"
    )
if abs(actual - complex(*registered["board_centre_mm"])) > 0.02:
    raise SystemExit("D39 PHOTO PLACEMENT: registered centre drifted")
orientation = board.FindFootprintByReference("D39").GetOrientationDegrees() % 360
if min(orientation, 360.0 - orientation) > 0.01:
    raise SystemExit("D39 PHOTO PLACEMENT: expected top-facing 0-degree package")

print(
    "D39 PHOTO PLACEMENT: PASS — upper-row D92-adjacent identity, two-sided "
    f"fit, centre {actual.real:.3f},{actual.imag:.3f} mm, and top notch guarded"
)
