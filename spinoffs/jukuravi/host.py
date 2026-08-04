#!/usr/bin/env python3
"""Jukuravi host session CLI for a serial port or the cosim PTY harness."""

from __future__ import annotations

import argparse
import copy
import datetime as dt
import errno
import fcntl
import hashlib
import json
import os
import secrets
import select
import struct
import sys
import termios
import time
from collections.abc import Callable
from pathlib import Path

import protocol


DEFAULT_BAUD = 2400
DEFAULT_TIMEOUT = 180.0
DEFAULT_BANNER_TIMEOUT = 15.0
DEFAULT_RESET_RETRIES = 2
DEFAULT_LOADER_TIMEOUT = 60.0
DEFAULT_LOADER_RETRIES = 3
DEFAULT_HEARTBEAT_TIMEOUT = 5.0
DEFAULT_HEARTBEAT_RESET_RETRIES = 0
DTR_RELEASE_SECONDS = 0.05
LOADER_SYMBOL_REQUESTS = (0xC6, 0xC7)
DEFAULT_LOADER_VOTES = 1
SOLICITED_RESPONSE_GUARD_SECONDS = 0.006
# Anchored to this file, not the CWD: host.py is documented as being run from the
# repository root, and a relative default scattered run logs there.
DEFAULT_LOG_DIR = Path(__file__).resolve().parent / "sessions" / "default"


class SessionError(RuntimeError):
    """A complete, trustworthy Jukuravi session could not be obtained."""


class BannerTimeout(SessionError):
    """No valid session banner arrived inside the pre-banner deadline."""


class HeartbeatTimeout(SessionError):
    """An uploaded program stopped producing its required liveness records."""


class LoaderFrameError(SessionError):
    """The ROM rejected a frame while retaining the next decoder cursor."""

    def __init__(self, status: int, cursor: int, description: str) -> None:
        self.status = status
        self.cursor = cursor
        super().__init__(
            f"loader error during {description}: {loader_status_name(status)}"
        )


class LoaderResponseTimeout(SessionError):
    """No loader response arrived, while retaining the decoder cursor."""

    def __init__(self, cursor: int, description: str) -> None:
        self.cursor = cursor
        super().__init__(f"timeout waiting for {description}")


class LoaderRequestDemux:
    """Extract C6/C7 flow-control tokens only outside framed ROM output."""

    def __init__(self) -> None:
        self.pending_sync = False
        self.header_bytes = 0
        self.frame_remaining = 0

    def feed(self, data: bytes) -> list[int]:
        requests: list[int] = []
        for byte in data:
            if self.frame_remaining:
                self.frame_remaining -= 1
                continue
            if self.header_bytes:
                if self.header_bytes == 2:
                    # Type byte.
                    self.header_bytes = 1
                else:
                    # Length byte; payload plus trailing CRC-8 are framed.
                    self.frame_remaining = byte + 1
                    self.header_bytes = 0
                continue
            if self.pending_sync:
                self.pending_sync = False
                if byte == protocol.SYNC[1]:
                    self.header_bytes = 2
                    continue
                # A lone A5 was ordinary out-of-frame output. Process this
                # current byte normally; only C6/C7 have transport meaning.
            if byte == protocol.SYNC[0]:
                self.pending_sync = True
            elif byte in LOADER_SYMBOL_REQUESTS:
                requests.append(byte)
        return requests


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


def parse_positive_int(value: str) -> int:
    parsed = int(value)
    if parsed <= 0:
        raise argparse.ArgumentTypeError("value must be positive")
    return parsed


def parse_nonnegative_float(value: str) -> float:
    parsed = float(value)
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


def diagnostic_status_json(values: list[int]) -> dict[str, object] | None:
    if not values:
        return None
    peripheral = next((value for value in values if not value & 0x80), None)
    ram = next((value for value in values if value & 0x80), None)
    return {
        "peripheral_fault_mask_hex": None if peripheral is None else f"{peripheral:02X}",
        "pic": None if peripheral is None else not bool(peripheral & 0x01),
        "ppi": None if peripheral is None else not bool(peripheral & 0x02),
        "d54": None if peripheral is None else not bool(peripheral & 0x04),
        "d55": None if peripheral is None else not bool(peripheral & 0x08),
        "d57": None if peripheral is None else not bool(peripheral & 0x10),
        "ram_4000": None if ram is None else bool(ram & 0x01),
        "ram_c000": None if ram is None else bool(ram & 0x02),
    }


def loader_status_name(status: int) -> str:
    return {
        protocol.LOADER_STATUS_OK: "ok",
        protocol.LOADER_STATUS_BAD_CRC: "bad_crc",
        protocol.LOADER_STATUS_BAD_COMMAND: "bad_command",
        protocol.LOADER_STATUS_BAD_LENGTH: "bad_length",
        protocol.LOADER_STATUS_BAD_RANGE: "bad_range",
        protocol.LOADER_STATUS_VERIFY_FAILED: "verify_failed",
        protocol.LOADER_STATUS_STRONG_CRC: "strong_crc",
        protocol.LOADER_STATUS_BAD_CONFIG: "bad_config",
        protocol.LOADER_STATUS_WORKSPACE: "workspace",
    }.get(status, f"unknown_{status:02X}")


def decode_loader_v2_result(frame: protocol.Frame) -> dict[str, int]:
    if frame.record_type != protocol.TYPE_LOADER_V2_RESULT or len(frame.payload) != 10:
        raise SessionError("loader API v2 RESULT must contain ten detail bytes")
    (
        transaction, status, command, decoded_length, address_hi, address_lo,
        count, crc_hi, crc_lo, store_retries,
    ) = frame.payload
    return {
        "transaction": transaction,
        "status": status,
        "command": command,
        "decoded_length": decoded_length,
        "address": (address_hi << 8) | address_lo,
        "count": count,
        "crc16": (crc_hi << 8) | crc_lo,
        "store_retries": store_retries,
    }


