#!/usr/bin/env python3
"""Serve a Juku system image through the native Janet 1.2 serial protocol.

The stock EktaSoft NetBios client is selected with ``T``/``N`` at the ROM
prompt.  A physical Juku whose keyboard S21 configuration switches define its
station needs only ``TN``.  ``TN0201`` is the fallback when that configuration
byte is zero (and is what the simulator uses): maximum station 02, this Juku
station 01.  This program acts as station 02 by default.
"""

from __future__ import annotations

import argparse
import ctypes
import errno
import os
import select
import sys
import termios
import time
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

SYNC = b"\xe4\xe4"
DATA_CONTROL = 0x07
POLL_CONTROL = 0x0C
ACK_CONTROL = 0x08
LOAD_ADDRESS = 0x0100
SYSTEM_LOAD_ADDRESS = 0xB400
RAM51_LOAD_ADDRESS = 0xB000
SYSTEM_ENTRY = 0xCA00
RAM51_ENTRY = 0xC600
SYSTEM_PREFIX = 0x0200
SYSTEM_BYTES = 0x1A00
RAM51_SYSTEM_BYTES = 0x1E00
RAM51_MAGIC = b"JUKU51\x1a\x00"
RAM_SYSTEM_MAGIC = b"JUKURM1\x1a"
SYSTEM_STAGING_ADDRESS = 0x0180
RECORD_SIZE = 128
DEFAULT_BAUD = 9600


class _Termios2(ctypes.Structure):
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


_TCGETS2 = 0x802C542A
_TCSETS2 = 0x402C542B
_CBAUD = 0x100F
_BOTHER = 0x1000


def _configure_arbitrary_baud(fd: int, baud: int) -> None:
    """Select and verify an exact Linux termios2/BOTHER baud rate."""
    settings = _Termios2()
    libc = ctypes.CDLL(None, use_errno=True)
    if libc.ioctl(fd, _TCGETS2, ctypes.byref(settings)) < 0:
        error = ctypes.get_errno()
        raise OSError(error, os.strerror(error))
    settings.c_cflag = (settings.c_cflag & ~_CBAUD) | _BOTHER
    settings.c_ispeed = baud
    settings.c_ospeed = baud
    if libc.ioctl(fd, _TCSETS2, ctypes.byref(settings)) < 0:
        error = ctypes.get_errno()
        raise OSError(error, os.strerror(error))
    check = _Termios2()
    if libc.ioctl(fd, _TCGETS2, ctypes.byref(check)) < 0:
        error = ctypes.get_errno()
        raise OSError(error, os.strerror(error))
    if check.c_ispeed != baud or check.c_ospeed != baud:
        raise RuntimeError(
            f"serial driver applied {check.c_ispeed}/{check.c_ospeed}, "
            f"expected exact {baud} baud"
        )
    termios.tcflush(fd, termios.TCIOFLUSH)


def xor_bytes(data: bytes) -> int:
    value = 0
    for byte in data:
        value ^= byte
    return value


def frame(destination: int, source: int, control: int,
          payload: bytes = b"") -> bytes:
    """Encode one byte-exact Janet physical frame."""
    header = SYNC + bytes((destination, source, control))
    if control & 0x0C == 0x04:
        body = header + bytes((len(payload),)) + payload
    else:
        if payload:
            raise ValueError("short Janet control frames cannot carry payload")
        body = header
    return body + bytes((xor_bytes(body),))


class FrameParser:
    """Incrementally recover checksum-valid Janet frames from a byte stream."""

    def __init__(self) -> None:
        self.buffer = bytearray()

    def feed(self, data: bytes) -> list[bytes]:
        self.buffer.extend(data)
        result: list[bytes] = []
        while len(self.buffer) >= 6:
            sync_at = self.buffer.find(SYNC)
            if sync_at < 0:
                del self.buffer[:-1]
                break
            if sync_at:
                del self.buffer[:sync_at]
            if len(self.buffer) < 6:
                break
            control = self.buffer[4]
            size = self.buffer[5] + 7 if control & 0x0C == 0x04 else 6
            if len(self.buffer) < size:
                break
            candidate = bytes(self.buffer[:size])
            if xor_bytes(candidate):
                del self.buffer[0]
                continue
            result.append(candidate)
            del self.buffer[:size]
        return result


