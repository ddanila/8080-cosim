#!/usr/bin/env /usr/bin/python3
"""Correct D34.12 to the native D37.11 pixel net in PCB snapshots.

The routed snapshots contain a false, unbranched clock spur from D34.12
to D103.11. Remove that spur without disturbing the D103-to-D57 clock path.
"""
from collections import defaultdict
from pathlib import Path
import pcbnew

ROOT = Path(__file__).resolve().parent
NAMES = ("juku.kicad_pcb", "juku_routed.kicad_pcb", "juku_routed_candidate.kicad_pcb")


def pos(point):
    return point.x, point.y


for name in NAMES:
    path = ROOT / name
    board = pcbnew.LoadBoard(str(path))
    fps = {fp.GetReference(): fp for fp in board.GetFootprints()}
    d34 = fps["D34"].FindPadByNumber("12")
    d103 = fps["D103"].FindPadByNumber("11")
    d37 = fps["D37"].FindPadByNumber("11")
    if (d34.GetNetname(), d103.GetNetname(), d37.GetNetname()) != (
        "CLK_123M", "CLK_123M", "VID_MIX1"
    ):
        raise RuntimeError(f"{name}: unexpected source pad nets")

    edges = defaultdict(list)
    for item in board.GetTracks():
        if item.GetNetname() != "CLK_123M" or not isinstance(item, pcbnew.PCB_TRACK):
            continue
        a, b = pos(item.GetStart()), pos(item.GetEnd())
        edges[a].append((b, item))
        edges[b].append((a, item))

    start, end = pos(d34.GetPosition()), pos(d103.GetPosition())
    remove = []
    if name != "juku.kicad_pcb":
        current, previous = start, None
        while current != end:
            options = [(other, item) for other, item in edges[current] if other != previous]
            if len(options) != 1 or (current != start and len(edges[current]) != 2):
                raise RuntimeError(f"{name}: clock spur branches at {current}")
            other, item = options[0]
            remove.append(item)
            previous, current = current, other
            if len(remove) > 11:
                raise RuntimeError(f"{name}: clock spur exceeds expected length")
        if len(remove) != 11:
            raise RuntimeError(f"{name}: expected 11 spur segments, found {len(remove)}")
    elif edges[start]:
        raise RuntimeError(f"{name}: source PCB unexpectedly has D34.12 clock copper")

    for item in remove:
        board.Remove(item)
    d34.SetNet(board.FindNet("VID_MIX1"))
    pcbnew.SaveBoard(str(path), board)
    print(f"{name}: D34.12 -> VID_MIX1; removed {len(remove)} false clock segments")
