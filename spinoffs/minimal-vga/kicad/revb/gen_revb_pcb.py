#!/usr/bin/env python3
"""Generate a rev B card PCB from its board.json (TD.7.2). Run with KiCad's python
(KICAD_PYTHON via env.sh). Reuses the pcbnew primitives proven in gen_rev_a_pcb.py:
footprint load, centre-place, Edge.Cuts outline, net assignment, silk. Deterministic
placement (no randomness); regeneration is content-checked, not byte-diffed (D1.25).

  KICAD_PYTHON gen_revb_pcb.py <card>   # writes fab/minimal-vga/revb/<card>.kicad_pcb
"""
import json, os, sys
import pcbnew

HERE = os.path.dirname(os.path.abspath(__file__))   # spinoffs/minimal-vga/kicad/revb
REPO = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
CARD = sys.argv[1] if len(sys.argv) > 1 else "mem"
FPROOT = os.environ["KICAD_FOOTPRINTS"]

# Card outlines (all <=100x100 cheap tier). io is taller: more parts (D1.23).
BOARD_H_BY_CARD = {"mem": 60.0, "io": 100.0, "cpu": 70.0, "backplane": 100.0}
BOARD_W = 100.0
BOARD_H = BOARD_H_BY_CARD.get(CARD, 60.0)

board_spec = json.load(open(os.path.join(HERE, f"{CARD}.board.json")))
fpmap = json.load(open(os.path.join(HERE, f"footprints.{CARD}.json")))


def mm(v): return pcbnew.FromMM(v)


def load_fp(fpname):
    lib, name = fpname.split(":")
    fp = pcbnew.FootprintLoad(os.path.join(FPROOT, f"{lib}.pretty"), name)
    if fp is None:
        raise RuntimeError(f"missing footprint {fpname}")
    return fp


def place(fp, x, y, rot=0):
    # rotate first (changes the bounding box), then centre the bbox on (x, y).
    if rot:
        fp.SetOrientationDegrees(rot)
    fp.SetPosition(pcbnew.VECTOR2I(mm(x), mm(y)))
    c = fp.GetBoundingBox(False, False).GetCenter()
    fp.SetPosition(pcbnew.VECTOR2I(2 * mm(x) - c.x, 2 * mm(y) - c.y))


def outline(board):
    for x1, y1, x2, y2 in ((0, 0, BOARD_W, 0), (BOARD_W, 0, BOARD_W, BOARD_H),
                           (BOARD_W, BOARD_H, 0, BOARD_H), (0, BOARD_H, 0, 0)):
        s = pcbnew.PCB_SHAPE(board); s.SetShape(pcbnew.SHAPE_T_SEGMENT)
        s.SetLayer(pcbnew.Edge_Cuts); s.SetWidth(mm(0.15))
        s.SetStart(pcbnew.VECTOR2I(mm(x1), mm(y1))); s.SetEnd(pcbnew.VECTOR2I(mm(x2), mm(y2)))
        board.Add(s)


def emit_bus_columns(board):
    """D1.29 column-route: the six base (and six ext) connectors are stacked at the
    same x-origin, so pad N of every slot shares an X and differs only in Y — a
    straight F.Cu segment between consecutive slots' pad N routes that whole bus net.
    We emit these deterministic vertical tracks here (locked, so freerouting keeps
    them and only fills the irregular power tail). Returns the track count."""
    import re
    from collections import defaultdict
    fps = {fp.GetReference(): fp for fp in board.GetFootprints()}
    n = 0
    for suffix in ("BUS", "EXT"):
        conns = sorted((r for r in fps if re.match(rf"J_S\d+_{suffix}$", r)),
                       key=lambda r: int(re.match(r"J_S(\d+)_", r).group(1)))
        if len(conns) < 2:
            continue
        cols = defaultdict(list)          # pad number -> pads across all slots
        for r in conns:
            for pad in fps[r].Pads():
                cols[pad.GetNumber()].append(pad)
        for pads in cols.values():
            pads.sort(key=lambda p: p.GetPosition().y)
            for a, b in zip(pads, pads[1:]):
                t = pcbnew.PCB_TRACK(board)
                t.SetStart(a.GetPosition()); t.SetEnd(b.GetPosition())
                t.SetWidth(mm(0.3)); t.SetLayer(pcbnew.F_Cu)
                net = a.GetNet()
                if net is not None:
                    t.SetNet(net)
                t.SetLocked(True)
                board.Add(t); n += 1
    return n