@dataclass(frozen=True)
class BootImage:
    data: bytes
    load_address: int
    entry: int
    format: str


def system_bootstrap(system: bytes, *, load_address: int = SYSTEM_LOAD_ADDRESS,
                     entry: int = SYSTEM_ENTRY,
                     disable_interrupts: bool = False) -> bytes:
    """Build the 0100h staging executable which relocates a resident image."""
    if not system or len(system) % RECORD_SIZE:
        raise ValueError("system payload must contain complete 128-byte sectors")
    if load_address + len(system) > 0x10000:
        raise ValueError("system payload crosses the 16-bit address space")
    # Optional DI, then LXI H,0180 / LXI D,target / LXI B,length; copy BC
    # bytes; JMP entry. The self-contained RAM BIOS uses DI before reclaiming
    # any former firmware workspace; legacy RomBios images remain byte-exact.
    loop_address = LOAD_ADDRESS + (10 if disable_interrupts else 9)
    stub = (b"\xF3" if disable_interrupts else b"") + bytes((
        0x21, SYSTEM_STAGING_ADDRESS & 0xFF, SYSTEM_STAGING_ADDRESS >> 8,
        0x11, load_address & 0xFF, load_address >> 8,
        0x01, len(system) & 0xFF, len(system) >> 8,
        0x7E, 0x12, 0x23, 0x13, 0x0B, 0x78, 0xB1, 0xC2, 0x09, 0x01,
        0xC3, entry & 0xFF, entry >> 8,
    ))
    stub = bytearray(stub)
    stub[-5:-3] = loop_address.to_bytes(2, "little")
    return bytes(stub).ljust(RECORD_SIZE, b"\x00") + system


def pad_records(image: bytes) -> bytes:
    size = (len(image) + RECORD_SIZE - 1) // RECORD_SIZE * RECORD_SIZE
    return image.ljust(size, b"\x00")


def crc16_ibm(data: bytes) -> int:
    """Return the reflected CRC-16/IBM used by the RAM-system container."""
    crc = 0
    for value in data:
        crc ^= value
        for _ in range(8):
            crc = (crc >> 1) ^ (0xA001 if crc & 1 else 0)
    return crc


