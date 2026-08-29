#!/usr/bin/env python3
"""R5.I1 checker for the frozen rev-B D57, POST, clocks and decode contract."""
from __future__ import annotations

import json
import sys
from pathlib import Path


HERE = Path(__file__).resolve().parent


def parse_range(text: str) -> set[int]:
    lo_text, hi_text = text.replace("h", "").split("-")
    return set(range(int(lo_text, 16), int(hi_text, 16) + 1))


def main() -> int:
    errors: list[str] = []
    cfg = json.loads((HERE / "io-expansion.json").read_text())
    io = json.loads((HERE / "io.board.json").read_text())

    regions: dict[str, set[int]] = {}
    for entry in cfg["io_map"]:
        ports = parse_range(entry["decoded"])
        regions[entry["name"]] = ports
    names = list(regions)
    for i, left in enumerate(names):
        for right in names[i + 1:]:
            overlap = regions[left] & regions[right]
            if overlap:
                errors.append(f"I/O overlap {left}/{right}: {sorted(overlap)}")

    # Exhaust the exact select predicate over all ports and both M1 states.
    implemented = {n for n in ("PIC", "PPI0", "USART", "D57", "POST")}
    for port in range(256):
        for iorq_n in (0, 1):
            for m1_n in (0, 1):
                selected = [n for n in implemented if port in regions[n] and not iorq_n and m1_n]
                if len(selected) > 1:
                    errors.append(f"multiple selects at {port:02X}h IORQ={iorq_n} M1={m1_n}: {selected}")
                if (iorq_n or not m1_n) and selected:
                    errors.append(f"select outside ordinary I/O cycle at {port:02X}h: {selected}")
        if port in set().union(*(regions[n] for n in implemented)) and port >= 0x24:
            errors.append(f"implemented select aliases above 23h at {port:02X}h")

    if regions["D57"] != set(range(0x18, 0x1C)):
        errors.append("D57 is not exactly 18h-1Bh")
    if regions["POST"] != set(range(0x20, 0x24)):
        errors.append("POST is not exactly the documented 20h-23h decode group")

    chips = {chip["ref"]: chip for chip in io["chips"]}
    u7 = chips.get("U7", {}).get("pins", {})
    if u7.get("4") != "PIT_CLK0":
        errors.append("U7 pin 4 no longer routes the required master /4 tap to PIT_CLK0")

    baud = cfg["baud_tree"]
    master = baud["master_hz"]
    pit_in = master // baud["pit_input_divisor"]
    if master % baud["pit_input_divisor"] or pit_in != 1_228_800:
        errors.append(f"PIT input arithmetic is not exact: {pit_in}")
    pit_out = pit_in // cfg["timer"]["channels"][0]["required_count"]
    if pit_in % cfg["timer"]["channels"][0]["required_count"] or pit_out != 307_200:
        errors.append(f"PIT count-4 output is not 307200 Hz: {pit_out}")
    if pit_out // baud["usart_oversample"] != 19_200:
        errors.append("PIT output is not exact 19200 x16")
    direct_19200 = master // baud["direct_19200_divisor"] // baud["usart_oversample"]
    direct_9600 = master // baud["direct_9600_divisor"] // baud["usart_oversample"]
    if (direct_19200, direct_9600) != (19_200, 9_600):
        errors.append(f"direct recovery arithmetic wrong: {direct_19200}/{direct_9600}")

    timer = cfg["timer"]
    pins = timer["pins"]
    expected_power = {"11": "VCC5", "12": "GND", "14": "VCC5", "16": "VCC5", "18": "GND", "24": "VCC5"}
    # Gate pins 11/14/16 are deliberately tied high; only 12 and 24 are package power.
    for pin, net in expected_power.items():
        if pins.get(pin) != net:
            errors.append(f"timer pin {pin} must be {net}")
    channels = {c["channel"]: c for c in timer["channels"]}
    if set(channels) != {0, 1, 2}:
        errors.append("all three timer channels must be defined")
    if channels.get(2, {}).get("clock_net") != "GND" or channels.get(2, {}).get("gate_net") != "VCC5":
        errors.append("unused channel 2 inputs are not held at defined levels")

    gal = cfg["decode_gal"]
    if gal["part"] != "ATF22V10C-15PU" or gal["used_inputs"] > 11 or gal["used_outputs"] > 10:
        errors.append("decode does not fit the frozen ATF22V10 contract")
    required_gal_nets = {"IORQ_N", "M1_N", "WR_N", "PIT_CS_N", "POST_CLK", "INTA_N", "INT_N"}
    if not required_gal_nets.issubset(set(gal["pins"].values())):
        errors.append("decode GAL pinout omits a required control net")
    if not gal["rules"]["selects_require_M1_high"]:
        errors.append("decode contract does not exclude interrupt acknowledge")

    post = cfg["post"]
    led_ma = (post["rail_max_v"] - post["led_vf_min_v"]) / post["led_resistor_ohm"] * 1000
    if led_ma > 2.0:
        errors.append(f"POST LED worst current {led_ma:.3f} mA exceeds 2 mA design limit")
    stages = post["codes"]["stages"]
    if list(stages) != [str(i) for i in range(1, 9)]:
        errors.append("POST stage nibbles are not the complete ordered 1..8 set")
    if post["codes"]["ready"] != "FF" or post["codes"]["low_nibble"] != {"0": "entered", "1": "passed", "F": "failed"}:
        errors.append("POST result convention is incomplete")

    sound = cfg["sound"]
    base_ma = (5.0 - 0.85) / sound["base_resistor_ohm"] * 1000
    if base_ma < sound["rated_current_ma"] / 10:
        errors.append(f"sound transistor base drive too small: {base_ma:.3f} mA")

    power = cfg["power_allowance_ma"]
    if power["previous_io_card"] + power["added"] != power["revised_io_card"]:
        errors.append("I/O current subtotal does not add")
    if power["previous_five_card"] + power["added"] != power["revised_five_card"]:
        errors.append("five-card current subtotal does not add")
    if power["qualified_supply"] - power["revised_five_card"] != power["headroom"] or power["headroom"] <= 0:
        errors.append("qualified supply has no checked positive headroom")

    if errors:
        print("rev B I/O expansion contract FAILED:")
        for error in errors:
            print(f"- {error}")
        return 1
    print(
        "rev B I/O expansion contract PASS: D57 18h-1Bh, POST 20h-23h, "
        f"{pit_in} Hz/count-4 -> {pit_out} Hz -> 19200 baud; "
        f"LED <= {led_ma:.3f} mA each; added allowance {power['added']} mA"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
