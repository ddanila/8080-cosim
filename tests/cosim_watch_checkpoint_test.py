#!/usr/bin/env python3
"""Prove watched write transitions are captured atomically in checkpoints."""

from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys
import tempfile


WATCH_ADDRESS = 0xC123


def fail(message: str) -> None:
    print(f"COSIM-WATCH-CHECKPOINT-TEST: FAIL: {message}", file=sys.stderr)
    raise SystemExit(1)


def parse_state(path: Path) -> dict[str, str]:
    return dict(
        line.split("=", 1)
        for line in path.read_text().splitlines()
        if "=" in line
    )


def main() -> int:
    if len(sys.argv) != 2:
        fail("usage: test.py /path/to/cosim-trace")
    trace = Path(sys.argv[1]).resolve()
    if not trace.is_file():
        fail("missing cosim executable")

    # MVI A,1; STA C123h; MVI A,0; STA C123h; HLT.  The remainder of the
    # 16 KiB monitor image is inert so the test owns every watched write.
    program = bytes((
        0x3E, 0x01,
        0x32, WATCH_ADDRESS & 0xFF, WATCH_ADDRESS >> 8,
        0x3E, 0x00,
        0x32, WATCH_ADDRESS & 0xFF, WATCH_ADDRESS >> 8,
        0x76,
    ))
    with tempfile.TemporaryDirectory(prefix="cosim-watch-checkpoint.") as name:
        work = Path(name)
        rom = work / "watch.bin"
        prefix = work / "checkpoint"
        rom.write_bytes(program.ljust(0x4000, b"\x00"))
        environment = {
            **os.environ,
            "JUKU_CHECKPOINT_PREFIX": str(prefix),
            "JUKU_WATCH_ADDRESS": hex(WATCH_ADDRESS),
            "JUKU_TRACE_BANK": "0",
        }
        completed = subprocess.run(
            [str(trace), str(rom), "1000"],
            cwd=work,
            env=environment,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=60,
            check=False,
        )
        if completed.returncode != 0:
            fail(
                f"cosim exited {completed.returncode}: "
                f"{completed.stderr[-300:]}"
            )
        state = parse_state(prefix.with_suffix(".state"))

    expected = {
        "watch_write_count": "2",
        "watch_write_previous_address": f"{WATCH_ADDRESS:04X}",
        "watch_write_previous_value": "01",
        "watch_write_last_address": f"{WATCH_ADDRESS:04X}",
        "watch_write_last_value": "00",
    }
    for key, value in expected.items():
        if state.get(key) != value:
            fail(f"checkpoint {key}={state.get(key)!r}, expected {value!r}")
    previous_cycle = int(state["watch_write_previous_cycle"])
    last_cycle = int(state["watch_write_last_cycle"])
    checkpoint_cycle = int(state["cyc"])
    if not 0 < previous_cycle < last_cycle <= checkpoint_cycle:
        fail(
            "watched cycles are not ordered inside the checkpoint: "
            f"{previous_cycle}, {last_cycle}, {checkpoint_cycle}"
        )

    print(
        "COSIM-WATCH-CHECKPOINT-TEST: PASS "
        f"(writes 1->0 at cycles {previous_cycle}->{last_cycle})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
