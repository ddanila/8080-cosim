#!/usr/bin/env python3
"""Exercise dual-drive Janet records and native Juku image conversion."""

from __future__ import annotations

import os
from pathlib import Path
import socket
import sys
import threading

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))

from tools.janet_disk_server import (  # noqa: E402
    NATIVE_VOLUME_SIZE,
    READ,
    RECORD_SIZE,
    REPLY_SYNC,
    TRACK_SIZE,
    VOLUME_SIZE,
    WRITE,
    checksum,
    juku_image_to_volume,
    record_offset,
    serve_disk,
)


def request(operation: int, sequence: int, drive: int, track: int,
            sector: int, payload: bytes = b"") -> bytes:
    body = b"JD" + bytes((operation, sequence, drive, track & 0xFF,
                           track >> 8, sector)) + payload
    return body + bytes((checksum(body),))


def receive_exact(sock: socket.socket, length: int) -> bytes:
    result = bytearray()
    while len(result) < length:
        incoming = sock.recv(length - len(result))
        if not incoming:
            raise AssertionError("disk server closed its socket early")
        result.extend(incoming)
    return bytes(result)


def main() -> int:
    # Each physical cylinder stores side 0 followed by side 1. The logical
    # volume stores all side-0 tracks before all side-1 tracks.
    image = bytearray(NATIVE_VOLUME_SIZE)
    for physical_track in range(160):
        image[physical_track * TRACK_SIZE:(physical_track + 1) * TRACK_SIZE] = \
            bytes((physical_track,)) * TRACK_SIZE
    native = juku_image_to_volume(image)
    if native[0] != 0 or native[79 * TRACK_SIZE] != 158 or \
            native[80 * TRACK_SIZE] != 1 or native[159 * TRACK_SIZE] != 159:
        raise AssertionError("physical .JUK side/cylinder conversion differs")

    drive_a = bytearray(VOLUME_SIZE)
    drive_b = bytearray(NATIVE_VOLUME_SIZE)
    high_offset = record_offset(159, 40, 160)
    assert high_offset is not None
    drive_b[high_offset:high_offset + RECORD_SIZE] = bytes(range(RECORD_SIZE))
    host, client = socket.socketpair()
    stats: dict[str, int] = {}
    errors: list[BaseException] = []

    def worker() -> None:
        try:
            serve_disk(
                host.fileno(), drive_a, drive_b=drive_b, writable=True,
                timeout=2, idle_timeout=0.05, reply_guard=0,
                verbose=False, stats=stats,
            )
        except BaseException as error:
            errors.append(error)

    thread = threading.Thread(target=worker)
    thread.start()
    if receive_exact(client, 2) != b"NR":
        raise AssertionError("resident-ready marker differs")

    client.sendall(request(READ, 1, 1, 159, 40))
    reply = receive_exact(client, 5 + RECORD_SIZE)
    if reply[:4] != REPLY_SYNC + b"\x01\x00" or checksum(reply) or \
            reply[4:-1] != bytes(range(RECORD_SIZE)):
        raise AssertionError("native B: high-track read differs")

    attempted = bytes((0xA5,)) * RECORD_SIZE
    client.sendall(request(WRITE, 2, 1, 159, 40, attempted))
    reply = receive_exact(client, 5)
    if reply[:4] != REPLY_SYNC + b"\x02\x01" or checksum(reply):
        raise AssertionError("read-only B: write was not rejected")
    if drive_b[high_offset:high_offset + RECORD_SIZE] == attempted:
        raise AssertionError("rejected B: write changed the native volume")

    client.sendall(request(WRITE, 3, 0, 2, 1, attempted))
    reply = receive_exact(client, 5)
    if reply[:4] != REPLY_SYNC + b"\x03\x00" or checksum(reply):
        raise AssertionError("writable A: record was rejected")

    thread.join(timeout=2)
    client.close()
    host.close()
    if thread.is_alive() or errors:
        raise AssertionError(f"disk server did not finish cleanly: {errors!r}")
    expected_stats = {
        "reads": 1, "writes": 1, "retries": 0,
        "reads_a": 0, "reads_b": 1, "writes_a": 1, "writes_b": 0,
    }
    if stats != expected_stats:
        raise AssertionError(f"dual-drive counters differ: {stats}")
    print("JANET-DISK-SERVER-TEST: PASS (writable 386K A: + read-only native 784K B:)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
