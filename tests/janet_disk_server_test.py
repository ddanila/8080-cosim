#!/usr/bin/env python3
"""Exercise dual-drive Janet records and native Juku image conversion."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import socket
import sys
import threading
from datetime import date, datetime, timezone

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))

from tools.janet_disk_server import (  # noqa: E402
    CAPABILITY_QUERY,
    BootSlot,
    CONSOLE_OUT,
    CONSOLE_POLL,
    CPM_EPOCH,
    HostClock,
    NATIVE_VOLUME_SIZE,
    READ,
    READ_AHEAD,
    READ_COMPACT,
    RECORD_SIZE,
    REPLY_SYNC,
    STATUS_REPORT,
    DIAG_REPORT,
    TRACK_SIZE,
    TIME_GET,
    TIME_SET,
    VolumeMedia,
    VOLUME_SIZE,
    WRITE,
    WRITE_V3,
    checksum,
    boot_slots_with_recovery,
    crc16_ibm,
    encode_v3_record,
    juku_image_to_volume,
    order_boot_slots,
    record_offset,
    serve_disk,
    write_boot_result,
    write_boot_slot_state,
    write_volume,
    validate_boot_manifest,
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
        "dropped_replies": 0, "short_replies": 0, "extra_reply_bytes": 0,
        "console_polls": 0, "console_input_bytes": 0,
        "console_output_bytes": 0,
        "clock_gets": 0, "clock_sets": 0, "clock_failures": 0,
        "status_reports": 0,
        "diag_reports": 0,
        "capability_queries": 0,
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
                v3_host.fileno(), drive_a, writable=True,
                timeout=2, idle_timeout=0.05,
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
    written = bytes((0x5A,)) * RECORD_SIZE
    v3_client.sendall(request(WRITE_V3, 7, 0, 4, 9, written))
    write_body = REPLY_SYNC + b"\x07\x00\x00"
    write_reply = write_body + crc16_ibm(write_body).to_bytes(2, "big")
    if receive_exact(v3_client, len(write_reply)) != write_reply:
        raise AssertionError("v3 write-through reply differs")
    write_offset = record_offset(4, 9)
    assert write_offset is not None
    if drive_a[write_offset:write_offset + RECORD_SIZE] != written:
        raise AssertionError("v3 write-through did not update the volume")
    v3_thread.join(timeout=2)
    v3_client.close()
    v3_host.close()
    if v3_thread.is_alive() or v3_errors:
        raise AssertionError(f"v3 disk server did not finish: {v3_errors!r}")
    if v3_stats["reads"] != 1 or v3_stats["read_records"] != 3 or \
            v3_stats["writes"] != 1 or \
            v3_stats["retries"] != 2 or \
            v3_stats["dropped_replies"] != 1:
        raise AssertionError(f"v3 counters differ: {v3_stats}")

    # A replacement physical server joins an already-running client without
    # emitting the NRN capability marker which belongs only to initial boot.
    resume_host, resume_client = socket.socketpair()
    resume_errors: list[BaseException] = []
    resume_console_confirmations: list[dict[str, int]] = []

    def resume_worker() -> None:
        try:
            serve_disk(
                resume_host.fileno(), drive_a, timeout=2, idle_timeout=0.05,
                reply_guard=0, protocol_version=3, verbose=False, resume=True,
                console_protocol=True,
                console_confirm_hook=resume_console_confirmations.append,
            )
        except BaseException as error:
            resume_errors.append(error)

    resume_thread = threading.Thread(target=resume_worker)
    resume_thread.start()
    resume_client.settimeout(0.05)
    try:
        resume_client.recv(1)
    except socket.timeout:
        pass
    else:
        raise AssertionError("resumed server emitted a bootstrap marker")
    finally:
        resume_client.settimeout(None)
    resume_client.sendall(request(CONSOLE_POLL, 9, 0, 0, 0))
    resume_console_reply = receive_exact(resume_client, 5)
    if resume_console_reply[:4] != REPLY_SYNC + b"\x09\x00" or \
            checksum(resume_console_reply) or \
            resume_console_confirmations != [
                {"operation": CONSOLE_POLL, "sequence": 9}
            ]:
        raise AssertionError(
            "resumed N4 console did not confirm its first target reprobe: "
            f"reply={resume_console_reply!r} "
            f"confirmations={resume_console_confirmations!r}"
        )
    resume_client.sendall(request(READ_AHEAD, 10, 0, 2, 1))
    resume_reply = receive_exact(resume_client, len(expected_reply))
    if resume_reply[:5] != b"DJ\x0A\x00\x03" or \
            int.from_bytes(resume_reply[-2:], "big") != \
            crc16_ibm(resume_reply[:-2]):
        raise AssertionError("resumed NetDisk-v3 reply differs")
    resume_thread.join(timeout=2)
    resume_client.close()
    resume_host.close()
    if resume_thread.is_alive() or resume_errors:
        raise AssertionError(
            f"resumed disk server did not finish: {resume_errors!r}"
        )

    console_host, console_client = socket.socketpair()
    console_input = bytearray(b"X")
    console_output = bytearray()
    console_stats: dict[str, int] = {}
    console_confirmations: list[dict[str, int]] = []
    console_errors: list[BaseException] = []
    status_reports: list[dict[str, int]] = []
    diag_reports: list[dict[str, int]] = []
    clock = HostClock(lambda: datetime(
        2026, 8, 17, 12, 34, 56, tzinfo=timezone.utc,
    ))

    def console_worker() -> None:
        try:
            serve_disk(
                console_host.fileno(), drive_a, timeout=2, idle_timeout=0.05,
                reply_guard=0, protocol_version=3, console_protocol=True,
                console_input=console_input, console_output=console_output,
                console_confirm_hook=console_confirmations.append,
                status_report_hook=status_reports.append,
                diag_report_hook=diag_reports.append,
                clock=clock,
                verbose=False, stats=console_stats,
            )
        except BaseException as error:
            console_errors.append(error)

    console_thread = threading.Thread(target=console_worker)
    console_thread.start()
    if receive_exact(console_client, 4) != b"NRN4":
        raise AssertionError("remote-console capability marker differs")
    out_request = request(CONSOLE_OUT, 7, ord("A"), 0, 0)
    console_client.sendall(out_request)
    out_reply = receive_exact(console_client, 5)
    if out_reply[:4] != REPLY_SYNC + b"\x07\x00" or checksum(out_reply):
        raise AssertionError("console-output acknowledgement differs")
    console_client.sendall(out_request)
    if receive_exact(console_client, 5) != out_reply:
        raise AssertionError("duplicate console output did not replay exactly")
    poll_request = request(CONSOLE_POLL, 8, 0, 0, 0)
    console_client.sendall(poll_request)
    poll_reply = receive_exact(console_client, 6)
    if poll_reply[:5] != REPLY_SYNC + b"\x08\x02X" or checksum(poll_reply):
        raise AssertionError("remote console input reply differs")
    console_client.sendall(poll_request)
    if receive_exact(console_client, 6) != poll_reply:
        raise AssertionError("duplicate console poll did not replay exactly")
    console_client.sendall(request(CONSOLE_POLL, 9, 0, 0, 0))
    empty_reply = receive_exact(console_client, 5)
    if empty_reply[:4] != REPLY_SYNC + b"\x09\x00" or checksum(empty_reply):
        raise AssertionError("empty remote console poll differs")
    day = (date(2026, 8, 17) - CPM_EPOCH).days + 1
    console_client.sendall(request(TIME_GET, 10, 0, 0, 0))
    time_reply = receive_exact(console_client, 10)
    expected_time = day.to_bytes(2, "little") + b"\x12\x34\x56"
    if time_reply[:4] != REPLY_SYNC + b"\x0A\x00" or \
            time_reply[4:-1] != expected_time or checksum(time_reply):
        raise AssertionError(f"host clock reply differs: {time_reply!r}")
    next_day = day + 1
    console_client.sendall(request(
        TIME_SET, 11, next_day & 0xFF,
        (0x09 << 8) | (next_day >> 8), 0x08,
    ))
    set_reply = receive_exact(console_client, 5)
    if set_reply[:4] != REPLY_SYNC + b"\x0B\x00" or checksum(set_reply):
        raise AssertionError("host clock set acknowledgement differs")
    console_client.sendall(request(TIME_GET, 12, 0, 0, 0))
    adjusted_reply = receive_exact(console_client, 10)
    if adjusted_reply[4:-1] != \
            next_day.to_bytes(2, "little") + b"\x09\x08\x00" or \
            checksum(adjusted_reply):
        raise AssertionError("session clock offset was not retained")
    console_client.sendall(request(TIME_SET, 13, 0, 0, 0))
    bad_set_reply = receive_exact(console_client, 5)
    if bad_set_reply[:4] != REPLY_SYNC + b"\x0D\x01" or \
            checksum(bad_set_reply):
        raise AssertionError("invalid CP/M date was not rejected")
    console_client.sendall(request(
        STATUS_REPORT, 14, 0x12, (0x0F << 8) | 1, 0,
    ))
    status_reply = receive_exact(console_client, 5)
    if status_reply[:4] != REPLY_SYNC + b"\x0E\x00" or \
            checksum(status_reply):
        raise AssertionError("target status report was not acknowledged")
    console_client.sendall(request(
        DIAG_REPORT, 15, 0x03, (0xA5 << 8) | 0x5A, 0x80,
    ))
    diag_reply = receive_exact(console_client, 5)
    if diag_reply[:4] != REPLY_SYNC + b"\x0F\x00" or checksum(diag_reply):
        raise AssertionError("target diagnostic report was not acknowledged")
    caps_request = request(CAPABILITY_QUERY, 16, 0, 0, 0)
    console_client.sendall(caps_request)
    caps_reply = receive_exact(console_client, 9)
    if caps_reply[:8] != REPLY_SYNC + b"\x10\x00\x03\x03\x0F\x01" or \
            checksum(caps_reply):
        raise AssertionError(f"explicit capability reply differs: {caps_reply!r}")
    console_client.sendall(caps_request)
    if receive_exact(console_client, 9) != caps_reply:
        raise AssertionError("duplicate capability query did not replay reply")
    console_thread.join(timeout=2)
    console_client.close()
    console_host.close()
    if console_thread.is_alive() or console_errors:
        raise AssertionError(
            f"remote console server did not finish: {console_errors!r}"
        )
    if console_output != b"A" or console_input or \
            console_stats["console_output_bytes"] != 1 or \
            console_stats["console_input_bytes"] != 1 or \
            console_stats["console_polls"] != 3 or \
            console_stats["clock_gets"] != 2 or \
            console_stats["clock_sets"] != 1 or \
            console_stats["clock_failures"] != 1 or \
            console_stats["status_reports"] != 1 or \
            console_stats["diag_reports"] != 1 or \
            console_stats["capability_queries"] != 1 or \
            console_confirmations != [{"operation": CONSOLE_OUT,
                                       "sequence": 7}]:
        raise AssertionError(
            f"remote console state/counters differ: output={console_output!r} "
            f"input={console_input!r} stats={console_stats} "
            f"confirmations={console_confirmations!r}"
        )
    if status_reports != [{
        "sequence": 14, "s21": 0x12, "video_mode": 1,
        "features": 0x0F, "clock_status": 0,
    }]:
        raise AssertionError(f"target status hook differs: {status_reports!r}")
    if diag_reports != [{
        "sequence": 15, "suite": 0x03, "pass_mask": 0x5A,
        "fail_mask": 0xA5, "flags": 0x80,
    }]:
        raise AssertionError(f"target diagnostic hook differs: {diag_reports!r}")

    result = ROOT / ".obj" / "janet-disk-server-result-test.json"
    result.parent.mkdir(exist_ok=True)
    write_boot_result(result, {"schema": "test", "elapsed_seconds": 1.25})
    if result.read_text() != \
            '{\n  "schema": "test",\n  "elapsed_seconds": 1.25\n}\n':
        raise AssertionError("boot timing JSON differs")
    result.unlink()
    volume_result = ROOT / ".obj" / "janet-disk-server-volume-test.img"
    volume_result.write_bytes(b"old")
    write_volume(volume_result, b"new volume")
    if volume_result.read_bytes() != b"new volume" or \
            volume_result.with_name(volume_result.name + ".tmp").exists():
        raise AssertionError("atomic writable-volume replacement differs")
    volume_result.unlink()

    media_root = ROOT / ".obj" / "janet-media-test"
    media_root.mkdir(exist_ok=True)
    media_base = media_root / "base.img"
    media_copy = media_root / "copy.img"
    media_snapshot = media_root / "snapshot.json"
    base_bytes = bytes(VOLUME_SIZE)
    media_base.write_bytes(base_bytes)
    read_only = VolumeMedia.open(media_base, "read-only")
    if read_only.writable:
        raise AssertionError("read-only media became writable")
    copy = VolumeMedia.open(media_base, "copy", media_copy)
    copy.volume[RECORD_SIZE:2 * RECORD_SIZE] = b"C" * RECORD_SIZE
    copy.save()
    if media_base.read_bytes() != base_bytes or \
            media_copy.read_bytes()[RECORD_SIZE:2 * RECORD_SIZE] != \
            b"C" * RECORD_SIZE:
        raise AssertionError("writable-copy policy changed its base")
    snapshot = VolumeMedia.open(media_base, "snapshot", media_snapshot)
    snapshot.volume[2 * RECORD_SIZE:3 * RECORD_SIZE] = b"S" * RECORD_SIZE
    snapshot.save()
    restored = VolumeMedia.open(media_base, "snapshot", media_snapshot)
    if restored.volume[2 * RECORD_SIZE:3 * RECORD_SIZE] != \
            b"S" * RECORD_SIZE or media_base.read_bytes() != base_bytes:
        raise AssertionError("sparse snapshot did not round-trip")
    changed_base = bytearray(base_bytes)
    changed_base[0] = 1
    media_base.write_bytes(changed_base)
    try:
        VolumeMedia.open(media_base, "snapshot", media_snapshot)
    except ValueError:
        pass
    else:
        raise AssertionError("snapshot accepted a different base image")
    media_base.unlink()
    media_copy.unlink()
    media_snapshot.unlink()
    media_root.rmdir()

    manifest_system = b"system"
    manifest_stage = b"stage"
    fallback_system = b"fallback-system"
    fallback_stage = b"fallback-stage"
    manifest_a = b"A" * VOLUME_SIZE
    manifest_b = b"B" * NATIVE_VOLUME_SIZE
    artifact = lambda name, data: {
        "file": name, "bytes": len(data),
        "sha256": hashlib.sha256(data).hexdigest(),
    }
    manifest_data = {
        "schema": "cpm-plus-juku-boot-manifest-v1",
        "build_identity": "native-test",
        "system": artifact("system.bin", manifest_system),
        "fast_stage": artifact("fast.bin", manifest_stage),
        "system_slots": [
            {
                "name": "primary",
                "system": artifact("system.bin", manifest_system),
                "fast_stage": artifact("fast.bin", manifest_stage),
            },
            {
                "name": "fallback",
                "system": artifact("fallback.bin", fallback_system),
                "fast_stage": artifact("fallback-fast.bin", fallback_stage),
            },
        ],
        "requirements": {"netdisk": 3, "disk_baud": 19200},
        "volumes": [
            {**artifact("a.img", manifest_a), "drive": "A"},
            {**artifact("b.juk", manifest_b), "drive": "B"},
        ],
    }
    manifest_path = ROOT / ".obj" / "janet-boot-manifest-test.json"
    manifest_path.write_text(json.dumps(manifest_data))
    validated = validate_boot_manifest(
        manifest_path, system=manifest_system, system_name="system.bin",
        fast_stage=manifest_stage, fast_stage_name="fast.bin",
        volume=manifest_a, volume_name="a.img", drive_b=manifest_b,
        drive_b_name="b.juk", disk_protocol=3, disk_baud=19200,
        fallback_system=fallback_system,
        fallback_system_name="fallback.bin",
        fallback_fast_stage=fallback_stage,
        fallback_fast_stage_name="fallback-fast.bin",
    )
    if validated["build_identity"] != "native-test":
        raise AssertionError("boot manifest identity differs")
    try:
        validate_boot_manifest(
            manifest_path, system=manifest_system, system_name="system.bin",
            fast_stage=manifest_stage, fast_stage_name="fast.bin",
            volume=manifest_a, volume_name="a.img", drive_b=manifest_b,
            drive_b_name="b.juk", disk_protocol=2, disk_baud=19200,
        )
    except ValueError:
        pass
    else:
        raise AssertionError("boot manifest accepted a protocol mismatch")
    slot_state = ROOT / ".obj" / "janet-boot-slot-state-test.json"
    primary_slot = BootSlot(
        "primary", Path("system.bin"), manifest_system,
        Path("fast.bin"), manifest_stage,
    )
    fallback_slot = BootSlot(
        "fallback", Path("fallback.bin"), fallback_system,
        Path("fallback-fast.bin"), fallback_stage,
    )
    attempts: list[str] = []

    def attempt_slot(slot: BootSlot) -> dict[str, object]:
        attempts.append(slot.name)
        if slot.name == "primary":
            raise TimeoutError("injected primary failure")
        return {"completion_confirmed": 1}

    selected_slot, slot_result = boot_slots_with_recovery(
        [primary_slot, fallback_slot], attempt_slot,
        max_restarts=0, verbose=False,
    )
    if selected_slot is not fallback_slot or attempts != [
            "primary", "fallback"] or \
            slot_result["boot_slot"] != "fallback":
        raise AssertionError("two-slot fallback order differs")
    write_boot_slot_state(slot_state, fallback_slot)
    if order_boot_slots(
            [primary_slot, fallback_slot], slot_state,
            )[0] is not fallback_slot:
        raise AssertionError("last-known-good slot was not preferred")
    stale_fallback = BootSlot(
        "fallback", Path("fallback.bin"), b"new-system",
        Path("fallback-fast.bin"), fallback_stage,
    )
    if order_boot_slots(
            [primary_slot, stale_fallback], slot_state,
            )[0] is not primary_slot:
        raise AssertionError("stale last-known-good hash was trusted")
    slot_state.unlink()
    manifest_path.unlink()
    print(
        "JANET-DISK-SERVER-TEST: PASS "
        "(dual drive + NetDisk v3 + live resume + atomic save + "
        "media policies + idempotent N4 console + host clock + target reports "
        "+ explicit capabilities + two-slot recovery)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
