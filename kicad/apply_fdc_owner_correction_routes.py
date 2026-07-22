#!/usr/bin/python3
"""Reuse safe promoted copper around the owner-corrected R94/reset topology.

The old RESET route is still valid for every endpoint except D93.19.  Its two
pad-touching segments are withheld so the new FDC_RESET_N net cannot be
shorted.  Likewise, the old D98 READY route is reusable except for the two
segments that touched the resistor body formerly misidentified as R94.
"""
from __future__ import annotations

import argparse
import collections
import heapq
import math
from pathlib import Path
import subprocess
import sys
import tempfile

import pcbnew


ROOT = Path(__file__).resolve().parents[1]
PROMOTED_OLD = ROOT / "kicad/juku_routed.kicad_pcb"
ROUTER = ROOT / "kicad/repair_fdc_route_gaps.py"


def point(item: pcbnew.BOARD_ITEM, end: str) -> tuple[int, int]:
    value = item.GetStart() if end == "start" else item.GetEnd()
    return value.x, value.y


def copper_key(item: pcbnew.BOARD_ITEM, netname: str) -> tuple[object, ...]:
    if item.GetClass() == "PCB_TRACK":
        start, end = sorted((point(item, "start"), point(item, "end")))
        return ("track", start, end, item.GetLayer(), item.GetWidth(), netname)
    position = item.GetPosition()
    return (
        "via", (position.x, position.y), item.GetViaType(),
        item.GetWidth(item.TopLayer()), item.GetDrillValue(),
        item.TopLayer(), item.BottomLayer(), netname,
    )


def pad_position(board: pcbnew.BOARD, ref: str, pin: str) -> tuple[int, int]:
    footprint = board.FindFootprintByReference(ref)
    pad = footprint.FindPadByNumber(pin) if footprint is not None else None
    if pad is None:
        raise SystemExit(f"missing pad {ref}.{pin}")
    position = pad.GetPosition()
    return position.x, position.y


def terminal_cut_keys(
    board: pcbnew.BOARD,
    netname: str,
    ref: str,
    pin: str,
    cut_points: tuple[tuple[float, float, int], ...],
) -> set[tuple[object, ...]]:
    items = [item for item in board.GetTracks() if item.GetNetname() == netname]
    adjacency: dict[tuple[int, int, int], list[tuple[tuple[int, int, int], int, float]]] = collections.defaultdict(list)
    for index, item in enumerate(items):
        if item.GetClass() == "PCB_TRACK":
            start = (*point(item, "start"), item.GetLayer())
            end = (*point(item, "end"), item.GetLayer())
            weight = math.dist(start[:2], end[:2])
        else:
            position = item.GetPosition()
            start = (position.x, position.y, pcbnew.F_Cu)
            end = (position.x, position.y, pcbnew.B_Cu)
            weight = 0.0
        adjacency[start].append((end, index, weight))
        adjacency[end].append((start, index, weight))

    pad = board.FindFootprintByReference(ref).FindPadByNumber(pin)
    position = pad.GetPosition()
    starts = ((position.x, position.y, pcbnew.F_Cu),
              (position.x, position.y, pcbnew.B_Cu))
    cut_indexes: set[int] = set()
    for x_mm, y_mm, layer in cut_points:
        goal = (pcbnew.FromMM(x_mm), pcbnew.FromMM(y_mm), layer)
        distances = {start: 0.0 for start in starts}
        previous: dict[tuple[int, int, int], tuple[tuple[int, int, int], int]] = {}
        queue = [(0.0, start) for start in starts]
        heapq.heapify(queue)
        while queue:
            distance, current = heapq.heappop(queue)
            if distance != distances[current]:
                continue
            if current == goal:
                break
            for neighbor, index, weight in adjacency[current]:
                candidate = distance + weight
                if candidate < distances.get(neighbor, math.inf):
                    distances[neighbor] = candidate
                    previous[neighbor] = (current, index)
                    heapq.heappush(queue, (candidate, neighbor))
        if goal not in distances:
            raise SystemExit(f"{netname}: guarded cut point {x_mm},{y_mm} is not on old copper")
        current = goal
        while current not in starts:
            current, index = previous[current]
            cut_indexes.add(index)
    return {copper_key(items[index], netname) for index in cut_indexes}


