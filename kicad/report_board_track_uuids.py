#!/usr/bin/env python3
"""Write the sorted routed-item UUIDs from one KiCad PCB as JSON."""
from __future__ import annotations

import json
from pathlib import Path
import sys

import pcbnew


if len(sys.argv) != 3:
    raise SystemExit(f"usage: {sys.argv[0]} BOARD.kicad_pcb OUTPUT.json")

board_path, output_path = map(Path, sys.argv[1:])
board = pcbnew.LoadBoard(str(board_path))
uuids = sorted(item.m_Uuid.AsString() for item in board.GetTracks())
output_path.write_text(json.dumps(uuids, indent=2) + "\n")
