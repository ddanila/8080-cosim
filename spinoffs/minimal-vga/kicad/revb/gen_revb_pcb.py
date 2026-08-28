#!/usr/bin/env python3
"""Generate a rev B card PCB from its board.json (TD.7.2). Run with KiCad's python
(KICAD_PYTHON via env.sh). Reuses the pcbnew primitives proven in gen_rev_a_pcb.py:
footprint load, centre-place, Edge.Cuts outline, net assignment, silk. Deterministic
placement (no randomness); regeneration is content-checked, not byte-diffed (D1.25).

  KICAD_PYTHON gen_revb_pcb.py <card>   # writes fab/minimal-vga/revb/<card>.kicad_pcb
"""
import hashlib, json, os, shutil, subprocess, sys
import pcbnew
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from revb_place import BOARD_W, BOARD_H_BY_CARD, PLACE_BY_CARD  # noqa: E402
from revb_assembly import display_value, expanded_parts, marking_text  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))   # spinoffs/minimal-vga/kicad/revb
REPO = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
CARD = sys.argv[1] if len(sys.argv) > 1 else "mem"
FPROOT = os.environ["KICAD_FOOTPRINTS"]
MATING = json.load(open(os.path.join(HERE, "mating.json")))

# Card outlines: BOARD_W + per-card BOARD_H come from revb_place (shared with the
# mating checker). io is taller: more parts (D1.23).
BOARD_H = BOARD_H_BY_CARD.get(CARD, 60.0)

board_spec = json.load(open(os.path.join(HERE, f"{CARD}.board.json")))
fpmap = json.load(open(os.path.join(HERE, f"footprints.{CARD}.json")))

# KiCad outline text is intentionally used for all printable silk.  The exact face
# is a local generation dependency (not redistributed by this repository); the
# generated Gerbers contain polygons and therefore do not require the font at fab.
SILK_STYLE = json.load(open(os.path.join(HERE, "silkscreen-style.json")))
SILK_FONT = SILK_STYLE["font_family"]


def validate_silk_font():
    """Reject a Fontconfig fallback or another file with the same family name."""
    fc_match = shutil.which("fc-match")
    if not fc_match:
        raise RuntimeError("fc-match is required to verify the pinned GOST silk font")
    result = subprocess.run(
        [fc_match, "--format=%{family[0]}|%{style[0]}|%{file}\n", SILK_FONT],
        check=True, text=True, capture_output=True).stdout.strip()
    family, style, path = result.split("|", 2)
    if family != SILK_FONT:
        raise RuntimeError(f"silk font {SILK_FONT!r} resolved to fallback {family!r}")
    digest = hashlib.sha256(open(path, "rb").read()).hexdigest()
    if digest != SILK_STYLE["font_file_sha256"]:
        raise RuntimeError(
            f"silk font file {path} SHA-256 {digest} != pinned "
            f"{SILK_STYLE['font_file_sha256']}")
    if SILK_STYLE["font_style"] not in style.split(","):
        raise RuntimeError(f"silk font style {style!r} is not {SILK_STYLE['font_style']!r}")


def mm(v): return pcbnew.FromMM(v)


def load_fp(fpname):
    lib, name = fpname.split(":")
    root = HERE if lib == "VJUGA" else FPROOT
    fp = pcbnew.FootprintLoad(os.path.join(root, f"{lib}.pretty"), name)
    if fp is None:
        raise RuntimeError(f"missing footprint {fpname}")
    # JLCPCB may widen sub-0.15-mm silk during CAM. Emit that floor ourselves so
    # the checked preview, not an undocumented vendor edit, is the order intent.
    for item in fp.GraphicalItems():
        if item.GetLayer() not in (pcbnew.F_SilkS, pcbnew.B_SilkS):
            continue
        if isinstance(item, pcbnew.PCB_TEXT) and item.IsVisible():
            size = item.GetTextSize()
            item.SetTextSize(pcbnew.VECTOR2I(max(size.x, mm(1.5)),
                                             max(size.y, mm(1.5))))
            item.SetTextThickness(max(item.GetTextThickness(), mm(0.15)))
            item.SetFontProp(SILK_FONT)
        else:
            try:
                item.SetWidth(max(item.GetWidth(), mm(0.15)))
            except Exception:
                pass
    return fp


