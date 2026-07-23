#!/usr/bin/env python3
"""Jukuravi host session CLI for a Nano USB port or the cosim PTY harness."""

from __future__ import annotations

import argparse
import datetime as dt
import errno
import fcntl
import json
import os
import select
import struct
import sys
import termios
import time
from pathlib import Path

import protocol


DEFAULT_BAUD = 115200
DEFAULT_TIMEOUT = 180.0
DTR_RELEASE_SECONDS = 0.05


class SessionError(RuntimeError):
    """A complete, trustworthy Jukuravi session could not be obtained."""


def parse_hex16(value: str) -> int:
    text = value.strip().lower()
    base = 16 if not text.startswith(("0x", "0o", "0b")) else 0
    parsed = int(text, base)
    if not 0 <= parsed <= 0xFFFF:
        raise argparse.ArgumentTypeError("value must fit 16 bits")
    return parsed


def parse_hex8(value: str) -> int:
    parsed = parse_hex16(value)
    if parsed > 0xFF:
        raise argparse.ArgumentTypeError("value must fit eight bits")
    return parsed


def configure_serial(fd: int, baud: int) -> None:
    speed = getattr(termios, f"B{baud}", None)
    if speed is None:
        raise SessionError(f"unsupported host serial baud: {baud}")
    attrs = termios.tcgetattr(fd)
    attrs[0] = 0
    attrs[1] = 0
    attrs[2] = termios.CS8 | termios.CREAD | termios.CLOCAL
    attrs[3] = 0
    attrs[4] = speed
    attrs[5] = speed
    attrs[6][termios.VMIN] = 0
    attrs[6][termios.VTIME] = 0
    termios.tcsetattr(fd, termios.TCSANOW, attrs)
    termios.tcflush(fd, termios.TCIOFLUSH)


def pulse_nano_dtr(fd: int) -> None:
    """Restart a classic Nano through its DTR-coupled reset capacitor."""
    try:
        clear_bits = termios.TIOCMBIC
        set_bits = termios.TIOCMBIS
        dtr = termios.TIOCM_DTR
    except AttributeError as error:
        raise SessionError("platform does not expose POSIX DTR controls") from error
    mask = struct.pack("i", dtr)
    try:
        # Deassert first, then assert: the USB adapter's active-low DTR output
        # creates the falling edge coupled into the classic Nano RESET input.
        fcntl.ioctl(fd, clear_bits, mask)
        time.sleep(DTR_RELEASE_SECONDS)
        fcntl.ioctl(fd, set_bits, mask)
        termios.tcflush(fd, termios.TCIOFLUSH)
    except OSError as error:
        raise SessionError(f"cannot restart Nano through DTR: {error}") from error


def open_transport(port: str | None, inherited_fd: int | None, baud: int) -> tuple[int, str]:
    if inherited_fd is not None:
        try:
            fd = os.dup(inherited_fd)
        except OSError as error:
            raise SessionError(f"cannot duplicate inherited fd {inherited_fd}: {error}") from error
        label = f"fd:{inherited_fd}"
    else:
        assert port is not None
        try:
            fd = os.open(port, os.O_RDWR | os.O_NOCTTY | os.O_NONBLOCK)
        except OSError as error:
            raise SessionError(f"cannot open serial port {port}: {error}") from error
        try:
            configure_serial(fd, baud)
        except Exception:
            os.close(fd)
            raise
        label = port
    os.set_blocking(fd, False)
    return fd, label


class SessionLogs:
    def __init__(self, root: Path, transport: str) -> None:
        now = dt.datetime.now(dt.timezone.utc)
        self.started = now.isoformat().replace("+00:00", "Z")
        stem = now.strftime("%Y%m%dT%H%M%S.%fZ")
        root.mkdir(parents=True, exist_ok=True)
        self.rx_path = root / f"{stem}.rx.bin"
        self.tx_path = root / f"{stem}.tx.bin"
        self.json_path = root / f"{stem}.json"
        self.transport = transport
        self._rx = self.rx_path.open("wb")
        self._tx = self.tx_path.open("wb")

    def rx(self, data: bytes) -> None:
        self._rx.write(data)
        self._rx.flush()

    def tx(self, data: bytes) -> None:
        self._tx.write(data)
        self._tx.flush()

    def finish(self, summary: dict[str, object]) -> None:
        self._rx.close()
        self._tx.close()
        summary = {
            "started_utc": self.started,
            "finished_utc": dt.datetime.now(dt.timezone.utc).isoformat().replace(
                "+00:00", "Z"
            ),
            "transport": self.transport,
            "rx_log": self.rx_path.name,
            "tx_log": self.tx_path.name,
            **summary,
        }
        self.json_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")


