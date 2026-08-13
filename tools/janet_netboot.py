#!/usr/bin/env python3
"""Serve a Juku system image through the native Janet 1.2 serial protocol.

The stock EktaSoft NetBios client is selected with ``T``/``N`` at the ROM
prompt.  For the default two-station setup type ``TN0201``: maximum station
02, this Juku is station 01.  This program acts as station 02.
"""

from __future__ import annotations

import argparse
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
SYSTEM_ENTRY = 0xCA00
SYSTEM_PREFIX = 0x0200
SYSTEM_BYTES = 0x1A00
SYSTEM_STAGING_ADDRESS = 0x0180
RECORD_SIZE = 128
DEFAULT_BAUD = 9600


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


def system_bootstrap(system: bytes) -> bytes:
    """Build the 0100h staging executable used for a 52K system image."""
    if len(system) != SYSTEM_BYTES:
        raise ValueError("52K system payload must contain 52 128-byte sectors")
    # LXI H,0180 / LXI D,B400 / LXI B,1A00; copy BC bytes; JMP CA00.
    stub = bytes((
        0x21, SYSTEM_STAGING_ADDRESS & 0xFF, SYSTEM_STAGING_ADDRESS >> 8,
        0x11, SYSTEM_LOAD_ADDRESS & 0xFF, SYSTEM_LOAD_ADDRESS >> 8,
        0x01, SYSTEM_BYTES & 0xFF, SYSTEM_BYTES >> 8,
        0x7E, 0x12, 0x23, 0x13, 0x0B, 0x78, 0xB1, 0xC2, 0x09, 0x01,
        0xC3, SYSTEM_ENTRY & 0xFF, SYSTEM_ENTRY >> 8,
    ))
    return stub.ljust(RECORD_SIZE, b"\x00") + system


def pad_records(image: bytes) -> bytes:
    size = (len(image) + RECORD_SIZE - 1) // RECORD_SIZE * RECORD_SIZE
    return image.ljust(size, b"\x00")


def prepare_image(image: bytes, *, load_address: int | None = None,
                  entry: int | None = None) -> BootImage:
    """Recognize JUKUSYS SYSGEN images or retain a plain executable."""
    if (load_address is None) != (entry is None):
        raise ValueError("load address and entry must be supplied together")
    if load_address is not None and entry is not None:
        return BootImage(pad_records(image), load_address, entry, "explicit")
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
                server: int = 2) -> list[bytes]:
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
    # first/middle/last fragment markers.
    execute = b"\x0f" + bytes(126)
    messages.extend((
        frame(client, server, DATA_CONTROL, b"\x02" + execute[:63]),
        frame(client, server, DATA_CONTROL, b"\x04" + execute[63:126]),
        frame(client, server, DATA_CONTROL, b"\x09" + execute[126:]),
    ))
    return messages


def configure_serial(
    fd: int, baud: int = DEFAULT_BAUD, *, parity: str = "odd",
    stop_bits: int = 1,
) -> None:
    speeds = {
        2400: termios.B2400,
        4800: termios.B4800,
        9600: termios.B9600,
        14400: termios.B14400,
        19200: termios.B19200,
        38400: termios.B38400,
    }
    try:
        speed = speeds[baud]
    except KeyError as exc:
        raise ValueError(f"unsupported baud rate: {baud}") from exc
    if parity not in ("none", "odd"):
        raise ValueError(f"unsupported parity: {parity}")
    if stop_bits not in (1, 2):
        raise ValueError(f"unsupported stop-bit count: {stop_bits}")
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


def write_all(fd: int, data: bytes) -> None:
    view = memoryview(data)
    while view:
        try:
            written = os.write(fd, view)
        except BlockingIOError:
            _, writable, _ = select.select([], [fd], [], 1.0)
            if not writable:
                raise TimeoutError("serial output remained blocked")
            continue
        view = view[written:]


