#!/usr/bin/env python3
"""Prove the network-first ROM ABI skeleton and low-RAM call gate."""

from __future__ import annotations

import errno
import os
import pty
import select
import subprocess
import sys
import tempfile
import time
import tty
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FIRMWARE = ROOT / "spinoffs" / "jukuravi" / "network-rom"
sys.path.insert(0, str(FIRMWARE))
import build_network_rom as network_rom  # noqa: E402


def fail(message: str) -> None:
    raise SystemExit(f"NETWORK-FIRST-ROM-ABI-TEST: {message}")


def parse_state(path: Path) -> dict[str, str]:
    return dict(
        line.split("=", 1) for line in path.read_text().splitlines()
        if "=" in line
    )


def main() -> int:
    if len(sys.argv) != 2:
        fail("usage: test.py /path/to/trace")
    trace = Path(sys.argv[1]).resolve()
    image, metadata = network_rom.build()
    selftest_image, _ = network_rom.build(abi_selftest=True)
    committed = network_rom.OUTPUT.read_bytes()
    if committed != image:
        fail("committed combined ROM differs from deterministic rebuild")
    if len(image) != 0x4000:
        fail(f"combined image is {len(image)} bytes, expected 16384")
    if network_rom.D15_OUTPUT.read_bytes() != image[:0x2000] or \
            network_rom.D16_OUTPUT.read_bytes() != image[0x2000:]:
        fail("D15/D16 split does not reproduce the combined image")
    if metadata["status"] != \
            "automatic-boot desk image; not for physical programming":
        fail("skeleton artifact lost its programming prohibition")
    manifest = image[0x3F00:0x3F20]
    if manifest[:10] != b"JUKUABI\0\x01\x00":
        fail(f"ABI signature/version differs: {manifest[:10].hex()}")
    if int.from_bytes(manifest[10:12], "little") != 0x100:
        fail("ABI table size differs")
    if int.from_bytes(manifest[12:14], "little") != 0x24:
        fail("skeleton advertises unexpected features")
    if int.from_bytes(manifest[16:18], "little") != 0x200:
        fail("ABI workspace size differs")
    if int.from_bytes(manifest[18:20], "little") != metadata["helper_bytes"]:
        fail("ABI helper size differs from the copied image")

    with tempfile.TemporaryDirectory(prefix="network-first-rom-abi.") as name:
        temporary = Path(name)
        rom = temporary / "network-rom.bin"
        rom.write_bytes(selftest_image)
        checkpoint = temporary / "checkpoint"
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
            JUKU_TRACE_BANK="1",
            JUKU_REALTIME_HZ="1700000",
        )
        process = subprocess.Popen(
            [str(trace), str(rom), "2000000"], cwd=temporary,
            env=environment, stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
        )
        os.close(slave)
        try:
            received = bytearray()
            deadline = time.monotonic() + 5.0
            while b"ABI1" not in received and time.monotonic() < deadline:
                ready, _, _ = select.select([master], [], [], 0.05)
                if ready:
                    try:
                        received.extend(os.read(master, 4096))
                    except OSError as error:
                        if error.errno != errno.EIO:
                            raise
                        time.sleep(0.01)
            if bytes(received) != b"ABI1":
                fail(f"serial ABI output differs: {bytes(received)!r}")
            # The ROM has crossed the manifest, video-helper, diagnostic, and
            # four transmit calls. Supply the awaited byte while its bounded
            # receive service and the serial link are both live.
            os.write(master, b"\xC3")
            process.wait(timeout=20.0)
            os.set_blocking(master, False)
            while True:
                try:
                    chunk = os.read(master, 4096)
                except BlockingIOError:
                    break
                except OSError:
                    break
                if not chunk:
                    break
                received.extend(chunk)
        finally:
            if process.poll() is None:
                process.kill()
                process.wait()
            os.close(master)
        stderr = process.stderr.read().decode(errors="replace") \
            if process.stderr is not None else ""
        if process.returncode != 0:
            fail(f"cosim exited {process.returncode}: {stderr[-800:]}")
        if bytes(received) != b"ABI1":
            fail(f"serial ABI output differs: {bytes(received)!r}")

        state = parse_state(checkpoint.with_suffix(".state"))
        ram = checkpoint.with_suffix(".ram").read_bytes()
        for key, expected in (
            ("halted", "1"), ("iff", "0"), ("mode", "1"),
            ("portc", "81"), ("sp", "D5F0"), ("pic_icw1", "D6"),
            ("pic_icw2", "FE"), ("pic_mask", "FF"),
            ("ppi1_control", "9B"),
            ("usart_mode", "4E"), ("usart_command", "35"),
            ("usart_tx_bytes", "4"), ("usart_rx_bytes", "1"),
        ):
            if state.get(key) != expected:
                fail(f"checkpoint {key}={state.get(key)}, expected {expected}")
        if state.get("port_18", "").split(",", 1)[0] != "last:04" or \
                state.get("port_1B", "").split(",", 1)[0] != "last:15":
            fail("serial ABI did not select D57 mode 2/count 4")
        for port, expected in (
            ("07", "0F"), ("10", "64"), ("11", "24"), ("12", "08"),
            ("14", "01"), ("15", "00"), ("16", "25"), ("17", "34"),
            ("1A", "FF"),
        ):
            if state.get(f"port_{port}", "").split(",", 1)[0] != \
                    f"last:{expected}":
                fail(f"reset hardware initialization lost port {port}")

        gate_bytes = int(metadata["gate_bytes"])
        helper_bytes = int(metadata["helper_bytes"])
        expected_gate = bytearray(
            selftest_image[0x1000:0x1000 + gate_bytes]
        )
        signature_offset = expected_gate.rfind(b"JUKUABI\0")
        if signature_offset <= 0:
            fail("stored gate has no local ABI signature")
        expected_gate[signature_offset - 1] = 1  # JCGREADY after init
        if ram[0xD620:0xD620 + gate_bytes] != expected_gate:
            fail("boot did not install the low-RAM call gate byte-exactly")
        if ram[0xD700:0xD700 + helper_bytes] != \
                selftest_image[0x1400:0x1400 + helper_bytes]:
            fail("boot did not install the mode-3 helper byte-exactly")
        if ram[0xD783] != 0xA5:
            fail(f"resident self-test status is {ram[0xD783]:02X}")
        if ram[0xD780] != 0x5A or ram[0xD782] != 0x5A:
            fail("mode-3 helper did not preserve and read back its test byte")
        if ram[0xD800] != 0x5A:
            fail("mode-3 helper did not reach underlying framebuffer RAM")
        if ram[0xD801] != 0x00:
            fail("mode-1 write unexpectedly passed through the ROM overlay")
        if ram[0xD5C0:0xD5D0] != b"\xA6" * 16 or \
                ram[0xD5F0:0xD600] != b"\xA6" * 16:
            fail("ABI calls crossed a stack guard")
        if "[BANK] mode 0 -> 1" not in stderr or \
                "[BANK] mode 1 -> 3" not in stderr or \
                "[BANK] mode 3 -> 1" not in stderr:
            fail("mode transition evidence is incomplete")
        if stderr.rfind("[BANK] mode 3 -> 1") < stderr.rfind("[BANK] mode 1 -> 3"):
            fail("mode-3 helper did not finish in resident-ROM mode")

    print(
        "NETWORK-FIRST-ROM-ABI-TEST: PASS "
        f"{metadata['image_sha256']} "
        f"(gate={metadata['gate_bytes']}, helper={metadata['helper_bytes']})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
