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
    # NOTE: KiCad DIP footprints stand VERTICAL at rot 0 (pins down both sides). So rot 90 =
    # horizontal package. ROM/DRAM sockets are drawn vertical -> rot 0; logic rows -> rot 90.
    # transceiver/driver row (horizontal), just below the top-edge X1/X2 connectors
    'D25':(34,40,90), 'D23':(66,40,90), 'D24':(150,40,90), 'D29':(184,40,90), 'D27':(255,40,90),
    # ROM row (vertical 28-pin sockets; D15/D16 populated, D17-D22 empty)
    'D15':(26,82,0), 'D16':(49,82,0),
    # DRAM bank (one row of 8 populated К565РУ5, vertical 16-pin)
    'D60':(30,122,0),'D61':(46,122,0),'D62':(62,122,0),'D63':(78,122,0),
    'D64':(94,122,0),'D65':(110,122,0),'D66':(126,122,0),'D67':(142,122,0),
    # I/O block (horizontal), fills the open upper-centre/right below the connectors
    'D57':(160,64,90),'D54':(210,64,90),'D11':(255,64,90),
    'D10':(160,86,90),'D55':(210,86,90),'D26':(255,86,90),
    # video address + dot-clock chain (horizontal row beneath the array)
    'D44':(30,152,90),'D45':(53,152,90),'D46':(76,152,90),'D47':(99,152,90),
    'D48':(122,152,90),'D49':(145,152,90),'D53':(168,152,90),'D56':(191,152,90),'D103':(214,152,90),
    # CPU + bus + decode (horizontal, bottom-centre row)
    'D1':(50,172,90),'D5':(114,172,90),'D6':(154,172,90),'D2':(178,172,90),
    'D4':(204,172,90),'DLB':(232,172,90),'D7':(260,172,90),
    # clock subsystem (horizontal, bottom strip)
    'D59':(30,190,90),'D35':(50,190,90),'D38':(68,190,90),'D40':(86,190,90),
    'D33':(106,190,90),'D36':(124,190,90),'D39':(142,190,90),
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
