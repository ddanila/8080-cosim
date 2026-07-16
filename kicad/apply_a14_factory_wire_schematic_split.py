#!/usr/bin/env python3
"""Insert W14 into the tracked schematic without UUID churn."""
from __future__ import annotations

import re
import sys
from pathlib import Path

from apply_a8_factory_wire_schematic_split import expression


def patch(target: str, donor: str) -> str:
    if 'property "Reference" "W14"' in target:
        raise ValueError("target already contains W14")
    ref_position = donor.index('property "Reference" "W14"')
    start = donor.rfind('(symbol (lib_id "juku:WIRE_LINK")', 0, ref_position)
    if start < 0:
        raise ValueError("W14 donor instance is missing")
    instance = expression(donor[start:], '(symbol (lib_id "juku:WIRE_LINK")')
    donor_y = re.search(r'\(symbol \(lib_id "juku:WIRE_LINK"\) \(at 50 ([0-9.]+) 0\)', instance)
    if not donor_y:
        raise ValueError("W14 donor position is missing")
    delta = 12360.0 - float(donor_y.group(1))

    def move_y(match: re.Match[str]) -> str:
        value = float(match.group(1)) + delta
        rendered = str(int(value)) if value.is_integer() else str(value)
        return f"{match.group(0)[:match.start(1)-match.start()]}{rendered}{match.group(0)[match.end(1)-match.start():]}"

    instance = re.sub(r'(?<=\s)([0-9]+(?:\.[0-9]+)?)(?= 0\))', move_y, instance)
    instance = re.sub(
        r'\(uuid "[^"]+"\)',
        '(uuid "a1400000-1000-0000-0000-000000000014")',
        instance,
        count=1,
    )

    old = '\t(label "PHI2" (at 75.4 997.46 0)'
    if target.count(old) != 1:
        raise ValueError("D35 PHI2 label is missing or ambiguous")
    target = target.replace(old, old.replace('"PHI2"', '"PHI2_D35"'))

    first_wire = target.index("\n\t(wire ")
    target = target[:first_wire] + "\n\t" + instance + target[first_wire:]
    additions = [
        '\t(wire (pts (xy 50.0 12360) (xy 50.0 12357.46)) (stroke (width 0) (type default)) (uuid "a1400000-1000-0000-0001-000000000014"))',
        '\t(label "PHI2" (at 50.0 12357.46 0) (effects (font (size 1.27 1.27)) (justify left bottom)))',
        '\t(wire (pts (xy 52.54 12360) (xy 52.54 12357.46)) (stroke (width 0) (type default)) (uuid "a1400000-1000-0000-0002-000000000014"))',
        '\t(label "PHI2_D35" (at 52.54 12357.46 0) (effects (font (size 1.27 1.27)) (justify left bottom)))',
    ]
    first_wire = target.index("\n\t(wire ")
    return target[:first_wire] + "\n" + "\n".join(additions) + target[first_wire:]


def main() -> int:
    if len(sys.argv) != 3:
        raise SystemExit("usage: apply_a14_factory_wire_schematic_split.py TARGET DONOR")
    target, donor = map(Path, sys.argv[1:])
    target.write_text(patch(target.read_text(), donor.read_text()))
    print(f"patched {target}: inserted W14 and split PHI2_D35")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
