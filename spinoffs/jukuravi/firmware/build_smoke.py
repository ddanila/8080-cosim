#!/usr/bin/env python3
"""Build the shared-mnemonic T31 speaker demo with zmac in 8080 mode."""

from __future__ import annotations

import argparse
import subprocess
import sys
import tempfile
from pathlib import Path


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT / "tools"))
from build_zmac import executable  # noqa: E402


SOURCE = HERE / "smoke-4000.asm"
COMMON = ROOT / "third_party" / "juku-common" / "music"
OUTPUT = HERE / "smoke-4000.bin"


def build() -> bytes:
    with tempfile.TemporaryDirectory(prefix="jukuravi-smoke.") as name:
        output = Path(name) / "smoke-4000.cim"
        subprocess.run(
            [
                str(executable()),
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
            raise SystemExit("smoke-4000.bin is missing or stale")
        action = "checked"
    else:
        OUTPUT.write_bytes(image)
        action = "wrote"

    print(f"JUKURAVI-SMOKE: {action} {OUTPUT.name} bytes={len(image)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
