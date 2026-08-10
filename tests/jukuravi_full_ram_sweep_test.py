#!/usr/bin/env python3
"""Guard T36's host-side full-RAM patterns and physical failure attribution."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "spinoffs" / "jukuravi"))
import batch  # noqa: E402


def main() -> int:
    patterns = batch.full_ram_patterns()
    assert [name for name, _ in patterns] == [
        "zeros",
        "ones",
        "checkerboard",
        "address",
    ]
    assert all(len(data) == 0x8000 for _, data in patterns)
    assert patterns[2][1][:4] == bytes.fromhex("55AA55AA")
    assert len(set(patterns[3][1])) == 256

    expected = bytes(0x8000)
    observed = bytearray(expected)
    observed[0x0012] = 0x15  # address 4012h -> physical row 12h
    observed[0x0192] = 0x80  # address 4192h -> the same physical row
    analysis = batch.full_ram_failure_map(expected, bytes(observed))
    assert analysis["mismatching_bytes"] == 2
    assert analysis["xor_or"] == "0x95"
    assert analysis["failing_rows"] == [{"row": "0x12", "mismatching_bytes": 2}]
    assert [item["address"] for item in analysis["first_mismatches"]] == [
        "0x4012",
        "0x4192",
    ]
    lanes = {item["package"] for item in analysis["lanes"]}
    assert lanes == {"D84", "D86", "D88", "D91"}
    print(
        "JUKURAVI-FULL-RAM-SWEEP: PASS "
        "(32 KiB patterns; alias data; MA0..MA6 row and D84..D91 attribution)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
