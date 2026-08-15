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
from janet_fastboot import FAST_BAUD, serve_fast


SYNC = b"JD"
REPLY_SYNC = b"DJ"
READ = 0x11
WRITE = 0x12
RECORD_SIZE = 128
TRACK_SIZE = 40 * RECORD_SIZE
TRACKS = 80
VOLUME_SIZE = TRACKS * TRACK_SIZE
NATIVE_TRACKS = 160
NATIVE_VOLUME_SIZE = NATIVE_TRACKS * TRACK_SIZE


def checksum(data: bytes) -> int:
    value = 0
    for byte in data:
        value ^= byte
    return value


def record_offset(track: int, sector: int, tracks: int = TRACKS) -> int | None:
    if not 0 <= track < tracks or not 1 <= sector <= 40:
        return None
    # BIOS sector translation produces the physical 128-byte record number.
    return track * TRACK_SIZE + (sector - 1) * RECORD_SIZE


def juku_image_to_volume(image: bytes) -> bytearray:
    """Convert a physical cylinder/head-interleaved .JUK to logical tracks."""
    if len(image) != NATIVE_VOLUME_SIZE:
        raise ValueError(
            f"Juku game image is {len(image)} bytes; expected {NATIVE_VOLUME_SIZE}"
        )
    volume = bytearray(NATIVE_VOLUME_SIZE)
    side_size = TRACKS * TRACK_SIZE
    for cylinder in range(TRACKS):
        for side in range(2):
            source = (cylinder * 2 + side) * TRACK_SIZE
            target = side * side_size + cylinder * TRACK_SIZE
            volume[target:target + TRACK_SIZE] = image[source:source + TRACK_SIZE]
    return volume


def serve_disk(fd: int, volume: bytearray, *, drive_b: bytearray | None = None,
               writable: bool = False,
               timeout: float | None = None,
               idle_timeout: float | None = None,
               reply_guard: float = 0.002,
               tx_byte_delay: float = 0.0,
               stop_marker: bytes | None = None,
               failure_marker: bytes | None = None,
               resume: bool = False,
               verbose: bool = True,
               stats: dict[str, int] | None = None,
               boot_started_at: float | None = None) -> dict[str, int]:
    """Serve the compact CP/M record protocol on an already configured fd."""
    if len(volume) != VOLUME_SIZE:
        raise ValueError(f"network volume is {len(volume)} bytes; expected {VOLUME_SIZE}")
    if drive_b is not None and len(drive_b) != NATIVE_VOLUME_SIZE:
        raise ValueError(
            f"network B: is {len(drive_b)} bytes; expected {NATIVE_VOLUME_SIZE}"
        )
    buffer = bytearray()
    reads = writes = retries = 0
    if stats is None:
        stats = {}
    stats.update(reads=0, writes=0, retries=0,
                 reads_a=0, reads_b=0, writes_a=0, writes_b=0)
    last_sequence: int | None = None
    last_request = b""
    last_reply = b""
    marker_buffer = bytearray()
    deadline = time.monotonic() + timeout if timeout is not None else None
    last_activity = time.monotonic()
    # The client changes D57/8251 rate after stock NetBios exits. It waits for
    # this marker before sending the first disk request, preventing bootstrap
    # parser read-ahead from consuming bytes belonging to the resident phase.
    if not resume:
        write_all(fd, b"NR")
    next_ready = time.monotonic() + 0.02
    synchronized = resume

    while deadline is None or time.monotonic() < deadline:
        wait = 0.1 if deadline is None else min(
            0.1, max(0.0, deadline - time.monotonic()),
        )
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
        if stop_marker or failure_marker:
            marker_buffer.extend(incoming)
            if failure_marker and failure_marker in marker_buffer:
                if verbose:
                    print(f"disk failure marker {failure_marker!r} received",
                          flush=True)
                stats["failure_marker"] = 1
                return stats
            if stop_marker and stop_marker in marker_buffer:
                if verbose:
                    print(f"disk session marker {stop_marker!r} received", flush=True)
                stats["marker"] = 1
                return stats
            keep = max(
                len(stop_marker or b""), len(failure_marker or b""),
            ) - 1
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
                if verbose:
                    print(f"disk invalid request: {request.hex(' ')}", flush=True)
                continue
            synchronized = True

            operation, sequence, drive = request[2:5]
            track = request[5] | request[6] << 8
            sector = request[7]
            selected = volume if drive == 0 else drive_b if drive == 1 else None
            tracks = TRACKS if drive == 0 else NATIVE_TRACKS
            offset = record_offset(track, sector, tracks) \
                if selected is not None else None
            can_write = writable and drive == 0
            status = 0 if offset is not None and \
                (operation == READ or can_write) else 1
            payload = bytes(selected[offset:offset + RECORD_SIZE]) \
                if operation == READ and status == 0 else b""
            body = REPLY_SYNC + bytes((sequence, status)) + payload
            reply = body + bytes((checksum(body),))

            if verbose:
                elapsed = "" if boot_started_at is None else \
                    f" boot+{time.monotonic() - boot_started_at:.3f}s"
                print(
                    f"disk request op={operation:02X} seq={sequence:02X} "
                    f"drive={drive} track={track} sector={sector} "
                    f"status={status}{elapsed}",
                    flush=True,
                )

            if sequence == last_sequence and request == last_request:
                retries += 1
                stats["retries"] = retries
                reply = last_reply
            elif status == 0 and operation == WRITE:
                selected[offset:offset + RECORD_SIZE] = request[8:8 + RECORD_SIZE]
                writes += 1
                stats["writes"] = writes
                stats["writes_a" if drive == 0 else "writes_b"] += 1
            elif status == 0:
                reads += 1
                stats["reads"] = reads
                stats["reads_a" if drive == 0 else "reads_b"] += 1
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
    result.add_argument(
        "--drive-b", type=Path, metavar="GAME.JUK",
        help="read-only native 800 KiB Juku image served as B:",
    )
    result.add_argument("--boot-baud", type=int, default=9600)
    result.add_argument("--disk-baud", type=int, default=9600)
    result.add_argument(
        "--fast-stage1", type=Path,
        help="stock-load this stage at 9600, then bulk-load the system at 19200",
    )
    result.add_argument(
        "--compact-stock-execute", action="store_true",
        help="with --fast-stage1, replace NETD's padded execute service with "
             "the ROM-proven one-fragment form",
    )
    result.add_argument(
        "--client", type=lambda value: int(value, 0),
        help="require this NetBios client (default: learn from request)",
    )
    result.add_argument(
        "--server", type=lambda value: int(value, 0),
        help="require this destination station (default: learn from request)",
    )
    result.add_argument("--writable", action="store_true",
                        help="allow writes to A: (B: remains read-only)")
    result.add_argument(
        "--disk-reply-guard-ms", type=float, default=2.0,
        help="request-to-reply half-duplex guard (default: 2 ms)",
    )
    result.add_argument(
        "--disk-tx-byte-delay-ms", type=float, default=0.0,
        help="host-to-Juku delay between disk-reply bytes (default: 0)",
    )
    result.add_argument(
        "--timeout", type=float, default=120.0,
        help="bootstrap timeout in seconds (default: 120)",
    )
    result.add_argument(
        "--disk-timeout", type=float,
        help="optional total disk-session lifetime in seconds",
    )
    return result