def write_all(fd: int, data: bytes, deadline: float) -> None:
    view = memoryview(data)
    while view:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise SessionError("timeout while sending ACK")
        if not select.select([], [fd], [], min(remaining, 0.25))[1]:
            continue
        try:
            written = os.write(fd, view)
        except BlockingIOError:
            continue
        except OSError as error:
            raise SessionError(f"serial write failed: {error}") from error
        view = view[written:]


def leading_training_bytes(raw: bytes) -> int:
    count = 0
    for byte in raw:
        if byte != 0x55:
            break
        count += 1
    return count


def frame_json(frame: protocol.Frame) -> dict[str, object]:
    return {
        "type": f"0x{frame.record_type:02X}",
        "payload_hex": frame.payload.hex().upper(),
    }


def survey_json(survey: protocol.RamSurvey) -> dict[str, object]:
    bad_by_chip = {
        f"D{84 + bit}": [f"0x{page:02X}" for page in pages]
        for bit, pages in enumerate(survey.bad_pages_by_bit)
    }
    largest = survey.largest_good_window
    return {
        "version": survey.version,
        "pattern_set": survey.pattern_set,
        "start": f"0x{survey.start_page << 8:04X}",
        "end_exclusive": f"0x{(survey.end_page + 1) << 8:05X}",
        "page_masks_hex": [f"{mask:02X}" for mask in survey.masks],
        "bad_pages_by_chip": bad_by_chip,
        "largest_good_window": None if largest is None else {
            "start": f"0x{largest.start:04X}",
            "end_exclusive": f"0x{largest.end:05X}",
            "bytes": largest.length,
        },
    }


class HostSession:
    def __init__(
        self,
        fd: int,
        logs: SessionLogs,
        timeout: float,
        expect_rom_version: int | None,
        expect_crc16: int | None,
        nano_reset_requested: bool,
    ) -> None:
        self.fd = fd
        self.logs = logs
        self.timeout = timeout
        self.expect_rom_version = expect_rom_version
        self.expect_crc16 = expect_crc16
        self.nano_reset_requested = nano_reset_requested
        self.nano_dtr_sequence_completed = False
        self.decoder = protocol.StreamDecoder()
        self.raw_rx = bytearray()
        self.raw_tx = bytearray()
        self.frames: list[protocol.Frame] = []
        self.banner_payload: bytes | None = None
        self.survey: protocol.RamSurvey | None = None

    def _accept_banner(self, frame: protocol.Frame, deadline: float) -> None:
        if len(frame.payload) != 4:
            raise SessionError("banner payload length is not four")
        protocol_version, rom_version, crc_hi, crc_lo = frame.payload
        crc16 = (crc_hi << 8) | crc_lo
        if protocol_version != protocol.PROTOCOL_VERSION:
            raise SessionError(
                f"protocol version {protocol_version} != {protocol.PROTOCOL_VERSION}"
            )
        if self.expect_rom_version is not None and rom_version != self.expect_rom_version:
            raise SessionError(
                f"ROM version {rom_version:02X} != expected {self.expect_rom_version:02X}"
            )
        if self.expect_crc16 is not None and crc16 != self.expect_crc16:
            raise SessionError(
                f"image CRC16 {crc16:04X} != expected {self.expect_crc16:04X}"
            )
        if self.banner_payload is not None:
            if frame.payload != self.banner_payload:
                raise SessionError("ROM identity changed during one session")
            return
        self.banner_payload = frame.payload
        ack = protocol.encode_frame(protocol.TYPE_ACK, frame.payload)
        write_all(self.fd, ack, deadline)
        self.logs.tx(ack)
        self.raw_tx.extend(ack)

    def run(self) -> None:
        deadline = time.monotonic() + self.timeout
        while self.survey is None:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise SessionError("timeout before a complete RAM survey")
            if not select.select([self.fd], [], [], min(remaining, 0.25))[0]:
                continue
            try:
                data = os.read(self.fd, 4096)
            except BlockingIOError:
                continue
            except OSError as error:
                if error.errno == errno.EIO:
                    raise SessionError("serial transport closed before RAM_END") from error
                raise SessionError(f"serial read failed: {error}") from error
            if not data:
                raise SessionError("serial transport reached EOF before RAM_END")
            self.logs.rx(data)
            self.raw_rx.extend(data)
            for frame in self.decoder.feed(data):
                self.frames.append(frame)
                if frame.record_type == protocol.TYPE_BANNER:
                    self._accept_banner(frame, deadline)
                elif frame.record_type == protocol.TYPE_RAM_END:
                    if self.banner_payload is None:
                        raise SessionError("RAM_END arrived without a session banner")
                    try:
                        self.survey = protocol.decode_ram_survey(self.frames)
                    except ValueError as error:
                        raise SessionError(f"invalid RAM survey: {error}") from error

    def summary(self, status: str, error: str | None = None) -> dict[str, object]:
        image: dict[str, object] | None = None
        if self.banner_payload is not None:
            image = {
                "protocol_version": self.banner_payload[0],
                "rom_version": self.banner_payload[1],
                "crc16": f"{int.from_bytes(self.banner_payload[2:], 'big'):04X}",
            }
        result: dict[str, object] = {
            "status": status,
            "error": error,
            "received_bytes": len(self.raw_rx),
            "transmitted_bytes": len(self.raw_tx),
            "leading_training_bytes": leading_training_bytes(self.raw_rx),
            "nano_control": {
                "dtr_reset_requested": self.nano_reset_requested,
                "dtr_sequence_completed": self.nano_dtr_sequence_completed,
            },
            "image": image,
            "frames": [frame_json(frame) for frame in self.frames],
            "ram_survey": None if self.survey is None else survey_json(self.survey),
        }
        return result


