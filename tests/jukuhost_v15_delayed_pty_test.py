#!/usr/bin/env python3
"""Prove that stock-assisted V15 survives a core delayed beyond four seconds."""

from __future__ import annotations

from collections import deque
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
CPM_ROOT = os.environ.get("CPM_PLUS_JUKU_ROOT")
CPM = Path(CPM_ROOT) / "out" if CPM_ROOT else ROOT / "tests/fixtures/jukuhost-v15"
HOST = ROOT / "build/jukuhost"
SYSTEM = CPM / "cpm-plus-juku-system.bin"
FASTBOOT = CPM / "cpm-plus-juku-fastboot-v15.bin"

sys.path.insert(0, str(ROOT / "tests/fixtures"))
from legacy_janet_fastboot import split_stage_artifact  # noqa: E402
from legacy_janet_fastboot import extension_packet  # noqa: E402
from legacy_janet_netboot import (  # noqa: E402
    ACK_CONTROL,
    DATA_CONTROL,
    POLL_CONTROL,
    FrameParser,
    frame,
)


RECORD = 128
VOLUME_BYTES = 80 * 40 * RECORD


def checked(kind: int, first: int, second: int) -> bytes:
    body = bytes((ord("J"), kind, first, second))
    value = 0
    for byte in body:
        value ^= byte
    return body + bytes((value,))


def xor(data: bytes) -> int:
    value = 0
    for byte in data:
        value ^= byte
    return value


def read_available(fd: int, timeout: float) -> bytes:
    result = bytearray()
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        ready, _, _ = select.select([fd], [], [], 0.02)
        if not ready:
            if result:
                break
            continue
        result.extend(os.read(fd, 4096))
    return bytes(result)


def read_contains(fd: int, expected: bytes, timeout: float = 10.0) -> bytes:
    result = bytearray()
    deadline = time.monotonic() + timeout
    while expected not in result and time.monotonic() < deadline:
        ready, _, _ = select.select([fd], [], [], 0.1)
        if ready:
            result.extend(os.read(fd, 4096))
    if expected not in result:
        raise AssertionError(
            f"did not receive {len(expected)}-byte expected sequence; "
            f"captured {len(result)} bytes"
        )
    return bytes(result)


class JanetPeer:
    def __init__(self, fd: int) -> None:
        self.fd = fd
        self.parser = FrameParser()
        self.pending: deque[bytes] = deque()

    def send(self, packet: bytes) -> None:
        os.write(self.fd, packet)

    def receive(self, timeout: float = 5.0) -> bytes:
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if self.pending:
                return self.pending.popleft()
            ready, _, _ = select.select([self.fd], [], [], 0.1)
            if ready:
                self.pending.extend(self.parser.feed(os.read(self.fd, 4096)))
        raise AssertionError("timed out waiting for Janet host frame")


def payload(packet: bytes) -> bytes:
    return packet[6:-1] if packet[4] & 0x0C == 0x04 else b""


