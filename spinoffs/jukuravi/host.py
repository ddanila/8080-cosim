#!/usr/bin/env python3
"""Jukuravi host session CLI for a Nano USB port or the cosim PTY harness."""

from __future__ import annotations

import argparse
import datetime as dt
import errno
import fcntl
import hashlib
import json
import os
import select
import struct
import sys
import termios
import time
from collections.abc import Callable
from pathlib import Path

import protocol


DEFAULT_BAUD = 115200
DEFAULT_TIMEOUT = 180.0
DEFAULT_BANNER_TIMEOUT = 15.0
DEFAULT_RESET_RETRIES = 2
DEFAULT_LOADER_TIMEOUT = 60.0
DTR_RELEASE_SECONDS = 0.05


class SessionError(RuntimeError):
    """A complete, trustworthy Jukuravi session could not be obtained."""


class BannerTimeout(SessionError):
    """No valid session banner arrived inside the pre-banner deadline."""


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


def parse_nonnegative_int(value: str) -> int:
    parsed = int(value)
    if parsed < 0:
        raise argparse.ArgumentTypeError("value must be nonnegative")
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


def write_all(
    fd: int, data: bytes, deadline: float, description: str = "data"
) -> None:
    view = memoryview(data)
    while view:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise SessionError(f"timeout while sending {description}")
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


def loader_status_name(status: int) -> str:
    return {
        protocol.LOADER_STATUS_OK: "ok",
        protocol.LOADER_STATUS_BAD_CRC: "bad_crc",
        protocol.LOADER_STATUS_BAD_COMMAND: "bad_command",
        protocol.LOADER_STATUS_BAD_LENGTH: "bad_length",
        protocol.LOADER_STATUS_BAD_RANGE: "bad_range",
        protocol.LOADER_STATUS_VERIFY_FAILED: "verify_failed",
    }.get(status, f"unknown_{status:02X}")