def prepare_image(image: bytes, *, load_address: int | None = None,
                  entry: int | None = None) -> BootImage:
    """Recognize Juku resident containers or retain a plain executable."""
    if (load_address is None) != (entry is None):
        raise ValueError("load address and entry must be supplied together")
    if load_address is not None and entry is not None:
        return BootImage(pad_records(image), load_address, entry, "explicit")
    if image.startswith(RAM_SYSTEM_MAGIC):
        if len(image) < SYSTEM_PREFIX:
            raise ValueError("JUKURM1 image is shorter than its header")
        resident_load = int.from_bytes(image[8:10], "little")
        resident_entry = int.from_bytes(image[10:12], "little")
        resident_size = int.from_bytes(image[12:14], "little")
        resident_crc = int.from_bytes(image[14:16], "little")
        end = SYSTEM_PREFIX + resident_size
        if (not resident_size or resident_size % RECORD_SIZE or
                end != len(image)):
            raise ValueError("JUKURM1 resident length is inconsistent")
        system = image[SYSTEM_PREFIX:end]
        if crc16_ibm(system) != resident_crc:
            raise ValueError("JUKURM1 resident CRC-16/IBM mismatch")
        return BootImage(
            system_bootstrap(
                system, load_address=resident_load, entry=resident_entry,
                disable_interrupts=True,
            ),
            LOAD_ADDRESS,
            LOAD_ADDRESS,
            "JUKURM1 self-describing RAM system via staging bootstrap",
        )
    if len(image) == 10240 and image.startswith(RAM51_MAGIC):
        system = image[
            SYSTEM_PREFIX:SYSTEM_PREFIX + RAM51_SYSTEM_BYTES
        ]
        return BootImage(
            system_bootstrap(
                system, load_address=RAM51_LOAD_ADDRESS, entry=RAM51_ENTRY,
            ),
            LOAD_ADDRESS,
            LOAD_ADDRESS,
            "JUKU51 51K RAM-console system via staging bootstrap",
        )
    if (len(image) == 10240 and
            image[:SYSTEM_PREFIX] == bytes((0xE5,)) * SYSTEM_PREFIX and
            image[SYSTEM_PREFIX] == 0xC3):
        # JUKUSYS stores the 52K system-track form: four unused sectors,
        # followed by 52 sectors from CCP=B400h through the BIOS.  The later
        # E5-filled allocation tail (including EKDOSVSW's isolated FFh) is not
        # part of the runnable system.
        system = image[SYSTEM_PREFIX:SYSTEM_PREFIX + SYSTEM_BYTES]
        return BootImage(system_bootstrap(system), LOAD_ADDRESS, LOAD_ADDRESS,
                         "JUKUSYS 52K system track via staging bootstrap")
    return BootImage(pad_records(image), LOAD_ADDRESS, LOAD_ADDRESS,
                     "0100h executable")


def boot_frames(image: bytes, *, load_address: int = LOAD_ADDRESS,
                entry: int = LOAD_ADDRESS, client: int = 1,
                server: int = 2,
                compact_execute: bool = False) -> list[bytes]:
    """Encode the captured Janet bootstrap start/data/end message sequence."""
    if not image:
        raise ValueError("system image is empty")
    if len(image) % RECORD_SIZE:
        raise ValueError("system image size must be a multiple of 128 bytes")
    if not 0 <= entry <= 0xFFFF:
        raise ValueError("entry address is outside 8080 memory")
    if not 0 <= load_address <= 0xFFFF or load_address + len(image) > 0x10000:
        raise ValueError("system image does not fit at its load address")

    messages = [
        frame(client, server, DATA_CONTROL,
              bytes((0x03, 0x05, 0, entry & 0xFF, entry >> 8, 0, 0, 0)))
    ]
    for offset in range(0, len(image), RECORD_SIZE):
        address = load_address + offset
        record = image[offset:offset + RECORD_SIZE]
        # A 128-byte logical bootstrap record is carried by three physical
        # Janet fragments.  02h/04h/09h are first/middle/last markers.
        messages.extend((
            frame(client, server, DATA_CONTROL,
                  bytes((0x02, 0x02, 0, address & 0xFF, address >> 8,
                         0, 0, 0)) + record[:56]),
            frame(client, server, DATA_CONTROL, b"\x04" + record[56:119]),
            frame(client, server, DATA_CONTROL, b"\x09" + record[119:]),
        ))
    messages.append(
        frame(client, server, DATA_CONTROL,
              bytes((0x03, 0x06, 0, entry & 0xFF, entry >> 8, 0, 0, 0)))
    )
    # NETD follows the end descriptor with the 127-byte execute service
    # message observed in the native server capture.  Its first logical byte
    # is 0Fh; the remaining bytes are zero-filled and use the same
    # first/middle/last fragment markers.  Fastboot may ask the unmodified
    # client to accept the semantically equivalent one-byte logical service:
    # 03h is the canonical single-fragment start+end marker, followed by 0Fh.
    if compact_execute:
        messages.append(frame(client, server, DATA_CONTROL, b"\x03\x0f"))
        return messages
    execute = b"\x0f" + bytes(126)
    messages.extend((
        frame(client, server, DATA_CONTROL, b"\x02" + execute[:63]),
        frame(client, server, DATA_CONTROL, b"\x04" + execute[63:126]),
        frame(client, server, DATA_CONTROL, b"\x09" + execute[126:]),
    ))
    return messages


