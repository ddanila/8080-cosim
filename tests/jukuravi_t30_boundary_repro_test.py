#!/usr/bin/env python3
"""Reproduce the physical T30 banner/status/reset cycle at ROM address 1000h."""

from __future__ import annotations

import os
import pty
import subprocess
import sys
import tempfile
import time
import tty
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HOST = ROOT / "spinoffs" / "jukuravi" / "host.py"
FIRMWARE = ROOT / "spinoffs" / "jukuravi" / "firmware"
sys.path[:0] = [str(FIRMWARE), str(FIRMWARE.parent)]
import build_d0_txready as firmware  # noqa: E402


def fail(message: str) -> None:
    print(f"JUKURAVI-T30-BOUNDARY-REPRO: FAIL: {message}", file=sys.stderr)
    raise SystemExit(1)


def main() -> int:
    if len(sys.argv) != 3:
        fail("usage: test.py /path/to/trace diag-d0-txready.bin")
    trace, rom_arg = (Path(value).resolve() for value in sys.argv[1:])
    image, metadata = firmware.build()
    if not trace.is_file() or rom_arg.read_bytes() != image:
        fail("trace or exact T30 image differs")

    banner = bytes(metadata["banner"])
    peripheral = bytes.fromhex("a5 5a 50 01 08 09")
    ram = bytes.fromhex("a5 5a 50 01 83 b1")
    with tempfile.TemporaryDirectory(prefix="jukuravi-t30-boundary-") as name:
        temp = Path(name)
        logs = temp / "logs"
        rom = temp / "t30.bin"
        rom.write_bytes(image)
        master, slave = pty.openpty()
        tty.setraw(slave)
        environment = os.environ.copy()
        environment.update(
            JUKU_USART_PTY=os.ttyname(slave),
            JUKU_USART_TRANSFER_CYCLES="64",
            JUKU_USART_BYTE_CYCLES="512",
            JUKU_ROM_EXEC_RESET_AT="0x1000",
            JUKU_PIT_FAULT="14:00:80",
        )
        with (temp / "cosim.stdout").open("wb") as stdout, (
            temp / "cosim.stderr"
        ).open("wb") as stderr:
            cosim = subprocess.Popen(
                [str(trace), str(rom), "2500000000"],
                cwd=temp,
                env=environment,
                stdout=stdout,
                stderr=stderr,
            )
        host = subprocess.Popen(
            [
                sys.executable,
                str(HOST),
                "--fd", str(master),
                "--timeout", "30",
                "--loader-timeout", "30",
                "--loader-guard-ms", "0",
                "--expect-rom-version", f"{firmware.ROM_VERSION:02X}",
                "--expect-crc16", f"{int(metadata['checksum']):04X}",
                "--probe-loader",
                "--log-dir", str(logs),
            ],
            cwd=ROOT,
            pass_fds=(master,),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        raw = b""
        try:
            deadline = time.monotonic() + 20
            while time.monotonic() < deadline:
                files = list(logs.glob("*.rx.bin"))
                if files:
                    raw = files[0].read_bytes()
                    if (
                        raw.count(banner) >= 3
                        and raw.count(peripheral) >= 3
                        and raw.count(ram) >= 3
                    ):
                        break
                time.sleep(0.05)
        finally:
            host.terminate()
            cosim.terminate()
            for process in (host, cosim):
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()
            os.close(master)
            os.close(slave)

        stderr_text = (temp / "cosim.stderr").read_text()
        if raw.count(banner) < 3:
            fail(f"only {raw.count(banner)} repeated banners captured")
        if raw.count(peripheral) < 3 or raw.count(ram) < 3:
            fail(
                "repeated status counts differ: "
                f"banner={raw.count(banner)} peripheral={raw.count(peripheral)} "
                f"ram={raw.count(ram)} raw={raw.hex(' ')}"
            )
        if any(marker in raw for marker in bytes((0xE0, 0xE1, 0xE2, 0xE3))):
            fail("post-diagnostic marker escaped across the forced boundary")
        if "at ROM pc=100C boundary=1000" not in stderr_text:
            fail("cosim did not reset exact T30 post-diagnostic entry 100Ch")

    print(
        "JUKURAVI-T30-BOUNDARY-REPRO: PASS "
        "(three exact banner/08/83/reset cycles; PC=100C; no E0)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
