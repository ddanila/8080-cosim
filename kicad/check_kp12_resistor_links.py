#!/usr/bin/python3
"""Guard the component-photo-proved KP12 resistor links."""
import json
from pathlib import Path

import pcbnew


ROOT = Path(__file__).resolve().parents[1]
BOARD = ROOT / "kicad" / "juku.kicad_pcb"
BOARD_JSON = ROOT / "kicad" / "juku.board.json"
EXPECTED_VALUES = {"R92": "1,3к", "R99": "4,7к"}
EXPECTED = {
    ("D95", "14"): "D95_A0_R92",
    ("R92", "2"): "D95_A0_R92",
    ("D101", "4"): "D101_D02_R92_R99",
    ("R92", "1"): "D101_D02_R92_R99",
    ("R99", "2"): "D101_D02_R92_R99",
    ("R99", "1"): "GND",
    ("D101", "8"): "GND",
}


def main() -> int:
    board = pcbnew.LoadBoard(str(BOARD))
    spec = json.loads(BOARD_JSON.read_text(encoding="utf-8"))
    chips = {chip["ref"]: chip for chip in spec["chips"]}
    failures = []
    for ref, expected in EXPECTED_VALUES.items():
        footprint = board.FindFootprintByReference(ref)
        actual = footprint.GetValue() if footprint is not None else None
        if actual != expected:
            failures.append(f"{ref} footprint value: {actual!r} != {expected!r}")
        if chips.get(ref, {}).get("value") != expected:
            failures.append(f"{ref} board-JSON value: {chips.get(ref, {}).get('value')!r} != {expected!r}")
    for (ref, pin), expected in EXPECTED.items():
        footprint = board.FindFootprintByReference(ref)
        pad = footprint.FindPadByNumber(pin) if footprint is not None else None
        actual = pad.GetNetname() if pad is not None else None
        if actual != expected:
            failures.append(f"{ref}.{pin}: {actual!r} != {expected!r}")
    if failures:
        for failure in failures:
            print("FAIL:", failure)
        return 1
    print("KP12 RESISTOR LINKS: PASS — R92/R99 values and endpoints closed from component photos")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
