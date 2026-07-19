#!/usr/bin/env python3
"""Guard the recovered .009 sheet-3 D106 recovery-counter transcription."""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BOARD = json.loads((ROOT / "kicad/juku.board.json").read_text(encoding="utf-8"))
NETS = {
    name: {f"{ref}.{pin}" for ref, pin in item.get("nodes", [])}
    for name, item in BOARD["nets"].items()
}

EXPECTED = {
    "D106_PRESET_HIGH": {"R78.1", "D106.1", "D106.5", "D106.9", "D106.10", "D106.15"},
    "FDC_SEPARATOR_CLOCK": {"D95.9", "D106.4"},
    "FDC_RAW_READ": {"D97.4", "D93.27", "D106.11"},
    "SEP_D106_Q3": {"D106.7", "D28.9"},
}
SUBSETS = {"P5V": {"R78.2"}, "GND": {"D106.14"}}
for name, expected in EXPECTED.items():
    if NETS.get(name, set()) != expected:
        raise SystemExit(f"FDC RECOVERY: {name} {sorted(NETS.get(name, set()))} != {sorted(expected)}")
for name, expected in SUBSETS.items():
    missing = expected - NETS.get(name, set())
    if missing:
        raise SystemExit(f"FDC RECOVERY: {name} missing {sorted(missing)}")

expected_nc = {f"D106.{pin}" for pin in ("2", "3", "6", "12", "13")}
actual_nc = {f"{ref}.{pin}" for ref, pin in BOARD.get("no_connects", [])}
if not expected_nc <= actual_nc:
    raise SystemExit(f"FDC RECOVERY: no-connects missing {sorted(expected_nc - actual_nc)}")

obsolete = {
    f"D106_{suffix}_BOUNDARY"
    for suffix in ("D1", "Q1", "Q0", "UP", "Q2", "D3", "D2", "LOAD", "CO", "BO", "CLR", "D0")
}
returned = obsolete & NETS.keys()
if returned:
    raise SystemExit(f"FDC RECOVERY: obsolete boundaries returned: {sorted(returned)}")

r78 = next(item for item in BOARD["chips"] if item["ref"] == "R78")
if not r78.get("pcb_placement_pending") or r78.get("value"):
    raise SystemExit("FDC RECOVERY: R78 must remain placement/value pending")
if r78.get("procurement", {}).get("action") != "circuit-review":
    raise SystemExit("FDC RECOVERY: R78 must remain a circuit-review item")

sources = {
    "PXL_20260718_101633062.jpg": "5f58dff9c2e1f8237f1c54e44a7ff5db2381b7c503d5e25466fcd219915f7047",
    "PXL_20260718_101644861.jpg": "8b8ad8abdf5cdf8c235cc942592ebe6c0019ec8ad90ae9958267fbc154bb0e67",
}
photo_dir = ROOT / "ref/photos/dgsh5-109-009-e3"
for name, expected in sources.items():
    actual = hashlib.sha256((photo_dir / name).read_bytes()).hexdigest()
    if actual != expected:
        raise SystemExit(f"FDC RECOVERY: source hash changed for {name}: {actual}")

hdl = (ROOT / "hdl/juku_top.v").read_text(encoding="utf-8")
for marker in ("ie7_ctr U_D106", "net_boundary U_D106PRESET", ".down(fdc_separator_clk)",
               ".load_n(fdc_raw_read)", ".d({4{d106_preset_high}})"):
    if marker not in hdl:
        raise SystemExit(f"FDC RECOVERY: HDL missing {marker!r}")
mapping = json.loads((ROOT / "sync/map.json").read_text(encoding="utf-8"))
if mapping.get("instances", {}).get("D106") != "U_D106":
    raise SystemExit("FDC RECOVERY: D106 is not LVS-mapped to U_D106")

pcb = (ROOT / "kicad/juku.kicad_pcb").read_text(encoding="utf-8")
ref_pos = pcb.index('(property "Reference" "D106"')
footprint = pcb[pcb.rfind("\n\t(footprint", 0, ref_pos):pcb.find("\n\t(footprint", ref_pos)]
pcb_expected = {
    "1": "D106_PRESET_HIGH", "2": None, "3": None,
    "4": "FDC_SEPARATOR_CLOCK", "5": "D106_PRESET_HIGH", "6": None,
    "7": "SEP_D106_Q3", "9": "D106_PRESET_HIGH", "10": "D106_PRESET_HIGH",
    "11": "FDC_RAW_READ", "12": None, "13": None, "14": "GND",
    "15": "D106_PRESET_HIGH",
}
for pin, expected in pcb_expected.items():
    match = re.search(
        rf'\n\t\t\(pad "{pin}"[\s\S]*?(?=\n\t\t\(pad|\n\t\t\(embedded_fonts)',
        footprint,
    )
    if not match:
        raise SystemExit(f"FDC RECOVERY: source PCB missing D106 pad {pin}")
    net_match = re.search(r'\n\t\t\t\(net \d+ "([^"]+)"\)', match.group())
    actual = net_match.group(1) if net_match else None
    if actual != expected:
        raise SystemExit(f"FDC RECOVERY: source PCB D106.{pin} net {actual!r} != {expected!r}")

print("FDC RECOVERY: PASS — sheet 3 closes D106 load, straps, clock, clear, Q3, and NCs")
