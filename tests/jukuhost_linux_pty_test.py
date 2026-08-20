#!/usr/bin/env python3
"""Exercise the native C host's Linux NetDisk/N4/media path over a PTY."""

from __future__ import annotations

import os
from pathlib import Path
import pty
import select
import signal
import subprocess
import sys
import tempfile
import time
import tty

ROOT = Path(__file__).resolve().parents[1]
HOST = ROOT / "build" / "jukuhost"
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
        assert captured.startswith(b"JHCAP1\x01") and len(captured) > 16
    print("JUKUHOST-LINUX-PTY-TEST: PASS (N3/N4 + B: + duplicate + journal)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
