#!/usr/bin/env python3
"""Retire the unproved D94 same-as-D8 address scaffold in the source PCB.

The original FDC scaffold assigned D94 A0-A4 to BA11-BA15 by analogy with
D8. No .009 scan, photo trace, or owner continuity supports that assignment.
This idempotent text patch preserves the reviewed PCB UUIDs, item order, and
existing net codes while moving only D94 pins 10-14 onto explicit boundaries.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BOARD = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "kicad/juku.kicad_pcb"
INPUTS = {
    "10": ("BA11", 418, "D94_A0_BOUNDARY"),
    "11": ("BA12", 573, "D94_A1_BOUNDARY"),
    "12": ("BA13", 574, "D94_A2_BOUNDARY"),
    "13": ("BA14", 575, "D94_A3_D104_X4_PULLUP"),
    "14": ("BA15", 576, "D94_A4_BOUNDARY"),
}


def matching_block(text: str, start: int) -> tuple[int, int]:
    depth = 0
    in_string = False
    escaped = False
    for pos in range(start, len(text)):
        char = text[pos]
        if in_string:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
            continue
        if char == '"':
            in_string = True
        elif char == "(":
            depth += 1
        elif char == ")":
            depth -= 1
            if depth == 0:
                return start, pos + 1
    raise ValueError("unterminated KiCad S-expression")


def footprint_block(text: str, ref: str) -> tuple[int, int]:
    ref_pos = text.find(f'(property "Reference" "{ref}"')
    if ref_pos < 0:
        raise ValueError(f"{ref} footprint absent")
    start = text.rfind("\n\t(footprint ", 0, ref_pos)
    if start < 0:
        raise ValueError(f"{ref} footprint start absent")
    return matching_block(text, start + 2)


def patch_pad(block: str, pin: str, retired: str, code: int, boundary: str) -> tuple[str, bool]:
    match = re.search(rf'\n\t\t\(pad "{re.escape(pin)}"\s', block)
    if not match:
        raise ValueError(f"D94.{pin} pad absent")
    start, end = matching_block(block, match.start() + 3)
    pad = block[start:end]
    net = re.search(r'\(net\s+(\d+)\s+"([^"]+)"\)', pad)
    if not net:
        raise ValueError(f"D94.{pin} has no net")
    current = net.group(2)
    if current == boundary:
        if int(net.group(1)) != code:
            raise ValueError(f"D94.{pin} boundary has unexpected net code {net.group(1)}")
        return block, False
    if current != retired:
        raise ValueError(
            f"D94.{pin} is on unexpected net {current!r}; expected "
            f"retired {retired!r} or boundary {boundary!r}"
        )
    replacement = f'(net {code} "{boundary}")'
    pad = pad[: net.start()] + replacement + pad[net.end() :]
    return block[:start] + pad + block[end:], True


def main() -> None:
    text = BOARD.read_text(encoding="utf-8")
    original = text

    # The reviewed board intentionally has a free net code 418. Fill that gap
    # with A0; append A1-A4 after the three photo-promoted tail nets. This keeps
    # every existing code stable and avoids a whole-board serialization diff.
    declarations = [(code, name) for _, code, name in INPUTS.values()]
    if not all(f'(net {code} "{name}")' in text for code, name in declarations):
        if any(re.search(rf'\(net\s+{code}\s+"(?!{re.escape(name)}")', text) for code, name in declarations):
            raise ValueError("a reserved D94 boundary net code is already occupied")
        if '(net 418 "D94_A0_BOUNDARY")' not in text:
            pattern = r'(?m)^(\t\(net 417 "D93_RG_BOUNDARY"\))$'
            text, count = re.subn(pattern, r'\1\n\t(net 418 "D94_A0_BOUNDARY")', text)
            if count != 1:
                raise ValueError("D93_RG boundary declaration anchor is not unique")
        additions = "".join(
            f'\t(net {code} "{name}")\n'
            for _, code, name in list(INPUTS.values())[1:]
            if f'(net {code} "{name}")' not in text
        )
        if additions:
            pattern = r'(?m)^(\t\(net 572 "FDC_WE_N"\))$'
            text, count = re.subn(pattern, lambda match: match.group(1) + "\n" + additions.rstrip("\n"), text)
            if count != 1:
                raise ValueError("FDC tail-net declaration anchor is not unique")

    start, end = footprint_block(text, "D94")
    block = text[start:end]
    changed_pads = 0
    for pin, (retired, code, boundary) in INPUTS.items():
        block, changed = patch_pad(block, pin, retired, code, boundary)
        changed_pads += int(changed)
    text = text[:start] + block + text[end:]

    if text != original:
        BOARD.write_text(text, encoding="utf-8")
    print(f"patched D94 A0-A4 input boundaries; changed {changed_pads} pads in {BOARD}")


if __name__ == "__main__":
    main()