def decode_loader_v2_data(frame: protocol.Frame) -> tuple[dict[str, int], bytes]:
    if frame.record_type != protocol.TYPE_LOADER_V2_DATA or len(frame.payload) < 6:
        raise SessionError("loader API v2 DATA is shorter than its six-byte header")
    transaction, status, command, address_hi, address_lo, count = frame.payload[:6]
    data = frame.payload[6:]
    if len(data) != count:
        raise SessionError(
            f"loader API v2 DATA count {count} differs from payload bytes {len(data)}"
        )
    return {
        "transaction": transaction,
        "status": status,
        "command": command,
        "address": (address_hi << 8) | address_lo,
        "count": count,
    }, data


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
        loader_guard_seconds: float = SOLICITED_RESPONSE_GUARD_SECONDS,
        loader_chunk_size: int | None = None,
        loader_retries: int = 3,
        loader_votes: int = DEFAULT_LOADER_VOTES,
        loader_resume: bool = False,
        loader_readback: bool = True,
        loader_run_mode: str = "call",
        result_address: int | None = None,
        result_length: int = 0,
        control_read_address: int | None = None,
        control_read_length: int = 0,
        loader_benchmark_passes: int = 1,
    ) -> None:
        self.fd = fd
        self.logs = logs
        self.timeout = timeout
        self.banner_timeout = banner_timeout
        self.expect_rom_version = expect_rom_version
        self.expect_crc16 = expect_crc16
        self.nano_reset_requested = nano_reset_requested
        self.loader_guard_seconds = loader_guard_seconds
        self.loader_chunk_size = loader_chunk_size
        self.loader_retries = loader_retries
        self.loader_votes = loader_votes
        self.loader_resume = loader_resume
        self.loader_readback = loader_readback
        self.loader_run_mode = loader_run_mode
        self.result_address = result_address
        self.result_length = result_length
        self.control_read_address = control_read_address
        self.control_read_length = control_read_length
        self.loader_benchmark_passes = loader_benchmark_passes
        self.nano_dtr_sequence_completed = False
        self.nano_dtr_sequences_completed = 0
        self.heartbeat_reset_retries_requested = 0
        self.heartbeat_reset_retries_used = 0
        self.decoder = protocol.StreamDecoder()
        self.request_demux = LoaderRequestDemux()
        self.raw_rx = bytearray()
        self.raw_tx = bytearray()
        self.frames: list[protocol.Frame] = []
        self.banner_payload: bytes | None = None
        self.survey: protocol.RamSurvey | None = None
        self.diagnostic_status: list[int] = []
        self.encoded_host_tx = False
        self.host_symbol_repetitions = 1
        self.solicited_host_tx = False
        self.symbol_requests: list[int] = []
        self.last_solicited_token: int | None = None
        self.last_solicited_byte: int | None = None
        self.handshake_mismatches: list[tuple[int, int]] = []
        self.loader: dict[str, object] | None = None
        self.nano_liveness: dict[str, object] | None = None
        self.attempts: list[dict[str, object]] = []
        self._attempt_number: int | None = None
        self._attempt_rx_start = 0
        self._attempt_tx_start = 0
        self._attempt_dtr_start = 0

    def begin_attempt(self, number: int) -> None:
        self.decoder = protocol.StreamDecoder()
        self.request_demux = LoaderRequestDemux()
        self.frames = []
        self.banner_payload = None
        self.survey = None
        self.diagnostic_status = []
        self.loader = None
        self.nano_liveness = None
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
                "loader": copy.deepcopy(self.loader),
                "nano_liveness": copy.deepcopy(self.nano_liveness),
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
            # A reset can bounce or be deliberately pressed while this host is
            # already waiting for LOADER_READY or a command response. The ROM
            # has forgotten the previous adaptive challenge, so an identical
            # banner must start a complete new negotiation rather than being
            # treated as an ignorable duplicate.
            self.symbol_requests.clear()
            self.last_solicited_token = None
            self.last_solicited_byte = None
        else:
            self.banner_payload = frame.payload
        ack = protocol.encode_frame(protocol.TYPE_ACK, frame.payload)
        if 0x11 <= rom_version <= 0x1B:
            challenge = bytes((0x55, 0xAA, 0x55, 0xAA, 0x55, 0xAA))
            previous: int | None = None
            for expected in challenge:
                while True:
                    remaining = deadline - time.monotonic()
                    if remaining <= 0 or not select.select(
                        [self.fd], [], [], min(remaining, 0.25)
                    )[0]:
                        if remaining <= 0:
                            raise SessionError("timeout during adaptive handshake")
                        continue
                    data = os.read(self.fd, 1)
                    if not data:
                        raise SessionError("serial EOF during adaptive handshake")
                    self.logs.rx(data)
                    self.raw_rx.extend(data)
                    if data[0] == 0xF0:
                        detail = bytearray()
                        while len(detail) < 2:
                            if not select.select([self.fd], [], [], 0.5)[0]:
                                raise SessionError("short adaptive mismatch telemetry")
                            part = os.read(self.fd, 2 - len(detail))
                            if not part:
                                raise SessionError("EOF in adaptive mismatch telemetry")
                            self.logs.rx(part)
                            self.raw_rx.extend(part)
                            detail.extend(part)
                        self.handshake_mismatches.append((detail[0], detail[1]))
                        continue
                    if previous is not None and data[0] == previous:
                        write_all(self.fd, data, deadline, "repeated adaptive symbol")
                        self.logs.tx(data)
                        self.raw_tx.extend(data)
                        continue
                    if data[0] != expected:
                        continue
                    write_all(self.fd, data, deadline, "adaptive handshake symbol")
                    self.logs.tx(data)
                    self.raw_tx.extend(data)
                    previous = expected
                    break
            self.encoded_host_tx = True
            self.host_symbol_repetitions = 7 if 0x12 <= rom_version <= 0x1B else 1
            self.solicited_host_tx = rom_version >= 0x14
            return
        if rom_version == 0x10:
            # The stop-and-wait ROM transmits each expected ACK byte as a
            # challenge and advances only after the host echoes it correctly.
            # Ignore corrupt challenges; the ROM retries each byte eight times.
            previous: int | None = None
            for expected in ack:
                while True:
                    remaining = deadline - time.monotonic()
                    if remaining <= 0 or not select.select(
                        [self.fd], [], [], min(remaining, 0.25)
                    )[0]:
                        if remaining <= 0:
                            raise SessionError("timeout during stop-and-wait ACK")
                        continue
                    data = os.read(self.fd, 1)
                    if not data:
                        raise SessionError("serial EOF during stop-and-wait ACK")
                    self.logs.rx(data)
                    self.raw_rx.extend(data)
                    if previous is not None and data[0] == previous:
                        # Juku did not receive the preceding echo and repeated
                        # its challenge.  Echo it again without advancing the
                        # host-side expected-byte cursor.
                        write_all(
                            self.fd, data, deadline,
                            "repeated stop-and-wait ACK byte",
                        )
                        self.logs.tx(data)
                        self.raw_tx.extend(data)
                        continue
                    if data[0] != expected:
                        continue
                    write_all(self.fd, data, deadline, "stop-and-wait ACK byte")
                    self.logs.tx(data)
                    self.raw_tx.extend(data)
                    previous = expected
                    break
            return
        # Robust-ROM v0F scans a bounded stream for one exact ACK.  Repeating
        # the independently framed ACK gives a noisy/turnaround-sensitive link
        # another synchronization opportunity without changing older ROMs.
        ack_repetitions = 4 if rom_version == 0x0F else 1
        ack_stream = ack * ack_repetitions
        if rom_version == 0x0F:
            # CS00015's CP2102/MAX3232 harness passed stop-and-wait loopback
            # but corrupted dense host-to-Juku bursts.  A 2 ms launch cadence
            # leaves roughly one character time idle at 9600 baud while
            # remaining inside the ROM's inter-byte scan window.
            for byte in ack_stream:
                write_all(self.fd, bytes((byte,)), deadline, "paced banner ACK")
                time.sleep(0.006)
        else:
            write_all(self.fd, ack_stream, deadline, "banner ACK")
        self.logs.tx(ack_stream)
        self.raw_tx.extend(ack_stream)

    def _accept_nano_liveness(self, frame: protocol.Frame) -> None:
        if self.banner_payload is not None:
            raise SessionError("Nano liveness record arrived after the ROM banner")
        if self.nano_liveness is not None:
            raise SessionError("duplicate Nano liveness record")
        if len(frame.payload) != 2:
            raise SessionError("Nano liveness payload length is not two")
        version, flags = frame.payload
        if version != protocol.NANO_LIVENESS_VERSION:
            raise SessionError(
                f"Nano liveness version {version} != "
                f"{protocol.NANO_LIVENESS_VERSION}"
            )
        if flags & ~protocol.NANO_LIVENESS_KNOWN_FLAGS:
            raise SessionError("Nano liveness flags contain unknown bits")
        if not flags & protocol.NANO_LIVENESS_ENABLED:
            raise SessionError("Nano liveness record is not enabled")
        self.nano_liveness = {
            "version": version,
            "flags_hex": f"{flags:02X}",
            "reset_released": bool(flags & protocol.NANO_LIVENESS_RESET_RELEASED),
            "clock_seen": bool(flags & protocol.NANO_LIVENESS_CLOCK_SEEN),
            "mrdc_seen": bool(flags & protocol.NANO_LIVENESS_MRDC_SEEN),
        }

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
        outside_frame_requests = self.request_demux.feed(data)
        if self.solicited_host_tx:
            self.symbol_requests.extend(outside_frame_requests)
        decoded = self.decoder.feed(data)
        self.frames.extend(decoded)
        return decoded

    def run(self) -> None:
        deadline = time.monotonic() + self.timeout
        banner_deadline = min(deadline, time.monotonic() + self.banner_timeout)
        while self.survey is None and not any(
            value & 0x80 for value in self.diagnostic_status
        ):
            active_deadline = (
                deadline if self.banner_payload is not None else banner_deadline
            )
            remaining = active_deadline - time.monotonic()
            if remaining <= 0:
                if self.banner_payload is None:
                    if self.frames:
                        if self.nano_liveness is not None:
                            raise SessionError(
                                "timeout after Nano liveness but before session banner"
                            )
                        raise SessionError(
                            "timeout after protocol frames but before session banner"
                        )
                    raise BannerTimeout("timeout before session banner")
                raise SessionError("timeout before a complete RAM survey")
            for frame in self._read_frames(active_deadline, "before RAM_END"):
                if frame.record_type == protocol.TYPE_NANO_LIVENESS:
                    self._accept_nano_liveness(frame)
                elif frame.record_type == protocol.TYPE_BANNER:
                    self._accept_banner(frame, deadline)
                elif frame.record_type == protocol.TYPE_DIAG_STATUS:
                    if self.banner_payload is None:
                        raise SessionError("diagnostic status arrived without a banner")
                    if len(frame.payload) != 1:
                        raise SessionError("diagnostic status payload length is not one")
                    self.diagnostic_status.append(frame.payload[0])
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
        wire_frame = (
            b"".join(
                bytes((0xAA if byte & (1 << bit) else 0x55,))
                * self.host_symbol_repetitions
                for byte in frame
                for bit in range(7, -1, -1)
            )
            if self.encoded_host_tx
            else frame
        )
        deadline = time.monotonic() + timeout
        if self.solicited_host_tx:
            index = 0
            last_token = None
            last_byte = None
            while index < len(wire_frame):
                while not self.symbol_requests:
                    if time.monotonic() >= deadline:
                        raise SessionError(
                            f"timeout waiting for Juku symbol request during {description}"
                        )
                    self._read_frames(deadline, f"during solicited {description}")
                token = self.symbol_requests.pop(0)
                if last_token is not None and token == last_token:
                    assert last_byte is not None
                    byte = last_byte
                else:
                    byte = wire_frame[index]
                    index += 1
                    last_token = token
                    last_byte = byte
                # The real MAX3232/CP2102 assembly echoes Juku's request into
                # its own 8251 RX. Let the ROM consume and reject that echo
                # before launching the solicited 55/AA response.
                time.sleep(self.loader_guard_seconds)
                write_all(fd=self.fd, data=bytes((byte,)), deadline=deadline,
                          description=f"solicited {description}")
            self.last_solicited_token = last_token
            self.last_solicited_byte = last_byte
        elif self.host_symbol_repetitions > 1:
            # The real CP2102/MAX3232/Juku path can drop characters from a
            # dense burst. Majority coding repairs values, not absent UART
            # characters, so launch each physical symbol with one idle
            # character time between writes.
            for byte in wire_frame:
                write_all(
                    self.fd, bytes((byte,)), deadline,
                    f"paced {description}",
                )
                # T24's 2400-baud physical character occupies about 4.17 ms.
                # Leave a complete idle character between symbols so the
                # marginal Juku receive path cannot lose back-to-back bytes.
                time.sleep(0.006)
        else:
            write_all(self.fd, wire_frame, deadline, description)
        self.logs.tx(wire_frame)
        self.raw_tx.extend(wire_frame)

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
            protocol.TYPE_LOADER_V2_RESULT,
            protocol.TYPE_LOADER_V2_DATA,
            protocol.TYPE_LOADER_V2_RETURN,
        }
        while True:
            # The final physical symbol can disappear after _send_loader_frame
            # has exhausted its input. T25 repeats the same sequence token
            # until that symbol is accepted; continue servicing that exact
            # token while awaiting the logical loader response. A changed
            # token belongs to the next logical frame and remains queued.
            while (
                self.solicited_host_tx
                and self.symbol_requests
                and self.symbol_requests[0] == self.last_solicited_token
            ):
                self.symbol_requests.pop(0)
                assert self.last_solicited_byte is not None
                time.sleep(self.loader_guard_seconds)
                write_all(
                    self.fd,
                    bytes((self.last_solicited_byte,)),
                    time.monotonic() + timeout,
                    f"final-symbol retransmit during {description}",
                )
                self.logs.tx(bytes((self.last_solicited_byte,)))
                self.raw_tx.append(self.last_solicited_byte)
            while cursor < len(self.frames):
                frame = self.frames[cursor]
                cursor += 1
                if frame.record_type == protocol.TYPE_NANO_LIVENESS:
                    self._accept_nano_liveness(frame)
                    continue
                if frame.record_type == protocol.TYPE_BANNER:
                    self._accept_banner(frame, deadline)
                    continue
                if frame.record_type == protocol.TYPE_LOADER_ERROR:
                    if len(frame.payload) != 1:
                        raise SessionError("loader error payload length is not one")
                    status = frame.payload[0]
                    raise LoaderFrameError(status, cursor, description)
                if frame.record_type == expected_type:
                    return frame, cursor
                if frame.record_type in response_types:
                    raise SessionError(
                        f"unexpected loader response 0x{frame.record_type:02X} "
                        f"during {description}"
                    )
            if time.monotonic() >= deadline:
                raise LoaderResponseTimeout(cursor, description)
            self._read_frames(deadline, f"while waiting for {description}")

    def _monitor_heartbeats(
        self,
        cursor: int,
        count: int,
        timeout: float,
        evidence: dict[str, object],
    ) -> None:
        events = evidence["events"]
        assert isinstance(events, list)
        previous_sequence: int | None = None
        evidence["status"] = "waiting"
        while len(events) < count:
            deadline = time.monotonic() + timeout
            while cursor >= len(self.frames):
                if time.monotonic() >= deadline:
                    raise HeartbeatTimeout(
                        f"heartbeat timeout after {len(events)}/{count} records"
                    )
                self._read_frames(deadline, "while waiting for heartbeat")
            frame_index = cursor
            frame = self.frames[cursor]
            cursor += 1
            if frame.record_type != protocol.TYPE_HEARTBEAT:
                raise SessionError(
                    f"unexpected post-RUN frame 0x{frame.record_type:02X} "
                    "while waiting for heartbeat"
                )
            if len(frame.payload) != 2:
                raise SessionError("heartbeat payload length is not two")
            version, sequence = frame.payload
            if version != protocol.HEARTBEAT_VERSION:
                raise SessionError(
                    f"heartbeat version {version} != {protocol.HEARTBEAT_VERSION}"
                )
            if (
                previous_sequence is not None
                and sequence != ((previous_sequence + 1) & 0xFF)
            ):
                raise SessionError(
                    f"heartbeat sequence {sequence:02X} does not follow "
                    f"{previous_sequence:02X}"
                )
            events.append(
                {
                    "index": len(events),
                    "frame_index": frame_index,
                    "sequence": sequence,
                }
            )
            evidence["received"] = len(events)
            previous_sequence = sequence
        evidence["status"] = "complete"

    def _loader_v2_transact(
        self,
        command: bytes,
        transaction: int,
        expected_type: int,
        cursor: int,
        timeout: float,
        description: str,
    ) -> tuple[protocol.Frame, int, int]:
        """Run one bounded, transaction-correlated loader API v2 exchange."""
        for attempt in range(1, self.loader_retries + 1):
            self._send_loader_frame(command, timeout, f"{description} attempt {attempt}")
            try:
                while True:
                    response, cursor = self._wait_loader_frame(
                        expected_type,
                        cursor,
                        timeout,
                        f"{description} response attempt {attempt}",
                    )
                    response_transaction = response.payload[0] if response.payload else None
                    if response_transaction == transaction:
                        break
                if response.record_type == protocol.TYPE_LOADER_V2_RESULT:
                    detail = decode_loader_v2_result(response)
                    if (
                        detail["status"]
                        in (protocol.LOADER_STATUS_BAD_CRC,
                            protocol.LOADER_STATUS_STRONG_CRC)
                        and attempt < self.loader_retries
                    ):
                        continue
                return response, cursor, attempt
            except LoaderFrameError as error:
                cursor = error.cursor
                if (
                    error.status != protocol.LOADER_STATUS_BAD_CRC
                    or attempt >= self.loader_retries
                ):
                    raise
            except LoaderResponseTimeout as error:
                cursor = error.cursor
                if attempt >= self.loader_retries:
                    raise
        raise AssertionError("bounded loader transaction loop fell through")

    def _loader_v2_result_command(
        self,
        record_type: int,
        transaction: int,
        body: bytes,
        cursor: int,
        timeout: float,
        description: str,
    ) -> tuple[dict[str, int], int, int]:
        command = protocol.encode_loader_v2_command(record_type, transaction, body)
        response, cursor, attempts = self._loader_v2_transact(
            command,
            transaction,
            protocol.TYPE_LOADER_V2_RESULT,
            cursor,
            timeout,
            description,
        )
        detail = decode_loader_v2_result(response)
        if detail["command"] != record_type:
            raise SessionError(
                f"loader API v2 {description} response command "
                f"0x{detail['command']:02X} "
                f"!= 0x{record_type:02X}"
            )
        return detail, cursor, attempts

    def _loader_v2_data_command(
        self,
        record_type: int,
        transaction: int,
        body: bytes,
        cursor: int,
        timeout: float,
        description: str,
    ) -> tuple[dict[str, int], bytes, int, int]:
        command = protocol.encode_loader_v2_command(record_type, transaction, body)
        response, cursor, attempts = self._loader_v2_transact(
            command,
            transaction,
            protocol.TYPE_LOADER_V2_DATA,
            cursor,
            timeout,
            description,
        )
        detail, data = decode_loader_v2_data(response)
        if detail["command"] != record_type:
            raise SessionError(
                f"loader API v2 {description} DATA command "
                f"0x{detail['command']:02X} "
                f"!= 0x{record_type:02X}"
            )
        return detail, data, cursor, attempts

    def _run_loader_v2(
        self,
        data: bytes,
        address: int,
        run_address: int | None,
        cursor: int,
        timeout: float,
        heartbeat_count: int,
        heartbeat_timeout: float,
        loader: dict[str, object],
        max_data: int,
    ) -> None:
        end = address + len(data)
        if data and (
            address < protocol.LOADER_V2_LOAD_MIN or end > protocol.LOADER_V2_LOAD_END
        ):
            raise SessionError(
                "loader API v2 upload must fit its 0x4000..0xBFFF window"
            )
        if run_address is not None:
            if data and not address <= run_address < end:
                raise SessionError("run address is outside the uploaded image")
            if not data and not (
                protocol.LOADER_V2_LOAD_MIN <= run_address < protocol.LOADER_V2_LOAD_END
            ):
                raise SessionError("resident run address is outside loader API v2 RAM")

        transaction = 0

        def next_transaction() -> int:
            nonlocal transaction
            value = transaction
            transaction = (transaction + 1) & 0xFF
            return value

        probe_cookie = b"T28\x00\x55\xAA\xC6\xC7"
        probe_tx = next_transaction()
        probe, echoed, cursor, probe_attempts = self._loader_v2_data_command(
            protocol.TYPE_LOADER_V2_PROBE,
            probe_tx,
            probe_cookie,
            cursor,
            timeout,
            "PROBE",
        )
        if probe["status"] != protocol.LOADER_STATUS_OK or echoed != probe_cookie:
            raise SessionError(
                "loader API v2 PROBE did not echo the exact host cookie: "
                f"status={loader_status_name(probe['status'])} "
                f"echo={echoed.hex().upper()}"
            )
        loader["probe"] = {
            "transaction": probe_tx,
            "cookie_hex": probe_cookie.hex().upper(),
            "attempts": probe_attempts,
        }

        if self.loader_votes != protocol.LOADER_V2_BOOT_VOTES:
            config_tx = next_transaction()
            config, cursor, config_attempts = self._loader_v2_result_command(
                protocol.TYPE_LOADER_V2_CONFIG,
                config_tx,
                bytes((self.loader_votes,)),
                cursor,
                timeout,
                "CONFIG",
            )
            if (
                config["status"] != protocol.LOADER_STATUS_OK
                or config["count"] != self.loader_votes
            ):
                raise SessionError(
                    "loader API v2 rejected vote configuration: "
                    f"{loader_status_name(config['status'])}"
                )
            self.host_symbol_repetitions = self.loader_votes
            loader["config"] = {
                "transaction": config_tx,
                "votes": self.loader_votes,
                "attempts": config_attempts,
            }
        else:
            loader["config"] = {
                "transaction": None,
                "votes": protocol.LOADER_V2_BOOT_VOTES,
                "attempts": 0,
            }

        if self.control_read_address is not None and self.control_read_length:
            read_data = bytearray()
            reads: list[dict[str, object]] = []
            for offset in range(0, self.control_read_length, protocol.LOADER_V2_MAX_DATA):
                count = min(
                    protocol.LOADER_V2_MAX_DATA, self.control_read_length - offset
                )
                read_address = self.control_read_address + offset
                read_tx = next_transaction()
                detail, part, cursor, attempts = self._loader_v2_data_command(
                    protocol.TYPE_LOADER_V2_READ,
                    read_tx,
                    read_address.to_bytes(2, "big") + bytes((count,)),
                    cursor,
                    timeout,
                    f"control READ {offset}",
                )
                if detail["status"] != protocol.LOADER_STATUS_OK:
                    raise SessionError(
                        "loader API v2 control READ failed: "
                        f"{loader_status_name(detail['status'])}"
                    )
                read_data.extend(part)
                reads.append(
                    {
                        "transaction": read_tx,
                        "address": f"0x{read_address:04X}",
                        "bytes": count,
                        "attempts": attempts,
                    }
                )
            loader["control_read"] = {
                "address": f"0x{self.control_read_address:04X}",
                "bytes": self.control_read_length,
                "hex": bytes(read_data).hex().upper(),
                "reads": reads,
            }

        if not data and run_address is None:
            loader["status"] = "control_complete"
            return

        chunk_size = max_data
        if self.loader_chunk_size is not None:
            if self.loader_chunk_size > max_data:
                raise SessionError(
                    "requested loader API v2 chunk size "
                    f"{self.loader_chunk_size} exceeds {max_data}"
                )
            chunk_size = self.loader_chunk_size
        loader["ready"]["effective_chunk_bytes"] = chunk_size
        loader["status"] = "loading"
        chunks = loader["chunks"]
        assert isinstance(chunks, list)

        benchmark_passes: list[dict[str, object]] = []
        if self.loader_benchmark_passes > 1:
            loader["benchmark"] = {
                "requested_passes": self.loader_benchmark_passes,
                "completed_passes": 0,
                "verification": "readback" if self.loader_readback else "crc16",
                "passes": benchmark_passes,
            }

        for pass_index in range(self.loader_benchmark_passes):
            pass_started = time.monotonic()
            pass_load_attempts = 0
            pass_verify_attempts = 0
            for index, offset in enumerate(range(0, len(data), chunk_size)):
                chunk_started = time.monotonic()
                chunk = data[offset : offset + chunk_size]
                chunk_address = address + offset
                expected_crc = protocol.crc16_ccitt_false(chunk)
                evidence: dict[str, object] = {
                    "index": index,
                    "pass": pass_index + 1,
                    "address": f"0x{chunk_address:04X}",
                    "bytes": len(chunk),
                    "crc16": f"{expected_crc:04X}",
                    "skipped": False,
                    "verified": False,
                }

                if self.loader_resume:
                    read_tx = next_transaction()
                    read_detail, existing, cursor, read_attempts = self._loader_v2_data_command(
                        protocol.TYPE_LOADER_V2_READ,
                        read_tx,
                        chunk_address.to_bytes(2, "big") + bytes((len(chunk),)),
                        cursor,
                        timeout,
                        f"READ resume pass {pass_index + 1} chunk {index}",
                    )
                    if read_detail["status"] != protocol.LOADER_STATUS_OK:
                        raise SessionError(
                            "loader API v2 resume READ failed: "
                            f"{loader_status_name(read_detail['status'])}"
                        )
                    evidence["resume_read_attempts"] = read_attempts
                    if existing == chunk:
                        evidence["skipped"] = True
                        evidence["verified"] = True
                        evidence["status"] = "already_present"
                        evidence["seconds"] = round(time.monotonic() - chunk_started, 6)
                        chunks.append(evidence)
                        continue

                load_tx = next_transaction()
                load_command = protocol.encode_loader_v2_load(load_tx, chunk_address, chunk)
                response, cursor, load_attempts = self._loader_v2_transact(
                    load_command,
                    load_tx,
                    protocol.TYPE_LOADER_V2_RESULT,
                    cursor,
                    timeout,
                    f"LOAD pass {pass_index + 1} chunk {index}",
                )
                result = decode_loader_v2_result(response)
                pass_load_attempts += load_attempts
                evidence.update(
                    transaction=load_tx,
                    attempts=load_attempts,
                    status=loader_status_name(result["status"]),
                    store_retries=result["store_retries"],
                )
                if result["status"] != protocol.LOADER_STATUS_OK:
                    evidence["seconds"] = round(time.monotonic() - chunk_started, 6)
                    chunks.append(evidence)
                    raise SessionError(
                        f"loader API v2 LOAD pass {pass_index + 1} "
                        f"chunk {index} failed: "
                        f"{loader_status_name(result['status'])}; "
                        f"decoded command=0x{result['command']:02X} "
                        f"length={result['decoded_length']} "
                        f"address=0x{result['address']:04X} count={result['count']} "
                        f"buffer_retries={result['store_retries']}"
                    )
                if (
                    result["command"] != protocol.TYPE_LOADER_V2_LOAD
                    or result["address"] != chunk_address
                    or result["count"] != len(chunk)
                    or result["crc16"] != expected_crc
                ):
                    evidence["seconds"] = round(time.monotonic() - chunk_started, 6)
                    chunks.append(evidence)
                    raise SessionError(
                        f"loader API v2 LOAD pass {pass_index + 1} chunk {index} "
                        "detailed result differs"
                    )

                if self.loader_readback:
                    read_tx = next_transaction()
                    read_detail, readback, cursor, read_attempts = self._loader_v2_data_command(
                        protocol.TYPE_LOADER_V2_READ,
                        read_tx,
                        chunk_address.to_bytes(2, "big") + bytes((len(chunk),)),
                        cursor,
                        timeout,
                        f"READ verify pass {pass_index + 1} chunk {index}",
                    )
                    pass_verify_attempts += read_attempts
                    evidence["readback_attempts"] = read_attempts
                    if (
                        read_detail["status"] != protocol.LOADER_STATUS_OK
                        or readback != chunk
                    ):
                        evidence["seconds"] = round(
                            time.monotonic() - chunk_started, 6
                        )
                        chunks.append(evidence)
                        raise SessionError(
                            "loader API v2 READ verification differs for "
                            f"pass {pass_index + 1} chunk {index}: "
                            f"status={loader_status_name(read_detail['status'])} "
                            f"received={readback.hex().upper()}"
                        )
                    evidence["verified"] = True
                else:
                    crc_tx = next_transaction()
                    crc_detail, cursor, crc_attempts = self._loader_v2_result_command(
                        protocol.TYPE_LOADER_V2_CRC,
                        crc_tx,
                        chunk_address.to_bytes(2, "big") + bytes((len(chunk),)),
                        cursor,
                        timeout,
                        f"CRC verify pass {pass_index + 1} chunk {index}",
                    )
                    pass_verify_attempts += crc_attempts
                    evidence["crc_attempts"] = crc_attempts
                    if (
                        crc_detail["status"] != protocol.LOADER_STATUS_OK
                        or crc_detail["address"] != chunk_address
                        or crc_detail["count"] != len(chunk)
                        or crc_detail["crc16"] != expected_crc
                    ):
                        evidence["seconds"] = round(
                            time.monotonic() - chunk_started, 6
                        )
                        chunks.append(evidence)
                        raise SessionError(
                            "loader API v2 CRC verification differs for "
                            f"pass {pass_index + 1} chunk {index}: "
                            f"status={loader_status_name(crc_detail['status'])} "
                            f"crc={crc_detail['crc16']:04X}"
                        )
                    evidence["verified"] = True
                evidence["seconds"] = round(time.monotonic() - chunk_started, 6)
                chunks.append(evidence)

            if self.loader_benchmark_passes > 1:
                benchmark_passes.append(
                    {
                        "pass": pass_index + 1,
                        "seconds": round(time.monotonic() - pass_started, 6),
                        "load_attempts": pass_load_attempts,
                        "verify_attempts": pass_verify_attempts,
                    }
                )
                benchmark = loader["benchmark"]
                assert isinstance(benchmark, dict)
                benchmark["completed_passes"] = pass_index + 1

        if self.loader_benchmark_passes > 1:
            benchmark = loader["benchmark"]
            assert isinstance(benchmark, dict)
            elapsed = sum(float(item["seconds"]) for item in benchmark_passes)
            load_attempts = sum(
                int(item["load_attempts"]) for item in benchmark_passes
            )
            verify_attempts = sum(
                int(item["verify_attempts"]) for item in benchmark_passes
            )
            store_retries = sum(int(item.get("store_retries", 0)) for item in chunks)
            verified_bytes = len(data) * self.loader_benchmark_passes
            benchmark.update(
                total_seconds=round(elapsed, 6),
                mean_seconds=round(elapsed / self.loader_benchmark_passes, 6),
                payload_bytes_per_pass=len(data),
                verified_payload_bytes=verified_bytes,
                payload_bytes_per_second=round(verified_bytes / elapsed, 6),
                load_attempts=load_attempts,
                load_retries=load_attempts - len(chunks),
                verify_attempts=verify_attempts,
                verify_retries=verify_attempts - len(chunks),
                parser_store_retries=store_retries,
            )

        loader["status"] = "loaded" if data else "resident_ready"
        if run_address is not None:
            run_mode = (
                protocol.LOADER_V2_RUN_CALL
                if self.loader_run_mode == "call"
                else protocol.LOADER_V2_RUN_JUMP
            )
            run_tx = next_transaction()
            execution_id = secrets.randbits(32)
            run_body = (
                run_address.to_bytes(2, "big")
                + bytes((run_mode,))
                + execution_id.to_bytes(4, "big")
            )
            run, cursor, run_attempts = self._loader_v2_result_command(
                protocol.TYPE_LOADER_V2_RUN,
                run_tx,
                run_body,
                cursor,
                timeout,
                "RUN",
            )
            if (
                run["status"] != protocol.LOADER_STATUS_OK
                or run["address"] != run_address
                or run["count"] != run_mode
            ):
                raise SessionError(
                    f"loader API v2 RUN failed: {loader_status_name(run['status'])}"
                )
            run_evidence = loader["run"]
            assert isinstance(run_evidence, dict)
            run_evidence.update(
                acknowledged=True,
                transaction=run_tx,
                attempts=run_attempts,
                mode=self.loader_run_mode,
                execution_id=f"0x{execution_id:08X}",
                return_replays=0,
                returned=False,
            )
            loader["status"] = "run_acknowledged"
            if run_mode == protocol.LOADER_V2_RUN_CALL:
                return_replays = 0
                while True:
                    try:
                        while True:
                            returned, cursor = self._wait_loader_frame(
                                protocol.TYPE_LOADER_V2_RETURN,
                                cursor,
                                timeout,
                                "RETURN",
                            )
                            if returned.payload and returned.payload[0] == run_tx:
                                break
                        break
                    except LoaderResponseTimeout as error:
                        cursor = error.cursor
                        if return_replays >= self.loader_retries - 1:
                            raise
                        return_replays += 1
                        replay, cursor, replay_attempts = self._loader_v2_result_command(
                            protocol.TYPE_LOADER_V2_RUN,
                            run_tx,
                            run_body,
                            cursor,
                            timeout,
                            f"RUN replay {return_replays}",
                        )
                        run_evidence["attempts"] = int(
                            run_evidence["attempts"]
                        ) + replay_attempts
                        if (
                            replay["status"] != protocol.LOADER_STATUS_OK
                            or replay["address"] != run_address
                            or replay["count"] != run_mode
                        ):
                            raise SessionError(
                                "loader API v2 replay-safe RUN failed: "
                                f"{loader_status_name(replay['status'])}"
                            )
                run_evidence["return_replays"] = return_replays
                if len(returned.payload) != 3:
                    raise SessionError(
                        "loader API v2 RETURN payload length is not three"
                    )
                _, return_status, return_a = returned.payload
                if return_status != protocol.LOADER_STATUS_OK:
                    raise SessionError(
                        "loader API v2 returned status "
                        f"{loader_status_name(return_status)}"
                    )
                run_evidence.update(returned=True, return_a=f"0x{return_a:02X}")
                loader["status"] = "returned"

                if self.result_address is not None and self.result_length:
                    result = bytearray()
                    result_reads: list[dict[str, object]] = []
                    for offset in range(0, self.result_length, protocol.LOADER_V2_MAX_DATA):
                        count = min(
                            protocol.LOADER_V2_MAX_DATA, self.result_length - offset
                        )
                        read_address = self.result_address + offset
                        read_tx = next_transaction()
                        detail, part, cursor, read_attempts = self._loader_v2_data_command(
                            protocol.TYPE_LOADER_V2_READ,
                            read_tx,
                            read_address.to_bytes(2, "big") + bytes((count,)),
                            cursor,
                            timeout,
                            f"READ returned result {offset}",
                        )
                        if detail["status"] != protocol.LOADER_STATUS_OK:
                            raise SessionError(
                                "loader API v2 returned-result READ failed: "
                                f"{loader_status_name(detail['status'])}"
                            )
                        result.extend(part)
                        result_reads.append(
                            {
                                "transaction": read_tx,
                                "address": f"0x{read_address:04X}",
                                "bytes": count,
                                "attempts": read_attempts,
                            }
                        )
                    run_evidence["result"] = {
                        "address": f"0x{self.result_address:04X}",
                        "bytes": self.result_length,
                        "hex": bytes(result).hex().upper(),
                        "reads": result_reads,
                    }
                return

            heartbeat = loader["heartbeat"]
            if isinstance(heartbeat, dict):
                try:
                    self._monitor_heartbeats(
                        cursor,
                        heartbeat_count,
                        heartbeat_timeout,
                        heartbeat,
                    )
                except (SessionError, OSError) as error:
                    heartbeat["status"] = "error"
                    heartbeat["error"] = str(error)
                    raise
                loader["status"] = "heartbeat_complete"

    def attach_loader_v2(
        self,
        data: bytes,
        source: str,
        address: int,
        run_address: int | None,
        timeout: float,
        heartbeat_count: int = 0,
        heartbeat_timeout: float = DEFAULT_HEARTBEAT_TIMEOUT,
    ) -> None:
        """Reattach after a host restart without resetting Juku or its RAM.

        The reattached session may upload a new snippet, or operate entirely
        on already-resident RAM through PROBE/READ/RUN.
        """
        self.encoded_host_tx = True
        self.solicited_host_tx = True
        self.host_symbol_repetitions = protocol.LOADER_V2_BOOT_VOTES
        self.symbol_requests.clear()

        # An earlier host may have configured any odd vote count. Remaining
        # silent lets the immutable loader count raw receive timeouts and restore its
        # documented seven-vote baseline. Require nine identical requests:
        # one initial request plus the eight bounded idle periods in the ROM.
        settle_deadline = time.monotonic() + timeout
        repeated = 0
        last_token: int | None = None
        while repeated < 9:
            if time.monotonic() >= settle_deadline:
                raise SessionError(
                    "timeout waiting for loader API v2 idle reset during attach"
                )
            self._read_frames(settle_deadline, "while attaching to loader API v2")
            while self.symbol_requests and repeated < 9:
                token = self.symbol_requests.pop(0)
                if token == last_token:
                    repeated += 1
                else:
                    last_token = token
                    repeated = 1

        # Every accumulated identical token names the same still-outstanding
        # physical symbol. Keep exactly the newest one; replaying the stale
        # timeout history would inject unsolicited duplicates after the ROM has
        # already accepted the first response and advanced.
        self.symbol_requests.clear()
        assert last_token is not None
        self.symbol_requests.append(last_token)

        cursor = len(self.frames)
        resync_tx = 0xFF
        resync, cursor, attempts = self._loader_v2_result_command(
            protocol.TYPE_LOADER_V2_RESYNC,
            resync_tx,
            b"",
            cursor,
            timeout,
            "attach RESYNC",
        )
        if (
            resync["status"] != protocol.LOADER_STATUS_OK
            or resync["count"] != protocol.LOADER_V2_BOOT_VOTES
        ):
            raise SessionError(
                "loader API v2 attach RESYNC failed: "
                f"{loader_status_name(resync['status'])}"
            )
        self.host_symbol_repetitions = protocol.LOADER_V2_BOOT_VOTES

        loader: dict[str, object] = {
            "requested": True,
            "attached": True,
            "control_only": not data,
            "status": "attached",
            "error": None,
            "source": source,
            "sha256": hashlib.sha256(data).hexdigest(),
            "address": f"0x{address:04X}",
            "end_exclusive": f"0x{address + len(data):04X}",
            "bytes": len(data),
            "ready": {
                "api_version": protocol.LOADER_V2_API_VERSION,
                "max_data_bytes": protocol.LOADER_V2_MAX_DATA,
                "api_base": f"0x{protocol.LOADER_API_BASE:04X}",
                "capabilities": f"0x{protocol.LOADER_V2_CAPABILITIES:04X}",
                "load_min": f"0x{protocol.LOADER_V2_LOAD_MIN:04X}",
                "load_end_exclusive": f"0x{protocol.LOADER_V2_LOAD_END:04X}",
                "workspace": f"0x{protocol.LOADER_V2_WORKSPACE_BASE:04X}",
                "stack_top": f"0x{protocol.LOADER_V2_WORKSPACE_END:04X}",
                "default_votes": protocol.LOADER_V2_BOOT_VOTES,
                "guard_ms": self.loader_guard_seconds * 1000.0,
                "retry_limit": self.loader_retries,
                "resume": self.loader_resume,
                "readback": self.loader_readback,
            },
            "attach": {
                "idle_requests": repeated,
                "baseline_token": None if last_token is None else f"0x{last_token:02X}",
                "resync_transaction": resync_tx,
                "resync_attempts": attempts,
            },
            "chunks": [],
            "run": {
                "requested": run_address is not None,
                "address": None if run_address is None else f"0x{run_address:04X}",
                "acknowledged": False,
            },
            "heartbeat": (
                None
                if heartbeat_count == 0
                else {
                    "required": heartbeat_count,
                    "received": 0,
                    "timeout_seconds": heartbeat_timeout,
                    "status": "pending_run",
                    "error": None,
                    "events": [],
                }
            ),
        }
        self.loader = loader
        try:
            self._run_loader_v2(
                data,
                address,
                run_address,
                cursor,
                timeout,
                heartbeat_count,
                heartbeat_timeout,
                loader,
                protocol.LOADER_V2_MAX_DATA,
            )
        except (SessionError, OSError) as error:
            loader["status"] = "error"
            loader["error"] = str(error)
            raise

    def run_loader(
        self,
        data: bytes,
        source: str,
        address: int,
        run_address: int | None,
        timeout: float,
        heartbeat_count: int = 0,
        heartbeat_timeout: float = DEFAULT_HEARTBEAT_TIMEOUT,
        control_only: bool = False,
    ) -> None:
        if self.survey is None and not any(
            value & 0x80 for value in self.diagnostic_status
        ):
            raise SessionError(
                "loader requested before a RAM survey or compact RAM status"
            )
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
            "heartbeat": (
                None
                if heartbeat_count == 0
                else {
                    "required": heartbeat_count,
                    "received": 0,
                    "timeout_seconds": heartbeat_timeout,
                    "status": "pending_run",
                    "error": None,
                    "events": [],
                }
            ),
        }
        if control_only:
            loader["control_only"] = True
        self.loader = loader
        try:
            if not data and not control_only:
                raise SessionError("upload file is empty")
            if data and (
                address < protocol.LOADER_LOAD_MIN or end > protocol.LOADER_LOAD_END
            ):
                raise SessionError(
                    "upload range is outside the loader's 0x4000..0xD7FF window"
                )
            if data and self.survey is not None:
                largest = self.survey.largest_good_window
                if largest is None or address < largest.start or end > largest.end:
                    raise SessionError(
                        "upload range is not inside the largest good RAM window"
                    )
            elif data:
                compact = self.diagnostic_status[-1]
                if address >= 0x4000 and end <= 0x5000 and not compact & 0x01:
                    raise SessionError("compact diagnostic found 4000h RAM unusable")
                if address >= 0xC000 and end <= 0xD000 and not compact & 0x02:
                    raise SessionError("compact diagnostic found C000h RAM unusable")
            if run_address is not None and not address <= run_address < end:
                raise SessionError("run address is outside the uploaded image")

            if self.survey is not None:
                survey_end_index = max(
                    index
                    for index, frame in enumerate(self.frames)
                    if frame.record_type == protocol.TYPE_RAM_END
                )
            else:
                survey_end_index = max(
                    index
                    for index, frame in enumerate(self.frames)
                    if frame.record_type == protocol.TYPE_DIAG_STATUS
                    and len(frame.payload) == 1
                    and frame.payload[0] & 0x80
                )
            cursor = survey_end_index + 1
            self.symbol_requests.clear()
            ready, cursor = self._wait_loader_frame(
                protocol.TYPE_LOADER_READY,
                cursor,
                timeout,
                "LOADER_READY",
            )
            if len(ready.payload) not in (4, 11):
                raise SessionError(
                    "LOADER_READY payload length is neither API v1 nor API v2"
                )
            api_version, max_data, api_hi, api_lo = ready.payload[:4]
            api_base = (api_hi << 8) | api_lo
            if api_version not in (
                protocol.LOADER_API_VERSION,
                protocol.LOADER_V2_API_VERSION,
            ):
                raise SessionError(
                    f"unsupported loader API version {api_version}"
                )
            if not 1 <= max_data <= (
                protocol.LOADER_V2_MAX_DATA
                if api_version == protocol.LOADER_V2_API_VERSION
                else protocol.LOADER_MAX_DATA
            ):
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
            if api_version == protocol.LOADER_V2_API_VERSION:
                if len(ready.payload) != 11:
                    raise SessionError(
                        "loader API v2 READY payload length is not eleven"
                    )
                (
                    _, _, _, _, caps_hi, caps_lo, load_min_page,
                    load_end_page, workspace_page, stack_page, default_votes,
                ) = ready.payload
                capabilities = (caps_hi << 8) | caps_lo
                if capabilities != protocol.LOADER_V2_CAPABILITIES:
                    raise SessionError(
                        f"loader API v2 capabilities {capabilities:04X} != "
                        f"{protocol.LOADER_V2_CAPABILITIES:04X}"
                    )
                if (
                    load_min_page << 8 != protocol.LOADER_V2_LOAD_MIN
                    or load_end_page << 8 != protocol.LOADER_V2_LOAD_END
                    or workspace_page << 8 != protocol.LOADER_V2_WORKSPACE_BASE
                    or stack_page << 8 != protocol.LOADER_V2_WORKSPACE_END
                    or default_votes != protocol.LOADER_V2_BOOT_VOTES
                ):
                    raise SessionError(
                        "loader API v2 advertised memory/transport constants differ"
                    )
                ready_evidence = loader["ready"]
                assert isinstance(ready_evidence, dict)
                ready_evidence.update(
                    capabilities=f"0x{capabilities:04X}",
                    load_min=f"0x{load_min_page << 8:04X}",
                    load_end_exclusive=f"0x{load_end_page << 8:04X}",
                    workspace=f"0x{workspace_page << 8:04X}",
                    stack_top=f"0x{stack_page << 8:04X}",
                    default_votes=default_votes,
                    guard_ms=self.loader_guard_seconds * 1000.0,
                    retry_limit=self.loader_retries,
                    resume=self.loader_resume,
                    readback=self.loader_readback,
                )
                self._run_loader_v2(
                    data,
                    address,
                    run_address,
                    cursor,
                    timeout,
                    heartbeat_count,
                    heartbeat_timeout,
                    loader,
                    max_data,
                )
                return
            if control_only:
                raise SessionError("loader control-only mode requires loader API v2")
            if self.host_symbol_repetitions > 1:
                # Bound retransmission cost and exposure per independently
                # checksummed frame on the repetition-coded physical link.
                max_data = min(max_data, 32)
                loader["ready"]["effective_chunk_bytes"] = max_data
            if self.loader_chunk_size is not None:
                if self.loader_chunk_size > max_data:
                    raise SessionError(
                        f"requested chunk size {self.loader_chunk_size} exceeds {max_data}"
                    )
                max_data = self.loader_chunk_size
                loader["ready"]["effective_chunk_bytes"] = max_data
            loader["status"] = "loading"

            chunks = loader["chunks"]
            assert isinstance(chunks, list)
            for index, offset in enumerate(range(0, len(data), max_data)):
                chunk = data[offset : offset + max_data]
                chunk_address = address + offset
                frame = protocol.encode_load_frame(chunk_address, chunk)
                response = None
                attempts = 0
                while attempts < self.loader_retries:
                    attempts += 1
                    self._send_loader_frame(
                        frame, timeout, f"LOAD chunk {index} attempt {attempts}"
                    )
                    try:
                        response, cursor = self._wait_loader_frame(
                            protocol.TYPE_LOAD_RESULT,
                            cursor,
                            timeout,
                            f"LOAD_RESULT chunk {index} attempt {attempts}",
                        )
                        if len(response.payload) != 1:
                            raise SessionError("LOAD_RESULT payload length is not one")
                        status = response.payload[0]
                        # These statuses reject the command before any RAM
                        # write.  The host has already validated the command,
                        # length, and range, so a real-board occurrence is a
                        # transport corruption which happened to collide in
                        # CRC-8.  Retrying the identical frame is bounded and
                        # side-effect free.
                        if status in (
                            protocol.LOADER_STATUS_BAD_COMMAND,
                            protocol.LOADER_STATUS_BAD_LENGTH,
                            protocol.LOADER_STATUS_BAD_RANGE,
                        ) and attempts < self.loader_retries:
                            response = None
                            continue
                        break
                    except LoaderFrameError as error:
                        cursor = error.cursor
                        if (
                            error.status != protocol.LOADER_STATUS_BAD_CRC
                            or attempts >= self.loader_retries
                        ):
                            raise
                    except LoaderResponseTimeout as error:
                        # T24 and newer bound their physical-symbol receive
                        # waits, discard a partial frame, reset the parser and
                        # return to the loader loop.  A missing/corrupt error
                        # response is therefore safe to recover from by
                        # resending the complete idempotent LOAD frame.
                        cursor = error.cursor
                        if self.banner_payload is None or self.banner_payload[1] < 0x13:
                            raise
                        if attempts >= self.loader_retries:
                            raise
                assert response is not None
                status = response.payload[0]
                chunk_evidence = {
                    "index": index,
                    "address": f"0x{chunk_address:04X}",
                    "bytes": len(chunk),
                    "status": loader_status_name(status),
                }
                if self.host_symbol_repetitions > 1 or attempts > 1:
                    chunk_evidence["attempts"] = attempts
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
                heartbeat = loader["heartbeat"]
                if isinstance(heartbeat, dict):
                    try:
                        self._monitor_heartbeats(
                            cursor,
                            heartbeat_count,
                            heartbeat_timeout,
                            heartbeat,
                        )
                    except (SessionError, OSError) as error:
                        heartbeat["status"] = "error"
                        heartbeat["error"] = str(error)
                        raise
                    loader["status"] = "heartbeat_complete"
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
                "heartbeat_reset_retries_requested": (
                    self.heartbeat_reset_retries_requested
                ),
                "heartbeat_reset_retries_used": self.heartbeat_reset_retries_used,
                "liveness": self.nano_liveness,
            },
            "attempts": self.attempts,
            "image": image,
            "frames": [frame_json(frame) for frame in self.frames],
            "ram_survey": None if self.survey is None else survey_json(self.survey),
            "diagnostic_status": diagnostic_status_json(self.diagnostic_status),
            "host_transport": {
                "encoded_symbols": self.encoded_host_tx,
                "symbol_repetitions": self.host_symbol_repetitions,
                "solicited_guard_ms": self.loader_guard_seconds * 1000.0,
                "loader_retry_limit": self.loader_retries,
                "requested_chunk_size": self.loader_chunk_size,
                "handshake_mismatches": [
                    {"expected": f"{expected:02X}", "received": f"{received:02X}"}
                    for expected, received in self.handshake_mismatches
                ],
            },
            "loader": self.loader,
        }
        return result


