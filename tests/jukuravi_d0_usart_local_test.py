#!/usr/bin/env python3
"""Prove Jukuravi D0 local-8251 success, stuck-TX, and CPU-fault paths."""

from __future__ import annotations

import os
import pty
import re
import select
import subprocess
import sys
import tempfile
import tty
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "spinoffs" / "jukuravi" / "firmware"))
import build_d0_usart_local as firmware  # noqa: E402


IO_RE = re.compile(
    r"^\[IOSEQ\] (IN |OUT) port=0x([0-9A-Fa-f]{2}) "
    r"value=0x([0-9A-Fa-f]{2}) cyc=([0-9]+) pc=([0-9A-Fa-f]{4})"
)
ALIVE_IO = [(0x1B, 0x76), (0x19, 0xD0), (0x19, 0x07),
            (0x1B, 0x50), (0x19, 0x01)]
USART_INIT_IO = [(0x09, 0x00)] * 3 + [
    (0x09, 0x40), (0x09, firmware.USART_MODE),
    (0x09, firmware.USART_COMMAND), (0x08, firmware.USART_TEST_BYTE),
    (0x1B, 0x34), (0x18, firmware.BAUD_DIVISOR), (0x18, 0x00),
]
CPU_FAIL_IO = [(0x1B, 0x76), (0x19, 0x40), (0x19, 0x1F)]
USART_FAIL_IO = [(0x1B, 0x76), (0x19, 0xA0), (0x19, 0x0F)]
EXPECTED_TONE_TSTATES = 1_000_035


def parse_state(path: Path) -> dict[str, str]:
    return dict(line.split("=", 1) for line in path.read_text().splitlines() if "=" in line)


def run_image(
    trace: Path, image: bytes, label: str, *, fault: str | None = None
) -> tuple[subprocess.CompletedProcess[str], dict[str, str], list[tuple[str, int, int, int]], bytes]:
    with tempfile.TemporaryDirectory(prefix=f"juku-d0-usart-{label}-") as tmp_name:
        tmp = Path(tmp_name)
        rom = tmp / f"{label}.bin"
        prefix = tmp / "checkpoint"
        rom.write_bytes(image)
        master, slave = pty.openpty()
        tty.setraw(slave)
        env = os.environ.copy()
        env.update({
            "JUKU_TRACE_IO": "1",
            "JUKU_CHECKPOINT_PREFIX": str(prefix),
            "JUKU_USART_PTY": os.ttyname(slave),
            "JUKU_USART_TRANSFER_CYCLES": "64",
            "JUKU_USART_BYTE_CYCLES": "512",
        })
        if fault:
            env["JUKU_USART_FAULT"] = fault
        proc = subprocess.run(
            [str(trace), str(rom), "10000000"], cwd=tmp, env=env,
            text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            timeout=20, check=False,
        )
        outbound = b""
        while select.select([master], [], [], 0)[0]:
            outbound += os.read(master, 256)
        os.close(master)
        os.close(slave)
        state = parse_state(prefix.with_suffix(".state"))
    events = []
    for line in proc.stderr.splitlines():
        match = IO_RE.match(line)
        if match:
            events.append((match.group(1).strip(), int(match.group(2), 16),
                           int(match.group(3), 16), int(match.group(4))))
    return proc, state, events, outbound


def common_failures(
    label: str,
    proc: subprocess.CompletedProcess[str],
    state: dict[str, str],
    events: list[tuple[str, int, int, int]],
    expected_writes: list[tuple[int, int]],
    expected_pc: int,
) -> list[str]:
    failures = []
    writes = [(port, value) for direction, port, value, _ in events if direction == "OUT"]
    if proc.returncode != 0:
        failures.append(f"{label}: cosim exited {proc.returncode}")
    if writes != expected_writes:
        failures.append(f"{label}: I/O writes differ: {writes}")
    alive = [event for event in events if event[0] == "OUT"]
    if len(alive) >= 4 and alive[3][3] - alive[2][3] != EXPECTED_TONE_TSTATES:
        failures.append(f"{label}: alive-tone duration differs")
    if state.get("pc") != f"{expected_pc:04X}":
        failures.append(f"{label}: PC {state.get('pc')} != {expected_pc:04X}")
    for key, expected in (("sp", "0000"), ("halted", "1"), ("iff", "0"),
                          ("mode", "0"), ("mode_switches", "0")):
        if state.get(key) != expected:
            failures.append(f"{label}: {key}={state.get(key, 'missing')} != {expected}")
    if "==== RAM write density (pages >0) ====\n  0x" in proc.stdout:
        failures.append(f"{label}: ROM wrote RAM")
    return failures


