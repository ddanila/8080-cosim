#!/usr/bin/env python3
"""Apply the owner-proved D40.11 1 MHz net correction to a PCB copy.

The old routed topology treated D92.2/.3 as part of PHI2TTL and used those
pads as a bridge between D39.1 and D35.13.  This guarded migration removes
only those two route branches, preserves the physical D92.2<->D92.3 tie on
LATCH_B, and merges every former VID_MUX_G item into LATCH_B.  The resulting
routed board deliberately has three open gaps; guarded routing and complete
KiCad DRC must close them before promotion.
"""

from __future__ import annotations

import argparse
from collections import deque
import json
from pathlib import Path

import pcbnew


ROOT = Path(__file__).resolve().parents[1]
BOARD_JSON = ROOT / "kicad" / "juku.board.json"
TARGET_NET = "LATCH_B"
RETIRED_NET = "VID_MUX_G"
PHI2TTL_NET = "PHI2TTL"
MERGED_ENDPOINTS = {
    ("D59", "5"),
    ("E14", "1"),
    ("E14", "3"),
    ("D50", "15"),
    ("D51", "15"),
}
D92_ENDPOINTS = {("D92", "2"), ("D92", "3")}
EXPECTED_PHI2TTL_ENDPOINTS = {
    ("D35", "13"),
    ("D39", "1"),
    ("D53", "4"),
    ("D30", "3"),
}
EXPECTED_BRANCH_TRACK_COUNTS = {
    (("D39", "1"), ("D92", "2")): 15,
    (("D35", "13"), ("D92", "3")): 18,
}
EXTRA_BRANCH_UUIDS = {
    (("D35", "13"), ("D92", "3")): {
        "7b4def56-5b85-43b3-9e86-f3e37e41c76a",
    },
}


def endpoint_set(spec: dict, net_name: str) -> set[tuple[str, str]]:
    return {
        (str(ref), str(pin))
        for ref, pin in spec["nets"][net_name].get("nodes", [])
    }


def validate_board_json() -> None:
    spec = json.loads(BOARD_JSON.read_text(encoding="utf-8"))
    if RETIRED_NET in spec["nets"]:
        raise SystemExit(f"board JSON still defines retired net {RETIRED_NET}")
    target = endpoint_set(spec, TARGET_NET)
    if not MERGED_ENDPOINTS | D92_ENDPOINTS <= target:
        raise SystemExit("board JSON does not contain the complete 1 MHz merge")
    if endpoint_set(spec, PHI2TTL_NET) != EXPECTED_PHI2TTL_ENDPOINTS:
        raise SystemExit("board JSON PHI2TTL endpoint set changed")


def pad(board: pcbnew.BOARD, endpoint: tuple[str, str]) -> pcbnew.PAD:
    ref, pin = endpoint
    footprint = board.FindFootprintByReference(ref)
    result = footprint.FindPadByNumber(pin) if footprint else None
    if result is None:
        raise SystemExit(f"missing PCB endpoint {ref}.{pin}")
    return result


def item_key(item: pcbnew.BOARD_CONNECTED_ITEM) -> tuple[str, str]:
    return item.GetClass(), item.m_Uuid.AsString()


def connected_neighbors(
    connectivity: pcbnew.CONNECTIVITY_DATA,
    item: pcbnew.BOARD_CONNECTED_ITEM,
) -> list[pcbnew.BOARD_CONNECTED_ITEM]:
    return list(connectivity.GetConnectedTracks(item)) + list(
        connectivity.GetConnectedPads(item)
    )


def shortest_path(
    connectivity: pcbnew.CONNECTIVITY_DATA,
    start: pcbnew.PAD,
    finish: pcbnew.PAD,
    net_name: str,
) -> list[pcbnew.BOARD_CONNECTED_ITEM]:
    start_key = item_key(start)
    finish_key = item_key(finish)
    queue = deque([start])
    objects = {start_key: start}
    previous: dict[tuple[str, str], tuple[str, str] | None] = {start_key: None}

    while queue:
        current = queue.popleft()
        current_key = item_key(current)
        if current_key == finish_key:
            break
        for neighbor in connected_neighbors(connectivity, current):
            if neighbor.GetNetname() != net_name:
                continue
            neighbor_key = item_key(neighbor)
            if neighbor_key in previous:
                continue
            objects[neighbor_key] = neighbor
            previous[neighbor_key] = current_key
            queue.append(neighbor)
    else:
        raise SystemExit(
            f"no routed {net_name} path from "
            f"{start.GetParentFootprint().GetReference()}.{start.GetNumber()} to "
            f"{finish.GetParentFootprint().GetReference()}.{finish.GetNumber()}"
        )

    result = []
    key: tuple[str, str] | None = finish_key
    while key is not None:
        result.append(objects[key])
        key = previous[key]
    result.reverse()
    return result


