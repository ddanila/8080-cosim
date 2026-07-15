#!/usr/bin/env python3
"""Insert W7 into the tracked schematic without UUID churn."""
from __future__ import annotations

import re
import sys
from pathlib import Path

from apply_a8_factory_wire_schematic_split import expression


SPLITS = (
    ("W7", "PHI1", "PHI1_D35", "70.32", "997.46", "12320", "a7000000", "000000000007"),
)


def patch(target: str, donor: str) -> str:
    instances: list[str] = []
    additions: list[str] = []
    for ref, main_net, remote_net, owner_x, owner_y, symbol_y, prefix, suffix in SPLITS:
        if f'property "Reference" "{ref}"' in target:
            raise ValueError(f"target already contains {ref}")
        ref_position = donor.index(f'property "Reference" "{ref}"')
        start = donor.rfind('(symbol (lib_id "juku:WIRE_LINK")', 0, ref_position)
        if start < 0:
            raise ValueError(f"{ref} donor instance is missing")
        instance = expression(donor[start:], '(symbol (lib_id "juku:WIRE_LINK")')
        donor_y = re.search(r'\(symbol \(lib_id "juku:WIRE_LINK"\) \(at 50 ([0-9.]+) 0\)', instance)
        if not donor_y:
            raise ValueError(f"{ref} donor position is missing")
        delta = float(symbol_y) - float(donor_y.group(1))

        def move_y(match: re.Match[str]) -> str:
            value = float(match.group(1)) + delta
            rendered = str(int(value)) if value.is_integer() else str(value)
            return f"{match.group(0)[:match.start(1)-match.start()]}{rendered}{match.group(0)[match.end(1)-match.start():]}"

        instance = re.sub(r'(?<=\s)([0-9]+(?:\.[0-9]+)?)(?= 0\))', move_y, instance)
        instance = re.sub(
            r'\(uuid "[^"]+"\)',
            f'(uuid "{prefix}-1000-0000-0000-{suffix}")',
            instance,
            count=1,
        )
        instances.append(instance)

        old = f'\t(label "{main_net}" (at {owner_x} {owner_y} 0)'
        if target.count(old) != 1:
            raise ValueError(f"D35 {main_net} label is missing or ambiguous")
        target = target.replace(old, old.replace(f'"{main_net}"', f'"{remote_net}"'))

        wire_prefix = f"{prefix}-1000-0000"
        landing_y = f"{float(symbol_y)-2.54:.2f}"
        additions.extend([
            f'\t(wire (pts (xy 50.0 {symbol_y}) (xy 50.0 {landing_y})) (stroke (width 0) (type default)) (uuid "{wire_prefix}-0001-{suffix}"))',
            f'\t(label "{main_net}" (at 50.0 {landing_y} 0) (effects (font (size 1.27 1.27)) (justify left bottom)))',
            f'\t(wire (pts (xy 52.54 {symbol_y}) (xy 52.54 {landing_y})) (stroke (width 0) (type default)) (uuid "{wire_prefix}-0002-{suffix}"))',
            f'\t(label "{remote_net}" (at 52.54 {landing_y} 0) (effects (font (size 1.27 1.27)) (justify left bottom)))',
        ])

    first_wire = target.index("\n\t(wire ")
    inserted = "\n".join(f"\t{instance}" for instance in instances)
    target = target[:first_wire] + "\n" + inserted + target[first_wire:]
    first_wire = target.index("\n\t(wire ")
    return target[:first_wire] + "\n" + "\n".join(additions) + target[first_wire:]


def main() -> int:
    if len(sys.argv) != 3:
        raise SystemExit("usage: apply_a7_factory_wire_schematic_split.py TARGET DONOR")
    target, donor = map(Path, sys.argv[1:])
    target.write_text(patch(target.read_text(), donor.read_text()))
    print(f"patched {target}: inserted W7 and split PHI1_D35")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
