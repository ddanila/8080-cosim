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
    'C_ELEC_AXIAL': ('Capacitor_THT.pretty', 'CP_Axial_L18.0mm_D6.5mm_P25.00mm_Horizontal'),
    'D_DIODE': ('Diode_THT.pretty',     'D_DO-35_SOD27_P7.62mm_Horizontal'),
    'SW':      ('Connector_PinHeader_2.54mm.pretty', 'PinHeader_1x02_P2.54mm_Vertical'),
    'JUMPER3': ('Connector_PinHeader_2.54mm.pretty', 'PinHeader_1x03_P2.54mm_Vertical'),   # Е-family config links
    'XTAL':    ('Crystal.pretty',       'Crystal_HC49-U_Horizontal'),   # РК-171 flat can, lying -- closest stock footprint
    'C_TRIM':  ('Capacitor_THT.pretty', 'C_Disc_D7.5mm_W4.4mm_P5.00mm'), # КТ4-23 trimmer stand-in (no trimmer lib in stock KiCad)
    'R_TRIM':  ('Potentiometer_THT.pretty', 'Potentiometer_Piher_PT-10-V10_Vertical'),  # legacy .006-only footprint support
    'SW_DIP6': ('Button_Switch_THT.pretty', 'SW_DIP_SPSTx06_Slide_9.78x17.42mm_W7.62mm_P2.54mm'),  # S3 video-config bank
    'JUMPER4': ('Connector_PinHeader_2.54mm.pretty', 'PinHeader_1x04_P2.54mm_Vertical'),  # Е13 strap
    'JUMPER2': ('Connector_PinHeader_2.54mm.pretty', 'PinHeader_1x02_P2.54mm_Vertical'),  # Е5 -5V array link
    'Q_KT13':  ('Package_TO_SOT_THT.pretty', 'TO-92_Inline'),                  # КТ315 flat KT-13; stock inline pad-row stand-in
    'Q_KT27':  ('Package_TO_SOT_THT.pretty', 'TO-126-3_Horizontal_TabDown'),    # КТ972 KT-27 / TO-126, mounted flat per factory detail
    'L_TAPPED':('Connector_PinHeader_2.54mm.pretty', 'PinHeader_1x03_P2.54mm_Vertical'), # legacy .006-only footprint support
    'VIDEO_CONN': ('Connector_PinHeader_2.54mm.pretty', 'PinHeader_1x02_P2.54mm_Vertical'),  # X7 video socket stand-in (601/602)
    'WIRE_PAD':   ('TestPoint.pretty', 'TestPoint_THTPad_D2.0mm_Drill1.0mm'),  # factory numbered flying-wire landings
}
PASSIVE_FP_REF = {
    'C16': ('Capacitor_THT.pretty', 'C_Axial_L5.1mm_D3.1mm_P12.50mm_Horizontal'),
    'C19': ('Capacitor_THT.pretty', 'C_Axial_L5.1mm_D3.1mm_P10.00mm_Horizontal'),
    'C20': ('Capacitor_THT.pretty', 'C_Axial_L5.1mm_D3.1mm_P10.00mm_Horizontal'),
    'C22': ('Capacitor_THT.pretty', 'C_Axial_L5.1mm_D3.1mm_P10.00mm_Horizontal'),
    'RUNK1': ('Resistor_THT.pretty', 'R_Axial_DIN0207_L6.3mm_D2.5mm_P10.16mm_Horizontal'),
    'R87': ('Resistor_THT.pretty', 'R_Axial_DIN0207_L6.3mm_D2.5mm_P10.16mm_Horizontal'),
    'R88': ('Resistor_THT.pretty', 'R_Axial_DIN0207_L6.3mm_D2.5mm_P10.16mm_Horizontal'),
    'R89': ('Resistor_THT.pretty', 'R_Axial_DIN0207_L6.3mm_D2.5mm_P10.16mm_Horizontal'),
    'R92': ('Resistor_THT.pretty', 'R_Axial_DIN0207_L6.3mm_D2.5mm_P10.16mm_Horizontal'),
    'R99': ('Resistor_THT.pretty', 'R_Axial_DIN0207_L6.3mm_D2.5mm_P10.16mm_Horizontal'),
    'R78': ('Resistor_THT.pretty', 'R_Axial_DIN0207_L6.3mm_D2.5mm_P10.16mm_Horizontal'),
    'R98': ('Resistor_THT.pretty', 'R_Axial_DIN0207_L6.3mm_D2.5mm_P10.16mm_Horizontal'),
    'R8': ('Resistor_THT.pretty', 'R_Axial_DIN0207_L6.3mm_D2.5mm_P10.16mm_Horizontal'),
    **{ref: ('Resistor_THT.pretty', 'R_Axial_DIN0207_L6.3mm_D2.5mm_P10.16mm_Horizontal')
       for ref in ('R49', 'R50', 'R51', 'R52', 'R53', 'R54', 'R55', 'R56')},
    'R57': ('Resistor_THT.pretty', 'R_Axial_DIN0207_L6.3mm_D2.5mm_P10.16mm_Horizontal'),
    'R104': ('Resistor_THT.pretty', 'R_Axial_DIN0411_L9.9mm_D3.6mm_P12.70mm_Horizontal'),
    'R18': ('Resistor_THT.pretty', 'R_Axial_DIN0207_L6.3mm_D2.5mm_P10.16mm_Horizontal'),
    'R1': ('Resistor_THT.pretty', 'R_Axial_DIN0207_L6.3mm_D2.5mm_P10.16mm_Horizontal'),
    'R30': ('Resistor_THT.pretty', 'R_Axial_DIN0411_L9.9mm_D3.6mm_P12.70mm_Horizontal'),
    'S4': ('Connector_PinHeader_2.54mm.pretty', 'PinHeader_1x03_P2.54mm_Vertical'),
}
FACTORY_WIRE_PLACE = {
    'W7': {
        'pads': {'1': (1.697, 179.350), '2': (227.668, 194.422)},
        'value': 'A:7 ~24cm insulated wire (cut length held)',
        # Both ends are photographed backside through-joints beside the
        # printed 7 marks, so preserve drilled rather than surface landings.
        'through_hole': True,
        'pad_diameter': 2.0,
        'drill_diameter': 1.0,
    },
    'W14': {
        'pads': {'1': (10.449, 179.305), '2': (224.478, 193.144)},
        'value': 'A:14 ~23cm insulated wire (cut length held)',
        # The common solder-side image shows both ends as plated through-joints
        # beside the printed 14 marks.
        'through_hole': True,
        'pad_diameter': 2.0,
        'drill_diameter': 1.0,
    },
    # Board point A:8 / conductor position 4. Both ends are photographed
    # component-side surface joints, not drilled test points. The pad diameter
    # is conservative provisional fabrication geometry; coordinates and island
    # identities are evidence-backed independently of that diameter.
    'W8': {
        'pads': {'1': (40.811, 99.989), '2': (223.601, 170.724)},
        'value': 'A:8 ~19cm insulated wire',
        'pad_diameter': 2.0,
    },
    'W10': {
        'pads': {'1': (240.091, 146.982), '2': (108.865, 152.813)},
        'value': 'A:10 13.5cm insulated wire',
        'pad_diameter': 2.0,
    },
    'W11': {
        'pads': {'1': (261.325, 128.548), '2': (142.256, 123.468)},
        'value': 'A:11 ~11.5cm insulated wire (cut length held)',
        'pad_diameter': 2.0,
    },
    'W19': {
        'pads': {'1': (35.308, 122.281), '2': (130.027, 121.736)},
        'value': 'A:19 ~9.5cm insulated wire',
        # A19B lies beside C54.1; 1.5 mm preserves 0.279 mm clearance while
        # retaining a generous component-side solder landing.
        'pad_diameter': 1.5,
    },
    'W20': {
        'pads': {'1': (178.780, 15.200), '2': (213.571, 78.499)},
        'value': 'A:20 ~6cm insulated wire',
        # Pad 1 sits wholly inside the existing 2 mm A23.1 plated landing;
        # pad 2 is the separately photographed D3-side surface joint.
        'pad_diameters': {'1': 1.0, '2': 1.5},
    },
}
# traced-network passives [scan] + decoupling C35-C72 (BOM count; chip-adjacent positions assumed)
PASSIVE_PLACE = {
    'R34':(247.0,125.6,90),  # 13k D40 CLR/LOAD pull-up, left of D40 [sheet-2]
    'R46':(266.6,184.0,90),  # 200R vertical between D33 and D103 [registered target photo]
    'C6':(251.0,165.0,90),   # 56p D33 input shunt [sheet-2; local placement approximate]
    'R33':(297.5,133.3,0),   # 620R D34 RC resistor, horizontal above D34 [owner photo]
    'C5':(304.0,127.5,0),    # 560p D34 RC capacitor above R33 [owner photo]
    'R19':(44.4,220.7,90),'VD5':(49.4,231.5,90),'C31':(23,228.0,90),'C32':(23,235.0,90),'C33':(24.5,244.0,90),   # corner re-layout: the assumed grid squatted the crystal's real estate (photo-true corner)
    'R3':(12,200.8,0),'R4':(16.9,209.2,90),'VD1':(12.5,216.1,270),'R20':(51.9,194.2,0),'C21':(48.5,205.9,0),'C1':(18.4,194.8,0),
    # Native sheet 1 names the H/-BLOCK pull-up R1 2k; the .009 drawing and
    # owner photo place it horizontally between D13 and D105. Pin 1 is the
    # right-hand +5 V landing and pin 2 is the left-hand H landing.
    'R1':(35.800,210.000,180),
    # .009 factory assembly labels the vertical 2K body immediately left of
    # D1 as R8.  The D1-local owner-photo fit fixes its two drills at 10.16 mm
    # pitch and the body centre here; direct continuity closes D94.1 to +5 V.
    'R8':(22.870,178.710,90),
    'A17':(115.8,27.1,0),  # two-sided owner photos, transferred from top mounting hole (114.4,13.3)
    # Registered component/solder views show one 2.5 mm-pitch X3 cable row;
    # sheet 1 labels the left/right ends A21/A32.
    'A21':(173.70,15.2,0),'A22':(176.24,15.2,0),'A23':(178.78,15.2,0),'A24':(181.32,15.2,0),
    'A25':(183.86,15.2,0),'A26':(186.40,15.2,0),'A27':(188.94,15.2,0),'A28':(191.48,15.2,0),
    'A29':(194.02,15.2,0),'A30':(196.56,15.2,0),'A31':(199.10,15.2,0),'A32':(201.64,15.2,0),
    'R104':(194.34,25.87,0), # registered photo terminals; 12.7 mm pitch, A21 side at left
    # Exact .009 sheet 1 identifies the D10 IR0/IR1 12k pull-downs. Factory
    # refdes order and D10-local owner-photo joints place the vertical pair.
    'R105':(164.670,108.170,90),'R107':(167.560,109.270,90),
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
    # X6 is bracket-mounted. Registered point A:3 is conductor 1's lap joint
    # on VD3.2/SOUND_CLAMP; A:4 is the separately insulated marked-return
    # conductor on the wide ground strip. Neither is drilled.
    'AX603':(299.551,124.391,0),'AX604':(305.182,123.141,0),
    # X4 is bracket-mounted. The 23-conductor bundle is visible above the
    # D93/D28 quadrant; sheets 4-5 map board points A X4:1..23 in order to
    # the remote connector. Row pitch and span are registered from the owner
    # component photo; per-contact copper beyond the first five remains open.
    'AX401':(221.5,15.2,0),'AX402':(224.04,15.2,0),'AX403':(226.58,15.2,0),'AX404':(229.12,15.2,0),
    'AX405':(231.66,15.2,0),'AX406':(234.20,15.2,0),'AX407':(236.74,15.2,0),'AX408':(239.28,15.2,0),
    'AX409':(241.82,15.2,0),'AX410':(244.36,15.2,0),'AX411':(246.90,15.2,0),'AX412':(249.44,15.2,0),
    'AX413':(251.98,15.2,0),'AX414':(254.52,15.2,0),'AX415':(257.06,15.2,0),'AX416':(259.60,15.2,0),
    'AX417':(262.14,15.2,0),'AX418':(264.68,15.2,0),'AX419':(267.22,15.2,0),'AX420':(269.76,15.2,0),
    'AX421':(272.30,15.2,0),'AX422':(274.84,15.2,0),'AX423':(277.38,15.2,0),
    # The registered 220-ohm body below-left of D98 is real but not R94.
    # Preserve its photographed placement under an explicitly non-historical
    # evidence placeholder until continuity identifies the original refdes.
    'RUNK1':(297.6,56.4,270),
    # .009 labels the three vertical bodies left of D94 as R87/R88/R89.
    # D94-local component/solder fits place pad 1 on the three signal traces;
    # pad 2 is the shared upper +5 V rail. All three values are photo-closed at 6K2.
    'R87':(222.305,32.704,90),'R88':(224.943,32.704,90),'R89':(227.629,32.704,90),
    # .009 factory-drawing affine registration, corroborated by the populated
    # owner-photo column at the right edge beside C19 (top to bottom). Two
    # independent component angles read R100/R102/R108 as 12K and R86 as 4K7.
    'R100':(299.776,94.000,0),'R102':(299.253,97.229,0),
    'R108':(298.731,100.458,0),'R86':(298.208,103.688,0),
    'R5':(44.0,187.0,90),'R6':(47.0,187.0,90),'R29':(50.0,187.0,90),  # D30 READY row, assembly drawing
    'R31':(94.0,257.0,90),  # .009/.158 СБ + owner photo: vertical between Z1 and D59; left of D59 pad row
    'R32':(109.5,246.0,0),  # .009/.158 СБ + owner photo: horizontal above D59
    'R38':(121.4,249.1,90),'R39':(230.5,192.5,0),
    'Z1':(79.4,243.5,90),    # РК-171 crystal at its PHOTO-TRUE spot (edge-relative measurement, straight-on corner crop)
    'S3':(63.5,182.4,0),   # video-config DIP-6 [emaplaat 'S3' box]
    'E13':(104,188,0),     # video strap posts [emaplaat E13 zone]
    'E14':(95,170,0),      # video-mux G strap [emaplaat E11/E12 post block zone]
    'E4':(39.9,226.5,0),'E5':(50.5,224.0,0),'C34':(47,242,0),   # E4/E5 СБ-true (poz pads read); C34 not yet located on the СБ [approx]
    # ---- .009 analog/FDC corner. The .006 VT3/VT4 dashed RF option is DNP on
    # the target; only the retained VT2/R62-R67/VD3/C94 path is placed here. ----
    # VT2's yellow Б/8901 KT-13 body is photo-fitted independently of its
    # three bent component-side lap joints; C94 is the separate factory-drawn
    # two-terminal position immediately right of VT2, not that yellow body.
    'VT2':(285.037,132.926,90),'VD3':(299.38,128.40,90),
    # Factory СБ affine registration: five X4 input pull-ups above D98 plus
    # READY/separator/drive-select open-collector pull-ups around D95/D28/D96.
    'R79':(292.431,19.166,90),'R80':(290.248,19.189,90),'R81':(288.066,19.212,90),
    'R82':(285.883,19.235,90),'R83':(283.701,19.258,90),
    'R84':(245.220,97.300,90),'R85':(278.302,66.090,90),
    # D106/D28-local owner-photo joints supersede the folded-drawing affine:
    # R78 is the left 10K body and R98 the right 4K7 body, both at 10.16 mm pitch.
    'R78':(267.999,68.177,90),'R94':(271.987,54.141,90),
    'R93':(277.443,54.083,90),'R95':(282.852,54.319,90),
    'R98':(270.485,68.177,90),
    'C11':(268.232,93.540,90),'C94':(289.870,130.321,90),
    # Remaining retained R6x grid refdes-to-slot assignments are approximate.
    'R62':(263,115,90),'R63':(266.5,115,90),'R64':(270,115,90),'R65':(282.21,125.14,90),'R66':(302.69,128.46,90),
    'R67':(295.94,125.39,90),
    # Factory lower-FDC drawing registered to photo-fitted D95/D99 and
    # D101/D97/D102 centres: C11/C15 are vertical between their IC pairs.
    'C9':(285.807,33.590,90),'C10':(252.361,73.163,90),'C12':(253.218,33.954,90),'C15':(280.230,110.120,90),
    # Factory affine centres plus registered component/solder views restore the
    # populated horizontal C16/R92/R99 row. Two component angles read R92=1K3
    # and R99=4K7; their copper endpoints are closed separately. C16 remains a
    # value/connectivity boundary.
    'C16':(267.094,101.055,0),'R92':(253.869,101.194,0),'R99':(241.207,103.467,0),
    # Exact .009 sheet-3 D99 timing parts, projected from their factory-drawing
    # body centres through the guarded lower-FDC affine registration.
    'C17':(303.000,55.000,90),'R103':(307.200,47.200,90),
    'C18':(303.000,70.000,90),'R97':(298.620,67.150,90),
    # The factory drawing identifies C19 immediately right of D99; the owner
    # component and solder views independently prove the populated vertical
    # axial body and its two distinct joints. Keep both destinations open.
    'C19':(292.893,93.574,90),
    # Registered owner component/solder views: the two grey axial capacitors
    # occupy adjacent 2.54 mm columns immediately beyond D102.8/.9. Their
    # 10 mm lead spans share D102's y centre; the bodies lean right in the
    # component photo, so body pixels are not drill-centre coordinates.
    'C20':(303.997,110.024,90),'C22':(306.537,110.024,90),
    'VT1':(247.8,213.8,0),  # КТ972 KT-27 beeper driver; factory mounting detail shows the body laid flat
    'S4':(245.0,80.2,0),    # ВДМ1-2 SPDT microswitch (СБ position, .100; 3-pad electrical stand-in)
    'X7':(258.5,6,0),   # video socket (СБ top edge; contact 601/602)
    'E1':(113,207,0),      # MA7/DRAM-size strap [emaplaat E1 post]
    # Target-board component photos and the .006 assembly drawing close the
    # RAS ladder as one vertical column: R56/R52, R55/R51, R54/R50,
    # R53/R49 from top to bottom. All eight use the photographed 10.16 mm
    # lead span; R49-R52 read 75 ohm and R53-R56 read 5K1.
    'R56':(221.0,135.2,90),'R52':(221.0,150.0,90),
    'R55':(221.0,162.2,90),'R51':(221.0,175.2,90),
    'R54':(221.0,189.0,90),'R50':(221.0,201.5,90),
    'R53':(221.0,215.2,90),'R49':(221.0,229.7,90),
    # The .006 drawing and target row place the photographed 20-ohm R57
    # vertically between D36 and the bottom-notched D37. R58's 5K1 value is
    # schematic-exact, but its separate physical position remains approximate.
    'R57':(236.7,177.6,90),'R58':(204.1,220.5,0),
    'R40':(74,176,90),'R41':(77,176,90),'R42':(80,176,90),'R43':(83,176,90),'R44':(86,176,90),'R45':(89,176,90),   # S3 pullup row [drawn; position approx]
    'C73':(58,241.5,0),
    'E2':(65.5,215.5,0),'E3':(49.5,215.5,0),   # beside D52's body (x52-62), not inside it   # СБ-true posts beside D52 (old 217.5 was a mis-entered routing guess)    # 4/20 pF trimmer (sheet-2: Z1+C73+R32 osc group; '8811' disc on the photos)
    'R17':(111.4,119.0,90),'C99':(105.1,119.8,0),   # D9.G1 RC deglitch -- SB-true spots (crop sb_decode)
    'R90':(251.6,216.1,90),'VD4':(254.1,216.1,90),'R91':(256.4,216.1,90),'R48':(245.1,207.4,0),'R60':(253.9,202.7,0),   # beeper cluster SB-true (crop sb_beeper); R60 = FRAME INT pullup between wire posts 2/1
    # D56 AG3 RCs СБ-true (crops sb_d56rc/sb_westpair): R59+C8 pair WEST of D56 (between D103 and D56),
    # C7+R47 pair EAST of D56; R61 not found on the СБ in the checked zones [stays approx]
    'R47':(296.5,166.8,90),'C7':(294.1,166.6,90),'R59':(280.1,174.0,90),'C8':(280.1,184.5,90),'R61':(293.5,189.0,0),
    'R11':(70.0,101.0,90),'R12':(73.5,101.0,90),
    'R13':(50.123,101.273,0),'R14':(59.460,125.041,0),  # row-photo fitted horizontal D6 pullups; R14 body is partly A19-obscured
}
_DEC = {  # DRAM-field decaps: emaplaat zigzag (per column, top->bottom)
    'C35':(119.6,120.9,0),'C36':(119.6,145.6,0),'C37':(119.6,170.7,0),'C38':(119.6,195.8,0),
    'C54':(130.9,120.9,0),'C55':(130.9,145.6,0),'C56':(130.9,170.7,0),'C57':(130.9,195.8,0),
    'C39':(142.3,120.9,0),'C40':(142.3,145.6,0),'C41':(142.3,170.7,0),'C42':(142.3,195.8,0),
    'C58':(153.7,120.9,0),'C59':(153.7,145.6,0),'C60':(153.7,170.7,0),'C61':(153.7,195.8,0),
    'C43':(164.7,120.9,0),'C44':(164.7,145.6,0),'C45':(164.7,170.7,0),'C46':(164.7,195.8,0),
    'C62':(176.1,120.9,0),'C63':(176.1,145.6,0),'C64':(176.1,170.7,0),'C65':(176.1,195.8,0),
    'C47':(187.1,120.9,0),'C48':(187.1,145.6,0),'C49':(187.1,170.7,0),'C50':(187.1,195.8,0),
    'C66':(198.4,120.9,0),'C67':(198.4,145.6,0),'C68':(198.4,170.7,0),'C69':(198.4,195.8,0),
}
PASSIVE_PLACE.update(_DEC)

