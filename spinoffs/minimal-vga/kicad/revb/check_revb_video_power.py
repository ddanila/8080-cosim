#!/usr/bin/env python3
"""R5.V2 decoupling, RGB-load and five-card current-budget gate."""
from __future__ import annotations

import copy
import json
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


def verify(board: dict, audit: dict) -> list[str]:
    errors: list[str] = []
    parts = {part["ref"]: part for part in board["chips"]}
    logic = {ref for ref in parts if ref.startswith("U")}
    caps = {ref for ref, part in parts.items() if part["type"] == "C_100N"}
    expected_caps = {f"C{i}" for i in range(1, audit["video_decouplers_100nf"] + 1)}
    if logic != {f"U{i}" for i in range(1, 24)}:
        errors.append("Video logic population is not U1..U23")
    if caps != expected_caps or len(caps) != len(logic):
        errors.append(f"100 nF set {sorted(caps)} does not cover every Video IC")
    for ref in caps:
        if parts[ref]["pins"] != {"1":"VCC5", "2":"GND"}:
            errors.append(f"{ref} is not across VCC5/GND")
    bulk = parts.get("C_BULK", {})
    if bulk.get("type") != "C_ELEC_47U" or bulk.get("pins") != {"1":"VCC5", "2":"GND"}:
        errors.append("47 uF local Video bulk capacitor missing")

    rgb = audit["rgb"]
    ideal_v = audit["rail_v"] * rgb["monitor_termination_ohm"] / (
        rgb["series_ohm"] + rgb["monitor_termination_ohm"])
    guard_v = rgb["guarded_driver_high_v"] * rgb["monitor_termination_ohm"] / (
        rgb["series_ohm"] + rgb["monitor_termination_ohm"])
    current = audit["rail_v"] * 1000 / (rgb["series_ohm"] + rgb["monitor_termination_ohm"])
    if not math.isclose(ideal_v, rgb["ideal_monitor_high_v"], abs_tol=1e-12):
        errors.append("ideal RGB divider arithmetic differs")
    if not math.isclose(guard_v, rgb["guarded_monitor_high_v"], abs_tol=1e-12):
        errors.append("guarded RGB divider arithmetic differs")
    if not math.isclose(current, rgb["ideal_driver_current_ma_per_channel"], abs_tol=1e-12):
        errors.append("RGB current arithmetic differs")
    if not (0.60 <= guard_v <= ideal_v <= 0.70):
        errors.append("470-ohm/75-ohm RGB levels are outside the frozen 0.60..0.70 V range")
    if current >= rgb["driver_current_rating_ma_per_channel"]:
        errors.append("RGB channel exceeds ACT driver rating")
    rgb_parts = (("R_VR","VID_R_DRV","VID_R"), ("R_VG","VID_G_DRV","VID_G"),
                 ("R_VB","VID_B_DRV","VID_B"))
    for ref, source, monitor in rgb_parts:
        if parts.get(ref, {}).get("type") != "R_470" or parts[ref]["pins"] != {"1":source,"2":monitor}:
            errors.append(f"{ref} is not the frozen 470-ohm series path")
    u23 = parts.get("U23", {}).get("pins", {})
    if [u23.get(p) for p in ("3","6","8")] != ["VID_R_DRV","VID_G_DRV","VID_B_DRV"]:
        errors.append("RGB channels do not have independent ACT outputs")
    if [parts["J_VGA"]["pins"][p] for p in ("1","2","3")] != ["VID_R","VID_G","VID_B"]:
        errors.append("DE-15 RGB pin order differs")

    power = audit["current_budget_ma"]
    video = power["video"]
    video_sum = sum(value for key, value in video.items() if key != "subtotal")
    if video_sum != video["subtotal"]:
        errors.append(f"Video current rows sum {video_sum}, not {video['subtotal']} mA")
    five = sum(power[key] for key in ("cpu","memory","io","backplane")) + video["subtotal"]
    if five != power["five_card_total"]:
        errors.append(f"five-card current rows sum {five}, not {power['five_card_total']} mA")
    headroom = power["qualified_supply_ma"] - five
    percent = 100 * headroom / power["qualified_supply_ma"]
    if headroom != power["supply_headroom_ma"] or not math.isclose(
            percent, power["supply_headroom_percent"], abs_tol=0.005):
        errors.append("2 A supply headroom arithmetic differs")
    if power["usb_branch_qualified_for_five_cards"] or power["usb_polyfuse_hold_ma"] >= five:
        errors.append("USB/polyfuse branch incorrectly qualified for full population")
    return errors


def main() -> int:
    board = json.loads((HERE / "video.board.json").read_text())
    audit = json.loads((HERE / "video-power-audit.json").read_text())
    errors = verify(board, audit)
    if "--self-test" in sys.argv:
        missing = copy.deepcopy(board)
        missing["chips"] = [part for part in missing["chips"] if part["ref"] != "C23"]
        if not verify(missing, audit):
            errors.append("missing-decoupler mutation escaped")
        shared = copy.deepcopy(board)
        u23 = next(part for part in shared["chips"] if part["ref"] == "U23")
        u23["pins"]["6"] = "VID_R_DRV"
        if not verify(shared, audit):
            errors.append("shared-RGB-driver mutation escaped")
    if errors:
        for error in errors:
            print(f"REVB-VIDEO-POWER: FAIL {error}", file=sys.stderr)
        return 1
    suffix = " + negative controls" if "--self-test" in sys.argv else ""
    print("REVB-VIDEO-POWER: PASS 23/23 decouplers, 47 uF bulk, "
          "0.606..0.688 V RGB, 1351 mA/2 A budget" + suffix)
    return 0


if __name__ == "__main__":
    sys.exit(main())
