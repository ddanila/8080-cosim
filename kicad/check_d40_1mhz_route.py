#!/usr/bin/env python3
"""Guard the owner-proved D40.11 1 MHz slot-clock route."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pcbnew


ROOT = Path(__file__).resolve().parents[1]
SPEC_PATH = ROOT / "kicad" / "juku.board.json"
DEFAULT_BOARDS = (
    ROOT / "kicad" / "juku.kicad_pcb",
    ROOT / "kicad" / "juku_routed.kicad_pcb",
    ROOT / "kicad" / "juku_routed_candidate.kicad_pcb",
)
TARGET_NET = "LATCH_B"
RETIRED_NET = "VID_MUX_G"
TARGET_ENDPOINTS = {
    ("D40", "11"),
    ("D37", "2"),
    ("D54", "9"),
    ("D54", "15"),
    ("D54", "18"),
    ("D95", "5"),
    ("D95", "6"),
    ("D92", "2"),
    ("D92", "3"),
    ("D59", "5"),
    ("E14", "1"),
    ("E14", "3"),
    ("D50", "15"),
    ("D51", "15"),
}
PHI2TTL_ENDPOINTS = {
    ("D35", "13"),
    ("D39", "1"),
    ("D53", "4"),
    ("D30", "3"),
}


def endpoints(spec: dict, net_name: str) -> set[tuple[str, str]]:
    return {
        (str(ref), str(pin))
        for ref, pin in spec["nets"][net_name].get("nodes", [])
    }


def board_pads(board: pcbnew.BOARD) -> dict[tuple[str, str], pcbnew.PAD]:
    return {
        (footprint.GetReference(), pad.GetNumber()): pad
        for footprint in board.GetFootprints()
        for pad in footprint.Pads()
    }


def check_board(path: Path) -> tuple[int, int]:
    board = pcbnew.LoadBoard(str(path))
    if board is None:
        raise SystemExit(f"{path}: failed to load")
    pads = board_pads(board)
    for endpoint in TARGET_ENDPOINTS:
        if pads[endpoint].GetNetname() != TARGET_NET:
            raise SystemExit(
                f"{path}: {endpoint[0]}.{endpoint[1]} is not on {TARGET_NET}"
            )
    for endpoint in PHI2TTL_ENDPOINTS:
        if pads[endpoint].GetNetname() != "PHI2TTL":
            raise SystemExit(
                f"{path}: {endpoint[0]}.{endpoint[1]} is not on PHI2TTL"
            )
    if pads[("D96", "6")].GetNetname() == TARGET_NET:
        raise SystemExit(f"{path}: forbidden D96.6 active-output merge")
    if any(pad.GetNetname() == RETIRED_NET for pad in pads.values()):
        raise SystemExit(f"{path}: pad remains on retired {RETIRED_NET}")
    tracks = list(board.GetTracks())
    expect_routed = bool(tracks)
    if any(item.GetNetname() == RETIRED_NET for item in tracks):
        raise SystemExit(f"{path}: copper remains on retired {RETIRED_NET}")

    ties = [
        item
        for item in tracks
        if item.GetClass() == "PCB_TRACK"
        and item.GetNetname() == TARGET_NET
        and item.GetLayer() == pcbnew.B_Cu
        and {
            (item.GetStart().x, item.GetStart().y),
            (item.GetEnd().x, item.GetEnd().y),
        }
        == {
            (
                pads[("D92", "2")].GetPosition().x,
                pads[("D92", "2")].GetPosition().y,
            ),
            (
                pads[("D92", "3")].GetPosition().x,
                pads[("D92", "3")].GetPosition().y,
            ),
        }
    ]
    if expect_routed and len(ties) != 1:
        raise SystemExit(f"{path}: expected one direct B.Cu D92.2/.3 tie")

    board.BuildConnectivity()
    opens = board.GetConnectivity().GetUnconnectedCount(False)
    if expect_routed and opens:
        raise SystemExit(f"{path}: routed board has {opens} open connection(s)")
    return len(pads), len(tracks)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("boards", nargs="*", type=Path)
    args = parser.parse_args()

    spec = json.loads(SPEC_PATH.read_text(encoding="utf-8"))
    if RETIRED_NET in spec["nets"]:
        raise SystemExit(f"board JSON still defines retired {RETIRED_NET}")
    if endpoints(spec, TARGET_NET) != TARGET_ENDPOINTS:
        raise SystemExit("board JSON 1 MHz endpoint set changed")
    if endpoints(spec, "PHI2TTL") != PHI2TTL_ENDPOINTS:
        raise SystemExit("board JSON PHI2TTL endpoint set changed")
    if "D40.11" not in spec["nets"][TARGET_NET].get("src", ""):
        raise SystemExit("board JSON 1 MHz provenance is missing D40.11")

    paths = tuple(args.boards) if args.boards else DEFAULT_BOARDS
    for path in paths:
        pad_count, copper_count = check_board(path)
        print(
            f"D40-1MHZ: PASS {path}; pads={pad_count}, copper={copper_count}"
        )


if __name__ == "__main__":
    main()
