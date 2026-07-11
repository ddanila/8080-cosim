#!/usr/bin/env python3
"""Apply the photo-proven vertical D2 posture without regenerating the PCB."""

import sys

import pcbnew


if len(sys.argv) != 3:
    raise SystemExit("usage: patch_d2_orientation.py INPUT.kicad_pcb OUTPUT.kicad_pcb")

board = pcbnew.LoadBoard(sys.argv[1])
d2 = board.FindFootprintByReference("D2")
if d2 is None:
    raise SystemExit("D2 footprint not found")

d2.SetOrientationDegrees(0.0)
pcbnew.SaveBoard(sys.argv[2], board)

pin1 = next(p for p in d2.Pads() if p.GetNumber() == "1").GetPosition()
pin8 = next(p for p in d2.Pads() if p.GetNumber() == "8").GetPosition()
if abs(pcbnew.ToMM(pin1.x) - pcbnew.ToMM(pin8.x)) > 0.001:
    raise SystemExit("D2 pin 1-8 row is not vertical after patch")
if pcbnew.ToMM(pin1.y) >= pcbnew.ToMM(pin8.y):
    raise SystemExit("D2 pin 1 is not above pin 8 after patch")

print(
    "D2 photo-proven posture: pin1",
    f"({pcbnew.ToMM(pin1.x):.3f},{pcbnew.ToMM(pin1.y):.3f})",
    "pin8",
    f"({pcbnew.ToMM(pin8.x):.3f},{pcbnew.ToMM(pin8.y):.3f})",
)
