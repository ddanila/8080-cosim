#!/usr/bin/python3
"""Shift the deterministic INT6_RAW segment clear of the (114.4,13.3) cutout."""

import sys

import pcbnew


if len(sys.argv) != 3:
    raise SystemExit(f"usage: {sys.argv[0]} INPUT.kicad_pcb OUTPUT.kicad_pcb")

board = pcbnew.LoadBoard(sys.argv[1])
old = None
for item in board.GetTracks():
    if (
        item.GetNetname() == "INT6_RAW"
        and item.GetLayer() == pcbnew.F_Cu
        and item.GetStart().y == pcbnew.FromMM(15.4384)
        and item.GetEnd().y == pcbnew.FromMM(15.4384)
    ):
        old = item
        break
if old is None:
    raise SystemExit("target INT6_RAW edge-clearance segment not found")

start, end, net, width = old.GetStart(), old.GetEnd(), old.GetNet(), old.GetWidth()
board.Remove(old)
left = pcbnew.VECTOR2I_MM(111.0, 15.3)
left_b = pcbnew.VECTOR2I_MM(111.0, 15.5)
right_b = pcbnew.VECTOR2I_MM(119.0, 15.5)
right = pcbnew.VECTOR2I_MM(119.0, 15.4384)
for pos in (left, right):
    via = pcbnew.PCB_VIA(board)
    via.SetPosition(pos)
    via.SetWidth(pcbnew.FromMM(0.6))
    via.SetDrill(pcbnew.FromMM(0.3))
    via.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
    via.SetNet(net)
    board.Add(via)
segments = [
    (start, left, pcbnew.F_Cu),
    (left, left_b, pcbnew.B_Cu),
    (left_b, right_b, pcbnew.B_Cu),
    (right_b, right, pcbnew.B_Cu),
    (right, end, pcbnew.F_Cu),
]
for a, b, layer in segments:
    track = pcbnew.PCB_TRACK(board)
    track.SetStart(a)
    track.SetEnd(b)
    track.SetLayer(layer)
    track.SetWidth(width)
    track.SetNet(net)
    board.Add(track)

pcbnew.SaveBoard(sys.argv[2], board)
print(f"shifted INT6_RAW clear of the (114.4,13.3) cutout -> {sys.argv[2]}")
