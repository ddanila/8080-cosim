#!/usr/bin/env python3
"""Patch the tracked source PCB without reserializing unrelated KiCad data.

The clean generator knows S1 is off-board, but the tracked source PCB retains
small hand-routed/photo-corrected work that a full regeneration intentionally
does not reproduce yet.  This narrow text transform removes only S1 and assigns
D98.7 to the factory wire-18 net while preserving every existing track, UUID,
and formatting choice.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path


NET_NAME = "D98_Y3_S1_2"


def block_end(text: str, start: int) -> int:
    """Return the byte after one balanced s-expression, respecting strings."""
    depth = 0
    quoted = escaped = False
    for index in range(start, len(text)):
        char = text[index]
        if quoted:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                quoted = False
            continue
        if char == '"':
            quoted = True
        elif char == "(":
            depth += 1
        elif char == ")":
            depth -= 1
            if depth == 0:
                return index + 1
    raise ValueError("unterminated KiCad s-expression")


def footprint_span(text: str, refdes: str) -> tuple[int, int]:
    for match in re.finditer(r"(?m)^\t\(footprint ", text):
        end = block_end(text, match.start() + 1)
        block = text[match.start():end]
        if f'(property "Reference" "{refdes}"' in block:
            return match.start(), end + (text[end:end + 1] == "\n")
    raise ValueError(f"footprint {refdes} not found")


def patch(text: str) -> str:
    if re.search(rf'(?m)^\t\(net \d+ "{re.escape(NET_NAME)}"\)$', text):
        raise ValueError(f"{NET_NAME} already present")

    s1_start, s1_end = footprint_span(text, "S1")
    text = text[:s1_start] + text[s1_end:]

    header_end = text.index("\n\t(footprint ")
    header = text[:header_end]
    declarations = list(re.finditer(r'(?m)^\t\(net (\d+) "[^"]+"\)$', header))
    if not declarations:
        raise ValueError("no top-level net declarations found")
    last = declarations[-1]
    net_id = int(last.group(1)) + 1
    insertion = last.end()
    text = text[:insertion] + f'\n\t(net {net_id} "{NET_NAME}")' + text[insertion:]

    d98_start, d98_end = footprint_span(text, "D98")
    d98 = text[d98_start:d98_end]
    pad_match = re.search(r'(?m)^\t\t\(pad "7" ', d98)
    if not pad_match:
        raise ValueError("D98 pad 7 not found")
    pad_end = block_end(d98, pad_match.start() + 2)
    pad = d98[pad_match.start():pad_end]
    if "\n\t\t\t(net " in pad:
        raise ValueError("D98 pad 7 is already assigned")
    uuid_at = pad.index("\n\t\t\t(uuid ")
    pad = pad[:uuid_at] + f'\n\t\t\t(net {net_id} "{NET_NAME}")' + pad[uuid_at:]
    d98 = d98[:pad_match.start()] + pad + d98[pad_end:]
    return text[:d98_start] + d98 + text[d98_end:]


def main() -> int:
    if len(sys.argv) != 2:
        raise SystemExit("usage: apply_s1_offboard_correction.py BOARD.kicad_pcb")
    board = Path(sys.argv[1])
    original = board.read_text(encoding="utf-8")
    updated = patch(original)
    board.write_text(updated, encoding="utf-8")
    print(f"patched {board}: removed S1; assigned D98.7 to {NET_NAME}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
