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

EXPECTED_NET_PINS = {
    "D107": {**{f"A{i}": str(i + 1) for i in range(8)},
             **{f"BA{i}": str(19 - i) for i in range(8)}},
    "D4": {
        "A8": "8", "A9": "7", "A10": "1", "A11": "2",
        "A12": "5", "A13": "4", "A14": "3", "A15": "6",
        "BA8": "12", "BA9": "13", "BA10": "19", "BA11": "18",
        "BA12": "15", "BA13": "16", "BA14": "17", "BA15": "14",
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
    for ref in ("D4", "D107"):
        actual = {pin: name for pin, name in chips[ref]["pins"].items() if pin in PHYSICAL}
        checks.append((f"{ref} uses the Intel DIP-20 logical pin names", actual == PHYSICAL))
        expected = EXPECTED_NET_PINS[ref]
        observed = {net: endpoint_net.get((ref, pin)) for net, pin in expected.items()}
        checks.append((f"{ref} address-channel pad assignments match sheet 1", observed == {n: n for n in expected}))

    type_map = mapping["pinmaps"]["kicad"]["BUF8286"]
    checks.append(("LVS type pinmap follows A0-A7 pins 1-8 and B0-B7 pins 19-12", type_map == PHYSICAL))
    d4_map = mapping["pinmaps"]["kicad_instance"]["D4"]
    expected_d4_map = {
        pin: f"AIN{i}" for i, pin in enumerate(("8", "7", "1", "2", "5", "4", "3", "6"))
    }
    expected_d4_map.update({
        pin: f"AOUT{i}" for i, pin in enumerate(("12", "13", "19", "18", "15", "16", "17", "14"))
    })
    checks.append(("D4 LVS override preserves its routed high-address permutation", d4_map == expected_d4_map))

    failed = [name for name, ok in checks if not ok]
    if failed:
        raise SystemExit("8286 PINOUT AUDIT: FAIL: " + "; ".join(failed))

    lines = [
        "# 8286 address-buffer pinout audit", "",
        "Status: **PHYSICAL PINOUT GUARDED**", "",
        "The original Intel `M8286/M8287 Octal Bus Transceiver` datasheet assigns",
        "A0-A7 to DIP pins 1-8 and the paired B0-B7 channels to pins 19-12.",
        "Sheet 1 routes D107 straight and deliberately permutes D4's high-address",
        "channels. The board pad endpoints and per-instance LVS map preserve that",
        "routing while HDL exposes ordered `A[15:0]`/`BA[15:0]` buses.", "",
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