class HostSession:
    def __init__(
        self,
        fd: int,
        logs: SessionLogs,
        timeout: float,
        banner_timeout: float,
        expect_rom_version: int | None,
        expect_crc16: int | None,
        nano_reset_requested: bool,
    ) -> None:
        self.fd = fd
        self.logs = logs
        self.timeout = timeout
        self.banner_timeout = banner_timeout
        self.expect_rom_version = expect_rom_version
        self.expect_crc16 = expect_crc16
        self.nano_reset_requested = nano_reset_requested
        self.nano_dtr_sequence_completed = False
        self.nano_dtr_sequences_completed = 0
        self.decoder = protocol.StreamDecoder()
        self.raw_rx = bytearray()
        self.raw_tx = bytearray()
        self.frames: list[protocol.Frame] = []
        self.banner_payload: bytes | None = None
        self.survey: protocol.RamSurvey | None = None
        self.loader: dict[str, object] | None = None
        self.attempts: list[dict[str, object]] = []
        self._attempt_number: int | None = None
        self._attempt_rx_start = 0
        self._attempt_tx_start = 0
        self._attempt_dtr_start = 0

    def begin_attempt(self, number: int) -> None:
        self.decoder = protocol.StreamDecoder()
        self.frames = []
        self.banner_payload = None
        self.survey = None
        self.loader = None
        self._attempt_number = number
        self._attempt_rx_start = len(self.raw_rx)
        self._attempt_tx_start = len(self.raw_tx)
        self._attempt_dtr_start = self.nano_dtr_sequences_completed

    def finish_attempt(self, outcome: str, error: str | None = None) -> None:
        assert self._attempt_number is not None
        self.attempts.append(
            {
                "number": self._attempt_number,
                "outcome": outcome,
                "error": error,
                "received_bytes": len(self.raw_rx) - self._attempt_rx_start,
                "transmitted_bytes": len(self.raw_tx) - self._attempt_tx_start,
                "decoded_frames": len(self.frames),
                "banner_seen": self.banner_payload is not None,
                "dtr_sequence_completed": (
                    self.nano_dtr_sequences_completed > self._attempt_dtr_start
                ),
            }
        )
        self._attempt_number = None

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
        write_all(self.fd, ack, deadline, "banner ACK")
        self.logs.tx(ack)
        self.raw_tx.extend(ack)

    def _read_frames(self, deadline: float, context: str) -> list[protocol.Frame]:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            return []
        if not select.select([self.fd], [], [], min(remaining, 0.25))[0]:
            return []
        try:
            data = os.read(self.fd, 4096)
        except BlockingIOError:
            return []
        except OSError as error:
            if error.errno == errno.EIO:
                raise SessionError(f"serial transport closed {context}") from error
            raise SessionError(f"serial read failed {context}: {error}") from error
        if not data:
            raise SessionError(f"serial transport reached EOF {context}")
        self.logs.rx(data)
        self.raw_rx.extend(data)
        decoded = self.decoder.feed(data)
        self.frames.extend(decoded)
        return decoded

    def run(self) -> None:
        deadline = time.monotonic() + self.timeout
        banner_deadline = min(deadline, time.monotonic() + self.banner_timeout)
        while self.survey is None:
            active_deadline = (
                deadline if self.banner_payload is not None else banner_deadline
            )
            remaining = active_deadline - time.monotonic()
            if remaining <= 0:
                if self.banner_payload is None:
                    if self.frames:
                        raise SessionError(
                            "timeout after protocol frames but before session banner"
                        )
                    raise BannerTimeout("timeout before session banner")
                raise SessionError("timeout before a complete RAM survey")
            for frame in self._read_frames(active_deadline, "before RAM_END"):
                if frame.record_type == protocol.TYPE_BANNER:
                    self._accept_banner(frame, deadline)
                elif frame.record_type == protocol.TYPE_RAM_END:
                    if self.banner_payload is None:
                        raise SessionError("RAM_END arrived without a session banner")
                    try:
                        self.survey = protocol.decode_ram_survey(self.frames)
                    except ValueError as error:
                        raise SessionError(f"invalid RAM survey: {error}") from error

    def _send_loader_frame(
        self, frame: bytes, timeout: float, description: str
    ) -> None:
        write_all(
            self.fd,
            frame,
            time.monotonic() + timeout,
            description,
        )
        self.logs.tx(frame)
        self.raw_tx.extend(frame)

    def _wait_loader_frame(
        self,
        expected_type: int,
        cursor: int,
        timeout: float,
        description: str,
    ) -> tuple[protocol.Frame, int]:
        deadline = time.monotonic() + timeout
        response_types = {
            protocol.TYPE_LOAD_RESULT,
            protocol.TYPE_RUN_ACK,
            protocol.TYPE_LOADER_READY,
            protocol.TYPE_LOADER_ERROR,
        }
        while True:
            while cursor < len(self.frames):
                frame = self.frames[cursor]
                cursor += 1
                if frame.record_type == protocol.TYPE_LOADER_ERROR:
                    if len(frame.payload) != 1:
                        raise SessionError("loader error payload length is not one")
                    status = frame.payload[0]
                    raise SessionError(
                        f"loader error during {description}: "
                        f"{loader_status_name(status)}"
                    )
                if frame.record_type == expected_type:
                    return frame, cursor
                if frame.record_type in response_types:
                    raise SessionError(
                        f"unexpected loader response 0x{frame.record_type:02X} "
                        f"during {description}"
                    )
            if time.monotonic() >= deadline:
                raise SessionError(f"timeout waiting for {description}")
            self._read_frames(deadline, f"while waiting for {description}")

    def run_loader(
        self,
        data: bytes,
        source: str,
        address: int,
        run_address: int | None,
        timeout: float,
    ) -> None:
        if self.survey is None:
            raise SessionError("loader requested before a complete RAM survey")
        end = address + len(data)
        loader: dict[str, object] = {
            "requested": True,
            "status": "waiting_ready",
            "error": None,
            "source": source,
            "sha256": hashlib.sha256(data).hexdigest(),
            "address": f"0x{address:04X}",
            "end_exclusive": f"0x{end:04X}",
            "bytes": len(data),
            "ready": None,
            "chunks": [],
            "run": {
                "requested": run_address is not None,
                "address": None if run_address is None else f"0x{run_address:04X}",
                "acknowledged": False,
            },
        }
        self.loader = loader
        try:
            if not data:
                raise SessionError("upload file is empty")
            if address < protocol.LOADER_LOAD_MIN or end > protocol.LOADER_LOAD_END:
                raise SessionError(
                    "upload range is outside the loader's 0x4000..0xD7FF window"
                )
            largest = self.survey.largest_good_window
            if largest is None or address < largest.start or end > largest.end:
                raise SessionError("upload range is not inside the largest good RAM window")
            if run_address is not None and not address <= run_address < end:
                raise SessionError("run address is outside the uploaded image")

            ram_end_index = max(
                index
                for index, frame in enumerate(self.frames)
                if frame.record_type == protocol.TYPE_RAM_END
            )
            cursor = ram_end_index + 1
            ready, cursor = self._wait_loader_frame(
                protocol.TYPE_LOADER_READY,
                cursor,
                timeout,
                "LOADER_READY",
            )
            if len(ready.payload) != 4:
                raise SessionError("LOADER_READY payload length is not four")
            api_version, max_data, api_hi, api_lo = ready.payload
            api_base = (api_hi << 8) | api_lo
            if api_version != protocol.LOADER_API_VERSION:
                raise SessionError(
                    f"loader API version {api_version} != "
                    f"{protocol.LOADER_API_VERSION}"
                )
            if not 1 <= max_data <= protocol.LOADER_MAX_DATA:
                raise SessionError(f"loader advertised invalid chunk size {max_data}")
            if api_base != protocol.LOADER_API_BASE:
                raise SessionError(
                    f"loader API base {api_base:04X} != {protocol.LOADER_API_BASE:04X}"
                )
            loader["ready"] = {
                "api_version": api_version,
                "max_data_bytes": max_data,
                "api_base": f"0x{api_base:04X}",
            }
            loader["status"] = "loading"

            chunks = loader["chunks"]
            assert isinstance(chunks, list)
            for index, offset in enumerate(range(0, len(data), max_data)):
                chunk = data[offset : offset + max_data]
                chunk_address = address + offset
                frame = protocol.encode_load_frame(chunk_address, chunk)
                self._send_loader_frame(frame, timeout, f"LOAD chunk {index}")
                response, cursor = self._wait_loader_frame(
                    protocol.TYPE_LOAD_RESULT,
                    cursor,
                    timeout,
                    f"LOAD_RESULT chunk {index}",
                )
                if len(response.payload) != 1:
                    raise SessionError("LOAD_RESULT payload length is not one")
                status = response.payload[0]
                chunk_evidence = {
                    "index": index,
                    "address": f"0x{chunk_address:04X}",
                    "bytes": len(chunk),
                    "status": loader_status_name(status),
                }
                chunks.append(chunk_evidence)
                if status != protocol.LOADER_STATUS_OK:
                    raise SessionError(
                        f"LOAD chunk {index} failed: {loader_status_name(status)}"
                    )

            loader["status"] = "loaded"
            if run_address is not None:
                run_frame = protocol.encode_run_frame(run_address)
                self._send_loader_frame(run_frame, timeout, "RUN command")
                response, cursor = self._wait_loader_frame(
                    protocol.TYPE_RUN_ACK,
                    cursor,
                    timeout,
                    "RUN_ACK",
                )
                if response.payload:
                    raise SessionError("RUN_ACK payload is not empty")
                run = loader["run"]
                assert isinstance(run, dict)
                run["acknowledged"] = True
                loader["status"] = "run_acknowledged"
        except (SessionError, OSError) as error:
            loader["status"] = "error"
            loader["error"] = str(error)
            raise

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
                "dtr_sequences_completed": self.nano_dtr_sequences_completed,
            },
            "attempts": self.attempts,
            "image": image,
            "frames": [frame_json(frame) for frame in self.frames],
            "ram_survey": None if self.survey is None else survey_json(self.survey),
            "loader": self.loader,
        }
        return result