def main() -> int:
    if len(sys.argv) != 3:
        print(f"usage: {Path(sys.argv[0]).name} /path/to/trace diag-d0-usart-local.bin", file=sys.stderr)
        return 2
    trace = Path(sys.argv[1]).resolve()
    rom = Path(sys.argv[2]).resolve()
    built, metadata = firmware.build()
    if not trace.is_file() or not rom.is_file():
        print("trace executable or local-USART diagnostic ROM is missing", file=sys.stderr)
        return 2
    if rom.read_bytes() != built:
        print("committed local-USART image differs from builder", file=sys.stderr)
        return 2

    success_proc, success_state, success_events, success_tx = run_image(
        trace, built, "success"
    )
    failures = common_failures(
        "success", success_proc, success_state, success_events,
        ALIVE_IO + USART_INIT_IO, int(metadata["success_halt"]) + 1,
    )
    statuses = [value & 0x05 for direction, port, value, _ in success_events
                if direction == "IN" and port == 0x09]
    compressed = [value for index, value in enumerate(statuses)
                  if index == 0 or value != statuses[index - 1]]
    if compressed != [0x05, 0x00, 0x01, 0x05]:
        failures.append(f"success: status progression {compressed} != [5, 0, 1, 5]")
    for key, expected in (("a", "05"), ("e", "D0"), ("usart_mode", "4E"),
                          ("usart_command", "37"), ("usart_status", "05"),
                          ("usart_tx_holding_full", "0"),
                          ("usart_tx_shift_busy", "0"), ("usart_tx_bytes", "1")):
        if success_state.get(key) != expected:
            failures.append(f"success: {key}={success_state.get(key, 'missing')} != {expected}")
    if success_tx != bytes([firmware.USART_TEST_BYTE]):
        failures.append(f"success: PTY byte {success_tx.hex()} != 55")

    stuck_proc, stuck_state, stuck_events, stuck_tx = run_image(
        trace, built, "tx-stuck", fault="tx_stuck"
    )
    failures.extend(common_failures(
        "tx-stuck", stuck_proc, stuck_state, stuck_events,
        ALIVE_IO + USART_INIT_IO + USART_FAIL_IO,
        int(metadata["usart_fail_halt"]) + 1,
    ))
    stuck_status_reads = sum(
        direction == "IN" and port == 0x09
        for direction, port, _, _ in stuck_events
    )
    if stuck_status_reads != firmware.TIMEOUT_COUNT + 2:
        failures.append(
            f"tx-stuck: status reads {stuck_status_reads} != "
            f"{firmware.TIMEOUT_COUNT + 2} (initial + immediate + full timeout)"
        )
    for key, expected in (("a", "0F"), ("e", "D0"), ("usart_status", "00"),
                          ("usart_tx_holding_full", "1"),
                          ("usart_tx_shift_busy", "0"), ("usart_tx_bytes", "0"),
                          ("usart_fault_tx_stuck", "1")):
        if stuck_state.get(key) != expected:
            failures.append(f"tx-stuck: {key}={stuck_state.get(key, 'missing')} != {expected}")
    if stuck_tx:
        failures.append(f"tx-stuck: unexpectedly transmitted {stuck_tx.hex()}")

    cpu_bad = bytearray(built)
    cpu_bad[int(metadata["signature_expected_offset"])] ^= 1
    cpu_proc, cpu_state, cpu_events, cpu_tx = run_image(trace, bytes(cpu_bad), "cpu-bad")
    failures.extend(common_failures(
        "cpu-bad", cpu_proc, cpu_state, cpu_events,
        ALIVE_IO + CPU_FAIL_IO, int(metadata["cpu_fail_halt"]) + 1,
    ))
    for key, expected in (("a", "1F"), ("e", "D0"), ("usart_mode", "00"),
                          ("usart_command", "00"), ("usart_tx_bytes", "0")):
        if cpu_state.get(key) != expected:
            failures.append(f"cpu-bad: {key}={cpu_state.get(key, 'missing')} != {expected}")
    if cpu_tx:
        failures.append(f"cpu-bad: unexpectedly transmitted {cpu_tx.hex()}")

    if failures:
        print("JUKURAVI-D0-USART-LOCAL: FAIL", file=sys.stderr)
        for failure in failures:
            print(f"- {failure}", file=sys.stderr)
        return 1
    print(
        "JUKURAVI-D0-USART-LOCAL: PASS "
        "(05->00->01->05, PTY=55, tx_stuck->500 Hz, CPU-bad->250 Hz, "
        "SP=0, RAM writes=0)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
