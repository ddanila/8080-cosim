#!/usr/bin/env python3
"""Exercise the native C host's Linux NetDisk/N4/media path over a PTY."""

from __future__ import annotations

import json
import os
from pathlib import Path
import pty
import select
import signal
import struct
import subprocess
import sys
import tempfile
import time
import tty
import zlib

ROOT = Path(__file__).resolve().parents[1]
HOST = ROOT / "build" / "jukuhost"
EVIDENCE = ROOT / "tools" / "jukuhost_evidence.py"
RECORD = 128
TRACK_BYTES = 40 * RECORD
VOLUME_BYTES = 80 * TRACK_BYTES
NATIVE_BYTES = 160 * TRACK_BYTES


def checksum(data: bytes) -> int:
    value = 0
    for item in data:
        value ^= item
    return value


def request(operation: int, sequence: int, drive: int = 0,
            track: int = 0, sector: int = 0, payload: bytes = b"") -> bytes:
    body = b"JD" + bytes((operation, sequence, drive, track & 0xFF,
                           track >> 8, sector)) + payload
    return body + bytes((checksum(body),))


def console_block(sequence: int, payload: bytes) -> bytes:
    body = b"JD" + bytes((0x28, sequence, len(payload))) + payload
    return body + bytes((checksum(body),))


def read_exact(fd: int, length: int, timeout: float = 3.0) -> bytes:
    result = bytearray()
    deadline = time.monotonic() + timeout
    while len(result) < length and time.monotonic() < deadline:
        ready, _, _ = select.select([fd], [], [], 0.1)
        if ready:
            result.extend(os.read(fd, length - len(result)))
    if len(result) != length:
        raise AssertionError(f"received {len(result)}/{length} bytes: {result.hex()}")
    return bytes(result)


def wait_log(process: subprocess.Popen[str], marker: str) -> list[str]:
    assert process.stdout is not None
    lines: list[str] = []
    pending = ""
    deadline = time.monotonic() + 5.0
    while time.monotonic() < deadline:
        ready, _, _ = select.select([process.stdout], [], [], 0.1)
        if not ready:
            if process.poll() is not None:
                break
            continue
        chunk = os.read(process.stdout.fileno(), 4096)
        if not chunk:
            break
        pending += chunk.decode(errors="replace")
        lines = pending.splitlines(keepends=True)
        if marker in pending:
            return lines
    raise AssertionError(f"host did not log {marker!r}: {''.join(lines)}")


def capture_records(data: bytes) -> list[tuple[int, int, bytes]]:
    assert data.startswith(b"JHCAP1\x01")
    result: list[tuple[int, int, bytes]] = []
    position = 16
    while position < len(data):
        assert position + 16 <= len(data)
        kind, flags, length = struct.unpack_from("<BBH", data, position)
        end = position + 16 + length
        assert end <= len(data)
        expected = struct.unpack_from("<I", data, end - 4)[0]
        assert zlib.crc32(data[position:end - 4]) == expected
        result.append((kind, flags, data[position + 12:end - 4]))
        position = end
    return result


def journal(state: int, sequence: int, offset: int,
            before: bytes, after: bytes) -> bytes:
    assert len(before) == RECORD and len(after) == RECORD
    result = bytearray(276)
    result[:8] = b"JHJR1" + bytes((1, state, 0))
    struct.pack_into("<II", result, 8, sequence, offset)
    result[16:144] = before
    result[144:272] = after
    struct.pack_into("<I", result, 272, zlib.crc32(result[:272]))
    return bytes(result)


