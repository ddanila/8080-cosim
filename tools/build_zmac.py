#!/usr/bin/env python3
"""Return a reproducible zmac executable, building the pinned source if needed."""

from __future__ import annotations

import os
from pathlib import Path
import subprocess


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "third_party" / "zmac" / "src"


def executable() -> Path:
    override = os.environ.get("ZMAC")
    if override:
        return Path(override)

    result = SOURCE / "zmac"
    if not result.is_file():
        if not (SOURCE / "zmac.y").is_file():
            raise SystemExit(
                "zmac source is absent; run git submodule update --init --recursive"
            )
        subprocess.run(
            ["make", "-C", str(SOURCE), "zmac", "CFLAGS=-std=gnu17"],
            check=True,
        )
    return result


if __name__ == "__main__":
    print(executable())
