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
    READ_AHEAD,
    READ_COMPACT,
    RECORD_SIZE,
    REPLY_SYNC,
    TRACK_SIZE,
    VOLUME_SIZE,
    WRITE,
    checksum,
    crc16_ibm,
    encode_v3_record,
    juku_image_to_volume,
    record_offset,
    serve_disk,
    write_boot_result,
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
    if encode_v3_record(b"\xA5" * RECORD_SIZE,
                        deleted_directory=False) != b"\x01\xA5":
        raise AssertionError("v3 uniform-fill encoding differs")
    deleted_encoding = bytearray(range(RECORD_SIZE))
    deleted_encoding[0::32] = b"\xE5" * 4
    if encode_v3_record(bytes(deleted_encoding),
                        deleted_directory=True) != b"\x02":
        raise AssertionError("v3 deleted-directory encoding differs")
    prefixed = bytes(range(10)) + b"\xE5" * (RECORD_SIZE - 10)
    if encode_v3_record(prefixed, deleted_directory=False) != \
            b"\x03\x0A" + bytes(range(10)) + b"\xE5":
        raise AssertionError("v3 prefix/fill encoding differs")
    raw = bytes(range(RECORD_SIZE))
    if encode_v3_record(raw, deleted_directory=False) != b"\x00" + raw:
        raise AssertionError("v3 raw encoding differs")

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
    compact_offset = record_offset(2, 1)
    assert compact_offset is not None
    drive_a[compact_offset:compact_offset + RECORD_SIZE] = b"\xE5" * RECORD_SIZE
    deleted_offset = record_offset(2, 2)
    assert deleted_offset is not None
    deleted = bytearray(range(RECORD_SIZE))
    deleted[0::32] = b"\xE5" * 4
    drive_a[deleted_offset:deleted_offset + RECORD_SIZE] = deleted
    host, client = socket.socketpair()
    stats: dict[str, int] = {}
    first_requests: list[dict[str, int | float]] = []
    errors: list[BaseException] = []

    def worker() -> None:
        try:
            serve_disk(
                host.fileno(), drive_a, drive_b=drive_b, writable=True,
                timeout=2, idle_timeout=0.05, reply_guard=0,
                verbose=False, stats=stats,
                boot_started_at=0.0,
                first_request_hook=first_requests.append,
            )
        except BaseException as error:
            errors.append(error)

    thread = threading.Thread(target=worker)
    thread.start()
    if receive_exact(client, 4) != b"NRN2":
        raise AssertionError("resident-ready marker differs")

    client.sendall(request(READ, 1, 1, 159, 40))
    reply = receive_exact(client, 5 + RECORD_SIZE)
    if reply[:4] != REPLY_SYNC + b"\x01\x00" or checksum(reply) or \
            reply[4:-1] != bytes(range(RECORD_SIZE)):
        raise AssertionError("native B: high-track read differs")

    client.sendall(request(READ_COMPACT, 2, 0, 2, 1))
    reply = receive_exact(client, 6)
    if reply[:4] != REPLY_SYNC + b"\x02\x02" or checksum(reply) or \
            reply[4:-1] != b"\xE5":
        raise AssertionError("compact A: read differs")

    client.sendall(request(READ_COMPACT, 3, 0, 2, 2))
    reply = receive_exact(client, 5)
    if reply[:4] != REPLY_SYNC + b"\x03\x03" or checksum(reply):
        raise AssertionError("deleted-directory A: read differs")

    attempted = bytes((0xA5,)) * RECORD_SIZE
    client.sendall(request(WRITE, 4, 1, 159, 40, attempted))
    reply = receive_exact(client, 5)
    if reply[:4] != REPLY_SYNC + b"\x04\x01" or checksum(reply):
        raise AssertionError("read-only B: write was not rejected")
    if drive_b[high_offset:high_offset + RECORD_SIZE] == attempted:
        raise AssertionError("rejected B: write changed the native volume")

    client.sendall(request(WRITE, 5, 0, 2, 1, attempted))
    reply = receive_exact(client, 5)
    if reply[:4] != REPLY_SYNC + b"\x05\x00" or checksum(reply):
        raise AssertionError("writable A: record was rejected")

    thread.join(timeout=2)
    client.close()
    host.close()
    if thread.is_alive() or errors:
        raise AssertionError(f"disk server did not finish cleanly: {errors!r}")
    expected_stats = {
        "reads": 3, "read_records": 3, "writes": 1, "retries": 0,
        "reads_a": 2, "reads_b": 1, "writes_a": 1, "writes_b": 0,
        "request_wire_bytes": 301, "reply_wire_bytes": 154,
        "compact_records": 2, "compact_bytes_saved": 255,
        "read_ahead_records": 0,
        "v3_raw": 0, "v3_fill": 0, "v3_deleted": 0, "v3_prefix": 0,
        "dropped_replies": 0,
    }
    if stats != expected_stats:
        raise AssertionError(f"dual-drive counters differ: {stats}")
    if len(first_requests) != 1 or first_requests[0]["operation"] != READ or \
            first_requests[0]["drive"] != 1 or \
            first_requests[0]["track"] != 159 or \
            first_requests[0]["sector"] != 40 or \
            first_requests[0]["status"] != 0 or \
            float(first_requests[0]["elapsed_seconds"]) <= 0:
        raise AssertionError(f"first disk request evidence differs: {first_requests}")

    v3_host, v3_client = socket.socketpair()
    v3_stats: dict[str, int] = {}
    v3_errors: list[BaseException] = []

    def v3_worker() -> None:
        try:
            serve_disk(
                v3_host.fileno(), drive_a, timeout=2, idle_timeout=0.05,
                reply_guard=0, protocol_version=3, verbose=False,
                stats=v3_stats,
                reply_filter=lambda attempt, reply: (
                    b"" if attempt == 1 else reply
                ),
            )
        except BaseException as error:
            v3_errors.append(error)

    v3_thread = threading.Thread(target=v3_worker)
    v3_thread.start()
    if receive_exact(v3_client, 4) != b"NRN3":
        raise AssertionError("v3 resident-ready marker differs")
    v3_client.sendall(request(READ_AHEAD, 6, 0, 2, 1))
    expected_body = (
        b"DJ\x06\x00\x03"
        + b"\x02\x00\x01\x01\xA5"
        + b"\x02\x00\x02\x02"
        + b"\x02\x00\x03\x01\x00"
    )
    expected_reply = expected_body + crc16_ibm(expected_body).to_bytes(
        2, "big",
    )
    v3_client.settimeout(0.05)
    try:
        v3_client.recv(1)
    except socket.timeout:
        pass
    else:
        raise AssertionError("empty reply filter did not drop the reply")
    finally:
        v3_client.settimeout(None)
    v3_client.sendall(request(READ_AHEAD, 6, 0, 2, 1))
    reply = receive_exact(v3_client, len(expected_reply))
    if reply != expected_reply:
        raise AssertionError(f"v3 read-ahead reply differs: {reply.hex()}")
    v3_client.sendall(request(READ_AHEAD, 6, 0, 2, 1))
    if receive_exact(v3_client, len(expected_reply)) != expected_reply:
        raise AssertionError("v3 duplicate request did not replay exactly")
    v3_thread.join(timeout=2)
    v3_client.close()
    v3_host.close()
    if v3_thread.is_alive() or v3_errors:
        raise AssertionError(f"v3 disk server did not finish: {v3_errors!r}")
    if v3_stats["reads"] != 1 or v3_stats["read_records"] != 3 or \
            v3_stats["retries"] != 2 or \
            v3_stats["dropped_replies"] != 1:
        raise AssertionError(f"v3 counters differ: {v3_stats}")

    result = ROOT / ".obj" / "janet-disk-server-result-test.json"
    result.parent.mkdir(exist_ok=True)
    write_boot_result(result, {"schema": "test", "elapsed_seconds": 1.25})
    if result.read_text() != \
            '{\n  "schema": "test",\n  "elapsed_seconds": 1.25\n}\n':
        raise AssertionError("boot timing JSON differs")
    result.unlink()
    print("JANET-DISK-SERVER-TEST: PASS (writable 386K A: + read-only native 784K B:)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
