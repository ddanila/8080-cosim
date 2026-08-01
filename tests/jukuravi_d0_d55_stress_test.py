#!/usr/bin/env python3
"""Prove the repeated, recovery-spaced D55 diagnostic paths."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "tests"), str(ROOT / "spinoffs" / "jukuravi"),
                str(ROOT / "spinoffs" / "jukuravi" / "firmware")]
import build_d0_d55_stress as firmware  # noqa: E402
import jukuravi_d0_pit_debug_test as base  # noqa: E402
import jukuravi_d0_ram_fallback_test as fallback_test  # noqa: E402

CASES = [(0x14, 0x80, 0x00), (0x15, 0x80, 0x00),
         (0x16, 0x80, 0x00), (0x14, 0x00, 0x80)]


def main() -> int:
    if len(sys.argv) != 3:
        print(f"usage: {Path(sys.argv[0]).name} trace diag-d0-d55-stress.bin",
              file=sys.stderr)
        return 2
    trace, rom = map(lambda value: Path(value).resolve(), sys.argv[1:])
    image, metadata = firmware.build()
    if not trace.is_file() or not rom.is_file() or rom.read_bytes() != image:
        print("trace executable or exact D55 stress image is missing", file=sys.stderr)
        return 2

    failures = []
    clean = fallback_test.run_fallback(trace, image, "d55-stress-clean")
    failures.extend(base.common_failures("clean", clean, metadata, checkpoint=None))
    reads = [event for event in base.io_events(clean[0])
             if event[0] == "IN" and event[1] in range(0x14, 0x17)]
    expected_reads = metadata["pit_debug_repetitions"] * 4
    if len(reads) != expected_reads:
        failures.append(f"clean: D55 reads={len(reads)} != {expected_reads}")

    for checkpoint, (port, stuck_low, stuck_high) in enumerate(CASES, 1):
        label = f"d55-checkpoint-{checkpoint}"
        result = fallback_test.run_fallback(
            trace, image, label,
            pit_fault=f"{port:02X}:{stuck_low:02X}:{stuck_high:02X}",
        )
        failures.extend(base.common_failures(label, result, metadata,
                                             checkpoint=checkpoint))
        fault_reads = [event for event in base.io_events(result[0])
                       if event[0] == "IN" and event[1] in range(0x14, 0x17)]
        expected_before = (checkpoint - 1) * metadata["pit_debug_repetitions"] + 1
        if len(fault_reads) != expected_before or fault_reads[-1][1] != port:
            failures.append(f"{label}: D55 reads={fault_reads}")

    if failures:
        print("JUKURAVI-D0-D55-STRESS: FAIL", file=sys.stderr)
        for failure in failures:
            print(f"- {failure}", file=sys.stderr)
        return 1
    print("JUKURAVI-D0-D55-STRESS: PASS (128 clean reads plus all four codes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
