#!/usr/bin/env python3
"""Apply exact-revision D93 HLT and RG dispositions to a generated PCB."""
from __future__ import annotations

import sys
import pcbnew


def net(board: pcbnew.BOARD, name: str) -> pcbnew.NETINFO_ITEM:
    found = board.FindNet(name)
    if found is not None:
        return found
    made = pcbnew.NETINFO_ITEM(board, name)
    board.Add(made)
    return made


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("usage: apply_d93_hlt_rg.py BOARD.kicad_pcb")
    board = pcbnew.LoadBoard(sys.argv[1])
    d93 = next((fp for fp in board.GetFootprints() if fp.GetReference() == "D93"), None)
    if d93 is None:
        raise SystemExit("D93 footprint is missing")
    d93.FindPadByNumber("23").SetNet(net(board, "FDC_READY"))
    d93.FindPadByNumber("25").SetNet(net(board, "D93_RG_NC"))
    pcbnew.SaveBoard(sys.argv[1], board)
    print("D93 HLT/RG: APPLIED — HLT->READY, RG->unused/open net")


if __name__ == "__main__":
    main()
