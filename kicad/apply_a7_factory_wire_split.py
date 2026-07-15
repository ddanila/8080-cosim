#!/usr/bin/env python3
"""Insert W7 and split the D35 PHI1 output without PCB-wide churn."""
from __future__ import annotations

import re
import sys
from pathlib import Path

from apply_a8_factory_wire_split import strip_render_caches
from apply_s1_offboard_correction import block_end, footprint_span
from apply_wire17_landing import net_ids


SPLITS = (
    ("W7", "D35", "10", "PHI1", "PHI1_D35", "a7000000-0000-0000-000{}-000000000007"),
)


def patch(target: str, donor: str) -> str:
    nets = net_ids(target)
    for ref, _owner, _pin, _main_net, remote_net, _uuid in SPLITS:
        if f'property "Reference" "{ref}"' in target or remote_net in nets:
            raise ValueError(f"target already contains the {ref} split")

    next_net_id = max(map(int, nets.values())) + 1
    insertion = target.index("\n\t(footprint ") + 1
    declarations = "".join(
        f'\t(net {next_net_id + offset} "{split[4]}")\n'
        for offset, split in enumerate(SPLITS)
    )
    target = target[:insertion] + declarations + target[insertion:]
    nets = net_ids(target)

    blocks: list[str] = []
    for ref, owner, pin_number, main_net, remote_net, uuid_template in SPLITS:
        start, end = footprint_span(donor, ref)
        block = strip_render_caches(donor[start:end].rstrip("\n"))
        uuids = re.findall(r'\(uuid "[^"]+"\)', block)
        if len(uuids) != 7:
            raise ValueError(f"{ref} donor has {len(uuids)} UUIDs, expected 7")
        replacements = iter(uuid_template.format(index) for index in range(7))
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
        blocks.append(block)

        start, end = footprint_span(target, owner)
        footprint = target[start:end]
        match = re.search(rf'(?m)^\t\t\(pad "{pin_number}" ', footprint)
        if not match:
            raise ValueError(f"{owner}.{pin_number} not found")
        pad_end = block_end(footprint, match.start() + 2)
        pad = footprint[match.start():pad_end]
        old = re.findall(r'\n\t\t\t\(net \d+ "([^"]+)"\)', pad)
        if old != [main_net]:
            raise ValueError(f"{owner}.{pin_number} expected on {main_net}, found {old}")
        pad = re.sub(
            rf'\n\t\t\t\(net \d+ "{main_net}"\)',
            f'\n\t\t\t(net {nets[remote_net]} "{remote_net}")',
            pad,
            count=1,
        )
        footprint = footprint[:match.start()] + pad + footprint[pad_end:]
        target = target[:start] + footprint + target[end:]

    insertion = target.index("\n\t(footprint ") + 1
    return target[:insertion] + "\n".join(blocks) + "\n" + target[insertion:]


def main() -> int:
    if len(sys.argv) != 3:
        raise SystemExit("usage: apply_a7_factory_wire_split.py TARGET DONOR")
    target, donor = map(Path, sys.argv[1:])
    target.write_text(patch(target.read_text(), donor.read_text()))
    print(f"patched {target}: inserted W7 and split PHI1_D35")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
