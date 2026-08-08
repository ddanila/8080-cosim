#!/usr/bin/env python3
"""Build the focused PIC/EI loop used by the typed INTA bus differential."""

from __future__ import annotations

import argparse
from pathlib import Path


ROM_SIZE = 0x4000
PROGRAM = bytes(
    (
        0xF3,              # DI
        0x3E, 0xD6,        # MVI A,D6: PIC ICW1, high vector bits -> FED4
        0xD3, 0x00,        # OUT 00
        0x3E, 0xFE,        # MVI A,FE: PIC ICW2/vector high byte
        0xD3, 0x01,        # OUT 01
        0x3E, 0xDF,        # MVI A,DF: unmask IR5 only
        0xD3, 0x01,        # OUT 01
        0x31, 0x00, 0x40,  # LXI SP,4000
        0xFB,              # EI
        0x00,              # one-instruction EI delay
        0xC3, 0x12, 0x00,  # JMP 0012: interruptible stable loop
    )
)


def build() -> bytes:
    image = bytearray(ROM_SIZE)
    image[: len(PROGRAM)] = PROGRAM
    return bytes(image)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path)
    parser.add_argument("--hex", action="store_true", help="write readmemh text")
    args = parser.parse_args()
    image = build()
    if args.hex:
        args.output.write_text("".join(f"{byte:02x}\n" for byte in image), encoding="ascii")
    else:
        args.output.write_bytes(image)
    print(f"INTA-BUS-ROM: wrote {len(image)} bytes, loop=0012 vector=FED4")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
