#!/usr/bin/env python3
"""Build T31 with every executed ROM byte below the suspect 1000h boundary."""

from __future__ import annotations

import argparse
import hashlib

import build_d0_resilient as base
from build_d5_loader_v5 import emit_loader as emit_loader_v5


OUTPUT = base.HERE / "diag-d0-low4k.bin"
DOS_OUTPUT = base.HERE / "dos" / "T31HOST.BIN"
README = base.HERE / "README.md"
ROM_VERSION = 0x1A
IDENTITY = b"JUKURAVI-D0-LOW4K-MONITOR-2400-1\0"
LOADER_EMITTER = emit_loader_v5
LOADER_SYMBOL_REPETITIONS = 7


def build():
    saved = (
        base.ROM_VERSION,
        base.IDENTITY,
        base.SOLICITED_INPUT,
        base.FILTER_INVALID_SYMBOLS,
        base.CLEAR_INVALID_ERRORS,
        base.VERIFY_BUFFER_STORES,
        base.LOADER_EMITTER,
        base.LOADER_SYMBOL_REPETITIONS,
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
        base.LOADER_EMITTER = LOADER_EMITTER
        base.LOADER_SYMBOL_REPETITIONS = LOADER_SYMBOL_REPETITIONS
        base.LOADER_WORKSPACE_BASE = 0xC000
        base.LOADER_WORKSPACE_BYTES = 0x1000
        base.POSTDIAG_PROGRESS_MARKERS = None
        base.REQUIRE_BANNER_TX_EMPTY = True
        base.REQUIRE_FINAL_TX_EMPTY = False
        base.DIRECT_LOADER_HANDOFF = True
        image, metadata = base.build()
        if int(metadata["loader_extension_end"]) > 0x1000:
            raise ValueError("T31 loader crosses the 1000h execution boundary")
        return image, metadata
    finally:
        (
            base.ROM_VERSION,
            base.IDENTITY,
            base.SOLICITED_INPUT,
            base.FILTER_INVALID_SYMBOLS,
            base.CLEAR_INVALID_ERRORS,
            base.VERIFY_BUFFER_STORES,
            base.LOADER_EMITTER,
            base.LOADER_SYMBOL_REPETITIONS,
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
            raise SystemExit("firmware README does not pin the T31 image SHA256")
        action = "checked"
    else:
        OUTPUT.write_bytes(image)
        DOS_OUTPUT.write_bytes(image)
        action = "wrote"
    print(
        f"JUKURAVI-D0-LOW4K-BUILD: {action} {OUTPUT.name} "
        f"bytes={len(image)} loader_end={int(metadata['loader_extension_end']):04X} "
        f"self_crc16={metadata['checksum']:04X} sha256={digest}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
