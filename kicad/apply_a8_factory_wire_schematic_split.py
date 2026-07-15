#!/usr/bin/env python3
"""Insert the A:8 wire symbol into the tracked schematic without UUID churn."""
from __future__ import annotations

import re
import sys
from pathlib import Path

from apply_s1_offboard_correction import block_end


INSTANCE_UUID = "a8000000-0000-0000-0000-000000000008"
PIN1_WIRE_UUID = "a8000000-0000-0000-0001-000000000008"
PIN2_WIRE_UUID = "a8000000-0000-0000-0002-000000000008"


def expression(text: str, marker: str) -> str:
    start = text.index(marker)
    end = block_end(text, start)
    return text[start:end]


def patch(target: str, donor: str) -> str:
    if 'property "Reference" "W8"' in target:
        raise ValueError("target already contains W8")
    if 'symbol "juku:WIRE_LINK"' in target:
        raise ValueError("target already contains WIRE_LINK library symbol")

    library = expression(donor, '(symbol "juku:WIRE_LINK"')
    library_close = target.index("\n\t)\n\t(symbol (lib_id")
    target = target[:library_close] + "\n\t\t" + library + target[library_close:]

    instance = expression(donor, '(symbol (lib_id "juku:WIRE_LINK")')
    instance = re.sub(
        r'\(uuid "[^"]+"\)', f'(uuid "{INSTANCE_UUID}")', instance, count=1
    )
    first_wire = target.index("\n\t(wire ")
    target = target[:first_wire] + "\n\t" + instance + target[first_wire:]

    old_label = (
        '\t(label "STSTB" (at 62.7 1037.46 0) '
        '(effects (font (size 1.27 1.27)) (justify left bottom)))'
    )
    new_label = old_label.replace('"STSTB"', '"STSTB_D38"')
    if target.count(old_label) != 1:
        raise ValueError("D38 STSTB label is missing or ambiguous")
    target = target.replace(old_label, new_label)

    additions = "\n".join(
        [
            '\t(wire (pts (xy 50.0 12120) (xy 50.0 12117.46)) '
            f'(stroke (width 0) (type default)) (uuid "{PIN1_WIRE_UUID}"))',
            '\t(label "STSTB" (at 50.0 12117.46 0) '
            '(effects (font (size 1.27 1.27)) (justify left bottom)))',
            '\t(wire (pts (xy 52.54 12120) (xy 52.54 12117.46)) '
            f'(stroke (width 0) (type default)) (uuid "{PIN2_WIRE_UUID}"))',
            '\t(label "STSTB_D38" (at 52.54 12117.46 0) '
            '(effects (font (size 1.27 1.27)) (justify left bottom)))',
        ]
    )
    first_wire = target.index("\n\t(wire ")
    return target[:first_wire] + "\n" + additions + target[first_wire:]


def main() -> int:
    if len(sys.argv) != 3:
        raise SystemExit(
            "usage: apply_a8_factory_wire_schematic_split.py "
            "TARGET.kicad_sch DONOR.kicad_sch"
        )
    target_path, donor_path = map(Path, sys.argv[1:])
    updated = patch(
        target_path.read_text(encoding="utf-8"),
        donor_path.read_text(encoding="utf-8"),
    )
    target_path.write_text(updated, encoding="utf-8")
    print(f"patched {target_path}: inserted W8 and split STSTB_D38")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
