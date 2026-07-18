#!/usr/bin/env python3
"""Generate a rev B card PCB from its board.json (TD.7.2). Run with KiCad's python
(KICAD_PYTHON via env.sh). Reuses the pcbnew primitives proven in gen_rev_a_pcb.py:
footprint load, centre-place, Edge.Cuts outline, net assignment, silk. Deterministic
placement (no randomness); regeneration is content-checked, not byte-diffed (D1.25).

  KICAD_PYTHON gen_revb_pcb.py <card>   # writes fab/minimal-vga/revb/<card>.kicad_pcb
"""
import json, os, sys
import pcbnew
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from revb_place import BOARD_W, BOARD_H_BY_CARD, PLACE_BY_CARD  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))   # spinoffs/minimal-vga/kicad/revb
REPO = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
CARD = sys.argv[1] if len(sys.argv) > 1 else "mem"
FPROOT = os.environ["KICAD_FOOTPRINTS"]

# Card outlines: BOARD_W + per-card BOARD_H come from revb_place (shared with the
# mating checker). io is taller: more parts (D1.23).
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


def edge_keepout(board):
    """No-track/no-via rule-area ring just inside the board outline. freerouting has no
    notion of KiCad's copper-to-edge clearance rule (0.5 mm) and repeatedly routed tracks
    0.4-0.6 mm from the edge (mem A11, the backplane corner via). The ring is exported to
    the DSN as a keepout, so freerouting simply can't go there. 0.6 mm ring = 0.5 mm rule
    + margin; no pads sit that close to an edge on any rev B board."""
    m = 0.6
    for x1, y1, x2, y2 in ((0, 0, BOARD_W, m), (0, BOARD_H - m, BOARD_W, BOARD_H),
                           (0, 0, m, BOARD_H), (BOARD_W - m, 0, BOARD_W, BOARD_H)):
        z = pcbnew.ZONE(board)
        z.SetIsRuleArea(True)
        z.SetDoNotAllowTracks(True)
        z.SetDoNotAllowVias(True)
        z.SetLayerSet(pcbnew.LSET.AllCuMask(2))
        z.Outline().NewOutline()
        for px, py in ((x1, y1), (x2, y1), (x2, y2), (x1, y2)):
            z.Outline().Append(mm(px), mm(py))
        board.Add(z)


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
    # Base columns on F.Cu, ext columns on B.Cu. Both are DRC-clean when emitted directly
    # here, even though mate-compatibility forces the ext row to x=14.45 inside the base
    # span (the two column grids interleave ~1.27 mm apart — fine for KiCad DRC). Note the
    # specctra DSN roundtrip silently DROPS the threading tracks (D1.33): freerouting then
    # re-routes those + the tail from the ratsnest. Pullups are placed on their columns so
    # freerouting's remaining job is short taps.
    for suffix, layer in (("BUS", pcbnew.F_Cu), ("EXT", pcbnew.B_Cu)):
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
                t.SetWidth(mm(0.3)); t.SetLayer(layer)
                net = a.GetNet()
                if net is not None:
                    t.SetNet(net)
                t.SetLocked(True)
                board.Add(t); n += 1
    return n