def main() -> int:
    if not all(path.is_file() for path in (HOST, SYSTEM, FASTBOOT)):
        raise SystemExit("missing C host or frozen CP/M/V15 artifacts")
    stage = FASTBOOT.read_bytes()
    core, extension, compressed = split_stage_artifact(stage)
    assert len(core) == 128 and extension is not None and compressed is not None
    with tempfile.TemporaryDirectory(prefix="jukuhost-v15-delay.") as name:
        temp = Path(name)
        volume = temp / "a.img"
        log = temp / "host.log"
        volume.write_bytes(bytes(VOLUME_BYTES))
        master, slave = pty.openpty()
        tty.setraw(master)
        tty.setraw(slave)
        host = subprocess.Popen([
            str(HOST), "--serial", os.ttyname(slave),
            "--system", str(SYSTEM), "--fast-stage", str(FASTBOOT),
            "--volume", str(volume), "--disk-protocol", "3",
            "--disk-baud", "19200", "--timeout", "20",
            "--disk-timeout", "20", "--log", str(log), "--verbose",
        ], cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
           text=True)
        peer = JanetPeer(master)
        try:
            deadline = time.monotonic() + 5.0
            while not log.exists() or "waiting for stock Janet request" not in \
                    log.read_text(errors="replace"):
                if time.monotonic() >= deadline:
                    raise AssertionError(
                        host.stdout.read() if host.stdout else "host did not start"
                    )
                time.sleep(0.02)
            peer.send(frame(2, 1, DATA_CONTROL, b"\x03\x04"))
            assert peer.receive()[4] == ACK_CONTROL
            peer.send(frame(2, 1, POLL_CONTROL))
            start = peer.receive()
            assert payload(start)[:2] == b"\x03\x05"
            peer.send(frame(2, 1, ACK_CONTROL))

            records: list[bytes] = []
            for expected_marker in (2, 4, 9):
                peer.send(frame(2, 1, POLL_CONTROL))
                release = peer.receive()
                packet = peer.receive()
                assert release[2] == 0 and packet[4] == DATA_CONTROL
                assert payload(packet)[0] == expected_marker
                records.append(payload(packet))
                peer.send(frame(2, 1, ACK_CONTROL))
            release = peer.receive()
            end = peer.receive()
            assert release[2] == 0 and payload(end)[:2] == b"\x03\x06"
            peer.send(frame(2, 1, ACK_CONTROL))
            execute = [peer.receive() for _ in range(7)]
            assert execute[-1][2] == 0
            loaded = records[0][8:] + records[1][1:] + records[2][1:]
            assert loaded == core

            # The retired host exhausted five 32-probe groups in about four
            # seconds and incorrectly returned to 9600. Keep the simulated
            # core unavailable longer than that, while bytes simply pass an
            # as-yet-disabled receiver as they would on the wire.
            time.sleep(5.0)
            probes = read_available(master, 0.2)
            assert b"\xA5\x3A" in probes
            os.write(master, b"\xC5")
            expected_extension_tail = extension_packet(extension)[2:]
            read_contains(master, expected_extension_tail)
            os.write(master, checked(ord("R"), 15, 1))

            stream_probe = read_available(master, 0.2)
            assert b"JZ" in stream_probe
            os.write(master, b"\xC6")
            read_contains(master, compressed, 15.0)
            os.write(master, checked(ord("A"), 0, 0))

            deadline = time.monotonic() + 5.0
            while "phase=netdisk" not in log.read_text(errors="replace"):
                if time.monotonic() >= deadline:
                    raise AssertionError(log.read_text(errors="replace"))
                time.sleep(0.05)
            # Discard repeated N3 capability markers, issue one real request,
            # and locate its complete raw-record reply.
            read_available(master, 0.1)
            request = b"JD" + bytes((0x11, 1, 0, 0, 0, 1))
            os.write(master, request + bytes((xor(request),)))
            reply = bytearray()
            deadline = time.monotonic() + 5.0
            while time.monotonic() < deadline:
                reply.extend(read_available(master, 0.1))
                start = reply.find(b"DJ\x01\x00")
                if start >= 0 and len(reply) >= start + 133:
                    packet = bytes(reply[start:start + 133])
                    assert xor(packet) == 0
                    break
            else:
                raise AssertionError(f"no NetDisk reply: {reply.hex()}")
            host.send_signal(signal.SIGINT)
            host.wait(timeout=5.0)
            assert host.returncode == 0
            evidence = log.read_text()
            assert "V15 core acknowledged" in evidence
            assert "Fastboot V15 complete" in evidence
            assert "phase=netdisk" in evidence
            assert "requests=1" in evidence
        finally:
            if host.poll() is None:
                host.kill()
                host.wait()
            os.close(master)
            os.close(slave)
    print("JUKUHOST-V15-DELAYED-PTY-TEST: PASS (5-second core delay)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
