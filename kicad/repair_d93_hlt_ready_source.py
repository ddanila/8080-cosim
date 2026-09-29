#!/usr/bin/env python3
"""Separate source-proved D99.4/D93.23 HLT from the routed READY trunk."""

from __future__ import annotations

import sys

import pcbnew


PAD = (243.561, 92.39)
REMOVE = {
    ((243.561, 92.39), (243.5, 93.0)),
    ((243.5, 93.0), (242.0, 94.5)),
    ((243.561, 92.39), (243.5, 92.0)),
    ((243.5, 92.0), (242.0, 90.5)),
}
BRIDGE = ((242.0, 90.5), (242.0, 94.5))


def xy(point: pcbnew.VECTOR2I) -> tuple[float, float]:
    return (round(pcbnew.ToMM(point.x), 3), round(pcbnew.ToMM(point.y), 3))


def point(pair: tuple[float, float]) -> pcbnew.VECTOR2I:
    return pcbnew.VECTOR2I(*(pcbnew.FromMM(v) for v in pair))


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("usage: repair_d93_hlt_ready_source.py BOARD.kicad_pcb")
    path = sys.argv[1]
    board = pcbnew.LoadBoard(path)
    if board is None:
        raise SystemExit(f"cannot load {path}")
    d93 = next(fp for fp in board.GetFootprints() if fp.GetReference() == "D93")
    pad = d93.FindPadByNumber("23")
    if xy(pad.GetPosition()) != PAD or pad.GetNetname() != "FDC_READY":
        raise SystemExit("D93.23 position or old READY net differs from guarded layout")
    hlt = board.FindNet("D99_Q1N_BOUNDARY")
    ready = board.FindNet("FDC_READY")
    if hlt is None or ready is None:
        raise SystemExit("expected HLT or READY net is missing")
    present = {
        (xy(track.GetStart()), xy(track.GetEnd())): track
        for track in board.GetTracks()
        if track.GetNetname() == "FDC_READY" and track.GetClass() == "PCB_TRACK"
    }
    matched = {ends: present[ends] for ends in REMOVE if ends in present}
    if matched and set(matched) != REMOVE:
        raise SystemExit(f"only part of D93.23 READY fanout matches: {sorted(matched)}")
    if not matched and any(path_part in path for path_part in ("routed", "candidate")):
        raise SystemExit("routed D93.23 READY fanout was not found")
    for track in matched.values():
        if track.GetLayer() != pcbnew.F_Cu or pcbnew.ToMM(track.GetWidth()) != 0.2:
            raise SystemExit("D93.23 READY fanout has unexpected layer or width")
    for track in matched.values():
        board.Remove(track)
    pad.SetNet(hlt)
    if matched:
        bridge = pcbnew.PCB_TRACK(board)
        bridge.SetStart(point(BRIDGE[0]))
        bridge.SetEnd(point(BRIDGE[1]))
        bridge.SetWidth(pcbnew.FromMM(0.2))
        bridge.SetLayer(pcbnew.F_Cu)
        bridge.SetNet(ready)
        board.Add(bridge)
    pcbnew.SaveBoard(path, board)
    print(f"D93 HLT/READY corrected: {path}; removed {len(matched)} READY segments")


if __name__ == "__main__":
    main()
