#!/usr/bin/env python3
# Phase B: generate a KiCad PCB (.kicad_pcb) from the LVS-verified board spec.
# Uses KiCad's own pcbnew API (run with KiCad's bundled python3) so the file is
# always format-valid. Loads a real DIP footprint per chip, assigns every net to
# its pads, lays chips out by functional group, and draws a board outline. The
# result is a placed board with the full ratsnest (all nets connected) -- ready
# for placement refinement (vs the assembly drawing) + routing.
#
# Run (KiCad python):
#   $KICAD/Contents/Frameworks/Python.framework/Versions/Current/bin/python3 \
#       kicad/gen_kicad_pcb.py kicad/juku.board.json kicad/juku.kicad_pcb
import sys, json, pcbnew

DIP_LIB = ("/opt/homebrew/Caskroom/kicad/10.0.4/KiCad/KiCad.app/Contents/"
           "SharedSupport/footprints/Package_DIP.pretty")

# chip type -> DIP footprint (real package widths; 600-mil for >=24-pin MSI)
FP = {
    'CPU8080':'DIP-40_W15.24mm', 'PPI8255':'DIP-40_W15.24mm', 'FDC1793':'DIP-40_W15.24mm',
    'SYS8238':'DIP-28_W15.24mm', 'EPROM8K':'DIP-28_W15.24mm', 'USART8251':'DIP-28_W15.24mm',
    'PIC8259':'DIP-28_W15.24mm', 'PIT8253':'DIP-24_W15.24mm', 'BUF8286':'DIP-20_W7.62mm',
}
def dip_for(n):                       # smallest standard DIP that holds n pins
    for s in (14,16,18,20,24,28,40):
        if n <= s: return f"DIP-{s}_W{'15.24' if s>=24 else '7.62'}mm"
    return "DIP-40_W15.24mm"

# real Soviet case marking (printed on the chip) per type -> silkscreen Value text. Taken from
# the authoritative component list ДГШ3.031.006 (juku3000 "nimekiri komponendid.pdf", pp.3-4).
# The МПК580 set + memory are exact; the few marked (tentative) need the schematic to pin the
# exact refdes<->part (the BOM gives counts, not refdes mapping).
MARK = {
    'CPU8080':'КР580ИК80А', 'SYS8238':'КР580ВК38',  'USART8251':'КР580ВВ51А',
    'PPI8255':'КР580ВВ55А', 'PIT8253':'КР580ВИ53',  'PIC8259':'КР580ВН59',
    'BUF8286':'КР580ВА86',  'RU5':'565РУ3Г',         'EPROM8K':'К573РФ5',
    'IO_DEC138':'К555ИД7',  'RASCAS_DEC':'К531ИД7',  'IE7_CTR':'К555ИЕ7',
    'KP14_MUX':'К531КП14',  'LA1_GATE':'К531ЛА1',    'LA3_GATE':'К555ЛА3',
    'LA12_GATE':'К531ЛА12', 'LN1_INV':'К531ЛН1',     'LN1_OSC':'К531ЛН1',
    'AG3_ONESHOT':'КМ555АГ3','IE10_CTR':'К555ИЕ10',  'DEC_PROM':'КР556РТ4',
    'CT16_CTR':'К531ИЕ7',   'CLK_PHASE':'К531ЛН5',           # pinned via repo tracing (clock-subsystem.md / memory.md)
}

