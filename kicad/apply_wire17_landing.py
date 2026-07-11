#!/usr/bin/env python3
"""Insert one generated footprint without reserializing the PCB.

The tracked source board contains small hand-routed corrections absent from a
clean generator run.  Copy only the requested footprint block from a donor
board, adding any missing named-net declarations and remapping its nets to the
tracked board's numeric net IDs.  The default reference keeps the original
wire-17 helper invocation compatible.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

from apply_s1_offboard_correction import footprint_span


def net_ids(text: str) -> dict[str, str]:
    header = text[:text.index("\n\t(footprint ")]
    return {name: number for number, name in re.findall(
        r'(?m)^\t\(net (\d+) "([^"]+)"\)$', header)}


def main() -> int:
    if len(sys.argv) not in (3, 4):
        raise SystemExit(
            "usage: apply_wire17_landing.py TARGET.kicad_pcb DONOR.kicad_pcb [REFDES]"
        )
    target_path, donor_path = map(Path, sys.argv[1:3])
    refdes = sys.argv[3] if len(sys.argv) == 4 else "A17"
    target = target_path.read_text(encoding="utf-8")
    donor = donor_path.read_text(encoding="utf-8")
    try:
        footprint_span(target, refdes)
    except ValueError:
        pass
    else:
        raise SystemExit(f"target already contains {refdes}")

    start, end = footprint_span(donor, refdes)
    block = donor[start:end].rstrip("\n")
    target_nets = net_ids(target)
    donor_net_names = dict(re.findall(r'\(net (\d+) "([^"]+)"\)', block)).values()
    missing_names = sorted(set(donor_net_names) - target_nets.keys())
    if missing_names:
        next_id = max(map(int, target_nets.values()), default=0) + 1
        declarations = "".join(
            f'\t(net {next_id + offset} "{name}")\n'
            for offset, name in enumerate(missing_names)
        )
        first_footprint = target.index("\n\t(footprint ") + 1
        target = target[:first_footprint] + declarations + target[first_footprint:]
        target_nets = net_ids(target)

    def remap(match: re.Match[str]) -> str:
        name = match.group(2)
        if name not in target_nets:
            raise ValueError(f"target lacks donor net {name}")
        return f'(net {target_nets[name]} "{name}")'

    block = re.sub(r'\(net (\d+) "([^"]+)"\)', remap, block)
    insertion = target.index("\n\t(footprint ") + 1
    updated = target[:insertion] + block + "\n" + target[insertion:]
    target_path.write_text(updated, encoding="utf-8")
    added = f"; added nets {', '.join(missing_names)}" if missing_names else ""
    print(f"patched {target_path}: inserted generated {refdes} footprint{added}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
