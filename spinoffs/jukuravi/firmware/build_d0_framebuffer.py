#!/usr/bin/env python3
"""Build Jukuravi D0 rung 5e: surveyed-RAM framebuffer test pattern."""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path

from build_d0_cpu import EXPECTED_SIGNATURE
from build_d0_ram_fallback import (
    FRAMEBUFFER_BASE,
    FRAMEBUFFER_BYTES,
    FRAMEBUFFER_END,
    ROM_CHECKSUM_END,
    ROM_CHECKSUM_OFFSET,
    ROM_CHECKSUM_START,
    build_variant,
)


HERE = Path(__file__).resolve().parent
OUTPUT = HERE / "diag-d0-framebuffer.bin"
README = HERE / "README.md"
IDENTITY = b"JUKURAVI-D0-FRAMEBUFFER-1\0"
ROM_VERSION = 8
ENTRY_OFFSET = ROM_CHECKSUM_START


def build() -> tuple[bytes, dict[str, int | list[int] | bytes]]:
    image, metadata = build_variant(
        rom_version=ROM_VERSION,
        identity=IDENTITY,
        rom_convention=True,
        entry_offset=ENTRY_OFFSET,
        pic_check=True,
        compact_fallback=True,
        ppi_check=True,
        pit_check=True,
        framebuffer_pattern=True,
    )
    stored = image[ROM_CHECKSUM_OFFSET]
    computed = sum(image[ROM_CHECKSUM_START:ROM_CHECKSUM_END]) & 0xFF
    if stored != computed or stored != metadata["rom_checksum"]:
        raise ValueError(
            f"block-1 checksum mismatch: stored={stored:02X} computed={computed:02X}"
        )
    pit_start = int(metadata["pit_extension_start"])
    pit_end = int(metadata["pit_extension_end"])
    framebuffer_start = int(metadata["framebuffer_extension_start"])
    framebuffer_end = int(metadata["framebuffer_extension_end"])
    if (
        metadata["banner_offset"] != ROM_CHECKSUM_END
        or pit_start != metadata["ack_offset"] + 9
        or pit_end - pit_start != 0x100
        or framebuffer_start != pit_end
        or framebuffer_end - framebuffer_start > 0xFF
        or metadata["framebuffer_base"] != FRAMEBUFFER_BASE
        or metadata["framebuffer_end"] != FRAMEBUFFER_END
        or metadata["framebuffer_bytes"] != FRAMEBUFFER_BYTES
    ):
        raise ValueError("guarded framebuffer layout is incomplete")
    if sum(image[pit_start:pit_end]) & 0xFF != metadata["pit_extension_checksum"]:
        raise ValueError("PIT extension additive checksum mismatch")
    if (
        sum(image[framebuffer_start:framebuffer_end]) & 0xFF
        != metadata["framebuffer_extension_checksum"]
    ):
        raise ValueError("framebuffer extension additive checksum mismatch")
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
            raise SystemExit("diag-d0-framebuffer.bin is stale; run build_d0_framebuffer.py")
        if not README.exists() or digest not in README.read_text():
            raise SystemExit("firmware README does not pin the framebuffer image SHA256")
        action = "checked"
    else:
        OUTPUT.write_bytes(image)
        action = "wrote"
    print(
        f"JUKURAVI-D0-FRAMEBUFFER-BUILD: {action} {OUTPUT.name} "
        f"bytes={len(image)} code={metadata['code_size']} "
        f"signature={EXPECTED_SIGNATURE:02X} "
        f"block1_sum={metadata['rom_checksum']:02X} "
        f"pit_sum={metadata['pit_extension_checksum']:02X} "
        f"framebuffer_sum={metadata['framebuffer_extension_checksum']:02X} "
        f"self_crc16={metadata['checksum']:04X} sha256={digest}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
