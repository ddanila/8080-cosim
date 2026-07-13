#!/usr/bin/python3
"""Guard the component-photo-proved KP12 resistor links."""
from pathlib import Path

import pcbnew


ROOT = Path(__file__).resolve().parents[1]
BOARD = ROOT / "kicad" / "juku.kicad_pcb"
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
    failures = []
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
    print("KP12 RESISTOR LINKS: PASS — R92/R99 endpoints closed from component copper")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
