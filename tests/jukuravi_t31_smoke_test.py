#!/usr/bin/env python3
"""Prove the exact T31 ROM running the timed uploaded speaker demo."""

from __future__ import annotations

import json
import os
import pty
import re
import subprocess
import sys
import tempfile
import tty
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HOST = ROOT / "spinoffs" / "jukuravi" / "host.py"
FIRMWARE = ROOT / "spinoffs" / "jukuravi" / "firmware"
PAYLOAD = FIRMWARE / "smoke-4000.bin"
sys.path[:0] = [str(FIRMWARE), str(FIRMWARE.parent)]
import build_d0_low4k as firmware  # noqa: E402


DIVISORS = (
    5102, 4290, 3822, 5102, 4290, 3608,
    3822, 5102, 4290, 3822, 4290, 5102,
)
TONE_UNITS = (1, 1, 2, 1, 1, 1, 2, 1, 1, 2, 1, 5)
GAP_UNITS = (1, 1, 1, 1, 1, 0, 2, 1, 1, 1, 1, 2)
EIGHTH_CYCLES = 2_000_000 * 60 / 112 / 2
TIMING_TOLERANCE_CYCLES = 2500
IO_PATTERN = re.compile(
    r"\[IOSEQ\] OUT port=0x(19|1B) value=0x([0-9A-F]{2}) "
    r"cyc=(\d+) pc=([0-9A-F]{4})"
)


def fail(message: str) -> None:
    print(f"JUKURAVI-T31-SMOKE: FAIL: {message}", file=sys.stderr)
    raise SystemExit(1)


def main() -> int:
    if len(sys.argv) != 3:
        fail("usage: test.py /path/to/trace diag-d0-low4k.bin")
    trace, rom_arg = (Path(value).resolve() for value in sys.argv[1:])
    image, metadata = firmware.build()
    if not trace.is_file() or rom_arg.read_bytes() != image:
        fail("trace or exact T31 image differs")
    if sum(TONE_UNITS) + sum(GAP_UNITS) != 32:
        fail("timing table is not four complete 4/4 bars")

    with tempfile.TemporaryDirectory(prefix="jukuravi-t31-smoke-") as temp_name:
        temp = Path(temp_name)
        logs = temp / "logs"
        master, slave = pty.openpty()
        tty.setraw(slave)
        environment = os.environ.copy()
        environment.update(
            JUKU_USART_PTY=os.ttyname(slave),
            JUKU_USART_TRANSFER_CYCLES="64",
            JUKU_USART_BYTE_CYCLES="512",
            JUKU_TRACE_IO="1",
        )
        stdout_path = temp / "cosim.stdout"
        stderr_path = temp / "cosim.stderr"
        with stdout_path.open("wb") as stdout, stderr_path.open("wb") as stderr:
            cosim = subprocess.Popen(
                [str(trace), str(rom_arg), "3000000000"],
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
                    "--loader-votes", "1",
                    "--expect-rom-version", f"{firmware.ROM_VERSION:02X}",
                    "--expect-crc16", f"{int(metadata['checksum']):04X}",
                    "--load", str(PAYLOAD),
                    "--load-address", "4000",
                    "--run-address", "4000",
                    "--run-mode", "call",
                    "--no-loader-readback",
                    "--result-address", "4100",
                    "--result-length", "5",
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
            fail(f"host failed:\n{host.stdout}{host.stderr}")
        summary = json.loads(next(logs.glob("*.json")).read_text())
        loader = summary.get("loader")
        if not isinstance(loader, dict):
            fail("loader evidence is absent")
        chunks = loader.get("chunks")
        if (
            loader.get("bytes") != len(PAYLOAD.read_bytes())
            or not isinstance(chunks, list)
            or len(chunks) != 5
            or any(
                chunk.get("attempts") != 1
                or chunk.get("crc_attempts") != 1
                or chunk.get("store_retries") != 0
                or chunk.get("verified") is not True
                for chunk in chunks
            )
        ):
            fail(f"CRC-verified upload evidence differs: {chunks!r}")
        run = loader.get("run")
        if (
            not isinstance(run, dict)
            or run.get("returned") is not True
            or run.get("return_a") != "0x0C"
            or run.get("result", {}).get("hex") != "534D4F4B00"
        ):
            fail(f"CALL/RET completion evidence differs: {run!r}")

        outputs: list[tuple[int, int, int]] = []
        for line in stderr_path.read_text().splitlines():
            match = IO_PATTERN.search(line)
            if not match:
                continue
            port = int(match.group(1), 16)
            value = int(match.group(2), 16)
            cycle = int(match.group(3))
            pc = int(match.group(4), 16)
            if 0x4000 <= pc < 0x4100:
                outputs.append((port, value, cycle))

        expected_values: list[tuple[int, int]] = []
        for divisor in DIVISORS:
            expected_values.extend(
                [
                    (0x1B, 0x76),
                    (0x19, divisor & 0xFF),
                    (0x19, divisor >> 8),
                    (0x1B, 0x50),
                    (0x19, 0x01),
                ]
            )
        if [(port, value) for port, value, _cycle in outputs] != expected_values:
            fail(f"speaker PIT sequence differs: {outputs!r}")

        onsets = [outputs[index * 5][2] for index in range(len(DIVISORS))]
        for index, (first, second) in enumerate(zip(onsets, onsets[1:])):
            expected = (TONE_UNITS[index] + GAP_UNITS[index]) * EIGHTH_CYCLES
            if abs((second - first) - expected) > TIMING_TOLERANCE_CYCLES:
                fail(
                    f"note {index + 1} onset delta {second - first} "
                    f"differs from {expected:.1f} cycles"
                )

    print(
        "JUKURAVI-T31-SMOKE: PASS "
        "(exact T31; 12 notes; 4 bars; 112 BPM; PIT sequence; CRC upload; RET)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
