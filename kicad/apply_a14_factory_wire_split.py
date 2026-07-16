#!/usr/bin/env python3
"""Insert W14 and split the D35 PHI2 output without PCB-wide churn."""
from __future__ import annotations

import re
import sys
from pathlib import Path

from apply_a8_factory_wire_split import strip_render_caches
from apply_s1_offboard_correction import block_end, footprint_span
from apply_wire17_landing import net_ids


REMOTE_NET = "PHI2_D35"
UUID_TEMPLATE = "a1400000-0000-0000-000{}-000000000014"


def patch(target: str, donor: str) -> str:
    if 'property "Reference" "W14"' in target or REMOTE_NET in net_ids(target):
        raise ValueError("target already contains the W14 split")

    nets = net_ids(target)
    next_net_id = max(map(int, nets.values())) + 1
    insertion = target.index("\n\t(footprint ") + 1
    target = target[:insertion] + f'\t(net {next_net_id} "{REMOTE_NET}")\n' + target[insertion:]
    nets = net_ids(target)

    start, end = footprint_span(donor, "W14")
    block = strip_render_caches(donor[start:end].rstrip("\n"))
    uuids = re.findall(r'\(uuid "[^"]+"\)', block)
    if len(uuids) != 7:
        raise ValueError(f"W14 donor has {len(uuids)} UUIDs, expected 7")
    replacements = iter(UUID_TEMPLATE.format(index) for index in range(7))
    block = re.sub(
        r'\(uuid "[^"]+"\)',
        lambda _match: f'(uuid "{next(replacements)}")',
        block,
    )
    block = re.sub(
        r'\(net (\d+) "([^"]+)"\)',
        lambda match: f'(net {nets[match.group(2)]} "{match.group(2)}")',
        block,
    )

    start, end = footprint_span(target, "D35")
    footprint = target[start:end]
    match = re.search(r'(?m)^\t\t\(pad "12" ', footprint)
    if not match:
        raise ValueError("D35.12 not found")
    pad_end = block_end(footprint, match.start() + 2)
    pad = footprint[match.start():pad_end]
    old = re.findall(r'\n\t\t\t\(net \d+ "([^"]+)"\)', pad)
    if old != ["PHI2"]:
        raise ValueError(f"D35.12 expected on PHI2, found {old}")
    pad = re.sub(
        r'\n\t\t\t\(net \d+ "PHI2"\)',
        f'\n\t\t\t(net {nets[REMOTE_NET]} "{REMOTE_NET}")',
        pad,
        count=1,
    )
    footprint = footprint[:match.start()] + pad + footprint[pad_end:]
    target = target[:start] + footprint + target[end:]

    insertion = target.index("\n\t(footprint ") + 1
    return target[:insertion] + block + "\n" + target[insertion:]


def main() -> int:
    if len(sys.argv) != 3:
        raise SystemExit("usage: apply_a14_factory_wire_split.py TARGET DONOR")
    target, donor = map(Path, sys.argv[1:])
    target.write_text(patch(target.read_text(), donor.read_text()))
    print(f"patched {target}: inserted W14 and split {REMOTE_NET}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