def run_session_with_retries(
    session: HostSession,
    reset_retries: int,
    completion: Callable[[], None] | None = None,
) -> None:
    attempt_limit = 1 + reset_retries if session.nano_reset_requested else 1
    for number in range(1, attempt_limit + 1):
        session.begin_attempt(number)
        try:
            if session.nano_reset_requested:
                pulse_nano_dtr(session.fd)
                session.nano_dtr_sequences_completed += 1
                session.nano_dtr_sequence_completed = True
            session.run()
            if completion is not None:
                completion()
        except BannerTimeout as error:
            session.finish_attempt("banner_timeout", str(error))
            if number < attempt_limit:
                continue
            raise
        except (SessionError, OSError) as error:
            session.finish_attempt("error", str(error))
            raise
        session.finish_attempt("ok")
        return


def print_verdict(session: HostSession, logs: SessionLogs) -> None:
    assert session.banner_payload is not None and session.survey is not None
    protocol_version, rom_version, crc_hi, crc_lo = session.banner_payload
    survey = session.survey
    if session.nano_dtr_sequence_completed:
        print(
            "JUKURAVI: nano-reset DTR sequences completed "
            f"{session.nano_dtr_sequences_completed}"
        )
    if len(session.attempts) > 1:
        print(f"JUKURAVI: session attempts {len(session.attempts)}")
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
    if session.loader is not None:
        ready = session.loader.get("ready")
        if isinstance(ready, dict):
            print(
                "JUKURAVI: loader "
                f"api={int(ready['api_version']):02X} "
                f"base={ready['api_base']} max_chunk={ready['max_data_bytes']}"
            )
        print(
            f"JUKURAVI: loaded {session.loader['source']} "
            f"bytes={session.loader['bytes']} address={session.loader['address']} "
            f"chunks={len(session.loader['chunks'])}"
        )
        run = session.loader.get("run")
        if isinstance(run, dict) and run.get("acknowledged"):
            print(f"JUKURAVI: run acknowledged address={run['address']}")
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
    parser.add_argument(
        "--banner-timeout",
        type=float,
        default=DEFAULT_BANNER_TIMEOUT,
        help="seconds to wait for a valid banner before a reset retry",
    )
    parser.add_argument(
        "--reset-retries",
        type=parse_nonnegative_int,
        default=DEFAULT_RESET_RETRIES,
        help="extra DTR resets after a missing banner (real --port sessions only)",
    )
    parser.add_argument("--log-dir", type=Path, default=Path("jukuravi-logs"))
    parser.add_argument("--expect-rom-version", type=parse_hex8)
    parser.add_argument("--expect-crc16", type=parse_hex16)
    parser.add_argument("--load", type=Path, help="binary file to upload after survey")
    parser.add_argument(
        "--load-address",
        type=parse_hex16,
        default=protocol.LOADER_LOAD_MIN,
        help="upload base address (hex; default 4000)",
    )
    parser.add_argument(
        "--run-address",
        type=parse_hex16,
        help="entry address after upload (hex; defaults to --load-address)",
    )
    parser.add_argument(
        "--load-only",
        action="store_true",
        help="upload and verify without sending RUN",
    )
    parser.add_argument(
        "--loader-timeout",
        type=float,
        default=DEFAULT_LOADER_TIMEOUT,
        help="seconds allowed for each loader response",
    )
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
    if args.banner_timeout <= 0:
        print("JUKURAVI: banner timeout must be positive", file=sys.stderr)
        return 2
    if args.loader_timeout <= 0:
        print("JUKURAVI: loader timeout must be positive", file=sys.stderr)
        return 2
    if args.load is None and (args.run_address is not None or args.load_only):
        print("JUKURAVI: --run-address/--load-only requires --load", file=sys.stderr)
        return 2
    if args.load_only and args.run_address is not None:
        print("JUKURAVI: --load-only conflicts with --run-address", file=sys.stderr)
        return 2
    upload_data: bytes | None = None
    run_address: int | None = None
    if args.load is not None:
        try:
            upload_data = args.load.read_bytes()
        except OSError as error:
            print(f"JUKURAVI: cannot read upload file: {error}", file=sys.stderr)
            return 2
        if not upload_data:
            print("JUKURAVI: upload file is empty", file=sys.stderr)
            return 2
        upload_end = args.load_address + len(upload_data)
        if (
            args.load_address < protocol.LOADER_LOAD_MIN
            or upload_end > protocol.LOADER_LOAD_END
        ):
            print(
                "JUKURAVI: upload range must fit 0x4000..0xD7FF",
                file=sys.stderr,
            )
            return 2
        if not args.load_only:
            run_address = (
                args.load_address if args.run_address is None else args.run_address
            )
            if not args.load_address <= run_address < upload_end:
                print(
                    "JUKURAVI: run address must be inside the uploaded image",
                    file=sys.stderr,
                )
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
        args.banner_timeout,
        args.expect_rom_version,
        args.expect_crc16,
        nano_reset_requested,
    )
    completion = None
    if upload_data is not None:
        completion = lambda: session.run_loader(
            upload_data,
            str(args.load),
            args.load_address,
            run_address,
            args.loader_timeout,
        )
    try:
        run_session_with_retries(session, args.reset_retries, completion)
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
