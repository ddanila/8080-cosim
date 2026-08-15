#!/usr/bin/env python3
"""Boot diskless Juku CP/M and serve its A: volume over the onboard USART."""

from __future__ import annotations

import argparse
import errno
import hashlib
import json
import os
import select
import sys
import time
import tty
from collections.abc import Callable, Iterable
from datetime import datetime, timezone
from pathlib import Path

try:
    from janet_netboot import configure_serial, serve as serve_boot, write_all
    from janet_fastboot import FAST_BAUD, crc16_ibm, serve_fast
except ModuleNotFoundError:  # Imported as tools.janet_disk_server by tests.
    from tools.janet_netboot import (  # type: ignore[no-redef]
        configure_serial,
        serve as serve_boot,
        write_all,
    )
    from tools.janet_fastboot import (  # type: ignore[no-redef]
        FAST_BAUD, crc16_ibm,
        serve_fast,
    )


SYNC = b"JD"
REPLY_SYNC = b"DJ"
READ = 0x11
WRITE = 0x12
READ_COMPACT = 0x13
READ_AHEAD = 0x14
CONSOLE_POLL = 0x20
CONSOLE_OUT = 0x21
RECORD_SIZE = 128
TRACK_SIZE = 40 * RECORD_SIZE
TRACKS = 80
VOLUME_SIZE = TRACKS * TRACK_SIZE
NATIVE_TRACKS = 160
NATIVE_VOLUME_SIZE = NATIVE_TRACKS * TRACK_SIZE
SECTOR_ORDER = (
    1, 2, 3, 4, 9, 10, 11, 12, 17, 18, 19, 20, 25, 26, 27, 28,
    33, 34, 35, 36, 5, 6, 7, 8, 13, 14, 15, 16, 21, 22, 23, 24,
    29, 30, 31, 32, 37, 38, 39, 40,
)
DIRECTORY_SECTORS = frozenset(SECTOR_ORDER[:32])
READ_AHEAD_RECORDS = 3
V3_RECORD_GUARD = 0.004


def encode_v3_record(payload: bytes, *, deleted_directory: bool) -> bytes:
    """Encode one record with a bounded decoder and no expansion risk."""
    if len(payload) != RECORD_SIZE:
        raise ValueError("v3 record must be exactly 128 bytes")
    if payload.count(payload[:1]) == RECORD_SIZE:
        return b"\x01" + payload[:1]
    if deleted_directory and all(
        payload[index] == 0xE5 for index in range(0, RECORD_SIZE, 32)
    ):
        return b"\x02"
    fill = payload[-1]
    prefix = RECORD_SIZE - 1
    while prefix and payload[prefix - 1] == fill:
        prefix -= 1
    if prefix + 3 < RECORD_SIZE + 1:
        return b"\x03" + bytes((prefix,)) + payload[:prefix] + bytes((fill,))
    return b"\x00" + payload


