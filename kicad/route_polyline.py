#!/usr/bin/python3
"""Add one explicit reviewable PCB polyline, optionally with endpoint vias."""
import argparse
import pcbnew

p = argparse.ArgumentParser()
p.add_argument("input"); p.add_argument("output"); p.add_argument("net")
p.add_argument("layer", choices=("F", "B")); p.add_argument("points", nargs="+")
p.add_argument("--via-start", action="store_true"); p.add_argument("--via-end", action="store_true")
args = p.parse_args()

board = pcbnew.LoadBoard(args.input); net = board.FindNet(args.net)
points = [pcbnew.VECTOR2I_MM(*map(float, value.split(","))) for value in args.points]
layer = pcbnew.F_Cu if args.layer == "F" else pcbnew.B_Cu
for start, end in zip(points, points[1:]):
    track = pcbnew.PCB_TRACK(board); track.SetStart(start); track.SetEnd(end)
    track.SetLayer(layer); track.SetWidth(pcbnew.FromMM(0.20)); track.SetNet(net); board.Add(track)
for position, enabled in ((points[0], args.via_start), (points[-1], args.via_end)):
    if enabled:
        via = pcbnew.PCB_VIA(board); via.SetPosition(position); via.SetNet(net)
        via.SetWidth(pcbnew.FromMM(0.6)); via.SetDrill(pcbnew.FromMM(0.3))
        via.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu); board.Add(via)
pcbnew.SaveBoard(args.output, board)
print(f"{args.net}: {args.layer}.Cu {len(points)-1} segments")