def silk(board, text, x, y, size=1.5, angle=0):
    t = pcbnew.PCB_TEXT(board); t.SetLayer(pcbnew.F_SilkS); t.SetText(text)
    t.SetTextPos(pcbnew.VECTOR2I(mm(x), mm(y))); t.SetTextAngleDegrees(angle)
    t.SetTextSize(pcbnew.VECTOR2I(mm(size), mm(size))); t.SetTextThickness(mm(0.2))
    board.Add(t)


# Deterministic placement table (mm, footprint CENTRE, rotation deg). Connectors
# rotated 90 so their pin rows run along X: the 1x39 base along the bottom edge, the
# 1x10 extension row just above it, pin-1-end aligned (D1.23/D1.4). DIPs vertical.
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
def _backplane_place():
    """Programmatic backplane placement (TF.2 / D1.29–D1.30). The six 39-pin base
    connectors span nearly the full width, so their vertical bus columns cover the
    board: the only clear space is the top/bottom margins. We therefore stack the
    six base connectors column-aligned in the UPPER region and the six 10-pin ext
    connectors column-aligned in the LOWER-LEFT (two independent bussed banks, each
    cleanly column-routable), and drop the power/reset/FTDI/LED tail into the free
    LOWER-RIGHT quadrant. Per-card base/ext edge mating is validated in Stage D."""
    p = {}
    for k in range(6):                       # base bank: x=50, 8 mm pitch, y 8..48
        p[f"J_S{k+1}_BUS"] = (50.0, 8.0 + k * 8.0, 90)
    for k in range(6):                       # ext bank: x=22, 4 mm pitch, y 68..88
        p[f"J_S{k+1}_EXT"] = (22.0, 68.0 + k * 4.0, 90)
    # Bus-signal pullups sit in the interior band between the two banks (y~58), spread
    # across the width so each taps its own column with a SHORT interior stub — this is
    # what keeps freerouting from dragging a long cross-board trace + via into a corner
    # (the copper-edge failure mode). Vertical (rot 90) to stay thin.
    for ref, x in (("R_INT", 18.0), ("R_WAIT", 32.0), ("R_NMI", 46.0),
                   ("R_BRQ", 60.0), ("R_M0", 74.0), ("R_M1", 88.0)):
        p[ref] = (x, 58.0, 90)
    # power/reset/serial tail: lower-right, all >=5 mm from every edge (ext bank owns
    # the lower-left). Coordinates are DRC-tuned, not hand-precise.
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


PLACE_BY_CARD["backplane"] = _backplane_place()
PLACE = dict(PLACE_BY_CARD[CARD])

# TF.1 placement-sweep hook (D1.28). The cpu card's A8 is a deterministic 2-layer
# fan-out constraint, so we search for a routable Z80 x-position/rotation headlessly
# rather than re-rolling the stochastic router. When REVB_SWEEP_REF names a placed
# ref, its X and rotation are overridden from the environment (Y is kept). This path
# is used only during the search; the winning value gets folded back into the table
# above, so normal regeneration never depends on the environment.
_sw_ref = os.environ.get("REVB_SWEEP_REF")
if _sw_ref and _sw_ref in PLACE:
    _x, _y, _rot = PLACE[_sw_ref]
    _x = float(os.environ.get("REVB_SWEEP_X", _x))
    _rot = float(os.environ.get("REVB_SWEEP_ROT", _rot))
    PLACE[_sw_ref] = (_x, _y, _rot)