def assign_endpoints(board: pcbnew.BOARD, target: pcbnew.NETINFO_ITEM) -> None:
    for endpoint in MERGED_ENDPOINTS:
        current = pad(board, endpoint)
        if current.GetNetname() != RETIRED_NET:
            raise SystemExit(
                f"guarded input mismatch: {endpoint[0]}.{endpoint[1]} is on "
                f"{current.GetNetname()}, expected {RETIRED_NET}"
            )
        current.SetNet(target)
    for endpoint in D92_ENDPOINTS:
        current = pad(board, endpoint)
        if current.GetNetname() != PHI2TTL_NET:
            raise SystemExit(
                f"guarded input mismatch: {endpoint[0]}.{endpoint[1]} is on "
                f"{current.GetNetname()}, expected {PHI2TTL_NET}"
            )
        current.SetNet(target)


def migrate_routed_copper(board: pcbnew.BOARD) -> tuple[int, int]:
    board.BuildConnectivity()
    connectivity = board.GetConnectivity()
    board_tracks = {
        item.m_Uuid.AsString(): item for item in board.GetTracks()
    }
    branch_uuids: set[str] = set()

    for endpoints, expected_count in EXPECTED_BRANCH_TRACK_COUNTS.items():
        start, finish = (pad(board, endpoint) for endpoint in endpoints)
        path = shortest_path(connectivity, start, finish, PHI2TTL_NET)
        copper = {
            item_key(item): item
            for item in path
            if item.GetClass() in {"PCB_TRACK", "PCB_VIA"}
        }
        # The rounded D92 through-hole pad touches two overlapping F.Cu
        # breakout segments.  The shortest graph path uses only one; both must
        # leave PHI2TTL or the unused segment would short the reassigned pad.
        copper.update(
            {
                item_key(item): item
                for item in connectivity.GetConnectedTracks(finish)
                if item.GetNetname() == PHI2TTL_NET
                and item.GetLayer() == pcbnew.F_Cu
            }
        )
        required_uuids = EXTRA_BRANCH_UUIDS.get(endpoints, set())
        copper.update(
            {
                item_key(item): item
                for item in board.GetTracks()
                if item.m_Uuid.AsString() in required_uuids
            }
        )
        if required_uuids - {item.m_Uuid.AsString() for item in copper.values()}:
            raise SystemExit(f"guarded extra branch copper is missing for {endpoints}")
        if len(copper) != expected_count:
            raise SystemExit(
                f"guarded {endpoints[0][0]}.{endpoints[0][1]} -> "
                f"{endpoints[1][0]}.{endpoints[1][1]} branch changed: "
                f"expected {expected_count} copper items, found {len(copper)}"
            )
        branch_uuids.update(item.m_Uuid.AsString() for item in copper.values())

    d92_2 = pad(board, ("D92", "2"))
    d92_3 = pad(board, ("D92", "3"))
    d92_3_track_keys = {
        item_key(item) for item in connectivity.GetConnectedTracks(d92_3)
    }
    ties = {
        item_key(item): item
        for item in connectivity.GetConnectedTracks(d92_2)
        if item_key(item) in d92_3_track_keys
        and item.GetNetname() == PHI2TTL_NET
        and item.GetClass() == "PCB_TRACK"
    }
    if len(ties) != 1:
        raise SystemExit(f"expected one D92.2/.3 copper tie, found {len(ties)}")
    tie_uuid = next(iter(ties.values())).m_Uuid.AsString()
    tie = board_tracks[tie_uuid]
    if tie.GetLayer() != pcbnew.B_Cu:
        raise SystemExit("guarded D92.2/.3 tie is no longer on B.Cu")

    target = board.FindNet(TARGET_NET)
    if target is None:
        raise SystemExit(f"input PCB is missing net {TARGET_NET}")
    tie.SetNet(target)

    retired_items = [
        item for item in board.GetTracks() if item.GetNetname() == RETIRED_NET
    ]
    if not retired_items:
        raise SystemExit(f"routed PCB has no {RETIRED_NET} copper to merge")
    for item in retired_items:
        item.SetNet(target)
    assign_endpoints(board, target)

    # Remove last: KiCad's Python connectivity wrappers retain borrowed
    # pointers, so no further item lookup is allowed after this loop.
    for item_uuid in branch_uuids:
        board.Remove(board_tracks[item_uuid])

    return len(branch_uuids), len(retired_items) + 1


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()

    if args.input.resolve() == args.output.resolve():
        raise SystemExit("input and output must differ")
    validate_board_json()

    board = pcbnew.LoadBoard(str(args.input))
    target = board.FindNet(TARGET_NET)
    if target is None:
        raise SystemExit(f"input PCB is missing net {TARGET_NET}")

    affected_tracks = [
        item
        for item in board.GetTracks()
        if item.GetNetname() in {RETIRED_NET, PHI2TTL_NET}
    ]
    removed = merged = 0
    if affected_tracks:
        removed, merged = migrate_routed_copper(board)
    else:
        assign_endpoints(board, target)

    pcbnew.SaveBoard(str(args.output), board)
    print(
        f"D40 1 MHz migration: endpoints=7, removed-phi2ttl-copper={removed}, "
        f"merged-copper={merged} -> {args.output}"
    )


if __name__ == "__main__":
    main()
