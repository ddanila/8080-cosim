#!/usr/bin/env python3
"""Merge provisional A22 harness net into source-proved S_OC."""
from __future__ import annotations

import re
import sys
from pathlib import Path

from apply_s1_offboard_correction import footprint_span


def patch(text: str) -> str:
    old = re.search(r'(?m)^\t\(net (\d+) "X3_HARNESS_2"\)\n', text)
    new = re.search(r'(?m)^\t\(net (\d+) "S_OC"\)$', text)
    if old is None or new is None:
        raise ValueError("required old/new net declarations are missing")
    start, end = footprint_span(text, "A22")
    footprint = text[start:end]
    old_pad = f'(net {old.group(1)} "X3_HARNESS_2")'
    if footprint.count(old_pad) != 1:
        raise ValueError("A22 does not carry exactly one provisional net assignment")
    footprint = footprint.replace(old_pad, f'(net {new.group(1)} "S_OC")')
    text = text[:start] + footprint + text[end:]
    return text[:old.start()] + text[old.end():]


def main() -> int:
    if len(sys.argv) != 2:
        raise SystemExit("usage: apply_a22_s_oc_correction.py BOARD.kicad_pcb")
    path = Path(sys.argv[1])
    path.write_text(patch(path.read_text(encoding="utf-8")), encoding="utf-8")
    print(f"patched {path}: merged A22 into S_OC")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
