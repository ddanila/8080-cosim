#!/usr/bin/env python3
"""Screen 14/16-pad IC supply-pad names and routed track endpoints."""

from pathlib import Path
import re

import pcbnew


ROOT = Path(__file__).resolve().parents[1]
BOARD = ROOT / "kicad/juku.kicad_pcb"
ROUTED = (ROOT / "kicad/juku_routed.kicad_pcb", ROOT / "kicad/juku_routed_candidate.kicad_pcb")
KNOWN_CONFLICT = {("D104", "16")}
KNOWN_UNROUTED = {
    (ref, pin)
    for ref, pins in {
        "D52": ("8", "16"), "D2": ("8", "16"),
        "D92": ("7",), "D8": ("16",),
    }.items()
    for pin in pins
}


def supply_pads(board: pcbnew.BOARD):
    counts = {14: 0, 16: 0}
    pads = {}
    for footprint in board.GetFootprints():
        ref = footprint.GetReference()
        if re.fullmatch(r"D\d+", ref) is None:
            continue
        numbered = {pad.GetNumber(): pad for pad in footprint.Pads()}
        count = len(numbered)
        if count not in counts:
            continue
        counts[count] += 1
        for pin in (("7", "14") if count == 14 else ("8", "16")):
            pads[(ref, pin)] = numbered[pin]
    return counts, pads


def main() -> int:
    board = pcbnew.LoadBoard(str(BOARD))
    counts, pads = supply_pads(board)
    gaps = {key for key, pad in pads.items() if not pad.GetNetname()}
    unexpected = gaps - KNOWN_CONFLICT
    resolved_conflict = KNOWN_CONFLICT - gaps
    print(f"Package pad screen: 14-pad={counts[14]}, 16-pad={counts[16]}, unowned={sorted(gaps)}")
    if unexpected or resolved_conflict:
        print(f"Unexpected unowned={sorted(unexpected)}; known-conflict state changed={sorted(resolved_conflict)}")
    failed = bool(unexpected or resolved_conflict)
    for path in ROUTED:
        routed = pcbnew.LoadBoard(str(path))
        _, rail_pads = supply_pads(routed)
        endpoints = {}
        for item in routed.GetTracks():
            if item.GetClass() != "PCB_TRACK":
                continue
            for point in (item.GetStart(), item.GetEnd()):
                endpoints.setdefault((point.x, point.y), set()).add(item.GetNetname())
        unconnected = {
            key for key, pad in rail_pads.items()
            if pad.GetNetname() and pad.GetNetname() not in endpoints.get((pad.GetPosition().x, pad.GetPosition().y), set())
        }
        print(f"{path.name}: no same-net track endpoint at {len(unconnected)} pads: {sorted(unconnected)}")
        failed |= unconnected != KNOWN_UNROUTED
    return int(failed)


if __name__ == "__main__":
    raise SystemExit(main())
