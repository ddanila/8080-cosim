#!/usr/bin/env python3
"""Prove the C9/C10 ABI, boot policy, and bounded host failures."""

from __future__ import annotations

import errno
import json
import os
from pathlib import Path
import pty
import select
import subprocess
import sys
import tempfile
import time
import tty


ROOT = Path(__file__).resolve().parents[1]
FIRMWARE = ROOT / "spinoffs" / "jukuravi" / "network-rom"
sys.path.insert(0, str(FIRMWARE))
sys.path.insert(0, str(ROOT / "third_party" / "juku-common" / "tools"))
import build_network_rom as network_rom  # noqa: E402
from creep_console_oracle import render_transcript  # noqa: E402

RELEASE = os.environ.get("NETWORK_FIRST_ROM_RELEASE", "c9").lower()
if RELEASE not in ("c9", "c10"):
    raise SystemExit(f"unsupported NETWORK_FIRST_ROM_RELEASE={RELEASE!r}")
LABEL = RELEASE.upper()


def fail(message: str) -> None:
    raise SystemExit(f"NETWORK-FIRST-ROM-{LABEL}-TEST: {message}")


def parse_state(path: Path) -> dict[str, str]:
    return dict(line.split("=", 1) for line in path.read_text().splitlines()
                if "=" in line)


def xor8(data: bytes) -> int:
    value = 0
    for byte in data:
        value ^= byte
    return value


def read_request(fd: int, process: subprocess.Popen[bytes], timeout: float) -> bytes:
    result = bytearray()
    deadline = time.monotonic() + timeout
    while len(result) < 9 and time.monotonic() < deadline and \
            process.poll() is None:
        ready, _, _ = select.select([fd], [], [], 0.02)
        if not ready:
            continue
        try:
            result.extend(os.read(fd, 4096))
        except OSError as error:
            if error.errno != errno.EIO:
                raise
    return bytes(result)


def run_transport_case(trace: Path, image: bytes, root: Path, label: str,
                       response: str, expected_reason: int,
                       *, usart_fault: str | None = None) -> int:
    case = root / label
    case.mkdir()
    rom = case / "rom.bin"
    rom.write_bytes(image)
    checkpoint = case / "checkpoint"
    master, slave = pty.openpty()
    tty.setraw(slave)
    environment = os.environ.copy()
    environment.update(
        JUKU_USART_PTY=os.ttyname(slave),
        JUKU_USART_TRANSFER_CYCLES="16",
        JUKU_USART_BYTE_CYCLES="256",
        JUKU_USART_PIT_CLOCK="1",
        JUKU_USART_PIT_CPU_HZ="1700000",
        JUKU_USART_HOST_SYNC_MS="250",
        JUKU_REALTIME_HZ="1700000",
        JUKU_DISABLE_SETTLE="1",
        JUKU_CHECKPOINT_PREFIX=str(checkpoint),
        JUKU_S21_CONFIG="0x00",
    )
    if usart_fault is not None:
        environment["JUKU_USART_FAULT"] = usart_fault
    process = subprocess.Popen(
        [str(trace), str(rom), "20000000"], cwd=case, env=environment,
        stdout=subprocess.DEVNULL, stderr=subprocess.PIPE,
    )
    os.close(slave)
    request = b""
    try:
        if usart_fault != "tx_stuck":
            request = read_request(master, process, 4.0)
            if len(request) != 9 or request[:3] != b"JD\x21" or \
                    request[4:8] != b"X\0\0\0" or xor8(request[:-1]) != \
                    request[-1]:
                fail(f"{label} request differs: {request.hex()}")
            sequence = request[3]
            # The half-duplex target finishes its fixed drain and changes D11
            # from transmit to receive after the final request byte reaches
            # the PTY. Do not inject an emulator-only reply before that turn.
            time.sleep(0.01)
            if response == "success":
                reply = bytes((ord("D"), ord("J"), sequence, 0))
                os.write(master, reply + bytes((xor8(reply),)))
            elif response == "sequence":
                reply = bytes((ord("D"), ord("J"), (sequence + 1) & 0xFF, 0))
                os.write(master, reply + bytes((xor8(reply),)))
            elif response == "integrity":
                reply = bytes((ord("D"), ord("J"), sequence, 0))
                os.write(master, reply + bytes((xor8(reply) ^ 0x01,)))
            elif response == "status":
                reply = bytes((ord("D"), ord("J"), sequence, 7))
                os.write(master, reply + bytes((xor8(reply),)))
            elif response == "garbage":
                os.write(master, b"Z" * 300)
            elif response == "truncated":
                os.write(master, bytes((ord("D"), ord("J"), sequence)))
            elif response != "silent":
                fail(f"unknown response fixture {response}")
        process.wait(timeout=12)
    finally:
        if process.poll() is None:
            process.kill()
            process.wait()
        os.close(master)
    stderr = process.stderr.read().decode(errors="replace") \
        if process.stderr is not None else ""
    if process.returncode != 0:
        fail(f"{label} cosim exited {process.returncode}: {stderr[-1200:]}")
    state = parse_state(checkpoint.with_suffix(".state"))
    ram = checkpoint.with_suffix(".ram").read_bytes()
    if state.get("halted") != "1" or state.get("mode") != "1" or \
            state.get("iff") != "0" or ram[0xD783] != 0xA5:
        fail(f"{label} did not return and halt safely: {state}")
    expected_flags = 0x0F if expected_reason == 0 else 0x06
    observed = ram[0xD7F8:0xD7FC]
    expected = bytes((expected_reason, 0, expected_flags, 0x21))
    if expected_reason == 0:
        expected = bytes((0, 0, expected_flags, 0))
    if observed != expected:
        fail(f"{label} state={observed.hex()}, expected={expected.hex()}")
    if ram[0xD5C0:0xD5D0] != b"\xA6" * 16 or \
            ram[0xD5F0:0xD600] != b"\xA6" * 16:
        fail(f"{label} crossed a stack guard")
    if ram[0xD800:0xD800 + 9600] != render_transcript(b"LR", mode=0):
        fail(f"{label} did not preserve local output around the host call")
    cycles = int(state["cyc"])
    if cycles >= 5_000_000:
        fail(f"{label} exceeded the bounded-return budget: {cycles} cycles")
    return cycles


