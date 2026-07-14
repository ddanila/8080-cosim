#!/usr/bin/python3
"""Remove one routed KiCad item by UUID in a short-lived pypcbnew process."""

from pathlib import Path
import sys

import pcbnew


if len(sys.argv) < 4:
    raise SystemExit(f"usage: {sys.argv[0]} INPUT.kicad_pcb OUTPUT.kicad_pcb UUID [UUID ...]")

input_path, output_path = map(Path, sys.argv[1:3])
uuids = set(sys.argv[3:])
board = pcbnew.LoadBoard(str(input_path))
matches = [item for item in board.GetTracks() if item.m_Uuid.AsString() in uuids]
found = {item.m_Uuid.AsString() for item in matches}
if found != uuids or len(matches) != len(uuids):
    missing = sorted(uuids - found)
    raise SystemExit(
        f"expected {len(uuids)} unique routed-item UUIDs, found {len(matches)}; "
        f"missing={missing}"
    )
for item in matches:
    board.Remove(item)
pcbnew.SaveBoard(str(output_path), board)
