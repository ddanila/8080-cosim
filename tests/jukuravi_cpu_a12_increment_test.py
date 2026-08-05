#!/usr/bin/env python3
"""Guard the single CPU increment fault against the physical T32 probes."""

from __future__ import annotations

import json
import os
import pty
import subprocess
import sys
import tempfile
import tty
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HOST = ROOT / "spinoffs" / "jukuravi" / "host.py"
FIRMWARE = ROOT / "spinoffs" / "jukuravi" / "firmware"
sys.path[:0] = [str(FIRMWARE), str(FIRMWARE.parent)]
import build_d0_waitclass as firmware  # noqa: E402


@dataclass(frozen=True)
class Probe:
    name: str
    image: Path
    result_address: int
    expected_clean: bytes
    expected_fault: bytes


def fail(message: str) -> None:
    print(f"JUKURAVI-CPU-A12-INCREMENT: FAIL: {message}", file=sys.stderr)
    raise SystemExit(1)


def lhld_classes(fault: bool) -> bytes:
    result = bytearray(b"L12C\xA5\x04\0\0")
    for lower, upper in (
        ((0x10, 0x11), (0x20, 0x21)),
        ((0x30, 0x31), (0x40, 0x41)),
        ((0x50, 0x51), (0x60, 0x61)),
        ((0x70, 0x71), (0x80, 0x81)),
    ):
        result.extend((*lower, *upper))
        result.extend(lower * 4)
        result.extend((upper[0], lower[1]) * 4 if fault else upper * 4)
    return bytes(result)


def write_map(fault: bool) -> bytes:
    result = bytearray(b"W12M\xA5\x04\0\0")
    result.extend((0, 0, 0, 0))
    result.extend((0x10, 0x11, 0, 0))
    result.extend((0x10, 0x11, 0x20, 0x21))
    result.extend((0x10, 0x11) * 4)
    result.extend(((0x20, 0x11) if fault else (0x20, 0x21)) * 4)
    # T32's cold-boot RAM survey leaves 55h in the CA pair.
    result.extend((0x55, 0x55, 0, 0))
    result.extend((0x55, 0x55, 0x80, 0x81))
    result.extend((0x70, 0x71, 0x80, 0x81))
    result.extend((0x70, 0x71) * 4)
    result.extend(((0x80, 0x71) if fault else (0x80, 0x81)) * 4)
    return bytes(result)


def instruction_classes(fault: bool) -> bytes:
    result = bytearray(b"I12C\xA5\x55\x55\x55")
    result.extend((0x10, 0x11))
    result.extend((0x20, 0x11) if fault else (0x20, 0x21))
    result.extend((0x30, 0x31))
    result.extend((0x40, 0x31) if fault else (0x40, 0x41))
    result.extend((0x50, 0x51, 0x60, 0x61))
    result.extend((0x50, 0xBB, 0xAA, 0x61) if fault else
                  (0x50, 0x51, 0xAA, 0xBB))
    result.extend(b"\x55" * 8)
    return bytes(result)


def ready_classes(fault: bool) -> bytes:
    result = bytearray(b"R12C\xA5\x04\x55\x55")
    for lower, upper in (
        ((0x10, 0x11), (0x20, 0x21)),
        ((0x30, 0x31), (0x40, 0x41)),
        ((0x50, 0x51), (0x60, 0x61)),
        ((0x70, 0x71), (0x80, 0x81)),
    ):
        result.extend((*lower, *upper))
        result.extend(((upper[0], lower[1]) if fault else upper) * 4)
    return bytes(result)


def boundary() -> bytes:
    return b"B12C\xA5\x55\x55\x55\x1F\x20\x2F\x40\x55\x55\x55\x55"


def increment_registers(fault: bool) -> bytes:
    result = bytearray(b"X12C\xA5\x55\x55\x55")
    result.extend((0x00, 0x10))
    result.extend((0x01, 0x0A) if fault else (0x01, 0x1A))
    result.extend((0x01, 0x4A) if fault else (0x01, 0x5A))
    result.extend((0x01, 0x8A) if fault else (0x01, 0x9A))
    result.extend((0x01, 0x1A))
    result.extend(b"\x55" * 6)
    return bytes(result)


