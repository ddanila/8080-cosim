#!/usr/bin/env python3
"""Prove C12 ABI 1.5 runtime console switching across its 4x4 matrix."""

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
FIRMWARE = ROOT / "spinoffs" / "jukuravi" / "network-rom"
sys.path.insert(0, str(ROOT / "third_party" / "juku-common" / "tools"))
sys.path.insert(0, str(FIRMWARE))
from creep_console_oracle import render_transcript  # noqa: E402
import build_network_rom as network_rom  # noqa: E402


C11_SHA256 = "b93428bb33cd7e31c2d9b2b84aa07ea17edda76c9d53ab73b3cb8687e8d53dfd"


def fail(message: str) -> None:
    raise SystemExit(f"NETWORK-FIRST-ROM-C12-TEST: FAIL: {message}")


def run_fixture(trace: Path, image: bytes, case: Path, *, mode: int,
                bank: int) -> tuple[dict[str, str], bytes]:
    rom = case / "rom.bin"
    rom.write_bytes(image)
    checkpoint = case / "checkpoint"
    master, slave = pty.openpty()
    tty.setraw(slave)
    default_mode = (mode + 2) & 3
    default_bank = (bank + 2) & 3
    environment = os.environb.copy()
    environment.update({
        b"JUKU_USART_PTY": os.fsencode(os.ttyname(slave)),
        b"JUKU_USART_TRANSFER_CYCLES": b"16",
        b"JUKU_USART_BYTE_CYCLES": b"1024",
        b"JUKU_USART_PIT_CLOCK": b"1",
        b"JUKU_USART_PIT_CPU_HZ": b"1700000",
        b"JUKU_CHECKPOINT_PREFIX": os.fsencode(checkpoint),
        b"JUKU_REALTIME_HZ": b"1700000",
        b"JUKU_KEYS": b"T",
        b"JUKU_KEY_START_VRAM": b"0",
        b"JUKU_S21_CONFIG": (
            f"0x{(default_bank << 3) | (default_mode << 1):02X}"
        ).encode("ascii"),
    })
    process = subprocess.Popen(
        [str(trace), str(rom), "6000000"], cwd=case, env=environment,
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
            fail(f"mode {mode}/bank {bank} serial output differs: {received!r}")
        os.write(master, b"\xC3")
        process.wait(timeout=25.0)
    finally:
        if process.poll() is None:
            process.kill()
            process.wait()
        os.close(master)
    stderr = process.stderr.read().decode(errors="replace") \
        if process.stderr is not None else ""
    if process.returncode != 0:
        fail(f"mode {mode}/bank {bank} cosim exited "
             f"{process.returncode}: {stderr[-1000:]}")
    state = dict(
        line.split("=", 1)
        for line in checkpoint.with_suffix(".state").read_text().splitlines()
        if "=" in line
    )
    ram = checkpoint.with_suffix(".ram").read_bytes()
    if state.get("halted") != "1" or state.get("mode") != "1" or \
            state.get("iff") != "0" or ram[0xD783] != 0xA5:
        fail(f"mode {mode}/bank {bank} did not finish safely: {state}")
    return state, ram


def main() -> int:
    if len(sys.argv) != 2:
        fail("usage: test.py /path/to/trace")
    trace = Path(sys.argv[1]).resolve()
    image, metadata = network_rom.build(c12=True)
    if image != network_rom.C12_OUTPUT.read_bytes():
        fail("committed C12 image differs from deterministic rebuild")
    if network_rom.digest(network_rom.build(c11=True)[0]) != C11_SHA256:
        fail("C12 work changed the immutable C11 ROM")
    if metadata.get("candidate") != \
            "network-first-abi1.5-c12-runtime-console-candidate" or \
            metadata.get("abi") != {"base": "FF00", "major": 1, "minor": 5} or \
            metadata.get("feature_bits", {}).get("value") != "1FFF" or \
            metadata.get("abi_vectors", {}).get("console_config") != "FF5F" or \
            metadata.get("boot_discovery", {}).get("frame") != \
            "4A 42 0C 01 05" or \
            metadata.get("runtime_console", {}).get(
                "keyboard_transition") != {
                    "pending_state": "discard", "key_remap": "preserve",
                } or metadata.get("gate_bytes") != 224 or \
            metadata.get("rom_envelope_padding_bytes") != {
                "resident_and_diagnostics_D800_EFFF": 154,
                "locale_console_F000_F7FF": 839,
                "resident_host_F800_FEFF": 896,
                "abi_manifest_vectors_FF00_FFFF": 158,
            }:
        fail(f"C12 metadata differs: {metadata}")
    manifest = image[0x3F00:0x3F63]
    if manifest[:10] != b"JUKUABI\0\x01\x05" or \
            int.from_bytes(manifest[12:14], "little") != 0x1FFF or \
            manifest[0x5F] != 0xC3:
        fail("C12 ABI manifest or console-config vector differs")

    with tempfile.TemporaryDirectory(prefix="network-rom-c12.") as name:
        temporary = Path(name)
        default_fixture, _ = network_rom.build(
            c12=True, abi_selftest=True,
        )
        default_case = temporary / "default-remap"
        default_case.mkdir()
        _, default_ram = run_fixture(
            trace, default_fixture, default_case, mode=1, bank=3,
        )
        if default_ram[0xD7FD] != 0x0E or default_ram[0xD7FE] != 0 or \
                default_ram[0xD7C2:0xD7C5] != b"\x01TX":
            fail(
                "default transition did not preserve remap: "
                f"active={default_ram[0xD7FD]:02X} "
                f"flags={default_ram[0xD7FE]:02X} "
                f"remap={default_ram[0xD7C2:0xD7C5].hex()}"
            )
        for bank in range(4):
            for mode in range(4):
                fixture, _ = network_rom.build(
                    c12=True,
                    abi_selftest=True,
                    selftest_locale=(bank + 2) & 3,
                    runtime_console_target=(mode, bank),
                )
                case = temporary / f"mode-{mode}-bank-{bank}"
                case.mkdir()
                state, ram = run_fixture(
                    trace, fixture, case, mode=mode, bank=bank,
                )
                default_mode = (mode + 2) & 3
                default_bank = (bank + 2) & 3
                default_config = (default_bank << 3) | (default_mode << 1)
                active_config = (bank << 3) | (mode << 1)
                if state.get("video_console_mode") != str(mode) or \
                        ram[0xD7C1] != default_config or \
                        ram[0xD7FD] != active_config or ram[0xD7FE] != 3:
                    fail(
                        f"mode {mode}/bank {bank} did not retain distinct "
                        f"default and active state: default={ram[0xD7C1]:02X} "
                        f"active={ram[0xD7FD]:02X} flags={ram[0xD7FE]:02X} "
                        f"video={state.get('video_console_mode')}"
                    )
                if ram[0xD7C2:0xD7C5] != b"\x01TX":
                    fail(
                        f"mode {mode}/bank {bank} erased persistent remap: "
                        f"{ram[0xD7C2:0xD7C5].hex()}"
                    )
                transcript = b"Z\xC4Q!"
                if mode == 3:
                    # All 26 supported glyphs plus unsupported neighbors.
                    # The old 17-entry search omitted D9/DA and nine total
                    # table entries despite the source containing 26 glyphs.
                    transcript += bytes(range(0xB0, 0xE0))
                expected = render_transcript(transcript, locale=bank, mode=mode)
                observed = ram[0xD800:0xD800 + 9600]
                if observed != expected:
                    differences = [
                        index for index, pair in enumerate(zip(observed, expected))
                        if pair[0] != pair[1]
                    ]
                    fail(
                        f"mode {mode}/bank {bank} framebuffer differs at "
                        f"{differences[:8]}"
                    )
                if any(ram[0xD800 + 9600:0xD800 + 9648]):
                    fail(f"mode {mode}/bank {bank} left stale raster-tail bytes")

    print(
        "NETWORK-FIRST-ROM-C12-TEST: PASS "
        f"{metadata['image_sha256']} (ABI 1.5; immutable C11; checked JB/12; "
        "invalid requests atomic; 4x4 runtime mode/bank matrix; retained "
        "override and key remap)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
