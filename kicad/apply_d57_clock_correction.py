#!/usr/bin/env python3
"""Transplant a DRC-reviewed D57 copper candidate without reserializing the PCB.

KiCad 10.0 rewrites the whole 10.99 board on save. This preserves the existing
file format and transfers only the reviewed pad/net and track/via UUID delta.
Run on temporary outputs first; use KiCad DRC and endpoint checks to qualify.
"""

from __future__ import annotations

import argparse
from pathlib import Path
import re


SOURCE_PAD_UUID = "aa9cb6db-5ef8-496f-9062-eeeb54666e77"
ROUTED_PAD_UUID = "6ae34792-d817-4721-ad00-763df84e36e7"
ALLOWED_NETS = {"CLK_123M", "VERT_RTR"}
REMOVED_UUIDS = {
    "0b998135-7830-427d-81cf-8f9d80faf5bc",
    "21ba77cf-aa16-4bf0-9b6b-ade79b21266e",
    "3c46e97e-c99e-4e17-ac30-d296d94253e6",
    "3f8e56e4-8da2-4740-bdcf-f4c2b5e018bf",
    "919c8d71-6a1f-49b3-96b1-fd2698752db5",
}
ITEM_RE = re.compile(r"(?ms)^\t\((?:segment|via)\n.*?^\t\)\n")
UUID_RE = re.compile(r'\(uuid "([0-9a-f-]+)"\)')
NET_DECL_RE = re.compile(r'^\t\(net (\d+) "([^"]+)"\)$', re.M)
PAD_RE = re.compile(r'(?ms)^\t\t\(pad "18" .*?^\t\t\)')


def items(data: str) -> dict[str, str]:
    result = {}
    for match in ITEM_RE.finditer(data):
        item = match.group()
        uuid = UUID_RE.search(item)
        if uuid is None or uuid.group(1) in result:
            raise ValueError("missing or duplicate track/via UUID")
        result[uuid.group(1)] = item
    return result


def change_pad(data: str, expected_uuid: str) -> str:
    footprints = re.finditer(r"(?ms)^\t\(footprint .*?^\t\)\n", data)
    matches = [match for match in footprints if '(property "Reference" "D57"' in match.group()]
    if len(matches) != 1:
        raise ValueError(f"expected one D57 footprint, got {len(matches)}")
    match = matches[0]
    footprint = match.group()
    pads = list(PAD_RE.finditer(footprint))
    pads = [pad for pad in pads if expected_uuid in pad.group()]
    if len(pads) != 1:
        raise ValueError("D57.18 pad UUID mismatch")
    pad = pads[0]
    old_net = re.search(r'\(net \d+ "CLK_123M"\)', pad.group())
    if old_net is None:
        raise ValueError("D57.18 is not on expected old net")
    codes = {name: int(code) for code, name in NET_DECL_RE.findall(data)}
    replacement = pad.group().replace(old_net.group(), f'(net {codes["VERT_RTR"]} "VERT_RTR")')
    footprint = footprint[:pad.start()] + replacement + footprint[pad.end():]
    return data[:match.start()] + footprint + data[match.end():]


def transplant(source: str, routed: str, candidate: str) -> tuple[str, str]:
    source = change_pad(source, SOURCE_PAD_UUID)
    old_items = items(routed)
    new_items = items(candidate)
    removed = set(old_items) - set(new_items)
    added = set(new_items) - set(old_items)
    if removed != REMOVED_UUIDS or len(added) != 49:
        raise ValueError(f"unexpected copper delta: removed={sorted(removed)}, added={len(added)}")
    codes = {name: int(code) for code, name in NET_DECL_RE.findall(routed)}
    for uuid in sorted(removed):
        if f'(net {codes["CLK_123M"]})' not in old_items[uuid]:
            raise ValueError(f"unexpected removed copper net: {uuid}")
        routed = routed.replace(old_items[uuid], "", 1)
    additions = []
    for uuid in sorted(added):
        item = new_items[uuid]
        net_match = re.search(r'\(net "([^"]+)"\)', item)
        if net_match is None or net_match.group(1) not in ALLOWED_NETS:
            raise ValueError(f"unexpected added copper net: {uuid}")
        item = item.replace(net_match.group(), f'(net {codes[net_match.group(1)]})')
        additions.append(item)
    routed = change_pad(routed, ROUTED_PAD_UUID)
    if not routed.endswith("\n)\n"):
        raise ValueError("unexpected PCB ending")
    routed = routed[:-2] + "".join(additions) + ")\n"
    return source, routed


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("source", "routed", "candidate", "source_output", "routed_output"):
        parser.add_argument(name, type=Path)
    args = parser.parse_args()
    source, routed = transplant(
        args.source.read_text(), args.routed.read_text(), args.candidate.read_text()
    )
    for output, data in ((args.source_output, source), (args.routed_output, routed)):
        if output.resolve() in {args.source.resolve(), args.routed.resolve(), args.candidate.resolve()}:
            raise ValueError("outputs must be separate from inputs")
        output.write_text(data)
    print("D57.18 -> VERT_RTR; removed 5 stale CLK items; added 49 reviewed copper items")


if __name__ == "__main__":
    main()
