#!/usr/bin/env python3
"""Run the direct D1 16-bit increment probe through the resident T32 loader."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
HOST = HERE / "host.py"
SOURCE = HERE / "firmware" / "ram-a12-increment-registers-4000.asm"
RESULT_ADDRESS = 0x4D00
RESULT_BYTES = 24


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", default="/dev/ttyUSB0")
    parser.add_argument("--baud", type=int, default=2400)
    parser.add_argument("--loader-votes", type=int, default=1)
    parser.add_argument(
        "--attach-loader",
        action="store_true",
        help="attach to an already-running loader instead of handling a fresh T32 boot",
    )
    parser.add_argument(
        "--log-dir",
        type=Path,
        default=HERE / "sessions" / "t32-ram-a12-increment-registers-physical",
    )
    args = parser.parse_args()
    args.log_dir.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="jukuravi-a12-increment-") as name:
        image = Path(name) / "A12INCR.BIN"
        subprocess.run(
            ["nasm", "-f", "bin", "-o", str(image), str(SOURCE)],
            cwd=ROOT,
            check=True,
        )
        command = [
                sys.executable, str(HOST),
                "--port", args.port,
                "--baud", str(args.baud),
                "--timeout", "60",
                "--loader-votes", str(args.loader_votes),
                "--loader-timeout", "30",
                "--no-nano-reset",
                "--load", str(image),
                "--load-address", "4000",
                "--run-address", "4000",
                "--run-mode", "call",
                "--result-address", f"{RESULT_ADDRESS:04X}",
                "--result-length", str(RESULT_BYTES),
                "--log-dir", str(args.log_dir),
            ]
        if args.attach_loader:
            command.append("--attach-loader")
        else:
            command.extend((
                "--expect-rom-version", "1B",
                "--expect-crc16", "D62B",
            ))
        completed = subprocess.run(
            command,
            cwd=ROOT,
        )
        if completed.returncode:
            return completed.returncode

    summaries = list(args.log_dir.glob("*.json"))
    if not summaries:
        raise SystemExit("JUKURAVI-A12-INCREMENT: no session summary")
    summary = json.loads(max(summaries, key=lambda p: p.stat().st_mtime_ns).read_text())
    result_hex = summary.get("loader", {}).get("run", {}).get("result", {}).get("hex")
    if not isinstance(result_hex, str):
        raise SystemExit("JUKURAVI-A12-INCREMENT: result block is missing")
    result = bytes.fromhex(result_hex)
    if len(result) != RESULT_BYTES or result[:5] != b"X12C\xA5":
        raise SystemExit(f"JUKURAVI-A12-INCREMENT: malformed {result.hex().upper()}")

    words = tuple(result[offset] | (result[offset + 1] << 8)
                  for offset in range(8, 18, 2))
    clean = (0x1000, 0x1A01, 0x5A01, 0x9A01, 0x1A01)
    fitted_fault = (0x1000, 0x0A01, 0x4A01, 0x8A01, 0x1A01)
    rendered = " ".join(f"{word:04X}" for word in words)
    if words == fitted_fault:
        print(f"JUKURAVI-A12-INCREMENT: D1 FAULT CONFIRMED ({rendered})")
        return 0
    if words == clean:
        print(f"JUKURAVI-A12-INCREMENT: CLEAN ({rendered})")
        return 0
    print(f"JUKURAVI-A12-INCREMENT: OTHER ({rendered})")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
