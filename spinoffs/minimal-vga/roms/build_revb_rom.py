#!/usr/bin/env python3
"""Build/check the physical 27C256 image required by rev-B overlay addressing."""
from __future__ import annotations

import argparse
import hashlib
import sys
from pathlib import Path


HERE = Path(__file__).resolve().parent
SOURCE = HERE / "ekta37_z80.bin"
OUTPUT = HERE / "ekta37_z80-27c256.bin"
SOURCE_SHA = "343ef2e6f0e5358bdc52cab7117f54ec583c0dc754499f5518ff8933bbc7befa"
OUTPUT_SHA = "e06dc0ee989d33049ad60c5a182df4d3da8814f206fd19c4f500603c772d9b2f"


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    source = SOURCE.read_bytes()
    if len(source) != 16384 or sha(source) != SOURCE_SHA:
        raise SystemExit("unexpected ekta37_z80.bin source")
    image = source + source
    if len(image) != 32768 or sha(image) != OUTPUT_SHA:
        raise SystemExit("27C256 image contract changed")
    if args.check:
        if not OUTPUT.exists() or OUTPUT.read_bytes() != image:
            raise SystemExit("ekta37_z80-27c256.bin is stale; rebuild without --check")
    else:
        OUTPUT.write_bytes(image)
    print(f"REVB-ROM: PASS 32768 bytes sha256={OUTPUT_SHA}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
