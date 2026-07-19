#!/usr/bin/env python3
"""Guard exact-revision D99 timing and distinct sheet-1 boundaries."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = ROOT / "kicad" / "juku.board.json"
HDL = ROOT / "hdl" / "juku_top.v"
PLACEMENT = ROOT / "ref/photos/dgsh5-109-009-sb/fdc-lower-placement-registration.json"


def main() -> None:
    spec = json.loads(SPEC.read_text(encoding="utf-8"))
    nets = spec["nets"]
    expected = {
        "D99_C2_TIMING": [["D99", "6"], ["C17", "2"]],
        "D99_RC2_TIMING": [["D99", "7"], ["C17", "1"], ["R97", "1"]],
        "D99_C1_TIMING": [["D99", "14"], ["C18", "2"]],
        "D99_RC1_TIMING": [["D99", "15"], ["C18", "1"], ["R103", "1"]],
        "D99_Q1_NC": [["D99", "13"]],
    }
    for name, nodes in expected.items():
        if nets.get(name, {}).get("nodes") != nodes:
            raise SystemExit(f"{name} changed: {nets.get(name, {}).get('nodes')}")
    for node in (["D99", "1"], ["D99", "3"]):
        if node not in nets["GND"]["nodes"]:
            raise SystemExit(f"D99 grounded input missing: {node}")
    for node in (["R97", "2"], ["R103", "2"]):
        if node not in nets["P5V"]["nodes"]:
            raise SystemExit(f"D99 timing pull-up missing: {node}")
    boundary_expected = {
        "D99_B2_SHEET1_BOUNDARY": [["D99", "10"]],
        "D100_CONTROL_SHEET1_BOUNDARY": [["D100", "9"], ["D100", "11"]],
    }
    for name, nodes in boundary_expected.items():
        if nets.get(name, {}).get("nodes") != nodes:
            raise SystemExit(f"{name} changed: {nets.get(name, {}).get('nodes')}")
    for node in (["D99", "10"], ["D100", "9"], ["D100", "11"]):
        if node in nets["P5V"]["nodes"]:
            raise SystemExit(f"sheet-1 continuation incorrectly tied high: {node}")
    stale = {
        "D100_CONTROL_1_BOUNDARY", "D99_A1N_BOUNDARY", "D99_B2_BOUNDARY",
        "D99_C1_BOUNDARY", "D99_RC1_BOUNDARY", "D99_C2_BOUNDARY",
        "D99_RC2_BOUNDARY", "D99_Q1_BOUNDARY",
    }
    returned = sorted(stale & nets.keys())
    if returned:
        raise SystemExit(f"stale D99 boundaries returned: {returned}")
    chips = {chip["ref"]: chip for chip in spec["chips"]}
    for ref, value in {"C17": "120 мкФ", "C18": "47 мкФ", "R97": "47к", "R103": "47к"}.items():
        if chips.get(ref, {}).get("value") != value:
            raise SystemExit(f"{ref} value/part missing")
    targets = {item["refdes"] for item in json.loads(PLACEMENT.read_text())["targets"]}
    if not {"C17", "C18", "R97", "R103"} <= targets:
        raise SystemExit("D99 timing-part factory placement registration incomplete")
    hdl = HDL.read_text(encoding="utf-8")
    for marker in ("ag3_oneshot U_D99", ".b2(d99_b2_sheet1_boundary)",
                   ".oe_n(d100_control_sheet1_boundary)",
                   ".t(d100_control_sheet1_boundary)"):
        if marker not in hdl:
            raise SystemExit(f"structural D99/D100 marker missing: {marker}")
    print("D99 SOURCE PATHS: PASS — timing networks closed; sheet-1 continuations remain distinct")


if __name__ == "__main__":
    main()
