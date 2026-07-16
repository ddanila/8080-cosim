#!/usr/bin/env python3
"""Apply the photo-fitted D13/D105/R1 cluster and X1.107B H assignment."""
from __future__ import annotations

import re
import sys
from pathlib import Path

from apply_s1_offboard_correction import block_end, footprint_span


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


def net_ids(text: str) -> dict[str, str]:
    return {name: code for code, name in re.findall(r'(?m)^\t\(net (\d+) "([^"]+)"\)$', text)}


def translate_nets(block: str, target: str) -> str:
    ids = net_ids(target)

    def replacement(match: re.Match[str]) -> str:
        name = match.group(2)
        if name not in ids:
            raise ValueError(f"target PCB is missing net {name}")
        return f'(net {ids[name]} "{name}")'

    return re.sub(r'\(net (\d+) "([^"]+)"\)', replacement, block)


def transplant_cluster(target: str, donor: str) -> str:
    for ref in ("D13", "D105", "R1"):
        donor_start, donor_end = footprint_span(donor, ref)
        block = translate_nets(donor[donor_start:donor_end], target)
        if f'(property "Reference" "{ref}"' in target:
            start, end = footprint_span(target, ref)
            target = target[:start] + block + target[end:]
            continue
        starts = [match.start() + 1 for match in re.finditer(r'(?m)^\t\(footprint ', target)]
        insertion = max(block_end(target, start) for start in starts)
        target = target[:insertion] + "\n" + block + target[insertion:]
    return target


def assign_x1_107b(target: str) -> str:
    ids = net_ids(target)
    net_id = ids["D105_10_H"]
    start, end = footprint_span(target, "X1")
    footprint = target[start:end]
    marker = '\n\t\t(pad "107B"'
    pad_start = footprint.index(marker) + len(marker) - len('(pad "107B"')
    pad_start = footprint.rfind("(", 0, pad_start + 1)
    left, right = matching_block(footprint, pad_start)
    pad = footprint[left:right]
    wanted = f'(net {net_id} "D105_10_H")'
    if re.search(r'\(net \d+ "[^"]+"\)', pad):
        pad = re.sub(r'\(net \d+ "[^"]+"\)', wanted, pad, count=1)
    else:
        pad = pad.rstrip()
        pad = pad[:-1].rstrip() + f'\n\t\t\t{wanted}\n\t\t)'
    footprint = footprint[:left] + pad + footprint[right:]
    return target[:start] + footprint + target[end:]


def main() -> int:
    if len(sys.argv) != 3:
        raise SystemExit("usage: apply_d105_h_closure.py TARGET.kicad_pcb DONOR.kicad_pcb")
    target_path, donor_path = map(Path, sys.argv[1:])
    target = target_path.read_text(encoding="utf-8")
    donor = donor_path.read_text(encoding="utf-8")
    target = transplant_cluster(target, donor)
    target = assign_x1_107b(target)
    target_path.write_text(target, encoding="utf-8")
    print(f"patched {target_path}: fitted D13/D105/R1 and assigned X1.107B to D105_10_H")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