def print_verdict(session: HostSession, logs: SessionLogs) -> None:
    assert session.banner_payload is not None and session.survey is not None
    protocol_version, rom_version, crc_hi, crc_lo = session.banner_payload
    survey = session.survey
    if session.nano_dtr_sequence_completed:
        print("JUKURAVI: nano-reset DTR sequence completed")
    print(
        f"JUKURAVI: protocol={protocol_version:02X} rom={rom_version:02X} "
        f"image_crc16={crc_hi:02X}{crc_lo:02X}"
    )
    print(
        f"JUKURAVI: RAM {survey.start_page:02X}00-"
        f"{survey.end_page:02X}FF survey={survey.version:02X} "
        f"pattern={survey.pattern_set:02X}"
    )
    for bit, pages in enumerate(survey.bad_pages_by_bit):
        verdict = "PASS" if not pages else "bad pages " + ",".join(
            f"{page:02X}" for page in pages
        )
        print(f"JUKURAVI: D{84 + bit}/bit{bit} {verdict}")
    largest = survey.largest_good_window
    if largest is None:
        print("JUKURAVI: largest-good-window NONE")
    else:
        print(
            f"JUKURAVI: largest-good-window {largest.start:04X}-"
            f"{largest.end - 1:04X} bytes={largest.length}"
        )
    print(f"JUKURAVI: logs {logs.json_path}")


def make_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run one framed Jukuravi diagnostic session"
    )
    transport = parser.add_mutually_exclusive_group(required=True)
    transport.add_argument("--port", help="Nano USB serial device, e.g. /dev/ttyUSB0")
    transport.add_argument(
        "--fd", type=int, help="inherited PTY master descriptor for the cosim harness"
    )
    parser.add_argument("--baud", type=int, default=DEFAULT_BAUD)
    parser.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT)
    parser.add_argument("--log-dir", type=Path, default=Path("jukuravi-logs"))
    parser.add_argument("--expect-rom-version", type=parse_hex8)
    parser.add_argument("--expect-crc16", type=parse_hex16)
    parser.add_argument(
        "--no-nano-reset",
        action="store_true",
        help="do not restart the Nano through DTR before a --port session",
    )
    return parser


def main() -> int:
    args = make_parser().parse_args()
    if args.timeout <= 0:
        print("JUKURAVI: timeout must be positive", file=sys.stderr)
        return 2
    try:
        fd, transport = open_transport(args.port, args.fd, args.baud)
    except SessionError as error:
        print(f"JUKURAVI: ERROR {error}", file=sys.stderr)
        return 1
    logs = SessionLogs(args.log_dir, transport)
    nano_reset_requested = args.port is not None and not args.no_nano_reset
    session = HostSession(
        fd,
        logs,
        args.timeout,
        args.expect_rom_version,
        args.expect_crc16,
        nano_reset_requested,
    )
    try:
        if nano_reset_requested:
            pulse_nano_dtr(fd)
            session.nano_dtr_sequence_completed = True
        session.run()
    except (SessionError, OSError) as error:
        logs.finish(session.summary("error", str(error)))
        print(f"JUKURAVI: ERROR {error}", file=sys.stderr)
        print(f"JUKURAVI: logs {logs.json_path}", file=sys.stderr)
        return 1
    finally:
        os.close(fd)
    logs.finish(session.summary("ok"))
    print_verdict(session, logs)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
