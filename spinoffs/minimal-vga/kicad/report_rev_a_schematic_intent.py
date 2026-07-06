#!/usr/bin/env python3
import json
import sys
from collections import Counter
from pathlib import Path


BOARD_JSON = Path("spinoffs/minimal-vga/kicad/rev-a-physical.board.json")

EXPECTED_REFS = {
    "Core CPU/ROM/decode": {
        "U1": "Z80_DIP40",
        "U2": "ROM_28C256_DIP28",
        "U5": "GAL22V10_DIP24_DECODE",
    },
    "DRAM and arbitration": {
        **{f"U{index}": "DRAM4164_DIP16" for index in range(10, 18)},
        "U20": "74HCT157_DIP16_ADDRMUX",
        "U21": "74HCT157_DIP16_ADDRMUX",
        "U22": "74HCT393_DIP14_REFRESH_LOW",
        "U23": "74HCT393_DIP14_VIDEO_LOW",
        "U24": "GAL22V10_DIP24_DRAMSEQ",
    },
    "Keyboard": {
        "U30": "PPI_82C55_DIP40",
        "U31": "74HCT148_DIP16",
        "J30": "KEYBOARD_HEADER",
    },
    "Video/VGA": {
        "U40": "TTL640X480_HEADER",
        "U41": "74HCT166_DIP16_PIXSHIFT",
        "J40": "VGA_HEADER",
    },
    "Power/clock/reset/debug": {
        "J1": "POWER_INPUT_TERMINAL",
        "J3": "USB_C_POWER_HRO",
        "F1": "FUSE_THT",
        "D1": "D_TVS_THT",
        "U50": "OSC_DIP14",
        "U51": "RESET_SUPERVISOR_TO92",
        "J90": "DEBUG_HEADER",
        "J91": "DEBUG_HEADER",
        "J92": "DEBUG_HEADER",
        "J93": "POWER_DEBUG_HEADER",
    },
}

CORE_NETS = {
    "Address bus A0..A15": [f"A{index}" for index in range(16)],
    "Data bus D0..D7": [f"D{index}" for index in range(8)],
    "CPU control": ["CLK", "RESET_N", "MREQ_N", "IORQ_N", "RD_N", "WR_N", "M1_N", "RFSH_N", "WAIT_N"],
    "Decode outputs": ["ROM_CE_N", "RAM_CE_N", "PPI_CS_N", "MEM_RD_N", "MEM_WR_N", "IO_RD_N", "IO_WR_N"],
    "DRAM timing": ["RAS_N", "CAS_N", "DRAM_WE_N", "ADDRMUX_SEL", "ADDRMUX_OE_N", "REFRESH_TICK"],
    "Keyboard": [f"KBD_COL{index}" for index in range(8)]
    + [f"KBD_COL{index}_DRV" for index in range(8)]
    + [f"KBD_ROW{index}_N" for index in range(8)]
    + ["KBD_ROW_A0_N", "KBD_ROW_A1_N", "KBD_ROW_A2_N", "KBD_GS_N", "KBD_EN_N"],
    "Video/VGA": ["PIXCLK", "PIXEL", "PIX_LOAD_N", "VIDEO_REQ", "VIDEO_ACK", "HSYNC_N", "VSYNC_N", "BLANK_N", "VGA_R", "VGA_G", "VGA_B"],
    "Power": ["VCC_RAW", "VCC", "GND", "PWR_OK", "USB_CC1", "USB_CC2"],
}


def load_board(path):
    return json.loads(path.read_text())


def refs_by_name(board):
    return {chip["ref"]: chip for chip in board["chips"]}


def net_nodes(board, name):
    net = board["nets"].get(name)
    if net is None:
        return []
    if isinstance(net, dict):
        return [tuple(node) for node in net.get("nodes", [])]
    return [tuple(node) for node in net]


def has_node(board, net, ref, pin):
    return (ref, str(pin)) in net_nodes(board, net)


def table_row(values):
    return "| " + " | ".join(str(value).replace("|", "/") if value else "-" for value in values) + " |"


def add_check(rows, failures, section, check, passed, detail):
    rows.append([section, check, "PASS" if passed else "FAIL", detail])
    if not passed:
        failures.append(f"{section}: {check} ({detail})")


