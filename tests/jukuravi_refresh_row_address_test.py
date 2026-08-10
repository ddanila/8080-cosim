#!/usr/bin/env python3
"""Guard the physical Juku/MK4564 refresh-row mapping and T35/T36 split."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIRMWARE = ROOT / "spinoffs" / "jukuravi" / "firmware"
sys.path[:0] = [str(FIRMWARE), str(FIRMWARE.parent)]
import build_d0_refresh as t35  # noqa: E402
import build_d0_row_refresh as t36  # noqa: E402


def fail(message: str) -> None:
    print(f"JUKURAVI-REFRESH-ROW-ADDRESS: FAIL: {message}", file=sys.stderr)
    raise SystemExit(1)


def node_net(board: dict[str, object], ref: str, pin: str) -> str | None:
    nets = board.get("nets")
    assert isinstance(nets, dict)
    for name, detail in nets.items():
        if not isinstance(detail, dict):
            continue
        if [ref, pin] in detail.get("nodes", []):
            return str(name)
    return None


def accessed_rows(metadata: dict[str, object]) -> set[int]:
    base = int(metadata["refresh_base_address"])
    rows = int(metadata["refresh_rows"])
    axis = metadata["refresh_address_axis"]
    if axis == "cpu-high-byte":
        addresses = (base + (index << 8) for index in range(rows))
    elif axis == "cpu-low-seven-bits":
        addresses = (base + index for index in range(rows))
    else:
        fail(f"unknown refresh address axis: {axis!r}")
    # D48/D49 A inputs are selected in the populated-bank RAS phase. Their
    # inversion changes polarity, not coverage; MK4564 refresh uses MA0..MA6.
    return {address & 0x7F for address in addresses}


def main() -> int:
    board = json.loads((ROOT / "kicad" / "juku.board.json").read_text())
    expected_mux = {
        ("D48", "2"): "BA0",
        ("D48", "14"): "BA1",
        ("D48", "11"): "BA2",
        ("D48", "5"): "BA3",
        ("D49", "2"): "BA4",
        ("D49", "14"): "BA5",
        ("D49", "11"): "BA6",
        ("D49", "5"): "BA7",
        ("D48", "4"): "MA0",
        ("D48", "12"): "MA1",
        ("D48", "9"): "MA2",
        ("D48", "7"): "MA3",
        ("D49", "4"): "MA4",
        ("D49", "12"): "MA5",
        ("D49", "9"): "MA6",
        ("D49", "7"): "MA7",
        ("D48", "1"): "PHI1",
        ("D49", "1"): "PHI1",
        ("D53", "15"): "D53_Y0_R49",
        ("D84", "4"): "RAIL14",
    }
    for endpoint, expected in expected_mux.items():
        if node_net(board, *endpoint) != expected:
            fail(f"drawing endpoint {endpoint} no longer maps to {expected}")

    dram_reference = (ROOT / "ref" / "datasheets" / "k565ru5-pinout.txt").read_text()
    if (
        "pin 9/A7 is not needed for refresh" not in dram_reference
        or "128 cycles / 2 ms" not in dram_reference
    ):
        fail("vendored MK4564 refresh contract is absent")

    old_image, old_metadata = t35.build()
    new_image, new_metadata = t36.build()
    if hashlib.sha256(old_image).hexdigest() != (
        "ceb55556f11318dea5ef8c36b81f931813a139ce6ba6e07b607318571c6e1274"
    ):
        fail("historical T35 artifact changed")
    if old_metadata["checksum"] != 0x45C4:
        fail("historical T35 CRC changed")
    if old_image[0x07CB:0x07D3] != bytes.fromhex("7E247E247E247E24"):
        fail("historical T35 no longer contains four MOV A,M / INR H pairs")
    if new_metadata["checksum"] != 0xC617:
        fail("T36 CRC changed")
    if new_image[0x07CB:0x07D3] != bytes.fromhex("7E2C7E2C7E2C7E2C"):
        fail("T36 does not contain four MOV A,M / INR L pairs")

    old_rows = accessed_rows(old_metadata)
    new_rows = accessed_rows(new_metadata)
    if old_rows != {0}:
        fail(f"T35 negative control unexpectedly covers {len(old_rows)} rows")
    if new_rows != set(range(128)):
        fail(f"T36 covers only {len(new_rows)} physical rows")

    trace_source = (ROOT / "cosim" / "trace.c").read_text()
    if "return (uint8_t)(address & 0x7F);" not in trace_source:
        fail("cosim does not group retention by physical CPU A0..A6 row")

    print(
        "JUKURAVI-REFRESH-ROW-ADDRESS: PASS "
        "(drawings+MK4564: CPU A0..A6; T35=1 row, T36=128 rows; "
        "T35 exact preserved)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
