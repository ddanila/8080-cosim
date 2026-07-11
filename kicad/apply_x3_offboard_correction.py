#!/usr/bin/env python3
"""Install photo-fitted A21-A32/D104 data without reserializing the PCB."""
from __future__ import annotations

import re
import sys
from pathlib import Path

from apply_s1_offboard_correction import footprint_span
from apply_wire17_landing import net_ids


INSERT = tuple(f"A{number}" for number in range(21, 33)) + ("D104", "D11")
REMOVE = ("X3", "D104", "D11")


def patch(target: str, donor: str) -> str:
    spans = [footprint_span(target, refdes) for refdes in REMOVE]
    for refdes in INSERT[:12]:
        try:
            footprint_span(target, refdes)
        except ValueError:
            pass
        else:
            raise ValueError(f"target already contains {refdes}")
    for start, end in sorted(spans, reverse=True):
        target = target[:start] + target[end:]

    target_nets = net_ids(target)
    donor_blocks = []
    donor_names: set[str] = set()
    for refdes in INSERT:
        start, end = footprint_span(donor, refdes)
        block = donor[start:end].rstrip("\n")
        donor_blocks.append(block)
        donor_names.update(re.findall(r'\(net \d+ "([^"]+)"\)', block))
    missing = sorted(donor_names - target_nets.keys())
    if missing:
        next_id = max(map(int, target_nets.values()), default=0) + 1
        declarations = "".join(
            f'\t(net {next_id + offset} "{name}")\n'
            for offset, name in enumerate(missing)
        )
        first_footprint = target.index("\n\t(footprint ") + 1
        target = target[:first_footprint] + declarations + target[first_footprint:]
        target_nets = net_ids(target)

    def remap(match: re.Match[str]) -> str:
        name = match.group(2)
        return f'(net {target_nets[name]} "{name}")'

    blocks = [re.sub(r'\(net (\d+) "([^"]+)"\)', remap, block) for block in donor_blocks]
    insertion = target.index("\n\t(footprint ") + 1
    return target[:insertion] + "\n".join(blocks) + "\n" + target[insertion:]


def main() -> int:
    if len(sys.argv) != 3:
        raise SystemExit("usage: apply_x3_offboard_correction.py TARGET DONOR")
    target_path, donor_path = map(Path, sys.argv[1:])
    target_path.write_text(
        patch(target_path.read_text(encoding="utf-8"), donor_path.read_text(encoding="utf-8")),
        encoding="utf-8",
    )
    print(f"patched {target_path}: removed X3; inserted A21-A32 and corrected D104")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
