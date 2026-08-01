#!/usr/bin/env python3
"""Prove all twelve slow, grouped audible PIT-debug checkpoint codes."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "tests"), str(ROOT / "spinoffs" / "jukuravi"),
                str(ROOT / "spinoffs" / "jukuravi" / "firmware")]
import build_d0_pit_debug_slow as firmware  # noqa: E402
import jukuravi_d0_pit_debug_test as base  # noqa: E402
import jukuravi_d0_pit_test as pit_test  # noqa: E402
import jukuravi_d0_ram_fallback_test as fallback_test  # noqa: E402


def main() -> int:
    if len(sys.argv) != 3:
        print(f"usage: {Path(sys.argv[0]).name} trace diag-d0-pit-debug-slow.bin",
              file=sys.stderr)
        return 2
    trace, rom = map(lambda value: Path(value).resolve(), sys.argv[1:])
    image, metadata = firmware.build()
    if not trace.is_file() or not rom.is_file() or rom.read_bytes() != image:
        print("trace executable or exact slow PIT-debug image is missing", file=sys.stderr)
        return 2

    failures = []
    clean = fallback_test.run_fallback(trace, image, "pit-debug-slow-clean")
    failures.extend(base.common_failures("clean", clean, metadata, checkpoint=None))
    expected_clean = pit_test.expected_pit_io()
    if pit_test.pit_slice(clean[0])[:len(expected_clean)] != expected_clean:
        failures.append("clean: full PIT sequence differs")

    for checkpoint, (port, stuck_low, stuck_high) in enumerate(base.CHECKPOINTS, 1):
        label = f"slow-checkpoint-{checkpoint:02d}"
        result = fallback_test.run_fallback(
            trace, image, label,
            pit_fault=f"{port:02X}:{stuck_low:02X}:{stuck_high:02X}",
        )
        failures.extend(base.common_failures(label, result, metadata,
                                             checkpoint=checkpoint))
        reads = [event for event in base.io_events(result[0])
                 if event[0] == "IN" and event[1] in range(0x10, 0x1B)]
        if len(reads) != checkpoint or reads[-1][1] != port:
            failures.append(f"{label}: PIT reads={reads}")

    if failures:
        print("JUKURAVI-D0-PIT-DEBUG-SLOW: FAIL", file=sys.stderr)
        for failure in failures:
            print(f"- {failure}", file=sys.stderr)
        return 1
    print("JUKURAVI-D0-PIT-DEBUG-SLOW: PASS (clean plus all 12 grouped codes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
