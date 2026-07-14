#!/usr/bin/python3
"""Reroute the residual GND edge-clearance segment around a mounting hole."""

from __future__ import annotations

import math
from pathlib import Path
import sys

import pcbnew


if len(sys.argv) != 3:
    raise SystemExit(f"usage: {sys.argv[0]} INPUT.kicad_pcb OUTPUT.kicad_pcb")

input_path, output_path = map(Path, sys.argv[1:])
if input_path.resolve() == output_path.resolve():
    raise SystemExit("input and output must differ")

board = pcbnew.LoadBoard(str(input_path))


def mm(point: pcbnew.VECTOR2I) -> tuple[float, float]:
    return pcbnew.ToMM(point.x), pcbnew.ToMM(point.y)


def close(a: tuple[float, float], b: tuple[float, float]) -> bool:
    return math.hypot(a[0] - b[0], a[1] - b[1]) < 0.0001


def find_track(
    netname: str,
    layer: int,
    start: tuple[float, float],
    end: tuple[float, float],
) -> pcbnew.PCB_TRACK:
    matches = []
    for item in board.GetTracks():
        if isinstance(item, pcbnew.PCB_VIA):
            continue
        if item.GetNetname() != netname or item.GetLayer() != layer:
            continue
        actual_start, actual_end = mm(item.GetStart()), mm(item.GetEnd())
        if (close(actual_start, start) and close(actual_end, end)) or (
            close(actual_start, end) and close(actual_end, start)
        ):
            matches.append(item)
    if len(matches) != 1:
        raise SystemExit(
            f"expected one {netname} track from {start} to {end}, found {len(matches)}"
        )
    return matches[0]


def add_route(netname: str, layer: int, points: list[tuple[float, float]]) -> None:
    net = board.FindNet(netname)
    for start, end in zip(points, points[1:]):
        track = pcbnew.PCB_TRACK(board)
        track.SetStart(pcbnew.VECTOR2I_MM(*start))
        track.SetEnd(pcbnew.VECTOR2I_MM(*end))
        track.SetWidth(pcbnew.FromMM(0.20))
        track.SetLayer(layer)
        track.SetNet(net)
        board.Add(track)


# Preserve the live GND chain endpoints while moving the intervening segment
# above the Edge.Cuts circle centred at (199, 251.2), radius 1.75 mm.  The
# horizontal dogleg is 2.6 mm from the centre, leaving 0.75 mm copper-to-edge
# clearance for a 0.20 mm track against the configured 0.50 mm minimum.  The
# lower side is occupied by RAM_RD_OE.
gnd_edge_track = find_track(
    "GND",
    pcbnew.F_Cu,
    (201.8412, 249.1243),
    (196.6493, 249.1243),
)
board.Remove(gnd_edge_track)
add_route(
    "GND",
    pcbnew.F_Cu,
    [
        (201.8412, 249.1243),
        (202.0, 253.8),
        (196.0, 253.8),
        (196.6493, 249.1243),
    ],
)

pcbnew.SaveBoard(str(output_path), board)
print(f"rerouted GND edge segment -> {output_path}")