def run_suite(trace: Path, rom: Path, probes: tuple[Probe, ...], fault: bool) -> None:
    with tempfile.TemporaryDirectory(prefix="jukuravi-cpu-a12-") as name:
        temp = Path(name)
        master, slave = pty.openpty()
        tty.setraw(slave)
        environment = os.environ.copy()
        environment.update(
            JUKU_USART_PTY=os.ttyname(slave),
            JUKU_USART_TRANSFER_CYCLES="64",
            JUKU_USART_BYTE_CYCLES="512",
            JUKU_PIT_FAULT="14:00:80",
        )
        if fault:
            environment["JUKU_CPU_A12_INCREMENT_FAULT"] = "1"
        stdout = (temp / "cosim.stdout").open("wb")
        stderr = (temp / "cosim.stderr").open("wb")
        process = subprocess.Popen(
            [str(trace), str(rom), "5000000000"],
            cwd=temp,
            env=environment,
            stdout=stdout,
            stderr=stderr,
        )
        stdout.close()
        stderr.close()
        try:
            for index, probe in enumerate(probes):
                logs = temp / probe.name
                command = [
                    sys.executable,
                    str(HOST),
                    "--fd", str(master),
                    "--timeout", "60",
                    "--loader-timeout", "30",
                    "--loader-guard-ms", "0",
                    "--loader-votes", "1",
                    "--load", str(probe.image),
                    "--load-address", "4000",
                    "--run-address", "4000",
                    "--run-mode", "call",
                    "--result-address", f"{probe.result_address:04X}",
                    "--result-length", str(len(probe.expected_clean)),
                    "--log-dir", str(logs),
                ]
                if index:
                    command.append("--attach-loader")
                else:
                    command.extend((
                        "--expect-rom-version", f"{firmware.ROM_VERSION:02X}",
                        "--expect-crc16", f"{int(firmware.build()[1]['checksum']):04X}",
                    ))
                host = subprocess.run(
                    command,
                    cwd=ROOT,
                    pass_fds=(master,),
                    text=True,
                    capture_output=True,
                    timeout=120,
                )
                if host.returncode:
                    fail(
                        f"{probe.name} {'fault' if fault else 'clean'} host failed:\n"
                        f"{host.stdout}{host.stderr}"
                    )
                summary = json.loads(next(logs.glob("*.json")).read_text())
                observed = bytes.fromhex(summary["loader"]["run"]["result"]["hex"])
                expected = probe.expected_fault if fault else probe.expected_clean
                if observed != expected:
                    fail(
                        f"{probe.name} {'fault' if fault else 'clean'} differs: "
                        f"expected {expected.hex().upper()}, got {observed.hex().upper()}"
                    )
        finally:
            if process.poll() is None:
                process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
            os.close(master)
            os.close(slave)


def main() -> int:
    if len(sys.argv) != 9:
        fail(
            "usage: test.py trace T32HOST.BIN "
            "lhld.bin write-map.bin instruction.bin ready.bin boundary.bin "
            "increment-registers.bin"
        )
    paths = tuple(Path(value).resolve() for value in sys.argv[1:])
    trace, rom = paths[:2]
    images = paths[2:]
    image, metadata = firmware.build()
    if not trace.is_file() or rom.read_bytes() != image or not all(p.is_file() for p in images):
        fail("trace, exact T32 image, or a probe image is missing/different")
    probes = (
        Probe("write-map", images[1], 0x4600, write_map(False), write_map(True)),
        Probe("lhld", images[0], 0x4800, lhld_classes(False), lhld_classes(True)),
        Probe("instruction", images[2], 0x4C00,
              instruction_classes(False), instruction_classes(True)),
        Probe("ready", images[3], 0x4F00, ready_classes(False), ready_classes(True)),
        Probe("boundary", images[4], 0x4E00, boundary(), boundary()),
        Probe("increment-registers", images[5], 0x4D00,
              increment_registers(False), increment_registers(True)),
    )
    if int(metadata["checksum"]) != 0xD62B:
        fail("unexpected T32 checksum")
    run_suite(trace, rom, probes, False)
    run_suite(trace, rom, probes, True)
    print("JUKURAVI-CPU-A12-INCREMENT: PASS (six clean/fault probe classes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
