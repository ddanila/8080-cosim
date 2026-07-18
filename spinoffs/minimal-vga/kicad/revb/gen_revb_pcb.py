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
        "U1": (35.0, 22.0, 90),   # Z80 DIP-40 horizontal
        "U2": (85.0, 18.0, 0),    # clock osc DIP-14 vertical
        "C1": (66.0, 36.0, 0), "C2": (88.0, 42.0, 0),
        "J_DIAG": (40.0, 46.0, 90),
    },
}
PLACE = PLACE_BY_CARD[CARD]


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
            add_fp("J_BUS", base_fp, PLACE["J_BUS"], base)
            add_fp("J_EXT", ext_fp, PLACE["J_EXT"], ext)
        else:
            fpname = fpmap.get(typ) or fpmap.get(f"HDR_1x{len(pins)}")
            xy = PLACE.get(ref, (50.0, 40.0))
            add_fp(ref, fpname, xy, pins, dnp=comp.get("dnp", False))

    # board-level silk placed in clear gaps (pin-1 marks come from the footprints).
    SILK = {
        "mem": [(f"REVB {CARD.upper()}", 60.0, 49.0, 1.3), ("NO HOT-PLUG", 89.0, 49.0, 1.2)],
        "io":  [(f"REVB {CARD.upper()}", 40.0, 30.0, 1.3), ("NO HOT-PLUG", 40.0, 58.0, 1.1)],
        "cpu": [(f"REVB {CARD.upper()}", 68.0, 46.0, 1.4), ("NO HOT-PLUG", 68.0, 53.0, 1.2)],
    }
    for text, sx, sy, ssz in SILK.get(CARD, SILK["mem"]):
        silk(board, text, sx, sy, size=ssz)

    outdir = os.path.join(REPO, "fab", "minimal-vga", "revb")
    os.makedirs(outdir, exist_ok=True)
    outpath = os.path.join(outdir, f"{CARD}.kicad_pcb")
    board.Save(outpath)
    print(f"wrote {outpath} ({len(list(board.GetFootprints()))} footprints, {len(nets)} nets)")


if __name__ == "__main__":
    main()
