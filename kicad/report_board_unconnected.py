#!/usr/bin/env python3
"""Print KiCad's uncapped connectivity-graph unconnected count for a PCB."""

from __future__ import annotations

import argparse

import pcbnew


parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("board")
args = parser.parse_args()

board = pcbnew.LoadBoard(args.board)
board.BuildConnectivity()
print(board.GetConnectivity().GetUnconnectedCount(False))
