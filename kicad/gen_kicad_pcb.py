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

# real case marking (printed on the chip) per type -> shown as the silkscreen Value text
MARK = {'CPU8080':'КР580ВМ80А'}      # 8080A clone; extend per type as each chip is verified

# Placement read from the ES101 assembly drawing (juku3000 emaplaat.pdf): landscape
# ~310x195 mm board. The top-edge connectors + transceiver row + ROM row + DRAM array are
# positioned per the real layout; logic clusters sit in their drawing regions. Tuple =
# (x_mm, y_mm, rotation_deg). rot 90 = vertical DIP (as drawn for ROM/DRAM).
PLACE = {
    # NOTE: KiCad DIP footprints stand VERTICAL at rot 0 (pins down both sides). So rot 90 =
    # horizontal package. ROM/DRAM sockets are drawn vertical -> rot 0; logic rows -> rot 90.
    # transceiver/driver row (horizontal), just below the top-edge X1/X2 connectors
    'D25':(28,42,90), 'D23':(68,42,90), 'D24':(122,42,90), 'D29':(158,42,90), 'D27':(255,42,90),
    # ROM row (vertical 28-pin sockets; D15/D16 populated, D17-D22 empty) + the USART D11 at the
    # right end. Exact drawing coords (verified frame): sockets at y≈105, ~32 mm pitch.
    'D15':(28,105,0), 'D16':(60,105,0), 'D11':(150,105,0),
    # DRAM bank: the populated К565РУ5 (vertical 16-pin) sit in the array on the RIGHT side of
    # the board (per emaplaat: rows of D50/D67/D66/D64/D63… on the right), not centre-left.
    'D67':(102,158,0),'D66':(121,158,0),'D65':(140,158,0),'D64':(159,158,0),
    'D63':(178,158,0),'D62':(197,158,0),'D61':(216,158,0),'D60':(235,158,0),
    # I/O block (horizontal), fills the open upper-centre/right below the connectors
    'D57':(160,64,90),'D54':(210,64,90),'D26':(255,64,90),
    'D55':(200,86,90),
    # CPU is a tall VERTICAL chip in the lower-left (per emaplaat: D1 + D4/D2/D107 stand there).
    # Exact verified-frame read: D1 center ≈ (35,176); D4/D2 vertical just right of it (≈y158).
    'D1':(35,176,0),'D4':(57,158,0),'D2':(83,158,0),
    # video address counters (ИЕ7) + DRAM addr muxes (КП14) live in the LEFT columns of the DRAM
    # array (read off the drawing): two sub-rows at y217 / y242 descending into the array, with
    # D46/D44/D48 over D47/D45/D49 -- NOT a separate row up by the bus. (~13 mm pitch, vertical.)
    'D46':(84,217,0),'D44':(97,217,0),'D48':(111,217,0),
    'D47':(85,242,0),'D45':(98,242,0),'D49':(112,242,0),
    # video-output chain (RAS/CAS decode D53, one-shot D56, IE10 D103) -- still in the old band;
    # refine to exact coords next pass (some sit out by the clock cluster on the right).
    'D53':(226,132,90),'D56':(252,132,90),'D103':(278,132,90),
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
    'D59':(70,255,90),
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
        if typ in MARK:                       # refdes at the top-narrow end; marking on-body, along the chip
            hh = pcbnew.ToMM(fp.GetBoundingBox(False, False).GetHeight()) / 2.0   # half chip height (no text)
            CTR_H, CTR_V = pcbnew.GR_TEXT_H_ALIGN_CENTER, pcbnew.GR_TEXT_V_ALIGN_CENTER
            r = fp.Reference(); v = fp.Value()
            r.SetVisible(True); r.SetLayer(pcbnew.F_SilkS)
            r.SetTextSize(pcbnew.VECTOR2I(pcbnew.FromMM(4), pcbnew.FromMM(4)))
            r.SetTextThickness(pcbnew.FromMM(0.7))
            r.SetHorizJustify(CTR_H); r.SetVertJustify(CTR_V)
            r.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(x), pcbnew.FromMM(y - hh - 3)))   # just above the top narrow end
            v.SetVisible(True); v.SetLayer(pcbnew.F_SilkS)
            v.SetTextSize(pcbnew.VECTOR2I(pcbnew.FromMM(3.0), pcbnew.FromMM(3.0)))
            v.SetTextThickness(pcbnew.FromMM(0.4))
            v.SetHorizJustify(CTR_H); v.SetVertJustify(CTR_V)                             # centred on the body
            try: v.SetTextAngle(pcbnew.EDA_ANGLE(90, pcbnew.DEGREES_T))                   # rotate 90 (along the chip)
            except Exception: v.SetTextAngle(900)
            v.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(x), pcbnew.FromMM(y)))            # on the chip body centre

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
    # which pushed every chip's %-position down. PCB edges: left 0, right 310, top 22, bottom 301
    # PCB = 310 x 260 mm (owner-confirmed). The 279 I'd measured is the OUTER envelope (the
    # video jack X8 extends ~19 mm below the PCB) -- NOT the PCB cut. So bottom = top(22)+260 =
    # 282 (the jack lives at mm 282..301, beyond the board). Chips read in the same frame sit
    # correctly relative to the top. <-- refine top with the owner's reference if D1 isn't centred.
    BX0, BY0, BX1, BY1 = 0.0, 22.0, 310.0, 282.0
    def edge(x1,y1,x2,y2):
        s = pcbnew.PCB_SHAPE(board); s.SetShape(pcbnew.SHAPE_T_SEGMENT)
        s.SetLayer(pcbnew.Edge_Cuts); s.SetWidth(pcbnew.FromMM(0.15))
        s.SetStart(pcbnew.VECTOR2I(pcbnew.FromMM(x1), pcbnew.FromMM(y1)))
        s.SetEnd(pcbnew.VECTOR2I(pcbnew.FromMM(x2), pcbnew.FromMM(y2))); board.Add(s)
    for a in [(BX0,BY0,BX1,BY0),(BX1,BY0,BX1,BY1),(BX1,BY1,BX0,BY1),(BX0,BY1,BX0,BY0)]: edge(*a)
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
