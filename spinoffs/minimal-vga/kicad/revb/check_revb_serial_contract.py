#!/usr/bin/env python3
"""R5.S1: prove the 8251-to-backplane TTL-console direction and continuity."""
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path


HERE = Path(__file__).resolve().parent
DOC = HERE.parents[1] / "docs" / "rev-b-bus-contract.md"


def components(card: str):
    board = json.loads((HERE / f"{card}.board.json").read_text())
    counts = Counter(c["ref"] for c in board["chips"])
    duplicates = sorted(ref for ref, count in counts.items() if count != 1)
    return board, {c["ref"]: c for c in board["chips"]}, duplicates


def main() -> int:
    errors: list[str] = []
    io, io_refs, io_dups = components("io")
    bp, bp_refs, bp_dups = components("backplane")
    if io_dups:
        errors.append(f"io duplicate references: {io_dups}")
    if bp_dups:
        errors.append(f"backplane duplicate references: {bp_dups}")

    uart = io_refs.get("U1", {})
    if uart.get("type") != "USART_8251":
        errors.append("I/O U1 is not the sole USART_8251")
    elif uart.get("pins", {}).get("3") != "RX" or uart.get("pins", {}).get("21") != "TX":
        errors.append("8251 pin 3/21 must be RX input/TX output")

    io_bus = io_refs.get("J_BUS", {}).get("pins", {})
    if (io_bus.get("35"), io_bus.get("36")) != ("TX", "RX"):
        errors.append("I/O bus pins 35/36 are not TX/RX")

    header = bp_refs.get("J_TTL", {}).get("pins", {})
    expected_header = {"1": "VCC_SENSE", "2": "BOARD_TX", "3": "BOARD_RX", "4": "GND"}
    if header != expected_header:
        errors.append(f"J_TTL pinout {header} != {expected_header}")

    jumper = bp_refs.get("JP_S5", {}).get("pins", {})
    expected_jumper = {"1": "TX", "2": "CON_TX_SRC", "3": "CON_RX_DRIVE", "4": "RX"}
    if jumper != expected_jumper:
        errors.append(f"JP_S5 shunt pairs {jumper} != {expected_jumper}")

    for slot in (c for c in bp["chips"] if c["type"] == "REVB_BUS_39_10"):
        if (slot["pins"].get("35"), slot["pins"].get("36")) != ("TX", "RX"):
            errors.append(f"{slot['ref']} pins 35/36 are not TX/RX")

    doc = DOC.read_text()
    for phrase in ("pin 1 = `VCC_SENSE`", "pin 2 = `BOARD_TX`", "pin 3 = `BOARD_RX`",
                   "pin 4 = GND", "TTL only, never RS-232"):
        if phrase not in doc:
            errors.append(f"bus contract lacks {phrase!r}")

    if errors:
        print("rev B serial contract FAILED:")
        for error in errors:
            print(f"- {error}")
        return 1
    print("rev B serial contract PASS: 8251 TX/RX -> bus 35/36 -> JP_S5 -> J_TTL board TX/RX")
    return 0


if __name__ == "__main__":
    sys.exit(main())