def emit_power_rails(board):
    """Backplane deterministic power distribution (D1.33 fallback, minimally scoped).
    The power columns end at slot 6 (y=90) while the power-hungry tail lives in the top
    strip (y>98); freerouting reliably fails to bridge that gap (130+ attempts, best 1
    unconnected — always power). Emit, per net: a locked riser from the slot-6 column
    pad, a horizontal strip rail, and straight drops to specific tail pads (so nothing
    dangles). VCC5 on F.Cu at y=101.5, GND on B.Cu at y=100.5 — different layers so
    their drops may cross. freerouting keeps only short local taps onto the rails,
    which it has always managed. Drop targets are pads reachable by a straight vertical
    (chosen to avoid other parts' pad columns); the rest tap the rail via freerouting."""
    RAILS = {
        "VCC5": {"layer": pcbnew.F_Cu, "y": 100.9,   # 101.5 grazed J_FTDI pad 2 (0.18 mm)
                 "drops": {("J_PWR", "VCC5"), ("U_RST", "VCC5"), ("J_FTDI", "VCC5"),
                           ("R_LED", "VCC5")}},
        "GND":  {"layer": pcbnew.B_Cu, "y": 100.5,
                 "drops": {("U_RST", "GND"), ("SW_RST", "GND")}},
    }
    pads_by_ref = {}
    riser, ext_pad = {}, {}
    for fp in board.GetFootprints():
        ref = fp.GetReference()
        for pad in fp.Pads():
            nn = pad.GetNetname()
            if nn in RAILS:
                pads_by_ref.setdefault((ref, nn), []).append(pad)
                if ref == "J_S6_BUS":
                    riser[nn] = pad
                elif ref == "J_S6_EXT":
                    ext_pad[nn] = pad

    def track(net, layer, x1, y1, x2, y2, w=0.5):
        t = pcbnew.PCB_TRACK(board)
        t.SetStart(pcbnew.VECTOR2I(mm(x1), mm(y1)))
        t.SetEnd(pcbnew.VECTOR2I(mm(x2), mm(y2)))
        t.SetWidth(mm(w)); t.SetLayer(layer)
        t.SetNet(net); t.SetLocked(True)
        board.Add(t)

    n = 0
    for netname, spec in RAILS.items():
        rp = riser.get(netname)
        if rp is None:
            continue
        net, ly, ry = rp.GetNet(), spec["layer"], spec["y"]
        rx = pcbnew.ToMM(rp.GetPosition().x)
        # riser: slot-6 pad straight up into the strip (THT pad joins both layers)
        track(net, ly, rx, pcbnew.ToMM(rp.GetPosition().y), rx, ry); n += 1
        # drops to the allow-listed pads
        xs = [rx]
        for key in spec["drops"]:
            for pad in pads_by_ref.get(key, []):
                px = pcbnew.ToMM(pad.GetPosition().x)
                py = pcbnew.ToMM(pad.GetPosition().y)
                track(net, ly, px, ry, px, py); n += 1
                xs.append(px)
        # ext-bank power column join (D1.33): the ext connector carries VCC5/GND too,
        # and its B.Cu columns are otherwise isolated (the DSN drops the interleave-
        # threading joins, so freerouting fails on exactly this). Rise from the slot-6
        # ext pad to the rail; via across if the rail is on the other layer.
        ep = ext_pad.get(netname)
        if ep is not None:
            ex = pcbnew.ToMM(ep.GetPosition().x)
            track(net, pcbnew.B_Cu, ex, pcbnew.ToMM(ep.GetPosition().y), ex, ry); n += 1
            if ly != pcbnew.B_Cu:
                v = pcbnew.PCB_VIA(board)
                v.SetPosition(pcbnew.VECTOR2I(mm(ex), mm(ry)))
                v.SetDrill(mm(0.4)); v.SetWidth(mm(0.8))
                v.SetNet(net); v.SetLocked(True)
                board.Add(v)
            xs.append(ex)
        # one rail spanning riser + drops + ext join
        track(net, ly, min(xs), ry, max(xs), ry); n += 1
    return n


def silk(board, text, x, y, size=1.5, angle=0):
    t = pcbnew.PCB_TEXT(board); t.SetLayer(pcbnew.F_SilkS); t.SetText(text)
    t.SetTextPos(pcbnew.VECTOR2I(mm(x), mm(y))); t.SetTextAngleDegrees(angle)
    t.SetTextSize(pcbnew.VECTOR2I(mm(size), mm(size))); t.SetTextThickness(mm(0.2))
    board.Add(t)


