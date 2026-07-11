#!/usr/bin/env python3
"""Copy the generated D95/D99 and D101/D97/D102 photo-row placements."""
from __future__ import annotations

import re
import sys
from pathlib import Path

from apply_s1_offboard_correction import footprint_span


def placement(text: str, refdes: str) -> str:
    start, end = footprint_span(text, refdes)
    block = text[start:end]
    match = re.search(r"(?m)^\t\t\(at [^)]+\)$", block)
    if match is None:
        raise ValueError(f"{refdes} footprint placement is missing")
    return match.group(0)


def value_property(text: str, refdes: str) -> str:
    start, end = footprint_span(text, refdes)
    block = text[start:end]
    offset = block.find('\t\t(property "Value" ')
    if offset < 0:
        raise ValueError(f"{refdes} value property is missing")
    depth = 0
    for index in range(offset, len(block)):
        if block[index] == "(":
            depth += 1
        elif block[index] == ")":
            depth -= 1
            if depth == 0:
                return block[offset:index + 1]
    raise ValueError(f"{refdes} value property is unterminated")


def main() -> int:
    if len(sys.argv) != 3:
        raise SystemExit("usage: apply_d101_photo_placement.py DONOR.kicad_pcb TARGET.kicad_pcb")
    donor_path, target_path = map(Path, sys.argv[1:])
    target = target_path.read_text(encoding="utf-8")
    donor = donor_path.read_text(encoding="utf-8")
    for refdes in ("D94", "D100", "D98", "D95", "D99", "D101", "D97", "D102",
                   "C9", "C12", "C11", "C15"):
        start, end = footprint_span(target, refdes)
        block = target[start:end]
        old = placement(target, refdes)
        new = placement(donor, refdes)
        if old != new:
            target = target[:start] + block.replace(old, new, 1) + target[end:]
    for refdes in ("D97", "D99", "D102"):
        start, end = footprint_span(target, refdes)
        block = target[start:end]
        old = value_property(target, refdes)
        new = value_property(donor, refdes)
        if old != new:
            target = target[:start] + block.replace(old, new, 1) + target[end:]
    target_path.write_text(target, encoding="utf-8")
    print(f"patched {target_path}: copied photo-corrected FDC IC rows and C9/C11/C12/C15 placements")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
