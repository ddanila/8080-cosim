#!/usr/bin/env python3
"""Execute the RAM A12-alias matrix clean and with page-selective faulting."""

from __future__ import annotations

import json
import os
import pty
import subprocess
import sys
import tempfile
import tty
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HOST = ROOT / "spinoffs" / "jukuravi" / "host.py"
FIRMWARE = ROOT / "spinoffs" / "jukuravi" / "firmware"
sys.path[:0] = [str(FIRMWARE), str(FIRMWARE.parent)]
import build_d0_waitclass as firmware  # noqa: E402


def fail(message: str) -> None:
    print(f"JUKURAVI-RAM-A12-ALIAS: FAIL: {message}", file=sys.stderr)
    raise SystemExit(1)


def expected_result(fault: bool) -> bytes:
    result = bytearray(b"A12M\x04\xA5\x00\x00")
    classes = (
        (0x1A, bytes((0x20, 0x21)), bytes((0x10, 0x11))),
        (0x5A, bytes((0x40, 0x41)), bytes((0x30, 0x31))),
        (0x9A, bytes((0x60, 0x61)), bytes((0x50, 0x51))),
        (0xDA, bytes((0x80, 0x81)), bytes((0x70, 0x71))),
    )
    for high, target, alias in classes:
        observed = (
            bytes((target[0], alias[1]))
            if fault and high in (0x1A, 0xDA)
            else target
        )
        result.extend((high, *target, *alias))
        result.extend(observed * 4)
    return bytes(result)


def run_case(trace: Path, rom: Path, probe: Path, fault: bool) -> None:
    with tempfile.TemporaryDirectory(prefix="jukuravi-ram-a12-") as name:
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
            environment["JUKU_CONSECUTIVE_A12_LOW_PAGES"] = "1,D"
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
        logs = temp / "host"
        command = [
            sys.executable,
            str(HOST),
            "--fd", str(master),
            "--timeout", "60",
            "--loader-timeout", "30",
            "--loader-guard-ms", "0",
            "--loader-votes", "1",
            "--expect-rom-version", f"{firmware.ROM_VERSION:02X}",
            "--expect-crc16", f"{int(firmware.build()[1]['checksum']):04X}",
            "--load", str(probe),
            "--load-address", "4000",
            "--run-address", "4000",
            "--run-mode", "call",
            "--result-address", "4400",
            "--result-length", "60",
            "--log-dir", str(logs),
        ]
        try:
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
                    f"{'fault' if fault else 'clean'} host failed:\n"
                    f"{host.stdout}{host.stderr}"
                )
            summary = json.loads(next(logs.glob("*.json")).read_text())
            observed = bytes.fromhex(summary["loader"]["run"]["result"]["hex"])
            expected = expected_result(fault)
            if observed != expected:
                fail(
                    f"{'fault' if fault else 'clean'} matrix differs: "
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
    if len(sys.argv) != 4:
        fail("usage: test.py /path/to/trace T32HOST.BIN ram-a12-alias.bin")
    trace, rom, probe = (Path(value).resolve() for value in sys.argv[1:])
    image, _ = firmware.build()
    if not trace.is_file() or rom.read_bytes() != image or not probe.is_file():
        fail("trace, exact T32 image, or probe is missing/different")
    run_case(trace, rom, probe, False)
    run_case(trace, rom, probe, True)
    print("JUKURAVI-RAM-A12-ALIAS: PASS (clean and pages 1/D fault matrix)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