def validate_refs(board, rows, failures):
    refs = refs_by_name(board)
    for section, expected in EXPECTED_REFS.items():
        for ref, chip_type in expected.items():
            actual = refs.get(ref, {}).get("type")
            add_check(
                rows,
                failures,
                section,
                f"{ref} type",
                actual == chip_type,
                actual or "missing",
            )


def validate_core_nets(board, rows, failures):
    for section, nets in CORE_NETS.items():
        missing = [net for net in nets if not net_nodes(board, net)]
        add_check(
            rows,
            failures,
            section,
            "required nets present",
            not missing,
            "all present" if not missing else ", ".join(missing),
        )


def validate_bus_contract(board, rows, failures):
    cpu_address_pins = {
        0: 30,
        1: 31,
        2: 32,
        3: 33,
        4: 34,
        5: 35,
        6: 36,
        7: 37,
        8: 38,
        9: 39,
        10: 40,
        11: 1,
        12: 2,
        13: 3,
        14: 4,
        15: 5,
    }
    for index in range(16):
        net = f"A{index}"
        expected = [("U1", cpu_address_pins[index])]
        if index <= 14:
            expected.append(("U2", {0: 10, 1: 9, 2: 8, 3: 7, 4: 6, 5: 5, 6: 4, 7: 3, 8: 25, 9: 24, 10: 21, 11: 23, 12: 2, 13: 26, 14: 1}[index]))
        if index >= 13:
            expected.append(("U5", {13: 9, 14: 10, 15: 11}[index]))
        missing = [f"{ref}.{pin}" for ref, pin in expected if not has_node(board, net, ref, pin)]
        add_check(rows, failures, "Core CPU/ROM/decode", f"{net} endpoints", not missing, "ok" if not missing else ", ".join(missing))

    for index in range(8):
        net = f"D{index}"
        expected = [
            ("U1", {0: 14, 1: 15, 2: 12, 3: 8, 4: 7, 5: 9, 6: 10, 7: 13}[index]),
            ("U2", 11 + index if index <= 2 else 12 + index),
            (f"U{10 + index}", "2"),
            (f"U{10 + index}", "14"),
            ("U30", 34 - index),
            ("U41", {0: 2, 1: 3, 2: 4, 3: 5, 4: 10, 5: 11, 6: 12, 7: 14}[index]),
        ]
        missing = [f"{ref}.{pin}" for ref, pin in expected if not has_node(board, net, ref, pin)]
        add_check(rows, failures, "Core CPU/ROM/decode", f"{net} shared data slice", not missing, "ok" if not missing else ", ".join(missing))


def validate_decode_contract(board, rows, failures):
    expected = {
        "ROM_CE_N": [("U5", 13), ("U2", 20)],
        "RAM_CE_N": [("U5", 14), ("U24", 3)],
        "PPI_CS_N": [("U5", 15), ("U30", 6)],
        "MEM_RD_N": [("U5", 16), ("U2", 22), ("U24", 4)],
        "MEM_WR_N": [("U5", 17), ("U2", 27), ("U24", 5)],
        "IO_RD_N": [("U5", 18), ("U30", 5)],
        "IO_WR_N": [("U5", 19), ("U30", 36)],
        "WAIT_N": [("U1", 24), ("U5", 22), ("U24", 17)],
    }
    for net, nodes in expected.items():
        missing = [f"{ref}.{pin}" for ref, pin in nodes if not has_node(board, net, ref, pin)]
        add_check(rows, failures, "Core CPU/ROM/decode", f"{net} contract", not missing, "ok" if not missing else ", ".join(missing))


