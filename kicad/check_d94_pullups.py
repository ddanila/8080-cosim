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
    "R87": ((222.305, 37.784), "D94_A3_D104_X4_PULLUP"),
    "R88": ((224.943, 37.784), "D94_A4_D101_Q0_PULLUP"),
    "R89": ((227.629, 37.784), "D94_D0_BOUNDARY"),
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
        if pad1 is None or pad1.GetNetname() != signal_net:
            failures.append(f"{ref}.1 is not assigned to {signal_net}")
        if pad2 is None or pad2.GetNetname() != "P5V":
            failures.append(f"{ref}.2 is not assigned to P5V")
        if pad1 is not None:
            actual = (mm(pad1.GetPosition().x), mm(pad1.GetPosition().y))
            if any(abs(got - want) > 0.002 for got, want in zip(actual, signal_position)):
                failures.append(f"{ref}.1 position {actual} != {signal_position}")

    if failures:
        for failure in failures:
            print("FAIL:", failure)
        return 1
    print("D94 PULL-UPS: PASS — R87/R88/R89 are guarded as 6.2 kohm pull-ups to +5 V")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
