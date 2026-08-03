#!/usr/bin/env python3
"""Build T30 without runtime dependence on the real board's TxEMPTY bit."""

from __future__ import annotations

import argparse
import hashlib

import build_d0_resilient as base
from build_d4_loader_v4 import emit_loader as emit_loader_v4


OUTPUT = base.HERE / "diag-d0-txready.bin"
DOS_OUTPUT = base.HERE / "dos" / "T30HOST.BIN"
README = base.HERE / "README.md"
ROM_VERSION = 0x19
IDENTITY = b"JUKURAVI-D0-TXREADY-ONLY-2400-1\0"
PROGRESS_MARKERS = (0xE0, 0xE1, 0xE2)


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
        base.POSTDIAG_PROGRESS_MARKERS,
        base.REQUIRE_BANNER_TX_EMPTY,
        base.REQUIRE_FINAL_TX_EMPTY,
        base.DIRECT_LOADER_HANDOFF,
    )
    try:
        base.ROM_VERSION = ROM_VERSION
        base.IDENTITY = IDENTITY
        base.SOLICITED_INPUT = True
        base.FILTER_INVALID_SYMBOLS = True
        base.CLEAR_INVALID_ERRORS = True
        base.VERIFY_BUFFER_STORES = True
        base.LOADER_EMITTER = emit_loader_v4
        base.LOADER_WORKSPACE_BASE = 0xC000
        base.LOADER_WORKSPACE_BYTES = 0x1000
        base.POSTDIAG_PROGRESS_MARKERS = PROGRESS_MARKERS
        base.REQUIRE_BANNER_TX_EMPTY = True
        base.REQUIRE_FINAL_TX_EMPTY = False
        base.DIRECT_LOADER_HANDOFF = False
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
            base.POSTDIAG_PROGRESS_MARKERS,
            base.REQUIRE_BANNER_TX_EMPTY,
            base.REQUIRE_FINAL_TX_EMPTY,
            base.DIRECT_LOADER_HANDOFF,
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
            raise SystemExit("firmware README does not pin the T30 image SHA256")
        action = "checked"
    else:
        OUTPUT.write_bytes(image)
        DOS_OUTPUT.write_bytes(image)
        action = "wrote"
    print(
        f"JUKURAVI-D0-TXREADY-BUILD: {action} {OUTPUT.name} "
        f"bytes={len(image)} self_crc16={metadata['checksum']:04X} "
        f"sha256={digest}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
