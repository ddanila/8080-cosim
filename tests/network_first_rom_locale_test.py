#!/usr/bin/env python3
"""Exercise the separately named ABI 1.1 locale/remap ROM fixture."""

from __future__ import annotations

import errno
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
COMMON_TOOLS = ROOT / "third_party" / "juku-common" / "tools"
FIRMWARE = ROOT / "spinoffs" / "jukuravi" / "network-rom"
sys.path.insert(0, str(COMMON_TOOLS))
sys.path.insert(0, str(FIRMWARE))
from creep_console_oracle import render_transcript  # noqa: E402
import build_network_rom as network_rom  # noqa: E402


def fail(message: str) -> None:
    raise SystemExit(f"NETWORK-FIRST-ROM-LOCALE-TEST: {message}")


def state_file(path: Path) -> dict[str, str]:
    return dict(line.split("=", 1) for line in path.read_text().splitlines()
                if "=" in line)


def boot_ready(trace: Path, image: bytes, root: Path, name: str, *,
               s21: int, keys: str | None, timeout: float) -> tuple[bool, bool]:
    case = root / name
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
        JUKU_KEY_START_VRAM="0",
        JUKU_KEY_HOLD_FRAMES="100000",
    )
    if keys is not None:
        environment["JUKU_KEYS"] = keys
    process = subprocess.Popen(
        [str(trace), str(rom), "500000000"], cwd=case, env=environment,
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    os.close(slave)
    ready = False
    try:
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline and process.poll() is None:
            readable, _, _ = select.select([master], [], [], 0.03)
            if not readable:
                continue
            try:
                if b"\xC4" in os.read(master, 4096):
                    ready = True
                    break
            except OSError as error:
                if error.errno != errno.EIO:
                    raise
        alive = process.poll() is None
    finally:
        if process.poll() is None:
            process.kill()
            process.wait()
        os.close(master)
    return ready, alive


def run_selftest(trace: Path, image: bytes, root: Path, mode: int) \
        -> tuple[dict[str, str], bytes]:
    case = root / f"console-mode-{mode}"
    case.mkdir()
    rom = case / "locale-selftest.bin"
    rom.write_bytes(image)
    checkpoint = case / "checkpoint"
    master, slave = pty.openpty()
    tty.setraw(slave)
    environment = os.environ.copy()
    environment.update(
        JUKU_USART_PTY=os.ttyname(slave),
        JUKU_USART_TRANSFER_CYCLES="16",
        JUKU_USART_BYTE_CYCLES="1024",
        JUKU_USART_PIT_CLOCK="1",
        JUKU_USART_PIT_CPU_HZ="1700000",
        JUKU_CHECKPOINT_PREFIX=str(checkpoint),
        JUKU_REALTIME_HZ="1700000",
        JUKU_KEYS="T",
        JUKU_KEY_START_VRAM="0",
        JUKU_S21_CONFIG=f"0x{0x08 | (mode << 1):02X}",
    )
    process = subprocess.Popen(
        [str(trace), str(rom), "3000000"], cwd=case,
        env=environment, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE,
    )
    os.close(slave)
    received = bytearray()
    try:
        deadline = time.monotonic() + 10
        while b"ABI1" not in received and time.monotonic() < deadline:
            ready, _, _ = select.select([master], [], [], 0.05)
            if not ready:
                continue
            try:
                received.extend(os.read(master, 4096))
            except OSError as error:
                if error.errno != errno.EIO:
                    raise
        if bytes(received) != b"ABI1":
            fail(f"mode {mode} serial self-test output differs: "
                 f"{bytes(received)!r}")
        os.write(master, b"\xC3")
        process.wait(timeout=20)
    finally:
        if process.poll() is None:
            process.kill()
            process.wait()
        os.close(master)
    stderr = process.stderr.read().decode(errors="replace") \
        if process.stderr is not None else ""
    if process.returncode != 0:
        fail(f"mode {mode} cosim exited {process.returncode}: {stderr[-800:]}")
    return (state_file(checkpoint.with_suffix(".state")),
            checkpoint.with_suffix(".ram").read_bytes())


def main() -> int:
    if len(sys.argv) != 2:
        fail("usage: test.py /path/to/trace")
    trace = Path(sys.argv[1]).resolve()
    image, metadata = network_rom.build(locale=True)
    selftest, _ = network_rom.build(locale=True, abi_selftest=True)
    if image != network_rom.LOCALE_OUTPUT.read_bytes():
        fail("committed ABI 1.1 image differs from deterministic rebuild")
    if metadata["abi"] != {"base": "FF00", "major": 1, "minor": 1} or \
            metadata["gate_bytes"] != 214 or \
            metadata.get("netdisk_cache") != {
                "records_per_drive": 8,
                "drives": 2,
                "shared_pointer_fallback": "alias-safe",
            }:
        fail(f"localized ABI metadata differs: {metadata}")
    manifest = image[0x3F00:0x3F50]
    if manifest[:10] != b"JUKUABI\0\x01\x01" or \
            int.from_bytes(manifest[12:14], "little") != 0x01AF:
        fail("ABI 1.1 manifest/version/features differ")
    if manifest[0x4A:0x50:3] != b"\xC3\xC3":
        fail("ABI 1.1 appended vectors are not JMP entries")

    with tempfile.TemporaryDirectory(prefix="network-rom-locale.") as name:
        temporary = Path(name)
        geometries = {
            0: bytes((0, 40, 24, 8, 10, 0xFF, 39,
                      0x90, 0x01, 0x68, 0x01, 0xF0, 0x23, 0x90, 0xD9)),
            1: bytes((1, 53, 24, 6, 10, 0xFC, 39,
                      0x90, 0x01, 0x68, 0x01, 0xF0, 0x23, 0x90, 0xD9)),
            2: bytes((2, 64, 20, 6, 10, 0xFC, 47,
                      0xE0, 0x01, 0xB0, 0x01, 0xA0, 0x23, 0xE0, 0xD9)),
            3: bytes((3, 80, 24, 5, 8, 0xF8, 49,
                      0x90, 0x01, 0x5E, 0x01, 0xF0, 0x23, 0x90, 0xD9)),
        }
        for mode, geometry in geometries.items():
            state, ram = run_selftest(trace, selftest, temporary, mode)
            if state.get("halted") != "1" or state.get("mode") != "1" or \
                    state.get("video_console_mode") != str(mode) or \
                    ram[0xD783] != 0xA5:
                fail(f"mode {mode} fixture did not finish cleanly: {state}")
            config = 0x08 | (mode << 1)
            if ram[0xD7C1] != config or \
                    ram[0xD7C2:0xD7C5] != b"\x01TX":
                fail(f"mode {mode} latched S21/remap differs: "
                     f"{ram[0xD7C1:0xD7CA].hex()}")
            if ram[0xD7CB:0xD7DA] != geometry:
                fail(f"mode {mode} resident geometry differs: "
                     f"{ram[0xD7CB:0xD7DA].hex()}")
            if ram[0xD786:0xD789] != bytes((1, 0, ord("X"))):
                fail(f"mode {mode} remapped key differs: "
                     f"{ram[0xD786:0xD789].hex()}")
            expected = render_transcript(b"Z\xC4", locale=1, mode=mode)
            if ram[0xD800:0xD800 + 9600] != expected:
                fail(f"mode {mode} Estonian framebuffer differs from oracle")

        auto_ready, _ = boot_ready(
            trace, image, temporary, "auto-bit-set", s21=0x01,
            keys=None, timeout=2.0,
        )
        held_ready, held_alive = boot_ready(
            trace, image, temporary, "auto-bit-clear", s21=0x00,
            keys=None, timeout=0.5,
        )
        key_ready, _ = boot_ready(
            trace, image, temporary, "local-n", s21=0x00,
            keys="N", timeout=2.0,
        )
        if not auto_ready or held_ready or not held_alive or not key_ready:
            fail(
                "S21 bit-0 policy differs: "
                f"auto={auto_ready} held={held_ready}/{held_alive} "
                f"local_n={key_ready}"
            )

    print(
        "NETWORK-FIRST-ROM-LOCALE-TEST: PASS "
        f"{metadata['image_sha256']} "
        "(four S21 modes, Estonian locale, remap T->X, bit0 policy)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
