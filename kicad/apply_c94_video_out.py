#!/usr/bin/env python3
"""Transplant generated C94 after the photo-proved VIDEO_OUT join."""
from __future__ import annotations

import re
import sys
from pathlib import Path

from apply_s1_offboard_correction import footprint_span


RETIRED = "C94_2_BOUNDARY"


def net_ids(text: str) -> dict[str, str]:
    return {name: code for code, name in re.findall(r'(?m)^\t\(net (\d+) "([^"]+)"\)$', text)}


def matching_block(text: str, start: int) -> tuple[int, int]:
    depth = 0
    in_string = False
    escaped = False
    for index in range(start, len(text)):
        char = text[index]
        if in_string:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
            continue
        if char == '"':
            in_string = True
        elif char == "(":
            depth += 1
        elif char == ")":
            depth -= 1
            if depth == 0:
                return start, index + 1
    raise ValueError("unterminated S-expression")


def patch(target: str, donor: str) -> str:
    ids = net_ids(target)
    if "VIDEO_OUT" not in ids:
        raise ValueError("target PCB is missing VIDEO_OUT")
    donor_start, donor_end = footprint_span(donor, "C94")
    donor_block = donor[donor_start:donor_end]
    if not re.search(r'\(pad "2"[\s\S]*?\(net \d+ "VIDEO_OUT"\)', donor_block):
        raise ValueError("donor C94.2 is not assigned to VIDEO_OUT")
    start, end = footprint_span(target, "C94")
    block = target[start:end]
    pad_start = block.index('(pad "2"')
    left, right = matching_block(block, pad_start)
    pad = block[left:right]
    wanted = f'(net {ids["VIDEO_OUT"]} "VIDEO_OUT")'
    pad, count = re.subn(r'\(net \d+ "[^"]+"\)', wanted, pad, count=1)
    if count != 1:
        raise ValueError("target C94.2 has no replaceable net assignment")
    block = block[:left] + pad + block[right:]
    target = target[:start] + block + target[end:]
    target, count = re.subn(
        rf'(?m)^\t\(net \d+ "{RETIRED}"\)\n', "", target
    )
    if count > 1 or f'"{RETIRED}"' in target:
        raise ValueError(f"retired net {RETIRED} still has references")
    return target


def main() -> int:
    if len(sys.argv) != 3:
        raise SystemExit("usage: apply_c94_video_out.py TARGET.kicad_pcb DONOR.kicad_pcb")
    target_path, donor_path = map(Path, sys.argv[1:])
    target_path.write_text(
        patch(target_path.read_text(encoding="utf-8"), donor_path.read_text(encoding="utf-8")),
        encoding="utf-8",
    )
    print(f"patched {target_path}: assigned C94.2 to VIDEO_OUT and retired {RETIRED}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
