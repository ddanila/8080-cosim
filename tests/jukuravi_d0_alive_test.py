#!/usr/bin/env python3
"""Run the Jukuravi D0 alive-beep ROM in cosim and guard its contract."""

from __future__ import annotations

import re
import subprocess
import sys
import tempfile
from pathlib import Path


IO_RE = re.compile(
    r"^\[IOSEQ\] OUT port=0x([0-9A-Fa-f]{2}) value=0x([0-9A-Fa-f]{2}) "
    r"cyc=([0-9]+) pc=([0-9A-Fa-f]{4})"
)
STOP_RE = re.compile(
    r"stopped pc=0x([0-9A-Fa-f]{4}) cyc=([0-9]+) halted=([01]) "
    r"iff=([01]) mode=([0-3]) switches=([0-9]+)"
)
EXPECTED_IO = [(0x1B, 0x76), (0x19, 0xD0), (0x19, 0x07), (0x1B, 0x50), (0x19, 0x01)]
EXPECTED_TONE_TSTATES = 1_000_035


def parse_state(path: Path) -> dict[str, str]:
    return dict(line.split("=", 1) for line in path.read_text().splitlines() if "=" in line)


def main() -> int:
    if len(sys.argv) != 3:
        print(f"usage: {Path(sys.argv[0]).name} /path/to/trace diag-d0-alive.bin", file=sys.stderr)
        return 2
    trace = Path(sys.argv[1]).resolve()
    rom = Path(sys.argv[2]).resolve()
    failures: list[str] = []
    if not trace.is_file() or not rom.is_file():
        print("trace executable or diagnostic ROM is missing", file=sys.stderr)
        return 2
    if rom.stat().st_size != 8192:
        failures.append(f"D15 image size is {rom.stat().st_size}, expected 8192")

    with tempfile.TemporaryDirectory(prefix="juku-d0-alive-") as tmp_name:
        tmp = Path(tmp_name)
        prefix = tmp / "checkpoint"
        proc = subprocess.run(
            [str(trace), str(rom), "2000000"],
            cwd=tmp,
            env={
                "PATH": str(Path(sys.executable).parent) + ":/usr/bin:/bin",
                "JUKU_TRACE_IO": "1",
                "JUKU_CHECKPOINT_PREFIX": str(prefix),
            },
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        state = parse_state(prefix.with_suffix(".state")) if prefix.with_suffix(".state").exists() else {}

    events = []
    for line in proc.stderr.splitlines():
        match = IO_RE.match(line)
        if match:
            events.append(
                (int(match.group(1), 16), int(match.group(2), 16), int(match.group(3)))
            )
    if proc.returncode != 0:
        failures.append(f"cosim exited {proc.returncode}")
    if [(port, value) for port, value, _ in events] != EXPECTED_IO:
        failures.append(f"I/O sequence differs: {events}")
    if len(events) == len(EXPECTED_IO):
        tone_tstates = events[3][2] - events[2][2]
        if tone_tstates != EXPECTED_TONE_TSTATES:
            failures.append(
                f"tone interval is {tone_tstates} T-states, expected {EXPECTED_TONE_TSTATES}"
            )

    stop = STOP_RE.search(proc.stderr)
    if not stop:
        failures.append("missing cosim stop state")
    elif (stop.group(1).lower(), stop.group(3), stop.group(4), stop.group(5), stop.group(6)) != (
        "001e", "1", "0", "0", "0"
    ):
        failures.append(f"unexpected stop state: {stop.group(0)}")
    if state.get("sp") != "0000":
        failures.append(f"stack pointer changed: {state.get('sp', 'missing')}")
    if "==== RAM write density (pages >0) ====\n  0x" in proc.stdout:
        failures.append("diagnostic ROM wrote RAM before proving it")
    if state.get("port_1B") != "last:50,out:2,in:0":
        failures.append(f"PIT control-port state differs: {state.get('port_1B', 'missing')}")
    if state.get("port_19") != "last:01,out:3,in:0":
        failures.append(f"PIT channel-1 state differs: {state.get('port_19', 'missing')}")

    if failures:
        print("JUKURAVI-D0-ALIVE: FAIL", file=sys.stderr)
        for failure in failures:
            print(f"- {failure}", file=sys.stderr)
        print(proc.stderr, file=sys.stderr)
        return 1
    print(
        "JUKURAVI-D0-ALIVE: PASS "
        f"(PIT writes exact, tone={EXPECTED_TONE_TSTATES} T-states, HLT, SP=0, RAM writes=0)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
