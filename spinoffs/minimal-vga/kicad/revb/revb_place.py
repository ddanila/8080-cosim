#!/usr/bin/env python3
"""Pure-python placement tables for rev B card PCBs (NO pcbnew import), so the PCB
generator (gen_revb_pcb.py) and the CI-safe mating checker (check_revb_mating.py) read
one source of truth. Values are footprint CENTRE (x, y, rotation_deg) in mm.

TG.1 state: card connector positions + the backplane layout are still the historical
hand-tuned values, which the mating checker (D1.31) deliberately FAILS against so it
proves it catches the known incompatibility. TG.2 rewires this module to DERIVE the
connector positions from mating.json so contract and reality agree by construction.
"""

BOARD_W = 100.0
BOARD_H_BY_CARD = {"mem": 60.0, "io": 100.0, "cpu": 70.0, "backplane": 100.0}

# Connectors rotated 90 so their pin rows run along X: the 1x39 base along the bottom
# edge, the 1x10 extension row just above it. DIPs vertical.
PLACE_BY_CARD = {
    "mem": {
        "J_BUS": (50.0, 55.0, 90), "J_EXT": (14.0, 50.0, 90),
        "U1": (20.0, 24.0, 180), "U2": (50.0, 23.0, 0), "U3": (82.0, 24.0, 0),
        "C1": (32.0, 10.0, 0), "C2": (64.0, 10.0, 0), "C3": (92.0, 10.0, 0),
        "J_OBS": (75.0, 47.0, 90), "J_NOP": (40.0, 47.0, 90),
    },
    "io": {   # 100x100: three well-separated chip rows for 2-layer routing channels
        "J_BUS": (50.0, 96.0, 90), "J_EXT": (14.0, 91.0, 90),
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
        "J_BUS": (50.0, 66.0, 90), "J_EXT": (14.0, 61.0, 90),
        "U1": (41.0, 22.0, 90),   # Z80 DIP-40 horizontal; x=41 from TF.1 sweep (D1.28) routes A8 0/0
        "U2": (85.0, 18.0, 0),    # clock osc DIP-14 vertical
        "C1": (66.0, 36.0, 0), "C2": (88.0, 42.0, 0),
        "J_DIAG": (40.0, 46.0, 90),
    },
}


def backplane_place():
    """Backplane placement. TG.1 state: the D1.30 two-bank layout (base bank upper, ext
    bank lower-left, tail lower-right) — route-clean but NOT mate-compatible, which the
    mating checker flags. TG.2 replaces this with per-slot base/ext pairs derived from
    mating.json."""
    p = {}
    for k in range(6):                       # base bank: x=50, 8 mm pitch, y 8..48
        p[f"J_S{k+1}_BUS"] = (50.0, 8.0 + k * 8.0, 90)
    for k in range(6):                       # ext bank: x=22, 4 mm pitch, y 68..88
        p[f"J_S{k+1}_EXT"] = (22.0, 68.0 + k * 4.0, 90)
    for ref, x in (("R_INT", 18.0), ("R_WAIT", 32.0), ("R_NMI", 46.0),
                   ("R_BRQ", 60.0), ("R_M0", 74.0), ("R_M1", 88.0)):
        p[ref] = (x, 58.0, 90)
    p["J_USBC"] = (48.0, 73.0, 0)
    p["J_PWR"]  = (60.0, 73.0, 0)
    p["U_RST"]  = (68.0, 73.0, 0)
    p["SW_RST"] = (76.0, 73.0, 0)
    p["J_FTDI"] = (87.0, 73.0, 0)
    p["JP_S5"]  = (46.0, 85.0, 0)
    p["D_PWR"]  = (55.0, 85.0, 0)
    p["R_LED"]  = (63.0, 85.0, 90)
    p["R_CC1"]  = (71.0, 85.0, 90)
    p["R_CC2"]  = (79.0, 85.0, 90)
    return p


PLACE_BY_CARD["backplane"] = backplane_place()
