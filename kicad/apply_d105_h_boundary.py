#!/usr/bin/env python3
"""Remove the false D105.10-to-minus-5V assignment from route artifacts."""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "kicad/juku.kicad_pcb"
ROUTED = ROOT / "kicad/juku_routed.kicad_pcb"
DSN = ROOT / "kicad/juku.dsn"
SES = ROOT / "kicad/juku.ses"
NEW_NET = 352
REMOVED_SEGMENTS = (
    "3896bafd-e60f-4be6-8d17-bcca07e7b4b9",
    "43ebc532-c09d-4739-a5f6-f48f290b06c2",
    "bebfd867-5f59-4a4b-9e07-eec30d01f61f",
    "d0ed8a5b-531b-4486-adc2-4c2da185afc7",
    "e851b90c-2d09-494c-b562-f5a9a5eb8798",
    "6392bf0b-30dc-4022-8620-0e688c3edbd0",
)


def matching_block(text: str, start: int) -> tuple[int, int]:
    depth = 0
    in_string = False
    escaped = False
    for index in range(start, len(text)):
        char = text[index]
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
                return start, index + 1
    raise ValueError("unterminated KiCad block")


def footprint_block(text: str, refdes: str) -> tuple[int, int]:
    reference = text.index(f'(property "Reference" "{refdes}"')
    start = text.rfind("\n\t(footprint ", 0, reference) + 2
    return matching_block(text, start)


def patch_pcb(path: Path, remove_segments: bool) -> None:
    text = path.read_text(encoding="utf-8")
    if '\t(net 352 "D105_10_H")' not in text:
        insertion = text.index("\n\t(footprint ")
        text = text[:insertion] + '\n\t(net 352 "D105_10_H")' + text[insertion:]

    start, end = footprint_block(text, "D105")
    block = text[start:end]
    pad_start = block.index('\n\t\t(pad "10"') + 3
    left, right = matching_block(block, pad_start)
    pad = block[left:right]
    pad, changed = re.subn(r'\(net\s+144\s+"M5V_DERIVED"\)',
                           '(net 352 "D105_10_H")', pad, count=1)
    if changed != 1 and "D105_10_H" not in pad:
        raise SystemExit(f"{path}: D105.10 does not carry expected old/new net")
    block = block[:left] + pad + block[right:]
    text = text[:start] + block + text[end:]

    if remove_segments:
        for uuid in REMOVED_SEGMENTS:
            marker = f'(uuid "{uuid}")'
            if marker not in text:
                continue
            position = text.index(marker)
            item_start = text.rfind("\n\t(segment", 0, position) + 2
            left, right = matching_block(text, item_start)
            text = text[:left - 2] + text[right:]
    path.write_text(text, encoding="utf-8")


def patch_dsn() -> None:
    text = DSN.read_text(encoding="utf-8")
    text = text.replace("(pins R19-2 VD5-2 E5-1 D105-10 D1-11)",
                        "(pins R19-2 VD5-2 E5-1 D1-11)")
    if "(net D105_10_H" not in text:
        marker = "\n    (net D105_GATE1_Y"
        text = text.replace(marker,
                            "\n    (net D105_10_H\n      (pins D105-10)\n    )" + marker,
                            1)
    DSN.write_text(text, encoding="utf-8")


def patch_ses() -> None:
    text = SES.read_text(encoding="utf-8")
    old_tail = """            355722 -2104985
            354781 -2105926
            354781 -2106448
            353083 -2108146
            353083 -2108167
            344400 -2116850"""
    text = text.replace(old_tail, "            355722 -2104985", 1)
    front_branch = """
        (wire
          (path F.Cu 2000
            444000 -2168900
            396450 -2168900
            344400 -2116850
          )
        )"""
    text = text.replace(front_branch, "", 1)
    SES.write_text(text, encoding="utf-8")


patch_pcb(SOURCE, False)
patch_pcb(ROUTED, True)
patch_dsn()
patch_ses()
print("D105 H boundary applied to source/routed PCB, DSN, and SES")
