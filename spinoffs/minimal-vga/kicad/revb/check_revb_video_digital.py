#!/usr/bin/env python3
"""R5.V1 real-silicon and complete-pin guard for the rev-B Video card."""
from __future__ import annotations

import copy
import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
BOARD = HERE / "video.board.json"
AUDIT = HERE / "video-digital-audit.json"

# Digest of all 398 U1..U23 (reference, type, physical pin, net) records.  This is
# deliberately separate from the generator: any pin edit needs an explicit audit
# and digest update, while the structural LVS independently checks net membership.
EXPECTED_DIGEST = "36f159d0bf39753555ef0cafaa75e87f7a02bd7ebb2e7290b0910d374ca14e23"
EXPECTED_TYPES = {
    "U1":"OSC_25M175", "U2":"ST_HC393", "U3":"ST_HC393", "U4":"ST_HC393",
    "U5":"GAL22V10_HDEC", "U6":"GAL22V10_VDEC", "U7":"GAL22V10_CTRL",
    "U8":"ACT_157", "U9":"ACT_157", "U10":"ACT_157", "U11":"ACT_157",
    "U12":"ACT_161", "U13":"ACT_161", "U14":"ACT_161", "U15":"ACT_161",
    "U16":"TTL_283", "U17":"ACT_273", "U18":"ACT_273", "U19":"ALS_166",
    "U20":"HCT_245", "U21":"SRAM_FB", "U22":"HCT_08", "U23":"ACT_08",
}
PIN_COUNTS = {
    "OSC_25M175":4, "ST_HC393":14, "GAL22V10_HDEC":24, "GAL22V10_VDEC":24,
    "GAL22V10_CTRL":24, "ACT_157":16, "ACT_161":16, "TTL_283":16,
    "ACT_273":20, "ALS_166":16, "HCT_245":20, "SRAM_FB":32, "HCT_08":14, "ACT_08":14,
}

# High-consequence maps are written from the manufacturers' physical pin tables,
# not inferred from signal names or the generated board.  They caught the original
# shifted AS6C1008 and scrambled CD74HC283 definitions.
SRAM = {
    "1":"FB_PIN1_NC", "2":"GND", "3":"GND", "4":"SA12", "5":"SA7", "6":"SA6",
    "7":"SA5", "8":"SA4", "9":"SA3", "10":"SA2", "11":"SA1", "12":"SA0",
    "13":"FD0", "14":"FD1", "15":"FD2", "16":"GND", "17":"FD3", "18":"FD4",
    "19":"FD5", "20":"FD6", "21":"FD7", "22":"FB_CE_N", "23":"SA10",
    "24":"FB_OE_N", "25":"SA11", "26":"SA9", "27":"SA8", "28":"SA13",
    "29":"FB_WE_N", "30":"VCC5", "31":"GND", "32":"VCC5",
}
ADDER = {
    "1":"FBA12", "2":"VCC5", "3":"SI12", "4":"FBA11", "5":"SI11",
    "6":"VCC5", "7":"GND", "8":"GND", "9":"VID_ADD_C4_NC",
    "10":"VID_ADD_S3_NC", "11":"GND", "12":"GND", "13":"FBA13",
    "14":"SI13", "15":"GND", "16":"VCC5",
}
CTRL = {
    "1":"FETCH", "2":"A11", "3":"A12", "4":"A13", "5":"A14", "6":"A15",
    "7":"MREQ_N", "8":"RD_N", "9":"WR_N", "10":"MODE0", "11":"MODE1",
    "12":"GND", "13":"RESET_N", "14":"WAIT_N", "15":"MUX_SEL", "16":"D245_DIR",
    "17":"D245_OE", "18":"FB_CE_N", "19":"FB_WE_N", "20":"FB_OE_N",
    "21":"VID_CTRL_O21_NC", "22":"VID_CTRL_O22_NC", "23":"VID_CTRL_CPUACC_NC", "24":"VCC5",
}

# Every unused CMOS/PLD input is held at a rail. Outputs may remain unconnected.
TIED_INPUTS = {
    ("U11","10"):"GND", ("U11","11"):"GND", ("U11","13"):"GND", ("U11","14"):"GND",
    ("U15","5"):"GND", ("U15","6"):"GND",
    ("U16","7"):"GND", ("U16","11"):"GND", ("U16","12"):"GND", ("U16","15"):"GND",
    ("U18","17"):"GND", ("U18","18"):"GND",
    ("U23","12"):"GND", ("U23","13"):"GND",
}


def digest(chips: dict[str, dict]) -> str:
    lines = []
    for ref in sorted(chips, key=lambda r: int(r[1:])):
        chip = chips[ref]
        for pin, net in sorted(chip["pins"].items(), key=lambda item: int(item[0])):
            lines.append(f"{ref}:{chip['type']}:{pin}:{net}")
    return hashlib.sha256(("\n".join(lines) + "\n").encode()).hexdigest()


