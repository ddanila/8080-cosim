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
    'AP2':'DIP-8_W7.62mm', 'LA18':'DIP-8_W7.62mm',   # DIP-8 confirmed by board photos
}
SHARED = "/opt/homebrew/Caskroom/kicad/10.0.4/KiCad/KiCad.app/Contents/SharedSupport/footprints/"
PASSIVE_FP = {
    'R_AXIAL': ('Resistor_THT.pretty',  'R_Axial_DIN0207_L6.3mm_D2.5mm_P7.62mm_Horizontal'),
    'C_KM':    ('Capacitor_THT.pretty', 'C_Disc_D4.7mm_W2.5mm_P5.00mm'),
    'C_ELEC':  ('Capacitor_THT.pretty', 'CP_Radial_D5.0mm_P2.00mm'),
    'D_DIODE': ('Diode_THT.pretty',     'D_DO-35_SOD27_P7.62mm_Horizontal'),
    'SW':      ('Connector_PinHeader_2.54mm.pretty', 'PinHeader_1x02_P2.54mm_Vertical'),
    'XTAL':    ('Crystal.pretty',       'Crystal_HC49-U_Horizontal'),   # РК-171 flat can, lying -- closest stock footprint
    'C_TRIM':  ('Capacitor_THT.pretty', 'C_Disc_D7.5mm_W4.4mm_P5.00mm'), # КТ4-23 trimmer stand-in (no trimmer lib in stock KiCad)
}
# traced-network passives [scan] + decoupling C35-C72 (BOM count; chip-adjacent positions assumed)
PASSIVE_PLACE = {
    'R19':(60,272,90),'VD5':(55,271,90),'C31':(86,257,0),'C32':(92,257,0),'C33':(98,257,0),   # corner re-layout: the assumed grid squatted the crystal's real estate (photo-true corner)
    'R3':(23,214,0),'R4':(34,214,0),'R20':(45,214,0),'C21':(53.5,214,0),'C1':(60,214,0),'S1':(67,214,0),
    'R38':(245,204,90),'R39':(245,217,90),
    'Z1':(78,271,90),    # РК-171 crystal at its PHOTO-TRUE spot (edge-relative measurement, straight-on corner crop)
    'CT1':(64,261,0),    # trimmer (8811) left of the crystal per the corner photos; ref placeholder until the schematic pins it
}
_DEC = [(238,171,0),(231,158,90),(215,158,90),(199,158,90),(183,158,90),(167,158,90),(152,158,90),(135,158,90),
        (22,109,0),(64,109,0),(106,109,0),(148,109,0),
        (35,124,0),(23.5,176,90),(189,124,0),(212.5,86,90),(240,278.5,0),(162,44,0),   # C51 below D26, X9 gap (the only pocket that fits a disc cap)
        (214,272,0),(271,252,0),(271,238,0),
        (55,51,0),(113,51,0),(68,127,0),(143,127,0),(97,203,0),(84,203,0),(111,203,0),
        (277,147,0),(259,176,90),(274,221,90),(142,261.5,0),(197,261.5,0),(207,54,90),(228,103,90),   # C66/C67 up with the bottom row (was y=273, overlapped the moved D42/D58)
        (199,190,90),(199,217,90),(199,242,90)]
for _i, _xy in enumerate(_DEC): PASSIVE_PLACE[f'C{35+_i}'] = _xy

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
    'CT16_CTR':'КР531ИЕ17',   'CLK_PHASE':'К155ЛН5',           # pinned via repo tracing (clock-subsystem.md / memory.md)
    'VABUS':'КР580ВА87',    'IR82':'КР580ИР82',      'IR16':'К155ИР16',
    'TL2':'К155ТЛ2',        'LN1_DUAL':'К531ЛН1',    'AP2':'К170АП2',
    'UP2':'К170УП2',        'LA18':'К155ЛА18',    'LN2':'К561ЛН2',
}
MARK_REF = {'D29':'КР580ВА86',   # the ВА86 among the VABUS transceivers (D23-25 = ВА87)
            'D37':'КР1533ЛА3', 'D39':'КР1533ЛА3',   # real series per board-#2 photos
            'D7':'КР1533ЛА3',   # owner-read off the real board (was assumed К555; ALS vs LS -- same logic/pinout, marking only)
            'D56':'К155АГ3',    # board-#2 row-4 АГ3s are К155 8901 (BOM said КМ555АГ3; real board wins, D7 precedent)
            'D2':'КР556РТ4А'}   # D2 is the 2nd РТ4 PROM (photo: both socketed by the CPU), not a 74138

