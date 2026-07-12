#!/usr/bin/env python3
"""Assign and route the five July-2026 photo-proven D2 address inputs."""

import sys

import pcbnew


if len(sys.argv) != 3:
    raise SystemExit("usage: patch_d2_photo_routes.py INPUT.kicad_pcb OUTPUT.kicad_pcb")

board = pcbnew.LoadBoard(sys.argv[1])
d2 = board.FindFootprintByReference("D2")
d4 = board.FindFootprintByReference("D4")
if d2 is None or d4 is None:
    raise SystemExit("D2 or D4 footprint not found")

links = {"1": ("1", "A10"), "3": ("3", "A14"), "5": ("5", "A12"),
         "6": ("6", "A15"), "7": ("7", "A9")}
d2pads = {p.GetNumber(): p for p in d2.Pads()}
d4pads = {p.GetNumber(): p for p in d4.Pads()}

# Delete an earlier invocation's D2-D4 corridor segments.  A straight segment
# reaches the correct D4 pad only after crossing D4's opposite pad row, so the
# route must enter through the midpoint between those pads first.
netnames = {netname for _d4pin, netname in links.values()}
x_min, x_max = pcbnew.FromMM(46.5), pcbnew.FromMM(70.8)
y_min, y_max = pcbnew.FromMM(128.5), pcbnew.FromMM(148.0)
remove = []
for track in list(board.GetTracks()):
    if isinstance(track, pcbnew.PCB_TRACK) and not isinstance(track, pcbnew.PCB_VIA):
        points = (track.GetStart(), track.GetEnd())
        if (track.GetNetname() in netnames and track.GetLayer() == pcbnew.B_Cu
                and all(x_min <= point.x <= x_max and y_min <= point.y <= y_max
                        for point in points)):
            remove.append(track)

new_tracks = []
for d2pin, (d4pin, netname) in links.items():
    net = board.FindNet(netname)
    if net is None:
        raise SystemExit(f"net {netname} not found")
    d2pads[d2pin].SetNet(net)
    start = d2pads[d2pin].GetPosition()
    end = d4pads[d4pin].GetPosition()
    # D4's opposite row is x=54.915 mm. Cross it halfway between
    # adjacent pads, then turn inside the package before reaching the target.
    gateway_y = end.y - pcbnew.FromMM(1.27)
    points = (start,
              pcbnew.VECTOR2I(pcbnew.FromMM(58.0), start.y),
              pcbnew.VECTOR2I(pcbnew.FromMM(58.0), gateway_y),
              pcbnew.VECTOR2I(pcbnew.FromMM(51.0), gateway_y),
              pcbnew.VECTOR2I(pcbnew.FromMM(51.0), end.y),
              end)
    for first, second in zip(points, points[1:]):
        track = pcbnew.PCB_TRACK(board)
        track.SetStart(first)
        track.SetEnd(second)
        track.SetLayer(pcbnew.B_Cu)
        track.SetWidth(pcbnew.FromMM(0.25))
        track.SetNet(net)
        new_tracks.append(track)

# Construct everything before removal: KiCad 10's SWIG layer can invalidate
# unrelated child proxies immediately after BOARD.Remove().
for track in remove:
    board.Remove(track)
for track in new_tracks:
    board.Add(track)

pcbnew.SaveBoard(sys.argv[2], board)
print("D2 photo routes:", ", ".join(f"D2.{a}->D4.{b[0]}/{b[1]}" for a, b in links.items()))
