#!/usr/bin/env python3
"""Remove the linker wall-clock timestamp from a deterministic PE build."""

from __future__ import annotations

import argparse
from pathlib import Path
import struct


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("executable", type=Path)
    args = parser.parse_args()
    data = bytearray(args.executable.read_bytes())
    if len(data) < 0x40 or data[:2] != b"MZ":
        raise SystemExit("normalize-pe: not an MZ executable")
    pe_offset = struct.unpack_from("<I", data, 0x3C)[0]
    if data[pe_offset:pe_offset + 4] != b"PE\0\0":
        raise SystemExit("normalize-pe: PE signature missing")
    struct.pack_into("<I", data, pe_offset + 8, 0)
    args.executable.write_bytes(data)
    print("JUKUWIN-PE-NORMALIZE: PASS (COFF timestamp=0)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
