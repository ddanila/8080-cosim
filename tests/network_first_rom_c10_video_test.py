#!/usr/bin/env python3
"""Regress the C9 POF fault, C10 correction, and C11 raster fixes."""

from __future__ import annotations

import errno
import json
import os
from pathlib import Path
import pty
import re
import select
import subprocess
import sys
import tempfile
import time
import tty


ROOT = Path(__file__).resolve().parents[1]
FIRMWARE = ROOT / "spinoffs" / "jukuravi" / "network-rom"
sys.path.insert(0, str(FIRMWARE))
import build_network_rom as network_rom  # noqa: E402


C9_SHA256 = "352417fafcf1ceaef40b8d39916acdaee6de03d914eafe2b54185ccbabe35530"
IOSEQ = re.compile(r"\[IOSEQ\] OUT port=0x07 value=0x([0-9A-Fa-f]{2})")
WATCH_FD80 = "[WATCH] MW FD80="


def fail(message: str) -> None:
    raise SystemExit(f"NETWORK-FIRST-ROM-C10-VIDEO-TEST: FAIL: {message}")


def xor8(data: bytes) -> int:
    value = 0
    for byte in data:
        value ^= byte
    return value


def read_request(fd: int, process: subprocess.Popen[bytes]) -> bytes:
    result = bytearray()
    deadline = time.monotonic() + 5.0
    while len(result) < 9 and time.monotonic() < deadline and process.poll() is None:
        ready, _, _ = select.select([fd], [], [], 0.02)
        if not ready:
            continue
        try:
            result.extend(os.read(fd, 4096))
        except OSError as error:
            if error.errno != errno.EIO:
                raise
    return bytes(result)


def run_fixture(trace: Path, image: bytes, case: Path, *, s21: int = 0) \
        -> tuple[dict[str, str], bytes, list[int], str]:
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
        JUKU_S21_CONFIG=f"0x{s21:02X}",
        JUKU_TRACE_IO="1",
        JUKU_WATCH_ADDRESS="0xFD80",
    )
    process = subprocess.Popen(
        [str(trace), str(rom), "20000000"], cwd=case, env=environment,
        stdout=subprocess.DEVNULL, stderr=subprocess.PIPE,
    )
    os.close(slave)
    try:
        request = read_request(master, process)
        if len(request) != 9 or request[:3] != b"JD\x21" or \
                xor8(request[:-1]) != request[-1]:
            fail(f"{case.name} host request differs: {request.hex()}")
        time.sleep(0.01)
        reply = bytes((ord("D"), ord("J"), request[3], 0))
        os.write(master, reply + bytes((xor8(reply),)))
        process.wait(timeout=12)
    finally:
        if process.poll() is None:
            process.kill()
            process.wait()
        os.close(master)
    stderr = process.stderr.read().decode(errors="replace") \
        if process.stderr is not None else ""
    if process.returncode != 0:
        fail(f"{case.name} cosim exited {process.returncode}: {stderr[-1000:]}")
    state = dict(
        line.split("=", 1)
        for line in checkpoint.with_suffix(".state").read_text().splitlines()
        if "=" in line
    )
    ram = checkpoint.with_suffix(".ram").read_bytes()
    control_writes = [int(match.group(1), 16) for match in IOSEQ.finditer(stderr)]
    return state, ram[0xD800:0xD800 + 9648], control_writes, stderr


def visible_pixels(framebuffer: bytes, portc: int) -> bytes:
    """Digital POF oracle: sync is separate; PC7 high suppresses pixels."""
    return bytes(len(framebuffer)) if portc & 0x80 else framebuffer


