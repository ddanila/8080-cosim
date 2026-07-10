#!/usr/bin/python3
"""Restore 0.20 mm GND width around the (199,251.2) Edge.Cuts circle."""

import math
import sys

import pcbnew


if len(sys.argv) != 2:
    raise SystemExit(f"usage: {sys.argv[0]} BOARD.kicad_pcb")

board = pcbnew.LoadBoard(sys.argv[1])
cx, cy = 199.0, 251.2
changed = 0
for item in board.GetTracks():
    if item.GetClass() != "PCB_TRACK" or item.GetNetname() != "GND":
        continue
    points = (item.GetStart(), item.GetEnd())
    if min(
        math.hypot(pcbnew.ToMM(point.x) - cx, pcbnew.ToMM(point.y) - cy)
        for point in points
    ) < 4.0 and item.GetWidth() > pcbnew.FromMM(0.2):
        item.SetWidth(pcbnew.FromMM(0.2))
        changed += 1

pcbnew.SaveBoard(sys.argv[1], board)
print(f"narrowed {changed} GND segments near the (199,251.2) cutout")
