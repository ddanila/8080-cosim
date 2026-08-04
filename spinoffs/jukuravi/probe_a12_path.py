#!/usr/bin/env python3
"""Distinguish a D15-local A12 fault from the shared D1/D4/BA12 path."""

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
PAIR_SOURCE = HERE / "firmware" / "rom-read-pair-4000.asm"
RESULT_ADDRESS = 0x4100
RESULT_BYTES = 42
LOWER_ADDRESS = 0x4A00
UPPER_ADDRESS = 0x5A00
LOWER_PAIR = bytes((0x11, 0x22))
UPPER_PAIR = bytes((0xAA, 0xBB))


def run_host(common: list[str], arguments: list[str]) -> None:
    result = subprocess.run(
        [sys.executable, str(HOST), *common, *arguments], cwd=ROOT
    )
    if result.returncode:
        raise SystemExit(result.returncode)


def newest_summary(directory: Path) -> dict[str, object]:
    summaries = list(directory.glob("*.json"))
    if not summaries:
        raise SystemExit(f"no session summary in {directory}")
    newest = max(summaries, key=lambda path: path.stat().st_mtime_ns)
    return json.loads(newest.read_text())


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", default="/dev/ttyUSB0")
    parser.add_argument("--baud", type=int, default=2400)
    parser.add_argument("--loader-votes", type=int, default=1)
    parser.add_argument(
        "--log-root",
        type=Path,
        default=HERE / "sessions" / "t32-a12-path-physical",
    )
    args = parser.parse_args()

    common = [
        "--port", args.port,
        "--baud", str(args.baud),
        "--attach-loader",
        "--loader-timeout", "30",
        "--loader-votes", str(args.loader_votes),
        "--no-nano-reset",
    ]
    args.log_root.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="jukuravi-a12-path-") as name:
        temp = Path(name)
        lower = temp / "LOWER.BIN"
        upper = temp / "UPPER.BIN"
        probe = temp / "PAIR.BIN"
        lower.write_bytes(LOWER_PAIR)
        upper.write_bytes(UPPER_PAIR)
        subprocess.run(
            [
                "nasm", "-f", "bin",
                "-DTARGET=0x5A00",
                "-DEXPECTED0=0xAA",
                "-DEXPECTED1=0xBB",
                "-o", str(probe),
                str(PAIR_SOURCE),
            ],
            cwd=ROOT,
            check=True,
        )

        for label, payload, address in (
            ("lower", lower, LOWER_ADDRESS),
            ("upper", upper, UPPER_ADDRESS),
        ):
            run_host(
                common,
                [
                    "--load", str(payload),
                    "--load-address", f"{address:04X}",
                    "--load-only",
                    "--log-dir", str(args.log_root / label),
                ],
            )

        result_logs = args.log_root / "pair"
        run_host(
            common,
            [
                "--load", str(probe),
                "--load-address", "4000",
                "--run-address", "4000",
                "--run-mode", "call",
                "--result-address", f"{RESULT_ADDRESS:04X}",
                "--result-length", str(RESULT_BYTES),
                "--log-dir", str(result_logs),
            ],
        )

    summary = newest_summary(result_logs)
    result_hex = (
        summary.get("loader", {})
        .get("run", {})
        .get("result", {})
        .get("hex")
    )
    if not isinstance(result_hex, str):
        raise SystemExit("JUKURAVI-A12-PATH: result block is missing")
    result = bytes.fromhex(result_hex)
    expected_header = b"PAIR" + bytes((0x5A, 0x00, 0xAA, 0xBB, 16, 0xA5))
    if result[:10] != expected_header or len(result) != RESULT_BYTES:
        raise SystemExit(
            f"JUKURAVI-A12-PATH: malformed result {result.hex().upper()}"
        )
    pairs = [result[offset:offset + 2] for offset in range(10, 42, 2)]
    unique = sorted(set(pairs))
    if unique == [UPPER_PAIR]:
        print(
            "JUKURAVI-A12-PATH: D15-LOCAL "
            "(all 16 RAM pairs AA BB; shared D1/D4/BA12 path passes)"
        )
        return 0
    mixed = bytes((UPPER_PAIR[0], LOWER_PAIR[1]))
    if unique == [mixed]:
        print(
            "JUKURAVI-A12-PATH: SHARED-A12 "
            "(all 16 RAM pairs AA 22; inspect D1.37, D4.5/.15, and BA12)"
        )
        return 0
    print(
        "JUKURAVI-A12-PATH: OTHER "
        + ",".join(pair.hex().upper() for pair in unique)
    )
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
