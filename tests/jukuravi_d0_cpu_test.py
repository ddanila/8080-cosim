#!/usr/bin/env python3
"""Run Jukuravi D0 CPU self-test success and injected-failure paths in cosim."""

from __future__ import annotations

import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "spinoffs" / "jukuravi" / "firmware"))
import build_d0_cpu  # noqa: E402


IO_RE = re.compile(
    r"^\[IOSEQ\] OUT port=0x([0-9A-Fa-f]{2}) value=0x([0-9A-Fa-f]{2}) "
    r"cyc=([0-9]+) pc=([0-9A-Fa-f]{4})"
)
ALIVE_IO = [(0x1B, 0x76), (0x19, 0xD0), (0x19, 0x07), (0x1B, 0x50), (0x19, 0x01)]
FAIL_IO = [(0x1B, 0x76), (0x19, 0x40), (0x19, 0x1F)]
EXPECTED_TONE_TSTATES = 1_000_035


def parse_state(path: Path) -> dict[str, str]:
    return dict(line.split("=", 1) for line in path.read_text().splitlines() if "=" in line)


def run_image(trace: Path, image: bytes, label: str) -> tuple[subprocess.CompletedProcess[str], dict[str, str], list[tuple[int, int, int]]]:
    with tempfile.TemporaryDirectory(prefix=f"juku-d0-cpu-{label}-") as tmp_name:
        tmp = Path(tmp_name)
        rom = tmp / f"{label}.bin"
        prefix = tmp / "checkpoint"
        rom.write_bytes(image)
        env = os.environ.copy()
        env["JUKU_TRACE_IO"] = "1"
        env["JUKU_CHECKPOINT_PREFIX"] = str(prefix)
        proc = subprocess.run(
            [str(trace), str(rom), "2000000"],
            cwd=tmp,
            env=env,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        state = parse_state(prefix.with_suffix(".state"))
    events = []
    for line in proc.stderr.splitlines():
        match = IO_RE.match(line)
        if match:
            events.append((int(match.group(1), 16), int(match.group(2), 16), int(match.group(3))))
    return proc, state, events


def validate_common(
    label: str,
    proc: subprocess.CompletedProcess[str],
    state: dict[str, str],
    events: list[tuple[int, int, int]],
    expected_io: list[tuple[int, int]],
    expected_pc: int,
) -> list[str]:
    failures = []
    if proc.returncode != 0:
        failures.append(f"{label}: cosim exited {proc.returncode}")
    if [(port, value) for port, value, _ in events] != expected_io:
        failures.append(f"{label}: I/O sequence differs: {events}")
    if len(events) >= 4 and events[3][2] - events[2][2] != EXPECTED_TONE_TSTATES:
        failures.append(f"{label}: alive-tone duration differs")
    if state.get("pc") != f"{expected_pc:04X}":
        failures.append(f"{label}: PC {state.get('pc')} != {expected_pc:04X}")
    for key, expected in (("sp", "0000"), ("halted", "1"), ("iff", "0"), ("mode", "0"), ("mode_switches", "0")):
        if state.get(key) != expected:
            failures.append(f"{label}: {key}={state.get(key, 'missing')} != {expected}")
    if "==== RAM write density (pages >0) ====\n  0x" in proc.stdout:
        failures.append(f"{label}: ROM wrote RAM")
    return failures


def main() -> int:
    if len(sys.argv) != 3:
        print(f"usage: {Path(sys.argv[0]).name} /path/to/trace diag-d0-cpu.bin", file=sys.stderr)
        return 2
    trace = Path(sys.argv[1]).resolve()
    rom = Path(sys.argv[2]).resolve()
    built, metadata = build_d0_cpu.build()
    if not trace.is_file() or not rom.is_file():
        print("trace executable or CPU diagnostic ROM is missing", file=sys.stderr)
        return 2
    if rom.read_bytes() != built:
        print("committed CPU diagnostic image differs from builder", file=sys.stderr)
        return 2

    success_proc, success_state, success_events = run_image(trace, built, "success")
    failures = validate_common(
        "success", success_proc, success_state, success_events,
        ALIVE_IO, metadata["success_halt"] + 1,
    )
    if success_state.get("e") != f"{build_d0_cpu.EXPECTED_SIGNATURE:02X}":
        failures.append(f"success: E signature is {success_state.get('e', 'missing')}")
    if success_state.get("a") != f"{build_d0_cpu.EXPECTED_SIGNATURE:02X}":
        failures.append(f"success: A signature is {success_state.get('a', 'missing')}")

    corrupt = bytearray(built)
    expected_offset = metadata["signature_expected_offset"]
    corrupt[expected_offset] ^= 0x01
    failure_proc, failure_state, failure_events = run_image(trace, bytes(corrupt), "bad-signature")
    failures.extend(validate_common(
        "bad-signature", failure_proc, failure_state, failure_events,
        ALIVE_IO + FAIL_IO, metadata["fail_halt"] + 1,
    ))
    if failure_state.get("e") != f"{build_d0_cpu.EXPECTED_SIGNATURE:02X}":
        failures.append(f"bad-signature: E signature is {failure_state.get('e', 'missing')}")
    if failure_state.get("a") != f"{build_d0_cpu.FAIL_TONE_DIVISOR >> 8:02X}":
        failures.append(f"bad-signature: failure-tone high byte is {failure_state.get('a', 'missing')}")

    if failures:
        print("JUKURAVI-D0-CPU: FAIL", file=sys.stderr)
        for failure in failures:
            print(f"- {failure}", file=sys.stderr)
        print(success_proc.stderr, file=sys.stderr)
        print(failure_proc.stderr, file=sys.stderr)
        return 1
    print(
        "JUKURAVI-D0-CPU: PASS "
        f"(17-result signature={build_d0_cpu.EXPECTED_SIGNATURE:02X}, flags/rotates/DAA, "
        "bad-signature -> continuous 250 Hz code, SP=0, RAM writes=0)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