# Placement read from the ES101 assembly drawing (juku3000 emaplaat.pdf): landscape
# ~310x195 mm board. The top-edge connectors + transceiver row + ROM row + DRAM array are
# positioned per the real layout; logic clusters sit in their drawing regions. Tuple =
# (x_mm, y_mm, rotation_deg). rot 90 = vertical DIP (as drawn for ROM/DRAM).
PLACE = {
    # NOTE: KiCad DIP footprints stand VERTICAL at rot 0 (pins down both sides). So rot 90 =
    # horizontal package. ROM/DRAM sockets are drawn vertical -> rot 0; logic rows -> rot 90.
    # transceiver/driver row (horizontal), just below the top-edge X1/X2 connectors
    # D27 (wide PPI 8255) sits at the right end of the top transceiver band @ (162,57). The bus
    # transceivers D25/D23/D24/D29 in this row are NOT net-modeled (not in board.json) -> they're
    # placement outlines below, not PLACE entries (PLACE entries for non-board.json refs no-op).
    'D27':(162,57,90),
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
    'D57':(292,223,90),'D55':(292,245,90),'D54':(292,269,90),'D26':(245,265,90),   # stack -7mm: edge-relative re-measure on the 9.50 y-scale (pitch 24 confirmed; absolute y was inflated)
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
    'D53':(253,225,0),'D103':(291,200,0),
    'D56':(302,200,0),    # АГ3 at its DRAWN spot after all: the "К555ЛУ?/1068" photo read there was
                          # К155АГ3 8901 UPSIDE DOWN (1068 = 8901 rotated). Quadrant round-trip reverted.
    # bus interface band (read off the drawing): a horizontal row in the gap BETWEEN the ROM row
    # and the DRAM array -- D5 (8238) far left, then D6 / DLB(=D8) / D7, and the wide D10 (8259).
    # This was a fictional bottom-centre row before; the muxes above now occupy that freed space.
    'D5':(35,136,90),'D6':(68,136,90),'DLB':(93,136,90),'D7':(143,136,90),'D10':(189,136,90),
    # clock subsystem -- RELOCATED to its real right-centre region, read off the assembly drawing
    # via the validated frame (the divider/gate mesh sits right of the DRAM array near D40/D41/D34,
    # not a fictional bottom-left row). D40 (СТ16) is drawn horizontal -> rot 90; the ЛА/ЛН gates
    # D38/D39/D33/D36/D35 are drawn vertical -> rot 0. D59 (osc) is still approximate (the drawing
    # puts it bottom-centre by the transformer -- read it next pass).
    'D40':(277,155,90),'D38':(251,176,0),'D39':(280,176,0),   # D39 294->280: photo shows ЛА3+ЛП5 side by side, ЛП5 (D34) owns the ~294 slot
    'D36':(253,200,180),'D33':(277,200,180),'D35':(266,221,0),   # D36/D33 notch-DOWN (emaplaat+photo)   # D36 +3mm right to clear the DRAM right column; D35 up 4mm to clear D7
    'D59':(105.5,267.5,90),   # osc ЛН1 -- read off the drawing: horizontal, bottom-centre by transformer Z
                          # (bottom row 281->275: photo shows ~11 mm body-to-edge margin; 281 put pads 3 mm from the cut)
    # NET-MODELED this session (Phase-B) -- promoted from placement-outlines to real footprints at
    # their traced drawing positions: bus transceivers (top band, horizontal) + bottom row.
    'D25':(23,59,90),'D23':(55,59,90),'D24':(86,59,90),'D29':(113,59,90),
    'D42':(142,269,90),'D43':(170,269,90),'D58':(197,269,90),   # bottom row -6mm: photo-1's y-scale is 9.50 px/mm (board spans 2528px/266mm), not the 9.87 x-scale -- edge-relative re-measure
    'D37':(265,200,180),   # ЛА3 D42-serial inverter; notch-DOWN (emaplaat+photo)
    'D13':(30,223,90),   # ТЛ2 reset + 8238-STSTB source (net-modeled), lower-left CPU cluster
}
# unpopulated DRAM banks 1-3 (D68-D91) -- now net-modeled sockets -> real footprints at their
# array positions (bit7..bit0 = cols 127..238; rows y190/217/242), promoted from silk outlines.
_DCOLS = [127, 144, 159, 175, 191, 207, 223, 238]
for _ry, _refs in [(190, range(75, 67, -1)), (217, range(83, 75, -1)), (242, range(91, 83, -1))]:
    for _cx, _r in zip(_DCOLS, _refs): PLACE[f'D{_r}'] = (_cx, _ry, 0)
# unpopulated ROM sockets D17-D22 (now net-modeled) -> footprints in the ROM row (y86, ~21mm pitch)
for _i, _r in enumerate(range(17, 23)): PLACE[f'D{_r}'] = (64 + _i*21, 86, 0)
# serial-port cluster (net-modeled): REAL positions read off the emaplaat (relative to the D11
# anchor): D104/D32/D14 = the column under the X3 serial connector; D12/D3 right of D11.
PLACE['D104'] = (198, 54, 0); PLACE['D32'] = (215, 34, 0); PLACE['D14'] = (215, 54, 0)
PLACE['D12']  = (220, 80, 0); PLACE['D3']  = (220, 103, 0)
X0, Y0, DX, DY = 30.0, 30.0, 28.0, 30.0   # fallback grid for any chip not in PLACE

