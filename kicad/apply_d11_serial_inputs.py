#!/usr/bin/env python3
"""Assign source-proved D11 auxiliary pads without reserializing the PCB."""
from __future__ import annotations

import re
import sys
from pathlib import Path

from apply_s1_offboard_correction import block_end, footprint_span


ASSIGNMENTS = {
    "17": "SER_CTS_N",
    "20": "D13_4_D105_2",
    "21": "RESET",
    "22": "SER_DSR_N",
}


def patch(text: str) -> str:
    start, end = footprint_span(text, "D11")
    footprint = text[start:end]
    for pin, net_name in ASSIGNMENTS.items():
        declaration = re.search(
            rf'(?m)^\t\(net (\d+) "{re.escape(net_name)}"\)$', text
        )
        if declaration is None:
            raise ValueError(f"top-level net {net_name} is missing")
        pad_match = re.search(rf'(?m)^\t\t\(pad "{pin}" ', footprint)
        if pad_match is None:
            raise ValueError(f"D11 pad {pin} not found")
        pad_end = block_end(footprint, pad_match.start() + 2)
        pad = footprint[pad_match.start():pad_end]
        assigned = re.search(r'\n\t\t\t\(net \d+ "([^"]+)"\)', pad)
        if assigned:
            if assigned.group(1) != net_name:
                raise ValueError(
                    f"D11 pad {pin} is assigned to {assigned.group(1)}, expected {net_name}"
                )
            continue
        uuid_at = pad.index("\n\t\t\t(uuid ")
        pad = (
            pad[:uuid_at]
            + f'\n\t\t\t(net {declaration.group(1)} "{net_name}")'
            + pad[uuid_at:]
        )
        footprint = footprint[:pad_match.start()] + pad + footprint[pad_end:]
    return text[:start] + footprint + text[end:]


def main() -> int:
    if len(sys.argv) != 2:
        raise SystemExit("usage: apply_d11_serial_inputs.py BOARD.kicad_pcb")
    path = Path(sys.argv[1])
    path.write_text(patch(path.read_text(encoding="utf-8")), encoding="utf-8")
    print(f"patched {path}: guarded D11.17/20/21/22 auxiliary assignments")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