def run_session_with_retries(
    session: HostSession,
    reset_retries: int,
    completion: Callable[[], None] | None = None,
    heartbeat_reset_retries: int = 0,
) -> None:
    missing_banner_remaining = reset_retries if session.nano_reset_requested else 0
    heartbeat_remaining = (
        heartbeat_reset_retries if session.nano_reset_requested else 0
    )
    session.heartbeat_reset_retries_requested = heartbeat_reset_retries
    session.heartbeat_reset_retries_used = 0
    number = 0
    while True:
        number += 1
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
            if missing_banner_remaining > 0:
                missing_banner_remaining -= 1
                continue
            raise
        except HeartbeatTimeout as error:
            session.finish_attempt("heartbeat_timeout", str(error))
            if heartbeat_remaining > 0:
                heartbeat_remaining -= 1
                session.heartbeat_reset_retries_used += 1
                continue
            raise
        except (SessionError, OSError) as error:
            session.finish_attempt("error", str(error))
            raise
        session.finish_attempt("ok")
        return


def print_verdict(session: HostSession, logs: SessionLogs) -> None:
    attached = session.banner_payload is None and session.loader is not None
    if not attached:
        assert session.banner_payload is not None
        protocol_version, rom_version, crc_hi, crc_lo = session.banner_payload
    if session.nano_dtr_sequence_completed:
        print(
            "JUKURAVI: nano-reset DTR sequences completed "
            f"{session.nano_dtr_sequences_completed}"
        )
    if session.nano_liveness is not None:
        print(
            "JUKURAVI: nano-liveness "
            f"reset={'yes' if session.nano_liveness['reset_released'] else 'no'} "
            f"clock={'yes' if session.nano_liveness['clock_seen'] else 'no'} "
            f"mrdc={'yes' if session.nano_liveness['mrdc_seen'] else 'no'}"
        )
    if len(session.attempts) > 1:
        print(f"JUKURAVI: session attempts {len(session.attempts)}")
    if session.heartbeat_reset_retries_used:
        print(
            "JUKURAVI: heartbeat reset retries "
            f"{session.heartbeat_reset_retries_used}/"
            f"{session.heartbeat_reset_retries_requested}"
        )
    if attached:
        print("JUKURAVI: attached to running loader API v2 without RESET")
    else:
        print(
            f"JUKURAVI: protocol={protocol_version:02X} rom={rom_version:02X} "
            f"image_crc16={crc_hi:02X}{crc_lo:02X}"
        )
    if session.encoded_host_tx:
        print(
            "JUKURAVI: host transport encoded-symbols "
            f"mismatches={len(session.handshake_mismatches)}"
        )
    if attached:
        pass
    elif session.survey is None:
        status = diagnostic_status_json(session.diagnostic_status)
        assert status is not None
        for name in ("pic", "ppi", "d54", "d55", "d57"):
            print(f"JUKURAVI: {name.upper()} {'PASS' if status[name] else 'FAIL'}")
        for name, address in (("ram_4000", "4000-4FFF"),
                              ("ram_c000", "C000-CFFF")):
            print(f"JUKURAVI: RAM {address} {'PASS' if status[name] else 'FAIL'}")
        if session.loader is None:
            print(f"JUKURAVI: logs {logs.json_path}")
            return
    else:
        survey = session.survey
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
        if session.loader.get("control_only"):
            print("JUKURAVI: loader API v2 control probe complete; RAM unchanged")
        else:
            print(
                f"JUKURAVI: loaded {session.loader['source']} "
                f"bytes={session.loader['bytes']} address={session.loader['address']} "
                f"chunks={len(session.loader['chunks'])}"
            )
        control_read = session.loader.get("control_read")
        if isinstance(control_read, dict):
            print(
                "JUKURAVI: read "
                f"address={control_read['address']} bytes={control_read['bytes']} "
                f"hex={control_read['hex']}"
            )
        run = session.loader.get("run")
        if isinstance(run, dict) and run.get("acknowledged"):
            print(f"JUKURAVI: run acknowledged address={run['address']}")
            if run.get("returned"):
                print(f"JUKURAVI: returned A={run['return_a']}; loader remains active")
        heartbeat = session.loader.get("heartbeat")
        if isinstance(heartbeat, dict):
            events = heartbeat["events"]
            assert isinstance(events, list)
            last_sequence = events[-1]["sequence"] if events else None
            print(
                "JUKURAVI: heartbeat "
                f"{heartbeat['received']}/{heartbeat['required']} "
                f"last={last_sequence:02X} timeout={heartbeat['timeout_seconds']}s"
            )
    print(f"JUKURAVI: logs {logs.json_path}")


