#!/usr/bin/env python3
"""Build the loader-callable diagnostic backed by juku-common."""

from __future__ import annotations

import argparse
import os
import subprocess
import tempfile
from pathlib import Path


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
SOURCE = HERE / "shared-memory-4000.asm"
COMMON = ROOT / "third_party" / "juku-common" / "diag"
OUTPUT = HERE / "shared-memory-4000.bin"


def build() -> bytes:
    zmac = os.environ.get("ZMAC", "zmac")
    with tempfile.TemporaryDirectory(prefix="jukuravi-shared-diag.") as name:
        output = Path(name) / "shared-memory-4000.cim"
        subprocess.run(
            [
                zmac,
                "--nmnv",
                "--zmac",
                "-8",
                f"-I{COMMON}",
                "-o",
                str(output),
                str(SOURCE),
            ],
            check=True,
        )
        return output.read_bytes()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--check", action="store_true", help="fail if the committed image is stale"
    )
    args = parser.parse_args()
    image = build()

    if args.check:
        if not OUTPUT.exists() or OUTPUT.read_bytes() != image:
            raise SystemExit("shared-memory-4000.bin is missing or stale")
        action = "checked"
    else:
        OUTPUT.write_bytes(image)
        action = "wrote"

    print(f"JUKURAVI-SHARED-DIAG: {action} {OUTPUT.name} bytes={len(image)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
