#!/usr/bin/python3
"""Apply the owner-closed D54/D55/D56 timing-net split to a PCB copy.

The July 2026 continuity batch superseded the older four-net topology after the
zero-open route was promoted.  This helper changes only the eight involved pad
assignments and removes copper on the four obsolete local nets.  New routed
copper must be added separately and accepted only after complete KiCad DRC.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pcbnew


ROOT = Path(__file__).resolve().parents[1]
BOARD_JSON = ROOT / "kicad" / "juku.board.json"

EXPECTED_OLD = {
    ("D54", "17"): "PIT_HSYNC_DSL",
    ("D55", "15"): "PIT_HSYNC_DSL",
    ("D55", "18"): "PIT_HSYNC_DSL",
    ("D55", "17"): "VERT_SYNC",
    ("D56", "2"): "SYNC_B",
    ("D56", "10"): "SYNC_B",
    ("D56", "12"): "D56_Q2N_TAG16",
    ("D57", "17"): "SYNC_B",
}

EXPECTED_NEW = {
    ("D54", "17"): "PIT_HSYNC_DSL",
    ("D55", "15"): "D56_Q2N_TAG16",
    ("D55", "18"): "D56_Q2N_TAG16",
    ("D55", "17"): "VERT_SYNC",
    ("D56", "2"): "VERT_SYNC",
    ("D56", "10"): "PIT_HSYNC_DSL",
    ("D56", "12"): "D56_Q2N_TAG16",
    ("D57", "17"): "SYNC_B",
}

AFFECTED_NETS = set(EXPECTED_OLD.values()) | set(EXPECTED_NEW.values())


def board_json_endpoints() -> dict[tuple[str, str], str]:
    spec = json.loads(BOARD_JSON.read_text(encoding="utf-8"))
    result: dict[tuple[str, str], str] = {}
    for net_name in AFFECTED_NETS:
        for ref, pin in spec["nets"][net_name].get("nodes", []):
            endpoint = (ref, pin)
            if endpoint in result:
                raise SystemExit(f"board JSON duplicates affected endpoint {ref}.{pin}")
            result[endpoint] = net_name
    return result


def pad(board: pcbnew.BOARD, ref: str, pin: str) -> pcbnew.PAD:
    footprint = board.FindFootprintByReference(ref)
    if footprint is None:
        raise SystemExit(f"missing footprint {ref}")
    result = footprint.FindPadByNumber(pin)
    if result is None:
        raise SystemExit(f"missing pad {ref}.{pin}")
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()

    if args.input.resolve() == args.output.resolve():
        raise SystemExit("input and output must differ")
    if board_json_endpoints() != EXPECTED_NEW:
        raise SystemExit("board JSON D54/D55/D56 owner-timing topology changed")

    board = pcbnew.LoadBoard(str(args.input))
    actual_old = {
        endpoint: pad(board, *endpoint).GetNetname()
        for endpoint in EXPECTED_OLD
    }
    if actual_old != EXPECTED_OLD:
        changed = {
            f"{ref}.{pin}": (EXPECTED_OLD[(ref, pin)], actual_old[(ref, pin)])
            for ref, pin in EXPECTED_OLD
            if actual_old[(ref, pin)] != EXPECTED_OLD[(ref, pin)]
        }
        raise SystemExit(f"input does not have the guarded old topology: {changed}")

    for endpoint, net_name in EXPECTED_NEW.items():
        net = board.FindNet(net_name)
        if net is None:
            raise SystemExit(f"input is missing net {net_name}")
        pad(board, *endpoint).SetNet(net)

    # pcbnew invalidates some SWIG footprint proxies after Board.Remove(), so
    # finish every pad lookup before removing routed items.
    removed = 0
    for item in list(board.GetTracks()):
        if item.GetNetname() in AFFECTED_NETS:
            board.Remove(item)
            removed += 1

    pcbnew.SaveBoard(str(args.output), board)
    print(
        f"D56 owner timing: reassigned {len(EXPECTED_NEW)} pads, "
        f"removed {removed} obsolete track/via items -> {args.output}"
    )


if __name__ == "__main__":
    main()
