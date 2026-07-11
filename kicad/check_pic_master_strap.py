#!/usr/bin/python3
"""Guard the sheet-1 D10 SP/EN high strap."""
from pathlib import Path

import pcbnew


ROOT = Path(__file__).resolve().parents[1]
board = pcbnew.LoadBoard(str(ROOT / "kicad/juku.kicad_pcb"))
d10 = board.FindFootprintByReference("D10")
pad = d10.FindPadByNumber("16") if d10 else None
if pad is None or pad.GetNetname() != "P5V":
    raise SystemExit("FAIL: D10.16 SP/EN is not strapped to P5V")
print("PIC MASTER STRAP: PASS — D10.16 SP/EN tied high")
