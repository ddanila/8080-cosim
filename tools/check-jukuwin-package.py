#!/usr/bin/env python3
"""Verify the exact self-contained JUKUWIN release-folder contract."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


EXPECTED = {
    "JUKUWIN.EXE", "JUKUWIN.INI", "MANIFEST.json", "README.md",
    "SHA256SUMS",
}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fail(message: str) -> None:
    raise SystemExit(f"check-jukuwin-package: {message}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("directory", type=Path)
    args = parser.parse_args()
    actual = {item.name for item in args.directory.iterdir()}
    if actual != EXPECTED:
        fail("folder members differ: " + ", ".join(sorted(actual)))

    sums: dict[str, str] = {}
    for line in (args.directory / "SHA256SUMS").read_text("ascii").splitlines():
        parts = line.split("  ", 1)
        if len(parts) != 2 or parts[1] in sums:
            fail("malformed SHA256SUMS")
        sums[parts[1]] = parts[0]
    expected_sums = EXPECTED - {"SHA256SUMS"}
    if set(sums) != expected_sums:
        fail("SHA256SUMS membership differs")
    for name, expected in sums.items():
        if digest(args.directory / name) != expected:
            fail(f"hash mismatch for {name}")

    manifest = json.loads((args.directory / "MANIFEST.json").read_text("ascii"))
    executable = args.directory / "JUKUWIN.EXE"
    if manifest.get("schema") != "jukuwin-package-v1":
        fail("manifest schema differs")
    identity = manifest.get("executable", {})
    if identity.get("file") != executable.name:
        fail("manifest executable name differs")
    if identity.get("bytes") != executable.stat().st_size:
        fail("manifest executable size differs")
    if identity.get("sha256") != digest(executable):
        fail("manifest executable hash differs")
    payloads = manifest.get("embedded_payloads", [])
    if len(payloads) != 6 or {item.get("mode") for item in payloads} != {
        "stock", "c11", "c12"
    }:
        fail("manifest embedded payload catalog differs")

    print(
        "JUKUWIN-PACKAGE-CHECK: PASS "
        f"(5 files, 6 embedded payloads, EXE {executable.stat().st_size} bytes)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