def verify(board: dict) -> list[str]:
    chips = {c["ref"]: c for c in board["chips"] if c["ref"].startswith("U")}
    errors: list[str] = []
    if set(chips) != set(EXPECTED_TYPES):
        errors.append(f"digital refs {sorted(chips)} != U1..U23")
    for ref, typ in EXPECTED_TYPES.items():
        if ref not in chips:
            continue
        if chips[ref]["type"] != typ:
            errors.append(f"{ref} type {chips[ref]['type']} != {typ}")
        if len(chips[ref]["pins"]) != PIN_COUNTS[typ]:
            errors.append(f"{ref} pin count {len(chips[ref]['pins'])} != {PIN_COUNTS[typ]}")
    for ref, expected in (("U21", SRAM), ("U16", ADDER), ("U7", CTRL)):
        if ref in chips and chips[ref]["pins"] != expected:
            errors.append(f"{ref} datasheet/intent pin map differs")
    for (ref, pin), net in TIED_INPUTS.items():
        if chips.get(ref, {}).get("pins", {}).get(pin) != net:
            errors.append(f"{ref}.{pin} unused input is not tied to {net}")

    # CPU data may reach framebuffer data only through U20; CPU addresses reach SRAM
    # only through U8..U11. WAIT is a shared open-drain bus net, not a data-path net.
    for bit in range(8):
        if chips["U20"]["pins"][str(2 + bit)] != f"D{bit}":
            errors.append(f"U20 CPU data A{bit} path wrong")
        if chips["U20"]["pins"][str(18 - bit)] != f"FD{bit}":
            errors.append(f"U20 framebuffer data B{bit} path wrong")
    if chips["U7"]["pins"]["14"] != "WAIT_N":
        errors.append("control GAL does not own WAIT_N")
    if chips["U5"]["pins"]["13"] != "RESET_N" or chips["U5"]["pins"]["21"] != "FETCH":
        errors.append("H-decode reset/fetch phase contract is absent")
    if chips["U5"]["pins"]["22"] != "RB_STROBE" or chips["U6"]["pins"]["1"] != "RB_STROBE":
        errors.append("per-line V-decode/divider clock contract is absent")
    if chips["U6"]["pins"]["13"] != "RESET_N" or chips["U7"]["pins"]["13"] != "RESET_N":
        errors.append("V-decode/control reset gating is absent")
    hct = chips["U22"]["pins"]
    if [hct[p] for p in ("4","5","6","9","10","8")] != [
            "H_END","H_END","H_CLR","V_END","V_END","V_CLR"]:
        errors.append("HCT reset-level translators are not wired as frozen")
    if [hct[p] for p in ("1","2","3","12","13","11")] != [
            "H_ACTIVE","V_ACTIVE","HV_ACTIVE","PIXEL","HV_ACTIVE","VID_PIXEL"]:
        errors.append("HCT two-axis pixel blanking is not wired as frozen")

    audit = json.loads(AUDIT.read_text())
    dot = audit["dot_clock_mhz"]
    for refs, family in audit["families"].items():
        if "fmax_min_mhz" in family and family["fmax_min_mhz"] <= dot:
            errors.append(f"{refs} has no guaranteed dot-clock margin")
    timing = audit["fetch_timing"]
    calc_available = timing["address_to_load_dots"] * 1000.0 / dot
    calc_path = sum(timing[k] for k in (
        "guarded_mux_delay_ns", "sram_access_ns", "guarded_shifter_setup_ns"))
    if abs(calc_available - timing["available_ns"]) > 1e-9:
        errors.append("fetch available-time arithmetic differs")
    if abs(calc_path - timing["path_ns"]) > 1e-9:
        errors.append("fetch path arithmetic differs")
    if abs(calc_available - calc_path - timing["margin_ns"]) > 1e-9 or timing["margin_ns"] < 20:
        errors.append("fetch timing margin is below the frozen 20 ns guard")
    wait = audit["wait_contract"]
    if abs(wait["worst_fetch_hold_ns"] - timing["fetch_window_dots"] * 1000.0 / dot) > 1e-9:
        errors.append("WAIT hold arithmetic differs")
    if digest(chips) != EXPECTED_DIGEST:
        errors.append("full 398-pin digital-map digest differs")
    return errors


def self_test(board: dict) -> list[str]:
    errors = []
    swapped = copy.deepcopy(board)
    u16 = next(c for c in swapped["chips"] if c["ref"] == "U16")
    u16["pins"]["3"], u16["pins"]["14"] = u16["pins"]["14"], u16["pins"]["3"]
    if not verify(swapped):
        errors.append("swapped-pin mutation escaped")
    missing = copy.deepcopy(board)
    u21 = next(c for c in missing["chips"] if c["ref"] == "U21")
    del u21["pins"]["22"]
    if not verify(missing):
        errors.append("missing-pin mutation escaped")
    return errors


def main() -> int:
    board = json.loads(BOARD.read_text())
    errors = verify(board)
    if "--self-test" in sys.argv:
        errors += self_test(board)
    if errors:
        for error in errors:
            print(f"REVB-VIDEO-DIGITAL: FAIL {error}", file=sys.stderr)
        return 1
    suffix = " + swapped/missing mutation controls" if "--self-test" in sys.argv else ""
    print(f"REVB-VIDEO-DIGITAL: PASS 23 packages / 398 pins{suffix}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
