#!/usr/bin/env python3
"""Guard the recovered .009 sheet-3 D95 FDC clock-mux transcription."""
from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BOARD = json.loads((ROOT / "kicad/juku.board.json").read_text(encoding="utf-8"))
NETS = {
    name: {f"{ref}.{pin}" for ref, pin in item.get("nodes", [])}
    for name, item in BOARD["nets"].items()
}

EXPECTED = {
    "FDC_CLK": {"D95.7", "D93.24"},
    "FDC_SEPARATOR_CLOCK": {"D95.9", "D106.4"},
    "FDC_DRIVE_SIZE_5_8": {"D26.17", "D95.2"},
    "FDC_DDEN": {"D26.13", "D93.37", "D95.14", "R92.2"},
}
SUBSETS = {
    "LATCH_B": {"D40.11", "D95.5", "D95.6"},
    "D40Q2_D33": {"D40.12", "D95.3", "D95.4"},
    "D40Q1_D39": {"D40.13", "D95.11", "D95.12", "D95.13"},
    "D40QA": {"D40.14", "D95.10"},
    "GND": {"D95.1", "D95.15"},
}

for name, expected in EXPECTED.items():
    actual = NETS.get(name, set())
    if actual != expected:
        raise SystemExit(
            f"FDC CLOCK MUX: {name} {sorted(actual)} != {sorted(expected)}"
        )

for name, expected in SUBSETS.items():
    missing = expected - NETS.get(name, set())
    if missing:
        raise SystemExit(f"FDC CLOCK MUX: {name} missing {sorted(missing)}")

obsolete = {
    "D95_OE0_BOUNDARY", "D95_A1_BOUNDARY", "D95_D03_BOUNDARY",
    "D95_D02_BOUNDARY", "D95_D01_BOUNDARY", "D95_D00_BOUNDARY",
    "D95_Q0_BOUNDARY", "D95_Q1_BOUNDARY", "D95_D10_BOUNDARY",
    "D95_D11_BOUNDARY", "D95_D12_BOUNDARY", "D95_D13_BOUNDARY",
    "D95_A0_R92", "D95_OE1_BOUNDARY", "D106_DOWN_BOUNDARY",
    "D93_CLK_BOUNDARY", "FDC_DRIVE_SIZE_5_8_BOUNDARY",
}
returned = obsolete & NETS.keys()
if returned:
    raise SystemExit(f"FDC CLOCK MUX: obsolete boundaries returned: {sorted(returned)}")

chip = next(item for item in BOARD["chips"] if item["ref"] == "D95")
provenance = " ".join(str(value) for value in chip.get("prov", {}).values())
for marker in ("1 MHz", "2 MHz", "4 MHz", "8 MHz", "D93 CLK", "D106 DOWN"):
    if marker not in provenance:
        raise SystemExit(f"FDC CLOCK MUX: D95 provenance missing {marker!r}")

hdl = (ROOT / "hdl/juku_top.v").read_text(encoding="utf-8")
for marker in ("kp12_mux U_D95", ".clk(fdc_clk)",
               ".d0({clk2m, clk2m, clk1m, clk1m})",
               ".d1({clk4m, clk4m, clk4m, clk8m})"):
    if marker not in hdl:
        raise SystemExit(f"FDC CLOCK MUX: HDL missing {marker!r}")

mapping = json.loads((ROOT / "sync/map.json").read_text(encoding="utf-8"))
if mapping.get("instances", {}).get("D95") != "U_D95":
    raise SystemExit("FDC CLOCK MUX: D95 is not LVS-mapped to U_D95")

print("FDC CLOCK MUX: PASS — D95 selects 1/2 MHz VG93 and 4/8 MHz separator clocks")
