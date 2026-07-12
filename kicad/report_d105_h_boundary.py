#!/usr/bin/env python3
"""Guard the owner-measured D105 H/DBIN/MEMW connectivity."""
from __future__ import annotations

import json
from pathlib import Path

import pcbnew

ROOT = Path(__file__).resolve().parents[1]
BOARD_JSON = ROOT / "kicad/juku.board.json"
SOURCE = ROOT / "kicad/juku.kicad_pcb"
ROUTED = ROOT / "kicad/juku_routed.kicad_pcb"
HDL = ROOT / "hdl/juku_top.v"
REPORT = ROOT / "docs/d105-h-boundary.md"

spec = json.loads(BOARD_JSON.read_text(encoding="utf-8"))


def nodes(name: str) -> set[tuple[str, str]]:
    return {tuple(node) for node in spec["nets"].get(name, {}).get("nodes", [])}


def pad_net(board: pcbnew.BOARD, ref: str, pin: str) -> str:
    footprint = board.FindFootprintByReference(ref)
    return next(pad.GetNetname() for pad in footprint.Pads() if pad.GetNumber() == pin)


checks: list[tuple[str, bool, str]] = []
expected = {
    "D105_10_H": {("D105", "10"), ("D13", "13")},
    "DBIN": {("D1", "17"), ("D105", "9")},
    "DBIN_GATED": {("D105", "6"), ("D5", "4")},
    "D105_WAIT_STAGE": {("D105", "8"), ("D105", "4"), ("D105", "5")},
    "D105_MEMW_INV": {("D105", "11"), ("D30", "13")},
}
for name, wanted in expected.items():
    actual = nodes(name)
    checks.append((f"Source model preserves {name}", actual == wanted, str(sorted(actual))))
checks.append(("MEMW reaches tied D105 inputs",
               {("D105", "12"), ("D105", "13")} <= nodes("MEMW"),
               str(sorted(nodes("MEMW") & {("D105", "12"), ("D105", "13")}))))
checks.append(("H remains separate from derived -5 V",
               not (nodes("D105_10_H") & nodes("M5V_DERIVED")),
               str(sorted(nodes("M5V_DERIVED")))))

source = pcbnew.LoadBoard(str(SOURCE))
for ref, pin, wanted in (
    ("D105", "10", "D105_10_H"), ("D13", "13", "D105_10_H"),
    ("D1", "17", "DBIN"), ("D105", "9", "DBIN"),
    ("D105", "6", "DBIN_GATED"), ("D5", "4", "DBIN_GATED"),
    ("D105", "12", "MEMW"), ("D105", "13", "MEMW"),
):
    actual = pad_net(source, ref, pin)
    checks.append((f"Source PCB assigns {ref}.{pin} to {wanted}", actual == wanted, actual))

hdl = HDL.read_text(encoding="utf-8")
checks.append(("HDL models pulled-up H and gated DBIN",
               "tri1 d105_h" in hdl and ".a4(dbin), .b4(d105_h), .y4(d105_dbin_n)" in hdl
               and ".dbin(d105_dbin_gated)" in hdl,
               "hdl/juku_top.v"))

routed = pcbnew.LoadBoard(str(ROUTED))
routed_mismatches = []
for ref, pin, wanted in (
    ("D105", "10", "D105_10_H"), ("D105", "9", "DBIN"),
    ("D105", "6", "DBIN_GATED"), ("D5", "4", "DBIN_GATED"),
    ("D105", "12", "MEMW"), ("D105", "13", "MEMW"),
):
    actual = pad_net(routed, ref, pin)
    if actual != wanted:
        routed_mismatches.append(f"{ref}.{pin}: {actual} != {wanted}")
checks.append(("Invalid routed snapshot is explicitly stale",
               bool(routed_mismatches), "; ".join(routed_mismatches)))

ok = all(result for _, result, _ in checks)
status = "D105 H/DBIN HANDOFF ADOPTED / ROUTED REFRESH REQUIRED" if ok else "D105 HANDOFF FAILED"
lines = [
    "# D105 H/DBIN boundary", "", f"Status: **{status}**", "",
    "Direct owner continuity on the physical `.009` board supersedes the older",
    "interpretation of this package. D105.10 is the pulled-up edge-bus `H` net",
    "shared with D13.13, not the −5 V supply. CPU D1.17 `DBIN` reaches D105.9;",
    "D105.9/.10 feed one NAND and tied D105.4/.5 invert it again, so D105.6",
    "drives D5.4 as `DBIN AND H`. Tied D105.12/.13 receive `MEMW`, while",
    "D105.11 drives D30.13.", "",
    "The authoritative board JSON, source PCB, and HDL now preserve that measured",
    "topology. The routed PCB/DSN/SES predate it and remain deliberately stale:",
    "they must be regenerated after the separately documented placement collisions",
    "are resolved, not patched locally around invalid package placement.", "",
    "| Check | Result | Evidence |", "| --- | --- | --- |",
]
for name, result, evidence in checks:
    lines.append(f"| {name} | {'PASS' if result else 'FAIL'} | `{evidence}` |")
lines += [
    "", "## Rejected routed-snapshot repairs", "",
    "Earlier local copper trials attempted to preserve the obsolete routed netlist.",
    "They produced shorts or clearance failures around PHI2TTL, PHI2, RESIN, GND,",
    "RAM_OUT_EN, and the E3 control routing. Those trials remain rejected. The",
    "correct next operation is a complete routed refresh from the measured source",
    "netlist after collision-free placement, followed by DRC—not restoration of the",
    "old D2.12-to-D105.9 assumption or a hidden jumper.",
]
REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
print(status)
raise SystemExit(0 if ok else 1)
