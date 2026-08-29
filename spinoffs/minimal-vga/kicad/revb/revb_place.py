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
                   "video": 100.0,
                   "backplane": _C["backplane_board_h"]}


def _card_connectors(h):
    """Card bus/ext rows relative to the card's own bottom edge (contract-derived)."""
    return {
        # 270 degrees points the right-angle mating posts out through the card's
        # bottom edge. J_EXT is mounted on B.Cu by the PCB generator so the two
        # connector bodies can overlap in XY without colliding in Z.
        "J_BUS": (_C["base_row_x"], h - _C["base_edge_offset"], 270),
        "J_EXT": (_C["ext_row_x"], h - _C["ext_edge_offset"], 270),
    }


# Non-connector parts per card (chips, caps, diag headers) — hand-placed for routing.
_PARTS = {
    "mem": {
        "U1": (20.0, 24.0, 180), "U2": (50.0, 23.0, 0), "U3": (82.0, 24.0, 0),
        "C1": (34.0, 10.0, 0), "C2": (64.0, 10.0, 0), "C3": (92.0, 10.0, 0),  # C1 clear of the 600mil U1
        "J_OBS": (75.0, 47.0, 90), "J_NOP": (40.0, 47.0, 90),
    },
    "io": {   # R5.I5: expanded D57/POST card, four signal-flow bands
        "U4": (28.0, 12.0, 90), "U1": (78.0, 12.0, 90),
        "U6": (18.5, 33.0, 90), "U8": (52.5, 33.0, 90), "U2": (83.5, 33.0, 90),
        "U5": (12.0, 56.0, 90), "U7": (34.0, 56.0, 90),
        "U9": (58.0, 56.0, 90), "U3": (86.0, 56.0, 0),
        # Front-side decouplers preserve the 16-mm card-stack envelope.  The
        # lower row sits in the measured channel between the second and third
        # socket bands; C1/C4 share the inter-package channel in the top band.
        "C1": (67.0, 22.5, 0), "C2": (76.0, 22.5, 0), "C3": (84.0, 45.0, 0),
        "C4": (43.0, 22.5, 0), "C5": (4.0, 48.0, 0), "C6": (35.0, 22.5, 0),
        "C7": (26.0, 48.0, 0), "C8": (64.0, 48.0, 0), "C9": (48.0, 48.0, 0),
        "D_POST0": (4.0, 70.0, 0), "D_POST1": (12.0, 70.0, 0),
        "D_POST2": (20.0, 70.0, 0), "D_POST3": (28.0, 70.0, 0),
        "D_POST4": (36.0, 70.0, 0), "D_POST5": (44.0, 70.0, 0),
        "D_POST6": (52.0, 70.0, 0), "D_POST7": (60.0, 70.0, 0),
        "R_POST0": (4.0, 78.0, 0), "R_POST1": (11.0, 78.0, 0),
        "R_POST2": (18.0, 78.0, 0), "R_POST3": (25.0, 78.0, 0),
        "R_POST4": (32.0, 78.0, 0), "R_POST5": (39.0, 78.0, 0),
        "R_POST6": (46.0, 78.0, 0), "R_POST7": (53.0, 78.0, 0),
        "BZ1": (69.5, 69.0, 0), "Q1": (82.0, 67.0, 0),
        "R_SOUND_BASE": (82.0, 73.0, 0), "R_SOUND_PD": (88.0, 73.0, 0),
        "J_SOUND": (74.0, 80.0, 0), "J_PIT_TP": (92.0, 78.0, 90),
        "J_KBD": (40.0, 86.0, 90), "J_IOSEL": (80.0, 88.0, 90),
        "JP_BAUD": (84.0, 82.0, 90), "JP_CLK_SRC": (94.0, 86.0, 90),
    },
    "cpu": {   # 100x70: unbuffered Z80 + osc + diag, wide fan-out channel (D1.21)
        # R5.J2 clean-source sweep refresh: x=39 routes 0/0 on bounded attempt 1;
        # the former x=41 result had become a repeated one-ratline placement.
        "U1": (39.0, 22.0, 90),   # Z80 DIP-40 horizontal
        "U2": (85.0, 18.0, 0),    # clock osc DIP-14 vertical
        "C1": (66.0, 36.0, 0), "C2": (88.0, 42.0, 0),
        "J_DIAG": (40.0, 46.0, 90),
    },
    # R5.V5 Video placement follows signal flow in six compact horizontal bands.
    # The VGA connector is edge-anchored separately by gen_revb_pcb.py; its tuple is
    # the exact footprint-origin position required after the 180-degree rotation.
    "video": {
        "J_VGA": (45.428, 2.5, 180),
        # Pixel output, timing and local oscillator along the top two bands.
        "U1": (10.8, 11.0, 0), "R_CLK": (23.4, 7.2, 90),
        "U23": (35.0, 11.0, 90), "U19": (30.5, 25.0, 90),
        "U5": (83.0, 11.0, 90),
        "U2": (10.0, 25.0, 90), "U3": (89.5, 25.0, 90),
        "U22": (51.0, 25.0, 90), "U4": (70.0, 25.0, 90),
        "C_BULK": (96.0, 68.0, 0),
        # Decode and scan address pipeline. U7 is vertical in the right-side channel.
        "U6": (26.0, 38.0, 90), "U12": (53.0, 38.0, 90),
        "U13": (74.0, 38.0, 90), "U7": (95.0, 45.5, 0),
        "U15": (5.5, 46.5, 0), "U17": (24.0, 51.5, 90),
        "U18": (51.0, 51.5, 90), "U14": (76.0, 51.5, 90),
        # CPU/scan address mux row and framebuffer/data row.
        "U8": (14.0, 62.8, 90), "U9": (35.0, 62.8, 90),
        "U10": (56.0, 62.8, 90), "U11": (77.0, 62.8, 90),
        "U20": (14.0, 76.6, 90), "U21": (50.0, 76.6, 90),
        "U16": (85.0, 76.6, 90),
        # RGB series network between the driver row and the edge connector.
        "R_VR": (27.0, 18.4, 0), "R_VG": (51.0, 18.4, 0),
        "R_VB": (39.0, 18.4, 0),
        # One 100 nF capacitor per U-number. Small 2.5-mm-pitch discs sit beside
        # their packages; the constrained set is mounted on B.Cu under sockets.
        "C1": (10.8, 2.5, 0), "C2": (10.0, 31.5, 0),
        "C3": (83.0, 18.4, 0), "C4": (70.0, 31.5, 0),
        "C5": (72.5, 11.0, 0), "C6": (16.0, 44.8, 0),
        "C7": (95.0, 35.0, 0), "C8": (8.9, 62.8, 0),
        "C9": (29.9, 62.8, 0), "C10": (50.9, 62.8, 0),
        "C11": (71.9, 62.8, 0), "C12": (43.0, 44.8, 0),
        "C13": (66.0, 44.8, 0), "C14": (75.0, 44.8, 0),
        "C15": (5.5, 34.0, 0), "C16": (85.0, 69.8, 0),
        "C17": (24.0, 44.8, 0), "C18": (51.0, 44.8, 0),
        "C19": (30.5, 31.5, 0), "C20": (14.0, 69.8, 0),
        "C21": (34.2, 74.0, 0), "C22": (51.0, 31.5, 0),
        "C23": (32.0, 2.5, 0),
    },
}

