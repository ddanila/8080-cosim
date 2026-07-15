#!/usr/bin/env python3
"""Insert W10 into the tracked schematic without regenerating existing UUIDs."""
from __future__ import annotations

import re
import sys
from pathlib import Path

from apply_a8_factory_wire_schematic_split import expression


def patch(target: str, donor: str) -> str:
    if 'property "Reference" "W10"' in target:
        raise ValueError("target already contains W10")
    ref_position = donor.index('property "Reference" "W10"')
    instance_start = donor.rfind('(symbol (lib_id "juku:WIRE_LINK")', 0, ref_position)
    if instance_start < 0:
        raise ValueError("W10 donor instance is missing")
    instance = expression(donor[instance_start:], '(symbol (lib_id "juku:WIRE_LINK")')
    instance = re.sub(r'\(uuid "[^"]+"\)', '(uuid "a1000000-1000-0000-0000-000000000010")', instance, count=1)
    first_wire = target.index("\n\t(wire ")
    target = target[:first_wire] + "\n\t" + instance + target[first_wire:]
    for at in ("50.0 8317.46", "50.0 8477.46"):
        old = f'\t(label "W10_QA_SEL" (at {at} 0)'
        if target.count(old) != 1:
            raise ValueError(f"missing D50/D51 label at {at}")
        target = target.replace(old, old.replace('"W10_QA_SEL"', f'"{REMOTE_NET}"'))
    additions = "\n".join([
        '\t(wire (pts (xy 50.0 12160) (xy 50.0 12157.46)) (stroke (width 0) (type default)) (uuid "a1000000-1000-0000-0001-000000000010"))',
        '\t(label "W10_QA_SEL" (at 50.0 12157.46 0) (effects (font (size 1.27 1.27)) (justify left bottom)))',
        '\t(wire (pts (xy 52.54 12160) (xy 52.54 12157.46)) (stroke (width 0) (type default)) (uuid "a1000000-1000-0000-0002-000000000010"))',
        f'\t(label "{REMOTE_NET}" (at 52.54 12157.46 0) (effects (font (size 1.27 1.27)) (justify left bottom)))',
    ])
    first_wire = target.index("\n\t(wire ")
    return target[:first_wire] + "\n" + additions + target[first_wire:]


REMOTE_NET = "W10_QA_SEL_D50"


def main() -> int:
    if len(sys.argv) != 3:
        raise SystemExit("usage: apply_a10_factory_wire_schematic_split.py TARGET DONOR")
    target, donor = map(Path, sys.argv[1:])
    target.write_text(patch(target.read_text(), donor.read_text()))
    print(f"patched {target}: inserted W10 and split {REMOTE_NET}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