def boot_with_recovery(
    attempt: Callable[[], dict[str, object]], *,
    prepare_retry: Callable[[], None] | None = None,
    max_restarts: int = 3,
    verbose: bool = True,
) -> dict[str, object]:
    """Retry a complete bootstrap after a reset or abandoned exchange."""
    if max_restarts < 0:
        raise ValueError("max_restarts must not be negative")
    restarts = 0
    while True:
        try:
            result = attempt()
            result["boot_restarts"] = restarts
            return result
        except TimeoutError:
            if restarts >= max_restarts:
                raise
            restarts += 1
            if verbose:
                print(
                    "Bootstrap exchange disappeared; returning to stock "
                    f"request discovery ({restarts}/{max_restarts})",
                    flush=True,
                )
            if prepare_retry is not None:
                prepare_retry()


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
               protocol_version: int = 2,
               verbose: bool = True,
               stats: dict[str, int] | None = None,
               boot_started_at: float | None = None,
               first_request_hook: Callable[
                   [dict[str, int | float]], None
               ] | None = None,
               reply_filter: Callable[[int, bytes], bytes] | None = None,
               console_reply_filter: Callable[[int, int, bytes], bytes] |
               None = None,
               console_protocol: bool = False,
               console_input: bytearray | None = None,
               console_output: bytearray | None = None,
               console_fd: int | None = None,
               ) -> dict[str, int]:
    """Serve the compact CP/M record protocol on an already configured fd."""
    if len(volume) != VOLUME_SIZE:
        raise ValueError(f"network volume is {len(volume)} bytes; expected {VOLUME_SIZE}")
    if drive_b is not None and len(drive_b) != NATIVE_VOLUME_SIZE:
        raise ValueError(
            f"network B: is {len(drive_b)} bytes; expected {NATIVE_VOLUME_SIZE}"
        )
    buffer = bytearray()
    if protocol_version not in (1, 2, 3):
        raise ValueError("protocol_version must be 1, 2, or 3")
    reads = read_records = writes = retries = 0
    if stats is None:
        stats = {}
    stats.update(reads=0, read_records=0, writes=0, retries=0,
                 reads_a=0, reads_b=0, writes_a=0, writes_b=0,
                 request_wire_bytes=0, reply_wire_bytes=0,
                 compact_records=0, compact_bytes_saved=0,
                 read_ahead_records=0, v3_raw=0, v3_fill=0,
                 v3_deleted=0, v3_prefix=0, dropped_replies=0,
                 console_polls=0, console_input_bytes=0,
                 console_output_bytes=0)
    if console_protocol and protocol_version != 3:
        raise ValueError("remote console requires NetDisk protocol 3")
    if console_protocol and console_input is None:
        console_input = bytearray()
    last_sequence: int | None = None
    last_request = b""
    last_reply = b""
    last_reply_chunks: tuple[bytes, ...] = ()
    marker_buffer = bytearray()
    deadline = time.monotonic() + timeout if timeout is not None else None
    last_activity = time.monotonic()
    # The client changes D57/8251 rate after stock NetBios exits. It waits for
    # this marker before sending the first disk request, preventing bootstrap
    # parser read-ahead from consuming bytes belonging to the resident phase.
    if not resume:
        write_all(fd, b"NRN4" if console_protocol else
                  b"NRN3" if protocol_version == 3 else
                  b"NRN2" if protocol_version == 2 else b"NR")
    next_ready = time.monotonic() + 0.02
    synchronized = resume
    first_request_seen = False
    reply_attempts = 0
    console_reply_attempts = 0

    while deadline is None or time.monotonic() < deadline:
        wait = 0.1 if deadline is None else min(
            0.1, max(0.0, deadline - time.monotonic()),
        )
        ready, _, _ = select.select([fd], [], [], wait)
        if not ready:
            if not synchronized and time.monotonic() >= next_ready:
                write_all(
                    fd, b"NRN4" if console_protocol else
                    b"NRN3" if protocol_version == 3 else
                    b"NRN2" if protocol_version == 2 else b"NR",
                )
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
            if request[2] not in (
                    READ, WRITE, READ_COMPACT, READ_AHEAD,
                    CONSOLE_POLL, CONSOLE_OUT,
            ) or \
                    checksum(request):
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
            console_supported = console_protocol and (
                console_input is not None or console_output is not None or
                console_fd is not None
            )
            if operation == CONSOLE_POLL and console_fd is not None:
                ready_console, _, _ = select.select([console_fd], [], [], 0)
                if ready_console:
                    try:
                        console_input.extend(os.read(console_fd, 256))
                    except OSError as error:
                        if error.errno not in (errno.EAGAIN, errno.EWOULDBLOCK):
                            raise
            can_write = writable and drive == 0
            records = 1
            valid_read = operation in (READ, READ_COMPACT, READ_AHEAD) and \
                (operation != READ_COMPACT or protocol_version >= 2) and \
                (operation != READ_AHEAD or protocol_version == 3) and \
                offset is not None
            status = 0 if valid_read or \
                (operation == WRITE and offset is not None and can_write) else 1
            encoding = ""
            reply_chunks: tuple[bytes, ...] = ()
            payload = bytes(selected[offset:offset + RECORD_SIZE]) \
                if valid_read and status == 0 else b""
            if operation == CONSOLE_POLL:
                stats["console_polls"] += 1
                if not console_supported:
                    status = 1
                    payload = b""
                elif console_input:
                    status = 2
                    payload = bytes(console_input[:1])
                else:
                    status = 0
                    payload = b""
                body = REPLY_SYNC + bytes((sequence, status)) + payload
                reply = body + bytes((checksum(body),))
            elif operation == CONSOLE_OUT:
                status = 0 if console_supported else 1
                payload = b""
                body = REPLY_SYNC + bytes((sequence, status))
                reply = body + bytes((checksum(body),))
            elif operation == READ_COMPACT and status == 0:
                if payload and payload.count(payload[:1]) == RECORD_SIZE:
                    status = 2
                    encoding = "fill"
                    encoded = payload[:1]
                elif track == 2 and sector in DIRECTORY_SECTORS and all(
                    payload[index] == 0xE5 for index in range(0, RECORD_SIZE, 32)
                ):
                    status = 3
                    encoding = "deleted-directory"
                    encoded = b""
                else:
                    encoding = "raw"
                    encoded = payload
                saved = max(0, RECORD_SIZE - len(encoded))
                if saved:
                    stats["compact_records"] += 1
                    stats["compact_bytes_saved"] += saved
                payload = encoded
            if operation == READ_AHEAD:
                descriptors = bytearray()
                descriptor_chunks: list[bytes] = []
                records = 0
                if status == 0:
                    order_index = SECTOR_ORDER.index(sector)
                    next_track = track
                    next_index = order_index
                    while records < READ_AHEAD_RECORDS and next_track < tracks:
                        next_sector = SECTOR_ORDER[next_index]
                        next_offset = record_offset(
                            next_track, next_sector, tracks,
                        )
                        assert next_offset is not None and selected is not None
                        record = bytes(
                            selected[next_offset:next_offset + RECORD_SIZE],
                        )
                        encoded = encode_v3_record(
                            record,
                            deleted_directory=(
                                next_track == 2 and
                                next_sector in DIRECTORY_SECTORS
                            ),
                        )
                        descriptors.extend((
                            next_track & 0xFF, next_track >> 8, next_sector,
                        ))
                        descriptors.extend(encoded)
                        descriptor_chunks.append(
                            bytes((next_track & 0xFF, next_track >> 8,
                                   next_sector)) + encoded,
                        )
                        stats[("v3_raw", "v3_fill", "v3_deleted",
                               "v3_prefix")[encoded[0]]] += 1
                        records += 1
                        next_index += 1
                        if next_index == len(SECTOR_ORDER):
                            next_index = 0
                            next_track += 1
                body = REPLY_SYNC + bytes((sequence, status, records)) + \
                    bytes(descriptors)
                reply = body + crc16_ibm(body).to_bytes(2, "big")
                reply_chunks = (
                    body[:5], *descriptor_chunks, reply[-2:],
                )
                payload = bytes(descriptors)
                encoding = f"v3-ahead-{records}"
                stats["read_ahead_records"] += records
            elif operation not in (CONSOLE_POLL, CONSOLE_OUT):
                body = REPLY_SYNC + bytes((sequence, status)) + payload
                reply = body + bytes((checksum(body),))
            stats["request_wire_bytes"] += len(request)
            stats["reply_wire_bytes"] += len(reply)

            request_at = time.monotonic()
            if not first_request_seen:
                first_request_seen = True
                if first_request_hook is not None:
                    first_request_hook({
                        "elapsed_seconds": (
                            request_at - boot_started_at
                            if boot_started_at is not None else 0.0
                        ),
                        "operation": operation,
                        "sequence": sequence,
                        "drive": drive,
                        "track": track,
                        "sector": sector,
                        "status": 0 if status in (2, 3) else status,
                    })

            if verbose:
                elapsed = "" if boot_started_at is None else \
                    f" boot+{request_at - boot_started_at:.3f}s"
                display_status = 0 if status in (2, 3) else status
                encoding_detail = f" encoding={encoding}" if encoding else ""
                print(
                    f"disk request op={operation:02X} seq={sequence:02X} "
                    f"drive={drive} track={track} sector={sector} "
                    f"status={display_status}{encoding_detail}{elapsed}",
                    flush=True,
                )

            if sequence == last_sequence and request == last_request:
                retries += 1
                stats["retries"] = retries
                reply = last_reply
                reply_chunks = last_reply_chunks
            elif status == 0 and operation == WRITE:
                selected[offset:offset + RECORD_SIZE] = request[8:8 + RECORD_SIZE]
                writes += 1
                stats["writes"] = writes
                stats["writes_a" if drive == 0 else "writes_b"] += 1
            elif status == 0 and operation == CONSOLE_OUT:
                value = request[4]
                if console_output is not None:
                    console_output.append(value)
                if console_fd is not None:
                    write_all(console_fd, bytes((value,)))
                stats["console_output_bytes"] += 1
            elif status == 2 and operation == CONSOLE_POLL:
                assert console_input
                del console_input[0]
                stats["console_input_bytes"] += 1
            elif status in (0, 2, 3):
                reads += 1
                read_records += records
                stats["reads"] = reads
                stats["read_records"] = read_records
                stats["reads_a" if drive == 0 else "reads_b"] += 1
            last_sequence = sequence
            last_request = request
            last_reply = reply
            last_reply_chunks = reply_chunks
            if reply_guard:
                time.sleep(reply_guard)
            reply_attempts += 1
            outgoing = reply_filter(reply_attempts, reply) \
                if reply_filter is not None else reply
            if operation in (CONSOLE_POLL, CONSOLE_OUT) and \
                    console_reply_filter is not None:
                console_reply_attempts += 1
                outgoing = console_reply_filter(
                    console_reply_attempts, operation, outgoing,
                )
            if outgoing == b"":
                stats["dropped_replies"] += 1
                if verbose:
                    print(
                        f"disk reply attempt {reply_attempts} intentionally "
                        "dropped",
                        flush=True,
                    )
                continue
            if len(outgoing) != len(reply):
                raise ValueError("disk reply filter must preserve length")
            if reply_chunks and outgoing != reply:
                lengths = tuple(map(len, reply_chunks))
                rebuilt = []
                position = 0
                for length in lengths:
                    rebuilt.append(outgoing[position:position + length])
                    position += length
                reply_chunks = tuple(rebuilt)
            elif not reply_chunks:
                reply = outgoing
            if reply_chunks:
                write_all(fd, reply_chunks[0])
                for chunk in reply_chunks[1:-1]:
                    write_all(fd, chunk)
                    time.sleep(V3_RECORD_GUARD)
                write_all(fd, reply_chunks[-1])
            elif tx_byte_delay:
                for value in reply:
                    write_all(fd, bytes((value,)))
                    time.sleep(tx_byte_delay)
            else:
                write_all(fd, reply)

    if verbose:
        print(
            f"Janet disk session: read requests={reads}, "
            f"records={read_records}, writes={writes}, retries={retries}",
            flush=True,
        )
    return stats


