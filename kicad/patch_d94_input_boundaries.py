#!/usr/bin/env python3
"""Retired one-shot migration for the superseded D94 address scaffold.

The authoritative mapping is now maintained in ``kicad/juku.board.json`` and
generated into the schematic. Owner continuity through 2026-07-19 proves
A0..A4 = BA0, BA1, IORD, D105.3 qualified /WR, D101.7. Re-running the old PCB
text patch would restore false boundary names, so this retained historical
entry point deliberately refuses to modify anything.
"""

raise SystemExit(
    "patch_d94_input_boundaries.py is retired; edit kicad/juku.board.json and "
    "regenerate the controlled PCB snapshot instead"
)