def place(fp, x, y, rot=0):
    # rotate first (changes the bounding box), then centre the bbox on (x, y).
    if rot:
        fp.SetOrientationDegrees(rot)
    fp.SetPosition(pcbnew.VECTOR2I(mm(x), mm(y)))
    c = fp.GetBoundingBox(False, False).GetCenter()
    fp.SetPosition(pcbnew.VECTOR2I(2 * mm(x) - c.x, 2 * mm(y) - c.y))


def place_pad_row(fp, x, y, rot=0):
    """Put the connector PAD-ROW centre, not its asymmetric body bbox, at (x,y).

    mating.json defines electrical/mating row coordinates. A right-angle card header's
    body sits wholly on one side of that row, so bbox-centering silently moves its pins
    by several millimetres and makes the abstract mating proof false.
    """
    if rot:
        fp.SetOrientationDegrees(rot)
    fp.SetPosition(pcbnew.VECTOR2I(mm(x), mm(y)))
    pads = [pad.GetPosition() for pad in fp.Pads() if str(pad.GetNumber()).isdigit()]
    if not pads:
        raise RuntimeError(f"{fp.GetReference()}: connector has no numeric pads")
    cx = (min(p.x for p in pads) + max(p.x for p in pads)) // 2
    cy = (min(p.y for p in pads) + max(p.y for p in pads)) // 2
    pos = fp.GetPosition()
    fp.SetPosition(pcbnew.VECTOR2I(pos.x + mm(x) - cx, pos.y + mm(y) - cy))


def place_vga_edge(fp, x, y, rot=180):
    """Place the exact NorComp origin, not its body centre.

    At 180 degrees, origin (45.428, 2.5) puts the drawing's PCB-edge line on
    board y=0, centres the 30.81-mm shell on x=50, leaves every solder tail
    inside the board, and projects the mating face 5.8 mm beyond the edge.
    """
    fp.SetOrientationDegrees(rot)
    fp.SetPosition(pcbnew.VECTOR2I(mm(x), mm(y)))


def place_origin(fp, x, y, rot=0):
    """Place a mechanical datum directly, without bounding-box centring.

    Edge connectors are dimensioned from their mating-face origin.  Treating that
    datum as a generic component centre moves the opening away from the board edge
    and makes an otherwise correct footprint mechanically inaccessible.
    """
    fp.SetOrientationDegrees(rot)
    fp.SetPosition(pcbnew.VECTOR2I(mm(x), mm(y)))


def strip_bus_edge_graphics(fp):
    """Remove generic library silk/courtyard around mating posts outside the PCB.

    The exact body/lead presentation is guarded by mating.json and the parts checker.
    KiCad's stock footprint encloses the full 6-mm mating post in a courtyard, which
    intentionally crosses the board edge and also treats the interleaved opposite-side
    connector as a component collision. Those are not useful assembly courtyards.
    """
    move = {
        pcbnew.F_SilkS: pcbnew.F_Fab, pcbnew.F_CrtYd: pcbnew.F_Fab,
        pcbnew.B_SilkS: pcbnew.B_Fab, pcbnew.B_CrtYd: pcbnew.B_Fab,
    }
    for item in list(fp.GraphicalItems()):
        if item.GetLayer() in move:
            item.SetLayer(move[item.GetLayer()])


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
        z.SetDoNotAllowPads(False)
        z.SetDoNotAllowFootprints(False)
        z.SetDoNotAllowZoneFills(False)
        z.SetLayerSet(pcbnew.LSET.AllCuMask(board.GetCopperLayerCount()))
        z.Outline().NewOutline()
        for px, py in ((x1, y1), (x2, y1), (x2, y2), (x1, y2)):
            z.Outline().Append(mm(px), mm(py))
        board.Add(z)


