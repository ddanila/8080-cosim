#!/usr/bin/env python3
"""Build the slow repeated D55 timing diagnostic."""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path

from build_d0_cpu import EXPECTED_SIGNATURE
from build_d0_ram_fallback import (
    D55_RECOVERY_NOPS, D55_STRESS_REPETITIONS, ROM_CHECKSUM_END,
    ROM_CHECKSUM_OFFSET, ROM_CHECKSUM_START, build_variant,
)

HERE = Path(__file__).resolve().parent
OUTPUT = HERE / "diag-d0-d55-stress.bin"
README = HERE / "README.md"
IDENTITY = b"JUKURAVI-D0-D55-STRESS-1\0"
ROM_VERSION = 13


def build() -> tuple[bytes, dict[str, int | list[int] | bytes]]:
    image, metadata = build_variant(
        rom_version=ROM_VERSION, identity=IDENTITY, rom_convention=True,
        entry_offset=ROM_CHECKSUM_START, pic_check=True, compact_fallback=True,
        ppi_check=True, pit_check=True, no_serial_fallback=True,
        pit_debug=True, pit_debug_slow=True, pit_debug_d55_stress=True,
    )
    if metadata["pit_debug_checkpoints"] != list(range(1, 5)):
        raise ValueError("D55 stress checkpoint numbering is incomplete")
    if metadata["pit_debug_repetitions"] != D55_STRESS_REPETITIONS:
        raise ValueError("D55 stress repetition count mismatch")
    if metadata["pit_debug_recovery_nops"] != D55_RECOVERY_NOPS:
        raise ValueError("D55 stress recovery spacing mismatch")
    stored = image[ROM_CHECKSUM_OFFSET]
    computed = sum(image[ROM_CHECKSUM_START:ROM_CHECKSUM_END]) & 0xFF
    if stored != computed or stored != metadata["rom_checksum"]:
        raise ValueError("D55 stress block-1 checksum mismatch")
    return image, metadata


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    image, metadata = build()
    digest = hashlib.sha256(image).hexdigest()
    if args.check:
        if not OUTPUT.exists() or OUTPUT.read_bytes() != image:
            raise SystemExit("diag-d0-d55-stress.bin is missing or stale")
        if not README.exists() or digest not in README.read_text():
            raise SystemExit("firmware README does not pin the D55 stress SHA256")
        action = "checked"
    else:
        OUTPUT.write_bytes(image)
        action = "wrote"
    print(
        f"JUKURAVI-D0-D55-STRESS-BUILD: {action} {OUTPUT.name} "
        f"bytes={len(image)} code={metadata['code_size']} "
        f"signature={EXPECTED_SIGNATURE:02X} block1_sum={metadata['rom_checksum']:02X} "
        f"self_crc16={metadata['checksum']:04X} sha256={digest}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
