#!/usr/bin/env python3
"""Apply the photo-proven marked D98 К155ЛП11 placement."""

import sys

import pcbnew


if len(sys.argv) != 3:
    raise SystemExit("usage: patch_d98_orientation.py INPUT.kicad_pcb OUTPUT.kicad_pcb")

board = pcbnew.LoadBoard(sys.argv[1])
d98 = board.FindFootprintByReference("D98")
if d98 is None:
    raise SystemExit("D98 footprint not found")
d98.SetOrientationDegrees(90.0)
d98.SetPosition(pcbnew.VECTOR2I_MM(290.00, 37.40))
pcbnew.SaveBoard(sys.argv[2], board)

pads = {p.GetNumber(): p.GetPosition() for p in d98.Pads()}
p1 = pads["1"]
p8 = pads["8"]
if pcbnew.ToMM(p1.x) >= pcbnew.ToMM(p8.x) or abs(pcbnew.ToMM(p1.y - p8.y)) > 0.001:
    raise SystemExit("D98 lower row does not match the horizontal notch-left photograph")
print(
    "D98 photo-proven posture: pin1",
    f"({pcbnew.ToMM(p1.x):.3f},{pcbnew.ToMM(p1.y):.3f})",
    "pin8",
    f"({pcbnew.ToMM(p8.x):.3f},{pcbnew.ToMM(p8.y):.3f})",
)
