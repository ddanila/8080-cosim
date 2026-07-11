#!/usr/bin/env python3
"""Assign existing D98.3 to the photo-proved R94 near-terminal net."""
from __future__ import annotations

import re
import sys
from pathlib import Path

from apply_s1_offboard_correction import block_end, footprint_span


NET_NAME = "D98_Y1_R94"


def patch(text: str) -> str:
    declaration = re.search(
        rf'(?m)^\t\(net (\d+) "{re.escape(NET_NAME)}"\)$', text
    )
    if declaration is None:
        raise ValueError(f"top-level net {NET_NAME} is missing")
    net_id = declaration.group(1)
    start, end = footprint_span(text, "D98")
    footprint = text[start:end]
    pad_match = re.search(r'(?m)^\t\t\(pad "3" ', footprint)
    if pad_match is None:
        raise ValueError("D98 pad 3 not found")
    pad_end = block_end(footprint, pad_match.start() + 2)
    pad = footprint[pad_match.start():pad_end]
    if "\n\t\t\t(net " in pad:
        raise ValueError("D98 pad 3 is already assigned")
    uuid_at = pad.index("\n\t\t\t(uuid ")
    pad = pad[:uuid_at] + f'\n\t\t\t(net {net_id} "{NET_NAME}")' + pad[uuid_at:]
    footprint = footprint[:pad_match.start()] + pad + footprint[pad_end:]
    return text[:start] + footprint + text[end:]


def main() -> int:
    if len(sys.argv) != 2:
        raise SystemExit("usage: apply_r94_landing.py BOARD.kicad_pcb")
    board = Path(sys.argv[1])
    board.write_text(patch(board.read_text(encoding="utf-8")), encoding="utf-8")
    print(f"patched {board}: assigned D98.3 to {NET_NAME}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
