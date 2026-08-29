#!/usr/bin/env python3
"""R5.I7 exact expanded-I/O parts, package and marking gate."""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


def verify(contract: dict, board: dict, footprints: dict, markings: dict) -> list[str]:
    errors: list[str] = []
    chips = {chip["ref"]: chip for chip in board["chips"]}
    for name, part in contract["parts"].items():
        refs = part["refs"]
        if part.get("quantity", len(refs)) != len(refs):
            errors.append(f"{name}: quantity differs from reference set")
        for ref in refs:
            chip = chips.get(ref)
            if chip is None:
                errors.append(f"{name}: missing {ref}")
                continue
            if chip["type"] != part["type"]:
                errors.append(f"{ref}: type {chip['type']} != {part['type']}")
        if footprints.get(part["type"]) != part["footprint"]:
            errors.append(f"{name}: footprint differs from exact-parts contract")
        if not part.get("mpn") or not part.get("datasheet", "").startswith("https://"):
            errors.append(f"{name}: exact MPN/datasheet is incomplete")

    pit = contract["parts"]["pit"]
    if (pit["mpn"], pit["package"]["pins"], pit["package"]["row_spacing_mm"],
            pit["supply_v"], pit["maximum_clock_mhz"]) != (
            "ID82C54", 24, 15.24, [4.5, 5.5], 8):
        errors.append("U8 is not the frozen 5 V ID82C54 socket contract")
    u8 = chips.get("U8", {}).get("pins", {})
    if {p: u8.get(p) for p in ("12", "18", "24")} != {
            "12": "GND", "18": "GND", "24": "VCC5"}:
        errors.append("U8 power pins differ")
    q1 = chips.get("Q1", {}).get("pins", {})
    if q1 != {"1": "GND", "2": "SOUND_BASE", "3": "SOUND_LOW"}:
        errors.append("Q1 E/B/C board nets differ from P2N3904ABU")

    assembly_marks = {
        "USART_8251": "8251A", "PPI_8255": "82C55A",
        "PIC_8259": "82C59A", "PIT_8253": "82C54 D57",
        "ENC_74148": "74LS148", "GAL22V10_IOSEL": "ATF22V10C IO",
        "ACT_273_POST": "74ACT273 POST", "NPN_2N3904": "2N3904",
        "PIEZO_12MM": "5V PIEZO", "LED_GREEN": "GREEN"
    }
    values = markings.get("values_by_type", {})
    for kind, wanted in assembly_marks.items():
        if values.get(kind) != wanted:
            errors.append(f"silk value for {kind} is not {wanted}")
    return errors


def main() -> int:
    contract = json.loads((HERE / "io-parts.json").read_text())
    board = json.loads((HERE / "io.board.json").read_text())
    footprints = json.loads((HERE / "footprints.io.json").read_text())
    markings = json.loads((HERE / "assembly-markings.json").read_text())
    errors = verify(contract, board, footprints, markings)
    if "--self-test" in sys.argv:
        broken = copy.deepcopy(contract)
        broken["parts"]["pit"]["package"]["pins"] = 28
        if not verify(broken, board, footprints, markings):
            errors.append("wrong-PIT-package mutation escaped")
        broken_board = copy.deepcopy(board)
        broken_board["chips"] = [c for c in broken_board["chips"] if c["ref"] != "U9"]
        if not verify(contract, broken_board, footprints, markings):
            errors.append("missing-latch mutation escaped")
        broken_marks = copy.deepcopy(markings)
        broken_marks["values_by_type"]["PIT_8253"] = "8253"
        if not verify(contract, board, footprints, broken_marks):
            errors.append("generic-silk mutation escaped")
    if errors:
        print("REVB-IO-PARTS: FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    print("REVB-IO-PARTS: PASS 10 exact part groups, ID82C54/power/pinout and complete unambiguous assembly silk + three mutations")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
