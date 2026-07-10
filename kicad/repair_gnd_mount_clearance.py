#!/usr/bin/python3
"""Dogleg the deterministic GND segment around the (199,251.2) cutout."""

import sys

import pcbnew


if len(sys.argv) != 3:
    raise SystemExit(f"usage: {sys.argv[0]} INPUT.kicad_pcb OUTPUT.kicad_pcb")

board = pcbnew.LoadBoard(sys.argv[1])
ends = {
    (198551100, 253670100, 194430000, 249549000),
    (194430000, 249549000, 198551100, 253670100),
    (199508200, 248752600, 205475000, 254719400),
    (205475000, 254719400, 199508200, 248752600),
}
old = None
for item in board.GetTracks():
    key = (item.GetStart().x, item.GetStart().y, item.GetEnd().x, item.GetEnd().y)
    if item.GetNetname() == "GND" and item.GetLayer() == pcbnew.B_Cu and key in ends:
        old = item
        break
if old is None:
    raise SystemExit("target GND edge-clearance segment not found")

start, end, net, width = old.GetStart(), old.GetEnd(), old.GetNet(), old.GetWidth()
board.Remove(old)
if {start.x, end.x} == {199508200, 205475000}:
    mid = pcbnew.VECTOR2I_MM(202.5, 247.5)
else:
    mid = pcbnew.VECTOR2I_MM(196.2, 254.0)
for a, b in ((start, mid), (mid, end)):
    track = pcbnew.PCB_TRACK(board)
    track.SetStart(a)
    track.SetEnd(b)
    track.SetLayer(pcbnew.B_Cu)
    track.SetWidth(width)
    track.SetNet(net)
    board.Add(track)

pcbnew.SaveBoard(sys.argv[2], board)
print(f"doglegged GND around the (199,251.2) cutout -> {sys.argv[2]}")
