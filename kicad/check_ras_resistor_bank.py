#!/usr/bin/env python3
"""Check the generated source PCB against the registered R49-R56 bank."""
from __future__ import annotations

import json
import math
from pathlib import Path

import pcbnew


ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "ref/photos/juku-pcb-2/ras-resistor-bank-registration.json"
BOARD = ROOT / "kicad/juku.kicad_pcb"


def fail(message: str) -> None:
    raise SystemExit(f"RAS RESISTOR BANK: FAIL: {message}")


evidence = json.loads(EVIDENCE.read_text(encoding="utf-8"))
board = pcbnew.LoadBoard(str(BOARD))
for ref, expected in evidence["placements"].items():
    footprint = board.FindFootprintByReference(ref)
    if footprint is None:
        fail(f"missing {ref}")
    pads = list(footprint.Pads())
    if len(pads) != 2:
        fail(f"{ref} does not have two pads")
    centre = (
        sum(pad.GetPosition().x for pad in pads) / len(pads) / 1e6,
        sum(pad.GetPosition().y for pad in pads) / len(pads) / 1e6,
    )
    target = tuple(expected["centre_mm"])
    error = math.hypot(centre[0] - target[0], centre[1] - target[1])
    if error > 0.02:
        fail(f"{ref} centre error {error:.3f} mm")
    orientation = footprint.GetOrientationDegrees() % 360.0
    if abs(orientation - evidence["footprint"]["orientation_deg"]) > 0.01:
        fail(f"{ref} orientation is {orientation:.3f} degrees")
    span = math.hypot(
        pcbnew.ToMM(pads[0].GetPosition().x - pads[1].GetPosition().x),
        pcbnew.ToMM(pads[0].GetPosition().y - pads[1].GetPosition().y),
    )
    if abs(span - evidence["footprint"]["lead_span_mm"]) > 0.01:
        fail(f"{ref} lead span is {span:.3f} mm")
    if footprint.GetValue() != expected["value"]:
        fail(f"{ref} value is {footprint.GetValue()!r}")
    for pad in pads:
        if abs(pcbnew.ToMM(pad.GetSize().x) - 1.6) > 0.01:
            fail(f"{ref}.{pad.GetNumber()} does not use normal pad geometry")

c69 = board.FindFootprintByReference("C69")
if c69 is None or any(abs(pcbnew.ToMM(pad.GetSize().x) - 1.6) > 0.01 for pad in c69.Pads()):
    fail("C69 normal pad geometry was not restored")

print("RAS RESISTOR BANK: PASS; eight vertical positions, values, and normal annuli guarded")