def format_boot_progress(completed_records: int, total_records: int) -> str:
    """Format concise logical-record progress for a bootstrap transfer."""
    if total_records <= 0 or not 0 <= completed_records <= total_records:
        raise ValueError("invalid Janet bootstrap record progress")
    percent = completed_records * 100 // total_records
    remaining = total_records - completed_records
    return (
        f"Janet bootstrap: {percent:3d}% "
        f"({completed_records}/{total_records} records, {remaining} remaining)"
    )


def configure_serial(
    fd: int, baud: int = DEFAULT_BAUD, *, parity: str = "odd",
    stop_bits: int = 1,
) -> None:
    speeds = {
        baud_rate: getattr(termios, constant)
        for baud_rate, constant in (
            (2400, "B2400"),
            (4800, "B4800"),
            (9600, "B9600"),
            (14400, "B14400"),
            (19200, "B19200"),
            (38400, "B38400"),
        )
        if hasattr(termios, constant)
    }
    if parity not in ("none", "odd"):
        raise ValueError(f"unsupported parity: {parity}")
    if stop_bits not in (1, 2):
        raise ValueError(f"unsupported stop-bit count: {stop_bits}")
    speed = speeds.get(baud)
    if speed is None:
        if not 50 <= baud <= 4_000_000:
            raise ValueError(f"unsupported baud rate: {baud}")
        # Establish framing through ordinary termios, then replace only the
        # speed. Readback catches adapters which quantize custom requests.
        configure_serial(
            fd, DEFAULT_BAUD, parity=parity, stop_bits=stop_bits,
        )
        _configure_arbitrary_baud(fd, baud)
        return
    attrs = termios.tcgetattr(fd)
    attrs[0] = termios.IGNPAR
    attrs[1] = 0
    attrs[2] &= ~(termios.CSIZE | termios.CSTOPB | termios.PARENB |
                  termios.PARODD |
                  getattr(termios, "CRTSCTS", 0))
    attrs[2] |= termios.CS8 | termios.CLOCAL | termios.CREAD
    if parity == "odd":
        attrs[2] |= termios.PARENB | termios.PARODD
    if stop_bits == 2:
        attrs[2] |= termios.CSTOPB
    attrs[3] = 0
    attrs[4] = speed
    attrs[5] = speed
    attrs[6][termios.VMIN] = 0
    attrs[6][termios.VTIME] = 1
    termios.tcsetattr(fd, termios.TCSANOW, attrs)
    termios.tcflush(fd, termios.TCIOFLUSH)
    applied = termios.tcgetattr(fd)
    required = termios.CS8 | termios.CLOCAL | termios.CREAD
    if parity == "odd":
        required |= termios.PARENB | termios.PARODD
    forbidden = getattr(termios, "CRTSCTS", 0)
    if stop_bits == 1:
        forbidden |= termios.CSTOPB
    elif not applied[2] & termios.CSTOPB:
        raise RuntimeError(
            f"serial driver did not apply {baud} baud 8"
            f"{'O' if parity == 'odd' else 'N'}{stop_bits} "
            f"(cflag=0x{applied[2]:x})"
        )
    if parity == "none":
        forbidden |= termios.PARENB | termios.PARODD
    if (applied[4] != speed or applied[5] != speed or
            applied[2] & required != required or applied[2] & forbidden):
        raise RuntimeError(
            f"serial driver did not apply {baud} baud "
            f"8{'O' if parity == 'odd' else 'N'}{stop_bits} "
            f"(cflag=0x{applied[2]:x}, ispeed={applied[4]}, "
            f"ospeed={applied[5]})"
        )


