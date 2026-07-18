#!/usr/bin/env python3
"""Pure-python placement tables for rev B card PCBs (NO pcbnew import), so the PCB
generator (gen_revb_pcb.py) and the CI-safe mating checker (check_revb_mating.py) read
one source of truth. Values are footprint CENTRE (x, y, rotation_deg) in mm.

TG.2: the bus/ext CONNECTOR positions on every card and every backplane slot are DERIVED
from mating.json, so the mating contract and the generated geometry agree by construction
(the checker then guards against hand-edits and the derived invariants). Only the
non-connector parts keep hand-tuned positions.
"""
import json
import os

_HERE = os.path.dirname(os.path.abspath(__file__))
_C = json.load(open(os.path.join(_HERE, "mating.json")))

BOARD_W = 100.0
BOARD_H_BY_CARD = {"mem": 60.0, "io": 100.0, "cpu": 70.0,
                   "backplane": _C["backplane_board_h"]}


def _card_connectors(h):
    """Card bus/ext rows relative to the card's own bottom edge (contract-derived)."""
    return {
        "J_BUS": (_C["base_row_x"], h - _C["base_edge_offset"], 90),
        "J_EXT": (_C["ext_row_x"], h - _C["ext_edge_offset"], 90),
    }


# Non-connector parts per card (chips, caps, diag headers) — hand-placed for routing.
_PARTS = {
    "mem": {
        "U1": (20.0, 24.0, 180), "U2": (50.0, 23.0, 0), "U3": (82.0, 24.0, 0),
        "C1": (34.0, 10.0, 0), "C2": (64.0, 10.0, 0), "C3": (92.0, 10.0, 0),  # C1 clear of the 600mil U1
        "J_OBS": (75.0, 47.0, 90), "J_NOP": (40.0, 47.0, 90),
    },
    "io": {   # 100x100: three well-separated chip rows for 2-layer routing channels
        "U4": (29.0, 14.0, 90),   # 8255 DIP-40
        "U1": (78.0, 14.0, 90),   # 8251 DIP-28
        "U6": (26.0, 44.0, 90),   # 8259 DIP-28
        "U2": (76.0, 44.0, 90),   # GAL16V8 DIP-20
        "U5": (26.0, 72.0, 90),   # 74148 DIP-16
        "U3": (88.0, 70.0, 0),    # baud osc DIP-14 (vertical)
        "C1": (55.0, 28.0, 0), "C2": (55.0, 58.0, 0), "C3": (95.0, 28.0, 0), "C4": (62.0, 72.0, 0),
        "J_IOSEL": (90.0, 84.0, 90), "J_KBD": (40.0, 84.0, 90),
    },
    "cpu": {   # 100x70: unbuffered Z80 + osc + diag, wide fan-out channel (D1.21)
        "U1": (41.0, 22.0, 90),   # Z80 DIP-40 horizontal; x=41 from TF.1 sweep (D1.28) routes A8 0/0
        "U2": (85.0, 18.0, 0),    # clock osc DIP-14 vertical
        "C1": (66.0, 36.0, 0), "C2": (88.0, 42.0, 0),
        "J_DIAG": (40.0, 46.0, 90),
    },
}

PLACE_BY_CARD = {c: {**_card_connectors(BOARD_H_BY_CARD[c]), **_PARTS[c]}
                 for c in _PARTS}


def backplane_place():
    """Backplane = six per-slot base/ext connector PAIRS derived from mating.json, so a
    card (base row 5 mm up, ext row 10 mm up) mates: backplane slot k has its base socket
    at (base_row_x, slot0_y + k·pitch) and its ext socket ext_row_dy above it. Base rows
    span nearly the full width and their bus columns cover y 10..90, so the power/reset/
    serial tail lives in the column-free top strip above the slots (D1.31). Bus-signal
    pullups tap their columns from that strip; the DRC-gated route loop closes the rest."""
    p = {}
    x_b, x_e = _C["base_row_x"], _C["ext_row_x"]
    for k in range(_C["n_slots"]):
        y_base = _C["slot0_y"] + k * _C["slot_pitch"]
        p[f"J_S{k+1}_BUS"] = (x_b, y_base, 90)
        p[f"J_S{k+1}_EXT"] = (x_e, y_base + _C["ext_row_dy"], 90)

    # Tail lives in the two column-free strips: the TOP strip (above the top ext row)
    # holds the connectors + CC/LED resistors; the BOTTOM strip (below the first base
    # row, y<8) holds the six bus-signal pullups. All resistors horizontal (rot 0) to
    # stay short in Y. Splitting keeps each strip one part tall — no cross-row overlap.
    y_conn = _C["tail_strip_y0"] + 6.0     # 104 — connector row (tallest part ~USB-C)
    y_ccr  = _C["tail_strip_y0"] + 14.0    # 112 — CC/LED resistor row
    p["J_USBC"] = (14.0, y_conn, 0)
    p["J_PWR"]  = (30.0, y_conn, 0)
    p["U_RST"]  = (40.0, y_conn, 0)
    p["SW_RST"] = (50.0, y_conn, 0)
    p["J_FTDI"] = (64.0, y_conn, 0)
    p["JP_S5"]  = (73.0, y_conn, 0)        # near J_FTDI for the short TX/RX jumper link
    p["D_PWR"]  = (90.0, y_conn, 0)
    for ref, x in (("R_CC1", 20.0), ("R_CC2", 40.0), ("R_LED", 60.0)):
        p[ref] = (x, y_ccr, 0)
    # Bottom-strip bus-signal pullups, evenly spread (horizontal axials need ~16 mm
    # spacing). R_INT sits at x=60 near its INT_N column (x~55) so its tap is a short
    # stub; R_BRQ takes the far-left slot near its BUSRQ_N column (x~8). A far-flung
    # pullup (R_INT at x=12 vs its column at 55) otherwise left a long unroutable tap.
    for ref, x in (("R_BRQ", 12.0), ("R_WAIT", 28.0), ("R_NMI", 44.0),
                   ("R_INT", 60.0), ("R_M0", 76.0), ("R_M1", 92.0)):
        p[ref] = (x, 4.0, 0)               # bottom strip, below the first base row
    return p


PLACE_BY_CARD["backplane"] = backplane_place()
