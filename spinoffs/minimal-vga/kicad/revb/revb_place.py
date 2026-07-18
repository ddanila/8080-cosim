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

    # Tail lives in the two column-free strips. TOP strip (above the top ext row, now
    # ~22 mm tall) holds the power-entry / reset / serial parts in three rows; BOTTOM
    # strip (below the first base row, y<8) holds the six bus-signal pullups.
    y0 = _C["tail_strip_y0"]
    yr1, yr2, yr3 = y0 + 6.0, y0 + 13.0, y0 + 19.0   # 104, 111, 117
    # Headers rotated 90 so pins run along X (short in Y); the big USB-C goes far-right,
    # clear of the ext connectors (x 3..26). Row 1 = the tall parts (USB-C, bulk cap,
    # button, LED); rows 2-3 = the short parts (fuse, caps, headers, CC/LED resistors).
    p["C_BULK"] = (14.0, yr1, 0)
    p["SW_RST"] = (30.0, yr1, 0)
    p["D_PWR"]  = (44.0, yr1, 0)
    p["J_USBC"] = (82.0, yr1, 0)
    p["F_VBUS"] = (12.0, yr2, 0)
    p["C_IN"]   = (22.0, yr2, 0)
    p["J_PWR"]  = (32.0, yr2, 90)
    p["U_RST"]  = (46.0, yr2, 90)
    p["R_RST"]  = (60.0, yr2, 0)
    p["C_RST"]  = (70.0, yr2, 0)
    p["J_FTDI"] = (14.0, yr3, 90)
    p["JP_S5"]  = (30.0, yr3, 0)
    p["R_CC1"]  = (44.0, yr3, 0)
    p["R_CC2"]  = (56.0, yr3, 0)
    p["R_LED"]  = (68.0, yr3, 0)
    # Bottom-strip bus-signal pullups, evenly spread (horizontal axials need ~16 mm
    # spacing). R_INT sits near its INT_N column (x~55); R_BRQ near BUSRQ_N (x~8).
    for ref, x in (("R_BRQ", 12.0), ("R_WAIT", 28.0), ("R_NMI", 44.0),
                   ("R_INT", 60.0), ("R_M0", 76.0), ("R_M1", 92.0)):
        p[ref] = (x, 4.0, 0)               # bottom strip, below the first base row
    return p


PLACE_BY_CARD["backplane"] = backplane_place()
