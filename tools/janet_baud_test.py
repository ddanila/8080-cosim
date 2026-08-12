#!/usr/bin/env python3
"""Load BAUDTEST.COM over a live 9600 disk and sweep a raw rate both ways."""

from __future__ import annotations

import argparse
import json
import os
import select
import termios
import time
from pathlib import Path

from janet_disk_server import checksum, serve_disk
from janet_netboot import configure_serial, serve as serve_boot, write_all


def write_result(path: Path | None, result: dict[str, object]) -> None:
    if path:
        path.write_text(json.dumps(result, indent=2) + "\n")
        print(f"Result written to {path}", flush=True)


def read_exact(fd: int, size: int, timeout: float) -> bytes:
    result = bytearray()
    deadline = time.monotonic() + timeout
    while len(result) < size and time.monotonic() < deadline:
        ready, _, _ = select.select([fd], [], [], 0.1)
        if ready:
            result.extend(os.read(fd, size - len(result)))
    if len(result) != size:
        raise TimeoutError(f"received {len(result)}/{size} bytes")
    return bytes(result)


CASES = (
    # Eight unpaced bursts locate the clean receive envelope; the final
    # long paced control distinguishes throughput from framing/rate trouble.
    (1, 0.0),
    (2, 0.0),
    (4, 0.0),
    (8, 0.0),
    (16, 0.0),
    (32, 0.0),
    (64, 0.0),
    (133, 0.0),
    (133, 0.75),
    (133, 1.25),
    (133, 2.0),
)


