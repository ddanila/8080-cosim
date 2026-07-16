#!/usr/bin/env python3
"""Transplant generated C19/right-edge values and photo-closed local joins."""
from __future__ import annotations

import re
import sys
from pathlib import Path

from apply_s1_offboard_correction import footprint_span


REFS = ("C19", "R100", "R102", "R108", "R86")
RESISTOR_REFS = REFS[1:]
JOINED_NETS = {
    "C19_1_R100_1_BOUNDARY": "C19_1_BOUNDARY",
    "C19_2_R86_1_BOUNDARY": "C19_2_BOUNDARY",
}
RETIRED = (
    *(f"{ref}_2_BOUNDARY" for ref in RESISTOR_REFS),
    "R100_1_BOUNDARY",
    "R86_1_BOUNDARY",
)
COMMON_RAIL = "RIGHT_EDGE_RESISTOR_RAIL_BOUNDARY"


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


def patch(target: str, donor: str) -> str:
    ids = net_ids(target)
    for joined, seed in JOINED_NETS.items():
        if joined not in ids:
            if seed not in ids:
                raise ValueError(f"target PCB is missing both {joined} and migration seed {seed}")
            target = target.replace(f'"{seed}"', f'"{joined}"')
            ids = net_ids(target)
    if COMMON_RAIL not in ids:
        seed = "R100_2_BOUNDARY"
        if seed in ids:
            target = target.replace(f'"{seed}"', f'"{COMMON_RAIL}"')
        else:
            next_id = max(map(int, ids.values())) + 1
            footprint_at = target.index("\n\t(footprint ")
            target = target[:footprint_at] + f'\n\t(net {next_id} "{COMMON_RAIL}")' + target[footprint_at:]
    for ref in REFS:
        donor_start, donor_end = footprint_span(donor, ref)
        block = translate_nets(donor[donor_start:donor_end], target)
        start, end = footprint_span(target, ref)
        target = target[:start] + block + target[end:]
    for name in RETIRED:
        target, count = re.subn(
            rf'(?m)^\t\(net \d+ "{re.escape(name)}"\)\n', "", target
        )
        if count > 1:
            raise ValueError(f"duplicate retired declaration {name}")
        if f'"{name}"' in target:
            raise ValueError(f"retired net {name} still has references")
    return target


def main() -> int:
    if len(sys.argv) != 3:
        raise SystemExit("usage: apply_right_edge_resistor_values.py TARGET.kicad_pcb DONOR.kicad_pcb")
    target_path, donor_path = map(Path, sys.argv[1:])
    target_path.write_text(
        patch(target_path.read_text(encoding="utf-8"), donor_path.read_text(encoding="utf-8")),
        encoding="utf-8",
    )
    print(f"patched {target_path}: updated {'/'.join(REFS)} values, C19 joins, and shared pin-2 rail")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