def add_track(
    board: pcbnew.BOARD,
    netname: str,
    layer: int,
    start_mm: tuple[float, float],
    end_mm: tuple[float, float],
) -> None:
    track = pcbnew.PCB_TRACK(board)
    track.SetStart(pcbnew.VECTOR2I_MM(*start_mm))
    track.SetEnd(pcbnew.VECTOR2I_MM(*end_mm))
    track.SetLayer(layer)
    track.SetWidth(pcbnew.FromMM(0.20))
    track.SetNet(board.FindNet(netname))
    track.SetLocked(True)
    board.Add(track)


def remove_track(
    board: pcbnew.BOARD,
    netname: str,
    layer: int,
    start_mm: tuple[float, float],
    end_mm: tuple[float, float],
) -> None:
    wanted = {
        (pcbnew.FromMM(start_mm[0]), pcbnew.FromMM(start_mm[1])),
        (pcbnew.FromMM(end_mm[0]), pcbnew.FromMM(end_mm[1])),
    }
    matches = []
    for item in board.GetTracks():
        if (
            item.GetClass() == "PCB_TRACK"
            and item.GetNetname() == netname
            and item.GetLayer() == layer
            and {point(item, "start"), point(item, "end")} == wanted
        ):
            matches.append(item)
    if len(matches) != 1:
        raise SystemExit(
            f"expected one {netname} track {start_mm}->{end_mm}, found {len(matches)}"
        )
    board.Remove(matches[0])


