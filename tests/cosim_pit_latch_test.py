#!/usr/bin/env python3
"""Exercise the cosim 8253 load/latch/read slice through synthetic 8080 code."""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
from pathlib import Path


def mvi_out(program: bytearray, value: int, port: int) -> None:
    program.extend((0x3E, value, 0xD3, port))


def build_rom() -> bytes:
    program = bytearray()

    # D54 channel 0: LSB/MSB mode 0, then the 8253 latch command.
    mvi_out(program, 0x30, 0x13)
    mvi_out(program, 0x34, 0x10)
    mvi_out(program, 0x12, 0x10)
    mvi_out(program, 0x00, 0x13)
    program.extend((0xDB, 0x10, 0x47))  # IN 10 / MOV B,A: 34
    program.extend((0xDB, 0x10, 0x4F))  # IN 10 / MOV C,A: 12

    # D54 channel 1: LSB-only mode 0.
    mvi_out(program, 0x50, 0x13)
    mvi_out(program, 0xA5, 0x11)
    mvi_out(program, 0x40, 0x13)
    program.extend((0xDB, 0x11, 0x57))  # MOV D,A

    # D54 channel 2: MSB-only mode 0.
    mvi_out(program, 0xA0, 0x13)
    mvi_out(program, 0x5A, 0x12)
    mvi_out(program, 0x80, 0x13)
    program.extend((0xDB, 0x12, 0x5F))  # MOV E,A

    # Touch a counter/control register pair on each remaining decoded PIT.
    mvi_out(program, 0x10, 0x17)
    mvi_out(program, 0x96, 0x14)
    mvi_out(program, 0x00, 0x17)
    program.extend((0xDB, 0x14, 0x67))  # MOV H,A

    mvi_out(program, 0xA0, 0x1B)
    mvi_out(program, 0x68, 0x1A)
    mvi_out(program, 0x80, 0x1B)
    program.extend((0xDB, 0x1A, 0x6F))  # MOV L,A
    program.append(0x76)                # HLT

    return bytes(program).ljust(0x4000, b"\x76")


def parse_state(path: Path) -> dict[str, str]:
    return dict(
        line.split("=", 1) for line in path.read_text().splitlines() if "=" in line
    )


def run(trace: Path, rom: Path, tmp: Path, label: str, fault: str | None = None):
    prefix = tmp / label
    env = {
        "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
        "JUKU_TRACE_IO": "1",
        "JUKU_CHECKPOINT_PREFIX": str(prefix),
    }
    if fault:
        env["JUKU_PIT_FAULT"] = fault
    proc = subprocess.run(
        [str(trace), str(rom), "10000"], cwd=tmp, env=env,
        text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False,
    )
    state_path = prefix.with_suffix(".state")
    state = parse_state(state_path) if state_path.exists() else {}
    return proc, state


def main() -> int:
    if len(sys.argv) != 2:
        print(f"usage: {Path(sys.argv[0]).name} /path/to/trace", file=sys.stderr)
        return 2
    trace = Path(sys.argv[1]).resolve()
    if not trace.is_file():
        print("trace executable is missing", file=sys.stderr)
        return 2

    failures: list[str] = []
    with tempfile.TemporaryDirectory(prefix="cosim-pit-latch-") as tmp_name:
        tmp = Path(tmp_name)
        rom = tmp / "pit-latch.bin"
        rom.write_bytes(build_rom())
        clean, clean_state = run(trace, rom, tmp, "clean")
        stuck_high, stuck_high_state = run(
            trace, rom, tmp, "stuck-high", "1A:00:01"
        )
        stuck_low, stuck_low_state = run(
            trace, rom, tmp, "stuck-low", "12:02:00"
        )
        invalid = subprocess.run(
            [str(trace), str(rom), "10000"], cwd=tmp,
            env={"PATH": os.environ.get("PATH", "/usr/bin:/bin"),
                 "JUKU_PIT_FAULT": "13:00:01"},
            text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False,
        )

    for label, proc, state, expected_e, expected_l in (
        ("clean", clean, clean_state, "5A", "68"),
        ("stuck-high", stuck_high, stuck_high_state, "5A", "69"),
        ("stuck-low", stuck_low, stuck_low_state, "58", "68"),
    ):
        if proc.returncode != 0:
            failures.append(f"{label}: cosim exited {proc.returncode}")
        for key, expected in (
            ("b", "34"), ("c", "12"), ("d", "A5"), ("e", expected_e),
            ("h", "96"), ("l", expected_l), ("halted", "1"),
        ):
            if state.get(key) != expected:
                failures.append(
                    f"{label}: {key}={state.get(key, 'missing')} != {expected}"
                )
    for label, state, port, low, high in (
        ("stuck-high", stuck_high_state, "1A", "00", "01"),
        ("stuck-low", stuck_low_state, "12", "02", "00"),
    ):
        for key, expected in (
            ("pit_fault_enabled", "1"), ("pit_fault_port", port),
            ("pit_fault_stuck_low", low), ("pit_fault_stuck_high", high),
        ):
            if state.get(key) != expected:
                failures.append(
                    f"{label}: {key}={state.get(key, 'missing')} != {expected}"
                )
    if invalid.returncode != 2 or "invalid JUKU_PIT_FAULT" not in invalid.stderr:
        failures.append("control-port fault grammar was not rejected")

    if failures:
        print("COSIM-PIT-LATCH: FAIL", file=sys.stderr)
        for failure in failures:
            print(f"- {failure}", file=sys.stderr)
        return 1
    print(
        "COSIM-PIT-LATCH: PASS "
        "(LSB/MSB, single-byte formats, all chip selects, both fault polarities)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
