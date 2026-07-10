#!/usr/bin/env python3
"""Dogleg AMWC_N around the X1-area mounting-hole Edge.Cuts circle."""
import sys
import pcbnew


board_path = sys.argv[1] if len(sys.argv) > 1 else "kicad/juku_routed.kicad_pcb"
board = pcbnew.LoadBoard(board_path)
mm = pcbnew.FromMM

target = None
for item in board.GetTracks():
    if item.GetClass() != "PCB_TRACK" or item.GetNetname() != "AMWC_N":
        continue
    start, end = item.GetStart(), item.GetEnd()
    coords = {(round(pcbnew.ToMM(start.x), 4), round(pcbnew.ToMM(start.y), 4)),
              (round(pcbnew.ToMM(end.x), 4), round(pcbnew.ToMM(end.y), 4))}
    if coords == {(112.31, 3.4797), (112.31, 33.285)}:
        target = item
        break

if target is None:
    raise SystemExit("AMWC_N edge-clearance segment not found")

net = target.GetNet()
layer = target.GetLayer()
width = target.GetWidth()
board.Remove(target)

# Move the middle of the vertical run 0.51 mm west. This raises clearance from
# the mounting-hole Edge.Cuts circle at (114.4, 13.3) while retaining both
# router-selected endpoints and using 45-degree entry/exit segments.
points = [
    (112.31, 33.285),
    (112.31, 18.0),
    (111.80, 17.49),
    (111.80, 9.09),
    (112.31, 8.58),
    (112.31, 3.4797),
]
for a, b in zip(points, points[1:]):
    track = pcbnew.PCB_TRACK(board)
    track.SetStart(pcbnew.VECTOR2I(mm(a[0]), mm(a[1])))
    track.SetEnd(pcbnew.VECTOR2I(mm(b[0]), mm(b[1])))
    track.SetWidth(width)
    track.SetLayer(layer)
    track.SetNet(net)
    board.Add(track)

pcbnew.SaveBoard(board_path, board)
print(f"repaired AMWC_N mounting-hole clearance in {board_path}")