def main() -> int:
    if len(sys.argv) != 2:
        fail("usage: test.py /path/to/trace")
    trace = Path(sys.argv[1]).resolve()
    c9, c9_metadata = network_rom.build(c9=True, abi_selftest=True, host_selftest=True)
    c10, c10_metadata = network_rom.build(c10=True, abi_selftest=True, host_selftest=True)
    c11, c11_metadata = network_rom.build(c11=True, abi_selftest=True, host_selftest=True)
    if network_rom.digest(network_rom.build(c9=True)[0]) != C9_SHA256:
        fail("immutable C9 image changed")
    if c10_metadata.get("candidate") != \
            "network-first-abi1.4-c10-pof-release-candidate" or \
            c10_metadata.get("abi") != {"base": "FF00", "major": 1, "minor": 4}:
        fail(f"C10 identity/ABI differs: {json.dumps(c10_metadata)}")
    if c11_metadata.get("candidate") != \
            "network-first-abi1.4-c11-post-raster-candidate" or \
            c11_metadata.get("abi") != {"base": "FF00", "major": 1, "minor": 4}:
        fail(f"C11 identity/ABI differs: {json.dumps(c11_metadata)}")
    if c9_metadata["hardware_init"][0] != "ppi0-82-pc7-high" or \
            c10_metadata["hardware_init"][0] != "ppi0-82-pc7-high-then-low" or \
            c11_metadata["hardware_init"][0] != \
            "ppi0-82-checker-pc7-high-then-low":
        fail("C9/C10/C11 hardware-init metadata differs")
    if c11_metadata["console"].get("physical_raster_clear_bytes") != {
            "00": 9640, "01": 9640, "10": 9648, "11": 9600,
            "implementation_envelope": 9648,
    }:
        fail("C11 physical-raster metadata differs")

    with tempfile.TemporaryDirectory(prefix="network-rom-c10-video.") as name:
        root = Path(name)
        c9_case = root / "c9-negative-control"
        c10_case = root / "c10-release"
        c11_case = root / "c11-raster"
        c9_case.mkdir()
        c10_case.mkdir()
        c11_case.mkdir()
        c9_state, c9_frame, c9_writes, c9_log = run_fixture(
            trace, c9, c9_case,
        )
        c10_state, c10_frame, c10_writes, c10_log = run_fixture(
            trace, c10, c10_case,
        )
        c11_state, c11_frame, c11_writes, c11_log = run_fixture(
            trace, c11, c11_case,
        )
        c11_mode_frames = {0: c11_frame}
        for mode in (1, 2, 3):
            mode_case = root / f"c11-mode-{mode}"
            mode_case.mkdir()
            _state, frame, _writes, _log = run_fixture(
                trace, c11, mode_case, s21=mode << 1,
            )
            c11_mode_frames[mode] = frame

    if c9_state.get("portc") != "81" or c9_state.get("video_pof_released") != "0":
        fail(f"C9 negative control no longer reproduces POF high: {c9_state}")
    if c10_state.get("portc") != "01" or c10_state.get("video_pof_released") != "1":
        fail(f"C10 does not release POF in mode 1: {c10_state}")
    if c11_state.get("portc") != "01" or c11_state.get("video_pof_released") != "1":
        fail(f"C11 does not release POF in mode 1: {c11_state}")
    if c9_writes[:2] != [0x82, 0x0F] or 0x0E in c9_writes:
        fail(f"C9 control sequence differs: {c9_writes}")
    if c10_writes[:3] != [0x82, 0x0F, 0x0E]:
        fail(f"C10 stock POF sequence differs: {c10_writes}")
    if c11_writes[:3] != [0x82, 0x0F, 0x0E]:
        fail(f"C11 stock POF sequence differs: {c11_writes}")
    if not any(c9_frame[:9600]) or c9_frame[:9600] != c10_frame[:9600] or \
            c10_frame[:9600] != c11_frame[:9600]:
        fail("raw C9/C10 framebuffer evidence differs or is empty")
    if any(visible_pixels(c9_frame[:9600], 0x81)):
        fail("C9 POF-high negative control is not classified blank")
    if visible_pixels(c10_frame[:9600], 0x01) != c10_frame[:9600] or \
            not any(c10_frame[:9600]):
        fail("C10 POF-low framebuffer is not classified visible")
    for mode, frame in c11_mode_frames.items():
        if any(frame[9600:9648]):
            fail(
                f"C11 mode {mode} physical-raster tail was not cleared: "
                f"{frame[9600:].hex()}"
            )
    if WATCH_FD80 in c9_log or WATCH_FD80 in c10_log:
        fail("immutable C9/C10 unexpectedly write the extra raster line")
    checker_at = c11_log.find(WATCH_FD80 + "FF")
    release_match = re.search(
        r"\[IOSEQ\] OUT port=0x07 value=0x0E", c11_log,
    )
    clear_at = c11_log.find(WATCH_FD80 + "00", checker_at + 1)
    if checker_at < 0 or release_match is None or \
            not checker_at < release_match.start() < clear_at:
        fail("C11 does not draw checker, release POF, then clear the raster tail")

    print(
        "NETWORK-FIRST-ROM-C10-VIDEO-TEST: PASS "
        f"C9 portC=81 blank; C10 portC=01 visible; "
        f"writes={','.join(f'{value:02X}' for value in c10_writes[:3])}; "
        "C11 checker->POF->9648-byte clear"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
