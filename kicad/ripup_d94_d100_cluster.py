#!/usr/bin/python3
"""Rip obsolete D94/D100 local routes before applying photo-correct placement."""
import sys
import os
import pcbnew

if len(sys.argv) != 3:
    raise SystemExit(f"usage: {sys.argv[0]} INPUT.kicad_pcb OUTPUT.kicad_pcb")

board = pcbnew.LoadBoard(sys.argv[1])
nets = {f"DB{bit}" for bit in range(8)} | {f"FDC_DAL{bit}" for bit in range(8)}
nets |= {f"BA{bit}" for bit in range(11, 16)} | {"GND", "P5V"}
x0, y0, x1, y1 = 215.0, 8.0, 277.0, 48.0


def inside(point):
    x, y = pcbnew.ToMM(point.x), pcbnew.ToMM(point.y)
    return x0 <= x <= x1 and y0 <= y <= y1


removed = []
for item in list(board.GetTracks()):
    if item.GetNetname() not in nets:
        continue
    if isinstance(item, pcbnew.PCB_VIA):
        hit = inside(item.GetPosition())
    else:
        hit = inside(item.GetStart()) or inside(item.GetEnd())
    if hit:
        removed.append(item.GetNetname())
        board.Remove(item)

pcbnew.SaveBoard(sys.argv[2], board)
from collections import Counter
print(f"removed {len(removed)} local items: {dict(sorted(Counter(removed).items()))}", flush=True)
# pcbnew nightly's SWIG layer double-destroys removed track wrappers during
# interpreter shutdown. The board is already atomically saved; bypass that
# faulty cleanup path so this deterministic generator exits successfully.
os._exit(0)