def write_boot_result(path: Path, report: dict[str, object]) -> None:
    """Atomically persist one physical boot timing result."""
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(json.dumps(report, indent=2) + "\n")
    temporary.replace(path)


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
        "--fast-low-latency-guards", action="store_true",
        help="with compact stock execute, use TX drain plus a 10 ms success "
             "guard",
    )
    result.add_argument(
        "--fast-extension-guard-ms", type=float, default=20.0,
        help="delay before sending the high-speed extension (default: 20 ms)",
    )
    result.add_argument(
        "--fast-stock-handoff-guard-ms", type=float, default=30.0,
        help="after TX drain, allow final 9600-baud bytes to leave the USB "
             "UART (default: 30 ms)",
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
        "--disk-protocol", type=int, choices=(1, 2, 3), default=2,
        help="serve legacy, compact, or CRC/read-ahead records (default: 2; "
             "new clients negotiate down and old clients ignore additions)",
    )
    result.add_argument(
        "--console-pty",
        help="negotiate N4 and mirror CP/M console through this separate PTY "
             "(requires --disk-protocol 3)",
    )
    result.add_argument(
        "--timeout", type=float, default=120.0,
        help="bootstrap timeout in seconds (default: 120)",
    )
    result.add_argument(
        "--boot-restarts", type=int, default=3,
        help="complete bootstrap rediscoveries after timeout/reset (default: 3)",
    )
    result.add_argument(
        "--disk-timeout", type=float,
        help="optional total disk-session lifetime in seconds",
    )
    result.add_argument(
        "--boot-result-json", type=Path,
        help="write timing evidence when the first valid disk request arrives",
    )
    return result


