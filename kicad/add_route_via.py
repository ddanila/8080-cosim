#!/usr/bin/python3
"""Add one explicit 0.60/0.30 mm through via to a PCB copy."""

import argparse

import pcbnew


parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("input")
parser.add_argument("output")
parser.add_argument("net")
parser.add_argument("position", help="X,Y in millimetres")
args = parser.parse_args()

board = pcbnew.LoadBoard(args.input)
net = board.FindNet(args.net)
if net is None:
    raise SystemExit(f"missing net {args.net}")
x, y = map(float, args.position.split(","))
via = pcbnew.PCB_VIA(board)
via.SetPosition(pcbnew.VECTOR2I_MM(x, y))
via.SetNet(net)
via.SetWidth(pcbnew.FromMM(0.60))
via.SetDrill(pcbnew.FromMM(0.30))
via.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
board.Add(via)
pcbnew.SaveBoard(args.output, board)
print(f"{args.net}: via at {x:.4f},{y:.4f} mm")
