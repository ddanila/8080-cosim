#!/usr/bin/env python3
"""Guard the conflict-resolved .009 FDC write-precomp transcription."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = json.loads((ROOT / "kicad/juku.board.json").read_text(encoding="utf-8"))
HDL = (ROOT / "hdl/juku_top.v").read_text(encoding="utf-8")
LVS_MAP = json.loads((ROOT / "sync/map.json").read_text(encoding="utf-8"))
NETS = {name: {f"{ref}.{pin}" for ref, pin in item["nodes"]}
        for name, item in SPEC["nets"].items()}
COMPONENTS = {item["ref"]: item for item in SPEC["chips"]}

EXPECTED = {
    "FDC_PRECOMP_WRDATA": {"D101.9", "D100.6"},
    "FDC_EARLY_SEL": {"D93.17", "D101.2"},
    "FDC_LATE_SEL": {"D93.18", "D101.14"},
    "PRECOMP_TAP_1": {"D97.5", "D101.10"},
    "PRECOMP_TAP_2": {"D102.5", "D101.11"},
    "PRECOMP_TAP_3": {"D102.13", "D101.12"},
    "PRECOMP_CASCADE_1": {"D97.12", "D102.10"},
    "PRECOMP_CASCADE_2": {"D102.12", "D102.2"},
    "D97_RC1_C16": {"D97.15", "C16.1"},
    "D97_C1_C16": {"D97.14", "C16.2"},
    "D97_RC2_C19_R100": {"D97.7", "C19.1", "R100.1"},
    "D97_C2_C19_R86_TARGET": {"D97.6", "C19.2", "R86.1"},
    "D102_C2_C20": {"D102.6", "C20.1"},
    "D102_RC2_C20_R108": {"D102.7", "C20.2", "R108.1"},
    "D102_C1_C22": {"D102.14", "C22.1"},
    "D102_RC1_C22_R102": {"D102.15", "C22.2", "R102.1"},
    "FDC_WDATA_DELAY_IN": {"D93.31", "D97.10"},
    "D101_D02_R92_R99": {"D101.4", "R92.1", "R99.2"},
    "D94_A4_D101_Q0": {"D94.14", "D101.7"},
}

for name, nodes in EXPECTED.items():
    if NETS.get(name) != nodes:
        raise SystemExit(f"FDC PRECOMP: {name} {sorted(NETS.get(name, set()))} != {sorted(nodes)}")

for node in ("D97.3", "D97.11", "D102.3", "D102.11"):
    if node not in NETS["WREQ_N"]:
        raise SystemExit(f"FDC PRECOMP: {node} missing from WREQ_N")
for node in ("D97.1", "D97.9", "D102.1", "D102.9", "D101.13", "D101.15", "R99.1"):
    if node not in NETS["GND"]:
        raise SystemExit(f"FDC PRECOMP: {node} missing from GND")
for node in ("R100.2", "R102.2", "R108.2", "R86.2"):
    if node not in NETS["P5V"]:
        raise SystemExit(f"FDC PRECOMP: {node} missing from P5V")

actual_nc = {f"{ref}.{pin}" for ref, pin in SPEC.get("no_connects", [])}
for node in ("D97.13", "D102.4"):
    if node not in actual_nc:
        raise SystemExit(f"FDC PRECOMP: sheet-omitted output {node} is not NC")

for ref, value in {"R92": "1,3к", "R99": "4,7к", "R100": "12к", "R102": "12к",
                   "R108": "12к", "R86": "4,7к", "C20": "1,5 нФ", "C22": "1,5 нФ"}.items():
    if COMPONENTS[ref].get("value") != value:
        raise SystemExit(f"FDC PRECOMP: {ref} value drift")

obsolete = {"C19_1_R100_1_BOUNDARY", "C19_2_R86_1_BOUNDARY",
            "RIGHT_EDGE_RESISTOR_RAIL_BOUNDARY", "R102_1_BOUNDARY", "R108_1_BOUNDARY",
            "D97_Q1_BOUNDARY", "D102_Q1N_BOUNDARY"}
if obsolete & NETS.keys():
    raise SystemExit(f"FDC PRECOMP: obsolete boundaries returned: {sorted(obsolete & NETS.keys())}")

for ref in ("D97", "D101", "D102"):
    expected_instance = f"U_{ref}"
    if LVS_MAP["instances"].get(ref) != expected_instance:
        raise SystemExit(f"FDC PRECOMP: {ref} is outside LVS scope")
for marker in (
    "ag3_oneshot U_D97",
    "ag3_oneshot U_D102",
    "kp12_mux U_D101",
    ".q_n(fdc_raw_read)",
    ".q1(d100_wrdata_in_boundary)",
    ".q0(d94_a4_d101_q0)",
):
    if marker not in HDL:
        raise SystemExit(f"FDC PRECOMP: structural HDL marker missing: {marker}")
if "U_D100WDATALNK" in HDL:
    raise SystemExit("FDC PRECOMP: stale D100 write-data boundary returned")

print("FDC PRECOMP NETWORK: PASS")
