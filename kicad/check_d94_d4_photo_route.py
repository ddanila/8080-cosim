#!/usr/bin/env python3
"""Guard the retracted D94.5-to-D93.1 photo-route interpretation."""
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
if ["D94", "5"] not in spec.get("no_connects", []):
    errors.append("D94.5 is not recorded as a PCB no-connect")
stub_nodes = {tuple(map(str, node)) for node in spec["nets"]["D93_1_OPEN_STUB"]["nodes"]}
if stub_nodes != {("D93", "1")}:
    errors.append(f"D93_1_OPEN_STUB nodes drifted: {sorted(stub_nodes)}")
source = spec["nets"]["D93_1_OPEN_STUB"].get("src", "")
for phrase in ("PXL_20260718_101633062", "open terminal", "D94.5"):
    if phrase not in source:
        errors.append(f"D93_1_OPEN_STUB provenance lost {phrase!r}")

board = pcbnew.LoadBoard(str(PCB))
pad = board.FindFootprintByReference("D94").FindPadByNumber("5")
if pad is None:
    errors.append("D94.5 pad is missing in the held source PCB")
d93_pad = board.FindFootprintByReference("D93").FindPadByNumber("1")
if d93_pad is None:
    errors.append("D93.1 pad is missing in the source PCB")

hdl = (ROOT / "hdl/juku_top.v").read_text(encoding="utf-8")
if ".nc_back_bias(d93_1_open_stub)" not in hdl:
    errors.append("structural D93 model does not preserve the pin-1 open-stub boundary")

if errors:
    raise SystemExit("D94 D4 PHOTO ROUTE: FAIL\n- " + "\n- ".join(errors))

print(
    "D94 D4 PHOTO ROUTE: PASS — full-resolution review retracts the route: "
    "D93.1 owns the open stub; D94.5 is a PCB no-connect"
)
