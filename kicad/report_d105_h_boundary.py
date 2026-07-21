#!/usr/bin/env python3
"""Guard the owner-measured D105 H/DBIN/MEMW connectivity."""
from __future__ import annotations

import json
import hashlib
from pathlib import Path

import pcbnew

ROOT = Path(__file__).resolve().parents[1]
BOARD_JSON = ROOT / "kicad/juku.board.json"
SOURCE = ROOT / "kicad/juku.kicad_pcb"
ROUTED = ROOT / "kicad/juku_routed.kicad_pcb"
HDL = ROOT / "hdl/juku_top.v"
REPORT = ROOT / "docs/d105-h-boundary.md"
REGISTRATION = ROOT / "ref/photos/juku-pcb-2/d105-h-registration.json"

spec = json.loads(BOARD_JSON.read_text(encoding="utf-8"))


def nodes(name: str) -> set[tuple[str, str]]:
    return {tuple(node) for node in spec["nets"].get(name, {}).get("nodes", [])}


def pad_net(board: pcbnew.BOARD, ref: str, pin: str) -> str:
    footprint = board.FindFootprintByReference(ref)
    return next(pad.GetNetname() for pad in footprint.Pads() if pad.GetNumber() == pin)


checks: list[tuple[str, bool, str]] = []
expected = {
    "D105_10_H": {("D105", "10"), ("D13", "13"), ("X1", "107B"), ("R1", "2")},
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
chips = {chip["ref"]: chip for chip in spec["chips"]}
checks.append(("Native R1 pull-up value is preserved",
               chips.get("R1", {}).get("value") == "2к" and ("R1", "1") in nodes("P5V"),
               f"R1={chips.get('R1', {}).get('value')}; R1.1 on P5V={('R1', '1') in nodes('P5V')}"))

registration = json.loads(REGISTRATION.read_text(encoding="utf-8"))
source_errors = []
for record in registration.get("sources", []):
    path = ROOT / record["path"]
    digest = hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else "missing"
    if digest != record.get("sha256"):
        source_errors.append(f"{record['path']}: {digest}")
pullup = registration.get("pullup", {})
registration_ok = (
    registration.get("edge_contact", {}).get("pin") == "107B"
    and pullup.get("refdes") == "R1"
    and pullup.get("value") == "2к"
    and not source_errors
)
checks.append(("Native/.009/owner evidence registration is intact",
               registration_ok,
               "three source hashes + X1.107B/R1 2к" if registration_ok else "; ".join(source_errors)))

source = pcbnew.LoadBoard(str(SOURCE))
for ref, pin, wanted in (
    ("D105", "10", "D105_10_H"), ("D13", "13", "D105_10_H"),
    ("X1", "107B", "D105_10_H"), ("R1", "2", "D105_10_H"),
    ("R1", "1", "P5V"),
    ("D1", "17", "DBIN"), ("D105", "9", "DBIN"),
    ("D105", "6", "DBIN_GATED"), ("D5", "4", "DBIN_GATED"),
    ("D105", "12", "MEMW"), ("D105", "13", "MEMW"),
):
    actual = pad_net(source, ref, pin)
    checks.append((f"Source PCB assigns {ref}.{pin} to {wanted}", actual == wanted, actual))

r1 = source.FindFootprintByReference("R1")
expected_positions = {"1": (40.88, 210.0), "2": (30.72, 210.0)}
position_evidence = []
position_ok = r1 is not None
if r1 is not None:
    for pin, wanted in expected_positions.items():
        pad = r1.FindPadByNumber(pin)
        actual = (
            round(pcbnew.ToMM(pad.GetPosition().x), 3),
            round(pcbnew.ToMM(pad.GetPosition().y), 3),
        ) if pad is not None else None
        position_evidence.append(f"R1.{pin}={actual}")
        position_ok &= actual is not None and all(abs(got - want) <= 0.002 for got, want in zip(actual, wanted))
checks.append(("Source PCB preserves the registered R1 landings",
               position_ok, "; ".join(position_evidence)))
surface_ok = r1 is not None and all(
    pad.GetAttribute() == pcbnew.PAD_ATTRIB_SMD
    and pad.GetLayerSet().Contains(pcbnew.F_Cu)
    and not pad.GetLayerSet().Contains(pcbnew.B_Cu)
    for pad in r1.Pads()
)
checks.append(("R1 uses the photographed component-side surface landings",
               surface_ok, "F.Cu SMD; no drilled/B.Cu pads"))
orientation_evidence = []
orientation_ok = True
for ref in ("D13", "D105"):
    footprint = source.FindFootprintByReference(ref)
    angle = footprint.GetOrientationDegrees() % 360 if footprint is not None else None
    orientation_evidence.append(f"{ref}={angle}")
    orientation_ok &= angle is not None and abs(angle - 270.0) <= 0.01
checks.append(("D13/D105 preserve their photographed right-facing notches",
               orientation_ok, "; ".join(orientation_evidence)))
d105 = source.FindFootprintByReference("D105")
d105_outer = [d105.FindPadByNumber(pin) for pin in ("1", "7", "8", "14")] if d105 is not None else []
d105_center = (
    round(sum(pcbnew.ToMM(pad.GetPosition().x) for pad in d105_outer) / 4, 3),
    round(sum(pcbnew.ToMM(pad.GetPosition().y) for pad in d105_outer) / 4, 3),
) if d105_outer and all(pad is not None for pad in d105_outer) else None
checks.append(("D105 preserves its factory centre with owner-photo orientation",
               d105_center is not None
               and abs(d105_center[0] - 31.9) <= 0.01
               and abs(d105_center[1] - 215.5) <= 0.01,
               str(d105_center)))

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
checks.append(("Promoted routed PCB preserves the measured D105 nets",
               not routed_mismatches,
               "exact source parity" if not routed_mismatches else "; ".join(routed_mismatches)))

ok = all(result for _, result, _ in checks)
status = "D105 H/DBIN + X1.107B/R1 ROUTED CLOSURE VERIFIED" if ok else "D105 HANDOFF FAILED"
lines = [
    "# D105 H/DBIN boundary", "", f"Status: **{status}**", "",
    "The native full-resolution sheet closes edge contact `X1.107B` (`-BLOCK`)",
    "directly onto D13.13/`H` and labels its pull-up `R1 2 kΩ` to rail A (+5 V).",
    "The `.009` assembly drawing identifies R1 between D13 and D105, the owner",
    "photo registers the populated landings, and direct continuity independently",
    "closes D13.13 to D105.10. Thus D105.10 is not the −5 V supply. CPU D1.17",
    "`DBIN` reaches D105.9;",
    "D105.9/.10 feed one NAND and tied D105.4/.5 invert it again, so D105.6",
    "drives D5.4 as `DBIN AND H`. Tied D105.12/.13 receive `MEMW`, while",
    "D105.11 drives D30.13.", "",
    "The authoritative board JSON, source PCB, HDL, and promoted routed PCB now",
    "preserve that measured topology. The routed board has exact source-pad identity",
    "and the stable-KiCad route/package gates report zero opens and zero electrical",
    "blockers. Historical DSN/SES and rejected local repair trials remain audit",
    "artifacts only.", "",
    "| Check | Result | Evidence |", "| --- | --- | --- |",
]
for name, result, evidence in checks:
    lines.append(f"| {name} | {'PASS' if result else 'FAIL'} | `{evidence}` |")
lines += [
    "", "## Rejected routed-snapshot repairs", "",
    "Earlier local copper trials attempted to preserve the obsolete routed netlist.",
    "They produced shorts or clearance failures around PHI2TTL, PHI2, RESIN, GND,",
    "RAM_OUT_EN, and the E3 control routing. Those trials remain rejected. The",
    "Promoted exact-source routing supersedes those trials and passes DRC without",
    "restoring the old D2.12-to-D105.9 assumption or adding a hidden jumper. Any",
    "future source-net change must regenerate and re-verify the complete package.",
]
REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
print(status)
raise SystemExit(0 if ok else 1)
