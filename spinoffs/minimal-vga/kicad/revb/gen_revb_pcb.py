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

BOARD_W, BOARD_H = 100.0, 60.0     # D1.23 mem-card outline

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
    fp.SetPosition(pcbnew.VECTOR2I(mm(x), mm(y)))
    if rot:
        fp.SetOrientationDegrees(rot)


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


# Deterministic placement table (mm, footprint centre). The bus connector splits
# into a 1x39 base (bottom edge) + a 1x10 extension row 2.54 mm above it (D1.23/D1.4).
PLACE = {
    "J_BUS":  (50.0, 57.0), "J_EXT": (14.7, 54.46),
    "U1": (22.0, 24.0), "U2": (52.0, 24.0), "U3": (80.0, 24.0),
    "C1": (22.0, 10.0), "C2": (52.0, 10.0), "C3": (80.0, 10.0),
    "J_OBS": (88.0, 40.0), "J_NOP": (45.0, 44.0),
}


def main():
    board = pcbnew.BOARD()
    outline(board)

    # nets: one per board.json net name
    nets = {}
    for name in board_spec["nets"]:
        ni = pcbnew.NETINFO_ITEM(board, name)
        board.Add(ni); nets[name] = ni

    def add_fp(ref, fpname, xy, pin_to_net):
        fp = load_fp(fpname)
        board.Add(fp)
        fp.SetReference(ref)
        place(fp, *xy)
        for pad in fp.Pads():
            net = pin_to_net.get(str(pad.GetNumber()))
            if net and net in nets:
                pad.SetNet(nets[net])
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
            add_fp(ref, fpname, xy, pins)

    # silk: card banner + safety (pin-1 marks come from the footprints)
    silk(board, f"VJUGA REV B  {CARD.upper()} CARD", 50.0, 3.0, size=2.0)
    silk(board, "NO HOT-PLUG", 50.0, 51.0, size=1.4)
    silk(board, "BUS 1<-39   EXT E1<-E10", 50.0, 59.2, size=1.0)

    outdir = os.path.join(REPO, "fab", "minimal-vga", "revb")
    os.makedirs(outdir, exist_ok=True)
    outpath = os.path.join(outdir, f"{CARD}.kicad_pcb")
    board.Save(outpath)
    print(f"wrote {outpath} ({len(list(board.GetFootprints()))} footprints, {len(nets)} nets)")


if __name__ == "__main__":
    main()
