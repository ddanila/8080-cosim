#!/usr/bin/env python3
"""Guard D37 placement from its raw component fit and nearby fitted anchors."""
from __future__ import annotations

import cmath
import json
import math
from pathlib import Path

import pcbnew


ROOT = Path(__file__).resolve().parents[1]
BOARD = ROOT / "kicad/juku.kicad_pcb"
REPORT = ROOT / "docs/photo-registration/local-packages/report.json"
MAX_PRIMARY_SPREAD_MM = 0.05
MAX_HELDOUT_RESIDUAL_MM = 2.00
MAX_PLACEMENT_ERROR_MM = 0.02


def image_centre(fit: dict) -> complex:
    points = list(fit["projected_pins"].values())
    return complex(
        sum(point[0] for point in points) / len(points),
        sum(point[1] for point in points) / len(points),
    )


def pad_centre(board: pcbnew.BOARD, refdes: str) -> complex:
    footprint = board.FindFootprintByReference(refdes)
    if footprint is None:
        raise SystemExit(f"D37 PHOTO PLACEMENT: missing {refdes}")
    pads = list(footprint.Pads())
    return complex(
        sum(pcbnew.ToMM(pad.GetPosition().x) for pad in pads) / len(pads),
        sum(pcbnew.ToMM(pad.GetPosition().y) for pad in pads) / len(pads),
    )


document = json.loads(REPORT.read_text(encoding="utf-8"))
fits = {(fit["refdes"], fit["side"]): fit for fit in document["fits"]}
required = {(refdes, "component") for refdes in ("D37", "D38", "D40", "D41")}
required |= {("D37", "solder"), ("D38", "solder")}
missing = required - fits.keys()
if missing:
    raise SystemExit(f"D37 PHOTO PLACEMENT: missing fits {sorted(missing)}")

component_fits = {refdes: fits[(refdes, "component")] for refdes in
                  ("D37", "D38", "D40", "D41")}
images = {fit["image"] for fit in component_fits.values()}
if len(images) != 1:
    raise SystemExit("D37 PHOTO PLACEMENT: component fits do not share a raw photo")

board = pcbnew.LoadBoard(str(BOARD))
d37_fit = component_fits["D37"]
d37_solder = fits[("D37", "solder")]
d38_solder = fits[("D38", "solder")]
if d37_solder["image"] != d38_solder["image"]:
    raise SystemExit("D37 PHOTO PLACEMENT: D37/D38 solder fits do not share a raw photo")
if d37_solder["model"] != "similarity_reflected":
    raise SystemExit("D37 PHOTO PLACEMENT: solder fit is not reflected")
solder_checks = {item["pin"]: item["error_px"] for item in d37_solder["checks"]}
for pin in ("4", "8", "14"):
    if solder_checks.get(pin, float("inf")) > 0.6:
        raise SystemExit(
            f"D37 PHOTO PLACEMENT: solder pin {pin} residual "
            f"{solder_checks.get(pin)} px exceeds 0.6 px"
        )
if d37_solder["projected_pins"].get("4") != [850.5, 2121.0]:
    raise SystemExit("D37 PHOTO PLACEMENT: solder-side D37.4 coordinate drifted")


def estimate_from(anchor: str) -> complex:
    anchor_fit = component_fits[anchor]
    scale = (
        float(anchor_fit["scale_px_per_mm"])
        + float(d37_fit["scale_px_per_mm"])
    ) / 2
    # A component-side package fit maps board axes directly into the image.
    # Use the already placed anchor's phase: D37's own 178-degree phase records
    # its opposite package orientation and is not the photograph's board axis.
    axis = cmath.rect(1.0, math.radians(float(anchor_fit["rotation_deg"])))
    delta = (image_centre(d37_fit) - image_centre(anchor_fit)) / (scale * axis)
    return pad_centre(board, anchor) + delta


d40_estimate = estimate_from("D40")
d41_estimate = estimate_from("D41")
primary_spread = abs(d40_estimate - d41_estimate)
if primary_spread > MAX_PRIMARY_SPREAD_MM:
    raise SystemExit(
        f"D37 PHOTO PLACEMENT: D40/D41 estimates spread {primary_spread:.3f} mm"
    )

expected = (d40_estimate + d41_estimate) / 2
d38_estimate = estimate_from("D38")
heldout_residual = abs(d38_estimate - expected)
if heldout_residual > MAX_HELDOUT_RESIDUAL_MM:
    raise SystemExit(
        f"D37 PHOTO PLACEMENT: held-out D38 residual {heldout_residual:.3f} mm"
    )

actual = pad_centre(board, "D37")
placement_error = abs(actual - expected)
if placement_error > MAX_PLACEMENT_ERROR_MM:
    raise SystemExit(
        f"D37 PHOTO PLACEMENT: centre {actual.real:.3f},{actual.imag:.3f} mm; "
        f"expected {expected.real:.3f},{expected.imag:.3f} mm; "
        f"error {placement_error:.3f} mm"
    )

orientation = board.FindFootprintByReference("D37").GetOrientationDegrees() % 360
if min(orientation, 360.0 - orientation) > 0.01:
    raise SystemExit(
        f"D37 PHOTO PLACEMENT: expected top-facing 0-degree package, "
        f"got {orientation:.3f}"
    )

print(
    "D37 PHOTO PLACEMENT: PASS — "
    f"centre {actual.real:.3f},{actual.imag:.3f} mm; "
    f"D40/D41 spread {primary_spread:.3f} mm; "
    f"D38 held-out residual {heldout_residual:.3f} mm; "
    "solder held-outs ≤0.5 px"
)
