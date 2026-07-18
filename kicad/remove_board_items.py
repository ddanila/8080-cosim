#!/usr/bin/python3
"""Remove a JSON-listed batch of track/via UUIDs in an isolated pcbnew process."""

from __future__ import annotations

import json
import os
from pathlib import Path
import sys

import pcbnew


if len(sys.argv) != 4:
    raise SystemExit(f"usage: {sys.argv[0]} INPUT OUTPUT UUIDS.json")

input_path, output_path, uuid_path = map(Path, sys.argv[1:])
if input_path.resolve() == output_path.resolve():
    raise SystemExit("input and output must differ")
requested = set(json.loads(uuid_path.read_text()))
if not requested:
    raise SystemExit("UUID list is empty")

board = pcbnew.LoadBoard(str(input_path))
by_uuid = {item.m_Uuid.AsString(): item for item in board.GetTracks()}
missing = requested - set(by_uuid)
if missing:
    raise SystemExit(f"track/via UUIDs not present: {sorted(missing)}")
for item_uuid in sorted(requested):
    board.Remove(by_uuid[item_uuid])
pcbnew.SaveBoard(str(output_path), board)
print(f"removed {len(requested)} board item(s) -> {output_path}")
sys.stdout.flush()
# KiCad 10.99's SWIG wrapper can crash while destructing hundreds of removed
# BOARD_ITEM proxies even after SaveBoard succeeded. This helper owns no caller
# state, so bypass teardown after the transactional file has been flushed.
os._exit(0)
