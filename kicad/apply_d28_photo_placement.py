#!/usr/bin/env python3
"""Copy the generated D28/D96 photo-corrected placements into the tracked PCB."""
from __future__ import annotations

import re
import sys
from pathlib import Path

from apply_s1_offboard_correction import footprint_span


def placement(text: str, refdes: str) -> str:
    start, end = footprint_span(text, refdes)
    block = text[start:end]
    match = re.search(r'(?m)^\t\t\(at [^)]+\)$', block)
    if match is None:
        raise ValueError(f"{refdes} footprint placement is missing")
    return match.group(0)


def patch(target: str, donor: str) -> str:
    for refdes in ("D28", "D96"):
        start, end = footprint_span(target, refdes)
        block = target[start:end]
        old = placement(target, refdes)
        new = placement(donor, refdes)
        if old != new:
            block = block.replace(old, new, 1)
            target = target[:start] + block + target[end:]
    return target


def main() -> int:
    if len(sys.argv) != 3:
        raise SystemExit("usage: apply_d28_photo_placement.py DONOR.kicad_pcb TARGET.kicad_pcb")
    donor_path, target_path = map(Path, sys.argv[1:])
    target_path.write_text(
        patch(target_path.read_text(encoding="utf-8"), donor_path.read_text(encoding="utf-8")),
        encoding="utf-8",
    )
    print(f"patched {target_path}: copied photo-corrected D28/D96 placements")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
