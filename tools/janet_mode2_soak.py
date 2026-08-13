#!/usr/bin/env python3
"""Run the monitorless CS00014 19,200-baud PIT-mode-2 disk soak."""

from __future__ import annotations

import argparse
import array
import fcntl
import hashlib
import io
import json
import os
import sys
import termios
import time
import traceback
from pathlib import Path

from janet_disk_server import serve_disk
from janet_netboot import configure_serial, serve as serve_boot

TIOCGICOUNT = 0x545D


class TimestampedTee(io.TextIOBase):
    """Line-buffered output duplicated to the console and session log."""

    def __init__(self, console: io.TextIOBase, logfile: io.TextIOBase,
                 level: str) -> None:
        self.console = console
        self.logfile = logfile
        self.level = level
        self.at_line_start = True

    def writable(self) -> bool:
        return True

    def write(self, value: str) -> int:
        if not value:
            return 0
        rendered: list[str] = []
        for part in value.splitlines(keepends=True):
            if self.at_line_start:
                rendered.append(
                    f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] "
                    f"[{self.level}] "
                )
            rendered.append(part)
            self.at_line_start = part.endswith(("\n", "\r"))
        output = "".join(rendered)
        self.console.write(output)
        self.logfile.write(output)
        if "\n" in output or "\r" in output:
            self.flush()
        return len(value)

    def flush(self) -> None:
        self.console.flush()
        self.logfile.flush()


def write_result(path: Path, result: dict[str, object]) -> None:
    path.write_text(json.dumps(result, indent=2) + "\n")


def serial_counters(fd: int) -> dict[str, int] | None:
    values = array.array("i", [0] * 20)
    try:
        fcntl.ioctl(fd, TIOCGICOUNT, values, True)
    except (OSError, SystemError):
        return None
    names = ("cts", "dsr", "rng", "dcd", "rx", "tx", "frame", "overrun",
             "parity", "break", "buffer_overrun")
    return dict(zip(names, values[:len(names)], strict=True))


def counter_delta(before: dict[str, int] | None,
                  after: dict[str, int] | None) -> dict[str, int] | None:
    if before is None or after is None:
        return None
    return {name: after[name] - before[name] for name in before}


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("serial")
    result.add_argument("system", type=Path)
    result.add_argument("volume", type=Path)
    result.add_argument("--client", type=lambda value: int(value, 0), default=9)
    result.add_argument("--server", type=lambda value: int(value, 0), default=2)
    result.add_argument("--result", type=Path, required=True)
    result.add_argument(
        "--log", type=Path,
        help="session log path (default: RESULT with a .log suffix)",
    )
    result.add_argument("--no-termios", action="store_true",
                        help=argparse.SUPPRESS)
    return result


def run(args: argparse.Namespace) -> int:
    system = args.system.read_bytes()
    original_volume = args.volume.read_bytes()
    volume = bytearray(original_volume)
    fd = os.dup(int(args.serial.removeprefix("fd:"), 0)) \
        if args.serial.startswith("fd:") else os.open(
            args.serial, os.O_RDWR | os.O_NOCTTY | os.O_NONBLOCK,
        )
    os.set_blocking(fd, False)
    result: dict[str, object] = {
        "status": "starting",
        "protocol": "JUKU-MODE2-SOAK-v1",
        "client": args.client,
        "server": args.server,
        "boot_baud": 9600,
        "disk_baud": 19200,
        "pit_mode": 2,
        "pit_divisor": 4,
        "planned_records": 64,
        "planned_bytes_each_direction": 8192,
        "source_volume_sha256": hashlib.sha256(original_volume).hexdigest(),
    }
    write_result(args.result, result)
    started = time.monotonic()
    try:
        if not args.no_termios:
            configure_serial(fd, 9600)
        print(
            f"Booting {args.system} at 9600/8O1, station "
            f"{args.server:02X} -> {args.client:02X}",
            flush=True,
        )
        boot = serve_boot(
            fd, system, client=args.client, server=args.server, timeout=600,
        )
        result["bootstrap"] = boot
        result["status"] = "disk-soak"
        write_result(args.result, result)

        if not args.no_termios:
            configure_serial(fd, 19200)
        print(
            "Bootstrap complete; host switched to 19,200/8O1. "
            "Waiting for the mode-2 BIOS and serving writable A:",
            flush=True,
        )
        counters_before = serial_counters(fd)
        print(
            "Host UART kernel counters: "
            + ("available" if counters_before is not None
               else "unavailable (optional)"),
            flush=True,
        )
        stats: dict[str, int] = {}
        disk_started = time.monotonic()
        serve_disk(
            fd, volume, writable=True, timeout=180, idle_timeout=None,
            reply_guard=0.002, tx_byte_delay=0.0,
            stop_marker=b"M2PASS!", failure_marker=b"M2FAIL!", stats=stats,
        )
        if stats.get("failure_marker"):
            raise RuntimeError("target emitted M2FAIL! during file verification")
        if not stats.get("marker"):
            raise TimeoutError("target did not emit M2PASS!")
        disk_seconds = time.monotonic() - disk_started
        payload_bytes = (stats["reads"] + stats["writes"]) * 128
        payload_rate = payload_bytes / disk_seconds
        print(
            "M2PASS! received: 8 KiB write/read/byte verification passed; "
            f"{stats['reads']} reads + {stats['writes']} writes carried "
            f"{payload_bytes} payload bytes in {disk_seconds:.3f} s "
            f"({payload_rate:.1f} B/s aggregate); the Juku should now play "
            "the smoke tune",
            flush=True,
        )
        counters_after = serial_counters(fd)
        result.update(
            status="complete",
            pass_=True,
            records_written_and_verified=64,
            bytes_written_and_verified=8192,
            disk_phase_seconds=round(disk_seconds, 3),
            disk_payload_bytes=payload_bytes,
            disk_payload_bytes_per_second=round(payload_rate, 1),
            disk=stats,
            elapsed_seconds=round(time.monotonic() - started, 3),
            working_volume_sha256=hashlib.sha256(volume).hexdigest(),
            host_uart_counter_delta=counter_delta(
                counters_before, counters_after,
            ),
        )
        result["pass"] = result.pop("pass_")
        write_result(args.result, result)
        return 0
    except Exception as error:
        result.update(
            status="host-error",
            pass_=False,
            error=f"{type(error).__name__}: {error}",
            elapsed_seconds=round(time.monotonic() - started, 3),
        )
        result["pass"] = result.pop("pass_")
        write_result(args.result, result)
        raise
    finally:
        if not args.no_termios:
            try:
                termios.tcdrain(fd)
                configure_serial(fd, 9600)
            except OSError:
                pass
        os.close(fd)


def main() -> int:
    args = parser().parse_args()
    log_path = args.log or args.result.with_suffix(".log")
    log_path.parent.mkdir(parents=True, exist_ok=True)
    original_stdout = sys.stdout
    original_stderr = sys.stderr
    with log_path.open("w", buffering=1) as logfile:
        sys.stdout = TimestampedTee(original_stdout, logfile, "INFO")
        sys.stderr = TimestampedTee(original_stderr, logfile, "ERROR")
        try:
            print(f"Mode-2 soak session log: {log_path}", flush=True)
            print(f"Incremental result JSON: {args.result}", flush=True)
            return run(args)
        except BaseException:
            traceback.print_exc()
            return 1
        finally:
            sys.stdout.flush()
            sys.stderr.flush()
            sys.stdout = original_stdout
            sys.stderr = original_stderr


if __name__ == "__main__":
    raise SystemExit(main())
