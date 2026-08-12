#!/usr/bin/env python3
"""Load BAUDTEST once and sweep 14,400, 16,000, and 19,200 automatically."""

from __future__ import annotations

import argparse
import ctypes
import json
import os
import termios
import time
from pathlib import Path

from janet_baud_test import CASES, read_exact, send_case
from janet_disk_server import checksum, serve_disk
from janet_netboot import (
    configure_serial,
    serve as serve_boot,
    write_all,
)


# D57 remains in the EktaSoft LSB-only BCD mode. The 8251's x1 clock factor
# lets its integer divisors match three rates implemented natively by the
# classic CP2102. The first tuple field is the byte written to D57; the second
# is its effective BCD value.
RATES = (
    (0x85, 85, 14_400),
    (0x77, 77, 16_000),
    (0x64, 64, 19_200),
)


class Termios2(ctypes.Structure):
    _fields_ = [
        ("c_iflag", ctypes.c_uint),
        ("c_oflag", ctypes.c_uint),
        ("c_cflag", ctypes.c_uint),
        ("c_lflag", ctypes.c_uint),
        ("c_line", ctypes.c_ubyte),
        ("c_cc", ctypes.c_ubyte * 19),
        ("c_ispeed", ctypes.c_uint),
        ("c_ospeed", ctypes.c_uint),
    ]


TCGETS2 = 0x802C542A
TCSETS2 = 0x402C542B
CBAUD = 0x100F
BOTHER = 0x1000


def configure_ladder_serial(fd: int, baud: int) -> None:
    """Apply 8O1 at a CP2102-native ladder rate, including Linux B16000."""
    if baud != 16_000:
        configure_serial(fd, baud)
        return
    # Python exposes no termios.B16000. Establish all framing flags with the
    # shared helper, then select the exact integer rate through termios2.
    configure_serial(fd, 9600)
    settings = Termios2()
    libc = ctypes.CDLL(None, use_errno=True)
    if libc.ioctl(fd, TCGETS2, ctypes.byref(settings)) < 0:
        error = ctypes.get_errno()
        raise OSError(error, os.strerror(error))
    settings.c_cflag = (settings.c_cflag & ~CBAUD) | BOTHER
    settings.c_ispeed = baud
    settings.c_ospeed = baud
    if libc.ioctl(fd, TCSETS2, ctypes.byref(settings)) < 0:
        error = ctypes.get_errno()
        raise OSError(error, os.strerror(error))
    check = Termios2()
    if libc.ioctl(fd, TCGETS2, ctypes.byref(check)) < 0:
        error = ctypes.get_errno()
        raise OSError(error, os.strerror(error))
    if check.c_ispeed != baud or check.c_ospeed != baud:
        raise RuntimeError(
            f"serial driver reports {check.c_ispeed}/{check.c_ospeed}, "
            f"expected {baud}"
        )
    termios.tcflush(fd, termios.TCIOFLUSH)


def save(path: Path, status: str, sweeps: list[dict[str, object]]) -> None:
    path.write_text(json.dumps({
        "status": status,
        "framing": "8O1",
        "rates": sweeps,
        "pass": status == "complete" and all(
            bool(sweep.get("pass")) for sweep in sweeps
        ),
    }, indent=2) + "\n")


