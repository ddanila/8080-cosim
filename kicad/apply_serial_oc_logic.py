#!/usr/bin/env python3
"""Replace D3/D12 with source-proved serial OC nets without PCB reserialization."""
from __future__ import annotations

import re
import sys
from pathlib import Path

from apply_s1_offboard_correction import footprint_span
from apply_wire17_landing import net_ids


REFS = ("D3", "D12")


def patch(target: str, donor: str) -> str:
    spans = [footprint_span(target, refdes) for refdes in REFS]
    for start, end in sorted(spans, reverse=True):
        target = target[:start] + target[end:]
    blocks = []
    donor_names: set[str] = set()
    for refdes in REFS:
        start, end = footprint_span(donor, refdes)
        block = donor[start:end].rstrip("\n")
        blocks.append(block)
        donor_names.update(re.findall(r'\(net \d+ "([^"]+)"\)', block))
    target_nets = net_ids(target)
    missing = sorted(donor_names - target_nets.keys())
    if missing:
        next_id = max(map(int, target_nets.values()), default=0) + 1
        declarations = "".join(
            f'\t(net {next_id + offset} "{name}")\n'
            for offset, name in enumerate(missing)
        )
        insertion = target.index("\n\t(footprint ") + 1
        target = target[:insertion] + declarations + target[insertion:]
        target_nets = net_ids(target)

    def remap(match: re.Match[str]) -> str:
        name = match.group(2)
        return f'(net {target_nets[name]} "{name}")'

    blocks = [re.sub(r'\(net (\d+) "([^"]+)"\)', remap, block) for block in blocks]
    insertion = target.index("\n\t(footprint ") + 1
    return target[:insertion] + "\n".join(blocks) + "\n" + target[insertion:]


def main() -> int:
    if len(sys.argv) != 3:
        raise SystemExit("usage: apply_serial_oc_logic.py TARGET DONOR")
    target_path, donor_path = map(Path, sys.argv[1:])
    target_path.write_text(
        patch(target_path.read_text(encoding="utf-8"), donor_path.read_text(encoding="utf-8")),
        encoding="utf-8",
    )
    print(f"patched {target_path}: replaced D3/D12 serial OC logic")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
