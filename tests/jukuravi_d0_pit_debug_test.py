#!/usr/bin/env python3
"""Prove all twelve audible PIT-debug checkpoint codes."""

from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "tests"), str(ROOT / "spinoffs" / "jukuravi"),
                str(ROOT / "spinoffs" / "jukuravi" / "firmware")]
import build_d0_pit_debug as firmware  # noqa: E402
import jukuravi_d0_pit_test as pit_test  # noqa: E402
import jukuravi_d0_ppi_test as ppi_test  # noqa: E402
import jukuravi_d0_ram_fallback_test as fallback_test  # noqa: E402


CHECKPOINTS = [
    (0x10, 0x80, 0x00), (0x11, 0x80, 0x00), (0x12, 0x80, 0x00),
    (0x10, 0x00, 0x80),
    (0x14, 0x80, 0x00), (0x15, 0x80, 0x00), (0x16, 0x80, 0x00),
    (0x14, 0x00, 0x80),
    (0x18, 0x80, 0x00), (0x19, 0x80, 0x00), (0x1A, 0x80, 0x00),
    (0x18, 0x00, 0x80),
]


def io_events(proc) -> list[tuple[str, int, int]]:
    return ppi_test.io_events(proc)


def common_failures(label, result, metadata, *, checkpoint: int | None):
    proc, state, outbound, ram = result
    failures = []
    expected_pc = int(metadata[
        "pit_debug_success_halt" if checkpoint is None else "pit_debug_fail_halt"
    ]) + 1
    for key, expected in (
        ("pc", f"{expected_pc:04X}"), ("halted", "1"), ("sp", "0000"),
        ("iff", "0"), ("mode", "0"), ("mode_switches", "0"),
        ("usart_tx_bytes", "0"), ("usart_rx_bytes", "0"),
        ("e", f"{metadata['pit_debug_checkpoints'][-1] if checkpoint is None else checkpoint:02X}"),
    ):
        if state.get(key) != expected:
            failures.append(f"{label}: {key}={state.get(key)} != {expected}")
    if proc.returncode != 0:
        failures.append(f"{label}: cosim exited {proc.returncode}")
    if outbound or any(ram):
        failures.append(f"{label}: touched serial or RAM")
    io = io_events(proc)
    if any(port in (0x08, 0x09) for _, port, _ in io):
        failures.append(f"{label}: touched USART ports")
    tone_starts = sum(event == ("OUT", 0x1B, 0x76) for event in io)
    expected_starts = 4 if checkpoint is None else checkpoint + 2
    if tone_starts != expected_starts:
        failures.append(f"{label}: tone starts={tone_starts} != {expected_starts}")
    failures.extend(ppi_test.verify_safe_state(label, state))
    return failures


def main() -> int:
    if len(sys.argv) != 3:
        print(f"usage: {Path(sys.argv[0]).name} trace diag-d0-pit-debug.bin",
              file=sys.stderr)
        return 2
    trace, rom = map(lambda value: Path(value).resolve(), sys.argv[1:])
    image, metadata = firmware.build()
    if not trace.is_file() or not rom.is_file() or rom.read_bytes() != image:
        print("trace executable or exact PIT-debug image is missing", file=sys.stderr)
        return 2

    failures = []
    clean = fallback_test.run_fallback(trace, image, "pit-debug-clean")
    failures.extend(common_failures("clean", clean, metadata, checkpoint=None))
    expected_clean = pit_test.expected_pit_io()
    if pit_test.pit_slice(clean[0])[:len(expected_clean)] != expected_clean:
        failures.append("clean: full PIT sequence differs")

    for checkpoint, (port, stuck_low, stuck_high) in enumerate(CHECKPOINTS, 1):
        label = f"checkpoint-{checkpoint:02d}"
        result = fallback_test.run_fallback(
            trace, image, label,
            pit_fault=f"{port:02X}:{stuck_low:02X}:{stuck_high:02X}",
        )
        failures.extend(common_failures(label, result, metadata,
                                        checkpoint=checkpoint))
        reads = [event for event in io_events(result[0])
                 if event[0] == "IN" and event[1] in range(0x10, 0x1B)]
        if len(reads) != checkpoint or reads[-1][1] != port:
            failures.append(f"{label}: PIT reads={reads}")

    if failures:
        print("JUKURAVI-D0-PIT-DEBUG: FAIL", file=sys.stderr)
        for failure in failures:
            print(f"- {failure}", file=sys.stderr)
        return 1
    print("JUKURAVI-D0-PIT-DEBUG: PASS (clean plus all 12 pulse codes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