def serve(fd: int, image: bytes, *, load_address: int | None = None,
          entry: int | None = None, client: int = 1, server: int = 2,
          timeout: float = 30.0, verbose: bool = True) -> dict[str, int]:
    """Serve one client through the captured bootstrap execute service."""
    parser = FrameParser()
    prepared = prepare_image(image, load_address=load_address, entry=entry)
    transfer = boot_frames(prepared.data, load_address=prepared.load_address,
                           entry=prepared.entry, client=client, server=server)
    next_message = 0
    awaiting_ack = False
    request_seen = False
    start_pending = False
    advance_pending = False
    completion_pending = False
    received_frames = 0
    sent_frames = 0
    ack_08 = 0
    ack_09 = 0
    deadline = time.monotonic() + timeout

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

            if (destination == server and source == client and
                    control == POLL_CONTROL and not request_seen):
                write_all(fd, frame(client, server, POLL_CONTROL))
                sent_frames += 1
                continue

            if (destination == server and source == client and
                    control == POLL_CONTROL and start_pending):
                # The request ACK and first data frame must occupy separate
                # Janet turns.  Back-to-back bytes race the client's receive
                # reset; the next directed poll is its ready indication.
                write_all(fd, transfer[0])
                next_message = 1
                sent_frames += 1
                awaiting_ack = True
                start_pending = False
                if verbose:
                    print("Janet bootstrap request accepted", flush=True)
                continue

            ready_turn = (
                source == client and
                ((destination == 0 and control == 0x00) or
                 (destination == server and control == POLL_CONTROL))
            )
            if request_seen and ready_turn and completion_pending:
                write_all(fd, frame(0, server, 0x00))
                sent_frames += 1
                if verbose:
                    print(
                        f"Janet boot complete: {len(prepared.data)} bytes "
                        f"at {prepared.load_address:04X}h, entry "
                        f"{prepared.entry:04X}h, "
                        f"{sent_frames} frames sent",
                        flush=True,
                    )
                return {
                    "image_bytes": len(prepared.data),
                    "sent_frames": sent_frames,
                    "received_frames": received_frames,
                    "ack_08": ack_08,
                    "ack_09": ack_09,
                }

            if request_seen and ready_turn and advance_pending:
                write_all(fd, frame(0, server, 0x00))
                write_all(fd, transfer[next_message])
                next_message += 1
                sent_frames += 2
                awaiting_ack = True
                advance_pending = False
                continue

            if (destination == server and source == client and
                    control & 0x0C == 0x04 and payload[:2] == b"\x03\x04"):
                request_seen = True
                write_all(fd, frame(client, server, ACK_CONTROL))
                sent_frames += 1
                if not awaiting_ack and next_message == 0:
                    start_pending = True
                continue

            if (request_seen and awaiting_ack and destination == server and
                    source == client and control == ACK_CONTROL):
                awaiting_ack = False
                ack_08 += 1
                if next_message == len(transfer):
                    completion_pending = True
                elif next_message == len(transfer) - 3:
                    # After ACKing the 06h end descriptor the client stops
                    # polling and waits for the complete 0Fh execute service.
                    # NETD therefore emits its three fragments with explicit
                    # destination-0 line turns, without per-fragment ACKs.
                    while next_message < len(transfer):
                        write_all(fd, frame(0, server, 0x00))
                        write_all(fd, transfer[next_message])
                        next_message += 1
                        sent_frames += 2
                    write_all(fd, frame(0, server, 0x00))
                    sent_frames += 1
                    if verbose:
                        print(
                            f"Janet boot complete: {len(prepared.data)} bytes "
                            f"at {prepared.load_address:04X}h, entry "
                            f"{prepared.entry:04X}h, "
                            f"{sent_frames} frames sent",
                            flush=True,
                        )
                    return {
                        "image_bytes": len(prepared.data),
                        "sent_frames": sent_frames,
                        "received_frames": received_frames,
                        "ack_08": ack_08,
                        "ack_09": ack_09,
                    }
                else:
                    last_payload_marker = transfer[next_message - 1][6]
                    if last_payload_marker == 0x09:
                        # An acknowledged payload marker 09h closes a logical
                        # record; no extra client poll follows it.
                        write_all(fd, frame(0, server, 0x00))
                        write_all(fd, transfer[next_message])
                        next_message += 1
                        sent_frames += 2
                        awaiting_ack = True
                    else:
                        advance_pending = True
                continue

            if (request_seen and awaiting_ack and destination == server and
                    source == client and control == (ACK_CONTROL | 1)):
                # 09h is REJ.  It also hands the line back, so NETD can emit
                # the release marker and retry without waiting for a poll.
                ack_09 += 1
                write_all(fd, frame(0, server, 0x00))
                write_all(fd, transfer[next_message - 1])
                sent_frames += 2
                continue

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
    result.add_argument("--client", type=lambda value: int(value, 0), default=1)
    result.add_argument("--server", type=lambda value: int(value, 0), default=2)
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
            f"{args.baud} baud, 8O1, station {args.server:02X} -> "
            f"{args.client:02X}",
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