def send_case(
    fd: int, case: int, length: int, delay_ms: float, *, drain: bool,
) -> None:
    payload = bytes(range(length))
    body = bytes((0xA5, case, length)) + payload
    packet = body + bytes((checksum(body),))
    truncate = os.environ.get("JUKU_BAUDTEST_TRUNCATE_CASE") == str(case)
    if truncate:
        packet = packet[:-1]
    if delay_ms:
        for value in packet:
            write_all(fd, bytes((value,)))
            if drain:
                # A sleep between write(2) calls does not prove a wire gap:
                # USB-serial drivers may queue those bytes into one device
                # burst. Drain the CP2102 before starting the requested gap.
                termios.tcdrain(fd)
            time.sleep(delay_ms / 1000.0)
    else:
        write_all(fd, packet)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("serial")
    parser.add_argument("system", type=Path)
    parser.add_argument("volume", type=Path)
    parser.add_argument("--test-baud", type=int, default=19200)
    parser.add_argument(
        "--test-parity", choices=("odd", "none"), default="odd",
        help="framing for the raw test phase only (default: odd)",
    )
    parser.add_argument("--client", type=lambda value: int(value, 0), default=1)
    parser.add_argument("--server", type=lambda value: int(value, 0), default=2)
    parser.add_argument("--result", type=Path,
                        help="write the packet result as JSON before resuming A:")
    parser.add_argument("--no-resume", action="store_true",
                        help="exit after restoring 9600 instead of serving A:")
    parser.add_argument("--no-termios", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args()
    volume = bytearray(args.volume.read_bytes())
    if args.serial.startswith("fd:"):
        fd = os.dup(int(args.serial.removeprefix("fd:"), 0))
        os.set_blocking(fd, False)
    else:
        fd = os.open(args.serial, os.O_RDWR | os.O_NOCTTY | os.O_NONBLOCK)
    try:
        if not args.no_termios:
            configure_serial(fd, 9600)
        print("Booting automatic BAUDTEST system at 9600", flush=True)
        serve_boot(
            fd, args.system.read_bytes(), client=args.client, server=args.server,
            timeout=600,
        )
        if not args.no_termios:
            configure_serial(fd, 9600)
        print("Serving A:; BAUDTEST auto-starts after boot", flush=True)
        serve_disk(
            fd,
            volume,
            timeout=600,
            stop_marker=b"B96!",
            resume=False,
            reply_guard=0.010,
            tx_byte_delay=0.001,
        )

        if not args.no_termios:
            configure_serial(fd, args.test_baud, parity=args.test_parity)
        # BAUDTEST switches only after B96!, then announces BRD! at the test
        # rate. Waiting for that marker avoids racing its bounded Rx loop.
        ready = read_exact(fd, 4, 10)
        if ready != b"BRD!":
            raise ValueError(f"bad test-rate ready marker: {ready!r}")
        framing = f"8{'O' if args.test_parity == 'odd' else 'N'}1"
        print(
            f"{args.test_baud}/{framing} ready marker received", flush=True,
        )
        reports: list[dict[str, object]] = []
        for case, (length, delay_ms) in enumerate(CASES):
            ready = read_exact(fd, 2, 5)
            expected_ready = bytes((ord("C"), case))
            if ready != expected_ready:
                raise ValueError(
                    f"bad case-ready marker: {ready!r}, "
                    f"expected {expected_ready!r}"
                )
            # The marker has completely traversed the wire before read_exact
            # returns.  A small guard covers USB/RS-232 direction turnaround.
            time.sleep(0.025)
            send_case(
                fd, case, length, delay_ms, drain=not args.no_termios,
            )
            print(
                f"{args.test_baud} case {case}: sent {length} payload bytes "
                f"({'unpaced' if not delay_ms else f'{delay_ms:g} ms pacing'})",
                flush=True,
            )
            report = read_exact(fd, 8, 5)
            if report[:2] != bytes((ord("R"), case)):
                raise ValueError(f"bad case {case} report: {report.hex()}")
            expected, received, mismatches, errors, checksum_ok, protocol = \
                report[2:]
            clean = (
                expected == length and received == length
                and mismatches == 0 and errors == 0
                and checksum_ok == 1 and protocol == 0
            )
            row = {
                "case": case,
                "length": length,
                "pacing_ms": delay_ms,
                "expected": expected,
                "received": received,
                "mismatches": mismatches,
                "usart_errors": errors,
                "checksum_ok": bool(checksum_ok),
                "protocol": protocol,
                "pass": clean,
            }
            reports.append(row)
            if args.result:
                args.result.write_text(json.dumps({
                    "status": "running",
                    "test_baud": args.test_baud,
                    "test_parity": args.test_parity,
                    "host_to_juku": reports,
                }, indent=2) + "\n")
            print(
                f"{args.test_baud} case {case}: "
                f"{'PASS' if clean else 'FAIL'} count={received}/{expected} "
                f"mismatches={mismatches} 8251_errors=0x{errors:02X} "
                f"checksum_ok={checksum_ok} protocol={protocol}",
                flush=True,
            )
            time.sleep(0.020)
            write_all(fd, b"\xAC")

        payload = bytes(range(133))
        outbound = read_exact(fd, 2 + 133 + 1, 10)
        expected = b"J" + bytes((133,)) + payload
        expected += bytes((checksum(expected),))
        outbound_ok = outbound == expected
        print(
            f"{args.test_baud} Juku->host: "
            f"{'PASS' if outbound_ok else 'FAIL'}",
            flush=True,
        )
        time.sleep(0.020)
        write_all(fd, b"\xAC")
        done = read_exact(fd, 3, 5)
        print(f"{args.test_baud} return handshake: {done!r}", flush=True)

        time.sleep(0.05)
        if not args.no_termios:
            configure_serial(fd, 9600)
        clean = all(bool(row["pass"]) for row in reports) \
            and outbound_ok and done == b"D\x01!"
        print(
            f"JUKU-{args.test_baud}-LIVE: {'PASS' if clean else 'FAIL'}",
            flush=True,
        )
        result = {
            "test_baud": args.test_baud,
            "test_parity": args.test_parity,
            "host_to_juku": reports,
            "juku_to_host": {"packet_ok": outbound_ok},
            "return_handshake": done.hex(),
            "pass": clean,
        }
        write_result(args.result, result)
        if args.no_resume:
            print("Restored 9600; test complete", flush=True)
            return 0 if clean else 1
        print("Restored 9600 and resumed network A:", flush=True)
        serve_disk(
            fd, volume, timeout=600, resume=True,
            reply_guard=0.010, tx_byte_delay=0.001,
        )
        return 0 if clean else 1
    finally:
        os.close(fd)


if __name__ == "__main__":
    raise SystemExit(main())
