#!/usr/bin/env python3
"""Apply owner-measured D13/D93 reset and exact static-pin source closures."""
from __future__ import annotations

import sys

import pcbnew


def net(board: pcbnew.BOARD, name: str) -> pcbnew.NETINFO_ITEM:
    existing = board.FindNet(name)
    if existing is not None:
        return existing
    created = pcbnew.NETINFO_ITEM(board, name)
    board.Add(created)
    return created


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("usage: apply_d93_static_paths.py BOARD.kicad_pcb")
    path = sys.argv[1]
    board = pcbnew.LoadBoard(path)
    d93 = next((fp for fp in board.GetFootprints() if fp.GetReference() == "D93"), None)
    d13 = next((fp for fp in board.GetFootprints() if fp.GetReference() == "D13"), None)
    if d93 is None or d13 is None:
        raise SystemExit("D13/D93 footprint is missing")

    expected = {
        "19": {"D93_MR_BOUNDARY", "RESET", "FDC_RESET_N"},
        "22": {"D93_TEST_BOUNDARY", "D93_TEST_WF_VFOE"},
        "33": {"D93_WF_VFOE_BOUNDARY", "D93_TEST_WF_VFOE"},
    }
    for pin, allowed in expected.items():
        pad = d93.FindPadByNumber(pin)
        if pad is None:
            raise SystemExit(f"D93.{pin} pad is missing")
        if pad.GetNetname() not in allowed:
            raise SystemExit(
                f"D93.{pin} unexpected existing net {pad.GetNetname()!r}; expected {sorted(allowed)}"
            )

    reset = net(board, "RESET")
    fdc_reset = net(board, "FDC_RESET_N")
    for pin, target, allowed in (
        ("9", reset, {"", "RESET"}),
        ("8", fdc_reset, {"", "FDC_RESET_N"}),
    ):
        pad = d13.FindPadByNumber(pin)
        if pad is None or pad.GetNetname() not in allowed:
            actual = None if pad is None else pad.GetNetname()
            raise SystemExit(f"D13.{pin} unexpected existing net {actual!r}")
        pad.SetNet(target)
    d93.FindPadByNumber("19").SetNet(fdc_reset)
    static = net(board, "D93_TEST_WF_VFOE")
    d93.FindPadByNumber("22").SetNet(static)
    d93.FindPadByNumber("33").SetNet(static)
    pcbnew.SaveBoard(path, board)
    print("D93 STATIC PATHS: APPLIED — RESET->D13.9/.8->D93.19, TEST 22<->WF/VFOE 33")


if __name__ == "__main__":
    main()
