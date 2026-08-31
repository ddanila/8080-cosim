#!/usr/bin/env python3
"""Build the strict-8080 three-voice CP/M transient with pinned zmac."""

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


SOURCE = HERE / "three-voice-0100.asm"
OUTPUT = HERE / "three-voice.com"


def build() -> bytes:
    with tempfile.TemporaryDirectory(prefix="jukupoly-three-voice.") as name:
        output = Path(name) / "three-voice.cim"
        subprocess.run(
            [
                str(executable()),
                "--nmnv",
                "--zmac",
                "-8",
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
            raise SystemExit("three-voice.com is missing or stale")
        action = "checked"
    else:
        OUTPUT.write_bytes(image)
        action = "wrote"

    print(f"JUKUPOLY-THREE-VOICE: {action} {OUTPUT.name} bytes={len(image)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
