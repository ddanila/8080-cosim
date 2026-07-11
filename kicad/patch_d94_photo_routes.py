#!/usr/bin/env python3
"""Apply the three locally photo-traced D94-to-D93 component routes.

Evidence: two-sided package-local fits plus the continuous component-side
tracks in PXL_20260710_200402344.jpg.  The script is idempotent and touches only
D94 pads 1-3 and its new local fanout.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pcbnew

ROOT = Path(__file__).resolve().parents[1]
BOARD = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "kicad/juku.kicad_pcb"
ROUTES = {
    "1": ("FDC_RE_N", "4", [(229.275, 38.110), (232.000, 40.000), (232.000, 53.495), (240.380, 53.495)]),
    "2": ("FDC_CS_N", "3", [(231.815, 38.110), (234.000, 40.000), (234.000, 50.955), (240.380, 50.955)]),
    "3": ("FDC_WE_N", "2", [(234.355, 38.110), (236.000, 40.000), (236.000, 48.415), (240.380, 48.415)]),
}


def point(xy):
    return pcbnew.VECTOR2I(pcbnew.FromMM(xy[0]), pcbnew.FromMM(xy[1]))


def main() -> None:
    board = pcbnew.LoadBoard(str(BOARD)); d94 = board.FindFootprintByReference("D94")
    if d94 is None:
        raise SystemExit("D94 footprint absent")
    # The corrected footprint is two 2.54-mm pitches right of the prior source.
    current = d94.FindPadByNumber("1").GetPosition()
    delta = point((229.275, 38.110)) - current
    d94.SetPosition(d94.GetPosition() + delta)
    for pin in ("4", "5"):
        d94.FindPadByNumber(pin).SetNetCode(0)
    d93 = board.FindFootprintByReference("D93")
    if d93 is None:
        raise SystemExit("D93 footprint absent")
    # Reassign the already drawn photo-shaped geometry if it carries the former
    # assumed global I/O net; do not stack duplicate tracks on top of it.
    for pin, (net_name, d93_pin, vertices) in ROUTES.items():
        net = board.FindNet(net_name)
        if net is None:
            net = pcbnew.NETINFO_ITEM(board, net_name); board.Add(net)
        d94.FindPadByNumber(pin).SetNet(net); d93.FindPadByNumber(d93_pin).SetNet(net)
        segment_pairs = {(point(a).x, point(a).y, point(b).x, point(b).y)
                         for a, b in zip(vertices, vertices[1:])}
        segment_pairs |= {(x2, y2, x1, y1) for x1, y1, x2, y2 in segment_pairs}
        for track in board.GetTracks():
            a, b = track.GetStart(), track.GetEnd()
            if (a.x, a.y, b.x, b.y) in segment_pairs:
                track.SetNet(net)
    existing = set()
    for track in board.GetTracks():
        a, b = track.GetStart(), track.GetEnd()
        existing.add((track.GetNetname(), track.GetLayer(), a.x, a.y, b.x, b.y))
        existing.add((track.GetNetname(), track.GetLayer(), b.x, b.y, a.x, a.y))
    added = 0
    for pin, (net_name, d93_pin, vertices) in ROUTES.items():
        net = board.FindNet(net_name)
        pad = d94.FindPadByNumber(pin); pad.SetNet(net); d93.FindPadByNumber(d93_pin).SetNet(net)
        for start, end in zip(vertices, vertices[1:]):
            a, b = point(start), point(end)
            key = (net_name, pcbnew.F_Cu, a.x, a.y, b.x, b.y)
            if key in existing:
                continue
            track = pcbnew.PCB_TRACK(board); track.SetLayer(pcbnew.F_Cu)
            track.SetNet(net); track.SetWidth(pcbnew.FromMM(0.50))
            track.SetStart(a); track.SetEnd(b); board.Add(track); added += 1
    pcbnew.SaveBoard(str(BOARD), board)
    print(f"patched D94.1-3 nets; added {added} photo-matched F.Cu segments to {BOARD}")


if __name__ == "__main__":
    main()
