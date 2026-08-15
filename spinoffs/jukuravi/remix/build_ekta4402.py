#!/usr/bin/env python3
"""Build ekta4402, the direct-fastboot successor to frozen ekta4401."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import build_ekta4401 as base


HERE = Path(__file__).resolve().parent
OUTPUT = HERE / "ekta4402.bin"
D15_OUTPUT = HERE / "ekta4402-d15.bin"
D16_OUTPUT = HERE / "ekta4402-d16.bin"
BANNER = b"'EktaSoft&D.Sukharev '26#02"


def build() -> tuple[bytes, dict[str, object]]:
    return base.build(include_direct=True, banner_new=BANNER)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check", action="store_true",
        help="verify that all three committed programming artifacts are current",
    )
    args = parser.parse_args()
    image, metadata = build()
    outputs = (
        (OUTPUT, image),
        (D15_OUTPUT, image[:0x2000]),
        (D16_OUTPUT, image[0x2000:]),
    )
    if args.check:
        for path, expected in outputs:
            if not path.exists() or path.read_bytes() != expected:
                raise SystemExit(
                    f"EKTA4402: committed {path.name} differs from rebuild"
                )
        print(f"EKTA4402-CHECK: PASS {metadata['image_sha256']}")
        return 0
    for path, data in outputs:
        path.write_bytes(data)
    print(json.dumps(metadata, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
