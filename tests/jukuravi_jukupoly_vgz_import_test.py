#!/usr/bin/env python3
"""Regression checks for documented OPL-to-JukuPoly reduction rules."""

from __future__ import annotations

import importlib.util
import sys
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
IMPORTER = ROOT / "spinoffs/jukuravi/firmware/import_jukupoly_vgz.py"
SPEC = importlib.util.spec_from_file_location("import_jukupoly_vgz", IMPORTER)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def check_volume() -> None:
    registers = [[0] * 256 for _ in range(2)]
    expected = {0: 16, 3: 13, 4: 12, 6: 10, 63: 1}
    for attenuation, volume in expected.items():
        registers[0][0x43] = attenuation
        assert MODULE.editor_volume(registers, 0, 0) == volume

    registers[0][0x40] = 6
    registers[0][0x43] = 6
    registers[0][0xC0] = 1
    assert MODULE.editor_volume(registers, 0, 0) == 16


def event(start: int, signature: tuple[int, ...], note: int,
          channel: int) -> object:
    return MODULE.KeyEvent(
        start=start, end=start + 100, bank=0, channel=channel,
        signature=signature, note=note,
    )


def check_classification() -> None:
    variable = (1,)
    chord = (2,)
    fixed = (3,)
    events = [
        event(0, variable, 48, 0),
        event(10, variable, 50, 0),
        event(20, variable, 52, 0),
        event(30, variable, 53, 0),
        event(100, chord, 60, 0),
        event(100, chord, 64, 1),
        event(100, chord, 67, 2),
        event(200, fixed, 48, 3),
    ]
    counts = Counter({variable: 8, chord: 3, fixed: 20})
    melodic = MODULE.melodic_signatures(events, counts)
    assert variable in melodic
    assert chord in melodic
    assert fixed not in melodic


def main() -> int:
    check_volume()
    check_classification()
    print("JUKUPOLY-VGZ-IMPORT: PASS logarithmic-volume chord-classification")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