def write_all(fd: int, data: bytes, *, stall_timeout: float = 1.0) -> None:
    """Queue all bytes, allowing callers to size the serial-driver stall."""
    if stall_timeout <= 0:
        raise ValueError("serial output stall timeout must be positive")
    view = memoryview(data)
    while view:
        try:
            written = os.write(fd, view)
        except BlockingIOError:
            _, writable, _ = select.select([], [fd], [], stall_timeout)
            if not writable:
                raise TimeoutError("serial output remained blocked")
            continue
        view = view[written:]


def serve(fd: int, image: bytes, *, load_address: int | None = None,
          entry: int | None = None, client: int | None = None,
          server: int | None = None,
          timeout: float = 30.0,
          verbose: bool = True,
          compact_execute: bool = False) -> dict[str, object]:
    """Serve the first matching client through the bootstrap execute service.

    A ``None`` identity is learned from the first checksum-valid bootstrap
    request. Supplying either value retains strict matching for diagnostics.
    """
    parser = FrameParser()
    prepared = prepare_image(image, load_address=load_address, entry=entry)
    active_client: int | None = None
    active_server: int | None = None
    transfer: list[bytes] = []
    next_message = 0
    awaiting_ack = False
    request_seen = False
    start_pending = False
    advance_pending = False
    completion_pending = False
    received_frames = 0
    received_frames_before_request = 0
    sent_frames = 0
    ack_08 = 0
    ack_09 = 0
    total_records = len(prepared.data) // RECORD_SIZE
    last_progress_bucket = -1
    deadline = time.monotonic() + timeout
    request_started_at: float | None = None
    frame_actions: dict[str, int] = {}
    frame_timeline: list[dict[str, object]] = []

    def trace_frame(action: str, packet: bytes, payload: bytes) -> None:
        """Record the stock client's turns after its bootstrap request."""
        if request_started_at is None:
            return
        frame_actions[action] = frame_actions.get(action, 0) + 1
        frame_timeline.append({
            "elapsed_ms": round(
                (time.monotonic() - request_started_at) * 1000, 3,
            ),
            "action": action,
            "destination": packet[2],
            "source": packet[3],
            "control": packet[4],
            "payload_prefix_hex": payload[:4].hex(),
        })

    def boot_stats() -> dict[str, object]:
        if request_started_at is None:
            raise RuntimeError("bootstrap completed without a request timestamp")
        stats: dict[str, object] = {
            "image_bytes": len(prepared.data),
            "sent_frames": sent_frames,
            "received_frames": received_frames,
            "received_frames_before_request": received_frames_before_request,
            "received_frames_after_request": (
                received_frames - received_frames_before_request
            ),
            "frame_actions": frame_actions,
            "frame_timeline": frame_timeline,
            "ack_08": ack_08,
            "ack_09": ack_09,
            "client": int(active_client),
            "server": int(active_server),
            "compact_execute": int(compact_execute),
            "execute_service_bytes": 1 if compact_execute else 127,
            "request_started_at": request_started_at,
            "transfer_seconds": time.monotonic() - request_started_at,
        }
        if verbose:
            actions = ", ".join(
                f"{name}={count}" for name, count in frame_actions.items()
            )
            print(
                "Janet client turns: "
                f"before-request={received_frames_before_request}, "
                f"after-request={received_frames - received_frames_before_request}"
                + (f" ({actions})" if actions else ""),
                flush=True,
            )
        return stats

    if verbose:
        print(
            f"Janet boot image: {prepared.format}, {len(prepared.data)} bytes "
            f"in {total_records} records, load {prepared.load_address:04X}h, "
            f"entry {prepared.entry:04X}h",
            flush=True,
        )
        print("Waiting for a checksum-valid Juku bootstrap request...", flush=True)

    while time.monotonic() < deadline:
        ready, _, _ = select.select([fd], [], [], min(0.1, timeout))
        if not ready:
            continue
        try:
            incoming = os.read(fd, 4096)
        except OSError as error:
            # A freshly-created PTY master reports EIO during the short window
            # before cosim opens its slave.  A physical serial device does not.
            if error.errno == errno.EIO:
                time.sleep(0.001)
                continue
            raise
        if not incoming:
            continue
        for packet in parser.feed(incoming):
            received_frames += 1
            destination, source, control = packet[2:5]
            payload = packet[6:-1] if control & 0x0C == 0x04 else b""
            identity_allowed = (
                source != 0 and destination != 0 and
                (client is None or source == client) and
                (server is None or destination == server)
            )

            if (not request_seen and identity_allowed and
                    control == POLL_CONTROL and not request_seen):
                write_all(fd, frame(source, destination, POLL_CONTROL))
                sent_frames += 1
                continue

            if (request_seen and destination == active_server and
                    source == active_client and
                    control == POLL_CONTROL and start_pending):
                trace_frame("start_poll", packet, payload)
                # The request ACK and first data frame must occupy separate
                # Janet turns.  Back-to-back bytes race the client's receive
                # reset; the next directed poll is its ready indication.
                write_all(fd, transfer[0])
                next_message = 1
                sent_frames += 1
                awaiting_ack = True
                start_pending = False
                if verbose:
                    print(
                        "Janet bootstrap request accepted: station "
                        f"{active_server:02X} -> {active_client:02X}",
                        flush=True,
                    )
                    print(format_boot_progress(0, total_records), flush=True)
                    last_progress_bucket = 0
                continue

            ready_turn = (
                source == active_client and
                ((destination == 0 and control == 0x00) or
                 (destination == active_server and control == POLL_CONTROL))
            )
            if request_seen and ready_turn and completion_pending:
                trace_frame("completion_ready", packet, payload)
                write_all(fd, frame(0, active_server, 0x00))
                sent_frames += 1
                if verbose:
                    print(
                        f"Janet boot complete: {len(prepared.data)} bytes "
                        f"at {prepared.load_address:04X}h, entry "
                        f"{prepared.entry:04X}h, "
                        f"{sent_frames} frames sent",
                        flush=True,
                    )
                return boot_stats()

            if request_seen and ready_turn and advance_pending:
                trace_frame("advance_ready", packet, payload)
                write_all(fd, frame(0, active_server, 0x00))
                write_all(fd, transfer[next_message])
                next_message += 1
                sent_frames += 2
                awaiting_ack = True
                advance_pending = False
                continue

            if (not request_seen and identity_allowed and
                    control & 0x0C == 0x04 and payload[:2] == b"\x03\x04"):
                active_client = source
                active_server = destination
                request_started_at = time.monotonic()
                received_frames_before_request = received_frames - 1
                transfer = boot_frames(
                    prepared.data, load_address=prepared.load_address,
                    entry=prepared.entry, client=active_client,
                    server=active_server, compact_execute=compact_execute,
                )
                request_seen = True
                trace_frame("boot_request", packet, payload)
                write_all(fd, frame(active_client, active_server, ACK_CONTROL))
                sent_frames += 1
                if not awaiting_ack and next_message == 0:
                    start_pending = True
                continue

            if (request_seen and awaiting_ack and
                    destination == active_server and
                    source == active_client and control == ACK_CONTROL):
                trace_frame("ack", packet, payload)
                awaiting_ack = False
                ack_08 += 1
                acknowledged = transfer[next_message - 1]
                if acknowledged[6] == 0x09 and \
                        next_message <= 1 + total_records * 3:
                    completed_records = (next_message - 1) // 3
                    progress_bucket = completed_records * 10 // total_records
                    if verbose and progress_bucket > last_progress_bucket:
                        print(
                            format_boot_progress(completed_records, total_records),
                            flush=True,
                        )
                        last_progress_bucket = progress_bucket
                if next_message == len(transfer):
                    completion_pending = True
                elif acknowledged[6:8] == b"\x03\x06":
                    # After ACKing the 06h end descriptor the client stops
                    # polling and waits for the complete 0Fh execute service.
                    # Emit all remaining execute fragments with explicit
                    # destination-0 line turns, without per-fragment ACKs.
                    while next_message < len(transfer):
                        write_all(fd, frame(0, active_server, 0x00))
                        write_all(fd, transfer[next_message])
                        next_message += 1
                        sent_frames += 2
                    write_all(fd, frame(0, active_server, 0x00))
                    sent_frames += 1
                    if verbose:
                        print(
                            f"Janet boot complete: {len(prepared.data)} bytes "
                            f"at {prepared.load_address:04X}h, entry "
                            f"{prepared.entry:04X}h, "
                            f"{sent_frames} frames sent",
                            flush=True,
                        )
                    return boot_stats()
                else:
                    last_payload_marker = transfer[next_message - 1][6]
                    if last_payload_marker == 0x09:
                        # An acknowledged payload marker 09h closes a logical
                        # record; no extra client poll follows it.
                        write_all(fd, frame(0, active_server, 0x00))
                        write_all(fd, transfer[next_message])
                        next_message += 1
                        sent_frames += 2
                        awaiting_ack = True
                    else:
                        advance_pending = True
                continue

            if (request_seen and awaiting_ack and
                    destination == active_server and
                    source == active_client and
                    control == (ACK_CONTROL | 1)):
                trace_frame("reject", packet, payload)
                # 09h is REJ.  It also hands the line back, so NETD can emit
                # the release marker and retry without waiting for a poll.
                ack_09 += 1
                write_all(fd, frame(0, active_server, 0x00))
                write_all(fd, transfer[next_message - 1])
                sent_frames += 2
                continue

            if request_seen:
                trace_frame("ignored", packet, payload)

    stage = "bootstrap acknowledgements" if request_seen else "boot request"
    raise TimeoutError(
        f"timed out waiting for Janet {stage} "
        f"(sent message {next_message}/{len(transfer)}, "
        f"ACK08={ack_08}, ACK09={ack_09})"
    )


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("serial", help="serial device, for example /dev/ttyUSB0")
    result.add_argument("image", type=Path, help="system .BIN image")
    result.add_argument("--baud", type=int, default=DEFAULT_BAUD,
                        help="line rate (default: 9600, the stock divisor-8 rate)")
    result.add_argument(
        "--client", type=lambda value: int(value, 0),
        help="require this client station (default: learn from request)",
    )
    result.add_argument(
        "--server", type=lambda value: int(value, 0),
        help="require this destination station (default: learn from request)",
    )
    result.add_argument("--load-address", type=lambda value: int(value, 0),
                        help="override automatic image-format load address")
    result.add_argument("--entry", type=lambda value: int(value, 0),
                        help="override automatic image-format entry point")
    result.add_argument("--timeout", type=float, default=120.0)
    return result


def main(argv: Iterable[str] | None = None) -> int:
    args = parser().parse_args(argv)
    image = args.image.read_bytes()
    prepared = prepare_image(image, load_address=args.load_address,
                             entry=args.entry)
    fd = os.open(args.serial, os.O_RDWR | os.O_NOCTTY | os.O_NONBLOCK)
    try:
        configure_serial(fd, args.baud)
        print(
            f"Serving {args.image} ({len(prepared.data)}/{len(image)} bytes, "
            f"{prepared.format}, load {prepared.load_address:04X}h, entry "
            f"{prepared.entry:04X}h) on {args.serial}: "
            f"{args.baud} baud, 8O1, "
            + ("accepting the first valid station pair"
               if args.client is None and args.server is None
               else f"station {args.server!r} -> {args.client!r}"),
            flush=True,
        )
        serve(fd, image, load_address=args.load_address, entry=args.entry,
              client=args.client, server=args.server, timeout=args.timeout)
    finally:
        os.close(fd)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, TimeoutError, ValueError) as error:
        print(f"janet-netboot: {error}", file=sys.stderr)
        raise SystemExit(1)
