#!/usr/bin/env python3
"""Guard the exact sheet-1 D10 IR0/IR1 external-input paths."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = ROOT / "kicad/juku.board.json"
HDL = ROOT / "hdl/juku_top.v"


def main() -> None:
    spec = json.loads(SPEC.read_text(encoding="utf-8"))
    nets = spec["nets"]
    expected = {
        "X2_IRQ0": [["D10", "18"], ["X2", "214"], ["R105", "1"]],
        "X2_PB7": [
            ["D27", "25"], ["X2", "218"], ["D10", "19"], ["R107", "1"],
        ],
    }
    for name, nodes in expected.items():
        if nets.get(name, {}).get("nodes") != nodes:
            raise SystemExit(f"{name} changed: {nets.get(name, {}).get('nodes')}")
    for node in (["R105", "2"], ["R107", "2"]):
        if node not in nets["GND"]["nodes"]:
            raise SystemExit(f"PIC input pull-down missing: {node}")
    chips = {chip["ref"]: chip for chip in spec["chips"]}
    for ref in ("R105", "R107"):
        if chips.get(ref, {}).get("value") != "12к":
            raise SystemExit(f"{ref} value missing: {chips.get(ref, {}).get('value')}")
    if "214" not in chips["X2"]["pins"]:
        raise SystemExit("X2 contact 214 missing")
    for pin in ("216", "228"):
        if ["X2", pin] not in spec["no_connects"]:
            raise SystemExit(f"unused X2 contact {pin} is not an explicit NC")
    hdl = HDL.read_text(encoding="utf-8")
    for marker in (
        ".pb({x2_pb7_irq1, 7'h7F})",
        ".ir1(x2_pb7_irq1)",
        ".ir0(x2_irq0)",
    ):
        if marker not in hdl:
            raise SystemExit(f"structural PIC input marker missing: {marker}")
    print("D10 IR0/IR1: PASS — X2.214/.218 and R105/R107 pull-downs restored")


if __name__ == "__main__":
    main()
