#!/usr/bin/env python3
"""Apply the photo-proved D99.13 -> D93.24 backside clock route.

The corrected D99 and D93 solder fits identify both endpoints.  In
PXL_20260710_200506061.jpg the D93 joint launches one uninterrupted westbound
trace; panorama overlap identifies its far joint as D99 pin 13.  The script is
idempotent and touches only this net and its B.Cu route.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pcbnew

ROOT = Path(__file__).resolve().parents[1]
BOARD = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "kicad/juku.kicad_pcb"
NET = "FDC_CLK_1M"


def main() -> None:
    board = pcbnew.LoadBoard(str(BOARD))
    d93 = board.FindFootprintByReference("D93")
    d99 = board.FindFootprintByReference("D99")
    if d93 is None or d99 is None:
        raise SystemExit("D93 or D99 footprint absent")
    p93 = d93.FindPadByNumber("24")
    p99 = d99.FindPadByNumber("13")
    changed = False
    net = board.FindNet(NET)
    if net is None:
        net = pcbnew.NETINFO_ITEM(board, NET)
        board.Add(net)
        changed = True
    for pad in (p93, p99):
        if pad.GetNetname() != NET:
            pad.SetNet(net)
            changed = True

    start, end = p93.GetPosition(), p99.GetPosition()
    dx, dy = end.x - start.x, end.y - start.y
    vertices = [
        start,
        pcbnew.VECTOR2I(start.x + 65 * dx // 100, start.y),
        pcbnew.VECTOR2I(start.x + 72 * dx // 100, end.y),
        end,
    ]
    wanted = set()
    for a, b in zip(vertices, vertices[1:]):
        wanted.add((a.x, a.y, b.x, b.y))
        wanted.add((b.x, b.y, a.x, a.y))
    existing = set()
    for track in board.GetTracks():
        if track.GetLayer() != pcbnew.B_Cu or track.GetNetname() != NET:
            continue
        a, b = track.GetStart(), track.GetEnd()
        existing.add((a.x, a.y, b.x, b.y))
        existing.add((b.x, b.y, a.x, a.y))
    added = 0
    for a, b in zip(vertices, vertices[1:]):
        if (a.x, a.y, b.x, b.y) in existing:
            continue
        track = pcbnew.PCB_TRACK(board)
        track.SetLayer(pcbnew.B_Cu)
        track.SetNet(net)
        track.SetWidth(pcbnew.FromMM(0.45))
        track.SetStart(a)
        track.SetEnd(b)
        board.Add(track)
        added += 1
        changed = True
    if changed:
        pcbnew.SaveBoard(str(BOARD), board)
    print(f"patched D99.13 -> D93.24 {NET}; added {added} B.Cu segments to {BOARD}")


if __name__ == "__main__":
    main()
