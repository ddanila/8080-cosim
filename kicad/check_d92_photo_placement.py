#!/usr/bin/env python3
"""Guard the decapped D92 fit and its A11/A13 owner-pin coordinates."""
from __future__ import annotations

import cmath
import json
import math
from pathlib import Path

import pcbnew


ROOT = Path(__file__).resolve().parents[1]
BOARD = ROOT / "kicad/juku.kicad_pcb"
REPORT = ROOT / "docs/photo-registration/local-packages/report.json"


def image_centre(fit: dict) -> complex:
    points = list(fit["projected_pins"].values())
    return complex(
        sum(point[0] for point in points) / len(points),
        sum(point[1] for point in points) / len(points),
    )


def pad_centre(board: pcbnew.BOARD, refdes: str) -> complex:
    footprint = board.FindFootprintByReference(refdes)
    if footprint is None:
        raise SystemExit(f"D92 PHOTO PLACEMENT: missing {refdes}")
    pads = list(footprint.Pads())
    return complex(
        sum(pcbnew.ToMM(pad.GetPosition().x) for pad in pads) / len(pads),
        sum(pcbnew.ToMM(pad.GetPosition().y) for pad in pads) / len(pads),
    )


document = json.loads(REPORT.read_text(encoding="utf-8"))
fits = {(fit["refdes"], fit["side"]): fit for fit in document["fits"]}
required = {(refdes, "component") for refdes in ("D37", "D38", "D92")}
required |= {("D92", "solder")}
missing = required - fits.keys()
if missing:
    raise SystemExit(f"D92 PHOTO PLACEMENT: missing fits {sorted(missing)}")

component = fits[("D92", "component")]
solder = fits[("D92", "solder")]
if component["model"] != "affine" or solder["model"] != "affine":
    raise SystemExit("D92 PHOTO PLACEMENT: expected affine two-sided fits")

component_checks = {item["pin"]: item["error_px"] for item in component["checks"]}
for pin in ("4", "14"):
    if component_checks.get(pin, float("inf")) > 2.1:
        raise SystemExit(f"D92 PHOTO PLACEMENT: component pin {pin} residual drifted")
solder_checks = {item["pin"]: item["error_px"] for item in solder["checks"]}
for pin in ("4", "13", "14"):
    if solder_checks.get(pin, float("inf")) > 0.6:
        raise SystemExit(f"D92 PHOTO PLACEMENT: solder pin {pin} residual drifted")

if component["projected_pins"].get("1") != [2484.0, 2290.0]:
    raise SystemExit("D92 PHOTO PLACEMENT: component D92.1 coordinate drifted")
if component["projected_pins"].get("13") != [2654.333, 2345.833]:
    raise SystemExit("D92 PHOTO PLACEMENT: component D92.13 coordinate drifted")
if solder["projected_pins"].get("1") != [1382.0, 1949.0]:
    raise SystemExit("D92 PHOTO PLACEMENT: solder D92.1 coordinate drifted")
if solder["projected_pins"].get("13") != [1214.333, 2004.833]:
    raise SystemExit("D92 PHOTO PLACEMENT: solder D92.13 coordinate drifted")

board = pcbnew.LoadBoard(str(BOARD))


def estimate_from(anchor: str) -> complex:
    anchor_fit = fits[(anchor, "component")]
    scale = (
        float(anchor_fit["scale_px_per_mm"])
        + float(component["scale_px_per_mm"])
    ) / 2
    axis = cmath.rect(1.0, math.radians(float(anchor_fit["rotation_deg"])))
    delta = (image_centre(component) - image_centre(anchor_fit)) / (scale * axis)
    return pad_centre(board, anchor) + delta


d38_estimate = estimate_from("D38")
d37_estimate = estimate_from("D37")
spread = abs(d38_estimate - d37_estimate)
if spread > 2.0:
    raise SystemExit(f"D92 PHOTO PLACEMENT: D38/D37 estimates spread {spread:.3f} mm")
expected = (d38_estimate + d37_estimate) / 2
actual = pad_centre(board, "D92")
placement_error = abs(actual - expected)
if placement_error > 2.0:
    raise SystemExit(f"D92 PHOTO PLACEMENT: source centre error {placement_error:.3f} mm")

orientation = board.FindFootprintByReference("D92").GetOrientationDegrees() % 360
if min(orientation, 360.0 - orientation) > 0.01:
    raise SystemExit(f"D92 PHOTO PLACEMENT: expected 0 degrees, got {orientation:.3f}")

print(
    "D92 PHOTO PLACEMENT: PASS — "
    f"centre {actual.real:.3f},{actual.imag:.3f} mm; "
    f"D38/D37 spread {spread:.3f} mm; source residual {placement_error:.3f} mm; "
    "two-sided held-outs <=2.0 px"
)
