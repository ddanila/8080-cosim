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
    "D29": {
        "INHIB_STATUS_BOUNDARY": "3", "D29_AIN1_BOUNDARY": "2",
        "IOM_STATUS": "4", "MEMW": "1", "MEMR": "6",
        "AMW_N": "5", "IORD": "8", "IOWR": "7",
        "INHIB_N": "17", "CCLCK": "18", "IOM_N": "16", "MWC_N": "19",
        "MRC_N": "14", "AMWC_N": "15", "IORC_N": "12", "IOWC_N": "13",
    },
    "D23": {**{f"BA{i}": str(i + 1) for i in range(8)},
            **{f"ADR{i}_N": str(19 - i) for i in range(8)}},
    "D24": {**{f"BA{i + 8}": str(i + 1) for i in range(8)},
            **{f"ADR{'89ABCDEF'[i]}_N": str(19 - i) for i in range(8)}},
    "D25": {**{f"DB{i}": str(i + 1) for i in range(8)},
            **{f"DAT{i}_N": str(19 - i) for i in range(8)}},
    "D100": {**{f"DB{i}": str(i + 1) for i in range(8)},
             **{f"FDC_DAL{i}": str(19 - i) for i in range(8)}},
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
    for ref in ("D4", "D107", "D29", "D23", "D24", "D25"):
        actual = {pin: name for pin, name in chips[ref]["pins"].items() if pin in PHYSICAL}
        checks.append((f"{ref} uses the Intel DIP-20 logical pin names", actual == PHYSICAL))
        expected = EXPECTED_NET_PINS[ref]
        observed = {net: endpoint_net.get((ref, pin)) for net, pin in expected.items()}
        checks.append((f"{ref} address-channel pad assignments match sheet 1", observed == {n: n for n in expected}))

    d100 = chips["D100"]
    checks.append(("D100 uses the Intel 8287 DIP-20 pin names", d100["pins"] == PHYSICAL_D100))
    d100_expected = EXPECTED_NET_PINS["D100"]
    d100_observed = {net: endpoint_net.get(("D100", pin)) for net, pin in d100_expected.items()}
    checks.append(("D100 DB/DAL channel pad assignments follow the physical pairs", d100_observed == {n: n for n in d100_expected}))

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
    checks.append(("D4 LVS override preserves its routed high-address permutation", d4_map == expected_d4_map))
    d29_map = mapping["pinmaps"]["kicad_instance"]["D29"]
    expected_d29_map = {
        pin: f"AIN{i}" for i, pin in enumerate(("3", "2", "4", "1", "6", "5", "8", "7"))
    }
    expected_d29_map.update({
        pin: f"AOUT{i}" for i, pin in enumerate(("17", "18", "16", "19", "14", "15", "12", "13"))
    })
    checks.append(("D29 LVS override preserves its routed command permutation", d29_map == expected_d29_map))
    checks.append((
        "D7 pin 5 and D29 physical A2 pin 3 share the traced -INHIB source boundary",
        {
            (ref, str(pin))
            for ref, pin in board["nets"]["INHIB_STATUS_BOUNDARY"]["nodes"]
        } == {("D7", "5"), ("D29", "3")},
    ))

    failed = [name for name, ok in checks if not ok]
    if failed:
        raise SystemExit("8286 PINOUT AUDIT: FAIL: " + "; ".join(failed))

    lines = [
        "# 8286 transceiver pinout audit", "",
        "Status: **PHYSICAL PINOUT GUARDED**", "",
        "The original Intel `M8286/M8287 Octal Bus Transceiver` datasheet assigns",
        "A0-A7 to DIP pins 1-8 and the paired B0-B7 channels to pins 19-12.",
        "Sheet 1 routes D107 and D23-D25 straight, permutes D4's high-address",
        "channels, and permutes D29's eight command channels. Board pad endpoints",
        "and per-instance LVS maps preserve those routes while HDL keeps ordered",
        "logical buses. D100 independently preserves the same straight physical",
        "pairs between DB0-DB7 and the physical КР1818ВГ93 DAL bus.", "",
        "Primary pinout source:",
        "`https://www.silicon-ark.co.uk/datasheets/m8286-m8287-datasheet-intel.pdf`", "",
        "## Checks", "", "| Check | Result |", "| --- | --- |",
    ]
    lines.extend(f"| {name} | {'PASS' if ok else 'FAIL'} |" for name, ok in checks)
    OUT.write_text("\n".join(lines) + "\n")
    print(f"Wrote {OUT.relative_to(ROOT)}")
    print("8286 PINOUT AUDIT: PASS")


if __name__ == "__main__":
    main()
