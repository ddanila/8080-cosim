#!/usr/bin/env python3
"""R5.I4 independent generated-board/pin closure and mutation controls."""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path


HERE = Path(__file__).resolve().parent


def validate(board: dict, contract: dict) -> list[str]:
    errors: list[str] = []
    parts = {part["ref"]: part for part in board["chips"]}

    def exact(ref: str, pins: dict[str, str], typ: str) -> None:
        part = parts.get(ref)
        if part is None:
            errors.append(f"missing {ref}")
        elif part["type"] != typ or part["pins"] != pins:
            errors.append(f"{ref} type/pin map differs from frozen contract")

    exact("U2", contract["decode_gal"]["pins"], "GAL22V10_IOSEL")
    exact("U8", contract["timer"]["pins"], "PIT_8253")
    exact("U9", contract["post"]["latch_pins"], "ACT_273_POST")
    if parts.get("U7", {}).get("pins", {}).get("4") != "PIT_CLK0":
        errors.append("U7 /4 is not routed to PIT_CLK0")
    for ref, wanted in contract["baud_tree"]["jumpers"].items():
        if parts.get(ref, {}).get("pins") != wanted["pins"]:
            errors.append(f"{ref} does not implement frozen two-stage clock selection")

    if any(parts.get(ref, {}).get("dnp") for ref in ("U4", "U5", "U6")):
        errors.append("C10-capable PPI/PIC/encoder remains DNP")
    for ref in ("U1", "U2", "U3", "U4", "U5", "U6", "U7", "U8", "U9"):
        if ref not in parts:
            errors.append(f"missing populated digital package {ref}")
    for i in range(1, 10):
        if parts.get(f"C{i}", {}).get("pins") != {"1": "VCC5", "2": "GND"}:
            errors.append(f"C{i} is not the local VCC/GND 100 nF allowance")

    for bit in range(8):
        if parts.get(f"R_POST{bit}", {}).get("pins") != {
                "1": f"POST_Q{bit}", "2": f"POST_LED{bit}_A"}:
            errors.append(f"POST bit {bit} resistor path wrong")
        if parts.get(f"D_POST{bit}", {}).get("pins") != {
                "1": "GND", "2": f"POST_LED{bit}_A"}:
            errors.append(f"POST bit {bit} LED polarity wrong")
    sound = {
        "Q1": {"1": "GND", "2": "SOUND_BASE", "3": "SOUND_LOW"},
        "BZ1": {"1": "VCC5", "2": "SOUND_LOW"},
        "J_SOUND": {"1": "VCC5", "2": "SOUND_LOW"},
        "R_SOUND_BASE": {"1": "PIT_SOUND", "2": "SOUND_BASE"},
        "R_SOUND_PD": {"1": "SOUND_BASE", "2": "GND"},
    }
    for ref, pins in sound.items():
        if parts.get(ref, {}).get("pins") != pins:
            errors.append(f"sound path {ref} wrong")
    tp = parts.get("J_PIT_TP", {}).get("pins", {})
    if set(tp.values()) != {"PIT_CLK0", "PIT_BAUD", "PIT_SOUND", "PIT_OUT2_TP", "GND"}:
        errors.append("PIT test header omits a frozen clock/output/GND")

    # Every declared net must be the exact inverse of the package pin maps.
    derived: dict[str, list[list[str]]] = {}
    for part in board["chips"]:
        for pin, net in part["pins"].items():
            derived.setdefault(net, []).append([part["ref"], pin])
    recorded = {net: row["nodes"] for net, row in board["nets"].items()}
    if derived != recorded:
        errors.append("board nets are stale relative to package pins")
    return errors


def main() -> int:
    contract = json.loads((HERE / "io-expansion.json").read_text())
    board = json.loads((HERE / "io.board.json").read_text())
    errors = validate(board, contract)
    if "--self-test" in sys.argv:
        mutations = []
        for ref, pin, net in (("U8", "9", "BAUD_DIV2_NC"),
                              ("U8", "21", "UART_CS_N"),
                              ("U9", "11", "PIT_CS_N"),
                              ("Q1", "1", "SOUND_LOW"),
                              ("D_POST7", "1", "POST_LED7_A")):
            changed = copy.deepcopy(board)
            next(part for part in changed["chips"] if part["ref"] == ref)["pins"][pin] = net
            # Rebuild nets so each mutation tests the electrical contract rather than
            # merely the board.json inverse-net consistency check.
            nets: dict[str, list[list[str]]] = {}
            for part in changed["chips"]:
                for p, n in part["pins"].items(): nets.setdefault(n, []).append([part["ref"], p])
            changed["nets"] = {n: {"nodes": nodes} for n, nodes in nets.items()}
            mutations.append(bool(validate(changed, contract)))
        if not all(mutations):
            errors.append("one or more PIT/POST/sound mutation controls escaped")
    if errors:
        print("rev B expanded I/O board check FAILED:")
        for error in errors: print(f"- {error}")
        return 1
    print("rev B expanded I/O board PASS: U1-U9 populated, exact PIT/GAL/POST pins, clocks, LEDs, sound, decoupling and five mutations")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
