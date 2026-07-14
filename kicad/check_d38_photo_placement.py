#!/usr/bin/env python3
"""Guard D38 placement from independent component/solder fits relative to D41."""
from __future__ import annotations

import cmath
import json
import math
from pathlib import Path

import pcbnew


ROOT = Path(__file__).resolve().parents[1]
BOARD = ROOT / "kicad/juku.kicad_pcb"
REPORT = ROOT / "docs/photo-registration/local-packages/report.json"
MAX_CROSS_SIDE_SPREAD_MM = 1.25
MAX_PLACEMENT_ERROR_MM = 0.02


def image_centre(fit: dict) -> complex:
    points = list(fit["projected_pins"].values())
    return complex(
        sum(point[0] for point in points) / len(points),
        sum(point[1] for point in points) / len(points),
    )


def factor(fit: dict) -> complex:
    return cmath.rect(
        float(fit["scale_px_per_mm"]),
        math.radians(float(fit["rotation_deg"])),
    )


def pad_centre(board: pcbnew.BOARD, refdes: str) -> complex:
    footprint = board.FindFootprintByReference(refdes)
    if footprint is None:
        raise SystemExit(f"D38 PHOTO PLACEMENT: missing {refdes}")
    pads = list(footprint.Pads())
    return complex(
        sum(pcbnew.ToMM(pad.GetPosition().x) for pad in pads) / len(pads),
        sum(pcbnew.ToMM(pad.GetPosition().y) for pad in pads) / len(pads),
    )


document = json.loads(REPORT.read_text(encoding="utf-8"))
fits = {(fit["refdes"], fit["side"]): fit for fit in document["fits"]}
required = {
    ("D38", "component"),
    ("D38", "solder"),
    ("D41", "component"),
    ("D41", "solder"),
}
missing = required - fits.keys()
if missing:
    raise SystemExit(f"D38 PHOTO PLACEMENT: missing fits {sorted(missing)}")

d38_component = fits[("D38", "component")]
d38_solder = fits[("D38", "solder")]
d41_component = fits[("D41", "component")]
d41_solder = fits[("D41", "solder")]
if d38_component["image"] != d41_component["image"]:
    raise SystemExit("D38 PHOTO PLACEMENT: component fits do not share a raw photo")
if d38_solder["image"] != d41_solder["image"]:
    raise SystemExit("D38 PHOTO PLACEMENT: solder fits do not share a raw photo")

# Component fits map board x+iy directly into the raw image. Reflected solder
# fits map the conjugated board vector, so conjugate again after inversion.
component_delta = (
    image_centre(d38_component) - image_centre(d41_component)
) / ((factor(d38_component) + factor(d41_component)) / 2)
solder_delta = (
    (image_centre(d38_solder) - image_centre(d41_solder))
    / ((factor(d38_solder) + factor(d41_solder)) / 2)
).conjugate()
spread = abs(component_delta - solder_delta)
if spread > MAX_CROSS_SIDE_SPREAD_MM:
    raise SystemExit(
        f"D38 PHOTO PLACEMENT: cross-side spread {spread:.3f} mm exceeds "
        f"{MAX_CROSS_SIDE_SPREAD_MM:.3f} mm"
    )

board = pcbnew.LoadBoard(str(BOARD))
expected = pad_centre(board, "D41") + (component_delta + solder_delta) / 2
actual = pad_centre(board, "D38")
error = abs(actual - expected)
if error > MAX_PLACEMENT_ERROR_MM:
    raise SystemExit(
        f"D38 PHOTO PLACEMENT: D38 centre {actual.real:.3f},{actual.imag:.3f} mm; "
        f"expected {expected.real:.3f},{expected.imag:.3f} mm; error {error:.3f} mm"
    )
footprint = board.FindFootprintByReference("D38")
orientation = footprint.GetOrientationDegrees() % 360.0
if min(orientation, 360.0 - orientation) > 0.01:
    raise SystemExit(
        f"D38 PHOTO PLACEMENT: expected top-facing 0-degree package, got {orientation:.3f}"
    )

print(
    "D38 PHOTO PLACEMENT: PASS — "
    f"centre {actual.real:.3f},{actual.imag:.3f} mm; "
    f"component/solder spread {spread:.3f} mm"
)
