#!/usr/bin/env python3
"""Distinguish PC/instruction A12 from ordinary loader data addressing."""

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
RESULT_ADDRESS = 0x4100


def run_host(arguments: list[str]) -> None:
    result = subprocess.run([sys.executable, str(HOST), *arguments], cwd=ROOT)
    if result.returncode:
        raise SystemExit(result.returncode)


def marker_program(marker: int) -> bytes:
    # MVI A,marker / STA 4100h / MVI A,marker / RET
    return bytes((0x3E, marker, 0x32, 0x00, 0x41, 0x3E, marker, 0xC9))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", default="/dev/ttyUSB0")
    parser.add_argument("--baud", type=int, default=2400)
    parser.add_argument("--loader-votes", type=int, default=1)
    parser.add_argument(
        "--log-root",
        type=Path,
        default=HERE / "sessions" / "t32-pc-a12-physical",
    )
    args = parser.parse_args()
    args.log_root.mkdir(parents=True, exist_ok=True)

    common = [
        "--port", args.port,
        "--baud", str(args.baud),
        "--attach-loader",
        "--loader-votes", str(args.loader_votes),
        "--timeout", "20",
        "--loader-timeout", "20",
        "--no-nano-reset",
    ]
    with tempfile.TemporaryDirectory(prefix="jukuravi-pc-a12-") as name:
        temp = Path(name)
        for address, marker in ((0x4000, 0x40), (0x5000, 0x50)):
            payload = temp / f"MARK{marker:02X}.BIN"
            payload.write_bytes(marker_program(marker))
            run_host(
                common
                + [
                    "--load", str(payload),
                    "--load-address", f"{address:04X}",
                    "--load-only",
                    "--log-dir", str(args.log_root / f"load-{address:04X}"),
                ]
            )

        run_logs = args.log_root / "call-5000"
        run_host(
            common
            + [
                "--run-address", "5000",
                "--run-mode", "call",
                "--result-address", f"{RESULT_ADDRESS:04X}",
                "--result-length", "1",
                "--log-dir", str(run_logs),
            ]
        )

    summaries = list(run_logs.glob("*.json"))
    if not summaries:
        raise SystemExit("T32-PC-A12: no CALL summary")
    summary = json.loads(max(summaries, key=lambda path: path.stat().st_mtime_ns).read_text())
    run = summary.get("loader", {}).get("run", {})
    observed = run.get("result", {}).get("hex")
    returned_a = run.get("return_a")
    if observed == "50" and returned_a == "0x50":
        print("T32-PC-A12: PASS address 5000h executed marker 50h")
        return 0
    if observed == "40" and returned_a == "0x40":
        print("T32-PC-A12: ALIAS address 5000h executed 4000h marker 40h")
        return 1
    print(f"T32-PC-A12: INDETERMINATE marker={observed!r} A={returned_a!r}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
