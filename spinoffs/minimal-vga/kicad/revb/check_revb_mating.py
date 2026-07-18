#!/usr/bin/env python3
"""Mechanical mating contract checker (TG.1 / D1.31). Pure python — NO CAD tools — so
it runs in CI and on any desk. Asserts that every card's bus/ext connector geometry and
the backplane's slot geometry obey kicad/revb/mating.json, the single source of
mechanical truth. Two route-perfect boards that cannot physically plug together is the
class of error this guard exists to make impossible (the D1.18 completeness lesson,
applied to mechanics).

Checks:
  1. each card J_BUS  == (base_row_x, board_h - base_edge_offset)
  2. each card J_EXT  == (ext_row_x,  board_h - ext_edge_offset)
  3. backplane board height == backplane_board_h
  4. backplane slot k: J_S{k}_BUS == (base_row_x, slot0_y + (k-1)*slot_pitch)
                       J_S{k}_EXT == (ext_row_x,  that + ext_row_dy)
  5. base vs ext bus-column grids stay >= min_column_sep apart (2-layer routability)
  6. six slots + ext row + margin fit inside backplane_board_h, tail strip above them

Usage: check_revb_mating.py            # exit 0 = all match, 1 = any mismatch
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from revb_place import BOARD_H_BY_CARD, PLACE_BY_CARD  # noqa: E402

C = json.load(open(os.path.join(HERE, "mating.json")))
TOL = 0.001          # mm; contract values are exact, this only absorbs float noise
CARDS = ("mem", "io", "cpu")
fails = []


def near(a, b):
    return abs(a - b) <= TOL


def check_xy(label, got, exp_x, exp_y):
    gx, gy = got[0], got[1]
    if near(gx, exp_x) and near(gy, exp_y):
        return
    fails.append(f"{label}: got ({gx:.3f}, {gy:.3f}) expected ({exp_x:.3f}, {exp_y:.3f})")


# 1-2. per-card connector rows relative to the card's own bottom edge
for card in CARDS:
    h = BOARD_H_BY_CARD[card]
    place = PLACE_BY_CARD[card]
    check_xy(f"{card} J_BUS", place["J_BUS"], C["base_row_x"], h - C["base_edge_offset"])
    check_xy(f"{card} J_EXT", place["J_EXT"], C["ext_row_x"], h - C["ext_edge_offset"])

# 3. backplane outline height
if not near(BOARD_H_BY_CARD["backplane"], C["backplane_board_h"]):
    fails.append(f"backplane board_h: got {BOARD_H_BY_CARD['backplane']} "
                 f"expected {C['backplane_board_h']}")

# 4. backplane slot pairs
bp = PLACE_BY_CARD["backplane"]
for k in range(1, C["n_slots"] + 1):
    y_base = C["slot0_y"] + (k - 1) * C["slot_pitch"]
    bref, eref = f"J_S{k}_BUS", f"J_S{k}_EXT"
    if bref in bp:
        check_xy(bref, bp[bref], C["base_row_x"], y_base)
    else:
        fails.append(f"{bref}: missing from backplane placement")
    if eref in bp:
        check_xy(eref, bp[eref], C["ext_row_x"], y_base + C["ext_row_dy"])
    else:
        fails.append(f"{eref}: missing from backplane placement")

# 5. base vs ext column-grid separation (pins centre-symmetric about the row x)
pitch = C["pin_pitch"]
base_grid = C["base_row_x"] % pitch            # base 1x39: even pin count either side
ext_grid = (C["ext_row_x"] - 4.5 * pitch) % pitch   # ext 1x10: pin1 at centre-4.5*pitch
d = abs(base_grid - ext_grid) % pitch
col_sep = min(d, pitch - d)
if col_sep < C["min_column_sep"] - TOL:
    fails.append(f"column grids only {col_sep:.3f} mm apart "
                 f"(< min_column_sep {C['min_column_sep']}); base/ext bus columns collide")

# 6. geometric fit inside the backplane outline
top_ext = C["slot0_y"] + (C["n_slots"] - 1) * C["slot_pitch"] + C["ext_row_dy"]
if not (top_ext < C["tail_strip_y0"] < C["backplane_board_h"]):
    fails.append(f"tail strip y0 {C['tail_strip_y0']} must sit between top ext row "
                 f"{top_ext:.1f} and board height {C['backplane_board_h']}")
if top_ext + 3.0 > C["backplane_board_h"]:
    fails.append(f"top ext row {top_ext:.1f} + margin exceeds board height "
                 f"{C['backplane_board_h']}")

if fails:
    print(f"rev B mating contract: {len(fails)} violation(s) -> FAIL")
    for f in fails:
        print(f"    {f}")
    sys.exit(1)
print(f"rev B mating contract OK: {len(CARDS)} cards + {C['n_slots']}-slot backplane "
      f"obey mating.json (col sep {col_sep:.2f} mm)")
