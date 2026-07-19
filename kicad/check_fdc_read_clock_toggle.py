#!/usr/bin/env python3
"""Guard the recovered .009 sheet-3 D96 read-clock toggle transcription."""
from __future__ import annotations

import csv
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
    "D96_TOGGLE_FEEDBACK": {"D96.2", "D96.6"},
    "SEP_D28_CLK": {"D28.8", "D96.3", "R85.1"},
    "FDC_RCLK": {"D96.5", "D93.26"},
    "D96_Q2_N_TEST_LANDING": {"D96.8"},
}
for name, expected in EXPECTED.items():
    if NETS.get(name, set()) != expected:
        raise SystemExit(f"FDC RCLK: {name} {sorted(NETS.get(name, set()))} != {sorted(expected)}")
missing_wreq = {"D96.1", "D96.4"} - NETS.get("WREQ_N", set())
if missing_wreq:
    raise SystemExit(f"FDC RCLK: WREQ_N missing {sorted(missing_wreq)}")

expected_nc = {f"D96.{pin}" for pin in ("9", "10", "11", "12", "13")}
actual_nc = {f"{ref}.{pin}" for ref, pin in BOARD.get("no_connects", [])}
if not expected_nc <= actual_nc:
    raise SystemExit(f"FDC RCLK: no-connects missing {sorted(expected_nc - actual_nc)}")

obsolete = {
    f"D96_{suffix}_BOUNDARY"
    for suffix in ("CLR1", "D1", "PRE1", "Q1N", "Q2", "PRE2", "CLK2", "D2", "CLR2")
}
returned = obsolete & NETS.keys()
if returned:
    raise SystemExit(f"FDC RCLK: obsolete boundaries returned: {sorted(returned)}")

endpoint_rows = {}
with (ROOT / "ref/photos/juku-pcb-2/endpoints.csv").open(newline="", encoding="utf-8") as handle:
    for row in csv.DictReader(handle):
        if row.get("endpoint_id") in {"seed-component-D96-8", "seed-solder-D96-8"}:
            endpoint_rows[row["endpoint_id"]] = row
if set(endpoint_rows) != {"seed-component-D96-8", "seed-solder-D96-8"}:
    raise SystemExit("FDC RCLK: accepted D96.8 test-landing evidence is missing")
for row in endpoint_rows.values():
    if row.get("review_state") != "accepted" or row.get("candidate_net") != "D96_Q2_N_TEST_LANDING":
        raise SystemExit(f"FDC RCLK: stale D96.8 evidence row {row.get('endpoint_id')}")

sources = {
    "PXL_20260718_101633062.jpg": "5f58dff9c2e1f8237f1c54e44a7ff5db2381b7c503d5e25466fcd219915f7047",
    "PXL_20260718_101644861.jpg": "8b8ad8abdf5cdf8c235cc942592ebe6c0019ec8ad90ae9958267fbc154bb0e67",
}
photo_dir = ROOT / "ref/photos/dgsh5-109-009-e3"
for name, expected in sources.items():
    payload = (photo_dir / name).read_bytes()
    if payload.startswith(b"version https://git-lfs.github.com/spec/v1\n"):
        pointer = payload.decode("ascii")
        match = re.search(r"^oid sha256:([0-9a-f]{64})$", pointer, re.MULTILINE)
        actual = match.group(1) if match else "invalid-lfs-pointer"
    else:
        actual = hashlib.sha256(payload).hexdigest()
    if actual != expected:
        raise SystemExit(f"FDC RCLK: source hash changed for {name}: {actual}")

hdl = (ROOT / "hdl/juku_top.v").read_text(encoding="utf-8")
for marker in ("tm2_dff #(.FUNCTIONAL(1)) U_D96", ".clr1_n(wreq_n)",
               ".d1(d96_q1_n)", ".clk1(d96_separator_clk)",
               ".pre1_n(wreq_n)", ".q1(fdc_rclk)", ".q1_n(d96_q1_n)"):
    if marker not in hdl:
        raise SystemExit(f"FDC RCLK: HDL missing {marker!r}")
mapping = json.loads((ROOT / "sync/map.json").read_text(encoding="utf-8"))
if mapping.get("instances", {}).get("D96") != "U_D96":
    raise SystemExit("FDC RCLK: D96 is not LVS-mapped to U_D96")

pcb = (ROOT / "kicad/juku.kicad_pcb").read_text(encoding="utf-8")
ref_pos = pcb.index('(property "Reference" "D96"')
footprint = pcb[pcb.rfind("\n\t(footprint", 0, ref_pos):pcb.find("\n\t(footprint", ref_pos)]
pcb_expected = {
    "1": "WREQ_N", "2": "D96_TOGGLE_FEEDBACK", "3": "SEP_D28_CLK",
    "4": "WREQ_N", "5": "FDC_RCLK", "6": "D96_TOGGLE_FEEDBACK",
    "8": "D96_Q2_N_TEST_LANDING", "9": None, "10": None, "11": None,
    "12": None, "13": None,
}
for pin, expected in pcb_expected.items():
    match = re.search(
        rf'\n\t\t\(pad "{pin}"[\s\S]*?(?=\n\t\t\(pad|\n\t\t\(embedded_fonts)',
        footprint,
    )
    if not match:
        raise SystemExit(f"FDC RCLK: source PCB missing D96 pad {pin}")
    net_match = re.search(r'\n\t\t\t\(net \d+ "([^"]+)"\)', match.group())
    actual = net_match.group(1) if net_match else None
    if actual != expected:
        raise SystemExit(f"FDC RCLK: source PCB D96.{pin} net {actual!r} != {expected!r}")

print("FDC RCLK: PASS — sheet 3 closes the D96 divide-by-two read-clock toggle")