# Placement tables (PLACE_BY_CARD) come from revb_place (shared with the mating
# checker). Copy so the sweep hook below can mutate one card without side effects.
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
    # Edge no-track ring on every board. It used to break the backplane, but that was a
    # ring x locked-column interaction; with the columns retired (D1.34) the backplane
    # freeroutes cleanly and needs the ring too (freerouting kept hugging its edge).
    edge_keepout(board)

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
            # Map logical power pins to the GCT USB4085 THT receptacle's pads (full USB-C
            # pinout): VBUS=A4/A9/B4/B9, GND=A1/A12/B1/B12 + shield, CC1=A5, CC2=B5. The
            # data/SBU pins (A6-A8/B6-B8) are intentionally unused on a power-only sink.
            v, g = pins["VBUS"], pins["GND"]
            padnet = {"A4": v, "A9": v, "B4": v, "B9": v,
                      "A1": g, "A12": g, "B1": g, "B12": g, "SH": g,
                      "A5": pins["CC1"], "B5": pins["CC2"]}
            usb = add_fp(ref, fpmap[typ], PLACE.get(ref, (50.0, 40.0)), padnet)
            # USB-C is 0.85 mm pitch -> 0.15 mm inter-pad copper gaps, inherent to the
            # standard (VBUS/GND are always adjacent) and fine for any cheap fab, but
            # below KiCad's 0.2 mm default. Relax clearance for THIS connector only so it
            # doesn't force the whole board to 6-mil rules (order-readiness notes the
            # 0.15 mm fab requirement at the connector).
            try:
                usb.SetLocalClearance(mm(0.1))
                for pad in usb.Pads():
                    pad.SetLocalClearance(mm(0.1))
            except Exception:
                pass
        else:
            fpname = fpmap.get(typ) or fpmap.get(f"HDR_1x{len(pins)}")
            xy = PLACE.get(ref, (50.0, 40.0))
            add_fp(ref, fpname, xy, pins, dnp=comp.get("dnp", False))

    # board-level silk placed in clear gaps (pin-1 marks come from the footprints).
    SILK = {
        "mem": [(f"REVB {CARD.upper()}", 60.0, 49.0, 1.3), ("NO HOT-PLUG", 89.0, 49.0, 1.2)],
        "io":  [(f"REVB {CARD.upper()}", 40.0, 30.0, 1.3), ("NO HOT-PLUG", 40.0, 58.0, 1.1)],
        "cpu": [(f"REVB {CARD.upper()}", 68.0, 46.0, 1.4), ("NO HOT-PLUG", 68.0, 53.0, 1.2)],
        # backplane: one short label in the thin clear band between the top ext row
        # (y<=96.7) and the connector tail row (y>=99.5); strips are otherwise full.
        "backplane": [("REVB BACKPLANE", 45.0, 98.0, 1.0)],
    }
    for text, sx, sy, ssz in SILK.get(CARD, SILK["mem"]):
        silk(board, text, sx, sy, size=ssz)

    # backplane bus columns are emitted deterministically (D1.29); other cards route
    # entirely via freerouting.
    # D1.34: the backplane routes like any other card — plain freerouting, no locked
    # pre-routes. The Stage-C column pre-routing (D1.29) was retired when the layout
    # became mate-compatible: pcbnew's specctra roundtrip mangles locked tracks near
    # the base/ext interleave (drops a varying subset), freerouting then reliably fails
    # around the corpse (170+ attempts), while the SAME board with no locked tracks
    # routes 0/0 on attempt 1. REVB_COLUMNS=1 re-enables the emitters for comparison.
    if CARD == "backplane" and os.environ.get("REVB_COLUMNS"):
        ncol = emit_bus_columns(board)
        nris = emit_power_rails(board)
        print(f"  emitted {ncol} bus-column segments + {nris} power-rail segments (locked)")

    outdir = os.path.join(REPO, "fab", "minimal-vga", "revb")
    os.makedirs(outdir, exist_ok=True)
    outpath = os.path.join(outdir, f"{CARD}.kicad_pcb")
    board.Save(outpath)
    print(f"wrote {outpath} ({len(list(board.GetFootprints()))} footprints, {len(nets)} nets)")


if __name__ == "__main__":
    main()