def emit_bus_columns(board):
    """D1.29 column-route: the configured base/ext connectors are stacked at the
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
    The power columns end at the final slot while the power-hungry tail lives in the top
    strip. Emit, per net: a locked riser from the final-slot column
    pad, a horizontal strip rail, and straight drops to specific tail pads (so nothing
    dangles). VCC5 on F.Cu and GND on B.Cu — different layers so
    their drops may cross. freerouting keeps only short local taps onto the rails,
    which it has always managed. Drop targets are pads reachable by a straight vertical
    (chosen to avoid other parts' pad columns); the rest tap the rail via freerouting."""
    last_bus = f"J_S{MATING['n_slots']}_BUS"
    last_ext = f"J_S{MATING['n_slots']}_EXT"
    tail_y = MATING["tail_strip_y0"]
    RAILS = {
        "VCC5": {"layer": pcbnew.F_Cu, "y": tail_y + 0.9,
                 "drops": {("J_PWR", "VCC5"), ("U_RST", "VCC5"), ("R_VSENSE", "VCC5"),
                           ("R_LED", "VCC5")}},
        "GND":  {"layer": pcbnew.B_Cu, "y": tail_y + 0.5,
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
                if ref == last_bus:
                    riser[nn] = pad
                elif ref == last_ext:
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
        # riser: final-slot pad straight up into the strip (THT pad joins both layers)
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
        # threading joins, so freerouting fails on exactly this). Rise from the final-slot
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


def emit_backplane_power_spines(board):
    """Emit the R5.V6 high-current path before autorouting.

    The base connector alone is rated for the complete 1.351-A desk budget, so a
    2.0-mm VCC_BUS spine and a 2.0-mm GND_BUS spine run directly through its power pads in
    all five slots.  VCC_BUS uses F.Cu and GND_BUS uses B.Cu, allowing ordinary bus signals
    to cross on the other layer.  The normal-input fuse and jack are tied directly to
    those spines with the same width; no thin autorouted segment is in the normal
    machine current path.  Extension-row power remains connected by the router as a
    redundant, non-credit path.
    """
    import re
    fps = {fp.GetReference(): fp for fp in board.GetFootprints()}

    def pad(ref, number):
        p = fps[ref].FindPadByNumber(str(number))
        if p is None:
            raise RuntimeError(f"{ref}: missing pad {number}")
        return p

    def add_track(net, layer, a, b, width=2.0):
        t = pcbnew.PCB_TRACK(board)
        t.SetStart(a); t.SetEnd(b); t.SetWidth(mm(width)); t.SetLayer(layer)
        t.SetNet(net); t.SetLocked(True); board.Add(t)
        return t

    slot_refs = sorted((r for r in fps if re.fullmatch(r"J_S\d+_BUS", r)),
                       key=lambda r: int(re.search(r"\d+", r).group()))
    if len(slot_refs) != MATING["n_slots"]:
        raise RuntimeError("cannot emit power spines: slot connector set incomplete")

    specs = {
        "VCC_BUS": (pcbnew.F_Cu, "F_MAIN", "2"),
        "GND_BUS": (pcbnew.B_Cu, "J_PWR", "2"),
    }
    count = 0
    for netname, (layer, source_ref, source_padno) in specs.items():
        power_pads = []
        for ref in slot_refs:
            matches = [p for p in fps[ref].Pads() if p.GetNetname() == netname]
            if len(matches) != 1:
                raise RuntimeError(f"{ref}: expected one {netname} pad, got {len(matches)}")
            power_pads.append(matches[0])
        power_pads.sort(key=lambda p: p.GetPosition().y)
        net = power_pads[0].GetNet()
        for a, b in zip(power_pads, power_pads[1:]):
            add_track(net, layer, a.GetPosition(), b.GetPosition()); count += 1

        source = pad(source_ref, source_padno)
        top = power_pads[-1].GetPosition()
        if netname == "GND_BUS":
            # The jack's wide centre-contact and the vertical main fuse sit above
            # this row.  A short B.Cu dogleg at y=95 avoids both PTH envelopes before
            # joining the dedicated GND column.
            clear_y = mm(95.0)
            a = pcbnew.VECTOR2I(source.GetPosition().x, clear_y)
            corner = pcbnew.VECTOR2I(top.x, clear_y)
            add_track(net, layer, source.GetPosition(), a); count += 1
            add_track(net, layer, a, corner); count += 1
            add_track(net, layer, corner, top); count += 1
        else:
            # Orthogonal source feed: first align X at the source Y, then descend
            # along the exact slot-power column.
            corner = pcbnew.VECTOR2I(top.x, source.GetPosition().y)
            if source.GetPosition() != corner:
                add_track(net, layer, source.GetPosition(), corner); count += 1
            add_track(net, layer, corner, top); count += 1

    return count


def emit_raw_input(board):
    """Lock the sole, short 2-mm barrel-to-fuse path before autorouting.

    Widening a 0.8-mm autorouted candidate after import can create a signal short
    which the router never saw.  This two-segment path has no bus-column interaction,
    so unlike the retired column pre-routes it survives the Specctra round trip and
    gives FreeRouting the true copper obstacle.
    """
    fps = {fp.GetReference(): fp for fp in board.GetFootprints()}
    raw_a = fps["J_PWR"].FindPadByNumber("1")
    raw_b = fps["F_MAIN"].FindPadByNumber("1")
    corner = pcbnew.VECTOR2I(raw_b.GetPosition().x, raw_a.GetPosition().y)
    for start, end in ((raw_a.GetPosition(), corner), (corner, raw_b.GetPosition())):
        track = pcbnew.PCB_TRACK(board)
        track.SetStart(start)
        track.SetEnd(end)
        track.SetWidth(mm(2.0))
        track.SetLayer(pcbnew.F_Cu)
        track.SetNet(raw_a.GetNet())
        track.SetLocked(True)
        board.Add(track)
    return 2


def emit_video_vga_escapes(board):
    """Route the two trapped inner VGA tails through the exact 7+8 pad fanout.

    A 0.15-mm neck with 0.15-mm local pad clearance fits the 1.524-mm same-row
    pitch and 1.00-mm pads with 0.037 mm geometric margin per side. Once clear
    of the connector, the deterministic tracks run in open B.Cu channels; all
    remaining router-generated signals retain the ordinary 0.20-mm floor.
    """
    fps = {fp.GetReference(): fp for fp in board.GetFootprints()}

    def pad(ref, number):
        found = fps[ref].FindPadByNumber(str(number))
        if found is None:
            raise RuntimeError(f"missing escape endpoint {ref}.{number}")
        return found

    def polyline(net, points):
        for start, end in zip(points, points[1:]):
            track = pcbnew.PCB_TRACK(board)
            track.SetStart(pcbnew.VECTOR2I(mm(start[0]), mm(start[1])))
            track.SetEnd(pcbnew.VECTOR2I(mm(end[0]), mm(end[1])))
            track.SetWidth(mm(0.15))
            track.SetLayer(pcbnew.B_Cu)
            track.SetNet(net)
            track.SetLocked(True)
            board.Add(track)

    vg = pad("J_VGA", 2)
    vg_end = pad("R_VG", 2)
    polyline(vg.GetNet(), [
        (pcbnew.ToMM(vg.GetPosition().x), pcbnew.ToMM(vg.GetPosition().y)),
        (47.714, 5.5), (57.0, 5.5), (57.0, 17.2),
        (pcbnew.ToMM(vg_end.GetPosition().x), pcbnew.ToMM(vg_end.GetPosition().y)),
    ])
    hs = pad("J_VGA", 13)
    hs_end = pad("U5", 15)
    polyline(hs.GetNet(), [
        (pcbnew.ToMM(hs.GetPosition().x), pcbnew.ToMM(hs.GetPosition().y)),
        (50.762, 4.5), (91.89, 4.5),
        (pcbnew.ToMM(hs_end.GetPosition().x), pcbnew.ToMM(hs_end.GetPosition().y)),
    ])


def emit_video_local_strap(board):
    """Emit the exact adjacent U22 V_END tie under the socket.

    A clean-source R5.J2 run showed that leaving this trivial 2.54-mm connection
    stochastic lets FreeRouting consume the channel with HC1 and return one ratline.
    The previously released DRC-clean route used this same direct F.Cu segment.
    """
    fp = next(item for item in board.GetFootprints() if item.GetReference() == "U22")
    a, b = fp.FindPadByNumber("9"), fp.FindPadByNumber("10")
    if a.GetNetname() != "V_END" or b.GetNetname() != "V_END":
        raise RuntimeError("U22 local V_END strap pin contract changed")
    track = pcbnew.PCB_TRACK(board)
    track.SetStart(a.GetPosition())
    track.SetEnd(b.GetPosition())
    track.SetWidth(mm(0.20))
    track.SetLayer(pcbnew.F_Cu)
    track.SetNet(a.GetNet())
    track.SetLocked(True)
    board.Add(track)


def silk(board, text, x, y, size=1.5, angle=0, layer=pcbnew.F_SilkS,
         thickness=0.2):
    t = pcbnew.PCB_TEXT(board); t.SetLayer(layer); t.SetText(text)
    t.SetTextPos(pcbnew.VECTOR2I(mm(x), mm(y))); t.SetTextAngleDegrees(angle)
    t.SetTextSize(pcbnew.VECTOR2I(mm(size), mm(size))); t.SetTextThickness(mm(thickness))
    t.SetFontProp(SILK_FONT)
    if layer == pcbnew.B_SilkS:
        t.SetMirrored(True)
    board.Add(t)
    return t


def emit_assembly_markings(board, parts):
    """Put a reference plus fitted value/role beside every physical footprint.

    Long IC/connector markings are split over lines and aligned with the package's
    long axis.  DIP and axial-body labels use the pad-free package interior; small
    radial/vertical parts use the first pad- and text-clear position around their
    footprint.  Back-side parts receive B.Silkscreen text on their assembly side.
    """
    footprints = {fp.GetReference(): fp for fp in board.GetFootprints()}

    def bounds(item):
        box = item.GetBoundingBox()
        pos, size = box.GetPosition(), box.GetSize()
        return pos.x, pos.y, pos.x + size.x, pos.y + size.y

    def overlaps(a, b, gap_mm=0.20):
        gap = mm(gap_mm)
        return not (a[2] + gap <= b[0] or b[2] + gap <= a[0]
                    or a[3] + gap <= b[1] or b[3] + gap <= a[1])

    def in_board(box):
        inset = mm(0.8)
        return (box[0] >= inset and box[1] >= inset
                and box[2] <= mm(BOARD_W) - inset
                and box[3] <= mm(BOARD_H) - inset)

    placed = [item for item in board.GetDrawings()
              if isinstance(item, pcbnew.PCB_TEXT) and item.IsVisible()
              and item.GetLayer() in (pcbnew.F_SilkS, pcbnew.B_SilkS)]
    graphic_obstacles = [item for fp in board.GetFootprints()
                         for item in fp.GraphicalItems()
                         if not isinstance(item, pcbnew.PCB_TEXT)
                         and item.GetLayer() in (pcbnew.F_SilkS, pcbnew.B_SilkS)]

    # Larger bodies first; their natural interiors are the least ambiguous homes.
    ordered = sorted(parts, key=lambda ref: (
        0 if ref.startswith("U") else 1,
        -footprints[ref].GetBoundingBox(False, False).GetArea(), ref))
    for ref in ordered:
        fp, part = footprints[ref], parts[ref]
        fp.SetValue(display_value(ref, part))
        layer = pcbnew.B_SilkS if fp.GetLayer() == pcbnew.B_Cu else pcbnew.F_SilkS
        typ = part["type"]
        body_centre = (ref.startswith("U") and ref != "U_RST") or (
            ref.startswith(("R", "W")) and not typ.endswith("_VERT"))
        multiline = ((not body_centre and ref.startswith(("J", "JP")))
                     or (not body_centre and len(marking_text(ref, part)) > 13))
        label = marking_text(ref, part, multiline=multiline)
        box = fp.GetBoundingBox(False, False)
        centre = box.GetCenter()
        long_angle = 0 if box.GetWidth() >= box.GetHeight() else 90
        text = silk(board, label, pcbnew.ToMM(centre.x), pcbnew.ToMM(centre.y),
                    size=SILK_STYLE["assembly_text_height_mm"],
                    angle=long_angle if body_centre else 0, layer=layer,
                    thickness=SILK_STYLE["assembly_text_thickness_mm"])

        candidates = [(centre.x, centre.y, long_angle)] if body_centre else []
        # Re-evaluate text dimensions after each angle; positions use the
        # component bbox plus the candidate text's actual rendered extent. A
        # bounded near-part grid gives dense Video/Backplane labels several clean
        # alternatives without turning the board into a remote legend table.
        for angle in (0, 90):
            text.SetTextAngleDegrees(angle)
            tb = text.GetBoundingBox()
            tw, th = tb.GetWidth(), tb.GetHeight()
            margin = mm(0.5)
            candidates.extend([
                (centre.x, box.GetY() - th // 2 - margin, angle),
                (centre.x, box.GetBottom() + th // 2 + margin, angle),
                (box.GetX() - tw // 2 - margin, centre.y, angle),
                (box.GetRight() + tw // 2 + margin, centre.y, angle),
            ])
            for radius_mm in (3.0, 5.0, 7.0, 9.0, 12.0, 15.0):
                radius = mm(radius_mm)
                for dx, dy in ((-radius, -radius), (0, -radius), (radius, -radius),
                               (-radius, 0), (radius, 0),
                               (-radius, radius), (0, radius), (radius, radius)):
                    candidates.append((centre.x + dx, centre.y + dy, angle))
            # Last resort remains on the component side and DRC-clean: search the
            # complete board in nearest-first order. This is mainly needed by the
            # densely populated Backplane service strip. The review render makes
            # any association that became too remote a human finding, not a hidden
            # fabrication compromise.
            grid = [(mm(x), mm(y)) for y in range(3, int(BOARD_H) - 2, 2)
                    for x in range(3, int(BOARD_W) - 2, 2)]
            grid.sort(key=lambda point: (abs(point[0] - centre.x)
                                         + abs(point[1] - centre.y),
                                         point[1], point[0]))
            candidates.extend((x, y, angle) for x, y in grid)

        selected = None
        for x, y, angle in candidates:
            text.SetTextAngleDegrees(angle)
            text.SetTextPos(pcbnew.VECTOR2I(x, y))
            text_box = bounds(text)
            if not in_board(text_box):
                continue
            copper_layer = pcbnew.B_Cu if layer == pcbnew.B_SilkS else pcbnew.F_Cu
            if any(pad.IsOnLayer(copper_layer) and overlaps(text_box, bounds(pad), 0.15)
                   for other in board.GetFootprints() for pad in other.Pads()):
                continue
            if any(other.GetLayer() == layer and overlaps(text_box, bounds(other), 0.15)
                   for other in placed):
                continue
            if any(other.GetLayer() == layer and overlaps(text_box, bounds(other), 0.15)
                   for other in graphic_obstacles):
                continue
            selected = (x, y, angle)
            break

        if selected is None:
            # Keep the deterministic preferred location. Total DRC and the render
            # review must reject it if the fallback is not fabrication-safe.
            selected = candidates[0]
        text.SetTextAngleDegrees(selected[2])
        text.SetTextPos(pcbnew.VECTOR2I(selected[0], selected[1]))
        placed.append(text)


def add_power_zone(board, net, layer, name):
    """Continuous inner-layer power plane, inset only past the edge guard."""
    inset = 0.8
    zone = pcbnew.ZONE(board)
    zone.SetLayer(layer)
    zone.SetNet(net)
    zone.SetZoneName(name)
    zone.SetPadConnection(pcbnew.ZONE_CONNECTION_FULL)
    zone.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_ALWAYS)
    for x, y in ((inset, inset), (BOARD_W - inset, inset),
                 (BOARD_W - inset, BOARD_H - inset), (inset, BOARD_H - inset)):
        zone.AppendCorner(pcbnew.VECTOR2I(mm(x), mm(y)), -1)
    board.Add(zone)


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
    validate_silk_font()
    board = pcbnew.BOARD()
    if CARD == "video":
        board.SetCopperLayerCount(4)
        board.GetDesignSettings().SetCopperLayerCount(4)
        # The exact NorComp board-lock holes are tangent to the specified PCB edge;
        # ordinary routed copper still stays behind the explicit 0.6-mm edge ring.
        board.GetDesignSettings().m_CopperEdgeClearance = mm(0.30)
        board.GetDesignSettings().m_TrackMinWidth = mm(0.15)
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

    def add_fp(ref, fpname, xy, pin_to_net, dnp=False, pad_row_anchor=False,
               vga_edge_anchor=False, origin_anchor=False, back_side=False):
        fp = load_fp(fpname)
        board.Add(fp)
        fp.SetReference(ref)
        if back_side:
            fp.Flip(fp.GetPosition(), False)
        (place_vga_edge if vga_edge_anchor else
         place_origin if origin_anchor else
         place_pad_row if pad_row_anchor else place)(fp, *xy)
        if dnp:
            try: fp.SetDNP(True)
            except Exception: pass
        for pad in fp.Pads():
            net = pin_to_net.get(str(pad.GetNumber()))
            if net and net in nets:
                pad.SetNet(nets[net])
                if ref == "J_VGA" and net == "GND":
                    pad.SetLocalZoneConnection(pcbnew.ZONE_CONNECTION_FULL)
            if ref == "J_VGA" and str(pad.GetNumber()).isdigit():
                pad.SetLocalClearance(mm(0.15))
        if ref == "J_VGA":
            # The footprint's explicit pin-1 numeral is useful, but enlarging it to
            # the GOST fabrication floor at its library location overlaps pad 1.
            for item in fp.GraphicalItems():
                if (isinstance(item, pcbnew.PCB_TEXT) and item.IsVisible()
                        and item.GetText() == "1"):
                    item.SetTextPos(pcbnew.VECTOR2I(mm(45.428), mm(5.0)))
            if ref == "U_RST" and pad.HasHole():
                # DS1813's exact inline TO-92 pitch is only 1.27 mm. Increase the
                # stock footprint from 0.15 to JLCPCB's 0.18-mm 2-layer absolute ring;
                # the recommended 0.25-mm ring cannot fit that exact pitch. Production
                # confirmation is mandatory for this explicitly audited exception.
                size, drill = pad.GetSize(), pad.GetDrillSize()
                pad.SetSize(pcbnew.VECTOR2I(
                    max(size.x, drill.x + mm(0.36)),
                    max(size.y, drill.y + mm(0.36))))
                pad.SetLocalClearance(mm(0.15))
        # Hide library placeholder ref/value fields: their footprint-relative
        # positions stray onto pads and outlines after rotation. The deterministic
        # board-level assembly pass below replaces them with checked ref+value text.
        fp.Value().SetVisible(False)
        fp.Reference().SetVisible(False)
        return fp

    for comp in board_spec["chips"]:
        ref, typ, pins = comp["ref"], comp["type"], comp["pins"]
        if typ == "REVB_BUS_39_10":
            base_fp, ext_fp = fpmap[typ]
            base = {p: n for p, n in pins.items() if p.isdigit()}
            ext = {p[1:]: n for p, n in pins.items() if p.startswith("E")}  # E1->pad 1
            # Single-card bus keeps the J_BUS/J_EXT names; the backplane slots derive
            # per-slot refs so each connector is uniquely named
            # and its pins align in vertical columns (D1.29 column-route prerequisite).
            bref = "J_BUS" if ref == "J_BUS" else f"{ref}_BUS"
            eref = "J_EXT" if ref == "J_BUS" else f"{ref}_EXT"
            bfp = add_fp(bref, base_fp, PLACE[bref], base, pad_row_anchor=True)
            efp = add_fp(eref, ext_fp, PLACE[eref], ext, pad_row_anchor=True,
                         back_side=(CARD != "backplane"))
            if CARD != "backplane":
                strip_bus_edge_graphics(bfp)
                strip_bus_edge_graphics(efp)
        else:
            fpname = fpmap.get(typ) or fpmap.get(f"HDR_1x{len(pins)}")
            xy = PLACE.get(ref, (50.0, 40.0))
            add_fp(ref, fpname, xy, pins, dnp=comp.get("dnp", False),
                   vga_edge_anchor=(CARD == "video" and ref == "J_VGA"),
                   origin_anchor=(CARD == "backplane" and ref == "J_PWR"),
                   # These small through-hole decouplers occupy the clear space
                   # between socket rows on B.Cu. That keeps their VCC legs local
                   # without consuming the dense front-side signal channels.
                   back_side=(CARD == "video" and ref in {
                       "C5", "C7", "C8", "C9", "C10", "C11", "C21"}))

    if CARD == "video":
        # KiCad's PTH courtyard test has no opposite-face body model: it reports
        # every B-side capacitor deliberately placed between a front-side socket's
        # rows as a collision. Retire only those seven front courtyards; the V5
        # physical checker instead proves side, capacitor-to-pad clearance and
        # local VCC distance for each explicit U/C pair.
        for ref in ("U5", "U7", "U8", "U9", "U10", "U11", "U21"):
            for item in list(next(fp for fp in board.GetFootprints()
                                  if fp.GetReference() == ref).GraphicalItems()):
                if item.GetLayer() == pcbnew.F_CrtYd:
                    item.SetLayer(pcbnew.F_Fab)
    # Board-level silk uses one visual grammar on all five designs. Safety and
    # interface labels remain conspicuous; the complete ref+value assembly legend
    # is emitted separately below from assembly-markings.json.
    SILK = {
        "mem": [(SILK_STYLE["titles"]["mem"], 59.0, 52.0, 1.8),
                (SILK_STYLE["common_safety_text"], 89.0, 49.0, 1.5)],
        "io":  [(SILK_STYLE["titles"]["io"], 40.0, 30.0, 1.8),
                (SILK_STYLE["common_safety_text"], 40.0, 58.0, 1.5)],
        "cpu": [(SILK_STYLE["titles"]["cpu"], 68.0, 46.0, 1.8),
                (SILK_STYLE["common_safety_text"], 68.0, 53.0, 1.5)],
        "video": [(SILK_STYLE["titles"]["video"], 34.0, 87.0, 1.8),
                  ("4 LAYER", 34.0, 91.0, 1.5),
                  (SILK_STYLE["common_safety_text"], 76.0, 87.0, 1.5)],
        # Backplane console labels are board-relative: TX is output from VJUGA,
        # RX is input to VJUGA. The electrical boundary is TTL, never RS-232.
        "backplane": [(SILK_STYLE["titles"]["backplane"], 50.0, 68.0, 1.8),
                      (SILK_STYLE["common_safety_text"], 82.0, 68.0, 1.5),
                      ("SLOT 1", 35.0, 15.0, 1.5),
                      ("SLOT 2", 35.0, 31.0, 1.5),
                      ("SLOT 3", 35.0, 47.0, 1.5),
                      ("SLOT 4 - KEEP EMPTY", 44.0, 63.0, 1.5),
                      ("SLOT 5 - VIDEO", 40.0, 79.0, 1.5),
                      ("TTL ONLY", 97.0, 50.0, 1.5, 90),
                      ("NOT RS-232", 93.5, 50.0, 1.5, 90),
                      ("1:5V SENSE", 51.0, 78.2, 1.5),
                      ("2:TX 3:RX 4:GND", 70.0, 78.2, 1.5)],
    }
    for entry in SILK.get(CARD, SILK["mem"]):
        text, sx, sy, ssz, *rest = entry
        silk(board, text, sx, sy, size=ssz, angle=(rest[0] if rest else 0))

    # Card connectors are symmetric enough to permit a dangerous reverse insertion.
    # Put the pad-1 cue on both faces; bottom text is mirrored so it reads correctly
    # when the board is viewed from that side.
    if CARD != "backplane":
        silk(board, "PIN 1 >", 91.5, BOARD_H - 9.0, size=1.5)
        # Viewed from the bottom, physical X is reversed and pad 1 is to the left.
        silk(board, "< PIN 1", 91.5, BOARD_H - 9.0, size=1.5,
              layer=pcbnew.B_SilkS)

    # Assembly contract: every one of the 131 physical footprints has exactly one
    # ref+value/role marking on the same face as the fitted component. DNP markings
    # are part of the same label so an optional footprint cannot be populated by
    # mistake during the first-system build.
    emit_assembly_markings(board, expanded_parts(board_spec))

    # D1.34: the backplane bus routes like any other card — plain freerouting, no
    # locked bus-column pre-routes. The Stage-C column pre-routing (D1.29) was retired when the layout
    # became mate-compatible: pcbnew's specctra roundtrip mangles locked tracks near
    # the base/ext interleave (drops a varying subset), freerouting then reliably fails
    # around the corpse (170+ attempts), while the SAME board with no locked tracks
    # routes 0/0 on attempt 1. REVB_COLUMNS=1 re-enables the emitters for comparison.
    # Direct locked spines remain a diagnostic comparison only.  The Specctra
    # round trip can preserve their geometry yet leave FreeRouting with a stable
    # seven-net dead end.  The release flow instead assigns these nets a 0.8-mm
    # routing class in route_revb_pcb.sh, which lets the router negotiate crossings.
    # R5.J1 keeps only the isolated two-segment PWR_RAW path deterministic so the
    # router sees its final 2.0-mm obstacle instead of having it widened afterward.
    if CARD == "backplane":
        emit_raw_input(board)

    if CARD == "backplane" and os.environ.get("REVB_POWER_SPINES") == "1":
        npwr = emit_backplane_power_spines(board)
        print(f"  emitted {npwr} locked 2.0-mm normal-input/power-spine segments")

    if CARD == "backplane" and os.environ.get("REVB_COLUMNS"):
        ncol = emit_bus_columns(board)
        nris = emit_power_rails(board)
        print(f"  emitted {ncol} bus-column segments + {nris} power-rail segments (locked)")

    if CARD == "video":
        emit_video_local_strap(board)
        emit_video_vga_escapes(board)

    if CARD == "video" and os.environ.get("REVB_NO_ZONES") != "1":
        add_power_zone(board, nets["GND"], pcbnew.In1_Cu, "VJUGA rev B Video GND plane")
        add_power_zone(board, nets["VCC5"], pcbnew.In2_Cu, "VJUGA rev B Video VCC5 plane")

    requested_out = os.environ.get("REVB_OUTPUT")
    outdir = (os.path.dirname(os.path.abspath(requested_out)) if requested_out else
              os.path.join(REPO, "fab", "minimal-vga", "revb"))
    os.makedirs(outdir, exist_ok=True)
    outpath = (os.path.abspath(requested_out) if requested_out else
               os.path.join(outdir, f"{CARD}.kicad_pcb"))
    if not outpath.endswith(".kicad_pcb"):
        raise RuntimeError("REVB_OUTPUT must name a .kicad_pcb file")
    board.Save(outpath)
    if board.Zones():
        pcbnew.ZONE_FILLER(board).Fill(board.Zones())
        board.Save(outpath)
    print(f"wrote {outpath} ({len(list(board.GetFootprints()))} footprints, {len(nets)} nets)")


if __name__ == "__main__":
    main()
