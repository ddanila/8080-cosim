#!/usr/bin/env python3
"""Insert W20 and split D3.10 from the A23/X3.3 S_TTL island."""
from __future__ import annotations

import re
import sys
from pathlib import Path

from apply_a8_factory_wire_split import strip_render_caches
from apply_s1_offboard_correction import block_end, footprint_span
from apply_wire17_landing import net_ids

REMOTE_NET = "S_TTL_D3"
UUIDS = tuple(f"a2000000-0000-0000-000{i}-000000000020" for i in range(7))


def patch(target: str, donor: str) -> str:
    if 'property "Reference" "W20"' in target or REMOTE_NET in net_ids(target):
        raise ValueError("target already contains the W20 split")
    start, end = footprint_span(donor, "W20")
    block = strip_render_caches(donor[start:end].rstrip("\n"))
    found = re.findall(r'\(uuid "[^"]+"\)', block)
    if len(found) != len(UUIDS):
        raise ValueError(f"W20 donor has {len(found)} UUIDs, expected {len(UUIDS)}")
    replacements = iter(UUIDS)
    block = re.sub(r'\(uuid "[^"]+"\)', lambda _m: f'(uuid "{next(replacements)}")', block)
    nets = net_ids(target)
    net_id = max(map(int, nets.values())) + 1
    insertion = target.index("\n\t(footprint ") + 1
    target = target[:insertion] + f'\t(net {net_id} "{REMOTE_NET}")\n' + target[insertion:]
    nets = net_ids(target)
    block = re.sub(r'\(net (\d+) "([^"]+)"\)', lambda m: f'(net {nets[m.group(2)]} "{m.group(2)}")', block)
    start, end = footprint_span(target, "D3")
    footprint = target[start:end]
    match = re.search(r'(?m)^\t\t\(pad "10" ', footprint)
    if not match:
        raise ValueError("D3.10 not found")
    pad_end = block_end(footprint, match.start() + 2)
    pad = footprint[match.start():pad_end]
    old = re.findall(r'\n\t\t\t\(net \d+ "([^"]+)"\)', pad)
    if old != ["S_TTL"]:
        raise ValueError(f"D3.10 expected on S_TTL, found {old}")
    pad = re.sub(r'\n\t\t\t\(net \d+ "S_TTL"\)', f'\n\t\t\t(net {net_id} "{REMOTE_NET}")', pad, count=1)
    footprint = footprint[:match.start()] + pad + footprint[pad_end:]
    target = target[:start] + footprint + target[end:]
    insertion = target.index("\n\t(footprint ") + 1
    return target[:insertion] + block + "\n" + target[insertion:]


def main() -> int:
    if len(sys.argv) != 3:
        raise SystemExit("usage: apply_a20_factory_wire_split.py TARGET DONOR")
    target, donor = map(Path, sys.argv[1:])
    target.write_text(patch(target.read_text(), donor.read_text()))
    print(f"patched {target}: inserted W20 and split {REMOTE_NET}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
