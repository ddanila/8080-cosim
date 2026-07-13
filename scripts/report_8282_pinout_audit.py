#!/usr/bin/env python3
"""Guard the complete physical D58 8282 latch package contract."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BOARD = ROOT / "kicad/juku.board.json"
MAP = ROOT / "sync/map.json"
OUT = ROOT / "docs/8282-pinout-audit.md"

PINOUT = {
    **{str(i + 1): f"D{i}" for i in range(8)},
    "9": "OE_N", "10": "VSS_GND", "11": "STB",
    **{str(19 - i): f"Q{i}" for i in range(8)},
    "20": "VCC_5V",
}
NET_PINS = {
    **{f"RDO{i}": str(i + 1) for i in range(8)},
    "RAM_RD_OE": "9", "GND": "10", "D58_STB_TAG5": "11",
    **{f"DB{i}": str(19 - i) for i in range(8)},
    "P5V": "20",
}


def main() -> None:
    board = json.loads(BOARD.read_text())
    mapping = json.loads(MAP.read_text())
    chip = next(chip for chip in board["chips"] if chip["ref"] == "D58")
    endpoint_net = {}
    for name, entry in board["nets"].items():
        nodes = entry.get("nodes", []) if isinstance(entry, dict) else entry
        for ref, pin in nodes:
            endpoint_net[(ref, str(pin))] = name

    observed = {net: endpoint_net.get(("D58", pin)) for net, pin in NET_PINS.items()}
    checks = [
        ("D58 declares the complete Intel 8282 DIP-20 pinout", chip["pins"] == PINOUT),
        ("D58 RDO/DB/control/power pad assignments match sheet 2", observed == {n: n for n in NET_PINS}),
        ("LVS IR82 pinmap includes the complete package contract", mapping["pinmaps"]["kicad"]["IR82"] == PINOUT),
    ]
    failed = [name for name, ok in checks if not ok]
    if failed:
        raise SystemExit("8282 PINOUT AUDIT: FAIL: " + "; ".join(failed))

    lines = [
        "# D58 8282 latch pinout audit", "",
        "Status: **PHYSICAL PINOUT GUARDED**", "",
        "The Intel 8282 contract places DI0-DI7 on pins 1-8, OE on pin 9,",
        "GND on pin 10, STB on pin 11, DO7-DO0 on pins 12-19, and +5 V on",
        "pin 20. Sheet 2 uses D58 as the DRAM read-data latch from `RDO0-7`",
        "to `DB0-7`; its OE and strobe remain separately traced boundaries.", "",
        "Intel datasheet scan: `https://datasheet4u.com/datasheet-pdf/Intel/M8282/pdf.php?id=727746`", "",
        "## Checks", "", "| Check | Result |", "| --- | --- |",
    ]
    lines.extend(f"| {name} | {'PASS' if ok else 'FAIL'} |" for name, ok in checks)
    OUT.write_text("\n".join(lines) + "\n")
    print(f"Wrote {OUT.relative_to(ROOT)}")
    print("8282 PINOUT AUDIT: PASS")


if __name__ == "__main__":
    main()
