#!/usr/bin/env python3
"""Replace the fictitious on-board X6 body with photographed A:3/A:4 lap joints."""
from __future__ import annotations

import re
import sys
from pathlib import Path

from apply_s1_offboard_correction import footprint_span
from apply_wire17_landing import net_ids


LANDINGS = ("AX603", "AX604")


def patch(target: str, donor: str) -> str:
    x6_start, x6_end = footprint_span(target, "X6")
    target_nets = net_ids(target)
    blocks: list[str] = []
    for refdes in LANDINGS:
        try:
            footprint_span(target, refdes)
        except ValueError:
            pass
        else:
            raise ValueError(f"target already contains {refdes}")
        start, end = footprint_span(donor, refdes)
        block = donor[start:end].rstrip("\n")

        def remap(match: re.Match[str]) -> str:
            name = match.group(2)
            if name not in target_nets:
                raise ValueError(f"target lacks donor net {name}")
            return f'(net {target_nets[name]} "{name}")'

        blocks.append(re.sub(r'\(net (\d+) "([^"]+)"\)', remap, block))

    target = target[:x6_start] + target[x6_end:]
    insertion = target.index("\n\t(footprint ") + 1
    return target[:insertion] + "\n".join(blocks) + "\n" + target[insertion:]


def main() -> int:
    if len(sys.argv) != 3:
        raise SystemExit(
            "usage: apply_x6_offboard_correction.py TARGET.kicad_pcb DONOR.kicad_pcb"
        )
    target_path, donor_path = map(Path, sys.argv[1:])
    target_path.write_text(
        patch(target_path.read_text(encoding="utf-8"), donor_path.read_text(encoding="utf-8")),
        encoding="utf-8",
    )
    print(f"patched {target_path}: removed X6; inserted AX603/AX604 lap joints")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