def main() -> int:
    if not HOST.is_file():
        raise SystemExit("missing build/jukuhost; run sync/jukuhost_linux_build.sh")
    with tempfile.TemporaryDirectory(prefix="jukuhost-linux-pty.") as name:
        temp = Path(name)
        volume = temp / "a.img"
        drive_b = temp / "b.juk"
        log = temp / "host.log"
        capture = temp / "host.cap"
        volume.write_bytes(bytes(VOLUME_BYTES))
        native = bytearray(NATIVE_BYTES)
        for physical_track in range(160):
            native[physical_track * TRACK_BYTES:(physical_track + 1) *
                   TRACK_BYTES] = bytes((physical_track,)) * TRACK_BYTES
        drive_b.write_bytes(native)
        serial_master, serial_slave = pty.openpty()
        console_master, console_slave = pty.openpty()
        tty.setraw(serial_master)
        tty.setraw(serial_slave)
        tty.setraw(console_master)
        tty.setraw(console_slave)
        command = [
            str(HOST), "--serial", os.ttyname(serial_slave),
            "--volume", str(volume), "--resume-disk", "--writable",
            "--drive-b", str(drive_b), "--disk-protocol", "3",
            "--disk-baud", "19200", "--read-ahead", "3",
            "--console-pty", os.ttyname(console_slave),
            "--disk-timeout", "10", "--log", str(log),
            "--capture", str(capture), "--verbose",
        ]
        process = subprocess.Popen(
            command, cwd=ROOT, text=True, stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
        try:
            wait_log(process, "serving A:")

            os.write(serial_master, request(0x11, 1, 0, 0, 1))
            reply = read_exact(serial_master, 5 + RECORD)
            assert reply[:4] == b"DJ\x01\x00" and not checksum(reply)
            assert reply[4:-1] == bytes(RECORD)

            payload = b"\xA5" * RECORD
            os.write(serial_master, request(0x15, 2, 0, 0, 1, payload))
            write_reply = read_exact(serial_master, 7)
            assert write_reply[:5] == b"DJ\x02\x00\x00"
            os.write(serial_master, request(0x15, 2, 0, 0, 1, payload))
            assert read_exact(serial_master, 7) == write_reply

            os.write(serial_master, request(0x13, 3, 0, 0, 1))
            compact = read_exact(serial_master, 6)
            assert compact[:5] == b"DJ\x03\x02\xA5" and not checksum(compact)

            os.write(serial_master, request(0x11, 4, 1, 159, 40))
            native_reply = read_exact(serial_master, 5 + RECORD)
            assert native_reply[:4] == b"DJ\x04\x00"
            assert native_reply[4:-1] == bytes((159,)) * RECORD

            os.write(serial_master, request(0x26, 5))
            capabilities = read_exact(serial_master, 9)
            assert capabilities[:4] == b"DJ\x05\x00"
            assert capabilities[4:8] == bytes((3, 3, 0x7F, 2))

            os.write(serial_master, console_block(6, b"HELLO"))
            assert read_exact(serial_master, 5)[:4] == b"DJ\x06\x00"
            assert read_exact(console_master, 5) == b"HELLO"
            os.write(console_master, b"K")
            time.sleep(0.05)
            os.write(serial_master, request(0x20, 7))
            console_reply = read_exact(serial_master, 6)
            assert console_reply[:5] == b"DJ\x07\x02K"

            # Fill the host-to-target PTY queue with valid N4 poll replies,
            # then interrupt while the writer is back-pressured. This pins
            # Ctrl+C as a clean lifecycle stop even when it lands inside a
            # partial serial write rather than in the idle read loop.
            os.set_blocking(serial_master, False)
            sequence = 8
            while True:
                burst = b"".join(
                    request(0x20, (sequence + index) & 0xFF)
                    for index in range(128)
                )
                try:
                    os.write(serial_master, burst)
                except BlockingIOError:
                    break
                sequence = (sequence + 128) & 0xFF
            time.sleep(0.1)
            process.send_signal(signal.SIGINT)
            process.wait(timeout=5.0)
            remainder = process.stdout.read() if process.stdout is not None else ""
            assert process.returncode == 0, remainder
        finally:
            if process.poll() is None:
                process.kill()
                process.wait()
            os.close(serial_master)
            os.close(serial_slave)
            os.close(console_master)
            os.close(console_slave)
        assert volume.read_bytes()[:RECORD] == b"\xA5" * RECORD
        assert not Path(str(volume) + ".jhj").exists()
        assert "stop exit=0" in log.read_text()
        captured = capture.read_bytes()
        records = capture_records(captured)
        events = [(flags, payload) for kind, flags, payload in records
                  if kind == 3]
        assert any(payload == b"phase=netdisk" for _, payload in events)
        assert any(payload.startswith(b"media write seq=1")
                   for _, payload in events)
        assert any(payload.startswith(b"stop exit=0") for _, payload in events)
        assert any(kind == 1 for kind, _, _ in records)
        assert any(kind == 2 for kind, _, _ in records)
        requests_path = temp / "requests.jsonl"
        converted = subprocess.run([
            sys.executable, str(EVIDENCE), str(capture),
            "--requests-jsonl", str(requests_path),
        ], cwd=ROOT, text=True, stdout=subprocess.PIPE,
           stderr=subprocess.STDOUT, check=False)
        assert converted.returncode == 0, converted.stdout
        request_evidence = [json.loads(line)
                            for line in requests_path.read_text().splitlines()]
        assert len(request_evidence) >= 8
        assert request_evidence[0]["operation"] == 0x11
        assert request_evidence[0]["operation_name"] == "netdisk-read"
        assert request_evidence[-1]["operation"] == 0x20
        assert request_evidence[-1]["operation_name"] == "console-poll"
        assert all(record["schema"] == "juku-netdisk-request-trace-v1"
                   for record in request_evidence)

        # Simulate a crash after the image record was applied but before the
        # journal could be committed. A new production process must roll back
        # the working image before serving any request.
        image = bytearray(volume.read_bytes())
        image[:RECORD] = b"\x5A" * RECORD
        volume.write_bytes(image)
        journal_path = Path(str(volume) + ".jhj")
        journal_path.write_bytes(journal(
            2, 99, 0, b"\xA5" * RECORD, b"\x5A" * RECORD))
        recovery_master, recovery_slave = pty.openpty()
        tty.setraw(recovery_master)
        tty.setraw(recovery_slave)
        recovery_log = temp / "recovery.log"
        recovery = subprocess.Popen([
            str(HOST), "--serial", os.ttyname(recovery_slave),
            "--volume", str(volume), "--resume-disk", "--writable",
            "--disk-timeout", "10", "--log", str(recovery_log),
        ], cwd=ROOT, text=True, stdout=subprocess.PIPE,
           stderr=subprocess.STDOUT)
        try:
            wait_log(recovery, "recovered interrupted media transaction")
            recovery.send_signal(signal.SIGINT)
            recovery.wait(timeout=5.0)
            assert recovery.returncode == 0
        finally:
            if recovery.poll() is None:
                recovery.kill()
                recovery.wait()
            os.close(recovery_master)
            os.close(recovery_slave)
        assert volume.read_bytes()[:RECORD] == b"\xA5" * RECORD
        assert not journal_path.exists()
        assert "stop exit=0" in recovery_log.read_text()
    print("JUKUHOST-LINUX-PTY-TEST: PASS "
          "(N3/N4 + B: + duplicate + journal recovery + capture events)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
