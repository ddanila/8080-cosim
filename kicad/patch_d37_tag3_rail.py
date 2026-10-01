#!/usr/bin/env /usr/bin/python3
"""Move D37.12 from its provisional singleton to native numbered rail 3."""
from pathlib import Path
import pcbnew

ROOT = Path(__file__).resolve().parent
for name in ("juku.kicad_pcb", "juku_routed.kicad_pcb", "juku_routed_candidate.kicad_pcb"):
    path = ROOT / name
    board = pcbnew.LoadBoard(str(path))
    footprints = {fp.GetReference(): fp for fp in board.GetFootprints()}
    pad = footprints["D37"].FindPadByNumber("12")
    if pad.GetNetname() != "D37_I12_TAG3":
        raise RuntimeError(f"{name}: D37.12 unexpectedly on {pad.GetNetname()}")
    rail = board.FindNet("XTAL16M")
    if rail is None:
        raise RuntimeError(f"{name}: XTAL16M missing")
    pad.SetNet(rail)
    pcbnew.SaveBoard(str(path), board)
    print(f"{name}: D37.12 -> XTAL16M")
