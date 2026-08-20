#!/usr/bin/env python3
"""Load resilient BAUDTEST2 over 9600 and capture its diagnostic matrix."""

from __future__ import annotations

import argparse
import array
import fcntl
import io
import json
import os
import select
import sys
import termios
import time
import traceback
from pathlib import Path

FIXTURES = Path(__file__).resolve().parents[1] / "tests" / "fixtures"
sys.path.insert(0, str(FIXTURES))
from legacy_janet_disk_server import checksum, serve_disk  # noqa: E402
from legacy_janet_netboot import (  # noqa: E402
    configure_serial, serve as serve_boot, write_all,
)


SYNC = b"\xD5\x3A"
TIOCGICOUNT = 0x545D
FRAME_SIZES = {ord("C"): 13, ord("R"): 17, ord("E"): 6}
EXPECTED_REPORTS = 68
STAGE_CONFIG = {
    0: {"baud": 19200, "clock_factor": 16, "pit_mode": 3, "divisor": 4},
    1: {"baud": 9600, "clock_factor": 64, "pit_mode": 3, "divisor": 2},
    2: {"baud": 19200, "clock_factor": 16, "pit_mode": 2, "divisor": 4},
}
PATTERNS = ("increment", "00", "ff", "55", "aa", "decrement",
            "walking-one", "walking-zero", "prbs")
IDLE_SECONDS = (0.0, 0.000050, 0.000250, 0.001, 0.005, 0.020)
PREAMBLES = (b"", b"\xFF" * 16, b"\x00" * 16,
             b"\x55" * 16, b"\xAA" * 16)
STAGE_NAMES = {
    0: "19,200/x16, PIT mode 3 count 4",
    1: "9,600/x64, PIT mode 3 count 2",
    2: "19,200/x16, PIT mode 2 count 4",
}


class TimestampedTee(io.TextIOBase):
    """Line-buffered timestamped output duplicated to console and run log."""

    def __init__(self, console: io.TextIOBase, logfile: io.TextIOBase,
                 level: str) -> None:
        self.console = console
        self.logfile = logfile
        self.level = level
        self.at_line_start = True

    def writable(self) -> bool:
        return True

    def write(self, text: str) -> int:
        if not text:
            return 0
        rendered: list[str] = []
        for part in text.splitlines(keepends=True):
            if self.at_line_start:
                stamp = time.strftime("%Y-%m-%d %H:%M:%S")
                rendered.append(f"[{stamp}] [{self.level}] ")
            rendered.append(part)
            self.at_line_start = part.endswith(("\n", "\r"))
        output = "".join(rendered)
        self.console.write(output)
        self.logfile.write(output)
        if "\n" in output or "\r" in output:
            self.flush()
        return len(text)

    def flush(self) -> None:
        self.console.flush()
        self.logfile.flush()


class FrameParser:
    """Recover complete checksum-valid BAUDTEST2 frames after lost bytes."""

    def __init__(self) -> None:
        self.buffer = bytearray()
        self.bad_checksums = 0
        self.discarded = 0

    def feed(self, data: bytes) -> list[bytes]:
        self.buffer.extend(data)
        frames: list[bytes] = []
        while len(self.buffer) >= 4:
            at = self.buffer.find(SYNC)
            if at < 0:
                self.discarded += max(0, len(self.buffer) - 1)
                del self.buffer[:-1]
                break
            if at:
                self.discarded += at
                del self.buffer[:at]
            if len(self.buffer) < 4:
                break
            size = FRAME_SIZES.get(self.buffer[2])
            if size is None:
                self.discarded += 1
                del self.buffer[0]
                continue
            if len(self.buffer) < size:
                break
            candidate = bytes(self.buffer[:size])
            if checksum(candidate[:-1]) != candidate[-1]:
                self.bad_checksums += 1
                self.discarded += 1
                del self.buffer[0]
                continue
            frames.append(candidate)
            del self.buffer[:size]
        return frames


def write_result(path: Path | None, result: dict[str, object]) -> None:
    if path:
        path.write_text(json.dumps(result, indent=2) + "\n")


def read_raw_until(fd: int, marker: bytes, timeout: float) -> None:
    buffer = bytearray()
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        ready, _, _ = select.select([fd], [], [], 0.1)
        if ready:
            buffer.extend(os.read(fd, 4096))
            if marker in buffer:
                return
            del buffer[:-max(len(marker) - 1, 1)]
    raise TimeoutError(f"did not receive marker {marker!r}")