def make_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run one framed Jukuravi diagnostic session"
    )
    transport = parser.add_mutually_exclusive_group(required=True)
    transport.add_argument("--port", help="serial device, e.g. /dev/ttyUSB0")
    transport.add_argument(
        "--fd", type=int, help="inherited PTY master descriptor for the cosim harness"
    )
    parser.add_argument(
        "--baud",
        type=int,
        default=DEFAULT_BAUD,
        help=f"serial baud rate (default: {DEFAULT_BAUD})",
    )
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
    parser.add_argument("--log-dir", type=Path, default=DEFAULT_LOG_DIR)
    parser.add_argument("--expect-rom-version", type=parse_hex8)
    parser.add_argument("--expect-crc16", type=parse_hex16)
    parser.add_argument("--load", type=Path, help="binary file to upload after survey")
    parser.add_argument(
        "--attach-loader",
        action="store_true",
        help="reattach to a running loader API v2 without resetting Juku or RAM",
    )
    parser.add_argument(
        "--probe-loader",
        action="store_true",
        help="probe loader API v2 without writing or running code",
    )
    parser.add_argument(
        "--read-address",
        type=parse_hex16,
        help="loader API v2 RAM address to read in control-only mode",
    )
    parser.add_argument(
        "--read-length",
        type=parse_positive_int,
        help="bytes to read from --read-address in control-only mode",
    )
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
        "--run-mode",
        choices=("call", "jump"),
        default="call",
        help="API v2 calls a RET-ending snippet by default; jump is non-returning",
    )
    parser.add_argument(
        "--result-address",
        type=parse_hex16,
        help="RAM result block to READ after a loader API v2 call returns",
    )
    parser.add_argument(
        "--result-length",
        type=parse_positive_int,
        help="bytes to READ from --result-address after return",
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
        "--loader-guard-ms",
        type=parse_nonnegative_float,
        default=SOLICITED_RESPONSE_GUARD_SECONDS * 1000.0,
        help=(
            "delay after each receive request before transmitting "
            f"(default: {SOLICITED_RESPONSE_GUARD_SECONDS * 1000:g} ms)"
        ),
    )
    parser.add_argument(
        "--loader-chunk-size",
        type=parse_positive_int,
        help="host-selected bytes per independently verified loader transaction",
    )
    parser.add_argument(
        "--loader-retries",
        type=parse_positive_int,
        default=DEFAULT_LOADER_RETRIES,
        help=(
            "bounded attempts per idempotent loader transaction "
            f"(default: {DEFAULT_LOADER_RETRIES})"
        ),
    )
    parser.add_argument(
        "--loader-benchmark-passes",
        type=parse_positive_int,
        default=1,
        help="repeat LOAD and verification N times in one configured session",
    )
    parser.add_argument(
        "--loader-votes",
        type=parse_positive_int,
        default=DEFAULT_LOADER_VOTES,
        help=(
            "API v2 physical symbols per logical bit; odd 1..15 "
            f"(default: {DEFAULT_LOADER_VOTES})"
        ),
    )
    parser.add_argument(
        "--loader-resume",
        action="store_true",
        help="read each API v2 target chunk and skip exact bytes already present",
    )
    parser.add_argument(
        "--no-loader-readback",
        action="store_true",
        help="use API v2 CRC verification instead of exact READ verification",
    )
    parser.add_argument(
        "--heartbeat-count",
        type=parse_nonnegative_int,
        default=0,
        help="consecutive post-RUN heartbeat records required (default: disabled)",
    )
    parser.add_argument(
        "--heartbeat-timeout",
        type=float,
        default=DEFAULT_HEARTBEAT_TIMEOUT,
        help="seconds allowed between required heartbeat records",
    )
    parser.add_argument(
        "--heartbeat-reset-retries",
        type=parse_nonnegative_int,
        default=DEFAULT_HEARTBEAT_RESET_RETRIES,
        help="extra full DTR/reset/upload attempts after a heartbeat gap",
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
    if (
        args.loader_votes < protocol.LOADER_V2_MIN_VOTES
        or args.loader_votes > protocol.LOADER_V2_MAX_VOTES
        or not args.loader_votes & 1
    ):
        print("JUKURAVI: --loader-votes must be odd and in 1..15", file=sys.stderr)
        return 2
    if args.loader_resume and args.load is None:
        print("JUKURAVI: --loader-resume requires --load", file=sys.stderr)
        return 2
    if args.loader_benchmark_passes > 1 and (
        args.load is None or not args.load_only or args.loader_resume
    ):
        print(
            "JUKURAVI: --loader-benchmark-passes requires --load and --load-only "
            "without --loader-resume",
            file=sys.stderr,
        )
        return 2
    if args.attach_loader and args.load is None and not (
        args.probe_loader or args.run_address is not None
    ):
        print(
            "JUKURAVI: attach without --load requires --probe-loader, "
            "--read-address, or --run-address",
            file=sys.stderr,
        )
        return 2
    if args.probe_loader and args.load is not None:
        print("JUKURAVI: --probe-loader is a no-upload operation", file=sys.stderr)
        return 2
    if (args.read_address is None) != (args.read_length is None):
        print(
            "JUKURAVI: --read-address and --read-length require each other",
            file=sys.stderr,
        )
        return 2
    if args.read_address is not None and not args.probe_loader:
        print("JUKURAVI: control READ requires --probe-loader", file=sys.stderr)
        return 2
    if args.read_address is not None and (
        args.read_address < protocol.LOADER_V2_LOAD_MIN
        or args.read_address + args.read_length > protocol.LOADER_V2_LOAD_END
    ):
        print("JUKURAVI: control READ must fit 0x4000..0xBFFF", file=sys.stderr)
        return 2
    if args.attach_loader and (
        args.expect_rom_version is not None or args.expect_crc16 is not None
    ):
        print(
            "JUKURAVI: attach cannot re-observe the startup ROM identity; "
            "omit --expect-rom-version/--expect-crc16",
            file=sys.stderr,
        )
        return 2
    if args.heartbeat_timeout <= 0:
        print("JUKURAVI: heartbeat timeout must be positive", file=sys.stderr)
        return 2
    if args.load is None and (
        (args.run_address is not None and not args.attach_loader)
        or args.load_only
        or args.heartbeat_count
    ):
        print(
            "JUKURAVI: --run-address/--load-only/--heartbeat-count requires --load",
            file=sys.stderr,
        )
        return 2
    if args.load_only and args.run_address is not None:
        print("JUKURAVI: --load-only conflicts with --run-address", file=sys.stderr)
        return 2
    if args.load_only and args.heartbeat_count:
        print(
            "JUKURAVI: --load-only conflicts with --heartbeat-count",
            file=sys.stderr,
        )
        return 2
    if (args.result_address is None) != (args.result_length is None):
        print(
            "JUKURAVI: --result-address and --result-length require each other",
            file=sys.stderr,
        )
        return 2
    if args.result_address is not None and (
        args.load_only or args.run_mode != "call"
    ):
        print(
            "JUKURAVI: returned result reads require loader API v2 call mode",
            file=sys.stderr,
        )
        return 2
    if args.result_address is not None and args.load is None and not (
        args.attach_loader and args.run_address is not None
    ):
        print(
            "JUKURAVI: returned result READ requires an uploaded or resident RUN",
            file=sys.stderr,
        )
        return 2
    if args.result_address is not None and (
        args.result_address < protocol.LOADER_V2_LOAD_MIN
        or args.result_address + args.result_length > protocol.LOADER_V2_LOAD_END
    ):
        print("JUKURAVI: returned result READ must fit 0x4000..0xBFFF", file=sys.stderr)
        return 2
    if args.heartbeat_count and args.run_mode != "jump":
        print(
            "JUKURAVI: heartbeat supervision requires --run-mode jump",
            file=sys.stderr,
        )
        return 2
    if args.heartbeat_reset_retries and not args.heartbeat_count:
        print(
            "JUKURAVI: --heartbeat-reset-retries requires --heartbeat-count",
            file=sys.stderr,
        )
        return 2
    if args.heartbeat_reset_retries and (
        args.port is None or args.no_nano_reset
    ):
        print(
            "JUKURAVI: --heartbeat-reset-retries requires reset-enabled --port",
            file=sys.stderr,
        )
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
        load_min = protocol.LOADER_V2_LOAD_MIN if args.attach_loader else protocol.LOADER_LOAD_MIN
        load_end = protocol.LOADER_V2_LOAD_END if args.attach_loader else protocol.LOADER_LOAD_END
        if args.load_address < load_min or upload_end > load_end:
            print(
                "JUKURAVI: upload range must fit "
                f"0x{load_min:04X}..0x{load_end - 1:04X}",
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
    elif args.attach_loader and args.run_address is not None:
        run_address = args.run_address
    try:
        fd, transport = open_transport(args.port, args.fd, args.baud)
    except SessionError as error:
        print(f"JUKURAVI: ERROR {error}", file=sys.stderr)
        return 1
    logs = SessionLogs(args.log_dir, transport)
    nano_reset_requested = (
        args.port is not None and not args.no_nano_reset and not args.attach_loader
    )
    session = HostSession(
        fd,
        logs,
        args.timeout,
        args.banner_timeout,
        args.expect_rom_version,
        args.expect_crc16,
        nano_reset_requested,
        args.loader_guard_ms / 1000.0,
        args.loader_chunk_size,
        args.loader_retries,
        args.loader_votes,
        args.loader_resume,
        not args.no_loader_readback,
        args.run_mode,
        args.result_address,
        0 if args.result_length is None else args.result_length,
        args.read_address,
        0 if args.read_length is None else args.read_length,
        args.loader_benchmark_passes,
    )
    completion = None
    if upload_data is not None:
        completion = lambda: session.run_loader(
            upload_data,
            str(args.load),
            args.load_address,
            run_address,
            args.loader_timeout,
            args.heartbeat_count,
            args.heartbeat_timeout,
        )
    elif args.probe_loader:
        completion = lambda: session.run_loader(
            b"",
            "<loader API v2 control>",
            protocol.LOADER_V2_LOAD_MIN,
            None,
            args.loader_timeout,
            0,
            args.heartbeat_timeout,
            True,
        )
    try:
        if args.attach_loader:
            attach_data = b"" if upload_data is None else upload_data
            attach_source = (
                "<loader API v2 resident control>"
                if args.load is None
                else str(args.load)
            )
            session.begin_attempt(1)
            session.attach_loader_v2(
                attach_data,
                attach_source,
                args.load_address,
                run_address,
                args.loader_timeout,
                args.heartbeat_count,
                args.heartbeat_timeout,
            )
            session.finish_attempt("ok")
        else:
            run_session_with_retries(
                session,
                args.reset_retries,
                completion,
                args.heartbeat_reset_retries,
            )
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
