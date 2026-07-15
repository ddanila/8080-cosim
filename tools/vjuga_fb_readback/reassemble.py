#!/usr/bin/env python3
"""Reassemble a VJUGA framebuffer from a captured memory-write stream.

This is the bench twin of the twin's own framebuffer dump: on real hardware the
RP2350 analyzer (capture Profile FB) records every memory write during boot as
one "ADDR DATA" line (hex, e.g. "d800 3c"); this replays that stream into a
64 KiB image and extracts the 40x241 = 9640-byte framebuffer at 0xD800. A
byte-identical result versus cosim's vram.bin is the boot PASS -- with zero
display electronics.

The exact same "ADDR DATA" format is emitted by the simulation twin
(hdl/vjuga_juku_top.v, +capture=<file>), so this tool is validated against the
verified twin before any board exists (see sim/vjuga_readback_check.sh). A later
bench mismatch therefore indicts the chip under test, not this script.

Usage:  reassemble.py <capture-stream> <framebuffer-out.bin>
"""
import sys

FB_BASE = 0xD800
FB_LEN = 40 * 241  # 9640 bytes, the mono 320x241 framebuffer stride*rows


def reassemble(capture_path):
    image = bytearray(0x10000)
    writes = 0
    for lineno, raw in enumerate(open(capture_path), 1):
        line = raw.split("#", 1)[0].strip()
        if not line:
            continue
        parts = line.split()
        if len(parts) != 2:
            raise SystemExit(f"{capture_path}:{lineno}: expected 'ADDR DATA', got {line!r}")
        addr = int(parts[0], 16) & 0xFFFF
        data = int(parts[1], 16) & 0xFF
        image[addr] = data  # last write wins, matching final DRAM state
        writes += 1
    return image[FB_BASE:FB_BASE + FB_LEN], writes


def main(argv):
    if len(argv) != 3:
        raise SystemExit(__doc__)
    fb, writes = reassemble(argv[1])
    with open(argv[2], "wb") as f:
        f.write(fb)
    sys.stderr.write(
        f"reassembled {writes} writes -> {len(fb)}-byte framebuffer "
        f"(0x{FB_BASE:04X}-0x{FB_BASE + FB_LEN - 1:04X}) -> {argv[2]}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
