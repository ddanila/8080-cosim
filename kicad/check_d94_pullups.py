#!/usr/bin/env python3
"""Guard the factory/photo-identified D94 pull-up row."""
from __future__ import annotations

import json
from pathlib import Path

import pcbnew


ROOT = Path(__file__).resolve().parents[1]
BOARD_JSON = ROOT / "kicad/juku.board.json"
BOARD = ROOT / "kicad/juku.kicad_pcb"
REGISTRATION = ROOT / "ref/photos/dgsh5-109-009-sb/fdc-upper-placement-registration.json"

EXPECTED = {
    "R87": ((222.305, 37.784), "FDC_WE_N"),
    "R88": ((224.943, 37.784), "FDC_RE_N"),
    "R89": ((227.629, 37.784), "D94_D1_D99_A2N"),
}
EXPECTED_VALUE = "6,2к"


def mm(value: int) -> float:
    return pcbnew.ToMM(value)


def main() -> int:
    failures: list[str] = []
    spec = json.loads(BOARD_JSON.read_text(encoding="utf-8"))
    registration = json.loads(REGISTRATION.read_text(encoding="utf-8"))
    board = pcbnew.LoadBoard(str(BOARD))

    if [item["refdes"] for item in registration.get("d94_pullups", [])] != list(EXPECTED):
        failures.append("factory/photo registration order is not R87/R88/R89")
    value_evidence = registration.get("d94_pullup_value_evidence", {})
    if value_evidence.get("value") != EXPECTED_VALUE or value_evidence.get("resistance_ohms") != 6200:
        failures.append("factory/photo value evidence does not guard 6.2 kohm")
    if value_evidence.get("factory_bom", {}).get("page") != 6:
        failures.append("factory BOM page for D94 pull-up values is not guarded")

    chips = {chip["ref"]: chip for chip in spec["chips"]}
    for ref, (signal_position, signal_net) in EXPECTED.items():
        chip = chips.get(ref)
        if chip is None or chip.get("type") != "R_AXIAL":
            failures.append(f"{ref} is missing from board JSON")
        elif chip.get("value") != EXPECTED_VALUE:
            failures.append(f"{ref} value {chip.get('value')!r} != {EXPECTED_VALUE!r}")
        signal_nodes = spec["nets"][signal_net]["nodes"]
        if [ref, "1"] not in signal_nodes:
            failures.append(f"{ref}.1 is missing from {signal_net}")
        if [ref, "2"] not in spec["nets"]["P5V"]["nodes"]:
            failures.append(f"{ref}.2 is missing from P5V")

        footprint = board.FindFootprintByReference(ref)
        if footprint is None:
            failures.append(f"{ref} footprint is missing")
            continue
        if footprint.GetValue() != EXPECTED_VALUE:
            failures.append(f"{ref} footprint value {footprint.GetValue()!r} != {EXPECTED_VALUE!r}")
        pad1 = footprint.FindPadByNumber("1")
        pad2 = footprint.FindPadByNumber("2")
        # The tracked routed PCB is deliberately a held pre-correction snapshot.
        # Electrical truth is checked above from board JSON; retain only its
        # independently useful placement/value checks here until controlled reroute.
        if pad1 is not None:
            actual = (mm(pad1.GetPosition().x), mm(pad1.GetPosition().y))
            if any(abs(got - want) > 0.002 for got, want in zip(actual, signal_position)):
                failures.append(f"{ref}.1 position {actual} != {signal_position}")

    r8 = chips.get("R8", {})
    if r8.get("value") != "2к" or not r8.get("pcb_placement_pending"):
        failures.append("R8 2 kohm pull-up is missing or not placement-pending")
    if ["R8", "1"] not in spec["nets"]["D94_D0_BOUNDARY"]["nodes"]:
        failures.append("R8.1 is missing from D94_D0_BOUNDARY")
    if ["R8", "2"] not in spec["nets"]["P5V"]["nodes"]:
        failures.append("R8.2 is missing from P5V")

    if failures:
        for failure in failures:
            print("FAIL:", failure)
        return 1
    print("D94 PULL-UPS: PASS — R87/R88/R89 pull up D3/D2/D1; R8 2k pulls up D0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
