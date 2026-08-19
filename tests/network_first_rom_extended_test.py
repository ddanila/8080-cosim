#!/usr/bin/env python3
"""Prove ABI 1.2 services and integrated console/keyboard/cursor behavior."""

from __future__ import annotations

import errno
import hashlib
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
sys.path.insert(0, str(ROOT / "third_party" / "juku-common" / "tools"))
sys.path.insert(0, str(FIRMWARE))
from creep_console_oracle import render_transcript  # noqa: E402
import build_network_rom as network_rom  # noqa: E402


C5_SHA256 = "9ed6273f44c1b09dcb5fcd3ca94e5a1aad813b285607558a7d8cb98b1a5e6e7a"
C6_SHA256 = "0487d5150f9b662a193b3f031aadd90002ee232477d355d3877a757a247c2f09"


def fail(message: str) -> None:
    raise SystemExit(f"NETWORK-FIRST-ROM-EXTENDED-TEST: {message}")


def parse_state(path: Path) -> dict[str, str]:
    return dict(line.split("=", 1) for line in path.read_text().splitlines()
                if "=" in line)


def run_fixture(trace: Path, image: bytes, root: Path, name: str,
                mode: int, *, max_cycles: int = 5_000_000,
                realtime_hz: int = 1_700_000,
                timeout: float = 25.0) -> tuple[dict[str, str], bytes]:
    case = root / name
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
        JUKU_USART_BYTE_CYCLES="1024",
        JUKU_USART_PIT_CLOCK="1",
        JUKU_USART_PIT_CPU_HZ="1700000",
        JUKU_CHECKPOINT_PREFIX=str(checkpoint),
        JUKU_REALTIME_HZ=str(realtime_hz),
        JUKU_KEYS="T",
        JUKU_KEY_START_VRAM="0",
        JUKU_S21_CONFIG=f"0x{0x08 | (mode << 1):02X}",
    )
    process = subprocess.Popen(
        [str(trace), str(rom), str(max_cycles)], cwd=case, env=environment,
        stdout=subprocess.DEVNULL, stderr=subprocess.PIPE,
    )
    os.close(slave)
    received = bytearray()
    try:
        deadline = time.monotonic() + 12.0
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
            fail(f"{name} serial output differs: {bytes(received)!r}")
        os.write(master, b"\xC3")
        process.wait(timeout=timeout)
    finally:
        if process.poll() is None:
            process.kill()
            process.wait()
        os.close(master)
    stderr = process.stderr.read().decode(errors="replace") \
        if process.stderr is not None else ""
    if process.returncode != 0:
        fail(f"{name} cosim exited {process.returncode}: {stderr[-1000:]}")
    state = parse_state(checkpoint.with_suffix(".state"))
    ram = checkpoint.with_suffix(".ram").read_bytes()
    if state.get("halted") != "1" or state.get("mode") != "1" or \
            state.get("iff") != "0" or ram[0xD783] != 0xA5:
        fail(f"{name} did not finish safely: {state}")
    if ram[0xD5C0:0xD5D0] != b"\xA6" * 16 or \
            ram[0xD5F0:0xD600] != b"\xA6" * 16:
        fail(f"{name} crossed a stack guard")
    return state, ram


