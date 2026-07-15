#!/usr/bin/env python3
"""Guard the reviewed-but-occluded A13 factory-wire landing regions."""
from __future__ import annotations

import json
from pathlib import Path

import pcbnew


ROOT = Path(__file__).resolve().parents[1]
REGISTRATION = (
    ROOT
    / "ref/photos/dgsh5-109-009-sb/factory-wire-landing-registration.json"
)
REPORT = ROOT / "docs/photo-registration/local-packages/report.json"
BOARD = ROOT / "kicad/juku.kicad_pcb"

registration = json.loads(REGISTRATION.read_text(encoding="utf-8"))
point = next((item for item in registration["points"] if item["point"] == 13), None)
if point is None:
    raise SystemExit("A13 FACTORY BOUNDARIES: point 13 is missing")
if point.get("status") != "image-registered/board-fit-pending":
    raise SystemExit("A13 FACTORY BOUNDARIES: pending status drifted")

endpoints = {item["terminal"]: item for item in point["endpoints"]}
expected = {
    "A13A": {
        "drawing_px": [467, 3851],
        "owner_pin": "D13.1",
        "component": [1426, 906],
        "solder": [3051, 1193.5],
        "phrases": ("immediately before C95", "horizontal factory-wire bundle"),
    },
    "A13B": {
        "drawing_px": [1625, 3443],
        "owner_pin": "D92.1",
        "component": [2484, 2290],
        "solder": [1382, 1949],
        "phrases": ("immediately after D38", "no 13", "A8/A9"),
    },
}
errors: list[str] = []
for terminal, wanted in expected.items():
    endpoint = endpoints.get(terminal)
    if endpoint is None:
        errors.append(f"missing {terminal}")
        continue
    if endpoint.get("drawing_px") != wanted["drawing_px"]:
        errors.append(f"{terminal} drawing coordinate drifted")
    if endpoint.get("board_mm") is not None or endpoint.get("island_assignment") is not None:
        errors.append(f"{terminal} was promoted without visible landing proof")
    evidence = endpoint.get("occlusion_evidence", {})
    if evidence.get("owner_pin") != wanted["owner_pin"]:
        errors.append(f"{terminal} owner pin drifted")
    owner_px = evidence.get("owner_pin_px", {})
    if owner_px.get("component") != wanted["component"]:
        errors.append(f"{terminal} component owner coordinate drifted")
    if owner_px.get("solder") != wanted["solder"]:
        errors.append(f"{terminal} solder owner coordinate drifted")
    proof = evidence.get("proof", "")
    for phrase in wanted["phrases"]:
        if phrase not in proof:
            errors.append(f"{terminal} proof lost {phrase!r}")

fits_document = json.loads(REPORT.read_text(encoding="utf-8"))
fits = {(fit["refdes"], fit["side"]): fit for fit in fits_document["fits"]}
for refdes, component_px, solder_px in (
    ("D13", [1426.0, 906.0], [3051.0, 1193.5]),
    ("D92", [2484.0, 2290.0], [1382.0, 1949.0]),
):
    component = fits.get((refdes, "component"), {})
    solder = fits.get((refdes, "solder"), {})
    if component.get("projected_pins", {}).get("1") != component_px:
        errors.append(f"{refdes}.1 component fit drifted")
    if solder.get("projected_pins", {}).get("1") != solder_px:
        errors.append(f"{refdes}.1 solder fit drifted")

board = pcbnew.LoadBoard(str(BOARD))
for refdes in ("D13", "D92"):
    footprint = board.FindFootprintByReference(refdes)
    pad = footprint.FindPadByNumber("1") if footprint else None
    if pad is None or pad.GetNetname() != "ROE":
        errors.append(f"{refdes}.1 is not on ROE")

if errors:
    raise SystemExit("A13 FACTORY BOUNDARIES: FAIL\n- " + "\n- ".join(errors))

print(
    "A13 FACTORY BOUNDARIES: PASS — "
    "A13A C95/D30 corridor and A13B D38/R35 corridor remain occlusion-guarded; "
    "D13.1/D92.1 are fitted on both faces and both pending endpoints remain null"
)
