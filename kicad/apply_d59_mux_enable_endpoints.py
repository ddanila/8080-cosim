#!/usr/bin/python3
"""Assign the source-proved D59 mux-enable endpoints to a PCB copy.

Full-resolution sheet-2 review restores D59 section 5->6: input pin 5 is on
VID_MUX_G through E14, and output pin 6 is on CPU_MUX_G through E13.  This
helper changes only those two pad-net assignments.  Routed copper is added by
the guarded gap closer and accepted only after complete KiCad DRC.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pcbnew


ROOT = Path(__file__).resolve().parents[1]
BOARD_JSON = ROOT / "kicad" / "juku.board.json"
EXPECTED = {
    ("D59", "5"): "VID_MUX_G",
    ("D59", "6"): "CPU_MUX_G",
}


def board_json_endpoints() -> dict[tuple[str, str], str]:
    spec = json.loads(BOARD_JSON.read_text(encoding="utf-8"))
    result: dict[tuple[str, str], str] = {}
    for endpoint, net_name in EXPECTED.items():
        if list(endpoint) not in spec["nets"][net_name].get("nodes", []):
            raise SystemExit(
                f"board JSON no longer assigns {endpoint[0]}.{endpoint[1]} to {net_name}"
            )
        result[endpoint] = net_name
    return result


def pad(board: pcbnew.BOARD, ref: str, pin: str) -> pcbnew.PAD:
    footprint = board.FindFootprintByReference(ref)
    result = footprint.FindPadByNumber(pin) if footprint else None
    if result is None:
        raise SystemExit(f"missing PCB endpoint {ref}.{pin}")
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()

    if args.input.resolve() == args.output.resolve():
        raise SystemExit("input and output must differ")
    if board_json_endpoints() != EXPECTED:
        raise SystemExit("board JSON D59 mux-enable topology changed")

    board = pcbnew.LoadBoard(str(args.input))
    for endpoint, net_name in EXPECTED.items():
        target = pad(board, *endpoint)
        old_name = target.GetNetname()
        if old_name not in ("", net_name):
            raise SystemExit(
                f"guarded input mismatch: {endpoint[0]}.{endpoint[1]} is on {old_name}"
            )
        net = board.FindNet(net_name)
        if net is None:
            raise SystemExit(f"input PCB is missing net {net_name}")
        target.SetNet(net)

    pcbnew.SaveBoard(str(args.output), board)
    print(f"D59 mux enables: assigned 2 endpoints -> {args.output}")


if __name__ == "__main__":
    main()
