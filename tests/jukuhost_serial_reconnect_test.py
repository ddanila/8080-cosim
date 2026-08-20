#!/usr/bin/env python3
"""Prove bounded named-device reopen without restarting the C host."""

from __future__ import annotations

import os
from pathlib import Path
import pty
import select
import signal
import subprocess
import tempfile
import time
import tty

ROOT = Path(__file__).resolve().parents[1]
HOST = ROOT / "build" / "jukuhost"
RECORD = 128
VOLUME_BYTES = 80 * 40 * RECORD


def checksum(data: bytes) -> int:
    value = 0
    for item in data:
        value ^= item
    return value


def request(sequence: int, sector: int) -> bytes:
    body = b"JD" + bytes((0x11, sequence, 0, 0, 0, sector))
    return body + bytes((checksum(body),))


def read_exact(fd: int, length: int, timeout: float = 5.0) -> bytes:
    result = bytearray()
    deadline = time.monotonic() + timeout
    while len(result) < length and time.monotonic() < deadline:
        ready, _, _ = select.select([fd], [], [], 0.1)
        if ready:
            result.extend(os.read(fd, length - len(result)))
    if len(result) != length:
        raise AssertionError(f"received {len(result)}/{length}: {result.hex()}")
    return bytes(result)


def wait_output(process: subprocess.Popen[str], marker: str,
                timeout: float = 5.0) -> str:
    assert process.stdout is not None
    result = ""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        ready, _, _ = select.select([process.stdout], [], [], 0.1)
        if not ready:
            if process.poll() is not None:
                break
            continue
        chunk = os.read(process.stdout.fileno(), 4096)
        if not chunk:
            break
        result += chunk.decode(errors="replace")
        if marker in result:
            return result
    raise AssertionError(f"host did not emit {marker!r}: {result}")


def new_pty() -> tuple[int, int]:
    master, slave = pty.openpty()
    tty.setraw(master)
    tty.setraw(slave)
    return master, slave


def main() -> int:
    if not HOST.is_file():
        raise SystemExit("missing build/jukuhost; run Linux build first")
    with tempfile.TemporaryDirectory(prefix="jukuhost-reconnect.") as name:
        temp = Path(name)
        volume = temp / "a.img"
        port = temp / "serial"
        replacement = temp / "serial.next"
        log = temp / "host.log"
        volume.write_bytes(bytes(VOLUME_BYTES))
        master, slave = new_pty()
        port.symlink_to(os.ttyname(slave))
        process = subprocess.Popen([
            str(HOST), "--serial", str(port), "--volume", str(volume),
            "--resume-disk", "--disk-timeout", "20",
            "--reconnect-timeout", "5", "--log", str(log), "--verbose",
        ], cwd=ROOT, text=True, stdout=subprocess.PIPE,
           stderr=subprocess.STDOUT)
        next_master = -1
        next_slave = -1
        try:
            wait_output(process, "serving A:")
            os.write(master, request(1, 1))
            first = read_exact(master, 5 + RECORD)
            assert first[:4] == b"DJ\x01\x00" and not checksum(first)

            next_master, next_slave = new_pty()
            replacement.symlink_to(os.ttyname(next_slave))
            os.replace(replacement, port)
            os.close(master)
            os.close(slave)
            master = -1
            slave = -1

            wait_output(process, "serial reconnected count=1", 7.0)
            assert read_exact(next_master, 4) == b"NRN3"
            os.write(next_master, request(2, 2))
            second = read_exact(next_master, 5 + RECORD)
            assert second[:4] == b"DJ\x02\x00" and not checksum(second)

            process.send_signal(signal.SIGINT)
            process.wait(timeout=5.0)
            assert process.returncode == 0
        finally:
            if process.poll() is None:
                process.kill()
                process.wait()
            for descriptor in (master, slave, next_master, next_slave):
                if descriptor >= 0:
                    os.close(descriptor)
        evidence = log.read_text()
        assert "serial link lost" in evidence
        assert "reconnects=1" in evidence and "requests=2" in evidence
    print("JUKUHOST-SERIAL-RECONNECT-TEST: PASS (named PTY loss + reopen)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
