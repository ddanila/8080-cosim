#!/usr/bin/env python3
"""Build T28 with verified parser stores in private C000h workspace RAM."""

from __future__ import annotations

import argparse
import hashlib

import build_d0_resilient as base
from build_d2_loader_v2 import emit_loader as emit_loader_v2


OUTPUT = base.HERE / "diag-d0-buffer-verified.bin"
DOS_OUTPUT = base.HERE / "dos" / "T28HOST.BIN"
README = base.HERE / "README.md"
ROM_VERSION = 0x17
IDENTITY = b"JUKURAVI-D0-BUFFER-VERIFIED-2400-1\0"


def build():
    saved = (
        base.ROM_VERSION,
        base.IDENTITY,
        base.SOLICITED_INPUT,
        base.FILTER_INVALID_SYMBOLS,
        base.CLEAR_INVALID_ERRORS,
        base.VERIFY_BUFFER_STORES,
        base.LOADER_EMITTER,
        base.LOADER_WORKSPACE_BASE,
        base.LOADER_WORKSPACE_BYTES,
    )
    try:
        base.ROM_VERSION = ROM_VERSION
        base.IDENTITY = IDENTITY
        base.SOLICITED_INPUT = True
        base.FILTER_INVALID_SYMBOLS = True
        base.CLEAR_INVALID_ERRORS = True
        base.VERIFY_BUFFER_STORES = True
        base.LOADER_EMITTER = emit_loader_v2
        base.LOADER_WORKSPACE_BASE = 0xC000
        base.LOADER_WORKSPACE_BYTES = 0x1000
        return base.build()
    finally:
        (
            base.ROM_VERSION,
            base.IDENTITY,
            base.SOLICITED_INPUT,
            base.FILTER_INVALID_SYMBOLS,
            base.CLEAR_INVALID_ERRORS,
            base.VERIFY_BUFFER_STORES,
            base.LOADER_EMITTER,
            base.LOADER_WORKSPACE_BASE,
            base.LOADER_WORKSPACE_BYTES,
        ) = saved


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    image, metadata = build()
    digest = hashlib.sha256(image).hexdigest()
    if args.check:
        for output in (OUTPUT, DOS_OUTPUT):
            if not output.exists() or output.read_bytes() != image:
                raise SystemExit(f"{output.name} is missing or stale")
        if not README.exists() or digest not in README.read_text():
            raise SystemExit("firmware README does not pin the T28 image SHA256")
        action = "checked"
    else:
        OUTPUT.write_bytes(image)
        DOS_OUTPUT.write_bytes(image)
        action = "wrote"
    print(
        f"JUKURAVI-D0-BUFFER-VERIFIED-BUILD: {action} {OUTPUT.name} "
        f"bytes={len(image)} self_crc16={metadata['checksum']:04X} "
        f"sha256={digest}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
