#!/usr/bin/env python3
"""Apply the photo-proved D95/D101/R92/R99 pad-net joins to a source PCB."""
from __future__ import annotations

import re
import sys
from pathlib import Path

from apply_s1_offboard_correction import block_end, footprint_span


RENAMES = {
    "D101_D02_BOUNDARY": "D101_D02_R92_R99",
}
ASSIGNMENTS = {
    ("R92", "2"): "FDC_DDEN",
    ("R92", "1"): "D101_D02_R92_R99",
    ("R99", "2"): "D101_D02_R92_R99",
    ("R99", "1"): "GND",
}
RETIRED = {
    "R92_1_BOUNDARY", "R92_2_BOUNDARY",
    "R99_1_BOUNDARY", "R99_2_BOUNDARY",
}


def net_ids(text: str) -> dict[str, str]:
    return dict(re.findall(r'(?m)^\t\(net (\d+) "([^"]+)"\)$', text))


def names_to_ids(text: str) -> dict[str, str]:
    return {name: code for code, name in net_ids(text).items()}


def assign_pad(text: str, ref: str, pin: str, net_name: str) -> str:
    ids = names_to_ids(text)
    if net_name not in ids:
        raise ValueError(f"top-level net {net_name} is missing")
    start, end = footprint_span(text, ref)
    footprint = text[start:end]
    match = re.search(rf'(?m)^\t\t\(pad "{re.escape(pin)}" ', footprint)
    if match is None:
        raise ValueError(f"{ref}.{pin} pad is missing")
    pad_end = block_end(footprint, match.start() + 2)
    pad = footprint[match.start():pad_end]
    replacement = f'\n\t\t\t(net {ids[net_name]} "{net_name}")'
    if re.search(r'\n\t\t\t\(net \d+ "[^"]+"\)', pad):
        pad = re.sub(r'\n\t\t\t\(net \d+ "[^"]+"\)', replacement, pad, count=1)
    else:
        uuid_at = pad.index("\n\t\t\t(uuid ")
        pad = pad[:uuid_at] + replacement + pad[uuid_at:]
    footprint = footprint[:match.start()] + pad + footprint[pad_end:]
    return text[:start] + footprint + text[end:]


def patch(text: str) -> str:
    for old, new in RENAMES.items():
        if old in text:
            if new in text:
                raise ValueError(f"both old and new net names exist: {old}, {new}")
            text = text.replace(f'"{old}"', f'"{new}"')
        elif new not in text:
            raise ValueError(f"neither old nor new net name exists: {old}, {new}")
    for endpoint, net_name in ASSIGNMENTS.items():
        text = assign_pad(text, *endpoint, net_name)
    for name in RETIRED:
        text, count = re.subn(
            rf'(?m)^\t\(net \d+ "{re.escape(name)}"\)\n', "", text
        )
        if count > 1:
            raise ValueError(f"duplicate retired declaration {name}")
        if f'"{name}"' in text:
            raise ValueError(f"retired net {name} still has references")
    return text


def main() -> int:
    if len(sys.argv) != 2:
        raise SystemExit("usage: apply_kp12_resistor_links.py BOARD.kicad_pcb")
    board = Path(sys.argv[1])
    board.write_text(patch(board.read_text(encoding="utf-8")), encoding="utf-8")
    print(f"patched {board}: D95/D101/R92/R99 photo links")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