def next_frame(fd: int, parser: FrameParser, pending: list[bytes],
               timeout: float) -> bytes:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if pending:
            return pending.pop(0)
        ready, _, _ = select.select([fd], [], [], 0.1)
        if ready:
            pending.extend(parser.feed(os.read(fd, 4096)))
    raise TimeoutError("timed out waiting for a BAUDTEST2 frame")


def serial_counters(fd: int) -> dict[str, int] | None:
    """Return Linux UART error counters when this driver supports them."""
    # linux/serial.h serial_icounter_struct contains eleven public counters
    # followed by reserved[9]: twenty native ints in total.  Supplying a
    # shorter mutable buffer lets the kernel overrun it on drivers that
    # implement TIOCGICOUNT (Python reports that as SystemError).
    values = array.array("i", [0] * 20)
    try:
        fcntl.ioctl(fd, TIOCGICOUNT, values, True)
    except (OSError, SystemError):
        # These counters are observability only. PTYs and several USB-serial
        # drivers either reject the ioctl or return an incompatible payload;
        # neither condition may abort the finite target-side diagnostic.
        return None
    names = ("cts", "dsr", "rng", "dcd", "rx", "tx", "frame", "overrun",
             "parity", "break", "buffer_overrun")
    return dict(zip(names, values[:len(names)], strict=True))


def counter_delta(before: dict[str, int] | None,
                  after: dict[str, int] | None) -> dict[str, int] | None:
    if before is None or after is None:
        return None
    return {name: after[name] - before[name] for name in before}


def pattern_bytes(pattern: int, length: int) -> bytes:
    if pattern == 0:
        return bytes(range(length))
    if pattern == 1:
        return bytes(length)
    if pattern == 2:
        return bytes((0xFF,)) * length
    if pattern == 3:
        return bytes((0x55,)) * length
    if pattern == 4:
        return bytes((0xAA,)) * length
    if pattern == 5:
        return bytes((~index & 0xFF) for index in range(length))
    if pattern == 6:
        return bytes((1 << (index & 7)) for index in range(length))
    if pattern == 7:
        return bytes((~(1 << (index & 7)) & 0xFF) for index in range(length))
    if pattern == 8:
        result = bytearray()
        state = 0xA5
        for _ in range(length):
            result.append(state)
            state = (state >> 1) ^ (0xB8 if state & 1 else 0)
        return bytes(result)
    raise ValueError(f"unknown pattern {pattern}")


def send_case(fd: int, *, case: int, length: int, pattern: int,
              idle_code: int, preamble_code: int, chunk: int, gap_ms: int,
              drain: bool, stop_bits: int = 1) -> None:
    if idle_code >= len(IDLE_SECONDS) or preamble_code >= len(PREAMBLES):
        raise ValueError("target sent an invalid delay/preamble descriptor")
    time.sleep(IDLE_SECONDS[idle_code])
    preamble = PREAMBLES[preamble_code]
    if preamble:
        write_all(fd, preamble)
        if drain:
            termios.tcdrain(fd)
    payload = pattern_bytes(pattern, length)
    body = bytes((0xA5, case, length)) + payload
    packet = body + bytes((checksum(body),))
    truncate = os.environ.get("JUKU_BAUDTEST2_TRUNCATE") == f"{case}"
    if truncate:
        packet = packet[:-1]
    if not chunk:
        write_all(fd, packet)
        return
    for offset in range(0, len(packet), chunk):
        write_all(fd, packet[offset:offset + chunk])
        if drain:
            termios.tcdrain(fd)
        if offset + chunk < len(packet):
            time.sleep(gap_ms / 1000.0)


def parse_ready(frame: bytes) -> dict[str, int]:
    fields = frame[3:-1]
    names = ("stage", "case", "length", "pattern", "idle_code",
             "preamble_code", "chunk", "gap_ms", "repeat")
    return dict(zip(names, fields, strict=True))


def parse_report(frame: bytes) -> dict[str, int | bool]:
    fields = frame[3:-1]
    names = ("stage", "case", "length", "received", "mismatches",
             "first_mismatch_index", "first_expected", "first_actual",
             "discarded_before_sync", "usart_errors", "usart_status",
             "checksum_ok", "protocol")
    row: dict[str, int | bool] = dict(zip(names, fields, strict=True))
    row["checksum_ok"] = bool(row["checksum_ok"])
    return row


