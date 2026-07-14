#!/usr/bin/env python3
"""Guard the D50/D51 pair from two-sided raw-photo fits referenced to D2."""
from __future__ import annotations

import cmath
import json
import math
from pathlib import Path

import pcbnew


ROOT = Path(__file__).resolve().parents[1]
BOARD = ROOT / "kicad/juku.kicad_pcb"
REPORT = ROOT / "docs/photo-registration/local-packages/report.json"
MAX_D2_D50_SPREAD_MM = 2.30
MAX_PAIR_SPREAD_MM = 1.25
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
        raise SystemExit(f"D50/D51 PHOTO PLACEMENT: missing {refdes}")
    pads = list(footprint.Pads())
    return complex(
        sum(pcbnew.ToMM(pad.GetPosition().x) for pad in pads) / len(pads),
        sum(pcbnew.ToMM(pad.GetPosition().y) for pad in pads) / len(pads),
    )


document = json.loads(REPORT.read_text(encoding="utf-8"))
fits = {(fit["refdes"], fit["side"]): fit for fit in document["fits"]}
required = {(refdes, side) for refdes in ("D2", "D50", "D51")
            for side in ("component", "solder")}
missing = required - fits.keys()
if missing:
    raise SystemExit(f"D50/D51 PHOTO PLACEMENT: missing fits {sorted(missing)}")
for side in ("component", "solder"):
    images = {fits[(refdes, side)]["image"] for refdes in ("D2", "D50", "D51")}
    if len(images) != 1:
        raise SystemExit(f"D50/D51 PHOTO PLACEMENT: {side} fits do not share a photo")


def photo_delta(left: str, right: str, side: str) -> complex:
    left_fit = fits[(left, side)]
    right_fit = fits[(right, side)]
    scale = (
        float(left_fit["scale_px_per_mm"])
        + float(right_fit["scale_px_per_mm"])
    ) / 2
    # D2 defines the raw photograph's board-axis direction. D50/D51 are
    # physically rotated 180 degrees, so their package-fit phase must not be
    # mistaken for a board-coordinate reflection when comparing centres.
    d2_fit = fits[("D2", side)]
    axis = cmath.rect(1.0, math.radians(float(d2_fit["rotation_deg"])))
    delta = (image_centre(right_fit) - image_centre(left_fit)) / (scale * axis)
    return delta if side == "component" else delta.conjugate()


d2_d50 = [photo_delta("D2", "D50", side) for side in ("component", "solder")]
d50_d51 = [photo_delta("D50", "D51", side) for side in ("component", "solder")]
d2_d50_spread = abs(d2_d50[0] - d2_d50[1])
pair_spread = abs(d50_d51[0] - d50_d51[1])
if d2_d50_spread > MAX_D2_D50_SPREAD_MM:
    raise SystemExit(
        f"D50/D51 PHOTO PLACEMENT: D2-D50 spread {d2_d50_spread:.3f} mm"
    )
if pair_spread > MAX_PAIR_SPREAD_MM:
    raise SystemExit(
        f"D50/D51 PHOTO PLACEMENT: pair spread {pair_spread:.3f} mm"
    )

board = pcbnew.LoadBoard(str(BOARD))
expected_d50 = pad_centre(board, "D2") + sum(d2_d50) / 2
expected_d51 = expected_d50 + sum(d50_d51) / 2
for refdes, expected in (("D50", expected_d50), ("D51", expected_d51)):
    actual = pad_centre(board, refdes)
    error = abs(actual - expected)
    if error > MAX_PLACEMENT_ERROR_MM:
        raise SystemExit(
            f"D50/D51 PHOTO PLACEMENT: {refdes} centre "
            f"{actual.real:.3f},{actual.imag:.3f}; expected "
            f"{expected.real:.3f},{expected.imag:.3f}; error {error:.3f} mm"
        )
    orientation = board.FindFootprintByReference(refdes).GetOrientationDegrees() % 360
    if abs(orientation - 180.0) > 0.01:
        raise SystemExit(
            f"D50/D51 PHOTO PLACEMENT: {refdes} orientation {orientation:.3f}, expected 180"
        )

print(
    "D50/D51 PHOTO PLACEMENT: PASS — "
    f"D50 {expected_d50.real:.3f},{expected_d50.imag:.3f} mm; "
    f"D51 {expected_d51.real:.3f},{expected_d51.imag:.3f} mm; "
    f"cross-side spreads {d2_d50_spread:.3f}/{pair_spread:.3f} mm"
)