def main():
    board = pcbnew.BOARD()
    outline(board)

    # nets: one per board.json net name
    nets = {}
    for name in board_spec["nets"]:
        ni = pcbnew.NETINFO_ITEM(board, name)
        board.Add(ni); nets[name] = ni

    def add_fp(ref, fpname, xy, pin_to_net, dnp=False):
        fp = load_fp(fpname)
        board.Add(fp)
        fp.SetReference(ref)
        place(fp, *xy)
        if dnp:
            try: fp.SetDNP(True)
            except Exception: pass
        for pad in fp.Pads():
            net = pin_to_net.get(str(pad.GetNumber()))
            if net and net in nets:
                pad.SetNet(nets[net])
        # Hide per-footprint ref/value silk (they stray onto pads/outlines on this
        # dense card); board-level silk carries the essentials. Adding tidy per-ref
        # designators is cosmetic polish for the visual layout pass.
        fp.Value().SetVisible(False)
        fp.Reference().SetVisible(False)
        return fp

    for comp in board_spec["chips"]:
        ref, typ, pins = comp["ref"], comp["type"], comp["pins"]
        if typ == "REVB_BUS_39_10":
            base_fp, ext_fp = fpmap[typ]
            base = {p: n for p, n in pins.items() if p.isdigit()}
            ext = {p[1:]: n for p, n in pins.items() if p.startswith("E")}  # E1->pad 1
            # Single-card bus keeps the J_BUS/J_EXT names; the backplane's six slots
            # (J_S1..J_S6) derive per-slot refs so each connector is uniquely named
            # and its pins align in vertical columns (D1.29 column-route prerequisite).
            bref = "J_BUS" if ref == "J_BUS" else f"{ref}_BUS"
            eref = "J_EXT" if ref == "J_BUS" else f"{ref}_EXT"
            add_fp(bref, base_fp, PLACE[bref], base)
            add_fp(eref, ext_fp, PLACE[eref], ext)
        elif typ == "USB_C_PWR":
            # Map logical power pins to the 6P receptacle's physical pads; shield->GND.
            v, g = pins["VBUS"], pins["GND"]
            padnet = {"A9": v, "B9": v, "A12": g, "B12": g,
                      "A5": pins["CC1"], "B5": pins["CC2"], "SH": g}
            add_fp(ref, fpmap[typ], PLACE.get(ref, (50.0, 40.0)), padnet)
        else:
            fpname = fpmap.get(typ) or fpmap.get(f"HDR_1x{len(pins)}")
            xy = PLACE.get(ref, (50.0, 40.0))
            add_fp(ref, fpname, xy, pins, dnp=comp.get("dnp", False))

    # board-level silk placed in clear gaps (pin-1 marks come from the footprints).
    SILK = {
        "mem": [(f"REVB {CARD.upper()}", 60.0, 49.0, 1.3), ("NO HOT-PLUG", 89.0, 49.0, 1.2)],
        "io":  [(f"REVB {CARD.upper()}", 40.0, 30.0, 1.3), ("NO HOT-PLUG", 40.0, 58.0, 1.1)],
        "cpu": [(f"REVB {CARD.upper()}", 68.0, 46.0, 1.4), ("NO HOT-PLUG", 68.0, 53.0, 1.2)],
        # backplane: labels in the clear top strip above the base bank (y<8, no copper).
        "backplane": [("REVB BACKPLANE", 30.0, 4.0, 1.3), ("NO HOT-PLUG", 78.0, 4.0, 1.1)],
    }
    for text, sx, sy, ssz in SILK.get(CARD, SILK["mem"]):
        silk(board, text, sx, sy, size=ssz)

    # backplane bus columns are emitted deterministically (D1.29); other cards route
    # entirely via freerouting.
    if CARD == "backplane":
        ncol = emit_bus_columns(board)
        print(f"  emitted {ncol} bus-column track segments (locked)")

    outdir = os.path.join(REPO, "fab", "minimal-vga", "revb")
    os.makedirs(outdir, exist_ok=True)
    outpath = os.path.join(outdir, f"{CARD}.kicad_pcb")
    board.Save(outpath)
    print(f"wrote {outpath} ({len(list(board.GetFootprints()))} footprints, {len(nets)} nets)")


if __name__ == "__main__":
    main()
