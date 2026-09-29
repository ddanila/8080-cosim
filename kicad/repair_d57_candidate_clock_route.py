#!/usr/bin/env python3
"""Restore source-correct D57.18 timing routes in a routed candidate copy.

The candidate's former D57.18-to-CLK_123M experiment conflicts with the
exact .009 VER RTR conductor and the board JSON. Copy the two affected routed
net geometries from the primary routed board, leaving all other nets intact.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pcbnew


ROOT = Path(__file__).resolve().parents[1]
NETS = ("VERT_RTR", "CLK_123M")
EXPECTED_PRIMARY = {"VERT_RTR": 69, "CLK_123M": 39}
EXPECTED_CANDIDATE = {"VERT_RTR": 31, "CLK_123M": 33}


def track_counts(board: pcbnew.BOARD) -> dict[str, int]:
    return {name: sum(t.GetNetname() == name for t in board.GetTracks()) for name in NETS}


def pad(board: pcbnew.BOARD, ref: str, pin: str) -> pcbnew.PAD:
    footprint = board.FindFootprintByReference(ref)
    result = footprint.FindPadByNumber(pin) if footprint else None
    if result is None:
        raise SystemExit(f"missing {ref}.{pin}")
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("primary", type=Path)
    parser.add_argument("candidate", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    if args.output.resolve() in (args.primary.resolve(), args.candidate.resolve()):
        raise SystemExit("output must differ from inputs")

    spec = json.loads((ROOT / "kicad/juku.board.json").read_text())
    if ["D57", "18"] not in spec["nets"]["VERT_RTR"]["nodes"]:
        raise SystemExit("board JSON no longer assigns D57.18 to VERT_RTR")
    primary = pcbnew.LoadBoard(str(args.primary))
    candidate = pcbnew.LoadBoard(str(args.candidate))
    if track_counts(primary) != EXPECTED_PRIMARY:
        raise SystemExit(f"primary route changed: {track_counts(primary)}")
    if track_counts(candidate) != EXPECTED_CANDIDATE:
        raise SystemExit(f"candidate route changed: {track_counts(candidate)}")
    if pad(primary, "D57", "18").GetNetname() != "VERT_RTR":
        raise SystemExit("primary D57.18 is not on VERT_RTR")
    target = pad(candidate, "D57", "18")
    if target.GetNetname() != "CLK_123M":
        raise SystemExit(f"candidate D57.18 changed: {target.GetNetname()}")

    # Capture primitive geometry before deleting candidate items. KiCad's
    # Python wrappers can retain borrowed pointers after BOARD.Remove().
    geometry = []
    for item in primary.GetTracks():
        if item.GetNetname() not in NETS:
            continue
        kind = item.GetClass()
        if kind not in ("PCB_TRACK", "PCB_VIA"):
            raise SystemExit(f"unsupported timing copper primitive {kind}")
        geometry.append((
            item.GetNetname(), kind, item.GetStart(), item.GetEnd(),
            item.GetLayer(),
            item.GetWidth(pcbnew.F_Cu) if kind == "PCB_VIA" else item.GetWidth(),
            item.GetDrill() if kind == "PCB_VIA" else None,
        ))

    old_items = [item for item in candidate.GetTracks() if item.GetNetname() in NETS]
    for item in old_items:
        candidate.Remove(item)
    for name, kind, start, end, layer, width, drill in geometry:
        if kind == "PCB_VIA":
            new = pcbnew.PCB_VIA(candidate)
            new.SetPosition(start)
            new.SetWidth(width)
            new.SetDrill(drill)
            new.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
        else:
            new = pcbnew.PCB_TRACK(candidate)
            new.SetStart(start)
            new.SetEnd(end)
            new.SetWidth(width)
            new.SetLayer(layer)
        new.SetNet(candidate.FindNet(name))
        candidate.Add(new)
    target.SetNet(candidate.FindNet("VERT_RTR"))
    pcbnew.SaveBoard(str(args.output), candidate)
    print(f"restored {len(geometry)} timing-copper items; D57.18 -> VERT_RTR")


if __name__ == "__main__":
    main()