def main(argv: Iterable[str] | None = None) -> int:
    args = parser().parse_args(argv)
    if args.compact_stock_execute and not args.fast_stage1:
        raise ValueError("--compact-stock-execute requires --fast-stage1")
    if args.fast_low_latency_guards and not args.compact_stock_execute:
        raise ValueError(
            "--fast-low-latency-guards requires --compact-stock-execute"
        )
    if args.console_pty and args.disk_protocol != 3:
        raise ValueError("--console-pty requires --disk-protocol 3")
    system = args.system.read_bytes()
    volume = bytearray(args.volume.read_bytes())
    drive_b = juku_image_to_volume(args.drive_b.read_bytes()) \
        if args.drive_b else None
    fast_stage = args.fast_stage1.read_bytes() if args.fast_stage1 else b""
    fd = os.open(args.serial, os.O_RDWR | os.O_NOCTTY | os.O_NONBLOCK)
    console_fd = os.open(
        args.console_pty, os.O_RDWR | os.O_NOCTTY | os.O_NONBLOCK,
    ) if args.console_pty else None
    try:
        if console_fd is not None:
            tty.setraw(console_fd)
        configure_serial(fd, args.boot_baud)
        print(
            f"Booting {args.system} at {args.boot_baud} baud, 8O1, "
            + ("accepting the first valid station pair"
               if args.client is None and args.server is None
               else f"station {args.server!r} -> {args.client!r}")
            + (", compact stock execute"
               if args.compact_stock_execute else "")
            + (", low-latency guards"
               if args.fast_low_latency_guards else ""),
            flush=True,
        )
        if args.fast_stage1:
            if args.boot_baud != 9600 or args.disk_baud != FAST_BAUD:
                raise ValueError(
                    "--fast-stage1 requires --boot-baud 9600 and "
                    f"--disk-baud {FAST_BAUD}"
                )
            def boot_attempt() -> dict[str, object]:
                return serve_fast(
                    fd, fast_stage, system,
                    client=args.client, server=args.server,
                    stock_timeout=args.timeout,
                    compact_stock_execute=args.compact_stock_execute,
                    low_latency_guards=args.fast_low_latency_guards,
                    extension_guard=args.fast_extension_guard_ms / 1000.0,
                    stock_handoff_guard=
                    args.fast_stock_handoff_guard_ms / 1000.0,
                )

            boot = boot_with_recovery(
                boot_attempt,
                prepare_retry=lambda: configure_serial(fd, args.boot_baud),
                max_restarts=args.boot_restarts,
            )
            station_server = int(boot["stock_server"])
            station_client = int(boot["stock_client"])
        else:
            boot = boot_with_recovery(
                lambda: serve_boot(
                    fd, system, client=args.client, server=args.server,
                    timeout=args.timeout,
                ),
                prepare_retry=lambda: configure_serial(fd, args.boot_baud),
                max_restarts=args.boot_restarts,
            )
            station_server = int(boot["server"])
            station_client = int(boot["client"])
        print(
            f"Serving learned station {station_server:02X} -> "
            f"{station_client:02X}",
            flush=True,
        )
        configure_serial(fd, args.disk_baud)
        print(
            f"Serving A: from {args.volume} at {args.disk_baud} baud, 8O1, "
            f"NetDisk v{args.disk_protocol}",
            flush=True,
        )
        if args.drive_b:
            print(f"Serving read-only native B: from {args.drive_b}", flush=True)
        if args.console_pty:
            print(
                f"Remote console negotiated as N4 on {args.console_pty}; "
                "local Juku screen/keyboard remain enabled",
                flush=True,
            )

        def record_first_request(event: dict[str, int | float]) -> None:
            if args.boot_result_json is None:
                return
            report: dict[str, object] = {
                "schema": "juku-janet-boot-result-v1",
                "recorded_at_utc": datetime.now(timezone.utc).isoformat(),
                "serial": str(args.serial),
                "boot_baud": args.boot_baud,
                "disk_baud": args.disk_baud,
                "system": str(args.system),
                "system_sha256": hashlib.sha256(system).hexdigest(),
                "volume": str(args.volume),
                "fast_stage": str(args.fast_stage1)
                if args.fast_stage1 else None,
                "fast_stage_sha256": hashlib.sha256(fast_stage).hexdigest()
                if fast_stage else None,
                "compact_stock_execute": args.compact_stock_execute,
                "fast_low_latency_guards": args.fast_low_latency_guards,
                "fast_extension_guard_ms": args.fast_extension_guard_ms,
                "fast_stock_handoff_guard_ms":
                args.fast_stock_handoff_guard_ms,
                "station_server": station_server,
                "station_client": station_client,
                "bootstrap": {
                    key: value for key, value in boot.items()
                    if key != "request_started_at"
                },
                "first_disk_request": event,
            }
            write_boot_result(args.boot_result_json, report)
            print(f"Saved boot timing to {args.boot_result_json}", flush=True)

        serve_disk(
            fd,
            volume,
            drive_b=drive_b,
            writable=args.writable,
            timeout=args.disk_timeout,
            reply_guard=args.disk_reply_guard_ms / 1000.0,
            tx_byte_delay=args.disk_tx_byte_delay_ms / 1000.0,
            protocol_version=args.disk_protocol,
            boot_started_at=float(boot["request_started_at"]),
            first_request_hook=record_first_request,
            console_protocol=bool(args.console_pty),
            console_fd=console_fd,
        )
    finally:
        if args.writable:
            args.volume.write_bytes(volume)
            print(f"Saved writable A: to {args.volume}", flush=True)
        os.close(fd)
        if console_fd is not None:
            os.close(console_fd)
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
