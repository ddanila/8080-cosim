#!/usr/bin/env python3
"""Guard the two-sided D13 fit used to bound the A12 endpoint search."""
from __future__ import annotations

import json
from pathlib import Path

import pcbnew


ROOT = Path(__file__).resolve().parents[1]
BOARD = ROOT / "kicad/juku.kicad_pcb"
REPORT = ROOT / "docs/photo-registration/local-packages/report.json"

document = json.loads(REPORT.read_text(encoding="utf-8"))
fits = {(fit["refdes"], fit["side"]): fit for fit in document["fits"]}
required = {("D13", "component"), ("D13", "component-alt"), ("D13", "solder")}
missing = required - fits.keys()
if missing:
    raise SystemExit(f"D13 PHOTO PLACEMENT: missing fits {sorted(missing)}")

component = fits[("D13", "component")]
component_alt = fits[("D13", "component-alt")]
solder = fits[("D13", "solder")]
if component["model"] != "affine":
    raise SystemExit("D13 PHOTO PLACEMENT: component fit is not affine")
if component_alt["model"] != "affine":
    raise SystemExit("D13 PHOTO PLACEMENT: alternate component fit is not affine")
if solder["model"] != "similarity_reflected":
    raise SystemExit("D13 PHOTO PLACEMENT: solder fit is not reflected")

component_checks = {item["pin"]: item["error_px"] for item in component["checks"]}
for pin in ("4", "14"):
    if component_checks.get(pin, float("inf")) > 0.1:
        raise SystemExit(
            f"D13 PHOTO PLACEMENT: component pin {pin} residual "
            f"{component_checks.get(pin)} px exceeds 0.1 px"
        )

alt_checks = {item["pin"]: item["error_px"] for item in component_alt["checks"]}
for pin in ("4", "14"):
    if alt_checks.get(pin, float("inf")) > 0.1:
        raise SystemExit(
            f"D13 PHOTO PLACEMENT: alternate component pin {pin} residual "
            f"{alt_checks.get(pin)} px exceeds 0.1 px"
        )

solder_checks = {item["pin"]: item["error_px"] for item in solder["checks"]}
for pin in ("11", "1"):
    if solder_checks.get(pin, float("inf")) > 1.6:
        raise SystemExit(
            f"D13 PHOTO PLACEMENT: solder pin {pin} residual "
            f"{solder_checks.get(pin)} px exceeds 1.6 px"
        )

if component["projected_pins"].get("2") != [1369.0, 906.0]:
    raise SystemExit("D13 PHOTO PLACEMENT: component-side D13.2 coordinate drifted")
if solder["projected_pins"].get("2") != [2989.5, 1193.5]:
    raise SystemExit("D13 PHOTO PLACEMENT: solder-side D13.2 coordinate drifted")


def point(fit: dict, pin: str) -> complex:
    return complex(*fit["projected_pins"][pin])


def map_from_alt(candidate: complex, destination: dict) -> complex:
    """Map one point between local photos through the fitted D13 pad basis."""
    origin = point(component_alt, "1")
    x_basis = point(component_alt, "7") - origin
    y_basis = point(component_alt, "14") - origin
    determinant = x_basis.real * y_basis.imag - x_basis.imag * y_basis.real
    delta = candidate - origin
    x_weight = (delta.real * y_basis.imag - delta.imag * y_basis.real) / determinant
    y_weight = (x_basis.real * delta.imag - x_basis.imag * delta.real) / determinant
    return (
        point(destination, "1")
        + x_weight * (point(destination, "7") - point(destination, "1"))
        + y_weight * (point(destination, "14") - point(destination, "1"))
    )


# The alternate tile makes a loose/tinned white-wire end look like a surface
# joint at first glance. Both cross-view projections land on bare substrate;
# guard their reviewed coordinates so this false A12 candidate stays rejected.
wire_end_alt = complex(1405.0, 1479.0)
wire_end_component = map_from_alt(wire_end_alt, component)
wire_end_solder = map_from_alt(wire_end_alt, solder)
if abs(wire_end_component - complex(1627.770, 1070.144)) > 0.01:
    raise SystemExit("D13 PHOTO PLACEMENT: component wire-end projection drifted")
if abs(wire_end_solder - complex(3268.699, 1031.550)) > 0.01:
    raise SystemExit("D13 PHOTO PLACEMENT: solder wire-end projection drifted")

board = pcbnew.LoadBoard(str(BOARD))
footprint = board.FindFootprintByReference("D13")
if footprint is None:
    raise SystemExit("D13 PHOTO PLACEMENT: missing source footprint")
orientation = footprint.GetOrientationDegrees() % 360
if abs(orientation - 270.0) > 0.01:
    raise SystemExit(
        f"D13 PHOTO PLACEMENT: expected 270-degree right-facing package, got {orientation:.3f}"
    )

print(
    "D13 PHOTO PLACEMENT: PASS — "
    "D13.2 component 1369.0,906.0 px; solder 2989.5,1193.5 px; "
    "false wire end -> component 1627.8,1070.2 / solder 3268.7,1031.5 px; "
    "held-outs <=1.5 px"
)