def route_gap(
    input_path: Path,
    output_path: Path,
    netname: str,
    start: tuple[float, float],
    end: tuple[float, float],
    margin: float,
    step: float,
    clearance: float,
    start_layer: str,
    end_layer: str,
) -> None:
    subprocess.run(
        [
            sys.executable,
            str(ROUTER),
            str(input_path),
            str(output_path),
            "gap",
            netname,
            f"{start[0]},{start[1]}",
            f"{end[0]},{end[1]}",
            "M",
            str(margin),
            str(step),
            str(clearance),
            start_layer,
            end_layer,
        ],
        check=True,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="fresh routed-refresh candidate")
    parser.add_argument("output", type=Path)
    parser.add_argument("--old-routed", type=Path, default=PROMOTED_OLD)
    args = parser.parse_args()
    if args.input.resolve() == args.output.resolve():
        raise SystemExit("input and output must differ")

    old = pcbnew.LoadBoard(str(args.old_routed))
    board = pcbnew.LoadBoard(str(args.input))
    expected = {
        ("D13", "8"): "FDC_RESET_N",
        ("D13", "9"): "RESET",
        ("D93", "19"): "FDC_RESET_N",
        ("R94", "1"): "FDC_DRQ",
        ("R94", "2"): "P5V",
        ("RUNK1", "1"): "RUNK1_P1_BOUNDARY",
        ("RUNK1", "2"): "RUNK1_P2_BOUNDARY",
        ("D98", "3"): "D98_Y1_D28_READY",
        ("D28", "5"): "D98_Y1_D28_READY",
    }
    for endpoint, netname in expected.items():
        ref, pin = endpoint
        footprint = board.FindFootprintByReference(ref)
        pad = footprint.FindPadByNumber(pin) if footprint is not None else None
        if pad is None or pad.GetNetname() != netname:
            actual = None if pad is None else pad.GetNetname()
            raise SystemExit(f"{ref}.{pin} net {actual!r} != {netname!r}")

    reset_cut = terminal_cut_keys(
        old, "RESET", "D93", "19",
        ((225.25, 93.75, pcbnew.B_Cu), (226.0, 92.0, pcbnew.B_Cu)),
    )
    ready_cut = terminal_cut_keys(
        old, "D98_Y1_R94", "R94", "1",
        ((297.5, 46.0, pcbnew.F_Cu), (295.5, 52.5, pcbnew.F_Cu)),
    )
    d93_escape = terminal_cut_keys(
        old, "RESET", "D93", "19", ((226.0, 94.0, pcbnew.B_Cu),)
    )
    existing = {
        copper_key(item, item.GetNetname())
        for item in board.GetTracks()
    }
    copied = {"RESET": 0, "D98_Y1_D28_READY": 0}
    skipped = {"RESET": 0, "D98_Y1_D28_READY": 0}
    for old_name, new_name, cut_keys in (
        ("RESET", "RESET", reset_cut),
        ("D98_Y1_R94", "D98_Y1_D28_READY", ready_cut),
    ):
        target_net = board.FindNet(new_name)
        if target_net is None:
            raise SystemExit(f"missing target net {new_name}")
        for item in old.GetTracks():
            if item.GetNetname() != old_name:
                continue
            if copper_key(item, old_name) in cut_keys:
                skipped[new_name] += 1
                continue
            key = copper_key(item, new_name)
            if key in existing:
                continue
            duplicate = item.Duplicate()
            duplicate.SetNet(target_net)
            duplicate.SetLocked(True)
            board.Add(duplicate)
            existing.add(key)
            copied[new_name] += 1

    # Preserve the old, already-DRC-clean pad escape up to (226, 94), but
    # assign it to the newly separated active-low reset net.  It stops well
    # before the retained RESET bypass at (225.25, 93.75)->(226, 92).
    fdc_reset = board.FindNet("FDC_RESET_N")
    for item in old.GetTracks():
        if item.GetNetname() != "RESET" or copper_key(item, "RESET") not in d93_escape:
            continue
        duplicate = item.Duplicate()
        duplicate.SetNet(fdc_reset)
        duplicate.SetLocked(True)
        board.Add(duplicate)

    # Short owner-closed pull-up branches join the retained copper without
    # disturbing any other routed net.
    add_track(board, "P5V", pcbnew.F_Cu, (271.987, 50.331), (277.443, 50.273))
    add_track(board, "FDC_DRQ", pcbnew.B_Cu, (271.987, 57.951), (271.0, 60.5))
    # Bypass the old D93.19 transit point while keeping the rest of the RESET
    # tree intact; D93.19 now belongs only to FDC_RESET_N.
    add_track(board, "RESET", pcbnew.B_Cu, (225.25, 93.75), (226.0, 92.0))
    # Rejoin the two safe ends of the old READY route around the unidentified
    # resistor's isolated first pad.
    add_track(board, "D98_Y1_D28_READY", pcbnew.F_Cu, (297.5, 46.0), (294.5, 48.0))
    add_track(board, "D98_Y1_D28_READY", pcbnew.F_Cu, (294.5, 48.0), (294.5, 51.0))
    add_track(board, "D98_Y1_D28_READY", pcbnew.F_Cu, (294.5, 51.0), (295.5, 52.5))

    with tempfile.TemporaryDirectory(prefix="juku-fdc-owner-route-") as tmp_name:
        tmp = Path(tmp_name)
        stage0 = tmp / "owner-reuse.kicad_pcb"
        stage1 = tmp / "reset-local.kicad_pcb"
        stage2 = tmp / "d93-side.kicad_pcb"
        stage3 = tmp / "d13-escape.kicad_pcb"
        stage4 = tmp / "fdc-reset-joined.kicad_pcb"
        pcbnew.SaveBoard(str(stage0), board)

        # Restore the short RESET branch to the newly assigned D13.9 pad.
        route_gap(
            stage0, stage1, "RESET", (26.82, 201.495), (26.82, 209.115),
            15, 0.25, 0.20, "A", "A",
        )
        # Bring the D93 escape into the unobstructed top-edge corridor.
        route_gap(
            stage1, stage2, "FDC_RESET_N", (200.0, 1.5), (226.0, 94.0),
            30, 0.10, 0.20, "A", "B",
        )

        board = pcbnew.LoadBoard(str(stage2))
        # One short GND trace blocks the D13.8 escape.  Move only that trace;
        # its two endpoints are rejoined after FDC_RESET_N is complete.
        remove_track(
            board, "GND", pcbnew.F_Cu, (24.5, 207.0), (22.5, 209.0)
        )
        add_track(
            board, "FDC_RESET_N", pcbnew.F_Cu,
            (24.28, 209.115), (19.581537, 207.404899),
        )
        pcbnew.SaveBoard(str(stage3), board)

        route_gap(
            stage3, stage4, "FDC_RESET_N",
            (19.581537, 207.404899), (200.0, 1.5),
            40, 0.10, 0.20, "F", "A",
        )
        route_gap(
            stage4, args.output, "GND", (24.5, 207.0), (22.5, 209.0),
            15, 0.10, 0.20, "F", "F",
        )

    print(
        "FDC owner-route transaction: "
        f"RESET copied={copied['RESET']} skipped={skipped['RESET']}; "
        f"READY copied={copied['D98_Y1_D28_READY']} "
        f"skipped={skipped['D98_Y1_D28_READY']}; "
        f"D93 escape={len(d93_escape)} items; zero-open route stages=4"
    )


if __name__ == "__main__":
    main()
