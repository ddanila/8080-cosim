#!/usr/bin/env python3
"""Assign sheet-proved D10 SP/EN master strap without PCB reserialization."""
from __future__ import annotations

import re
import sys
from pathlib import Path

from apply_s1_offboard_correction import block_end, footprint_span


def patch(text: str) -> str:
    declaration = re.search(r'(?m)^\t\(net (\d+) "P5V"\)$', text)
    if declaration is None:
        raise ValueError("P5V declaration is missing")
    start, end = footprint_span(text, "D10")
    footprint = text[start:end]
    match = re.search(r'(?m)^\t\t\(pad "16" ', footprint)
    if match is None:
        raise ValueError("D10 pad 16 not found")
    pad_end = block_end(footprint, match.start() + 2)
    pad = footprint[match.start():pad_end]
    if "\n\t\t\t(net " in pad:
        raise ValueError("D10 pad 16 is already assigned")
    uuid_at = pad.index("\n\t\t\t(uuid ")
    pad = pad[:uuid_at] + f'\n\t\t\t(net {declaration.group(1)} "P5V")' + pad[uuid_at:]
    footprint = footprint[:match.start()] + pad + footprint[pad_end:]
    return text[:start] + footprint + text[end:]


def main() -> int:
    if len(sys.argv) != 2:
        raise SystemExit("usage: apply_pic_sp_en.py BOARD.kicad_pcb")
    path = Path(sys.argv[1])
    path.write_text(patch(path.read_text(encoding="utf-8")), encoding="utf-8")
    print(f"patched {path}: assigned D10.16 to P5V")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
