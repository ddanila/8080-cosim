#!/usr/bin/env python3
"""Insert the modeled A:8 assembly wire without PCB-wide reserialization.

The clean board generator emits the W8 two-pad footprint.  The tracked source
PCB also contains hand-preserved UUIDs and local corrections, so copy only W8,
append its new D38-side island net, and move D38.8 onto that island.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

from apply_s1_offboard_correction import block_end, footprint_span
from apply_wire17_landing import net_ids


WIRE_REF = "W8"
REMOTE_NET = "STSTB_D38"
WIRE_UUIDS = (
    "4afa8f6f-90dc-4fb0-be07-6901317ba35b",
    "e22c4aeb-b25e-4e8a-9212-31384d0e545e",
    "6b67ec35-753b-42c9-a79c-5ef0b9ef31e4",
    "4c503ffb-e535-434a-b44e-e98512e97d62",
    "2943a8e5-4b58-4ca7-b77e-96551a85e5af",
    "8976d9c1-9e5d-4982-9c61-68160a660fad",
    "4a4c2309-f1d3-47ad-8bc2-94a51ef237be",
)


def assign_d38_pad8(text: str, net_id: int) -> str:
    start, end = footprint_span(text, "D38")
    footprint = text[start:end]
    match = re.search(r'(?m)^\t\t\(pad "8" ', footprint)
    if not match:
        raise ValueError("D38 pad 8 not found")
    pad_end = block_end(footprint, match.start() + 2)
    pad = footprint[match.start():pad_end]
    old = re.findall(r'\n\t\t\t\(net \d+ "([^"]+)"\)', pad)
    if old != ["STSTB"]:
        raise ValueError(f"D38.8 expected on STSTB, found {old}")
    pad = re.sub(
        r'\n\t\t\t\(net \d+ "STSTB"\)',
        f'\n\t\t\t(net {net_id} "{REMOTE_NET}")',
        pad,
        count=1,
    )
    footprint = footprint[:match.start()] + pad + footprint[pad_end:]
    return text[:start] + footprint + text[end:]


def strip_render_caches(block: str) -> str:
    """Drop KiCad text-outline caches from the copied hidden properties."""
    marker = "\n\t\t\t(render_cache "
    while marker in block:
        start = block.index(marker)
        expression = start + 4
        end = block_end(block, expression)
        block = block[:start] + block[end:]
    return block


def stabilize_uuids(block: str) -> str:
    """Replace pcbnew's random donor UUIDs with the tracked W8 identities."""
    found = re.findall(r'\(uuid "[^"]+"\)', block)
    if len(found) != len(WIRE_UUIDS):
        raise ValueError(
            f"W8 donor has {len(found)} UUIDs, expected {len(WIRE_UUIDS)}"
        )
    replacements = iter(WIRE_UUIDS)
    return re.sub(
        r'\(uuid "[^"]+"\)',
        lambda _match: f'(uuid "{next(replacements)}")',
        block,
    )


def patch(target: str, donor: str) -> str:
    try:
        footprint_span(target, WIRE_REF)
    except ValueError:
        pass
    else:
        raise ValueError(f"target already contains {WIRE_REF}")
    if REMOTE_NET in net_ids(target):
        raise ValueError(f"target already contains {REMOTE_NET}")

    donor_start, donor_end = footprint_span(donor, WIRE_REF)
    block = stabilize_uuids(
        strip_render_caches(donor[donor_start:donor_end].rstrip("\n"))
    )
    target_nets = net_ids(target)
    next_id = max(map(int, target_nets.values()), default=0) + 1
    first_footprint = target.index("\n\t(footprint ") + 1
    target = (
        target[:first_footprint]
        + f'\t(net {next_id} "{REMOTE_NET}")\n'
        + target[first_footprint:]
    )
    target_nets = net_ids(target)

    def remap(match: re.Match[str]) -> str:
        name = match.group(2)
        if name not in target_nets:
            raise ValueError(f"target lacks donor net {name}")
        return f'(net {target_nets[name]} "{name}")'

    block = re.sub(r'\(net (\d+) "([^"]+)"\)', remap, block)
    target = assign_d38_pad8(target, next_id)
    insertion = target.index("\n\t(footprint ") + 1
    return target[:insertion] + block + "\n" + target[insertion:]


def main() -> int:
    if len(sys.argv) != 3:
        raise SystemExit(
            "usage: apply_a8_factory_wire_split.py TARGET.kicad_pcb DONOR.kicad_pcb"
        )
    target_path, donor_path = map(Path, sys.argv[1:])
    updated = patch(
        target_path.read_text(encoding="utf-8"),
        donor_path.read_text(encoding="utf-8"),
    )
    target_path.write_text(updated, encoding="utf-8")
    print(
        f"patched {target_path}: inserted {WIRE_REF}; "
        f"split D38.8 onto {REMOTE_NET}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
