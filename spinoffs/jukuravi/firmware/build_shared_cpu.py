#!/usr/bin/env python3
"""Build the loader-callable shared CPU diagnostic."""

from __future__ import annotations

import argparse
from pathlib import Path

from build_shared_memory import build_source


HERE = Path(__file__).resolve().parent
SOURCE = HERE / "shared-cpu-4000.asm"
OUTPUT = HERE / "shared-cpu-4000.bin"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--check", action="store_true", help="fail if the committed image is stale"
    )
    args = parser.parse_args()
    image = build_source(SOURCE)

    if args.check:
        if not OUTPUT.exists() or OUTPUT.read_bytes() != image:
            raise SystemExit("shared-cpu-4000.bin is missing or stale")
        action = "checked"
    else:
        OUTPUT.write_bytes(image)
        action = "wrote"

    print(f"JUKURAVI-SHARED-CPU: {action} {OUTPUT.name} bytes={len(image)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