def boot_ready(trace: Path, image: bytes, root: Path, label: str,
               s21: int) -> bool:
    case = root / label
    case.mkdir()
    rom = case / "rom.bin"
    rom.write_bytes(image)
    master, slave = pty.openpty()
    tty.setraw(slave)
    environment = os.environ.copy()
    environment.update(
        JUKU_USART_PTY=os.ttyname(slave),
        JUKU_USART_TRANSFER_CYCLES="16",
        JUKU_USART_BYTE_CYCLES="1024",
        JUKU_USART_PIT_CLOCK="1",
        JUKU_USART_PIT_CPU_HZ="1700000",
        JUKU_REALTIME_HZ="20000000",
        JUKU_DISABLE_SETTLE="1",
        JUKU_S21_CONFIG=f"0x{s21:02X}",
    )
    process = subprocess.Popen(
        [str(trace), str(rom), "500000000"], cwd=case, env=environment,
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    os.close(slave)
    ready = False
    try:
        deadline = time.monotonic() + 3.0
        while time.monotonic() < deadline and process.poll() is None:
            readable, _, _ = select.select([master], [], [], 0.03)
            if not readable:
                continue
            try:
                if b"\xC7" in os.read(master, 4096):
                    ready = True
                    break
            except OSError as error:
                if error.errno != errno.EIO:
                    raise
    finally:
        if process.poll() is None:
            process.kill()
            process.wait()
        os.close(master)
    return ready


def main() -> int:
    if len(sys.argv) != 2:
        fail("usage: test.py /path/to/trace")
    trace = Path(sys.argv[1]).resolve()
    if not trace.is_file():
        fail(f"missing trace executable: {trace}")
    build_options = {RELEASE: True}
    image, metadata = network_rom.build(**build_options)
    fixture, _ = network_rom.build(
        **build_options, abi_selftest=True, host_selftest=True,
    )
    output = network_rom.C10_OUTPUT if RELEASE == "c10" else \
        network_rom.C9_OUTPUT
    if output.is_file() and image != output.read_bytes():
        fail(f"committed {LABEL} image differs from deterministic rebuild")
    candidate = (network_rom.C10_CANDIDATE if RELEASE == "c10" else
                 "network-first-abi1.4-c9-bounded-host-simulator")
    if metadata.get("abi") != {"base": "FF00", "major": 1, "minor": 4} or \
            metadata.get("candidate") != candidate or \
            metadata.get("abi_vectors", {}).get("host_services") != "FF5C" or \
            metadata.get("resident_host", {}).get("state_bytes") != 4 or \
            metadata.get("resident_host", {}).get(
                "transaction_deadline") != {
                    "transmitter_ready_polls_per_byte": 8192,
                    "receiver_ready_polls_per_byte": 65535,
                    "reply_prefix_scan_bytes": 256,
                    "failure_backoff_console_polls": 1,
                } or \
            sum(image[0x1800:]) & 0xFF:
        fail(f"{LABEL} metadata/resident checksum differs: {json.dumps(metadata)}")
    manifest = image[0x3F00:0x3F60]
    if manifest[:10] != b"JUKUABI\0\x01\x04" or \
            manifest[0x5C] != 0xC3:
        fail(f"{LABEL} manifest or host vector differs")

    with tempfile.TemporaryDirectory(prefix=f"network-rom-{RELEASE}.") as name:
        temporary = Path(name)
        cases = (
            ("success", "success", 0, None),
            ("tx-timeout", "silent", 1, "tx_stuck"),
            ("rx-timeout", "silent", 2, None),
            ("truncated", "truncated", 2, None),
            ("sync-budget", "garbage", 3, None),
            ("sequence", "sequence", 4, None),
            ("integrity", "integrity", 5, None),
            ("status", "status", 6, None),
        )
        cycle_counts = {}
        for label, response, reason, fault in cases:
            cycle_counts[label] = run_transport_case(
                trace, fixture, temporary, label, response, reason,
                usart_fault=fault,
            )
        readiness = {
            s21: boot_ready(
                trace, image, temporary, f"s21-{s21:02x}", s21,
            )
            for s21 in range(0x20)
        }
        failed_configs = [value for value, ready in readiness.items()
                          if not ready]
        if failed_configs:
            fail(f"unconditional boot failed for S21={failed_configs}")

    print(
        f"NETWORK-FIRST-ROM-{LABEL}-TEST: PASS "
        f"{metadata['image_sha256']} "
        "(ABI 1.4; TX/RX/sync/sequence/integrity/status; "
        f"worst bounded return={max(cycle_counts.values())} cycles; "
        "all S21 bits 4:0 boot; bit0 reserved)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
