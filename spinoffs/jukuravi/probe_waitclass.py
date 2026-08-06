#!/usr/bin/env python3
"""Exercise and identify every T32 upper-ROM wait-class entry."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import host


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
HOST = HERE / "host.py"
FIRMWARE = HERE / "firmware"
sys.path.insert(0, str(FIRMWARE))
import build_d0_waitclass as firmware  # noqa: E402


PREMARKER = 0xD5


def hex_address(value: str) -> int:
    try:
        return int(value, 16)
    except ValueError as error:
        raise argparse.ArgumentTypeError(f"invalid hexadecimal address: {value}") from error


def run_host(arguments: list[str]) -> None:
    command = [sys.executable, str(HOST), *arguments]
    result = subprocess.run(command, cwd=ROOT)
    if result.returncode:
        raise SystemExit(result.returncode)


def newest_summary(directory: Path) -> dict[str, object]:
    summaries = list(directory.glob("*.json"))
    if not summaries:
        raise SystemExit(f"no session summary in {directory}")
    return json.loads(max(summaries, key=lambda path: path.stat().st_mtime_ns).read_text())


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--port",
        help="serial device; defaults to the first detected USB adapter",
    )
    parser.add_argument("--baud", type=int, default=2400)
    parser.add_argument("--loader-votes", type=int, default=1)
    parser.add_argument(
        "--jump-address",
        type=hex_address,
        default=0x4000,
        help="RAM address for the three-byte JMP trampoline (default: 4000)",
    )
    parser.add_argument(
        "--post-jump-seconds",
        type=float,
        default=1.0,
        help="quiet time before loader reattachment (default: 1.0)",
    )
    parser.add_argument(
        "--target",
        action="append",
        type=hex_address,
        help="upper-ROM entry in hexadecimal; repeat as needed (default: all)",
    )
    parser.add_argument(
        "--log-root",
        type=Path,
        default=HERE / "sessions" / "t32-waitclass-physical",
    )
    args = parser.parse_args()
    try:
        args.port, autodetected = host.resolve_serial_port(args.port)
    except host.SessionError as error:
        raise SystemExit(f"JUKURAVI-WAITCLASS: {error}") from error
    if autodetected:
        print(f"JUKURAVI-WAITCLASS: using {args.port}")

    targets = list(firmware.TRAMPOLINES)
    if args.target:
        unknown = [target for target in args.target if target not in firmware.TRAMPOLINES]
        if unknown:
            parser.error(
                "unsupported target(s): "
                + ", ".join(f"{target:04X}h" for target in unknown)
            )
        targets = args.target
    if not 0x4000 <= args.jump_address <= 0xBFFD:
        parser.error("--jump-address must fit a three-byte JMP in 4000h..BFFFh")
    if args.post_jump_seconds < 0:
        parser.error("--post-jump-seconds cannot be negative")

    common = [
        "--port", args.port,
        "--baud", str(args.baud),
        "--attach-loader",
        "--timeout", "20",
        "--loader-timeout", "20",
        "--loader-votes", str(args.loader_votes),
        "--no-nano-reset",
    ]
    args.log_root.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="jukuravi-t32-probe-") as name:
        probe = Path(name) / "JUMP.BIN"
        for target in targets:
            description = firmware.TRAMPOLINES[target]
            print(f"T32-PROBE: {target:04X}h {description}", flush=True)
            probe.write_bytes(
                bytes(
                    (
                        0x3E, PREMARKER,
                        0x32, firmware.RESULT_ADDRESS & 0xFF,
                        firmware.RESULT_ADDRESS >> 8,
                        0xC3, target & 0xFF, target >> 8,
                    )
                )
            )
            jump_logs = args.log_root / f"{target:04X}-jump"
            marker_logs = args.log_root / f"{target:04X}-marker"
            run_host(
                common
                + [
                    "--load", str(probe),
                    "--load-address", f"{args.jump_address:04X}",
                    "--run-address", f"{args.jump_address:04X}",
                    "--run-mode", "jump",
                    "--log-dir", str(jump_logs),
                ]
            )
            time.sleep(args.post_jump_seconds)
            run_host(
                common
                + [
                    "--probe-loader",
                    "--read-address", f"{firmware.RESULT_ADDRESS:04X}",
                    "--read-length", "1",
                    "--log-dir", str(marker_logs),
                ]
            )
            summary = newest_summary(marker_logs)
            observed = (
                summary.get("loader", {})
                .get("control_read", {})
                .get("hex")
            )
            expected = f"{target >> 8:02X}"
            if observed != expected:
                detail = (
                    "; RAM trampoline ran, upper-ROM marker did not"
                    if observed == f"{PREMARKER:02X}"
                    else ""
                )
                raise SystemExit(
                    f"T32-PROBE: FAIL {target:04X}h expected marker "
                    f"{expected}, observed {observed!r}{detail}"
                )
            print(f"T32-PROBE: {target:04X}h PASS marker={observed}", flush=True)

    print(f"T32-PROBE: PASS ({len(targets)} upper-ROM entries)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
