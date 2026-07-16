#!/usr/bin/env python3
"""Remove the contradicted C63 footprint without reserializing the PCB."""
from __future__ import annotations

import re
import sys
from pathlib import Path


def block_end(text: str, start: int) -> int:
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


def main() -> int:
    if len(sys.argv) != 2:
        raise SystemExit("usage: apply_c63_target_dnp.py BOARD.kicad_pcb")
    board = Path(sys.argv[1])
    text = board.read_text(encoding="utf-8")
    start, end = footprint_span(text, "C63")
    board.write_text(text[:start] + text[end:], encoding="utf-8")
    print(f"patched {board}: removed target-DNP C63 footprint")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
