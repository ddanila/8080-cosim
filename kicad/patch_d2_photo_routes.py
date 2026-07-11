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

# Delete only an earlier invocation's exact direct D2-D4 segments.
def point_key(point):
    return point.x, point.y


ends = {
    frozenset((point_key(d2pads[d2pin].GetPosition()), point_key(d4pads[d4pin].GetPosition())))
    for d2pin, (d4pin, _) in links.items()
}
for track in list(board.GetTracks()):
    if isinstance(track, pcbnew.PCB_TRACK) and not isinstance(track, pcbnew.PCB_VIA):
        if frozenset((point_key(track.GetStart()), point_key(track.GetEnd()))) in ends:
            board.Remove(track)

for d2pin, (d4pin, netname) in links.items():
    net = board.FindNet(netname)
    if net is None:
        raise SystemExit(f"net {netname} not found")
    d2pads[d2pin].SetNet(net)
    track = pcbnew.PCB_TRACK(board)
    track.SetStart(d2pads[d2pin].GetPosition())
    track.SetEnd(d4pads[d4pin].GetPosition())
    track.SetLayer(pcbnew.B_Cu)
    track.SetWidth(pcbnew.FromMM(0.25))
    track.SetNet(net)
    board.Add(track)

pcbnew.SaveBoard(sys.argv[2], board)
print("D2 photo routes:", ", ".join(f"D2.{a}->D4.{b[0]}/{b[1]}" for a, b in links.items()))