def validate_dram_contract(board, rows, failures):
    for net, pin in [("RAS_N", 4), ("CAS_N", 15), ("DRAM_WE_N", 3)]:
        expected = [("U24", {"RAS_N": 13, "CAS_N": 14, "DRAM_WE_N": 15}[net])]
        expected.extend((f"U{index}", pin) for index in range(10, 18))
        missing = [f"{ref}.{node_pin}" for ref, node_pin in expected if not has_node(board, net, ref, node_pin)]
        add_check(rows, failures, "DRAM and arbitration", f"{net} to all DRAMs", not missing, "ok" if not missing else ", ".join(missing))

    for index in range(8):
        net = f"DRAM_A{index}"
        expected_dram = [(f"U{ref}", {0: 5, 1: 7, 2: 6, 3: 12, 4: 11, 5: 10, 6: 13, 7: 9}[index]) for ref in range(10, 18)]
        missing = [f"{ref}.{pin}" for ref, pin in expected_dram if not has_node(board, net, ref, pin)]
        add_check(rows, failures, "DRAM and arbitration", f"{net} fanout", not missing, "ok" if not missing else ", ".join(missing))

    mux_expect = {
        "ADDRMUX_SEL": [("U20", 1), ("U21", 1), ("U24", 16)],
        "ADDRMUX_OE_N": [("U20", 15), ("U21", 15)],
        "VIDEO_REQ": [("U40", 7), ("U24", 7)],
        "VIDEO_ACK": [("U40", 8), ("U24", 18)],
        "REFRESH_TICK": [("U24", 19), ("J92", 5)],
    }
    for net, nodes in mux_expect.items():
        missing = [f"{ref}.{pin}" for ref, pin in nodes if not has_node(board, net, ref, pin)]
        add_check(rows, failures, "DRAM and arbitration", f"{net} contract", not missing, "ok" if not missing else ", ".join(missing))


def validate_keyboard_contract(board, rows, failures):
    for index in range(8):
        drv = f"KBD_COL{index}_DRV"
        out = f"KBD_COL{index}"
        resistor = f"R{16 + index}"
        expected_drv = [("U30", {0: 4, 1: 3, 2: 2, 3: 1, 4: 40, 5: 39, 6: 38, 7: 37}[index]), (resistor, 1)]
        expected_out = [(resistor, 2), ("J30", 1 + index)]
        missing = [f"{ref}.{pin}" for ref, pin in expected_drv if not has_node(board, drv, ref, pin)]
        missing += [f"{ref}.{pin}" for ref, pin in expected_out if not has_node(board, out, ref, pin)]
        add_check(rows, failures, "Keyboard", f"column {index} drive/header", not missing, "ok" if not missing else ", ".join(missing))

    for index in range(7):
        net = f"KBD_ROW{index}_N"
        resistor = f"R{7 + index}"
        expected = [("U31", {0: 10, 1: 11, 2: 12, 3: 13, 4: 1, 5: 2, 6: 3}[index]), (resistor, 2), ("J30", 9 + index)]
        missing = [f"{ref}.{pin}" for ref, pin in expected if not has_node(board, net, ref, pin)]
        add_check(rows, failures, "Keyboard", f"row {index} pullup/header", not missing, "ok" if not missing else ", ".join(missing))

    expected = {
        "KBD_ROW_A0_N": [("U31", 9), ("U30", 14)],
        "KBD_ROW_A1_N": [("U31", 7), ("U30", 15)],
        "KBD_ROW_A2_N": [("U31", 6), ("U30", 16)],
        "KBD_GS_N": [("U31", 14), ("U30", 17)],
        "KBD_EN_N": [("U31", 5), ("R15", 1)],
    }
    for net, nodes in expected.items():
        missing = [f"{ref}.{pin}" for ref, pin in nodes if not has_node(board, net, ref, pin)]
        add_check(rows, failures, "Keyboard", f"{net} contract", not missing, "ok" if not missing else ", ".join(missing))


def validate_video_contract(board, rows, failures):
    expected = {
        "PIXEL": [("U40", 6), ("U41", 13), ("R1", 1), ("R2", 1), ("R3", 1)],
        "PIX_LOAD_N": [("U40", 11), ("U41", 15)],
        "PIXCLK": [("U40", 1), ("U41", 7)],
        "HSYNC_N": [("U40", 3), ("J40", 4)],
        "VSYNC_N": [("U40", 4), ("J40", 5)],
        "BLANK_N": [("U40", 5), ("J40", 7)],
        "VGA_R": [("R1", 2), ("J40", 1)],
        "VGA_G": [("R2", 2), ("J40", 2)],
        "VGA_B": [("R3", 2), ("J40", 3)],
    }
    for net, nodes in expected.items():
        missing = [f"{ref}.{pin}" for ref, pin in nodes if not has_node(board, net, ref, pin)]
        add_check(rows, failures, "Video/VGA", f"{net} contract", not missing, "ok" if not missing else ", ".join(missing))


