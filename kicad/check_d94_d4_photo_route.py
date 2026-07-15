#!/usr/bin/env python3
"""Guard the exposed-socket D94.5 to D93.1 front-copper route."""
from __future__ import annotations

import json
from pathlib import Path

import pcbnew


ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "docs/photo-registration/local-packages/report.json"
BOARD_JSON = ROOT / "kicad/juku.board.json"
PCB = ROOT / "kicad/juku.kicad_pcb"

fits_document = json.loads(REPORT.read_text(encoding="utf-8"))
fits = {(fit["refdes"], fit["side"]): fit for fit in fits_document["fits"]}
required = {("D94", "component-alt"), ("D93", "component")}
missing = required - fits.keys()
if missing:
    raise SystemExit(f"D94 D4 PHOTO ROUTE: missing fits {sorted(missing)}")

d94 = fits[("D94", "component-alt")]
d93 = fits[("D93", "component")]
errors: list[str] = []
if d94.get("model") != "affine" or d93.get("model") != "affine":
    errors.append("D94/D93 exposed-socket fits are not affine")
if d94["projected_pins"].get("5") != [2477.0, 1768.714]:
    errors.append("D94.5 exposed-socket coordinate drifted")
if d93["projected_pins"].get("1") != [2215.0, 1810.0]:
    errors.append("D93.1 exposed-socket coordinate drifted")
checks = {item["pin"]: item["error_px"] for item in d94["checks"]}
if checks.get("4", float("inf")) > 0.8 or checks.get("9", float("inf")) > 0.1:
    errors.append("D94 exposed-socket held-out residual drifted")

spec = json.loads(BOARD_JSON.read_text(encoding="utf-8"))
nodes = {tuple(map(str, node)) for node in spec["nets"]["D94_D4"]["nodes"]}
if nodes != {("D94", "5"), ("D93", "1")}:
    errors.append(f"D94_D4 source nodes drifted: {sorted(nodes)}")
if ["D93", "1"] in spec.get("no_connects", []):
    errors.append("D93.1 is still recorded as a PCB no-connect")
source = spec["nets"]["D94_D4"].get("src", "")
for phrase in ("exposed-socket", "uninterrupted front copper", "internally NC/back-bias"):
    if phrase not in source:
        errors.append(f"D94_D4 provenance lost {phrase!r}")

board = pcbnew.LoadBoard(str(PCB))
for refdes, pin in (("D94", "5"), ("D93", "1")):
    pad = board.FindFootprintByReference(refdes).FindPadByNumber(pin)
    if pad is None or pad.GetNetname() != "D94_D4":
        errors.append(f"{refdes}.{pin} is not on D94_D4 in the source PCB")

hdl = (ROOT / "hdl/juku_top.v").read_text(encoding="utf-8")
if ".nc_back_bias(d94_d4)" not in hdl:
    errors.append("structural D93 model does not preserve the pin-1 board net")

if errors:
    raise SystemExit("D94 D4 PHOTO ROUTE: FAIL\n- " + "\n- ".join(errors))

print(
    "D94 D4 PHOTO ROUTE: PASS — D94.5 2477.0,1768.7 px reaches "
    "D93.1 2215.0,1810.0 px by uninterrupted exposed front copper; "
    "D93.1 is internally NC/back-bias, not a PCB no-connect"
)