def main():
    spec = json.load(open(sys.argv[1])); out = sys.argv[2]
    chips = {c['ref']: c for c in spec['chips']}

    # max pin number actually used per chip (pins dict + net nodes) -> footprint must cover it.
    # Skip non-numeric pins (connector edge-codes like "104C") -- connectors aren't DIP-placed.
    maxpin = {r: max([int(p) for p in c['pins'] if str(p).isdigit()] or [0]) for r, c in chips.items()}
    for net in spec['nets'].values():
        for ref, pin in (net['nodes'] if isinstance(net, dict) else net):
            if ref in maxpin and str(pin).isdigit(): maxpin[ref] = max(maxpin[ref], int(pin))

    board = pcbnew.BOARD()
    placed, n_pads = {}, 0

    def add_passive(ref, x, y, rot=0):
        nonlocal n_pads
        c = chips[ref]; typ = c['type']
        lib, fpn = PASSIVE_FP[typ]
        fp = pcbnew.FootprintLoad(SHARED + lib, fpn)
        if fp is None: raise RuntimeError(f"no passive footprint {fpn} for {ref}")
        fp.SetReference(ref); fp.SetValue(c.get('value', ''))
        fp.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(x), pcbnew.FromMM(y)))
        if rot: fp.SetOrientationDegrees(rot)
        board.Add(fp); placed[ref] = fp; n_pads += fp.GetPadCount()
        ctr = fp.GetBoundingBox(False, False).GetCenter()          # re-center on (x,y)
        fp.SetPosition(pcbnew.VECTOR2I(2*pcbnew.FromMM(x) - ctr.x, 2*pcbnew.FromMM(y) - ctr.y))
        CTR_H, CTR_V = pcbnew.GR_TEXT_H_ALIGN_CENTER, pcbnew.GR_TEXT_V_ALIGN_CENTER
        show_val = not (typ == 'C_KM' and ref.startswith('C') and c.get('value') == '0,047')
        flip = (int(round(x)) // 6) % 2 == 1   # stagger labels in dense passive rows (silk polish)
        for t, sz, dy in ((fp.Reference(), 1.1, 2.6 if flip else -2.6),
                          (fp.Value(), 0.9, -2.4 if flip else 2.4)):
            t.SetVisible(t is fp.Reference() or show_val)
            t.SetLayer(pcbnew.F_SilkS)
            t.SetTextSize(pcbnew.VECTOR2I(pcbnew.FromMM(sz), pcbnew.FromMM(sz)))
            t.SetTextThickness(pcbnew.FromMM(0.2))
            t.SetHorizJustify(CTR_H); t.SetVertJustify(CTR_V)
            try: t.SetTextAngle(pcbnew.EDA_ANGLE(0, pcbnew.DEGREES_T))
            except Exception: t.SetTextAngle(0)
            t.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(x), pcbnew.FromMM(y + dy)))

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
        # Silkscreen per chip (owner spec): (1) a clear pin-1 KEY dot, (2) the refdes at the KEY
        # end so orientation is readable, (3) the real case marking INSIDE the body, written along
        # the chip's long axis. KiCad rotates footprints CCW: at rot 0 (vertical DIP) pin 1 / the
        # notch is at the TOP; at rot 90 (horizontal) the notch lands at the LEFT.
        bb = fp.GetBoundingBox(False, False)
        hh = pcbnew.ToMM(bb.GetHeight()) / 2.0    # half height (long axis for rot 0)
        hw = pcbnew.ToMM(bb.GetWidth())  / 2.0
        CTR_H, CTR_V = pcbnew.GR_TEXT_H_ALIGN_CENTER, pcbnew.GR_TEXT_V_ALIGN_CENTER
        vert = (rot % 180 == 0)
        # (1) key dot: a filled silk circle just outside pin 1 (top-left at rot 0 -> to its left;
        # bottom-left at rot 90 -> below it)
        p1 = fp.FindPadByNumber('1')
        if p1 is not None:
            pp = p1.GetPosition()
            # outward offset from pin 1 by rotation: 0=top-left(-x) 90=bottom-left(+y)
            # 180=bottom-right(+x) 270=top-right(-y)
            q = rot % 360
            dx, dy = {0:(-1.9,0), 90:(0,1.9), 180:(1.9,0), 270:(0,-1.9)}.get(q, (-1.9,0))
            dot = pcbnew.PCB_SHAPE(board); dot.SetShape(pcbnew.SHAPE_T_CIRCLE)
            dot.SetLayer(pcbnew.F_SilkS); dot.SetFilled(True); dot.SetWidth(0)
            cxy = pcbnew.VECTOR2I(pp.x + pcbnew.FromMM(dx), pp.y + pcbnew.FromMM(dy))
            dot.SetCenter(cxy)
            dot.SetEnd(pcbnew.VECTOR2I(cxy.x + pcbnew.FromMM(0.45), cxy.y))
            board.Add(dot)
        # (2) refdes at the key end: above the top for vertical chips, left of the left end for
        # horizontal ones -- always adjacent to where the key/notch is.
        r = fp.Reference()
        r.SetVisible(True); r.SetLayer(pcbnew.F_SilkS)
        r.SetTextSize(pcbnew.VECTOR2I(pcbnew.FromMM(2.4), pcbnew.FromMM(2.4)))
        r.SetTextThickness(pcbnew.FromMM(0.4))
        r.SetHorizJustify(CTR_H); r.SetVertJustify(CTR_V)
        if vert:
            ry = y + hh + 2.2 if (rot % 360) == 180 else y - hh - 2.2   # refdes at the KEY end
            r.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(x), pcbnew.FromMM(ry)))
        else:
            rx = x + hw + 3.5 if (rot % 360) == 270 else x - hw - 3.5
            r.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(rx), pcbnew.FromMM(y)))
        # (3) marking inside the body, along the long axis, sized to FIT the body
        v = fp.Value()
        mark = MARK_REF.get(ref) or MARK.get(typ, typ)
        v.SetText(mark)
        body_len = 2*hh if vert else 2*hw          # long-axis length
        body_wid = 2*hw if vert else 2*hh
        ts = min(2.7, body_wid * 0.42, (body_len - 2.0) / (0.95 * max(len(mark), 1)))
        ts = max(ts, 1.0)
        v.SetVisible(True); v.SetLayer(pcbnew.F_SilkS)
        v.SetTextSize(pcbnew.VECTOR2I(pcbnew.FromMM(ts), pcbnew.FromMM(ts)))
        v.SetTextThickness(pcbnew.FromMM(max(0.15, ts * 0.16)))
        v.SetHorizJustify(CTR_H); v.SetVertJustify(CTR_V)
        mang = 90 if vert else 0
        try: v.SetTextAngle(pcbnew.EDA_ANGLE(mang, pcbnew.DEGREES_T))
        except Exception: v.SetTextAngle(mang * 10)
        v.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(x), pcbnew.FromMM(y)))

    # connectors are silk outlines, not DIP footprints -> never placed as chips
    CONN = {'EXPANSION_CONN', 'SERIAL_CONN', 'POWER_CONN'}
    # place per the assembly-drawing map; any chip not in PLACE -> fallback grid below
    row = 0
    for ref in chips:
        t = chips[ref]['type']
        if t in CONN: continue
        if t in PASSIVE_FP:
            if ref in PASSIVE_PLACE:
                x, y, rot = PASSIVE_PLACE[ref]; add_passive(ref, x, y, rot)
            continue
        if ref in PLACE:
            x, y, rot = PLACE[ref]; add_chip(ref, x, y, rot)
    col = 0
    for ref in sorted(chips):
        if chips[ref]['type'] in CONN or chips[ref]['type'] in PASSIVE_FP or ref in PLACE: continue
        add_chip(ref, X0 + col*DX, 215 + row*DY); col += 1
        if col == 8: col = 0; row += 1

    # ---- real connector footprints (owner photo: СНП59-96 Р-20-2-В / СНП59-30-23-В) ----
    # Built parametrically: 2.5 mm grid PTH pads (Ø1.6/drill 0.8), pad names = the schematic edge
    # codes, so the existing net loop wires them. X1 = СНП59-96 (32 cols x rows A/B/C -- codes
    # 1<col><row>, our traced nets use rows B/C); X3 = serial (codes 23..51, 2x8 provisional);
    # X8 = power (codes 59..64, 1x6 provisional). X2/X9 stay silk outlines until their nets
    # (PPI ports / keyboard) are traced. Geometry provisional until the owner's edge photos.
    def make_conn(ref, cx, cy, pads_xy):        # pads_xy: {name: (x_mm, y_mm) absolute}
        fp = pcbnew.FOOTPRINT(board)
        # unique FPID per connector: an empty FPID makes the Specctra DSN emit anonymous
        # component defs ('""', '::1'), which breaks the SES import round-trip.
        fp.SetFPID(pcbnew.LIB_ID("juku", f"CONN_{ref}"))
        fp.SetReference(ref); fp.SetValue('')
        fp.Reference().SetVisible(False)
        fp.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(cx), pcbnew.FromMM(cy)))
        for name, (px, py) in pads_xy.items():
            pad = pcbnew.PAD(fp)
            pad.SetAttribute(pcbnew.PAD_ATTRIB_PTH)
            pad.SetShape(pcbnew.PAD_SHAPE_CIRCLE)
            pad.SetSize(pcbnew.VECTOR2I(pcbnew.FromMM(1.6), pcbnew.FromMM(1.6)))
            pad.SetDrillSize(pcbnew.VECTOR2I(pcbnew.FromMM(0.8), pcbnew.FromMM(0.8)))
            pad.SetLayerSet(pcbnew.PAD.PTHMask())
            pad.SetNumber(name)
            pad.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(px), pcbnew.FromMM(py)))
            fp.Add(pad)
        board.Add(fp)
        placed[ref] = fp
        return fp
    # X1: СНП59-96, 32 columns (101..132) x rows A/B/C, grid centered in the mm15-107 silk span
    x1_pads = {}
    for col in range(1, 33):
        px = 22.25 + (col - 1) * 2.5            # 32 cols * 2.5 = 77.5mm, centered at x=61
        for ri, row in enumerate('ABC'):
            x1_pads[f'1{col:02d}{row}'] = (px, 24.5 + ri * 2.5)
    make_conn('X1', 61, 27.5, x1_pads)
    # X3: serial edge connector (traced codes 23,29,30,32,33,51 among 2 rows; provisional 2x8 grid)
    x3_codes = [['23','29','30','32','33','51','35','37'], ['24','26','28','31','34','36','38','40']]
    x3_pads = {}
    for ri, rowcodes in enumerate(x3_codes):
        for ci, code in enumerate(rowcodes):
            x3_pads[code] = (187.0 + ci * 2.5, 24.5 + ri * 2.5)
    make_conn('X3', 196, 25.75, x3_pads)
    # X8: power connector, codes 59..64 in one row (61=+5В 62=GND 60=+12В 59=-12В per scan)
    x8_pads = {str(59 + i): (76.0 + i * 4.0, 282.0) for i in range(6)}
    make_conn('X8', 86, 282, x8_pads)

    # ---- UNTRACED footprints: photo/BOM-identified chips whose NETS aren't traced yet ----
    # Real packages + real marks (renders as chips, not boxes); pads carry no nets (honest).
    # Confident IDs only; the rest stay silk outlines until identified.
    UNTRACED = {
        'D28':  ('DIP-16_W7.62mm', 'К155РЕ3',    228, 55, 0),   # РЕ3 #1, socketed [photo]
        'D30':  ('DIP-14_W7.62mm', 'КМ555ТМ2',   30, 207, 90),  # ready ТМ2 [photo]
        'D34':  ('DIP-14_W7.62mm', 'К555ЛП5',    294, 176, 0),  # video XOR [photo: right of D39, right pins ~12 mm off the edge]
        'D50':  ('DIP-16_W7.62mm', 'КР531КП14',  112, 158, 0),  # video addr mux [drawing; series per corner photo: the lone К555КП14 8904 lives in the D48/D49 cluster, so D50/D51 are КР531]
        'D51':  ('DIP-16_W7.62mm', 'КР531КП14',  112, 190, 0),  # video addr mux [drawing]
        'D93':  ('DIP-40_W15.24mm','КР1818ВГ93', 248, 92, 0),   # FDC [photo; DIP-40 length needs y=92]
        'D97':  ('DIP-20_W7.62mm', 'КР580ВА87',  245, 52, 0),   # FDC bus buffer [drawing top band]
        'D107': ('DIP-20_W7.62mm', 'КР580ВА86',  57, 185, 0),   # 2nd bus buffer, stacked below D4 [photo 201940304: ВА86 x2 8901; user-confirmed same-as-neighbor]
        'D9':   ('DIP-16_W7.62mm', 'К555ИД7',    122, 136, 90), # 3-to-8 decoder, bus band between D8 and D7 [owner-identified]
        'D105': ('DIP-14_W7.62mm', 'К155ЛА3',    30, 240, 90),  # quad NAND, lower-left column below D30/D13 [owner-identified]
        'D41':  ('DIP-16_W7.62mm', 'К555ИР16',   255, 155, 270),# shift register, paired with D40 [owner ID + photo 8902 DIP-16 label-down; x=255 clears the D60 DRAM column]
        # (D99/К561ИР9 REMOVED from the board: both location candidates refuted -- (296,82) excluded
        # by the owner's quadrant rows, (302,200) turned out to be D56's АГ3. The sheet-3 ИР9 exists
        # somewhere (tape-serial.md) but goes back on only when physically located.)
        'D92':  ('DIP-14_W7.62mm', 'К555ЛЕ4',    270, 176, 0),  # quad NOR [emaplaat label + owner's decapped chip]; likely the real Φ1/Φ2 phase generator core
        # --- ВГ93 quadrant, owner's authoritative 4-row layout (iter 39). Refdes PROVISIONAL
        # (nearest drawing-box match; the drawing's layout differs here -- etch reads will settle):
        # row 1 (y52, horiz): D28 РЕ3 ✓, D97 ВА87 ✓, then:
        'D95':  ('DIP-16_W7.62mm', 'К155ЛП11',   268, 52, 90), # hex buffer [iter-33 zoom: 8904, horizontal]
        # row 2 (y96, vertical; photo-6 grounded -- photo-1's top-region compression had put the whole ladder ~25 mm too high):
        'D94':  ('DIP-16_W7.62mm', 'К555ИЕ7',    262, 96, 0),  # counter [photo 8908]
        'D102': ('DIP-14_W7.62mm', 'К155ЛН3',    272, 96, 0),  # hex inv [owner: ЛН3; matches iter-10 К155ЛН3 sighting]
        'D101': ('DIP-14_W7.62mm', 'КМ555ТМ2',   284, 96, 0),  # dual D-FF [photo 8905; owner wrote ТМ3 -- ТМ2 per label]
        # row 3 (y115, horiz):
        'D98':  ('DIP-16_W7.62mm', 'К555КП12',   268, 115, 90), # mux #1 [photo 8812]
        'D96':  ('DIP-14_W7.62mm', 'К155АГ3',    288.5, 115, 90), # [owner: "АП3", behind cable -- АГ3 assumed, verify]
        # row 4 (y132, horiz, below D93's pin field):
        'D100': ('DIP-16_W7.62mm', 'К555КП12',   242, 131, 90),# mux #2 [photo 8812]
        'AG3B': ('DIP-14_W7.62mm', 'К155АГ3',    295.5, 132, 90),# one-shot [photo 8901, label-down]; refdes UNKNOWN -- was provisionally 'D106', but scan-verified D106 = К554СА3 tape comparator (tape-serial.md) owns that number
        'AG3C': ('DIP-14_W7.62mm', 'К155АГ3',    268, 132, 90),# row-4 middle АГ3 (owner's layout); refdes unknown -- NOT D56 (that one is at its drawn (302,200) spot, photo-confirmed)
        'D52':  ('DIP-14_W7.62mm', 'К155ЛА3',    59, 237, 0),   # the ТМ2-ТЛ2-ЛА3 trio [photo]
    }
    for ref, (fpn, mark, x, y, rot) in UNTRACED.items():
        fp = pcbnew.FootprintLoad(DIP_LIB, fpn)
        if fp is None: raise RuntimeError(f"no fp {fpn}")
        fp.SetReference(ref); fp.SetValue(mark)
        fp.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(x), pcbnew.FromMM(y)))
        if rot: fp.SetOrientationDegrees(rot)
        board.Add(fp); placed[ref] = fp
        ctr = fp.GetBoundingBox(False, False).GetCenter()
        fp.SetPosition(pcbnew.VECTOR2I(2*pcbnew.FromMM(x) - ctr.x, 2*pcbnew.FromMM(y) - ctr.y))
        bb = fp.GetBoundingBox(False, False)
        hh, hw = pcbnew.ToMM(bb.GetHeight())/2.0, pcbnew.ToMM(bb.GetWidth())/2.0
        CTR_H, CTR_V = pcbnew.GR_TEXT_H_ALIGN_CENTER, pcbnew.GR_TEXT_V_ALIGN_CENTER
        vert = (rot % 180 == 0)
        r = fp.Reference(); r.SetVisible(True); r.SetLayer(pcbnew.F_SilkS)
        r.SetTextSize(pcbnew.VECTOR2I(pcbnew.FromMM(2.4), pcbnew.FromMM(2.4)))
        r.SetTextThickness(pcbnew.FromMM(0.4)); r.SetHorizJustify(CTR_H); r.SetVertJustify(CTR_V)
        r.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(x if vert else x - hw - 3.5),
                                      pcbnew.FromMM(y - hh - 2.2 if vert else y)))
        v = fp.Value(); v.SetVisible(True); v.SetLayer(pcbnew.F_SilkS)
        body_len = 2*hh if vert else 2*hw; body_wid = 2*hw if vert else 2*hh
        ts = max(1.0, min(2.7, body_wid*0.42, (body_len-2.0)/(0.95*max(len(mark),1))))
        v.SetTextSize(pcbnew.VECTOR2I(pcbnew.FromMM(ts), pcbnew.FromMM(ts)))
        v.SetTextThickness(pcbnew.FromMM(max(0.15, ts*0.16)))
        v.SetHorizJustify(CTR_H); v.SetVertJustify(CTR_V)
        try: v.SetTextAngle(pcbnew.EDA_ANGLE(90 if vert else 0, pcbnew.DEGREES_T))
        except Exception: v.SetTextAngle((90 if vert else 0)*10)
        v.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(x), pcbnew.FromMM(y)))

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
    outline_chips = []                        # placement-only chip outlines (D-refs), for the count report
    outline_boxes = []                        # (x0,y0,x1,y1,label) for the outline-overlap guard
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
        outline_boxes.append((x0, y0, x1, y1, label))
        if label[:1] == 'D': outline_chips.append(label)       # count D-chips only (X1/X2/X9 are connectors)
    silk_box(15, 23, 107, 33, "X1"); silk_box(118, 23, 177, 33, "X2")
    silk_box(222, 283, 273, 287.6, "X9")   # bottom connector (read mm222..273, pins 58..45; box held 0.4 off the edge cut for silk-edge DRC)
    # ROM bank is К573РФ5 ×8 (BOM) -> D15-D22. D15/D16 are net-modeled chips; the other 6 aren't
    # traced yet (toward-76), so show them as PLACEMENT-ONLY silk socket outlines to complete the
    # 8-EPROM bank visually (same row y86, ~21 mm pitch). Not in board.json -> LVS unaffected.
    # (ROM sockets D17-D22 are now net-modeled footprints -- see PLACE -- not silk outlines.)
    # DRAM array is 565РУ3Г ×32 (BOM) -> D60-D91 in a 4×8 grid. Row 1 (D60-67 @ y158) is net-
    # modeled; add the other 3 rows (D68-D91, 24 chips) as placement-only silk outlines so the
    # full array shows (same 8 columns; rows read at y≈190/217/242). Not in board.json -> LVS clean.
    # (DRAM banks 1-3 D68-D91 are now net-modeled footprints -- see PLACE -- not silk outlines.)
    # DRAM-array left column D50/D51 (still placement-only). (D42/D43/D58 are now net-modeled
    # footprints -- see PLACE -- so they're no longer silk outlines here.)
    # (converted to untraced footprints)
    # right-side serial/tape/video block (toward-76) -- the clearly-separated chips as placement
    # outlines: D93 (big, ~246,64) + the top-edge row D97/D95/D98/D96 (~y40). The denser middle
    # cluster (D99/D100/D101/D102/D104/D106/D28/D12/D3...) has tilted/packed labels -> deferred.
    # (converted to untraced footprints)
    # top band row @ y≈55 (reliable tight-crop read: pitch 16, incl. D28). Corrects an earlier
    # y40/cramped placement of this row that came from a lower-res crop.
    # (D95/D94/D98/D96 -> untraced footprints in the ВГ93-quadrant 4-row layout; the old top-band
    # box positions were a drawing misread of this area -- see UNTRACED.)
    # lower-left chips (toward-76): completes the CPU cluster (D107 below D4) + the lower-left
    # corner (D52, D30). Read off the drawing; placement-only outlines.
    # (D107 -> untraced КР580ВА86 footprint, the 2nd of the photo's stacked ВА86 pair)
    # lower-left corner (read off the drawing): D30/D13/D105 = a horizontal column at x≈30; D52
    # vertical at x≈59. (D13/D30/D105 all -> footprints now.)
    # (D52 -> untraced footprint)
    # baud-rate chain re-read from a tight crop: a row at y≈82 (BELOW the y55 band, not the y54 I
    # (D101/D102/D100 -> untraced footprints in the ВГ93-quadrant rows; the earlier "baud row y82"
    # boxes were part of the same drawing misread. NOTE: tape-serial.md predicted ИЕ11/ИМ1/ИР9 for
    # the baud chain -- the real quadrant has ИЕ7/ЛН3/ТМ2, so either the chain lives elsewhere or
    # the sheet-3 read needs revisiting; D99=ИР9 (296,82) kept but now suspect.)
    # (D106 -> untraced К155АГ3 footprint, photo-confirmed)
    # (D32/D12/D3 are now net-modeled serial-driver footprints -- see PLACE.)
    silk_box(182, 22.5, 210, 30, "X3")   # serial edge connector, right of X2 (emaplaat)
    silk_box(72, 278, 98, 286, "X8")     # power connector, bottom-left (+5/GND/+12/-12; 61/62/60/59)     # RS-232 serial connector (drivers D14/D32/D3/D12 -> here)
    # clock/divider cluster fill (read off the drawing): D41 (≈251,155, paired with D40, horizontal),
    # D37 (≈261,200, between D36/D33), D34 (≈305,176, right edge).
    # (D41 -> untraced К555ИР16 footprint, owner-identified; D34/D37 -> footprints)
    # (D92 -> untraced К555ЛЕ4 footprint; likely the REAL Φ1/Φ2 phase generator core (cross-coupled
    # NORs) -- nets to trace, then net-model)
    # (D25/D23/D24/D29 bus transceivers are now net-modeled footprints -- see PLACE -- not outlines.)
    # (D9 -> untraced К555ИД7 footprint, owner-identified)
    BW, BH = BX1-BX0, BY1-BY0

    # ---- pre-routed escapes for the 4 X1 links freerouting deterministically fails on ----
    # D24 (addr-hi ВА87) pins 12-15 -> X1 cols 117/118 rows B/C (-ADRF/E/D/C). The corner under
    # X1's 96-pad field is too congested for the autorouter (same 4 unrouted across runs/seeds), so
    # these are laid on the EMPTY board (collision-free by construction: B.Cu verticals, F.Cu
    # collector rows y=33..35.4, between-column lane entries) and exported as existing wiring --
    # the router routes the other ~1048 around them.
    def _wire(net_name, pts, layers):
        net = board.FindNet(net_name)
        if net is None: return
        for (x1, y1), (x2, y2), lay in zip(pts, pts[1:], layers):
            t = pcbnew.PCB_TRACK(board)
            t.SetStart(pcbnew.VECTOR2I(pcbnew.FromMM(x1), pcbnew.FromMM(y1)))
            t.SetEnd(pcbnew.VECTOR2I(pcbnew.FromMM(x2), pcbnew.FromMM(y2)))
            t.SetLayer(lay); t.SetWidth(pcbnew.FromMM(0.25)); t.SetNet(net)
            t.SetLocked(True)   # -> DSN "(type protect)" so freerouting keeps the escape
            board.Add(t)
    def _via(net_name, x, y):
        net = board.FindNet(net_name)
        if net is None: return
        v = pcbnew.PCB_VIA(board); v.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(x), pcbnew.FromMM(y)))
        v.SetWidth(pcbnew.FromMM(0.6)); v.SetDrill(pcbnew.FromMM(0.3)); v.SetNet(net)
        v.SetLocked(True)
        board.Add(v)
    B, F = pcbnew.B_Cu, pcbnew.F_Cu
    # ADRF: D24.12 (94.89,55.19) -> X1.117B (62.25,27)
    _wire('ADRF_N', [(94.89,55.19),(94.89,33.0),(61.0,33.0),(61.0,28.25),(62.25,28.25),(62.25,27.0)],
          [B, F, B, B, B])
    _via('ADRF_N', 94.89,33.0); _via('ADRF_N', 61.0,33.0)
    # ADRE: D24.13 (92.35,55.19) -> X1.117C (62.25,29.5)
    _wire('ADRE_N', [(92.35,55.19),(92.35,33.8),(62.25,33.8),(62.25,29.5)], [B, F, B])
    _via('ADRE_N', 92.35,33.8); _via('ADRE_N', 62.25,33.8)
    # ADRD: D24.14 (89.81,55.19) -> X1.118B (64.75,27)
    _wire('ADRD_N', [(89.81,55.19),(89.81,34.6),(66.0,34.6),(66.0,28.25),(64.75,28.25),(64.75,27.0)],
          [B, F, B, B, B])
    _via('ADRD_N', 89.81,34.6); _via('ADRD_N', 66.0,34.6)
    # ADRC: D24.15 (87.27,55.19) -> X1.118C (64.75,29.5)
    _wire('ADRC_N', [(87.27,55.19),(87.27,35.4),(64.75,35.4),(64.75,29.5)], [B, F, B])
    _via('ADRC_N', 87.27,35.4); _via('ADRC_N', 64.75,35.4)
    # PHI1 escape REMOVED: hand-placed locked wires here create degenerate trace geometry that
    # livelocks freerouting's PolylineTrace.combine (bounded-guard build churns forever, stock
    # build stack-overflows). The ADR pre-routes are fine; PHI1's occasional single-link miss is
    # cheaper to fix by a placement nudge + re-roll than by poisoning the DSN.
    # DB5/DB6 pre-route bars REMOVED (were: D58.6->D89.14 / D58.7->D42.4 via the y~286-287 band).
    # Two reasons: (a) freerouting crashes on them (PolylineTrace.combine infinite recursion) and
    # poisons its SES echo of them ((type protect) wires that make pcbnew.ImportSpecctraSES return
    # False -- strip those blocks from the SES and the import succeeds); (b) the bottom chip row
    # moved up to y=275 to match the real board's ~11 mm edge margin, which opens the very routing
    # channel below the row that the original board uses -- the router gets a fair shot now. If the
    # links still fail deterministically, re-add bars with updated pad coords and use the
    # strip-protect-wires + re-inject flow (see finalize_route.py notes).

    board.BuildListOfNets()
    pcbnew.SaveBoard(out, board)
    # use the GOST CAD font for silkscreen text so the Cyrillic case markings render fully
    # (KiCad's built-in stroke font drops В/М glyphs). The face is resolved from ~/Library/Fonts.
    txt = open(out, encoding="utf-8").read().replace('(font', '(font (face "GOST CAD KK")')
    open(out, "w", encoding="utf-8").write(txt)
    n_pos = len(placed) + len(outline_chips)
    allrefs = list(placed) + outline_chips
    dups = sorted({r for r in allrefs if allrefs.count(r) > 1})
    print(f"wrote {out}: {len(placed)} footprints, {board.GetNetCount()} nets, "
          f"{assigned} pad-net assignments, board {BW:.0f}x{BH:.0f} mm (GOST silkscreen font)")
    print(f"  chip positions: {len(placed)} net-modeled + {len(outline_chips)} placement outlines "
          f"= {n_pos} / ~101 BOM ICs ({100*n_pos//101}%)")
    if dups: print(f"  WARNING: {len(dups)} duplicate refdes placed twice -> {dups}")
    # outline-overlap guard: the silk placement outlines aren't footprints, so validate_placement.py
    # (which checks footprints) can't catch outline collisions. Check them here.
    def hit(a, b):     # rect intersection (boxes given x0<x1, y0<y1)
        return a[0] < b[2] and a[2] > b[0] and a[1] < b[3] and a[3] > b[1]
    T = pcbnew.ToMM
    fp_boxes = []      # modeled-footprint bboxes (pads/graphics, no text) in mm
    for ref, fp in placed.items():
        b = fp.GetBoundingBox(False, False)
        fp_boxes.append((T(b.GetLeft()), T(b.GetTop()), T(b.GetRight()), T(b.GetBottom()), ref))
    ov = []
    for i in range(len(outline_boxes)):           # outline vs outline
        for j in range(i+1, len(outline_boxes)):
            if hit(outline_boxes[i], outline_boxes[j]):
                ov.append(f"{outline_boxes[i][4]}~{outline_boxes[j][4]}")
    for ob in outline_boxes:                       # outline vs modeled footprint
        for fb in fp_boxes:
            if ob[4] == fb[4]:
                continue                           # a connector's label box over its OWN footprint
            if hit(ob, fb): ov.append(f"{ob[4]}~{fb[4]}")
    print(f"  outline-overlap check: {'PASS' if not ov else 'FAIL -> ' + ', '.join(ov)}")

if __name__ == "__main__":
    main()
