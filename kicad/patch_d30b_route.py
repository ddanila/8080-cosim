#!/usr/bin/python3
"""Incrementally add the traced D30 section-B pin-10/pin-12 net.

The prior routed board is an electrically verified baseline.  This localized
patch assigns the newly recovered net and takes a short B.Cu dogleg around the
intervening pin 11.  KiCad DRC remains the acceptance authority.
"""

import sys

import pcbnew


if len(sys.argv) != 3:
    raise SystemExit(f"usage: {sys.argv[0]} INPUT.kicad_pcb OUTPUT.kicad_pcb")

board = pcbnew.LoadBoard(sys.argv[1])
fp = board.FindFootprintByReference("D30")
p10 = fp.FindPadByNumber("10")
p12 = fp.FindPadByNumber("12")
assert not p10.GetNetname() and not p12.GetNetname()

net = pcbnew.NETINFO_ITEM(board, "D30B_D_PRE_N")
board.Add(net)
p10.SetNet(net)
p12.SetNet(net)

points = [p10.GetPosition(), pcbnew.VECTOR2I_MM(35.44, 183.45),
          pcbnew.VECTOR2I_MM(30.36, 183.45), p12.GetPosition()]
for a, b in zip(points, points[1:]):
    track = pcbnew.PCB_TRACK(board)
    track.SetStart(a)
    track.SetEnd(b)
    track.SetLayer(pcbnew.F_Cu)
    track.SetWidth(pcbnew.FromMM(0.2))
    track.SetNet(net)
    board.Add(track)

pcbnew.SaveBoard(sys.argv[2], board)
print(f"added D30B_D_PRE_N on D30 pins 10/12 -> {sys.argv[2]}")