PLACE_BY_CARD = {c: {**_card_connectors(BOARD_H_BY_CARD[c]), **_PARTS[c]}
                 for c in _PARTS}


def backplane_place():
    """Backplane = five per-slot base/ext connector PAIRS derived from mating.json, so a
    card (base row 4 mm up, ext row 9 mm up) mates: backplane slot k has its base socket
    at (base_row_x, slot0_y + k·pitch) and its ext socket ext_row_dy above it. Base rows
    span nearly the full width and their bus columns cover y 10..74. The fifth slot is
    sufficient for the full CPU/memory/I/O/video/FDC system; omitting the former spare
    sixth slot leaves a mechanically clear top strip for power/reset/serial parts and
    puts the complete backplane inside the 100x100 low-cost fabrication tier."""
    p = {}
    x_b, x_e = _C["base_row_x"], _C["ext_row_x"]
    for k in range(_C["n_slots"]):
        y_base = _C["slot0_y"] + k * _C["slot_pitch"]
        # Match the outward-facing card headers: front-side base pin numbering
        # runs with 270 degrees; the back-side extension header matches 90 degrees.
        p[f"J_S{k+1}_BUS"] = (x_b, y_base, 270)
        p[f"J_S{k+1}_EXT"] = (x_e, y_base + _C["ext_row_dy"], 90)

    # The top strip is outside every seated-card envelope. This retains accessible
    # top-side power/reset/serial hardware without the component-collision risk of the
    # rejected six-slot 100x100 inter-slot experiment. Three sparse, staggered rows
    # keep through-hole chains from walling off the two-layer routing channels.
    y0 = _C["tail_strip_y0"]
    yr1, yr2, yr3 = y0 + 3.0, y0 + 9.0, y0 + 15.0
    p["C_BULK"] = (18.0, yr1, 0)
    p["SW_RST"] = (76.0, yr1, 0)
    p["D_PWR"]  = (85.0, yr1, 0)
    p["W_VCC"]  = (8.0, y0 + 12.0, 0)
    p["W_GND"]  = (18.0, y0 + 12.0, 0)
    p["C_IN"]   = (37.6, yr1, 0)
    p["C_CON"]  = (37.6, yr2, 0)
    p["U_CON"]  = (29.0, yr2 - 0.5, 0)
    # J_PWR uses an origin-at-edge placement in gen_revb_pcb.py.  At 180 degrees
    # the opening faces the top edge and the complete body remains on the board.
    p["J_PWR"]  = (47.5, 98.4, 180)
    # Vertical MF-R300: pad 1 (raw) is above pad 2 (VCC5), so the raw route
    # terminates before the 2-mm VCC5 spine continues down the same X coordinate.
    p["F_MAIN"] = (55.08, 89.0, 90)
    p["D_REV"]  = (65.0, yr1, 0)
    p["U_RST"]  = (71.5, yr2, 90)
    p["R_LED"]  = (8.0, yr3, 0)
    p["R_RST"]  = (18.0, yr3, 0)
    p["C_RST"]  = (37.6, yr3, 0)
    p["J_TTL"]  = (78.0, yr3, 90)
    p["JP_S5"]  = (77.5, yr2, 0)
    for ref, x in (("R_TX_TOP", 38.0), ("R_TX_BOT", 44.0),
                   ("R_RX_SER", 50.0)):
        p[ref] = (x, y0, 0)
    p["R_RX_PULL"] = (61.0, yr2, 0)
    p["R_VSENSE"] = (66.5, yr2, 0)
    p["D_VSENSE"] = (85.0, yr2, 0)
    p["R_TX_PULL"] = (97.0, yr2, 0)
    p["R_BUS_RX"]  = (60.0, yr3, 0)
    # Bottom-strip bus-signal pullups, evenly spread (horizontal axials need ~16 mm
    # spacing). R_INT sits near its INT_N column (x~55); R_BRQ near BUSRQ_N (x~8).
    for ref, x in (("R_BRQ", 12.0), ("R_WAIT", 28.0), ("R_NMI", 44.0),
                   ("R_INT", 60.0), ("R_M0", 76.0), ("R_M1", 92.0)):
        p[ref] = (x, 4.0, 0)               # bottom strip, below the first base row
    return p


PLACE_BY_CARD["backplane"] = backplane_place()