def main(argv: Iterable[str] | None = None) -> int:
    args = parser().parse_args(argv)
    if args.compact_stock_execute and not args.fast_stage1:
        raise ValueError("--compact-stock-execute requires --fast-stage1")
    system = args.system.read_bytes()
    volume = bytearray(args.volume.read_bytes())
    drive_b = juku_image_to_volume(args.drive_b.read_bytes()) \
        if args.drive_b else None
    fd = os.open(args.serial, os.O_RDWR | os.O_NOCTTY | os.O_NONBLOCK)
    try:
        configure_serial(fd, args.boot_baud)
        print(
            f"Booting {args.system} at {args.boot_baud} baud, 8O1, "
            + ("accepting the first valid station pair"
               if args.client is None and args.server is None
               else f"station {args.server!r} -> {args.client!r}")
            + (", compact stock execute"
               if args.compact_stock_execute else ""),
            flush=True,
        )
        if args.fast_stage1:
            if args.boot_baud != 9600 or args.disk_baud != FAST_BAUD:
                raise ValueError(
                    "--fast-stage1 requires --boot-baud 9600 and "
                    f"--disk-baud {FAST_BAUD}"
                )
            boot = serve_fast(
                fd, args.fast_stage1.read_bytes(), system,
                client=args.client, server=args.server,
                stock_timeout=args.timeout,
                compact_stock_execute=args.compact_stock_execute,
            )
            station_server = int(boot["stock_server"])
            station_client = int(boot["stock_client"])
        else:
            boot = serve_boot(
                fd, system, client=args.client, server=args.server,
                timeout=args.timeout,
            )
            station_server = int(boot["server"])
            station_client = int(boot["client"])
        print(
            f"Serving learned station {station_server:02X} -> "
            f"{station_client:02X}",
            flush=True,
        )
        configure_serial(fd, args.disk_baud)
        print(f"Serving A: from {args.volume} at {args.disk_baud} baud, 8O1",
              flush=True)
        if args.drive_b:
            print(f"Serving read-only native B: from {args.drive_b}", flush=True)
        serve_disk(
            fd,
            volume,
            drive_b=drive_b,
            writable=args.writable,
            timeout=args.disk_timeout,
            reply_guard=args.disk_reply_guard_ms / 1000.0,
            tx_byte_delay=args.disk_tx_byte_delay_ms / 1000.0,
            boot_started_at=float(boot["request_started_at"]),
        )
    finally:
        if args.writable:
            args.volume.write_bytes(volume)
            print(f"Saved writable A: to {args.volume}", flush=True)
        os.close(fd)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print("janet-disk-server: stopped by operator", file=sys.stderr)
        raise SystemExit(130)
    except (OSError, TimeoutError, ValueError) as error:
        print(f"janet-disk-server: {error}", file=sys.stderr)
        raise SystemExit(1)