def main() -> int:
    if len(sys.argv) != 2:
        fail("usage: test.py /path/to/trace")
    trace = Path(sys.argv[1]).resolve()
    image, metadata = network_rom.build(extended=True)
    successor_image, successor_metadata = network_rom.build(successor=True)
    if image != network_rom.EXTENDED_OUTPUT.read_bytes():
        fail("committed ABI 1.2 image differs from deterministic rebuild")
    if successor_image != network_rom.SUCCESSOR_OUTPUT.read_bytes():
        fail("committed C7 successor differs from deterministic rebuild")
    if hashlib.sha256(network_rom.LOCALE_OUTPUT.read_bytes()).hexdigest() != \
            C5_SHA256:
        fail("ABI 1.2 work changed the immutable C5 ROM")
    if hashlib.sha256(image).hexdigest() != C6_SHA256:
        fail("C7 work changed the immutable C6 ROM")
    if metadata.get("abi") != {"base": "FF00", "major": 1, "minor": 2} or \
            metadata.get("candidate") != \
            "network-first-abi1.2-c6-simulator" or \
            metadata.get("feature_bits", {}).get("value") != "0FBF" or \
            metadata.get("fastboot_protocol") != 16 or \
            metadata.get("target_ready_byte") != "C7" or \
            metadata.get("fastboot_extension_bytes") != 0 or \
            metadata.get("embedded_fastboot_extension_bytes") != \
            network_rom.EMBEDDED_EXTENSION_BYTES or \
            not {
                "console_block": "FF53",
                "netdisk_multi": "FF56",
                "keyboard_raw": "FF59",
                "sound": "FF41",
                "diagnostics": "FF44",
            }.items() <= metadata.get("abi_vectors", {}).items():
        fail(f"ABI 1.2 metadata differs: {metadata}")
    if successor_metadata.get("candidate") != \
            "network-first-abi1.2-c7-modified-raw-simulator" or \
            successor_metadata.get("abi") != metadata.get("abi") or \
            successor_image == image:
        fail(f"C7 successor metadata differs: {successor_metadata}")
    extension_start = network_rom.EMBEDDED_EXTENSION_STORED
    extension_end = extension_start + network_rom.EMBEDDED_EXTENSION_BYTES
    embedded_extension = image[extension_start:extension_end]
    if hashlib.sha256(embedded_extension).hexdigest() != \
            metadata.get("embedded_fastboot_extension_sha256") or \
            metadata.get("embedded_fastboot_extension_file_offset") != "0600":
        fail("V16 ROM-resident receive/decompress loader metadata differs")
    manifest = image[0x3F00:0x3F60]
    if manifest[:10] != b"JUKUABI\0\x01\x02" or \
            int.from_bytes(manifest[12:14], "little") != 0x0FBF or \
            manifest[0x53:0x5C:3] != b"\xC3\xC3\xC3":
        fail("ABI 1.2 manifest or appended ROM vectors differ")

    with tempfile.TemporaryDirectory(prefix="network-rom-extended.") as name:
        temporary = Path(name)
        screens: dict[int, bytes] = {}
        successor_fixture, _ = network_rom.build(
            successor=True, abi_selftest=True,
        )
        run_fixture(
            trace, successor_fixture, temporary, "c7-modified-raw", 3,
        )
        for mode in range(4):
            fixture, _ = network_rom.build(
                extended=True, abi_selftest=True,
            )
            state, ram = run_fixture(
                trace, fixture, temporary, f"mode-{mode}", mode,
            )
            if state.get("video_console_mode") != str(mode):
                fail(f"mode {mode} selected {state.get('video_console_mode')}")
            if ram[0xD786:0xD789] != bytes((1, 0, ord("X"))):
                fail(f"mode {mode} translated/remapped key state differs")
            expected = render_transcript(
                b"Z\xC4Q!", locale=1, mode=mode,
            )
            screen = ram[0xD800:0xD800 + 9600]
            if screen != expected:
                fail(f"mode {mode} console-span framebuffer differs")
            screens[mode] = screen

        hidden_image, _ = network_rom.build(
            extended=True, abi_selftest=True, cursor_phase="hidden",
        )
        visible_image, _ = network_rom.build(
            extended=True, abi_selftest=True, cursor_phase="visible",
        )
        _, hidden_ram = run_fixture(
            trace, hidden_image, temporary, "integrated-cursor-hidden", 3,
        )
        _, visible_ram = run_fixture(
            trace, visible_image, temporary, "integrated-cursor-visible", 3,
        )
        hidden = hidden_ram[0xD800:0xD800 + 9600]
        visible = visible_ram[0xD800:0xD800 + 9600]
        if visible != screens[3] or hidden == visible:
            fail("console + local keyboard + cursor phases are not integrated")
        differing = sum(a != b for a, b in zip(hidden, visible))
        if differing not in (1, 2):
            fail(f"cursor phase changed {differing} framebuffer bytes")

        sound_image, _ = network_rom.build(
            extended=True, abi_selftest=True, sound_selftest=True,
        )
        sound_state, _ = run_fixture(
            trace, sound_image, temporary, "sound-complete-phrase", 3,
            max_cycles=30_000_000, realtime_hz=20_000_000, timeout=20,
        )
        # Twelve notes each write divisor-low/divisor-high/silence to channel
        # 1 (36 writes). The later diagnostic latch makes 15h the final
        # control byte, so the total 1Bh count, not its last value, proves all
        # 24 cue control writes plus the six ordinary setup/diagnostic writes.
        if sound_state.get("port_19") != "last:01,out:36,in:0" or \
                sound_state.get("port_1B") != "last:15,out:30,in:0":
            fail(
                "sound cue did not execute twelve notes and final silence: "
                f"19={sound_state.get('port_19')} "
                f"1B={sound_state.get('port_1B')}"
            )

    print(
        "NETWORK-FIRST-ROM-EXTENDED-TEST: PASS "
        f"{metadata['image_sha256']} {successor_metadata['image_sha256']} "
        "(immutable C6; C7 modified raw; four modes; integrated cursor/key)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
