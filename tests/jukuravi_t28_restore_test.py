#!/usr/bin/env python3
"""Prove T28 repairs stack/interrupt/serial state after a cooperative RET."""

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
import build_d0_buffer_verified as firmware  # noqa: E402


def fail(message: str) -> None:
    print(f"JUKURAVI-T28-RESTORE: FAIL: {message}", file=sys.stderr)
    raise SystemExit(1)


def main() -> int:
    if len(sys.argv) != 3:
        fail("usage: test.py /path/to/trace diag-d0-buffer-verified.bin")
    trace, rom_arg = (Path(value).resolve() for value in sys.argv[1:])
    image, metadata = firmware.build()
    if not trace.is_file() or rom_arg.read_bytes() != image:
        fail("trace or exact T28 image differs")

    # POP the ROM continuation, move it to a different stack, reset the 8251,
    # change its PIT clock from divisor 32 to 8, enable interrupts, and RET.
    # T28 must still restore its stack/DI/2400-baud hardware and report A=5Ah.
    payload = bytes(
        (
            0xE1,                    # POP H (ROM continuation)
            0x31, 0xF0, 0x4F,       # LXI SP,4FF0h
            0xE5,                    # PUSH H
            0x3E, 0xA5,             # MVI A,A5h
            0x32, 0x00, 0x41,       # STA 4100h (post-RET READ proof)
            0x3E, 0x40, 0xD3, 0x09, # MVI A,40h / OUT 8251 control (reset)
            0x3E, 0x34, 0xD3, 0x1B, # PIT channel-0 mode
            0x3E, 0x08, 0xD3, 0x18, # divisor low = 8
            0xAF, 0xD3, 0x18,       # divisor high = 0
            0xFB,                    # EI
            0x3E, 0x5A,             # returned A
            0xC9,                    # ordinary RET
        )
    )

    with tempfile.TemporaryDirectory(prefix="jukuravi-t28-restore-") as temp_name:
        temp = Path(temp_name)
        rom = temp / "t28.bin"
        snippet = temp / "dirty-ret.bin"
        logs = temp / "logs"
        rom.write_bytes(image)
        snippet.write_bytes(payload)
        master, slave = pty.openpty()
        tty.setraw(slave)
        environment = os.environ.copy()
        environment.update(
            JUKU_USART_PTY=os.ttyname(slave),
            JUKU_USART_TRANSFER_CYCLES="64",
            JUKU_USART_BYTE_CYCLES="512",
        )
        with (temp / "cosim.stdout").open("wb") as stdout, (
            temp / "cosim.stderr"
        ).open("wb") as stderr:
            cosim = subprocess.Popen(
                [str(trace), str(rom), "2000000000"],
                cwd=temp,
                env=environment,
                stdout=stdout,
                stderr=stderr,
            )
        try:
            result = subprocess.run(
                [
                    sys.executable,
                    str(HOST),
                    "--fd", str(master),
                    "--timeout", "60",
                    "--loader-timeout", "30",
                    "--loader-guard-ms", "0",
                    "--expect-rom-version", f"{firmware.ROM_VERSION:02X}",
                    "--expect-crc16", f"{int(metadata['checksum']):04X}",
                    "--load", str(snippet),
                    "--load-address", "4000",
                    "--run-address", "4000",
                    "--run-mode", "call",
                    "--result-address", "4100",
                    "--result-length", "1",
                    "--log-dir", str(logs),
                ],
                cwd=ROOT,
                pass_fds=(master,),
                text=True,
                capture_output=True,
                timeout=120,
            )
        finally:
            cosim.terminate()
            try:
                cosim.wait(timeout=5)
            except subprocess.TimeoutExpired:
                cosim.kill()
                cosim.wait()
            os.close(master)
            os.close(slave)

        if result.returncode:
            fail(f"real CLI failed after dirty RET:\n{result.stdout}{result.stderr}")
        summary = json.loads(next(logs.glob("*.json")).read_text())
        run = summary.get("loader", {}).get("run")
        if (
            not isinstance(run, dict)
            or run.get("return_a") != "0x5A"
            or run.get("result", {}).get("hex") != "A5"
        ):
            fail(f"restored RETURN evidence differs: {run!r}")

    print(
        "JUKURAVI-T28-RESTORE: PASS "
        "(RET survived foreign SP, EI, 8251 reset, and PIT baud change)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
