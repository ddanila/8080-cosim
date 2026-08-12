#!/usr/bin/env python3
"""Boot diskless Juku CP/M and serve its A: volume over the onboard USART."""

from __future__ import annotations

import argparse
import errno
import os
import select
import sys
import time
from collections.abc import Iterable
from pathlib import Path

from janet_netboot import configure_serial, serve as serve_boot, write_all


SYNC = b"JD"
REPLY_SYNC = b"DJ"
READ = 0x11
WRITE = 0x12
RECORD_SIZE = 128
TRACK_SIZE = 40 * RECORD_SIZE
TRACKS = 80
VOLUME_SIZE = TRACKS * TRACK_SIZE


def checksum(data: bytes) -> int:
    value = 0
    for byte in data:
        value ^= byte
    return value


def record_offset(track: int, sector: int) -> int | None:
    if not 0 <= track < TRACKS or not 1 <= sector <= 40:
        return None
    # BIOS sector translation produces the physical 128-byte record number.
    return track * TRACK_SIZE + (sector - 1) * RECORD_SIZE


def serve_disk(fd: int, volume: bytearray, *, writable: bool = False,
               timeout: float = 120.0, idle_timeout: float | None = None,
               reply_guard: float = 0.002,
               tx_byte_delay: float = 0.0,
               stop_marker: bytes | None = None,
               resume: bool = False,
               verbose: bool = True,
               stats: dict[str, int] | None = None) -> dict[str, int]:
    """Serve the compact CP/M record protocol on an already configured fd."""
    if len(volume) != VOLUME_SIZE:
        raise ValueError(f"network volume is {len(volume)} bytes; expected {VOLUME_SIZE}")
    buffer = bytearray()
    reads = writes = retries = 0
    if stats is None:
        stats = {}
    stats.update(reads=0, writes=0, retries=0)
    last_sequence: int | None = None
    last_request = b""
    last_reply = b""
    marker_buffer = bytearray()
    deadline = time.monotonic() + timeout
    last_activity = time.monotonic()
    # The client changes D57/8251 rate after stock NetBios exits. It waits for
    # this marker before sending the first disk request, preventing bootstrap
    # parser read-ahead from consuming bytes belonging to the resident phase.
    if not resume:
        write_all(fd, b"NR")
    next_ready = time.monotonic() + 0.02
    synchronized = resume

    while time.monotonic() < deadline:
        wait = min(0.1, max(0.0, deadline - time.monotonic()))
        ready, _, _ = select.select([fd], [], [], wait)
        if not ready:
            if not synchronized and time.monotonic() >= next_ready:
                write_all(fd, b"NR")
                next_ready = time.monotonic() + 0.02
            if reads + writes and idle_timeout is not None and \
                    time.monotonic() - last_activity >= idle_timeout:
                break
            continue
        try:
            incoming = os.read(fd, 4096)
        except OSError as error:
            if error.errno == errno.EIO:
                continue
            raise
        if not incoming:
            continue
        buffer.extend(incoming)
        last_activity = time.monotonic()
        if stop_marker:
            marker_buffer.extend(incoming)
            if stop_marker in marker_buffer:
                if verbose:
                    print(f"disk session marker {stop_marker!r} received", flush=True)
                stats["marker"] = 1
                return stats
            keep = max(0, len(stop_marker) - 1)
            if len(marker_buffer) > keep:
                del marker_buffer[:-keep]

        while True:
            start = buffer.find(SYNC)
            if start < 0:
                if buffer[-1:] != SYNC[:1]:
                    buffer.clear()
                else:
                    del buffer[:-1]
                break
            if start:
                del buffer[:start]
            if len(buffer) < 3:
                break
            size = 9 + (RECORD_SIZE if buffer[2] == WRITE else 0)
            if len(buffer) < size:
                break
            request = bytes(buffer[:size])
            del buffer[:size]
            if request[2] not in (READ, WRITE) or checksum(request):
                retries += 1
                stats["retries"] = retries
                continue
            synchronized = True

            operation, sequence, drive = request[2:5]
            track = request[5] | request[6] << 8
            sector = request[7]
            offset = record_offset(track, sector) if drive == 0 else None
            status = 0 if offset is not None and (operation == READ or writable) else 1
            payload = bytes(volume[offset:offset + RECORD_SIZE]) \
                if operation == READ and status == 0 else b""
            body = REPLY_SYNC + bytes((sequence, status)) + payload
            reply = body + bytes((checksum(body),))

            if verbose:
                print(
                    f"disk request op={operation:02X} seq={sequence:02X} "
                    f"drive={drive} track={track} sector={sector} "
                    f"status={status}",
                    flush=True,
                )

            if sequence == last_sequence and request == last_request:
                retries += 1
                stats["retries"] = retries
                reply = last_reply
            elif status == 0 and operation == WRITE:
                volume[offset:offset + RECORD_SIZE] = request[8:8 + RECORD_SIZE]
                writes += 1
                stats["writes"] = writes
            elif status == 0:
                reads += 1
                stats["reads"] = reads
            last_sequence = sequence
            last_request = request
            last_reply = reply
            if reply_guard:
                time.sleep(reply_guard)
            if tx_byte_delay:
                for value in reply:
                    write_all(fd, bytes((value,)))
                    time.sleep(tx_byte_delay)
            else:
                write_all(fd, reply)

    if verbose:
        print(f"Janet disk session: reads={reads}, writes={writes}, retries={retries}",
              flush=True)
    return stats


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("serial", help="serial device, for example /dev/ttyUSB0")
    result.add_argument("system", type=Path, help="juku-net-system.bin")
    result.add_argument("volume", type=Path, help="flat 400 KiB CP/M volume")
    result.add_argument("--boot-baud", type=int, default=9600)
    result.add_argument("--disk-baud", type=int, default=9600)
    result.add_argument("--client", type=lambda value: int(value, 0), default=1,
                        help="NetBios client station (default: 1)")
    result.add_argument("--server", type=lambda value: int(value, 0), default=2,
                        help="host bootstrap station (default: 2)")
    result.add_argument("--writable", action="store_true")
    result.add_argument(
        "--disk-reply-guard-ms", type=float, default=2.0,
        help="request-to-reply half-duplex guard (default: 2 ms)",
    )
    result.add_argument(
        "--disk-tx-byte-delay-ms", type=float, default=0.0,
        help="host-to-Juku delay between disk-reply bytes (default: 0)",
    )
    result.add_argument("--timeout", type=float, default=120.0)
    return result


def main(argv: Iterable[str] | None = None) -> int:
    args = parser().parse_args(argv)
    system = args.system.read_bytes()
    volume = bytearray(args.volume.read_bytes())
    fd = os.open(args.serial, os.O_RDWR | os.O_NOCTTY | os.O_NONBLOCK)
    try:
        configure_serial(fd, args.boot_baud)
        print(
            f"Booting {args.system} at {args.boot_baud} baud, 8O1, "
            f"station {args.server:02X} -> {args.client:02X}",
            flush=True,
        )
        serve_boot(fd, system, client=args.client, server=args.server,
                   timeout=args.timeout)
        configure_serial(fd, args.disk_baud)
        print(f"Serving A: from {args.volume} at {args.disk_baud} baud, 8O1",
              flush=True)
        serve_disk(
            fd,
            volume,
            writable=args.writable,
            timeout=args.timeout,
            reply_guard=args.disk_reply_guard_ms / 1000.0,
            tx_byte_delay=args.disk_tx_byte_delay_ms / 1000.0,
        )
        if args.writable:
            args.volume.write_bytes(volume)
    finally:
        os.close(fd)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, TimeoutError, ValueError) as error:
        print(f"janet-disk-server: {error}", file=sys.stderr)
        raise SystemExit(1)
