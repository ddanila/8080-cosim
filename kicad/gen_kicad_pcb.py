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
import os, sys, json, pcbnew

SILK_FONT_FACE = "GOST type B italic"

def footprint_root():
    candidates = [
        os.environ.get("KICAD_FOOTPRINT_DIR"),
        "/usr/share/kicad/footprints",
        ("/opt/homebrew/Caskroom/kicad/10.0.4/KiCad/KiCad.app/Contents/"
         "SharedSupport/footprints"),
    ]
    for path in candidates:
        if path and os.path.isdir(path):
            return path
    raise RuntimeError("KiCad footprint directory not found; set KICAD_FOOTPRINT_DIR")

FOOTPRINT_ROOT = footprint_root()
DIP_LIB = os.path.join(FOOTPRINT_ROOT, "Package_DIP.pretty")

# chip type -> DIP footprint (real package widths; 600-mil for >=24-pin MSI)
FP = {
    'CPU8080':'DIP-40_W15.24mm', 'PPI8255':'DIP-40_W15.24mm', 'FDC1793':'DIP-40_W15.24mm',
    'SYS8238':'DIP-28_W15.24mm', 'EPROM8K':'DIP-28_W15.24mm', 'USART8251':'DIP-28_W15.24mm',
    'PIC8259':'DIP-28_W15.24mm', 'PIT8253':'DIP-24_W15.24mm', 'BUF8286':'DIP-20_W7.62mm',
    'AP2':'DIP-8_W7.62mm', 'LA18':'DIP-8_W7.62mm',   # DIP-8 confirmed by board photos
    'TM2_DFF':'DIP-14_W7.62mm',
    'LN3_OC_INV':'DIP-14_W7.62mm', 'KP12_MUX':'DIP-16_W7.62mm',
    'LP11_BUF':'DIP-16_W7.62mm',
}
SHARED = FOOTPRINT_ROOT + "/"
PASSIVE_FP = {
    'R_AXIAL': ('Resistor_THT.pretty',  'R_Axial_DIN0207_L6.3mm_D2.5mm_P7.62mm_Horizontal'),
    'C_KM':    ('Capacitor_THT.pretty', 'C_Disc_D4.7mm_W2.5mm_P5.00mm'),
    'C_ELEC':  ('Capacitor_THT.pretty', 'CP_Radial_D5.0mm_P2.00mm'),
    'D_DIODE': ('Diode_THT.pretty',     'D_DO-35_SOD27_P7.62mm_Horizontal'),
    'SW':      ('Connector_PinHeader_2.54mm.pretty', 'PinHeader_1x02_P2.54mm_Vertical'),
    'JUMPER3': ('Connector_PinHeader_2.54mm.pretty', 'PinHeader_1x03_P2.54mm_Vertical'),   # Е-family config links
    'XTAL':    ('Crystal.pretty',       'Crystal_HC49-U_Horizontal'),   # РК-171 flat can, lying -- closest stock footprint
    'C_TRIM':  ('Capacitor_THT.pretty', 'C_Disc_D7.5mm_W4.4mm_P5.00mm'), # КТ4-23 trimmer stand-in (no trimmer lib in stock KiCad)
    'R_TRIM':  ('Potentiometer_THT.pretty', 'Potentiometer_Piher_PT-10-V10_Vertical'),  # R73 = СП3-22б 4.7k (ВП лист 7) stand-in
    'SW_DIP6': ('Button_Switch_THT.pretty', 'SW_DIP_SPSTx06_Slide_9.78x17.42mm_W7.62mm_P2.54mm'),  # S3 video-config bank
    'JUMPER4': ('Connector_PinHeader_2.54mm.pretty', 'PinHeader_1x04_P2.54mm_Vertical'),  # Е13 strap
    'JUMPER2': ('Connector_PinHeader_2.54mm.pretty', 'PinHeader_1x02_P2.54mm_Vertical'),  # Е5 -5V array link
    'Q_TO92':  ('Package_TO_SOT_THT.pretty', 'TO-92_Inline'),                  # КТ315/КТ325 (flat KT-13 pkg; TO-92 stand-in)
    'L_RADIAL':('Inductor_THT.pretty', 'L_Radial_D7.0mm_P3.00mm'),             # L1 RF coil (tunable core; stand-in)
    'VIDEO_CONN': ('Connector_PinHeader_2.54mm.pretty', 'PinHeader_1x02_P2.54mm_Vertical'),  # X7 video socket stand-in (601/602)
    'RF_CONN':    ('Connector_PinHeader_2.54mm.pretty', 'PinHeader_1x02_P2.54mm_Vertical'),  # X6 RF socket stand-in (701/702)
    'WIRE_PAD':   ('TestPoint.pretty', 'TestPoint_THTPad_D2.0mm_Drill1.0mm'),  # factory numbered flying-wire landings
}
PASSIVE_FP_REF = {
    'R94': ('Resistor_THT.pretty', 'R_Axial_DIN0207_L6.3mm_D2.5mm_P10.16mm_Horizontal'),
    'R104': ('Resistor_THT.pretty', 'R_Axial_DIN0411_L9.9mm_D3.6mm_P12.70mm_Horizontal'),
    'R18': ('Resistor_THT.pretty', 'R_Axial_DIN0207_L6.3mm_D2.5mm_P10.16mm_Horizontal'),
    'R30': ('Resistor_THT.pretty', 'R_Axial_DIN0411_L9.9mm_D3.6mm_P12.70mm_Horizontal'),
}
# traced-network passives [scan] + decoupling C35-C72 (BOM count; chip-adjacent positions assumed)
PASSIVE_PLACE = {
    'R19':(44.4,220.7,90),'VD5':(49.4,231.5,90),'C31':(23,228.0,90),'C32':(23,235.0,90),'C33':(24.5,244.0,90),   # corner re-layout: the assumed grid squatted the crystal's real estate (photo-true corner)
    'R3':(12,200.8,0),'R4':(16.9,209.2,90),'R20':(51.9,194.2,0),'C21':(48.5,205.9,0),'C1':(18.4,194.8,0),
    'A17':(115.8,27.1,0),  # two-sided owner photos, transferred from top mounting hole (114.4,13.3)
    # Registered component/solder views show one 2.5 mm-pitch X3 cable row;
    # sheet 1 labels the left/right ends A21/A32.
    'A21':(173.70,15.2,0),'A22':(176.24,15.2,0),'A23':(178.78,15.2,0),'A24':(181.32,15.2,0),
    'A25':(183.86,15.2,0),'A26':(186.40,15.2,0),'A27':(188.94,15.2,0),'A28':(191.48,15.2,0),
    'A29':(194.02,15.2,0),'A30':(196.56,15.2,0),'A31':(199.10,15.2,0),'A32':(201.64,15.2,0),
    'R104':(194.34,25.87,0), # registered photo terminals; 12.7 mm pitch, A21 side at left
    'R30':(203.74,38.37,270), # registered photo terminals; S_OC at top, ground at bottom
    'R18':(215.20,64.59,278), # registered photo terminals; S_OC at top, SER_TXD at bottom
    # X9 is bracket-mounted. These are its reversed-ribbon PCB landings:
    # A45->X9.14 through A58->X9.1 (factory sheets 4-5).
    'A45':(224.5,262.0,0),'A46':(222.0,262.0,0),'A47':(219.5,262.0,0),'A48':(217.0,262.0,0),
    'A49':(214.5,262.0,0),'A50':(212.0,262.0,0),'A51':(209.5,262.0,0),'A52':(207.0,262.0,0),
    'A53':(204.5,262.0,0),'A54':(202.0,262.0,0),'A55':(199.5,262.0,0),'A56':(197.0,262.0,0),
    'A57':(194.5,262.0,0),'A58':(192.0,262.0,0),
    # X8 is bracket-mounted; these four points terminate its six-conductor
    # power cable (A61 +5 V and A62 GND each take two conductors).
    'A59':(34.0,252.6,0),'A60':(29.0,252.6,0),'A61':(24.0,252.6,0),'A62':(19.0,252.6,0),
    'R94':(297.6,56.4,270), # .009 assembly + owner photo; pin 1 is upper D98.3 end
    'R5':(44.0,187.0,90),'R6':(47.0,187.0,90),'R29':(50.0,187.0,90),  # D30 READY row, assembly drawing
    'R38':(121.4,249.1,90),'R39':(230.5,192.5,0),
    'Z1':(79.4,243.5,90),    # РК-171 crystal at its PHOTO-TRUE spot (edge-relative measurement, straight-on corner crop)
    'S3':(63.5,182.4,0),   # video-config DIP-6 [emaplaat 'S3' box]
    'E13':(104,188,0),     # video strap posts [emaplaat E13 zone]
    'E14':(95,170,0),      # video-mux G strap [emaplaat E11/E12 post block zone]
    'E4':(39.9,226.5,0),'E5':(50.5,224.0,0),'C34':(47,242,0),   # E4/E5 СБ-true (poz pads read); C34 not yet located on the СБ [approx]
    # ---- analog video/RF corner: REAL zone = mid-right x260-300 y95-125 per the СБ assembly
    # drawing (7.102.100; VT2/VT3/VT4/R73/VD3 read precisely, R6x/C grid improved-approx) ----
    'VT4':(264.3,98.6,0),'R73':(282.1,102.3,0),'VT3':(295.8,102.3,0),'VT2':(280.7,126.4,0),'VD3':(299.0,119.6,90),
    'R72':(294.4,95.3,0),'R74':(292.3,102.1,90),'R75':(264.7,104.6,0),'C14':(272.2,102.3,90),'C11':(268.232,93.540,90),'R85':(274.7,87.4,0),'C94':(284.4,119.6,90),
    # R6x grid: slot positions СБ-true (crops sb_analog2/sb_r6x_right: trio y116.9 at x288.3/291.0/293.8,
    # trio y126.2 same x, singles ~(297.5,117.5)/(299.4,120.4)); refdes-to-slot within the grid is APPROX —
    # the rotated labels sit at the scan's resolution floor (blocked: needs macro photo / owner read)
    'R62':(263,115,90),'R63':(266.5,115,90),'R64':(270,115,90),'R65':(276.9,117.2,90),'R66':(293.8,127.2,90),
    'R67':(288.3,116.4,90),'R68':(291.0,116.4,90),'R69':(293.8,116.4,90),'R70':(288.3,127.2,90),'R71':(291.0,127.2,90),
    # Factory lower-FDC drawing registered to photo-fitted D95/D99 and
    # D101/D97/D102 centres: C11/C15 are vertical between their IC pairs.
    'C9':(275,95,0),'C10':(283.5,112,90),'C12':(254.6,95.6,0),'C13':(249.5,99.0,90),'C15':(280.230,110.120,90),
    'R76':(272,125,0),'R77':(271.5,132.5,0),'L1':(298.9,129.2,0),   # L1 = the СБ circle part at (298.9,129.2); old approx sat on VT2
    'VT1':(247.8,213.8,0),  # КТ972А beeper driver (ВП л.8; СБ position; wiring = sheet-1 beeper zone [pending])
    'S4':(245.0,80.2,0),    # ВДМ1-2 microswitch (СБ position, .100; present on .158 photos; wiring pending)
    'X7':(258.5,6,0),   # video socket (СБ top edge; contact 601/602)
    'X6':(288,6,0),     # RF socket (СБ top edge, поз.18 ring; contact 701/702)
    'E1':(113,207,0),      # MA7/DRAM-size strap [emaplaat E1 post]
    'R49':(204.1,181.7,0),'R50':(204.1,186,0),'R51':(204.1,190.3,0),'R52':(204.1,194.6,0),   # 100R strobe series [sheet-2; emaplaat x204 column]
    'R53':(204.1,199,0),'R54':(204.1,203.3,0),'R55':(204.1,207.6,0),'R56':(204.1,211.9,0),   # 5.1k strobe pullups -> rail E
    'R57':(204.1,216.2,0),'R58':(204.1,220.5,0),   # R57 = CAS rail-15 series (<- D36.11), R58 = rail-15 5.1k pullup -> E [bite-2; same column, position approx]
    'R40':(74,176,90),'R41':(77,176,90),'R42':(80,176,90),'R43':(83,176,90),'R44':(86,176,90),'R45':(89,176,90),   # S3 pullup row [drawn; position approx]
    'C73':(58,241.5,0),
    'E2':(65.5,215.5,0),'E3':(49.5,215.5,0),   # beside D52's body (x52-62), not inside it   # СБ-true posts beside D52 (old 217.5 was a mis-entered routing guess)    # 4/20 pF trimmer (sheet-2: Z1+C73+R32 osc group; '8811' disc on the photos)
    'R17':(111.4,119.0,90),'C99':(105.1,119.8,0),   # D9.G1 RC deglitch -- SB-true spots (crop sb_decode)
    'R90':(251.6,216.1,90),'VD4':(254.1,216.1,90),'R91':(256.4,216.1,90),'R48':(245.1,207.4,0),'R60':(253.9,202.7,0),   # beeper cluster SB-true (crop sb_beeper); R60 = FRAME INT pullup between wire posts 2/1
    # D56 AG3 RCs СБ-true (crops sb_d56rc/sb_westpair): R59+C8 pair WEST of D56 (between D103 and D56),
    # C7+R47 pair EAST of D56; R61 not found on the СБ in the checked zones [stays approx]
    'R47':(296.5,166.8,90),'C7':(294.1,166.6,90),'R59':(280.1,174.0,90),'C8':(280.1,184.5,90),'R61':(293.5,189.0,0),
    'R11':(70.0,101.0,90),'R12':(73.5,101.0,90),'R13':(84.5,122.0,90),'R14':(88.0,122.0,90),   # 1k pullups on the D6 OC rails (ROM/RAM/REV/-RAMOUTEN), decode cluster between D6 and D8 [approx]
}
_DEC = {  # DRAM-field decaps: emaplaat zigzag (per column, top->bottom)
    'C35':(119.6,120.9,0),'C36':(119.6,145.6,0),'C37':(119.6,170.7,0),'C38':(119.6,195.8,0),
    'C54':(130.9,120.9,0),'C55':(130.9,145.6,0),'C56':(130.9,170.7,0),'C57':(130.9,195.8,0),
    'C39':(142.3,120.9,0),'C40':(142.3,145.6,0),'C41':(142.3,170.7,0),'C42':(142.3,195.8,0),
    'C58':(153.7,120.9,0),'C59':(153.7,145.6,0),'C60':(153.7,170.7,0),'C61':(153.7,195.8,0),
    'C43':(164.7,120.9,0),'C44':(164.7,145.6,0),'C45':(164.7,170.7,0),'C46':(164.7,195.8,0),
    'C62':(176.1,120.9,0),'C63':(176.1,145.6,0),'C64':(176.1,170.7,0),'C65':(176.1,195.8,0),
    'C47':(187.1,120.9,0),'C48':(187.1,145.6,0),'C49':(187.1,170.7,0),'C50':(187.1,195.8,0),
    'C66':(198.4,120.9,0),'C67':(198.4,145.6,0),'C68':(198.4,170.7,0),'C69':(194.5,195.8,0),
    # non-field decaps (bus band / I/O / clock zones)
    'C51':(240,255,0),'C52':(162,40,0),'C53':(214,252,0),
    'C70':(216,150,0),'C71':(216,175,0),'C72':(216,200,0),
}
PASSIVE_PLACE.update(_DEC)

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
    'RE3_PROM':'К155РЕ3',  'RE3_PROM_092':'К155РЕ3', 'TM2_DFF':'КМ555ТМ2',
    'LN3_OC_INV':'К155ЛН3', 'KP12_MUX':'К555КП12', 'LP11_BUF':'К155ЛП11',
    'CT16_CTR':'КР531ИЕ17',   'CLK_PHASE':'К155ЛН5',           # pinned via repo tracing (clock-subsystem.md / memory.md)
    'VABUS':'КР580ВА87',    'IR82':'КР580ИР82',      'IR16':'К155ИР16',
    'TL2':'К155ТЛ2',        'LN1_DUAL':'К531ЛН1',    'AP2':'К170АП2',
    'UP2':'К170УП2',        'LA18':'К155ЛА18',    'LN2':'К561ЛН2',
}
MARK_REF = {'D29':'КР580ВА86',   # the ВА86 among the VABUS transceivers (D23-25 = ВА87)
            'D37':'КР1533ЛА3', 'D39':'КР1533ЛА3',   # real series per board-#2 photos
            'D7':'КР1533ЛА3',   # owner-read off the real board (was assumed К555; ALS vs LS -- same logic/pinout, marking only)
            'D56':'К155АГ3',    # board-#2 row-4 АГ3s are К155 8901 (BOM said КМ555АГ3; real board wins, D7 precedent)
            'D97':'К155АГ3', 'D99':'К155АГ3', 'D102':'К155АГ3',  # owner-photo FDC row, 8901 batch
            'D2':'КР556РТ4А',    # D2 is the 2nd РТ4 PROM (photo: both socketed by the CPU), not a 74138
            'D105':'К155ЛА3'}    # official .009 BOM/assembly marking; sheet-1 wait-chain gate