# Placement read from the ES101 assembly drawing (juku3000 emaplaat.pdf): landscape
# ~310x195 mm board. The top-edge connectors + transceiver row + ROM row + DRAM array are
# positioned per the real layout; logic clusters sit in their drawing regions. Tuple =
# (x_mm, y_mm, rotation_deg). rot 90 = vertical DIP (as drawn for ROM/DRAM).
PLACE = {
    # NOTE: KiCad DIP footprints stand VERTICAL at rot 0 (pins down both sides). So rot 90 =
    # horizontal package. ROM/DRAM sockets are drawn vertical -> rot 0; logic rows -> rot 90.
    # transceiver/driver row (horizontal), just below the top-edge X1/X2 connectors
    # transceiver row read precisely off the drawing: y59, x 23/55/86/113 (was y42, too far right).
    # D27 (wide PPI 8255) sits at the right end of this top band @ (162,57).
    'D25':(23,59,90), 'D23':(55,59,90), 'D24':(86,59,90), 'D29':(113,59,90), 'D27':(162,57,90),
    # ROM row (vertical 28-pin sockets; D15/D16 populated, D17-D22 empty) + the USART D11 at the
    # right end. Exact drawing coords (verified frame): sockets at y≈105, ~32 mm pitch.
    'D15':(22,86,0), 'D16':(43,86,0), 'D11':(201,86,0),   # ROM sockets y86, ~21mm pitch; D11 (USART) at its real spot right of the sockets
    # DRAM bank (565РУ3Г, vertical 16-pin): the top array row D67..D60, read precisely off the
    # drawing -- x 127..238, ~16 mm pitch (was 102..235/pitch-19, ~25 mm too far left at D67). The
    # left column (unmodeled D50 @ ~112) lines up with the D48/D49 muxes below it.
    'D67':(127,158,0),'D66':(144,158,0),'D65':(159,158,0),'D64':(175,158,0),
    'D63':(191,158,0),'D62':(207,158,0),'D61':(223,158,0),'D60':(238,158,0),
    # I/O block (PIT 8253 + PPI 8255) -- the drawing puts these on the RIGHT/bottom-right, NOT the
    # top: PITs D57/D55/D54 stack down the right edge (x~292, pulled in from the ~296 read to fit
    # the 310 cut), and PPI D26 sits bottom-right just left of D54. (Was a fictional top I/O row.)
    'D57':(292,230,90),'D55':(292,252,90),'D54':(292,276,90),'D26':(245,276,90),
    # CPU is a tall VERTICAL chip in the lower-left (per emaplaat: D1 + D4/D2/D107 stand there).
    # Exact verified-frame read: D1 center ≈ (35,176); D4/D2 vertical just right of it (≈y158).
    'D1':(35,176,0),'D4':(57,158,0),'D2':(83,158,0),
    # video address counters (ИЕ7) + DRAM addr muxes (КП14) live in the LEFT columns of the DRAM
    # array (read off the drawing): two sub-rows at y217 / y242 descending into the array, with
    # D46/D44/D48 over D47/D45/D49 -- NOT a separate row up by the bus. (~13 mm pitch, vertical.)
    'D46':(84,217,0),'D44':(97,217,0),'D48':(111,217,0),
    'D47':(85,242,0),'D45':(98,242,0),'D49':(112,242,0),
    # video-output chain -- relocated to the right-centre with the clock cluster (read off the
    # drawing): RAS/CAS decode D53 sits below D36; IE10 ctr D103 below D39; AG3 one-shot D56 far
    # right (raw read hit the 310 edge -> pulled in 5 mm so the DIP stays on-board). All vertical.
    'D53':(244,225,0),'D103':(294,200,0),'D56':(305,200,0),
    # bus interface band (read off the drawing): a horizontal row in the gap BETWEEN the ROM row
    # and the DRAM array -- D5 (8238) far left, then D6 / DLB(=D8) / D7, and the wide D10 (8259).
    # This was a fictional bottom-centre row before; the muxes above now occupy that freed space.
    'D5':(35,136,90),'D6':(68,136,90),'DLB':(93,136,90),'D7':(143,136,90),'D10':(189,136,90),
    # clock subsystem -- RELOCATED to its real right-centre region, read off the assembly drawing
    # via the validated frame (the divider/gate mesh sits right of the DRAM array near D40/D41/D34,
    # not a fictional bottom-left row). D40 (СТ16) is drawn horizontal -> rot 90; the ЛА/ЛН gates
    # D38/D39/D33/D36/D35 are drawn vertical -> rot 0. D59 (osc) is still approximate (the drawing
    # puts it bottom-centre by the transformer -- read it next pass).
    'D40':(277,155,90),'D38':(251,176,0),'D39':(294,176,0),
    'D36':(244,200,0),'D33':(277,200,0),'D35':(263,221,0),   # D35 nudged up 4mm to clear D7
    'D59':(112,281,90),   # osc ЛН1 -- read off the drawing: horizontal, bottom-centre by transformer Z
}
X0, Y0, DX, DY = 30.0, 30.0, 28.0, 30.0   # fallback grid for any chip not in PLACE

