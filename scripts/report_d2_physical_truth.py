#!/usr/bin/env python3
"""Classify and guard the physical D2 `.037` READY PROM truth."""
from __future__ import annotations

import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "ref/physical-proms/validated/d2_037.raw.bin"
REPORT = ROOT / "docs/d2-physical-truth.md"
EXPECTED_SHA256 = "953be4bf899e02f0885ecef53e4f9d26469b8d78ceea87394aa35cd28df0255b"


def classified_raw(index: int) -> int:
    wreq = (index >> 7) & 1
    a10 = (index >> 6) & 1
    xack = (index >> 5) & 1
    a14 = (index >> 4) & 1
    cas = (index >> 3) & 1
    a9 = (index >> 2) & 1
    a15 = (index >> 1) & 1
    a12 = index & 1
    if not wreq:
        release = False
    elif not a10:
        exceptional_low = not a9 and cas == a12 and a15 != a12
        release = not exceptional_low
    elif xack:
        release = False
    elif a14:
        release = True
    else:
        exceptional_low = a9 and a15 and not a12
        release = not exceptional_low
    return 0xF if release else 0x0


def main() -> int:
    data = RAW.read_bytes()
    sha = hashlib.sha256(data).hexdigest()
    if len(data) != 256 or sha != EXPECTED_SHA256:
        raise SystemExit(f"unexpected D2 physical image: bytes={len(data)} sha256={sha}")
    if any(value not in (0x0, 0xF) for value in data):
        raise SystemExit("D2 outputs are no longer four identical all-low/all-high bits")
    mismatches = [index for index, value in enumerate(data) if value != classified_raw(index)]
    if mismatches:
        raise SystemExit(f"D2 piecewise classification mismatch at {mismatches[:8]}")

    high = [index for index, value in enumerate(data) if value == 0xF]
    low = [index for index, value in enumerate(data) if value == 0x0]
    lines = [
        "# Physical D2 `.037` truth", "", "Status: **PHYSICAL READY TRUTH CLASSIFIED AND GUARDED**", "",
        "This generated report reduces the preserved D2 КР556РТ4 image to an exact",
        "piecewise condition over its eight traced inputs. It describes raw electrical",
        "levels; D0/pin12 is an open-collector input to the pulled-up D30 READY latch.", "",
        "## Guarded artifact", "", f"- Raw image: `ref/physical-proms/validated/d2_037.raw.bin` ({len(data)} bytes)",
        f"- SHA256: `{sha}`", "- Index order, MSB to LSB: `WREQ_N, A10, XACK_N, A14, CAS, A9, A15, A12`",
        f"- Four-bit raw `F` (all outputs released/high): {len(high)} rows",
        f"- Four-bit raw `0` (all outputs pulled low): {len(low)} rows", "",
        "All four physical outputs are identical at every address. Only D0/pin12 has",
        "a proved board destination; the factory symbol makes pins 9-11 explicit no-connects.", "",
        "## Exact piecewise classification", "",
        "The raw output is `0` whenever `WREQ_N=0`. For `WREQ_N=1`:", "",
        "| Condition | Raw output |", "| --- | --- |",
        "| `A10=0` and `A9=0` and `CAS=A12` and `A15!=A12` | `0` |",
        "| `A10=0`, all other combinations | `F` |",
        "| `A10=1` and `XACK_N=1` | `0` |",
        "| `A10=1`, `XACK_N=0`, and `A14=1` | `F` |",
        "| `A10=1`, `XACK_N=0`, `A14=0`, `A9=1`, `A15=1`, `A12=0` | `0` |",
        "| `A10=1`, `XACK_N=0`, `A14=0`, all other combinations | `F` |", "",
        "The classifier above is evaluated against all 256 preserved rows on every",
        "report refresh. `CAS` is a don't-care in the `A10=1` half; `XACK_N` and",
        "`A14` are don't-cares in the `A10=0` half.", "",
        "## READY interpretation boundary", "",
        "- Raw `0` means the open-collector D2 output actively pulls `READY_D` low.",
        "- Raw `F` releases D0/pin12, allowing R6 to pull `READY_D` high.",
        "- D30 samples that level with PHI2TTL and its asynchronous controls; this",
        "  table alone does not prove the full cycle-by-cycle WAIT timing.",
        "- Pins 9-11 remain physically programmed and were captured by the reader, but",
        "  the factory symbol draws no external stubs; they are intentional no-connects",
        "  and must not acquire PCB nets merely because their truth matches D0.", "",
    ]
    REPORT.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {REPORT.relative_to(ROOT)}")
    print("Status: PHYSICAL READY TRUTH CLASSIFIED AND GUARDED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