BOARD_SILK_NOTES = [
    ("8080 HEART", 32, 134, 0),
    ("BOOT ROM FIELD", 93, 72, 0),
    ("DRAM MEMORY FIELD", 160, 132, 0),
    ("VIDEO TIMING", 96, 188, 0),
    ("CLOCK MILL", 256, 127, 0),
    ("FDC OUTPOST", 270, 18, 0),
    ("SERIAL / TAPE", 201, 37, 0),
    ("KEYBOARD SCANNER", 222, 246, 0),
    ("POWER EDGE", 58, 248, 0),
    ("EXPANSION BUS", 62, 36, 0),
]

def patch_text_fonts(path):
    lines = open(path, encoding="utf-8").read().splitlines()
    patched = []
    for line in lines:
        patched.append(line)
        if line.strip() == "(font":
            indent = line[:len(line) - len(line.lstrip())] + "\t"
            patched.append(f'{indent}(face "{SILK_FONT_FACE}")')
            patched.append(f"{indent}(italic yes)")
    open(path, "w", encoding="utf-8").write("\n".join(patched) + "\n")

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
    'D27':(151.7,35.7,90),
    # ROM row (vertical 28-pin sockets; D15/D16 populated, D17-D22 empty) + the USART D11 at the
    # right end. Exact drawing coords (verified frame): sockets at y≈105, ~32 mm pitch.
    'D15':(23.5,70.8,0), 'D16':(42.3,70.8,0), 'D11':(185.5,65.7,0),   # ROM sockets y86, ~21mm pitch; D11 (USART) at its real spot right of the sockets
    # DRAM bank (565РУ3Г, vertical 16-pin): the top array row D67..D60, read precisely off the
    # drawing -- x 127..238, ~16 mm pitch (was 102..235/pitch-19, ~25 mm too far left at D67). The
    # left column (unmodeled D50 @ ~112) lines up with the D48/D49 muxes below it.
    'D67':(119.6,133.1,0),'D66':(130.9,133.1,0),'D65':(142.3,133.1,0),'D64':(153.7,133.1,0),
    'D63':(164.7,133.1,0),'D62':(176.1,133.1,0),'D61':(187.1,133.1,0),'D60':(198.4,133.1,0),   # bank0 at 133.1: the emaplaat decap zigzag (C35 124.3 above it, C36 145.6 below) brackets the row; the old y148 read collided with the zigzag
    # I/O block (PIT 8253 + PPI 8255) -- the drawing puts these on the RIGHT/bottom-right, NOT the
    # top: PITs D57/D55/D54 stack down the right edge (x~292, pulled in from the ~296 read to fit
    # the 310 cut), and PPI D26 sits bottom-right just left of D54. (Was a fictional top I/O row.)
    'D57':(274.9,206.6,90),'D55':(274.9,229.2,90),'D54':(274.7,251,90),'D26':(232,251,90),   # stack -7mm: edge-relative re-measure on the 9.50 y-scale (pitch 24 confirmed; absolute y was inflated)
    # CPU is a tall VERTICAL chip in the lower-left (per emaplaat: D1 + D4/D2/D107 stand there).
    # Exact verified-frame read: D1 center ≈ (35,176); D4/D2 vertical just right of it (≈y158).
    # D2 input compensates the stock footprint anchor offset so the saved
    # photo-corrected KiCad position remains (70.010,129.905), notch upward.
    'D1':(32.3,157,0),'D4':(51.1,142.4,0),'D2':(73.815,138.795,0),'D8':(89.5,102.4,0),'D9':(114.0,103.0,0),   # D8 = socketed РЕ3 PROM; D9 = К555ИД7 IO decoder
    # video address counters (ИЕ7) + DRAM addr muxes (КП14) live in the LEFT columns of the DRAM
    # array (read off the drawing): two sub-rows at y217 / y242 descending into the array, with
    # D46/D44/D48 over D47/D45/D49 -- NOT a separate row up by the bus. (~13 mm pitch, vertical.)
    'D46':(80.7,198.5,0),'D44':(93.3,198.5,0),'D48':(105.6,198.5,0),
    'D47':(80.7,223,0),'D45':(93.3,223,0),'D49':(105.6,223,0),
    # video-output chain -- relocated to the right-centre with the clock cluster (read off the
    # drawing): RAS/CAS decode D53 sits below D36; IE10 ctr D103 below D39; AG3 one-shot D56 far
    # right (raw read hit the 310 edge -> pulled in 5 mm so the DIP stays on-board). All vertical.
    'D53':(227.8,204.9,0),'D52':(57.2,211.6,0),'D50':(106.2,133.1,0),'D51':(106.2,158.2,0),'D92':(260,159.2,0),'D103':(273.0,181.8,0),   # D51 = row-2 mux, left DRAM column (emaplaat); D52 = 5th КП14; D50/D92 net-carrying (beeper wires 10/11/13)
    'D56':(287.8,180,0),    # АГ3 at its DRAWN spot after all: the "К555ЛУ?/1068" photo read there was
                          # К155АГ3 8901 UPSIDE DOWN (1068 = 8901 rotated). Quadrant round-trip reverted.
    # bus interface band (read off the drawing): a horizontal row in the gap BETWEEN the ROM row
    # and the DRAM array -- D5 (8238) far left, then D6 / D7, and the wide D10 (8259).
    # This was a fictional bottom-centre row before; the muxes above now occupy that freed space.
    # D5 at its СБ box (y92-106; old 114.1 clipped the ROM sockets); D6/D7/D10 row at y114.1
    # (old 116.7-118 dips clipped the x-decap band at 124.3 and bank0 at 133.1)
    'D5':(31.2,99.2,90),'D6':(63.8,114.1,90),'D7':(137.8,110.0,90),
    'D10':(192.44,110.08,90),  # КР580ВН59 local affine photo fit; old centre projected onto adjacent resistors/body
    'D107':(51.1,168.2,0),   # 3rd ВА86 (=U_BUFL) directly below D4 [emaplaat + owner photo]
    'D30':(32.9,189.5,90),   # READY flip-flop; section A traced, section B remains boundary
    'D105':(31.9,215.5,90),  # wait/MRD NAND below D13; official .009 assembly position
    # clock subsystem -- RELOCATED to its real right-centre region, read off the assembly drawing
    # via the validated frame (the divider/gate mesh sits right of the DRAM array near D40/D41/D34,
    # not a fictional bottom-left row). D40 (СТ16) is drawn horizontal -> rot 90; the ЛА/ЛН gates
    # D38/D39/D33/D36/D35 are drawn vertical -> rot 0. D59 (osc) is still approximate (the drawing
    # puts it bottom-centre by the transformer -- read it next pass).
    'D40':(258.0,125.6,90),'D41':(235,140.9,270),'D38':(233.4,156.6,0),'D39':(284.3,156.1,0),   # D41 net-modeled now (sheet-2 LATCH chain); К555ИР16 photo-confirmed, label-down   # D39 294->280: photo shows ЛА3+ЛП5 side by side, ЛП5 (D34) owns the ~294 slot
    'D34':(297.5,143.2,0),   # ЛП5 XOR pulse gen [sheet-2]
    # Inputs below compensate the stock footprint anchor/bounding-box offset so
    # the saved KiCad footprint positions remain the photo-guarded coordinates
    # D94=(229.275,38.110), D100=(257.650,37.400), D98=(290.000,37.400).
    'D93':(248,70,0),'D94':(238.165,34.305,90),'D100':(269.08,33.595,90),
    # Registered component fits: D28 centre is 15.064 mm right / 1.442 mm
    # above D106; D96 is another 14.451 mm right / 0.240 mm below D28.
    'D98':(298.89,33.595,90),'D106':(262,74,0),'D28':(277.064,72.558,0),'D96':(291.515,72.798,0),
    # D95/D101/D97/D102 share one raw component photograph. Package-local
    # scales establish their relative centres; the visible x=3682 px right
    # board edge anchors the row inside the physical 310 mm outline.
    'D95':(256.000,93.000,90),'D97':(268.604,110.273,90),'D101':(244.810,110.380,90),
    'D99':(279.895,93.451,90),'D102':(292.567,110.024,90),
    'D36':(228.1,180.4,180),'D33':(258,180,180),'D35':(241.0,200.5,0),   # D36/D33 notch-DOWN (emaplaat+photo)   # D36 +3mm right to clear the DRAM right column; D35 up 4mm to clear D7
    'D59':(106.6,257,90),   # osc ЛН1 -- read off the drawing: horizontal, bottom-centre by transformer Z
                          # (bottom row 281->275: photo shows ~11 mm body-to-edge margin; 281 put pads 3 mm from the cut)
    # NET-MODELED this session (Phase-B) -- promoted from placement-outlines to real footprints at
    # their traced drawing positions: bus transceivers (top band, horizontal) + bottom row.
    # buffer row at СБ y37.1 (sb_left_0: D25/D23 boxes y34.7-39.5; the old 53.4 sat on the ROM sockets)
    'D25':(29.8,37.1,90),'D23':(54.6,37.1,90),'D24':(81.6,37.1,90),'D29':(108.5,37.1,90),
    'D42':(136,259,90),'D43':(159.6,259.5,90),'D58':(183.0,243.1,90),   # bottom row -6mm: photo-1's y-scale is 9.50 px/mm (board spans 2528px/266mm), not the 9.87 x-scale -- edge-relative re-measure
    'D37':(241.7,181,180),   # ЛА3 D42-serial inverter; notch-DOWN (emaplaat+photo)
    'D13':(31.9,205.3,90),
}
# remaining DRAM rows D68-D91 -- now net-modeled sockets -> real footprints at their
# array positions. D84-D91 are populated on the .158/.009 target; D68-D83 are empty.
_DCOLS = [119.6, 130.9, 142.3, 153.7, 164.7, 176.1, 187.1, 198.4]
# rows re-anchored to bank-0's precise y=148 (the old ladder started at 158.2 = bank-0's PRE-re-base
# y; leaving banks 1-3 unshifted overlapped bank 0 with bank 1 -> 192 pad shorts, route-blocking)
for _ry, _refs in [(158.2, range(75, 67, -1)), (183.3, range(83, 75, -1)), (208.4, range(91, 83, -1))]:
    for _cx, _r in zip(_DCOLS, _refs): PLACE[f'D{_r}'] = (_cx, _ry, 0)
