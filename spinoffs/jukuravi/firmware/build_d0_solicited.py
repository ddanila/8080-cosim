#!/usr/bin/env python3
"""Build the receiver-driven T25 diagnostic and upload ROM."""

from __future__ import annotations

import argparse
import hashlib

import build_d0_resilient as base


OUTPUT = base.HERE / "diag-d0-solicited.bin"
ROM_VERSION = 0x14
IDENTITY = b"JUKURAVI-D0-SOLICITED-2400-1\0"


def build():
    saved = (base.ROM_VERSION, base.IDENTITY, base.SOLICITED_INPUT,
             base.FILTER_INVALID_SYMBOLS, base.CLEAR_INVALID_ERRORS)
    try:
        base.ROM_VERSION = ROM_VERSION
        base.IDENTITY = IDENTITY
        base.SOLICITED_INPUT = True
        base.FILTER_INVALID_SYMBOLS = False
        base.CLEAR_INVALID_ERRORS = False
        return base.build()
    finally:
        (base.ROM_VERSION, base.IDENTITY, base.SOLICITED_INPUT,
         base.FILTER_INVALID_SYMBOLS, base.CLEAR_INVALID_ERRORS) = saved


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    image, metadata = build()
    digest = hashlib.sha256(image).hexdigest()
    if args.check:
        if not OUTPUT.exists() or OUTPUT.read_bytes() != image:
            raise SystemExit("diag-d0-solicited.bin is missing or stale")
        action = "checked"
    else:
        OUTPUT.write_bytes(image)
        action = "wrote"
    print(
        f"JUKURAVI-D0-SOLICITED-BUILD: {action} {OUTPUT.name} "
        f"bytes={len(image)} self_crc16={metadata['checksum']:04X} "
        f"sha256={digest}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
