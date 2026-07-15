#!/usr/bin/env python3
"""Insert W20 into the tracked schematic without UUID churn."""
from __future__ import annotations

import re
import sys
from pathlib import Path

from apply_a8_factory_wire_schematic_split import expression

REMOTE_NET = "S_TTL_D3"


def patch(target: str, donor: str) -> str:
    if 'property "Reference" "W20"' in target:
        raise ValueError("target already contains W20")
    ref_position = donor.index('property "Reference" "W20"')
    start = donor.rfind('(symbol (lib_id "juku:WIRE_LINK")', 0, ref_position)
    if start < 0:
        raise ValueError("W20 donor instance is missing")
    instance = expression(donor[start:], '(symbol (lib_id "juku:WIRE_LINK")')
    instance = re.sub(r'\(uuid "[^"]+"\)', '(uuid "a2000000-1000-0000-0000-000000000020")', instance, count=1)
    first_wire = target.index("\n\t(wire ")
    target = target[:first_wire] + "\n\t" + instance + target[first_wire:]
    old = '\t(label "S_TTL" (at 70.32 3317.46 0)'
    if target.count(old) != 1:
        raise ValueError("D3.10 S_TTL label is missing or ambiguous")
    target = target.replace(old, old.replace('"S_TTL"', f'"{REMOTE_NET}"'))
    additions = "\n".join([
        '\t(wire (pts (xy 50.0 12280) (xy 50.0 12277.46)) (stroke (width 0) (type default)) (uuid "a2000000-1000-0000-0001-000000000020"))',
        '\t(label "S_TTL" (at 50.0 12277.46 0) (effects (font (size 1.27 1.27)) (justify left bottom)))',
        '\t(wire (pts (xy 52.54 12280) (xy 52.54 12277.46)) (stroke (width 0) (type default)) (uuid "a2000000-1000-0000-0002-000000000020"))',
        f'\t(label "{REMOTE_NET}" (at 52.54 12277.46 0) (effects (font (size 1.27 1.27)) (justify left bottom)))',
    ])
    first_wire = target.index("\n\t(wire ")
    return target[:first_wire] + "\n" + additions + target[first_wire:]


def main() -> int:
    if len(sys.argv) != 3:
        raise SystemExit("usage: apply_a20_factory_wire_schematic_split.py TARGET DONOR")
    target, donor = map(Path, sys.argv[1:])
    target.write_text(patch(target.read_text(), donor.read_text()))
    print(f"patched {target}: inserted W20 and split {REMOTE_NET}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
