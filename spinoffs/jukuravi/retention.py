#!/usr/bin/env python3
"""Characterize Juku RAM retention through an already-running loader v2."""

from __future__ import annotations

import argparse
import os
import sys
import time
from pathlib import Path

import host

HERE = Path(__file__).resolve().parent
DEFAULT_LOG_DIR = HERE / "sessions" / "retention"
MARKER = bytes.fromhex(
    "00FF55AA966969963CC3C33C0FF0F00F"
    "0123456789ABCDEFFEDCBA9876543210"
)


def parse_ages(value: str) -> tuple[float, ...]:
    try:
        ages = tuple(float(item.strip()) for item in value.split(",") if item.strip())
    except ValueError as error:
        raise argparse.ArgumentTypeError("ages must be comma-separated seconds") from error
    if not ages or any(age < 0 for age in ages) or tuple(sorted(ages)) != ages:
        raise argparse.ArgumentTypeError("ages must be nonnegative and ascending")
    return ages


def make_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="write and repeatedly read one RAM marker in a live loader"
    )
    parser.add_argument("--port", default="/dev/ttyUSB0")
    parser.add_argument("--baud", type=int, default=host.DEFAULT_BAUD)
    parser.add_argument("--address", type=host.parse_hex16, default=0x4D00)
    parser.add_argument("--ages", type=parse_ages, default=(0.0, 1.0, 2.0, 4.0, 8.0, 16.0))
    parser.add_argument("--loader-timeout", type=float, default=host.DEFAULT_LOADER_TIMEOUT)
    parser.add_argument(
        "--loader-guard-ms",
        type=host.parse_nonnegative_float,
        default=host.SOLICITED_RESPONSE_GUARD_SECONDS * 1000.0,
    )
    parser.add_argument("--log-dir", type=Path, default=DEFAULT_LOG_DIR)
    parser.add_argument(
        "--cold",
        action="store_true",
        help="wait for a fresh exact T34 boot instead of attaching to a live loader",
    )
    return parser


def main() -> int:
    args = make_parser().parse_args()
    if args.address < 0x4000 or args.address + len(MARKER) > 0xC000:
        print("JUKURAVI-RETENTION: marker must fit 4000h..BFFFh", file=sys.stderr)
        return 2
    try:
        fd, transport = host.open_transport(args.port, None, args.baud)
    except host.SessionError as error:
        print(f"JUKURAVI-RETENTION: ERROR {error}", file=sys.stderr)
        return 1

    logs = host.SessionLogs(args.log_dir, transport)
    session = host.HostSession(
        fd,
        logs,
        600.0,
        600.0,
        0x1C if args.cold else None,
        0xA637 if args.cold else None,
        False,
        args.loader_guard_ms / 1000.0,
        None,
        3,
        1,
        False,
        True,
        "call",
        None,
        0,
        None,
        0,
        1,
        True,
    )
    samples: list[dict[str, object]] = []
    error_text: str | None = None
    interrupted = False
    try:
        session.begin_attempt(1)
        if args.cold:
            print(
                f"JUKURAVI-RETENTION: listening on {transport} at {args.baud}; "
                "press RESET once",
                flush=True,
            )
            session.run()
            session.run_loader(
                MARKER,
                "<retention-marker>",
                args.address,
                None,
                args.loader_timeout,
            )
        else:
            session.attach_loader_v2(
                MARKER,
                "<retention-marker>",
                args.address,
                None,
                args.loader_timeout,
            )
        written = time.monotonic()
        print(
            f"JUKURAVI-RETENTION: marker verified address=0x{args.address:04X} "
            f"bytes={len(MARKER)}",
            flush=True,
        )
        for target_age in args.ages:
            remaining = target_age - (time.monotonic() - written)
            if remaining > 0:
                time.sleep(remaining)
            operation = session.run_resident_loader_v2(
                b"",
                f"<retention-read:{target_age:g}s>",
                0x4000,
                None,
                args.loader_timeout,
                control_read_address=args.address,
                control_read_length=len(MARKER),
            )
            observed = bytes.fromhex(str(operation["control_read"]["hex"]))
            age = time.monotonic() - written
            differences = [
                index for index, (expected, got) in enumerate(zip(MARKER, observed))
                if expected != got
            ]
            sample = {
                "target_age_seconds": target_age,
                "observed_age_seconds": round(age, 6),
                "verdict": "pass" if not differences else "fail",
                "differing_bytes": differences,
                "expected_hex": MARKER.hex().upper(),
                "observed_hex": observed.hex().upper(),
                "operation": operation,
            }
            samples.append(sample)
            print(
                f"JUKURAVI-RETENTION: age={age:.3f}s "
                f"{'PASS' if not differences else 'FAIL'} "
                f"differing_bytes={len(differences)}",
                flush=True,
            )
        session.finish_attempt("ok")
    except KeyboardInterrupt:
        interrupted = True
        error_text = "interrupted by operator"
        if session._attempt_number is not None:
            session.finish_attempt("error", error_text)
    except (host.SessionError, OSError) as error:
        error_text = str(error)
        if session._attempt_number is not None:
            session.finish_attempt("error", error_text)
    finally:
        os.close(fd)

    summary = session.summary("error" if error_text else "ok", error_text)
    summary["retention"] = {
        "address": f"0x{args.address:04X}",
        "marker_hex": MARKER.hex().upper(),
        "samples": samples,
    }
    logs.finish(summary)
    if interrupted:
        print(f"JUKURAVI-RETENTION: INTERRUPTED; logs {logs.json_path}", file=sys.stderr)
    elif error_text:
        print(f"JUKURAVI-RETENTION: ERROR {error_text}", file=sys.stderr)
    print(f"JUKURAVI-RETENTION: logs {logs.json_path}", flush=True)
    if interrupted:
        return 130
    return 1 if error_text or any(item["verdict"] == "fail" for item in samples) else 0


if __name__ == "__main__":
    raise SystemExit(main())