def main():
    spec = json.load(open(sys.argv[1])); out = sys.argv[2]
    chips = {c['ref']: c for c in spec['chips']}

    # max pin number actually used per chip (pins dict + net nodes) -> footprint must cover it
    maxpin = {r: max([int(p) for p in c['pins']] or [0]) for r, c in chips.items()}
    for net in spec['nets'].values():
        for ref, pin in (net['nodes'] if isinstance(net, dict) else net):
            if ref in maxpin: maxpin[ref] = max(maxpin[ref], int(pin))

    board = pcbnew.BOARD()
    placed, n_pads = {}, 0

    def add_chip(ref, x, y, rot=0):
        nonlocal n_pads
        c = chips[ref]; typ = c['type']
        fpname = FP.get(typ) or dip_for(maxpin[ref])
        fp = pcbnew.FootprintLoad(DIP_LIB, fpname)
        if fp is None: raise RuntimeError(f"no footprint {fpname} for {ref}")
        fp.SetReference(ref); fp.SetValue(MARK.get(typ, typ))
        fp.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(x), pcbnew.FromMM(y)))
        if rot: fp.SetOrientationDegrees(rot)
        board.Add(fp); placed[ref] = fp
        n_pads += fp.GetPadCount()
        # KiCad's footprint ANCHOR sits at pin 1 (a CORNER), not the body centre -- so the
        # SetPosition above placed the corner at (x,y), shifting the chip half-its-size down/right.
        # Re-place so the body CENTRE lands on (x,y), which is what the drawing coords mean.
        c = fp.GetBoundingBox(False, False).GetCenter()
        fp.SetPosition(pcbnew.VECTOR2I(2*pcbnew.FromMM(x) - c.x, 2*pcbnew.FromMM(y) - c.y))
        # EVERY chip gets its real case marking centred on the body (along the chip's long axis)
        # + its refdes just past the top-narrow end. Marking text angle follows the package: a
        # vertical chip (rot 0) reads along Y (90); a horizontal chip (rot 90) reads along X (0).
        hh = pcbnew.ToMM(fp.GetBoundingBox(False, False).GetHeight()) / 2.0   # half chip height (no text)
        CTR_H, CTR_V = pcbnew.GR_TEXT_H_ALIGN_CENTER, pcbnew.GR_TEXT_V_ALIGN_CENTER
        mang = 90 if rot % 180 == 0 else 0
        r = fp.Reference(); v = fp.Value()
        r.SetVisible(True); r.SetLayer(pcbnew.F_SilkS)
        r.SetTextSize(pcbnew.VECTOR2I(pcbnew.FromMM(3), pcbnew.FromMM(3)))
        r.SetTextThickness(pcbnew.FromMM(0.5))
        r.SetHorizJustify(CTR_H); r.SetVertJustify(CTR_V)
        r.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(x), pcbnew.FromMM(y - hh - 2.5)))     # just above the top narrow end
        v.SetVisible(True); v.SetLayer(pcbnew.F_SilkS)
        v.SetTextSize(pcbnew.VECTOR2I(pcbnew.FromMM(2.7), pcbnew.FromMM(2.7)))            # readable, still fits DIP-14/16
        v.SetTextThickness(pcbnew.FromMM(0.45))
        v.SetHorizJustify(CTR_H); v.SetVertJustify(CTR_V)                                # centred on the body
        try: v.SetTextAngle(pcbnew.EDA_ANGLE(mang, pcbnew.DEGREES_T))                     # along the chip
        except Exception: v.SetTextAngle(mang * 10)
        v.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(x), pcbnew.FromMM(y)))                # on the chip body centre

    # place per the assembly-drawing map; any chip not in PLACE -> fallback grid below
    row = 0
    for ref in chips:
        if ref in PLACE:
            x, y, rot = PLACE[ref]; add_chip(ref, x, y, rot)
    col = 0
    for ref in sorted(chips):
        if ref not in PLACE:
            add_chip(ref, X0 + col*DX, 215 + row*DY); col += 1
            if col == 8: col = 0; row += 1

    # nets: create a NETINFO per net name, assign to each (ref,pin) pad
    assigned = 0
    for name, e in spec['nets'].items():
        ni = pcbnew.NETINFO_ITEM(board, name); board.Add(ni)
        for ref, pin in (e['nodes'] if isinstance(e, dict) else e):
            fp = placed.get(ref)
            if not fp: continue
            pad = fp.FindPadByNumber(str(pin))
            if pad: pad.SetNet(ni); assigned += 1

    # board outline (Edge.Cuts) in the read frame (origin = 310-dim left arrow @ orig-px
    # (1740,990), px/mm 14.52). FRAME BUG fixed: the board TOP edge is ~22 mm BELOW that dim line
    # (the width dimension sits in the top margin) -- I'd been treating the dim line as the top,
    # which pushed every chip's %-position down.
    # PCB = 310 x 266 mm (owner MEASURED the real board). So edges: left 0, right 310, top 22,
    # bottom = top(22)+266 = 288. (The 279 measured earlier was the OUTER envelope incl. the video
    # jack X8 overhang -- not the PCB cut.) Chips read in the same frame sit correctly vs the top.
    BX0, BY0, BX1, BY1 = 0.0, 22.0, 310.0, 288.0
    def edge(x1,y1,x2,y2):
        s = pcbnew.PCB_SHAPE(board); s.SetShape(pcbnew.SHAPE_T_SEGMENT)
        s.SetLayer(pcbnew.Edge_Cuts); s.SetWidth(pcbnew.FromMM(0.15))
        s.SetStart(pcbnew.VECTOR2I(pcbnew.FromMM(x1), pcbnew.FromMM(y1)))
        s.SetEnd(pcbnew.VECTOR2I(pcbnew.FromMM(x2), pcbnew.FromMM(y2))); board.Add(s)
    for a in [(BX0,BY0,BX1,BY0),(BX1,BY0,BX1,BY1),(BX1,BY1,BX0,BY1),(BX0,BY1,BX0,BY0)]: edge(*a)

    # mounting holes (mechanical -- no nets, LVS-clean): drilled Ø3.5 holes read off the drawing.
    # The drawing's corner ⊕ targets sit at TL≈(7,30), BL≈(5,289) on the MAIN board, and at the
    # RIGHT at ≈(319,290)/X6-jack≈323 -- i.e. on the jack overhang PAST the 310 cut (so excluded
    # from this 310×266 rectangle). This also CONFIRMS the frame: px/mm 14.52 is right and 310 is
    # the main width; the right-side jacks/tabs overhang past it (like the bottom video-jack gives 279).
    def mhole(hx, hy, d=3.5):
        h = pcbnew.PCB_SHAPE(board); h.SetShape(pcbnew.SHAPE_T_CIRCLE)
        h.SetLayer(pcbnew.Edge_Cuts); h.SetWidth(pcbnew.FromMM(0.15))
        h.SetCenter(pcbnew.VECTOR2I(pcbnew.FromMM(hx), pcbnew.FromMM(hy)))
        h.SetEnd(pcbnew.VECTOR2I(pcbnew.FromMM(hx + d/2.0), pcbnew.FromMM(hy))); board.Add(h)
    mhole(7, 30); mhole(6, 283)        # TL, BL (read 5,289 -> inset to stay within the 288 bottom)

    # top-edge expansion connectors X1/X2 -- non-electrical SILK OUTLINE annotations (read off the
    # drawing: X1 mm15..107, X2 mm118..177, at the top edge). Their full pin/net model is future
    # LVS work (bom-toward-76); this just shows the two prominent connectors so the top matches.
    def silk_box(x0, y0, x1, y1, label):
        r = pcbnew.PCB_SHAPE(board); r.SetShape(pcbnew.SHAPE_T_RECT)
        r.SetLayer(pcbnew.F_SilkS); r.SetWidth(pcbnew.FromMM(0.2))
        r.SetStart(pcbnew.VECTOR2I(pcbnew.FromMM(x0), pcbnew.FromMM(y0)))
        r.SetEnd(pcbnew.VECTOR2I(pcbnew.FromMM(x1), pcbnew.FromMM(y1))); board.Add(r)
        t = pcbnew.PCB_TEXT(board); t.SetText(label); t.SetLayer(pcbnew.F_SilkS)
        t.SetTextSize(pcbnew.VECTOR2I(pcbnew.FromMM(3), pcbnew.FromMM(3)))
        t.SetTextThickness(pcbnew.FromMM(0.5))
        t.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM((x0+x1)/2.0), pcbnew.FromMM((y0+y1)/2.0)))
        board.Add(t)
    silk_box(15, 23, 107, 33, "X1"); silk_box(118, 23, 177, 33, "X2")
    silk_box(222, 283, 273, 288, "X9")   # bottom connector (read mm222..273, pins 58..45)
    # ROM bank is К573РФ5 ×8 (BOM) -> D15-D22. D15/D16 are net-modeled chips; the other 6 aren't
    # traced yet (toward-76), so show them as PLACEMENT-ONLY silk socket outlines to complete the
    # 8-EPROM bank visually (same row y86, ~21 mm pitch). Not in board.json -> LVS unaffected.
    for i, ref in enumerate(['D17', 'D18', 'D19', 'D20', 'D21', 'D22']):
        cx = 64 + i*21
        silk_box(cx - 7.6, 66, cx + 7.6, 106, ref)
    # DRAM array is 565РУ3Г ×32 (BOM) -> D60-D91 in a 4×8 grid. Row 1 (D60-67 @ y158) is net-
    # modeled; add the other 3 rows (D68-D91, 24 chips) as placement-only silk outlines so the
    # full array shows (same 8 columns; rows read at y≈190/217/242). Not in board.json -> LVS clean.
    DRAM_COLS = [127, 144, 159, 175, 191, 207, 223, 238]
    for ry, refs in [(190, ['D75','D74','D73','D72','D71','D70','D69','D68']),
                     (217, ['D83','D82','D81','D80','D79','D78','D77','D76']),
                     (242, ['D91','D90','D89','D88','D87','D86','D85','D84'])]:
        for cx, ref in zip(DRAM_COLS, refs):
            silk_box(cx - 4, ry - 10, cx + 4, ry + 10, ref)
    # more toward-76 positions as placement-only outlines (not net-traced): the bottom row
    # D42/D43/D58 (alongside D59) and the DRAM-array left column D50/D51.
    for cx, ref in [(142, 'D42'), (170, 'D43'), (197, 'D58')]:
        silk_box(cx - 10, 277, cx + 10, 285, ref)              # bottom row, horizontal
    silk_box(108, 148, 116, 168, 'D50'); silk_box(108, 180, 116, 200, 'D51')   # array col0, vertical
    # right-side serial/tape/video block (toward-76) -- the clearly-separated chips as placement
    # outlines: D93 (big, ~246,64) + the top-edge row D97/D95/D98/D96 (~y40). The denser middle
    # cluster (D99/D100/D101/D102/D104/D106/D28/D12/D3...) has tilted/packed labels -> deferred.
    silk_box(239, 53, 253, 75, 'D93')
    for cx, ref in [(245, 'D97'), (254, 'D95'), (261, 'D94'), (268, 'D98'), (278, 'D96')]:
        silk_box(cx - 3.5, 34, cx + 3.5, 46, ref)             # top-edge row, small vertical (D94 fills the gap)
    # lower-left chips (toward-76): completes the CPU cluster (D107 below D4) + the lower-left
    # corner (D52, D30). Read off the drawing; placement-only outlines.
    silk_box(46, 174, 58, 196, 'D107'); silk_box(53, 207, 65, 229, 'D52'); silk_box(23, 203, 35, 225, 'D30')
    # baud-rate chain (tape-serial.md: D102=ИЕ11, D101=ИМ1, D99=ИР9) -- the readable row @ y≈54,
    # right of D93. (D100=2nd ИР9 + the rest of the packed cluster still need careful reads.)
    for cx, ref in [(257, 'D102'), (265, 'D101'), (273, 'D99')]:
        silk_box(cx - 3.5, 48, cx + 3.5, 62, ref)
    # small chips just right of D11 (USART): D12 (≈215,72), D3 (≈215,92) -- read off the drawing.
    silk_box(210, 64, 220, 80, 'D12'); silk_box(210, 84, 220, 100, 'D3')
    # clock/divider cluster fill (read off the drawing): D41 (≈251,155, paired with D40, horizontal),
    # D37 (≈261,200, between D36/D33), D34 (≈305,176, right edge).
    silk_box(240, 150, 262, 160, 'D41'); silk_box(255, 190, 267, 210, 'D37'); silk_box(300, 166, 310, 186, 'D34')
    BW, BH = BX1-BX0, BY1-BY0

    board.BuildListOfNets()
    pcbnew.SaveBoard(out, board)
    # use the GOST CAD font for silkscreen text so the Cyrillic case markings render fully
    # (KiCad's built-in stroke font drops В/М glyphs). The face is resolved from ~/Library/Fonts.
    txt = open(out, encoding="utf-8").read().replace('(font', '(font (face "GOST CAD KK")')
    open(out, "w", encoding="utf-8").write(txt)
    print(f"wrote {out}: {len(placed)} footprints, {board.GetNetCount()} nets, "
          f"{assigned} pad-net assignments, board {BW:.0f}x{BH:.0f} mm (GOST silkscreen font)")

if __name__ == "__main__":
    main()