def validate_power_clock_reset(board, rows, failures):
    expected = {
        "VCC_RAW": [("J1", 1), ("J3", "A9"), ("J3", "B9"), ("F1", 1)],
        "VCC": [("F1", 2), ("U1", 11), ("U2", 28), ("U30", 26), ("U50", 14), ("U51", 3)],
        "GND": [("J1", 2), ("J3", "A12"), ("J3", "B12"), ("U1", 29), ("U2", 14), ("U30", 7), ("U50", 7), ("U51", 1)],
        "CLK": [("U50", 8), ("U1", 6), ("U5", 1), ("U24", 1), ("R26", 1)],
        "RESET_N": [("U51", 2), ("U1", 26), ("U5", 2), ("U24", 2), ("U30", 35), ("U40", 2), ("U41", 9)],
        "OSC_OE_N": [("U50", 1), ("R4", 2)],
        "PWR_OK": [("R6", 2), ("R25", 1), ("J93", 3)],
    }
    for net, nodes in expected.items():
        missing = [f"{ref}.{pin}" for ref, pin in nodes if not has_node(board, net, ref, pin)]
        add_check(rows, failures, "Power/clock/reset/debug", f"{net} contract", not missing, "ok" if not missing else ", ".join(missing))

    decouplers = [chip for chip in refs_by_name(board).values() if chip["type"] == "C_DECOUPLE_THT"]
    add_check(
        rows,
        failures,
        "Power/clock/reset/debug",
        "decoupling capacitor count",
        len(decouplers) >= 25,
        str(len(decouplers)),
    )


def section_summary(rows):
    by_section = {}
    for section, _, status, _ in rows:
        counter = by_section.setdefault(section, Counter())
        counter[status] += 1
    return by_section


def build_report(board_path):
    board = load_board(board_path)
    rows = []
    failures = []

    validate_refs(board, rows, failures)
    validate_core_nets(board, rows, failures)
    validate_bus_contract(board, rows, failures)
    validate_decode_contract(board, rows, failures)
    validate_dram_contract(board, rows, failures)
    validate_keyboard_contract(board, rows, failures)
    validate_video_contract(board, rows, failures)
    validate_power_clock_reset(board, rows, failures)

    status = "READY" if not failures else "NOT READY"
    lines = [
        "# Rev A schematic intent review",
        "",
        f"Source: `{board_path}`",
        f"Status: **{status}**",
        "",
        "This report checks that the generated Rev A physical source model still",
        "matches the intended Z80, ROM, DRAM refresh/arbitration, keyboard, VGA,",
        "power, clock, and reset structure before order-time schematic review.",
        "",
        "It is a source-level contract check, not a replacement for final human",
        "schematic review of every symbol and pinout.",
        "",
        "## Summary",
        "",
        f"- Checks: {len(rows)}",
        f"- Failures: {len(failures)}",
        "",
        "| Section | PASS | FAIL |",
        "| --- | ---: | ---: |",
    ]
    for section, counter in section_summary(rows).items():
        lines.append(table_row([section, counter["PASS"], counter["FAIL"]]))

    lines.extend(["", "## Checks", "", "| Section | Check | Status | Detail |", "| --- | --- | --- | --- |"])
    lines.extend(table_row(row) for row in rows)

    if failures:
        lines.extend(["", "## Failures", ""])
        lines.extend(f"- {failure}" for failure in failures)

    lines.append("")
    return "\n".join(lines), status


def main():
    board_path = Path(sys.argv[1] if len(sys.argv) > 1 else BOARD_JSON)
    out_dir = Path(sys.argv[2] if len(sys.argv) > 2 else "fab/minimal-vga")
    report, status = build_report(board_path)
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / "schematic-intent-readiness.md"
    path.write_text(report)
    print(report)
    print(f"Wrote {path}")
    return 0 if status == "READY" else 3


if __name__ == "__main__":
    raise SystemExit(main())