def make_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("serial")
    parser.add_argument("system", type=Path)
    parser.add_argument("volume", type=Path)
    parser.add_argument("--client", type=lambda value: int(value, 0), default=1)
    parser.add_argument("--server", type=lambda value: int(value, 0), default=2)
    parser.add_argument("--result", type=Path, required=True)
    parser.add_argument(
        "--log", type=Path,
        help="session log path (default: RESULT with a .log suffix)",
    )
    parser.add_argument("--no-termios", action="store_true",
                        help=argparse.SUPPRESS)
    return parser


def run(args: argparse.Namespace) -> int:

    volume = bytearray(args.volume.read_bytes())
    if args.serial.startswith("fd:"):
        fd = os.dup(int(args.serial.removeprefix("fd:"), 0))
        os.set_blocking(fd, False)
    else:
        fd = os.open(args.serial, os.O_RDWR | os.O_NOCTTY | os.O_NONBLOCK)
    result: dict[str, object] = {
        "status": "starting", "protocol": "BAUDTEST2-v1", "cases": [],
    }
    write_result(args.result, result)
    try:
        if not args.no_termios:
            configure_serial(fd, 9600)
        print("Booting automatic resilient BAUDTEST2 at 9600", flush=True)
        serve_boot(fd, args.system.read_bytes(), client=args.client,
                   server=args.server, timeout=600)
        if not args.no_termios:
            configure_serial(fd, 9600)
        serve_disk(fd, volume, timeout=600, stop_marker=b"B2S!", resume=False,
                   reply_guard=0.010, tx_byte_delay=0.001)
        if not args.no_termios:
            configure_serial(fd, 19200)
        print(
            "BAUDTEST2 target loaded; disk phase stopped at B2S!; "
            "host switched to 19,200/8O1",
            flush=True,
        )
        print(f"Stage 0 start: {STAGE_NAMES[0]}", flush=True)

        frame_parser = FrameParser()
        pending: list[bytes] = []
        reports: list[dict[str, object]] = []
        result.update(status="running", cases=reports)
        current_stage = 0
        current: dict[str, int] | None = None
        descriptor_copies = 0
        counters_before = serial_counters(fd)
        print(
            "Host UART kernel counters: "
            + ("available" if counters_before is not None else "unavailable (optional)"),
            flush=True,
        )
        while True:
            frame = next_frame(fd, frame_parser, pending, 20)
            kind = frame[2]
            if kind == ord("C"):
                descriptor = parse_ready(frame)
                key = (descriptor["stage"], descriptor["case"])
                current_key = None if current is None else (
                    current["stage"], current["case"])
                if key != current_key:
                    current = descriptor
                    descriptor_copies = 1
                else:
                    descriptor_copies += 1
                if descriptor_copies == 4:
                    if descriptor["stage"] != current_stage:
                        raise ValueError(f"unexpected stage descriptor {descriptor}")
                    if descriptor["pattern"] >= len(PATTERNS):
                        raise ValueError(f"unknown target pattern {descriptor}")
                    print(
                        f"[{len(reports) + 1}/{EXPECTED_REPORTS}] "
                        f"stage {current_stage} case {descriptor['case']}: "
                        f"length={descriptor['length']} "
                        f"pattern={PATTERNS[descriptor['pattern']]} "
                        f"idle={IDLE_SECONDS[descriptor['idle_code']] * 1000:g}ms "
                        f"preamble={descriptor['preamble_code']} "
                        f"chunk={descriptor['chunk'] or 'wire-rate'} "
                        f"gap={descriptor['gap_ms']}ms "
                        f"stop={2 if descriptor['repeat'] & 0x80 else 1}",
                        flush=True,
                    )
                    stop_bits = 2 if descriptor["repeat"] & 0x80 else 1
                    if not args.no_termios:
                        configure_serial(
                            fd, int(STAGE_CONFIG[current_stage]["baud"]),
                            stop_bits=stop_bits,
                        )
                    send_case(fd, drain=not args.no_termios, **{
                        name: descriptor[name] for name in (
                            "case", "length", "pattern", "idle_code",
                            "preamble_code", "chunk", "gap_ms")
                    }, stop_bits=stop_bits)
                    print(
                        "  payload sent; waiting for target timeout/report",
                        flush=True,
                    )
            elif kind == ord("R"):
                report = parse_report(frame)
                key = (report["stage"], report["case"])
                if any((row["stage"], row["case"]) == key for row in reports):
                    continue
                descriptor = current if current and (
                    current["stage"], current["case"]) == key else {}
                merged: dict[str, object] = {
                    **STAGE_CONFIG[int(report["stage"])],
                    **descriptor,
                    **report,
                    "pattern_name": PATTERNS[int(descriptor.get("pattern", 0))],
                    "host_stop_bits": (
                        2 if int(descriptor.get("repeat", 0)) & 0x80 else 1
                    ),
                }
                merged["pass"] = (
                    report["received"] == report["length"]
                    and report["mismatches"] == 0
                    and report["usart_errors"] == 0
                    and report["checksum_ok"] is True
                    and report["protocol"] == 0
                )
                reports.append(merged)
                result.update(
                    status="running", cases=reports,
                    host_parser={"bad_checksums": frame_parser.bad_checksums,
                                 "discarded": frame_parser.discarded},
                )
                write_result(args.result, result)
                print(
                    f"  report {len(reports)}/{EXPECTED_REPORTS}: "
                    f"{'PASS' if merged['pass'] else 'FAIL'} "
                    f"count={report['received']}/{report['length']} "
                    f"mismatch={report['mismatches']} "
                    f"errors=0x{int(report['usart_errors']):02X} "
                    f"status=0x{int(report['usart_status']):02X} "
                    f"protocol={report['protocol']} checksum={report['checksum_ok']} "
                    f"(saved {args.result})",
                    flush=True,
                )
            else:
                old_stage, next_stage = frame[3], frame[4]
                if old_stage != current_stage:
                    continue
                transition_key = (old_stage, next_stage)
                if result.get("transition_key") == list(transition_key):
                    transition_copies = int(result.get("transition_copies", 0)) + 1
                else:
                    transition_copies = 1
                result["transition_key"] = list(transition_key)
                result["transition_copies"] = transition_copies
                if transition_copies < 5:
                    continue
                print(
                    f"Stage transition {old_stage}->{next_stage}: "
                    "all 5 copies validated",
                    flush=True,
                )
                if next_stage == 0xFF:
                    print(
                        "Final transition received; host switching to 9600 "
                        "and waiting for B2D! restoration marker",
                        flush=True,
                    )
                    if not args.no_termios:
                        configure_serial(fd, 9600)
                    read_raw_until(fd, b"B2D!", 20)
                    print("B2D! received: target confirmed at stock 9600", flush=True)
                    break
                current_stage = next_stage
                current = None
                descriptor_copies = 0
                config = STAGE_CONFIG[current_stage]
                if not args.no_termios:
                    configure_serial(fd, int(config["baud"]))
                print(
                    f"Stage {current_stage} start: {STAGE_NAMES[current_stage]}; "
                    f"host configured {config['baud']}/8O1",
                    flush=True,
                )
                # Discard duplicate E frames buffered at the previous rate.
                pending.clear()
                frame_parser.buffer.clear()

        counters_after = serial_counters(fd)
        result.update(
            status="complete", cases=reports,
            host_parser={"bad_checksums": frame_parser.bad_checksums,
                         "discarded": frame_parser.discarded},
            host_uart_counter_delta=counter_delta(counters_before, counters_after),
            restored_9600=True,
            pass_=(len(reports) == EXPECTED_REPORTS
                   and all(bool(row["pass"]) for row in reports)),
        )
        result["pass"] = result.pop("pass_")
        write_result(args.result, result)
        print(
            f"BAUDTEST2 complete: {len(reports)} reports, "
            f"{'PASS' if result['pass'] else 'diagnostic failures recorded'}; "
            "target restored 9600",
            flush=True,
        )
        # A physical receive failure is evidence, not a host-tool failure.
        return 0
    except Exception as error:
        result.update(status="host-error", error=f"{type(error).__name__}: {error}")
        write_result(args.result, result)
        raise
    finally:
        if not args.no_termios:
            try:
                configure_serial(fd, 9600)
            except OSError:
                pass
        os.close(fd)


def main() -> int:
    args = make_parser().parse_args()
    log_path = args.log or args.result.with_suffix(".log")
    log_path.parent.mkdir(parents=True, exist_ok=True)
    original_stdout = sys.stdout
    original_stderr = sys.stderr
    with log_path.open("w", buffering=1) as logfile:
        sys.stdout = TimestampedTee(original_stdout, logfile, "INFO")
        sys.stderr = TimestampedTee(original_stderr, logfile, "ERROR")
        try:
            print(f"BAUDTEST2 session log: {log_path}", flush=True)
            print(f"Incremental result JSON: {args.result}", flush=True)
            return run(args)
        except BaseException:  # retain the complete traceback in both outputs
            traceback.print_exc()
            return 1
        finally:
            sys.stdout.flush()
            sys.stderr.flush()
            sys.stdout = original_stdout
            sys.stderr = original_stderr


if __name__ == "__main__":
    raise SystemExit(main())
