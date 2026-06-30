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

# Placement read from the ES101 assembly drawing (juku3000 emaplaat.pdf): landscape
# ~310x195 mm board. The top-edge connectors + transceiver row + ROM row + DRAM array are
# positioned per the real layout; logic clusters sit in their drawing regions. Tuple =
# (x_mm, y_mm, rotation_deg). rot 90 = vertical DIP (as drawn for ROM/DRAM).
PLACE = {
    # transceiver/driver row, just below the X1/X2 edge connectors (top edge)
    'D25':(25,30,0), 'D23':(58,30,0), 'D24':(98,30,0), 'D29':(131,30,0), 'D27':(195,32,0),
    # ROM row (vertical 28-pin sockets, D15/D16 populated; D17-D22 empty)
    'D15':(20,62,90), 'D16':(38,62,90),
    # DRAM bank (one row of 8 populated К565РУ5, vertical 16-pin)
    'D60':(35,108,90),'D61':(49,108,90),'D62':(63,108,90),'D63':(77,108,90),
    'D64':(91,108,90),'D65':(105,108,90),'D66':(119,108,90),'D67':(133,108,90),
    # video address/dot-clock chain (row beneath the array)
    'D44':(35,140,0),'D45':(60,140,0),'D46':(85,140,0),'D47':(110,140,0),
    'D48':(135,140,0),'D49':(158,140,0),'D53':(181,140,0),'D56':(35,160,0),'D103':(60,160,0),
    # CPU + bus + decode cluster (lower-left)
    'D1':(45,182,0),'D4':(95,160,0),'DLB':(95,176,0),'D5':(130,168,0),'D6':(165,160,0),
    'D2':(165,176,0),'D7':(190,160,0),
    # I/O block (right side)
    'D26':(235,62,0),'D11':(235,100,0),'D54':(212,132,0),'D55':(245,132,0),'D57':(278,132,0),
    'D10':(250,160,0),
    # clock subsystem (bottom strip)
    'D59':(95,190,0),'D35':(118,190,0),'D38':(138,190,0),'D40':(158,190,0),
    'D33':(178,190,0),'D36':(198,190,0),'D39':(215,190,0),
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
        fp.SetReference(ref); fp.SetValue(typ)
        fp.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(x), pcbnew.FromMM(y)))
        if rot: fp.SetOrientationDegrees(rot)
        board.Add(fp); placed[ref] = fp
        n_pads += fp.GetPadCount()

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

    # board outline (Edge.Cuts) = the real ES101 board, 310 x 195 mm landscape
    BW, BH = 312.0, 198.0
    def edge(x1,y1,x2,y2):
        s = pcbnew.PCB_SHAPE(board); s.SetShape(pcbnew.SHAPE_T_SEGMENT)
        s.SetLayer(pcbnew.Edge_Cuts); s.SetWidth(pcbnew.FromMM(0.15))
        s.SetStart(pcbnew.VECTOR2I(pcbnew.FromMM(x1), pcbnew.FromMM(y1)))
        s.SetEnd(pcbnew.VECTOR2I(pcbnew.FromMM(x2), pcbnew.FromMM(y2))); board.Add(s)
    for a in [(5,5,5+BW,5),(5+BW,5,5+BW,5+BH),(5+BW,5+BH,5,5+BH),(5,5+BH,5,5)]: edge(*a)

    board.BuildListOfNets()
    pcbnew.SaveBoard(out, board)
    print(f"wrote {out}: {len(placed)} footprints, {board.GetNetCount()} nets, "
          f"{assigned} pad-net assignments, board {BW:.0f}x{BH:.0f} mm")

if __name__ == "__main__":
    main()
