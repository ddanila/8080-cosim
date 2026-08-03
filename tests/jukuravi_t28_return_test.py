#!/usr/bin/env python3
"""Prove T28 CALL/RET, returned A, and host-directed RAM result reads."""

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
    print(f"JUKURAVI-T28-RETURN: FAIL: {message}", file=sys.stderr)
    raise SystemExit(1)


def main() -> int:
    if len(sys.argv) != 3:
        fail("usage: test.py /path/to/trace diag-d0-buffer-verified.bin")
    trace, rom_arg = (Path(value).resolve() for value in sys.argv[1:])
    image, metadata = firmware.build()
    if not trace.is_file() or rom_arg.read_bytes() != image:
        fail("trace or exact T28 image differs")

    with tempfile.TemporaryDirectory(prefix="jukuravi-t28-return-") as temp_name:
        temp = Path(temp_name)
        rom = temp / "t28.bin"
        logs = temp / "logs"
        rom.write_bytes(image)
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
            host = subprocess.run(
                [
                    sys.executable,
                    str(HOST),
                    "--fd", str(master),
                    "--timeout", "60",
                    "--loader-timeout", "30",
                    "--loader-guard-ms", "0",
                    "--expect-rom-version", f"{firmware.ROM_VERSION:02X}",
                    "--expect-crc16", f"{int(metadata['checksum']):04X}",
                    "--load", str(FIRMWARE / "return-4000.bin"),
                    "--load-address", "4000",
                    "--run-address", "4000",
                    "--run-mode", "call",
                    "--no-loader-readback",
                    "--result-address", "4100",
                    "--result-length", "8",
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

        if host.returncode:
            fail(f"real CLI failed:\n{host.stdout}{host.stderr}")
        summary = json.loads(next(logs.glob("*.json")).read_text())
        loader = summary["loader"]
        run = loader["run"]
        if (
            loader["status"] != "returned"
            or run.get("mode") != "call"
            or run.get("returned") is not True
            or run.get("return_a") != "0x42"
        ):
            fail(f"CALL/RET evidence differs: {run!r}")
        result = run.get("result")
        if not isinstance(result, dict) or result.get("hex") != "5432385245542100":
            fail(f"returned RAM result differs: {result!r}")
        chunks = loader.get("chunks")
        if (
            not isinstance(chunks, list)
            or any(not chunk.get("verified") or "crc_attempts" not in chunk for chunk in chunks)
        ):
            fail(f"CRC-only post-write verification differs: {chunks!r}")

    print(
        "JUKURAVI-T28-RETURN: PASS "
        "(CRC verify; RET; A=42h; RAM result; loader resumed)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
