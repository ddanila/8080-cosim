#!/usr/bin/env python3
"""Generate the non-burnable D2 .037 address/truth constraint table."""

from __future__ import annotations

import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "ref" / "reconstructed-proms" / "d2_037_symbolic_truth.csv"

# RT4 address bit -> proven board signal.  The ordering is the physical PROM
# address ordering, not CPU address numeric ordering.
SIGNALS = {
    0: "A12",
    1: "A15",
    2: "A9",
    3: "VIDEO_CYCLE",
    4: "A14",
    5: "XACK_N",
    6: "A10",
    7: "WREQ_N",
}


def main() -> int:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    fields = ["prom_address_hex"] + [f"A{bit}_{SIGNALS[bit]}" for bit in range(7, -1, -1)]
    fields += ["D0", "status"]
    with OUT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for address in range(256):
            row = {"prom_address_hex": f"0x{address:02X}"}
            for bit in range(7, -1, -1):
                row[f"A{bit}_{SIGNALS[bit]}"] = (address >> bit) & 1
            row["D0"] = "?"
            row["status"] = "input vector proved; output truth requires .037 dump or capture"
            writer.writerow(row)
    print(f"Wrote {OUT.relative_to(ROOT)}: 256 symbolic rows; no burnable output values")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
