#!/usr/bin/env python3
"""Build Jukuravi D0 rung 5a: cumulative RAM paths plus ROM convention check."""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path

from build_d0_cpu import EXPECTED_SIGNATURE
from build_d0_ram_fallback import (
    ROM_CHECKSUM_END,
    ROM_CHECKSUM_OFFSET,
    ROM_CHECKSUM_START,
    build_variant,
)


HERE = Path(__file__).resolve().parent
OUTPUT = HERE / "diag-d0-romcheck.bin"
README = HERE / "README.md"
IDENTITY = b"JUKURAVI-D0-ROMCHECK-1\0"
ROM_VERSION = 4


def build() -> tuple[bytes, dict[str, int | list[int] | bytes]]:
    image, metadata = build_variant(
        rom_version=ROM_VERSION, identity=IDENTITY, rom_convention=True
    )
    stored = image[ROM_CHECKSUM_OFFSET]
    computed = sum(image[ROM_CHECKSUM_START:ROM_CHECKSUM_END]) & 0xFF
    if stored != computed or stored != metadata["rom_checksum"]:
        raise ValueError(
            f"block-1 checksum mismatch: stored={stored:02X} computed={computed:02X}"
        )
    return image, metadata


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--check", action="store_true", help="fail if the committed image is stale"
    )
    args = parser.parse_args()
    image, metadata = build()
    digest = hashlib.sha256(image).hexdigest()
    if args.check:
        if not OUTPUT.exists():
            raise SystemExit(f"missing generated image: {OUTPUT.name}")
        if OUTPUT.read_bytes() != image:
            raise SystemExit("diag-d0-romcheck.bin is stale; run build_d0_romcheck.py")
        if not README.exists() or digest not in README.read_text():
            raise SystemExit("firmware README does not pin the ROM-check SHA256")
        action = "checked"
    else:
        OUTPUT.write_bytes(image)
        action = "wrote"
    print(
        f"JUKURAVI-D0-ROMCHECK-BUILD: {action} {OUTPUT.name} "
        f"bytes={len(image)} code={metadata['code_size']} "
        f"signature={EXPECTED_SIGNATURE:02X} "
        f"block1_sum={metadata['rom_checksum']:02X} "
        f"self_crc16={metadata['checksum']:04X} sha256={digest}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
