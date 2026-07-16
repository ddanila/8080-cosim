#!/usr/bin/env python3
"""Transplant generated right-edge resistor value-bearing footprints into the source PCB."""
from __future__ import annotations

import re
import sys
from pathlib import Path

from apply_s1_offboard_correction import footprint_span


REFS = ("R100", "R102", "R108", "R86")


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
    for ref in REFS:
        donor_start, donor_end = footprint_span(donor, ref)
        block = translate_nets(donor[donor_start:donor_end], target)
        start, end = footprint_span(target, ref)
        target = target[:start] + block + target[end:]
    return target


def main() -> int:
    if len(sys.argv) != 3:
        raise SystemExit("usage: apply_right_edge_resistor_values.py TARGET.kicad_pcb DONOR.kicad_pcb")
    target_path, donor_path = map(Path, sys.argv[1:])
    target_path.write_text(
        patch(target_path.read_text(encoding="utf-8"), donor_path.read_text(encoding="utf-8")),
        encoding="utf-8",
    )
    print(f"patched {target_path}: updated {'/'.join(REFS)} values")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
