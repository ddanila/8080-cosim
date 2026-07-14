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
required = {("D13", "component"), ("D13", "solder")}
missing = required - fits.keys()
if missing:
    raise SystemExit(f"D13 PHOTO PLACEMENT: missing fits {sorted(missing)}")

component = fits[("D13", "component")]
solder = fits[("D13", "solder")]
if component["model"] != "affine":
    raise SystemExit("D13 PHOTO PLACEMENT: component fit is not affine")
if solder["model"] != "similarity_reflected":
    raise SystemExit("D13 PHOTO PLACEMENT: solder fit is not reflected")

component_checks = {item["pin"]: item["error_px"] for item in component["checks"]}
for pin in ("4", "14"):
    if component_checks.get(pin, float("inf")) > 0.1:
        raise SystemExit(
            f"D13 PHOTO PLACEMENT: component pin {pin} residual "
            f"{component_checks.get(pin)} px exceeds 0.1 px"
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

board = pcbnew.LoadBoard(str(BOARD))
footprint = board.FindFootprintByReference("D13")
if footprint is None:
    raise SystemExit("D13 PHOTO PLACEMENT: missing source footprint")
orientation = footprint.GetOrientationDegrees() % 360
if abs(orientation - 90.0) > 0.01:
    raise SystemExit(
        f"D13 PHOTO PLACEMENT: expected 90-degree package, got {orientation:.3f}"
    )

print(
    "D13 PHOTO PLACEMENT: PASS — "
    "D13.2 component 1369.0,906.0 px; solder 2989.5,1193.5 px; "
    "held-outs <=1.5 px"
)
