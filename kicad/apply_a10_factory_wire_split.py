#!/usr/bin/env python3
"""Insert W10 and split the D50/D51 select island without PCB-wide churn."""
from __future__ import annotations

import re
import sys
from pathlib import Path

from apply_a8_factory_wire_split import strip_render_caches
from apply_s1_offboard_correction import block_end, footprint_span
from apply_wire17_landing import net_ids


REMOTE_NET = "W10_QA_SEL_D50"
UUIDS = (
    "a1000000-0000-0000-0000-000000000010",
    "a1000000-0000-0000-0001-000000000010",
    "a1000000-0000-0000-0002-000000000010",
    "a1000000-0000-0000-0003-000000000010",
    "a1000000-0000-0000-0004-000000000010",
    "a1000000-0000-0000-0005-000000000010",
    "a1000000-0000-0000-0006-000000000010",
)


def move_pad(text: str, ref: str, pin: str, net_id: int) -> str:
    start, end = footprint_span(text, ref)
    footprint = text[start:end]
    match = re.search(rf'(?m)^\t\t\(pad "{pin}" ', footprint)
    if not match:
        raise ValueError(f"{ref}.{pin} not found")
    pad_end = block_end(footprint, match.start() + 2)
    pad = footprint[match.start():pad_end]
    old = re.findall(r'\n\t\t\t\(net \d+ "([^"]+)"\)', pad)
    if old != ["W10_QA_SEL"]:
        raise ValueError(f"{ref}.{pin} expected on W10_QA_SEL, found {old}")
    pad = re.sub(
        r'\n\t\t\t\(net \d+ "W10_QA_SEL"\)',
        f'\n\t\t\t(net {net_id} "{REMOTE_NET}")', pad, count=1,
    )
    footprint = footprint[:match.start()] + pad + footprint[pad_end:]
    return text[:start] + footprint + text[end:]


def patch(target: str, donor: str) -> str:
    if 'property "Reference" "W10"' in target or REMOTE_NET in net_ids(target):
        raise ValueError("target already contains the W10 split")
    start, end = footprint_span(donor, "W10")
    block = strip_render_caches(donor[start:end].rstrip("\n"))
    found = re.findall(r'\(uuid "[^"]+"\)', block)
    if len(found) != len(UUIDS):
        raise ValueError(f"W10 donor has {len(found)} UUIDs, expected {len(UUIDS)}")
    replacements = iter(UUIDS)
    block = re.sub(r'\(uuid "[^"]+"\)', lambda _m: f'(uuid "{next(replacements)}")', block)

    nets = net_ids(target)
    net_id = max(map(int, nets.values())) + 1
    insertion = target.index("\n\t(footprint ") + 1
    target = target[:insertion] + f'\t(net {net_id} "{REMOTE_NET}")\n' + target[insertion:]
    nets = net_ids(target)
    block = re.sub(
        r'\(net (\d+) "([^"]+)"\)',
        lambda m: f'(net {nets[m.group(2)]} "{m.group(2)}")', block,
    )
    target = move_pad(target, "D50", "1", net_id)
    target = move_pad(target, "D51", "1", net_id)
    insertion = target.index("\n\t(footprint ") + 1
    return target[:insertion] + block + "\n" + target[insertion:]


def main() -> int:
    if len(sys.argv) != 3:
        raise SystemExit("usage: apply_a10_factory_wire_split.py TARGET DONOR")
    target, donor = map(Path, sys.argv[1:])
    target.write_text(patch(target.read_text(), donor.read_text()))
    print(f"patched {target}: inserted W10 and split {REMOTE_NET}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