def dip_for(n):                       # smallest standard DIP that holds n pins
    for s in (14,16,18,20,24,28,40):
        if n <= s: return f"DIP-{s}_W{'15.24' if s>=24 else '7.62'}mm"
    return "DIP-40_W15.24mm"

# Default Soviet case marking per logical type. Exact factory or owner-observed
# per-refdes exceptions live as `marking` in juku.board.json and are guarded by
# ref/juku-official-009-ic-census.json.
MARK = {
    'CPU8080':'КР580ИК80А', 'SYS8238':'КР580ВК38',  'USART8251':'КР580ВВ51А',
    'PPI8255':'КР580ВВ55А', 'PIT8253':'КР580ВИ53',  'PIC8259':'КР580ВН59',
    'BUF8286':'КР580ВА86',  'RU5':'565РУ3Г',         'EPROM8K':'К573РФ5',
    'IO_DEC138':'К555ИД7',  'RASCAS_DEC':'К531ИД7',  'IE7_CTR':'К555ИЕ7',
    'KP14_MUX':'К531КП14',  'LA1_GATE':'К531ЛА1',    'LA3_GATE':'К555ЛА3',
    'LA12_GATE':'К531ЛА12', 'LN1_INV':'К531ЛН1',     'LN1_OSC':'К531ЛН1',
    'AG3_ONESHOT':'КМ555АГ3','IE10_CTR':'К555ИЕ10',  'DEC_PROM':'КР556РТ4',
    'WAIT_PROM':'КР556РТ4А',
    'RE3_PROM':'К155РЕ3',  'RE3_PROM_092':'К155РЕ3', 'TM2_DFF':'КМ555ТМ2',
    'LN3_OC_INV':'К155ЛН3', 'KP12_MUX':'К555КП12', 'LP11_BUF':'К155ЛП11',
    'CT16_CTR':'КР531ИЕ17',   'CLK_PHASE':'К155ЛН5',           # pinned via repo tracing (clock-subsystem.md / memory.md)
    'VABUS':'КР580ВА87',    'IR82':'КР580ИР82',      'IR16':'К555ИР16',
    'TL2':'К555ТЛ2',        'LN1_DUAL':'К531ЛН1',    'AP2':'К170АП2',
    'UP2':'К170УП2',        'LA18':'К155ЛА18',    'LN2':'К561ЛН2',
}
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
    'D1':(32.3,157,0),'D4':(51.1,142.4,0),'D2':(73.815,138.795,0),
    'D8':(83.332,113.303,270),  # photo-fitted socketed К155РЕ3 PROM, notch right; DIP origin compensates 5 um body-centre offset
    'D9':(109.923,113.303,270),  # photo-fitted metal К555ИД7, notch right; same stock-footprint anchor compensation
    # video address counters (ИЕ7) + DRAM addr muxes (КП14) live in the LEFT columns of the DRAM
    # array (read off the drawing): two sub-rows at y217 / y242 descending into the array, with
    # D46/D44/D48 over D47/D45/D49 -- NOT a separate row up by the bus. (~13 mm pitch, vertical.)
    'D46':(80.7,198.5,0),'D44':(93.3,198.5,0),'D48':(105.6,198.5,0),
    'D47':(80.7,223,0),'D45':(93.3,223,0),'D49':(105.6,223,0),
    # video-output chain -- relocated to the right-centre with the clock cluster (read off the
    # drawing): RAS/CAS decode D53 sits below D36; IE10 ctr D103 below D39; AG3 one-shot D56 far
    # right (raw read hit the 310 edge -> pulled in 5 mm so the DIP stays on-board). All vertical.
    'D53':(227.8,204.9,0),'D52':(57.2,211.6,0),'D50':(100.690,143.923,180),'D51':(100.690,169.057,180),'D92':(260,159.2,0),'D103':(273.0,181.8,0),   # D50/D51 are two-side photo-fitted with notches down; D52 = 5th КП14; D50/D92 net-carrying (beeper wires 10/11/13)
    'D56':(287.8,180,0),    # АГ3 at its DRAWN spot after all: the "К555ЛУ?/1068" photo read there was
                          # К155АГ3 8901 UPSIDE DOWN (1068 = 8901 rotated). Quadrant round-trip reverted.
    # bus interface band (read off the drawing): a horizontal row in the gap BETWEEN the ROM row
    # and the DRAM array -- D5 (8238) far left, then D6 / D7, and the wide D10 (8259).
    # This was a fictional bottom-centre row before; the muxes above now occupy that freed space.
    # D5/D7-D9 are direct-photo fitted against the nearby fitted D50/D51 anchors;
    # D6 remains on the assembly-seeded row.
    'D5':(23.69,109.52,270),  # marked КР580ВК38, notch right
    'D6':(63.8,114.1,90),'D7':(131.465,113.303,270),  # black КР1533ЛА3, notch right; stock-footprint anchor compensated
    'D10':(192.44,110.08,90),  # КР580ВН59 local affine photo fit; old centre projected onto adjacent resistors/body
    'D107':(51.1,168.2,0),   # 3rd ВА86 (=U_BUFL) directly below D4 [emaplaat + owner photo]
    'D30':(32.9,189.5,90),   # READY flip-flop; section A traced, section B remains boundary
    'D105':(31.9,215.5,270),  # .009 centre + owner-photo right-facing notch
    # clock subsystem -- RELOCATED to its real right-centre region, read off the assembly drawing
    # via the validated frame (the divider/gate mesh sits right of the DRAM array near D40/D41/D34,
    # not a fictional bottom-left row). D40 (СТ16) is photo-fitted horizontal, notch-right -> rot 270; the ЛА/ЛН gates
    # D38/D39/D33/D36/D35 are drawn vertical -> rot 0. D59 (osc) is still approximate (the drawing
    # puts it bottom-centre by the transformer -- read it next pass).
    'D40':(258.56,140.99,270),'D41':(235,140.9,270),'D38':(234.558,159.619,0),'D39':(273.972,159.582,0),   # D38 is cross-side photo-fitted; D40/D41 are the registered same-row notch-right pair; the upper top-notched КР1533ЛА3 immediately right of decapped D92 is D39
    'D34':(297.5,143.2,0),   # ЛП5 XOR pulse gen [sheet-2]
    # Inputs below compensate the stock footprint anchor/bounding-box offset so
    # the saved KiCad footprint positions remain the photo-guarded coordinates
    # D94=(229.275,38.110), D100=(257.650,37.400), D98=(290.000,37.400).
    'D93':(235.941,73.335,0),'D94':(238.165,34.305,90),'D100':(269.08,33.595,90),
    # Registered component fits: D28 centre is 15.064 mm right / 1.442 mm
    # above D106; D96 is another 14.451 mm right / 0.240 mm below D28.
    'D98':(298.89,33.595,90),'D106':(262,74,0),'D28':(277.064,72.558,0),'D96':(291.515,72.798,0),
    # D95/D101/D97/D102 share one raw component photograph. Package-local
    # scales establish their relative centres; the visible x=3682 px right
    # board edge anchors the row inside the physical 310 mm outline.
    # D95/D99/D101 have photographed right-facing notches (rot 270); D97/D102
    # have left-facing notches (rot 90). Centres alone are insufficient here:
    # reversing a one-shot or mux silently swaps every physical pin landing.
    'D95':(256.000,93.000,270),'D97':(268.604,110.273,90),'D101':(244.810,110.380,270),
    'D99':(279.895,93.451,270),'D102':(292.567,110.024,90),
    'D36':(228.1,180.4,180),'D33':(258,180,180),'D35':(241.0,200.5,0),   # D36/D33 notch-DOWN (emaplaat+photo)   # D36 +3mm right to clear the DRAM right column; D35 up 4mm to clear D7
    'D59':(106.6,257,90),   # osc ЛН1 -- read off the drawing: horizontal, bottom-centre by transformer Z
                          # (bottom row 281->275: photo shows ~11 mm body-to-edge margin; 281 put pads 3 mm from the cut)
    # NET-MODELED this session (Phase-B) -- promoted from placement-outlines to real footprints at
    # their traced drawing positions: bus transceivers (top band, horizontal) + bottom row.
    # buffer row at СБ y37.1 (sb_left_0: D25/D23 boxes y34.7-39.5; the old 53.4 sat on the ROM sockets)
    'D25':(29.8,37.1,90),'D23':(54.6,37.1,90),'D24':(81.6,37.1,90),'D29':(108.5,37.1,90),
    'D42':(136,259,90),'D43':(159.6,259.5,90),'D58':(183.0,243.1,90),   # bottom row -6mm: photo-1's y-scale is 9.50 px/mm (board spans 2528px/266mm), not the 9.87 x-scale -- edge-relative re-measure
    'D37':(245.5,180.1,180),   # .006 lower row: bottom-notched КР1533ЛА3 between R57 and D33
    'D13':(31.9,205.3,270),  # owner photo: horizontal К555ТЛ2, right-facing notch
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
# Registered owner component photo: D104 is the notch-down К170УП2 left of
# R30; D32/D14 are the upper/lower notch-up К170АП2 pair right of R30.
PLACE['D104'] = (195.7, 38.9, 180)
PLACE['D32'] = (211.8, 29.5, 0); PLACE['D14'] = (211.8, 41.0, 0)
PLACE['D12']  = (206.3, 80.9, 0); PLACE['D3']  = (220.434, 80.356, 180)
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

    def apply_population_flags(fp, chip):
        """Carry assembly intent into native KiCad manufacturing metadata."""
        if chip.get('assembly_dnp'):
            fp.SetDNP(True)
            fp.SetExcludedFromPosFiles(True)

    def add_passive(ref, x, y, rot=0):
        nonlocal n_pads
        c = chips[ref]; typ = c['type']
        lib, fpn = PASSIVE_FP_REF.get(ref, PASSIVE_FP[typ])
        fp = pcbnew.FootprintLoad(SHARED + lib, fpn)
        if fp is None: raise RuntimeError(f"no passive footprint {fpn} for {ref}")
        # Keep a photographed case marking visible when no interpreted BOM
        # value exists. C20/C22 `1Н5` are source-closed as 1.5 nF by GOST 11076-69.
        fp.SetReference(ref); fp.SetValue(c.get('value', c.get('prov', {}).get('marking', '')))
        apply_population_flags(fp, c)
        fp.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(x), pcbnew.FromMM(y)))
        if rot: fp.SetOrientationDegrees(rot)
        board.Add(fp); placed[ref] = fp; n_pads += fp.GetPadCount()
        # R1 is not drilled on the owner board: both bent leads terminate on
        # photographed component-side copper landings between D13 and D105.
        # Preserve that construction instead of punching a generic axial THT
        # footprint through the neighboring D13 fanout.
        if ref == "R1" or ref in {"AX603", "AX604"}:
            for pad in fp.Pads():
                pad.SetAttribute(pcbnew.PAD_ATTRIB_SMD)
                pad.SetDrillSize(pcbnew.VECTOR2I_MM(0, 0))
                pad.SetSize(pcbnew.VECTOR2I_MM(0.9, 0.9))
                layers = pcbnew.LSET()
                layers.AddLayer(pcbnew.F_Cu)
                layers.AddLayer(pcbnew.F_Mask)
                pad.SetLayerSet(layers)
        # R33 and R66 are photo-locked in the dense right-edge analog cluster.
        # Their nearest pads are 1.721 mm centre-to-centre, so the library's
        # 1.60 mm copper leaves only 0.121 mm.  The original-style 0.8 mm drills
        # retain a 0.35 mm annulus with 1.50 mm pads and clear the 0.20 mm rule
        # without moving either photographed component centre.
        if ref in {"R33", "R66"}:
            for pad in fp.Pads():
                pad.SetSize(pcbnew.VECTOR2I_MM(1.5, 1.5))
        # R89's photo-registered signal drill sits 1.678 mm from D94.1. Keep
        # both drill centres fixed and use a 1.25 mm land around the 0.80 mm
        # drill (0.225 mm annulus), clearing the socket's rectangular pin-1
        # land without displacing either source-registered centre.
        if ref == "R89":
            for pad in fp.Pads():
                pad.SetSize(pcbnew.VECTOR2I_MM(1.25, 1.25))
        # The stock horizontal TO-126 footprint assumes the tab is bolted to
        # the PCB. The factory VT1 detail and populated owner board instead
        # show the KT-27 body raised/laid flat with its tab hole left open: only
        # the three leads enter the PCB. Remove that optional board hole and
        # use 1.50 mm copper around the stock 0.80 mm lead drills; this retains
        # a 0.35 mm annulus and clears the photo-placed R90 landing.
        if ref == "VT1":
            for pad in list(fp.Pads()):
                if pad.GetAttribute() == pcbnew.PAD_ATTRIB_NPTH:
                    fp.Remove(pad)
                else:
                    pad.SetSize(pcbnew.VECTOR2I_MM(1.5, 1.5))
        ctr = fp.GetBoundingBox(False, False).GetCenter()          # re-center on (x,y)
        fp.SetPosition(pcbnew.VECTOR2I(2*pcbnew.FromMM(x) - ctr.x, 2*pcbnew.FromMM(y) - ctr.y))
        # The original KT-13 VT2 is raised 3+/-0.5 mm and its three bent leads
        # are lap-soldered to component-side copper left of the body. Registered
        # D102 photo coordinates close all three E-C-B joints; their cross-side
        # projections land on bare copper rather than drilled annuli. Preserve
        # those asymmetric physical landings instead of an invented TO-92 row.
        if ref == "VT2":
            targets = {
                "1": (280.068, 130.501),  # E / VIDEO_OUT / R65.1 common joint
                "2": (281.381, 133.201),  # C / P5V
                "3": (279.700, 135.892),  # B / VT2_BASE
            }
            layers = pcbnew.LSET()
            layers.AddLayer(pcbnew.F_Cu)
            layers.AddLayer(pcbnew.F_Mask)
            for pad in fp.Pads():
                pad.SetAttribute(pcbnew.PAD_ATTRIB_SMD)
                pad.SetDrillSize(pcbnew.VECTOR2I_MM(0, 0))
                pad.SetShape(pcbnew.PAD_SHAPE_CIRCLE)
                pad.SetSize(pcbnew.VECTOR2I_MM(1.5, 1.5))
                pad.SetLayerSet(layers)
                px, py = targets[pad.GetNumber()]
                pad.SetPosition(pcbnew.VECTOR2I_MM(px, py))
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
        apply_population_flags(fp, c)
        fp.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(x), pcbnew.FromMM(y)))
        if rot: fp.SetOrientationDegrees(rot)
        board.Add(fp); placed[ref] = fp
        n_pads += fp.GetPadCount()
        # KiCad's footprint ANCHOR sits at pin 1 (a CORNER), not the body centre -- so the
        # SetPosition above placed the corner at (x,y), shifting the chip half-its-size down/right.
        # Re-place so the body CENTRE lands on (x,y), which is what the drawing coords mean.
        ctr = fp.GetBoundingBox(False, False).GetCenter()
        fp.SetPosition(pcbnew.VECTOR2I(2*pcbnew.FromMM(x) - ctr.x, 2*pcbnew.FromMM(y) - ctr.y))
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
        mark = c.get('marking') or MARK.get(typ, typ)
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

    def add_factory_wire(ref, specification):
        """Add two assembly-wire landing pads without an etched bridge."""
        nonlocal n_pads
        pads = specification['pads']
        x0, y0 = pads['1']
        fp = pcbnew.FOOTPRINT(board)
        fp.SetFPID(pcbnew.LIB_ID('juku', f'FACTORY_WIRE_{ref}'))
        fp.SetReference(ref)
        fp.SetValue(specification['value'])
        fp.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(x0), pcbnew.FromMM(y0)))
        fp.Reference().SetVisible(False)
        fp.Value().SetVisible(False)
        for number, (x, y) in pads.items():
            diameter = specification.get('pad_diameters', {}).get(
                number, specification.get('pad_diameter', 2.0)
            )
            pad = pcbnew.PAD(fp)
            pad.SetShape(pcbnew.PAD_SHAPE_CIRCLE)
            pad.SetSize(pcbnew.VECTOR2I_MM(diameter, diameter))
            if specification.get('through_hole'):
                pad.SetAttribute(pcbnew.PAD_ATTRIB_PTH)
                pad.SetDrillSize(pcbnew.VECTOR2I_MM(
                    specification.get('drill_diameter', 1.0),
                    specification.get('drill_diameter', 1.0),
                ))
                pad.SetLayerSet(pcbnew.PAD.PTHMask())
            else:
                pad.SetAttribute(pcbnew.PAD_ATTRIB_SMD)
                layers = pcbnew.LSET()
                layers.AddLayer(pcbnew.F_Cu)
                layers.AddLayer(pcbnew.F_Mask)
                pad.SetLayerSet(layers)
            pad.SetNumber(number)
            pad.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(x), pcbnew.FromMM(y)))
            fp.Add(pad)
        board.Add(fp)
        placed[ref] = fp
        n_pads += len(pads)

    # connectors are silk outlines, not DIP footprints -> never placed as chips
    CONN = {'EXPANSION_CONN', 'SERIAL_CONN', 'POWER_CONN', 'PAR_CONN', 'KBD_CONN', 'FDC_CONN'}  # bracket connectors stay schematic-only; X1/X2 are made below
    # S1 is the reset pushbutton on the top connector bracket. Factory wire-table
    # rows 11/12 connect its terminals to remote board landings А:17/А:18; it is
    # retained in the schematic but must never become a PCB header footprint.
    OFF_BOARD = {'S1', 'S4', 'X3', 'X4', 'X6', 'X8', 'X9'}
    # place per the assembly-drawing map; any chip not in PLACE -> fallback grid below
    row = 0
    for ref in chips:
        t = chips[ref]['type']
        if (t in CONN or ref in OFF_BOARD or chips[ref].get('pcb_dnp')
                or chips[ref].get('pcb_placement_pending')):
            continue
        if t == 'WIRE_LINK':
            if ref in FACTORY_WIRE_PLACE:
                add_factory_wire(ref, FACTORY_WIRE_PLACE[ref])
            continue
        if t in PASSIVE_FP:
            if ref in PASSIVE_PLACE:
                x, y, rot = PASSIVE_PLACE[ref]; add_passive(ref, x, y, rot)
            continue
        if ref in PLACE:
            x, y, rot = PLACE[ref]; add_chip(ref, x, y, rot)
    col = 0
    for ref in sorted(chips):
        if (ref in OFF_BOARD or chips[ref].get('pcb_dnp')
                or chips[ref].get('pcb_placement_pending')
                or chips[ref]['type'] in CONN or chips[ref]['type'] in PASSIVE_FP
                or chips[ref]['type'] == 'WIRE_LINK' or ref in PLACE):
            continue
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
    # The contact code is connector 2 plus its two-digit physical position.
    # Preserve all 30 positions so unused contacts cannot compress later pads.
    x2_codes = [f'2{position:02d}' for position in range(1, 31)]
    x2_pads = {}
    for ci, code in enumerate(x2_codes):
        x2_pads[code] = (128.0 + (ci // 2) * 2.5, 6.6 + (ci % 2) * 2.5)
    make_conn('X2', 143, 7.85, x2_pads)
    # X8 itself is on the bracket. A59..A62 above are its physical PCB
    # cable landings; do not recreate the remote connector on the board.
    # X9 itself is on the bracket. A45..A58 above are the physical PCB
    # landings at this cable exit; do not recreate an on-board X9 footprint.
    # X6 itself is on the bracket. AX603/AX604 above preserve its photographed
    # A:3/A:4 component-side cable joints without inventing a PCB connector.

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