def run_sweep(
    fd: int, *, divisor_byte: int, divisor: int, host_baud: int,
    drain: bool, result_path: Path, completed: list[dict[str, object]],
) -> dict[str, object]:
    ready = read_exact(fd, 4, 10)
    if ready != b"BRD!":
        raise ValueError(
            f"divisor {divisor}: bad ready marker {ready!r}"
        )
    print(
        f"D57 BCD divisor {divisor} (write 0x{divisor_byte:02X}), 8251 x1: "
        f"target {16_000_000 / (13 * divisor):.3f}, host "
        f"{host_baud} baud, 8O1; ready received",
        flush=True,
    )
    reports: list[dict[str, object]] = []
    sweep: dict[str, object] = {
        "divisor": divisor,
        "divisor_byte": divisor_byte,
        "clock_factor": 1,
        "target_baud": 16_000_000 / (13 * divisor),
        "host_baud": host_baud,
        "host_to_juku": reports,
    }
    for case, (length, delay_ms) in enumerate(CASES):
        marker = read_exact(fd, 2, 5)
        expected_marker = bytes((ord("C"), case))
        if marker != expected_marker:
            raise ValueError(
                f"divisor {divisor}: bad case marker {marker!r}, "
                f"expected {expected_marker!r}"
            )
        time.sleep(0.025)
        send_case(fd, case, length, delay_ms, drain=drain)
        report = read_exact(fd, 8, 5)
        if report[:2] != bytes((ord("R"), case)):
            raise ValueError(
                f"divisor {divisor}: bad case {case} report {report.hex()}"
            )
        expected, received, mismatches, errors, checksum_ok, protocol = \
            report[2:]
        clean = (
            expected == length and received == length and mismatches == 0
            and errors == 0 and checksum_ok == 1 and protocol == 0
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
        save(result_path, "running", completed + [sweep])
        print(
            f"divisor {divisor} case {case}: "
            f"{'PASS' if clean else 'FAIL'} count={received}/{expected} "
            f"mismatches={mismatches} 8251_errors=0x{errors:02X} "
            f"checksum_ok={checksum_ok} protocol={protocol}",
            flush=True,
        )
        time.sleep(0.020)
        write_all(fd, b"\xAC")

    payload = bytes(range(133))
    outbound = read_exact(fd, 136, 10)
    expected_packet = b"J" + bytes((133,)) + payload
    expected_packet += bytes((checksum(expected_packet),))
    outbound_ok = outbound == expected_packet
    print(
        f"divisor {divisor} Juku->host: "
        f"{'PASS' if outbound_ok else 'FAIL'}",
        flush=True,
    )
    time.sleep(0.020)
    write_all(fd, b"\xAC")
    done = read_exact(fd, 3, 5)
    print(f"divisor {divisor} handshake: {done!r}", flush=True)
    sweep["juku_to_host"] = {"packet_ok": outbound_ok}
    sweep["handshake"] = done.hex()
    sweep["pass"] = (
        all(bool(row["pass"]) for row in reports)
        and outbound_ok and done == b"D\x01!"
    )
    save(result_path, "running", completed + [sweep])
    return sweep


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("serial")
    parser.add_argument("system", type=Path)
    parser.add_argument("volume", type=Path)
    parser.add_argument("--client", type=lambda value: int(value, 0), default=1)
    parser.add_argument("--server", type=lambda value: int(value, 0), default=2)
    parser.add_argument("--result", type=Path, required=True)
    parser.add_argument("--no-termios", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args()
    volume = bytearray(args.volume.read_bytes())
    if args.serial.startswith("fd:"):
        fd = os.dup(int(args.serial.removeprefix("fd:"), 0))
        os.set_blocking(fd, False)
    else:
        fd = os.open(args.serial, os.O_RDWR | os.O_NOCTTY | os.O_NONBLOCK)
    sweeps: list[dict[str, object]] = []
    try:
        if not args.no_termios:
            configure_serial(fd, 9600)
        print("Booting automatic baud-ladder system at 9600/8O1", flush=True)
        serve_boot(
            fd, args.system.read_bytes(), client=args.client,
            server=args.server, timeout=600,
        )
        if not args.no_termios:
            configure_serial(fd, 9600)
        print("Serving A:; baud ladder auto-starts after boot", flush=True)
        serve_disk(
            fd, volume, timeout=600, stop_marker=b"B96!", resume=False,
            reply_guard=0.010, tx_byte_delay=0.001,
        )

        for divisor_byte, divisor, host_baud in RATES:
            if not args.no_termios:
                configure_ladder_serial(fd, host_baud)
            sweeps.append(run_sweep(
                fd, divisor_byte=divisor_byte, divisor=divisor,
                host_baud=host_baud, drain=not args.no_termios,
                result_path=args.result, completed=sweeps,
            ))
        time.sleep(0.05)
        if not args.no_termios:
            configure_serial(fd, 9600)
        save(args.result, "complete", sweeps)
        clean = all(bool(sweep["pass"]) for sweep in sweeps)
        print(
            f"JUKU-BAUD-LADDER-LIVE: {'PASS' if clean else 'FAIL'}",
            flush=True,
        )
        print("Restored 9600/8O1; test complete", flush=True)
        return 0 if clean else 1
    finally:
        if not args.no_termios:
            configure_serial(fd, 9600)
        os.close(fd)


if __name__ == "__main__":
    raise SystemExit(main())
