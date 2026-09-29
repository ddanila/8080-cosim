#!/usr/bin/env python3
"""Move D38.5 to source-proved LATCH and retire its obsolete rail-4 branch.

The exact .009 sheet-2 drawing places D38.5 on D33.12 LATCH. D39.3 and
D39.4 remain tied on numbered rail 4. Routed boards retain the short local
D39.3/.4 segment and remove only the former long branch to D38.5. A new
LATCH route must be added separately before a routed board is complete.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pcbnew


ROOT = Path(__file__).resolve().parents[1]
SPEC = ROOT / "kicad" / "juku.board.json"


def pad(board: pcbnew.BOARD, ref: str, number: str) -> pcbnew.PAD:
    footprint = board.FindFootprintByReference(ref)
    result = footprint.FindPadByNumber(number) if footprint else None
    if result is None:
        raise SystemExit(f"missing {ref}.{number}")
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    if args.input.resolve() == args.output.resolve():
        raise SystemExit("input and output must differ")

    spec = json.loads(SPEC.read_text(encoding="utf-8"))
    if {tuple(node) for node in spec["nets"]["D39_MEMCYC"]["nodes"]} != {
        ("D39", "3"), ("D39", "4")
    } or ("D38", "5") not in {
        tuple(node) for node in spec["nets"]["LATCH_SIG"]["nodes"]
    }:
        raise SystemExit("board JSON no longer has the source-corrected topology")

    board = pcbnew.LoadBoard(str(args.input))
    d38 = pad(board, "D38", "5")
    d39_3 = pad(board, "D39", "3")
    d39_4 = pad(board, "D39", "4")
    if d38.GetNetname() != "D39_MEMCYC":
        raise SystemExit(f"guarded D38.5 net mismatch: {d38.GetNetname()}")
    if {d39_3.GetNetname(), d39_4.GetNetname()} != {"D39_MEMCYC"}:
        raise SystemExit("guarded D39.3/.4 net mismatch")

    old_tracks = [
        item for item in board.GetTracks() if item.GetNetname() == "D39_MEMCYC"
    ]
    def xy(point: pcbnew.VECTOR2I) -> tuple[int, int]:
        return point.x, point.y

    tie_endpoints = {xy(d39_3.GetPosition()), xy(d39_4.GetPosition())}
    ties = [
        item for item in old_tracks
        if item.GetClass() == "PCB_TRACK"
        and item.GetLayer() == pcbnew.F_Cu
        and {xy(item.GetStart()), xy(item.GetEnd())} == tie_endpoints
    ]
    if old_tracks and (len(old_tracks) != 19 or len(ties) != 1):
        raise SystemExit(
            f"guarded rail-4 copper changed: {len(old_tracks)} items, "
            f"{len(ties)} local D39 ties"
        )
    for item in old_tracks:
        if item not in ties:
            board.Remove(item)

    latch = board.FindNet("LATCH_SIG")
    if latch is None:
        raise SystemExit("missing LATCH_SIG net")
    d38.SetNet(latch)
    pcbnew.SaveBoard(str(args.output), board)
    print(f"D38.5 -> LATCH_SIG; removed {len(old_tracks) - len(ties)} old tracks")


if __name__ == "__main__":
    main()
