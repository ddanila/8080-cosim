#!/usr/bin/env python3
"""Refresh routed PCB metadata while preserving electrically compatible copper.

The source PCB owns footprints, pad nets, placement, and the small set of
photo-proved routes.  The routed PCB owns the bulk autorouted copper.  Copper on
an old net involved in a pad-net split is deliberately quarantined; copying it
would short the newly separated pads.
"""
from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path

import pcbnew

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "kicad/juku.kicad_pcb"
ROUTED = ROOT / "kicad/juku_routed.kicad_pcb"


def pads(board: pcbnew.BOARD) -> dict[tuple[str, str], tuple[str, tuple[int, int]]]:
    return {(footprint.GetReference(), pad.GetNumber()):
            (pad.GetNetname(), (pad.GetPosition().x, pad.GetPosition().y))
            for footprint in board.GetFootprints() for pad in footprint.Pads()}


def copper_key(item: pcbnew.BOARD_ITEM) -> tuple[object, ...]:
    start = (item.GetStart().x, item.GetStart().y)
    end = (item.GetEnd().x, item.GetEnd().y)
    if item.GetClass() == "PCB_TRACK":
        start, end = sorted((start, end))
        return ("track", start, end, item.GetLayer(), item.GetWidth(), item.GetNetname())
    if item.GetClass() == "PCB_VIA":
        return ("via", start, item.GetViaType(), item.GetWidth(item.TopLayer()), item.GetDrillValue(),
                item.TopLayer(), item.BottomLayer(), item.GetNetname())
    raise ValueError(f"unsupported copper item {item.GetClass()}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, default=SOURCE)
    parser.add_argument("--routed", type=Path, default=ROUTED)
    parser.add_argument("--output", type=Path,
                        help="write an audit candidate; omitted for read-only classification")
    parser.add_argument("--verbose", action="store_true",
                        help="list every quarantined net and mismatched endpoint")
    parser.add_argument("--exclude-drc", type=Path, action="append", default=[],
                        help="quarantine routed track/via nets implicated by copper errors in a KiCad DRC JSON")
    args = parser.parse_args()

    source = pcbnew.LoadBoard(str(args.source))
    routed = pcbnew.LoadBoard(str(args.routed))
    source_pads, routed_pads = pads(source), pads(routed)
    mismatches = {key: (routed_pads[key][0], source_value[0])
                  for key, source_value in source_pads.items()
                  if key in routed_pads and routed_pads[key][0] != source_value[0]}

    def nets_to_endpoints(values: dict[tuple[str, str], tuple[str, tuple[int, int]]]):
        result: dict[str, dict[tuple[str, str], tuple[int, int]]] = {}
        for endpoint, (netname, position) in values.items():
            if netname:
                result.setdefault(netname, {})[endpoint] = position
        return result

    source_endpoints = nets_to_endpoints(source_pads)
    routed_endpoints = nets_to_endpoints(routed_pads)
    compatible_nets = {netname for netname, endpoints in source_endpoints.items()
                       if routed_endpoints.get(netname) == endpoints}
    forced_excluded: set[str] = set()
    for drc_path in args.exclude_drc:
        report = json.loads(drc_path.read_text())
        for violation in report.get("violations", []):
            if violation.get("type") not in {"shorting_items", "clearance", "tracks_crossing"}:
                continue
            for item in violation.get("items", []):
                description = str(item.get("description", ""))
                match = re.match(r"(?:Track|Via) \[([^]]+)]", description)
                if match and match.group(1) != "<no net>":
                    forced_excluded.add(match.group(1))
    compatible_nets -= forced_excluded
    routed_copper_nets = {item.GetNetname() for item in routed.GetTracks()}
    quarantined_nets = routed_copper_nets - compatible_nets

    source_nets = {str(name) for name in source.GetNetsByName().keys()}
    existing = {copper_key(item) for item in source.GetTracks()}
    copied = Counter()
    skipped = Counter()
    for item in routed.GetTracks():
        netname = item.GetNetname()
        if netname not in compatible_nets:
            skipped[netname] += 1
            continue
        if netname not in source_nets:
            skipped[f"removed:{netname}"] += 1
            continue
        key = copper_key(item)
        if key in existing:
            skipped["duplicate"] += 1
            continue
        if args.output:
            duplicate = item.Duplicate()
            duplicate.SetNet(source.FindNet(netname))
            duplicate.SetLocked(True)
            source.Add(duplicate)
        existing.add(key)
        copied[netname] += 1

    if args.output:
        source.GetDesignSettings().m_CopperEdgeClearance = routed.GetDesignSettings().m_CopperEdgeClearance
        pcbnew.SaveBoard(str(args.output), source)
    print(f"routed refresh: copied {sum(copied.values())} copper items on {len(copied)} nets")
    print(f"  compatible routed nets: {len(compatible_nets & routed_copper_nets)}")
    print(f"  quarantined routed nets: {len(quarantined_nets)}")
    print(f"  quarantined/duplicate items: {sum(skipped.values())}")
    print(f"  common-pad mismatches requiring reroute: {len(mismatches)}")
    print(f"  DRC-forced excluded nets: {len(forced_excluded)}")
    if args.verbose:
        print(f"  DRC-forced excluded net names: {sorted(forced_excluded)}")
        print(f"  quarantined item counts: {dict(skipped)}")
        print(f"  mismatched endpoints: {mismatches}")
    if args.output:
        print(f"wrote audit candidate {args.output}; run DRC before adoption")
    else:
        print("read-only audit; no PCB written")


if __name__ == "__main__":
    main()