# unpopulated ROM sockets D17-D22 (now net-modeled) -> footprints in the ROM row (y86, ~21mm pitch)
for _i, _x in zip(range(17, 23), (62.9, 82.6, 102.6, 122.5, 142.6, 162.5)): PLACE[f'D{_i}'] = (_x, 70.8, 0)   # СБ: all 8 sockets one row at y~70.8 (old 83.4 clipped D9/D5)
# serial-port cluster (net-modeled): REAL positions read off the emaplaat (relative to the D11
# anchor): D104/D32/D14 = the column under the X3 serial connector; D12/D3 right of D11.
# serial column right of СБ-true D11 (D11 pins span x~177-194; D12 begins x~201):
# D104 tucked above the column, D32/D14 at their emaplaat slots
PLACE['D104'] = (199.5, 30.5, 0)
PLACE['D32'] = (198.9, 48.3, 0); PLACE['D14'] = (198.9, 58.7, 0)
PLACE['D12']  = (206.3, 80.9, 0); PLACE['D3']  = (205.8, 96.4, 0)
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
        lib, fpn = PASSIVE_FP_REF.get(ref, PASSIVE_FP[typ])
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
        for t, visible, sz, dy in ((fp.Reference(), True, 1.1, 2.6 if flip else -2.6),
                                   (fp.Value(), show_val, 0.9, -2.4 if flip else 2.4)):
            t.SetVisible(visible)
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
    CONN = {'EXPANSION_CONN', 'SERIAL_CONN', 'POWER_CONN', 'PAR_CONN', 'KBD_CONN'}  # PAR/KBD: X2/X9 are made by make_conn -- placing them here too duplicates the refdes and silently kills the Specctra DSN export
    # S1 is the reset pushbutton on the top connector bracket. Factory wire-table
    # rows 11/12 connect its terminals to remote board landings А:17/А:18; it is
    # retained in the schematic but must never become a PCB header footprint.
    OFF_BOARD = {'S1', 'X3', 'X8', 'X9'}
    # place per the assembly-drawing map; any chip not in PLACE -> fallback grid below
    row = 0
    for ref in chips:
        t = chips[ref]['type']
        if t in CONN or ref in OFF_BOARD: continue
        if t in PASSIVE_FP:
            if ref in PASSIVE_PLACE:
                x, y, rot = PASSIVE_PLACE[ref]; add_passive(ref, x, y, rot)
            continue
        if ref in PLACE:
            x, y, rot = PLACE[ref]; add_chip(ref, x, y, rot)
    col = 0
    for ref in sorted(chips):
        if ref in OFF_BOARD or chips[ref]['type'] in CONN or chips[ref]['type'] in PASSIVE_FP or ref in PLACE: continue
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
            x1_pads[f'1{col:02d}{row}'] = (px, 6.6 + ri * 2.5)
    make_conn('X1', 61, 9.1, x1_pads)
    # X3 is bracket-mounted. A21..A32 above are the photographed PCB cable
    # landings; the old 2x8 edge-connector stand-in was both provisional and
    # physically wrong.
    # X2: СНП59-30 parallel connector, top edge [emaplaat x~118-169].
    # Sheet-1 traces PPI signal codes 201-226 plus +5 V contacts 227/229/230.
    x2_codes = ['201','202','203','204','205','206','207','208','209','210','211','212','213',
                '215','217','218','219','220','221','222','223','224','225','226']
    x2_pads = {}
    for ci, code in enumerate(x2_codes):
        x2_pads[code] = (128.0 + (ci // 2) * 2.5, 6.6 + (ci % 2) * 2.5)
    x2_pads.update({'227': (158.0, 6.6), '229': (160.5, 6.6), '230': (160.5, 9.1)})
    make_conn('X2', 143, 7.85, x2_pads)
    # X8 itself is on the bracket. A59..A62 above are its physical PCB
    # cable landings; do not recreate the remote connector on the board.
    # X9 itself is on the bracket. A45..A58 above are the physical PCB
    # landings at this cable exit; do not recreate an on-board X9 footprint.

    # ---- UNTRACED footprints: photo/BOM-identified chips whose NETS aren't traced yet ----
    # Real packages + real marks (renders as chips, not boxes); pads carry no nets (honest).
    # Confident IDs only; the rest stay silk outlines until identified.
    UNTRACED = {
        # Refdes per the OFFICIAL ДГШ5.109.009 ПЭЗ (owner's scan, 2026-07) -- the FDC-revision
        # per-refdes BOM. Types photo-verified; positions photo-measured; nets untraced (no
        # schematic exists for the .009 additions).
        # D51 removed: promoted to a net-modeled chip (KP14_MUX in board.json) -- keeping it here duplicated the refdes (DSN killer)
        # --- ВГ93 quadrant (owner's 4-row layout; refdes = official .009) ---
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
    # Keep the three photo-promoted D94 control nets at the tail, matching the
    # established source-PCB net-number order. JSON insertion during evidence
    # promotion must not renumber every later KiCad net and create a 60k-line
    # serialization diff on an otherwise local placement correction.
    tail_nets = ("FDC_RE_N", "FDC_CS_N", "FDC_WE_N")
    net_names = [name for name in spec['nets'] if name not in tail_nets]
    net_names.extend(name for name in tail_nets if name in spec['nets'])
    for name in net_names:
        e = spec['nets'][name]
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
    BX0, BY0, BX1, BY1 = 0.0, 0.0, 310.0, 266.0
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
    mhole(10.2, 12.6); mhole(114.4, 13.3)  # top pair flanking X1 [emaplaat]
    mhole(10.1, 135.6)                     # mid-left [emaplaat]
    mhole(199, 251.2)                      # bottom-right [emaplaat]
    # The read mid-right (300.3,138.1) and bottom-left (104,251.4) targets collide
    # with D34/D59 copper in the current rectangular board model. Treat them as
    # deferred mechanical-overhang/fixture features until the exact board outline is
    # re-read rather than manufacturing edge-cut holes through routed copper.

    # top-edge expansion connectors X1/X2 -- non-electrical SILK OUTLINE annotations (read off the
    # drawing: X1 mm15..107, X2 mm118..177, at the top edge). Their full pin/net model is future
    # LVS work; this just shows the two prominent connectors so the top matches.
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

    def silk_note(label, x, y, rot=0):
        t = pcbnew.PCB_TEXT(board); t.SetText(label); t.SetLayer(pcbnew.F_SilkS)
        t.SetTextSize(pcbnew.VECTOR2I(pcbnew.FromMM(2.0), pcbnew.FromMM(2.0)))
        t.SetTextThickness(pcbnew.FromMM(0.25))
        t.SetItalic(True)
        try: t.SetTextAngle(pcbnew.EDA_ANGLE(rot, pcbnew.DEGREES_T))
        except Exception: t.SetTextAngle(rot * 10)
        t.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(x), pcbnew.FromMM(y)))
        board.Add(t)

    silk_box(15, 13, 107, 21, "X1"); silk_box(118, 13, 171.5, 21, "X2") # X2 ends immediately before photo-fitted A21
    silk_box(222, 283, 273, 287.6, "X9")   # bottom connector (read mm222..273, pins 58..45; box held 0.4 off the edge cut for silk-edge DRC)
    # ROM bank is К573РФ5 ×8 (BOM) -> D15-D22. D15/D16 are net-modeled chips; the other 6 aren't
    # traced yet (toward-76), so show them as PLACEMENT-ONLY silk socket outlines to complete the
    # 8-EPROM bank visually (same row y86, ~21 mm pitch). Not in board.json -> LVS unaffected.
    # (ROM sockets D17-D22 are now net-modeled footprints -- see PLACE -- not silk outlines.)
    # DRAM array is 565РУ5 ×32 -> D60-D91 in a 4×8 grid. All sockets are net-modeled;
    # the .158/.009 target populates the bottom D84-D91 row.
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
    # (D106 -> untraced К555ИЕ7 footprint, .009 BOM/photo reconciliation)
    # (D32/D12/D3 are now net-modeled serial-driver footprints -- see PLACE.)
    # X3 is on the bracket; its former on-board silk body is intentionally absent.
    silk_box(72, 278, 98, 286, "X8")     # power connector, bottom-left (+5/GND/+12/-12; 61/62/60/59)     # RS-232 serial connector (drivers D14/D32/D3/D12 -> here)
    for label, x, y, rot in BOARD_SILK_NOTES:
        silk_note(label, x, y, rot)
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
    # ADR escapes REMOVED (route campaign v76): the hardcoded bars used the OLD buffer-row pad
    # coords (D24 pads y55.19; collector rows y33-35.4) -- after the СБ-true buffer-row move to
    # y37.1 they shorted into the moved pads. The corner geometry changed entirely (D24 is now
    # ~16mm closer to X1), so per the original strategy note: give the router a fair shot first,
    # and only re-add bars with UPDATED pad coords if the links fail deterministically again.
    # (helpers _wire/_via kept above for that case)
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
    # Use the project-local GOST italic font for silkscreen text so Cyrillic chip
    # markings render fully and assembly labels share one house style.
    patch_text_fonts(out)
    board = pcbnew.LoadBoard(out)
    board.EmbedFonts()
    pcbnew.SaveBoard(out, board)
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
