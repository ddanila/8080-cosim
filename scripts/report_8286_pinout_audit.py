#!/usr/bin/env python3
"""Guard the physical 8286 pinout and D4/D107 routed channel assignments."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BOARD = ROOT / "kicad/juku.board.json"
MAP = ROOT / "sync/map.json"
OUT = ROOT / "docs/8286-pinout-audit.md"

PHYSICAL = {
    **{str(pin): f"AIN{pin - 1}" for pin in range(1, 9)},
    "9": "OE_N",
    "11": "T",
    **{str(pin): f"AOUT{19 - pin}" for pin in range(12, 20)},
}
PHYSICAL_D100 = {
    **{str(pin): f"A{pin - 1}" for pin in range(1, 9)},
    "9": "OE_N", "10": "VSS_GND", "11": "T",
    **{str(pin): f"B{19 - pin}" for pin in range(12, 20)},
    "20": "VCC_5V",
}

EXPECTED_NET_PINS = {
    "D107": {**{f"A{i}": str(i + 1) for i in range(8)},
             **{f"BA{i}": str(19 - i) for i in range(8)}},
    "D4": {
        "A8": "8", "A9": "7", "A10": "1", "A11": "2",
        "A12": "5", "A13": "4", "A14": "3", "A15": "6",
        "BA8": "12", "BA9": "13", "BA10": "19", "BA11": "18",
        "BA12": "15", "BA13": "16", "BA14": "17", "BA15": "14",
    },
    "D23": {**{f"BA{i}": str(i + 1) for i in range(8)},
            **{f"ADR{i}_N": str(19 - i) for i in range(8)}},
    "D24": {**{f"BA{i + 8}": str(i + 1) for i in range(8)},
            **{f"ADR{'89ABCDEF'[i]}_N": str(19 - i) for i in range(8)}},
    "D25": {**{f"DB{i}": str(i + 1) for i in range(8)},
            **{f"DAT{i}_N": str(19 - i) for i in range(8)}},
    "D100": {
        "FDC_DIR_TO_D100": "1", "FDC_STEP_TO_D100": "2",
        "FDC_HLD_TO_D100": "3", "FDC_TG43_TO_D100": "4",
        "FDC_WG_TO_D100": "5", "FDC_PRECOMP_WRDATA": "6",
        "D99_Q2_BOUNDARY": "7", "FDC_SIDE_SEL": "8",
        "D99_Q2N_BOUNDARY": "9", "D100_CONTROL_SHEET1_BOUNDARY": "11",
        "X4_SIDE_SEL": "12", "X4_MOTOR_ON_N": "13",
        "X4_WR_DATA_N": "14", "X4_WR_GATE_N": "15",
        "X4_TG43": "16", "X4_HLOAD_N": "17",
        "X4_STEP_N": "18", "X4_DIR_N": "19",
    },
}


def main() -> None:
    board = json.loads(BOARD.read_text())
    mapping = json.loads(MAP.read_text())
    chips = {chip["ref"]: chip for chip in board["chips"]}
    endpoint_net = {}
    for name, entry in board["nets"].items():
        nodes = entry.get("nodes", []) if isinstance(entry, dict) else entry
        for ref, pin in nodes:
            endpoint_net[(ref, str(pin))] = name

    checks = []
    for ref in ("D4", "D107", "D23", "D24", "D25"):
        actual = {pin: name for pin, name in chips[ref]["pins"].items() if pin in PHYSICAL}
        checks.append((f"{ref} uses the Intel DIP-20 logical pin names", actual == PHYSICAL))
        expected = EXPECTED_NET_PINS[ref]
        observed = {net: endpoint_net.get((ref, pin)) for net, pin in expected.items()}
        checks.append((f"{ref} channel pad assignments match sheet 1", observed == {n: n for n in expected}))

    d29_actual = {pin: name for pin, name in chips["D29"]["pins"].items() if pin in PHYSICAL}
    checks.append(("D29 uses the Intel DIP-20 logical pin names", d29_actual == PHYSICAL))
    d29_exact_source = {
        "1": "PHI2TTL", "2": "AMW_N", "3": "INHIB_STATUS_BOUNDARY",
        "4": "IORD", "5": "IOWR", "6": "MEMR", "7": "D30_Q2N_D29_AIN7",
        "8": "MEMW", "12": "AMWC_N", "13": "MWC_N", "14": "MRC_N",
        "15": "IOWC_N", "16": "IORC_N", "17": "INHIB_N", "18": "IOM_N",
        "19": "CCLCK",
    }
    checks.append((
        "D29 physical input/output pads match all eight exact .009 sheet-1 rows",
        {pin: endpoint_net.get(("D29", pin)) for pin in d29_exact_source}
        == d29_exact_source,
    ))

    d100 = chips["D100"]
    checks.append(("D100 uses the Intel 8287 DIP-20 pin names", d100["pins"] == PHYSICAL_D100))
    d100_expected = EXPECTED_NET_PINS["D100"]
    d100_observed = {key: endpoint_net.get(("D100", pin)) for key, pin in d100_expected.items()}
    d100_expected_nets = {key: key for key in d100_expected}
    checks.append(("D100 drive-interface pad assignments follow factory sheet 3", d100_observed == d100_expected_nets))

    type_map = mapping["pinmaps"]["kicad"]["BUF8286"]
    checks.append(("LVS type pinmap follows A0-A7 pins 1-8 and B0-B7 pins 19-12", type_map == PHYSICAL))
    vabus_map = mapping["pinmaps"]["kicad"]["VABUS"]
    checks.append(("8287 LVS type pinmap follows the same physical channel pairs", vabus_map == PHYSICAL))
    checks.append(("D100 LVS pinmap follows the complete 8287 contract", mapping["pinmaps"]["kicad"]["BUF8287"] == PHYSICAL_D100))
    d4_map = mapping["pinmaps"]["kicad_instance"]["D4"]
    expected_d4_map = {
        pin: f"AIN{i}" for i, pin in enumerate(("8", "7", "1", "2", "5", "4", "3", "6"))
    }
    expected_d4_map.update({
        pin: f"AOUT{i}" for i, pin in enumerate(("12", "13", "19", "18", "15", "16", "17", "14"))
    })
    checks.append(("D4 LVS override preserves its source high-address permutation", d4_map == expected_d4_map))
    d29_map = mapping["pinmaps"]["kicad_instance"]["D29"]
    expected_d29_map = {
        pin: f"AIN{i}" for i, pin in enumerate(("3", "1", "2", "7", "6", "8", "4", "5"))
    }
    expected_d29_map.update({
        pin: f"AOUT{i}" for i, pin in enumerate(("17", "19", "18", "13", "14", "12", "16", "15"))
    })
    checks.append(("D29 LVS override preserves its source command permutation", d29_map == expected_d29_map))
    checks.append((
        "D7 pin 5 and D29 physical A2 pin 3 share the traced -INHIB source boundary",
        {
            (ref, str(pin))
            for ref, pin in board["nets"]["INHIB_STATUS_BOUNDARY"]["nodes"]
        } == {("D7", "5"), ("D29", "3")},
    ))
    checks.append((
        "D7 pin 4 and D29 physical pin 8 share the exact -MWR conductor",
        {("D7", "4"), ("D29", "8")} <= {
            (ref, str(pin))
            for ref, pin in board["nets"]["MEMW"]["nodes"]
        },
    ))
    checks.append((
        "D7 pin 3 joins D29 physical pin 2 but remains separate from qualified /WR",
        {("D7", "3"), ("D29", "2")} <= {
            (ref, str(pin))
            for ref, pin in board["nets"]["AMW_N"]["nodes"]
        }
        and endpoint_net.get(("D105", "3")) == "IOWR",
    ))

    failed = [name for name, ok in checks if not ok]

    lines = [
        "# 8286 transceiver pinout audit", "",
        "Status: **PHYSICAL PINOUT GUARDED / EXACT D29 SOURCE MAP HOLD**" if failed
        else "Status: **PHYSICAL PINOUT GUARDED**", "",
        "The original Intel `M8286/M8287 Octal Bus Transceiver` datasheet assigns",
        "A0-A7 to DIP pins 1-8 and the paired B0-B7 channels to pins 19-12.",
        "Sheet 1 routes D107 and D23-D25 straight, permutes D4's high-address",
        "channels, and permutes D29's eight command channels. The exact .009",
        "D29 row transcription is in `ref/schematics/d29-exact-009-pinmap-review.json`;",
        "the command rows match the exact .009 source map. Other checked",
        "pad endpoints and per-instance LVS maps use ordered logical buses.",
        "Factory sheets 1 and 3 prove that D100 instead buffers eight",
        "floppy-drive outputs. Its paired channels and separate pin-9 OE_N and",
        "pin-11 T nets are guarded independently of the data-bus devices.", "",
        "Primary pinout source:",
        "`https://www.silicon-ark.co.uk/datasheets/m8286-m8287-datasheet-intel.pdf`", "",
        "## Command", "",
        "Run from the repository root with Python 3 (standard library only).",
        "The command overwrites this report after its checks pass.", "", "```sh",
        "python3 scripts/report_8286_pinout_audit.py", "```", "",
        "## Checks", "", "| Check | Result |", "| --- | --- |",
    ]
    lines.extend(f"| {name} | {'PASS' if ok else 'FAIL'} |" for name, ok in checks)
    lines.extend([
        "", "## Scope", "",
        "This guard compares the listed main-board source contracts, net endpoints",
        "and LVS mapping data with fixed pinout/channel expectations. It does not",
        "run LVS, inspect routed copper, simulate turnaround timing or measure",
        "physical continuity. D100 control and remote-source boundaries remain",
        "subject to the [FDC handoff](fdc-hardware-handoff.md).",
    ])
    OUT.write_text("\n".join(lines) + "\n")
    print(f"Wrote {OUT.relative_to(ROOT)}")
    if failed:
        raise SystemExit("8286 PINOUT AUDIT: FAIL: " + "; ".join(failed))
    print("8286 PINOUT AUDIT: PASS")


if __name__ == "__main__":
    main()
