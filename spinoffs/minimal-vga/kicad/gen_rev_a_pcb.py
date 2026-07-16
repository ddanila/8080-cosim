#!/usr/bin/env python3
import json
import os
import sys

import pcbnew


# Footprint library root. Defaults to the Linux/CI location; override with
# KICAD_FOOTPRINTS for other installs (e.g. the macOS app bundle at
# .../KiCad.app/Contents/SharedSupport/footprints).
ROOT = os.environ.get("KICAD_FOOTPRINTS", "/usr/share/kicad/footprints")
BOARD_WIDTH_MM = 285
BOARD_HEIGHT_MM = 285
ZONE_INSET_MM = 3
EDGE_CLEARANCE_MM = 14
CHIP_BLOCK_LABEL_GAP_MM = 2.0
SILK_LABELS = {
    "VJUGA REV A": (158, 268, 0, pcbnew.F_SilkS),
    "Z80 + 4164 DRAM REFRESH TESTBED": (158, 274, 0, pcbnew.F_SilkS, 1.6),
    "FUSE": (24, 42.0, 0, pcbnew.F_SilkS),
    "DEFAULT STROKE SILK": (22, 260, 0, pcbnew.B_SilkS),
}
CHIP_BLOCK_LABELS = {
    "CPU": "U1",
    "ROM": "U2",
    "ADDRESS DECODE": "U5",
    "DRAM CONTROL": "U24",
    "PARALLEL INTERFACE": "U30",
}

SILK_BLOCK_OUTLINES = {
    "POWER": (8, 16, 56, 112),
    "CLOCK_RESET": (232, 34, 276, 92),
    "DRAM_REFRESH_TIMING": (62, 76, 226, 124),
    "DRAM_BANK": (36, 130, 194, 168),
    "KEYBOARD_MATRIX": (42, 176, 190, 248),
    "VGA_OUT": (204, 144, 276, 220),
    "DIAGNOSTIC_LEDS": (204, 226, 276, 270),
    "DEBUG_HEADERS": (20, 252, 132, 281),
}
SILK_BLOCK_LABELS = {
    "POWER": "POWER",
    "CLOCK_RESET": "CLOCK + RESET",
    "DRAM_REFRESH_TIMING": "DRAM REFRESH + TIMING",
    "DRAM_BANK": "DRAM BANK",
    "KEYBOARD_MATRIX": "KEYBOARD MATRIX",
    "VGA_OUT": "VGA OUT",
    "DIAGNOSTIC_LEDS": "DIAGNOSTIC LEDS",
    "DEBUG_HEADERS": "DEBUG HEADERS",
}
SILK_BLOCK_LABEL_PADDING_MM = 2.0

SILK_VALUE_BY_REF = {
    "J1": "5V",
    "J3": "USB-C 5V",
    "J30": "JUKU KBD",
    "J40": "VGA RGB",
    "J90": "A0-A7 CLK",
    "J91": "D0-D7 RST",
    "J92": "DRAM/VIDEO",
    "J93": "PWR DBG",
    "U40": "TTL640x480",
    "U50": "CLK OSC",
    "U51": "RESET",
    "D1": "5V TVS",
    "D2": "PWR",
    "D3": "PWR OK",
    "D4": "CLK",
    "D5": "RESET",
    "D6": "M1",
    "D7": "RFSH",
    "F1": "3A",
}

POWER_INPUT_PIN_LABELS = (
    ("5V IN", 16.1, 25.35, 90),
    ("+5V", 27.85, 27.85, 90),
    ("GND", 27.85, 22.85, 90),
    ("PTC", 18.9, 38.0, 90),
)
POWER_INPUT_PIN_LABEL_SIZE_MM = 1.1
POWER_INPUT_PIN_LABEL_THICKNESS_MM = 0.16

SILK_VALUE_BY_TYPE = {
    "Z80_DIP40": "Z80",
    "PPI_82C55_DIP40": "82C55",
    "ROM_28C256_DIP28": "27C256",
    "GAL22V10_DIP24_DECODE": "GAL22V10",
    "GAL22V10_DIP24_DRAMSEQ": "GAL22V10",
    "DRAM4164_DIP16": "KM4164B",
    "74HCT157_DIP16_ADDRMUX": "74HCT157",
    "74HCT148_DIP16": "74HCT148",
    "74HCT166_DIP16_PIXSHIFT": "74HCT166",
    "74HCT393_DIP14_REFRESH_LOW": "74HCT393 REF",
    "74HCT393_DIP14_VIDEO_LOW": "74HCT393 VID",
    "TTL640X480_HEADER": "TTL640x480",
    "DEBUG_HEADER": "DEBUG",
    "POWER_INPUT_TERMINAL": "5V IN",
    "USB_C_POWER_HRO": "USB-C 5V",
    "KEYBOARD_HEADER": "JUKU KBD",
    "VGA_HEADER": "VGA",
    "OSC_DIP14": "CLK OSC",
    "RESET_SUPERVISOR_TO92": "RESET",
    "PS_ON_HEADER": "PS_ON",
    "POWER_DEBUG_HEADER": "PWR DBG",
    "PROM_556RT4_DIP16": "RT4 DECODE",
    "PROM_155RE3_DIP16": "RE3 PAGER",
    "HEX_INV_74HC04_DIP14": "74HC04",
    "JUMPER_1x2": "CLK SEL",
    "JUMPER_1x3": "MODE A/B",
    "DEBUG_HEADER_1x8": "CTL BUS",
    "DEBUG_HEADER_1x10": "HI ADDR",
    "DEBUG_HEADER_1x14": "DECODE DBG",
}

DOWNSTAIRS_VALUE_REFS = {
    "C50",
    "D1",
    "D2",
    "D3",
    "D4",
    "D5",
    "D6",
    "D7",
    "J3",
    "J30",
    "J40",
    "J90",
    "J91",
    "J92",
    "J93",
    "U51",
}
DOWNSTAIRS_VALUE_TYPES = {
    "TTL640X480_HEADER",
    # Jumpers: print the mode/value label horizontally just below the box
    # instead of vertically alongside it.
    "JUMPER_1x2",
    "JUMPER_1x3",
}

# DIP parts use the _Socket footprints: the nested "double" silk outline is the
# socket body plus the IC, which is intended -- every scarce/swappable chip is
# socketed on this bench fixture, and the socket courtyard must be reserved.
FP_BY_TYPE = {
    "Z80_DIP40": ("Package_DIP.pretty", "DIP-40_W15.24mm_Socket"),
    "PPI_82C55_DIP40": ("Package_DIP.pretty", "DIP-40_W15.24mm_Socket"),
    "ROM_28C256_DIP28": ("Package_DIP.pretty", "DIP-28_W15.24mm_Socket"),
    "GAL22V10_DIP24_DECODE": ("Package_DIP.pretty", "DIP-24_W15.24mm_Socket"),
    "GAL22V10_DIP24_DRAMSEQ": ("Package_DIP.pretty", "DIP-24_W15.24mm_Socket"),
    "DRAM4164_DIP16": ("Package_DIP.pretty", "DIP-16_W7.62mm_Socket"),
    "74HCT157_DIP16_ADDRMUX": ("Package_DIP.pretty", "DIP-16_W7.62mm_Socket"),
    "74HCT148_DIP16": ("Package_DIP.pretty", "DIP-16_W7.62mm_Socket"),
    "74HCT166_DIP16_PIXSHIFT": ("Package_DIP.pretty", "DIP-16_W7.62mm_Socket"),
    "74HCT393_DIP14_REFRESH_LOW": ("Package_DIP.pretty", "DIP-14_W7.62mm_Socket"),
    "74HCT393_DIP14_VIDEO_LOW": ("Package_DIP.pretty", "DIP-14_W7.62mm_Socket"),
    "TTL640X480_HEADER": ("Connector_PinHeader_2.54mm.pretty", "PinHeader_2x06_P2.54mm_Vertical"),
    "DEBUG_HEADER": ("Connector_PinHeader_2.54mm.pretty", "PinHeader_2x05_P2.54mm_Vertical"),
    "POWER_INPUT_TERMINAL": ("TerminalBlock.pretty", "TerminalBlock_MaiXu_MX126-5.0-02P_1x02_P5.00mm"),
    "USB_C_POWER_HRO": ("Connector_USB.pretty", "USB_C_Receptacle_HRO_TYPE-C-31-M-17"),
    "KEYBOARD_HEADER": ("Connector_PinHeader_2.54mm.pretty", "PinHeader_1x15_P2.54mm_Vertical"),
    "VGA_HEADER": ("Connector_PinHeader_2.54mm.pretty", "PinHeader_1x07_P2.54mm_Vertical"),
    "OSC_DIP14": ("Oscillator.pretty", "Oscillator_DIP-14"),
    "RESET_SUPERVISOR_TO92": ("Package_TO_SOT_THT.pretty", "TO-92_Inline"),
    "R_THT": ("Resistor_THT.pretty", "R_Axial_DIN0207_L6.3mm_D2.5mm_P7.62mm_Horizontal"),
    "C_DECOUPLE_THT": ("Capacitor_THT.pretty", "C_Disc_D4.7mm_W2.5mm_P5.00mm"),
    "C_BULK_THT": ("Capacitor_THT.pretty", "CP_Radial_D5.0mm_P2.00mm"),
    "FUSE_THT": ("Fuse.pretty", "Fuse_Bourns_MF-RG300"),
    "D_TVS_THT": ("Diode_THT.pretty", "D_DO-35_SOD27_P7.62mm_Horizontal"),
    "LED_THT": ("LED_THT.pretty", "LED_D3.0mm"),
    "PS_ON_HEADER": ("Connector_PinHeader_2.54mm.pretty", "PinHeader_1x02_P2.54mm_Vertical"),
    "POWER_DEBUG_HEADER": ("Connector_PinHeader_2.54mm.pretty", "PinHeader_1x04_P2.54mm_Vertical"),
    # Phase 3/4 additions: real decode PROM sockets, mode inverter, jumpers,
    # and the observability/high-address/control-bus headers.
    "PROM_556RT4_DIP16": ("Package_DIP.pretty", "DIP-16_W7.62mm_Socket"),
    "PROM_155RE3_DIP16": ("Package_DIP.pretty", "DIP-16_W7.62mm_Socket"),
    "HEX_INV_74HC04_DIP14": ("Package_DIP.pretty", "DIP-14_W7.62mm_Socket"),
    "JUMPER_1x2": ("Connector_PinHeader_2.54mm.pretty", "PinHeader_1x02_P2.54mm_Vertical"),
    "JUMPER_1x3": ("Connector_PinHeader_2.54mm.pretty", "PinHeader_1x03_P2.54mm_Vertical"),
    "DEBUG_HEADER_1x8": ("Connector_PinHeader_2.54mm.pretty", "PinHeader_1x08_P2.54mm_Vertical"),
    "DEBUG_HEADER_1x10": ("Connector_PinHeader_2.54mm.pretty", "PinHeader_1x10_P2.54mm_Vertical"),
    "DEBUG_HEADER_1x14": ("Connector_PinHeader_2.54mm.pretty", "PinHeader_1x14_P2.54mm_Vertical"),
}

# Pad-number aliases for footprints whose pad naming varies by KiCad library
# version. The HRO USB-C shell shield is "S1" in some versions, "SH" in others.
PAD_ALIASES = {
    "S1": ("SH", "SHIELD"),
    "SH": ("S1", "SHIELD"),
}

FP_BY_REF = {
    "J1": ("TerminalBlock_Phoenix.pretty", "TerminalBlock_Phoenix_MKDS-1,5-2-5.08_1x02_P5.08mm_Horizontal"),
    "R30": ("Resistor_THT.pretty", "R_Axial_DIN0204_L3.6mm_D1.6mm_P5.08mm_Horizontal"),
    "R31": ("Resistor_THT.pretty", "R_Axial_DIN0204_L3.6mm_D1.6mm_P5.08mm_Horizontal"),
}

PLACE = {
    "J1": (22, 25.6, 90),
    "J3": (5, 100, 270),     # USB-C rotated 90deg CW, mouth at the left board
                             # edge (fully on-board) so a cable plugs from outside
    "U1": (68, 45, 0),       # clear of the POWER block (right edge x56)
    "U2": (100, 45, 0),
    "U5": (210, 45, 0),
    "U20": (80, 95, 90),     # right of the block's left edge so the refdes clears it
    "U21": (105, 95, 90),
    "U22": (135, 95, 90),
    "U23": (160, 95, 90),
    "U24": (195, 95, 0),
    "U10": (45, 145, 0),
    "U11": (65, 145, 0),
    "U12": (85, 145, 0),
    "U13": (105, 145, 0),
    "U14": (125, 145, 0),
    "U15": (145, 145, 0),
    "U16": (165, 145, 0),
    "U17": (185, 145, 0),
    "U30": (55, 205, 0),
    "U31": (100, 205, 90),
    "J30": (170, 210, 90),
    "U40": (215, 160, 90),
    "U41": (220, 195, 90),
    "J40": (260, 185, 90),
    "J90": (40, 260, 90),
    "J91": (80, 260, 90),
    "J92": (120, 260, 90),
    "U50": (250, 45, 0),
    "U51": (245, 70, 0),
    "R1": (238, 168, 0),
    "R2": (238, 176, 0),
    "R3": (238, 184, 0),
    "R4": (250, 58, 0),
    "R5": (245, 82, 0),
    "R6": (36, 70, 0),
    "R30": (42, 92, 0),
    "R31": (42, 100, 0),
    "R7": (128, 190, 0),
    "R8": (128, 196, 0),
    "R9": (128, 202, 0),
    "R10": (128, 208, 0),
    "R11": (128, 214, 0),
    "R12": (128, 220, 0),
    "R13": (128, 226, 0),
    "R14": (128, 232, 0),
    "R15": (104, 242, 0),
    "R16": (118, 190, 0),
    "R17": (118, 196, 0),
    "R18": (118, 202, 0),
    "R19": (118, 208, 0),
    "R20": (118, 214, 0),
    "R21": (118, 220, 0),
    "R22": (118, 226, 0),
    "R23": (118, 232, 0),
    "D2": (212, 236, 0),
    "D3": (222, 236, 0),
    "D4": (232, 236, 0),
    "D5": (242, 236, 0),
    "D6": (252, 236, 0),
    "D7": (262, 236, 0),
    "R24": (212, 246, 0),
    "R25": (222, 246, 0),
    "R26": (232, 246, 0),
    "R27": (242, 246, 0),
    "R28": (252, 246, 0),
    "R29": (262, 246, 0),
    "C50": (28, 48, 0),
    "F1": (24, 38, 0),
    "D1": (38, 56, 90),
    "J93": (60, 260, 90),
    # Phase 3/4 decode + observability parts (first-pass placement for review).
    # Decode PROMs sit between ROM (U2) and the decode GAL (U5) in the top band.
    "U3": (130, 62, 0),      # К556РТ4 memory-map decode
    "U4": (158, 62, 0),      # К155РЕ3 ROM pager
    "U6": (186, 62, 0),      # 74HC04 PC0/PC1 inverter
    # Decoupling caps: C26/C27 in the clear gaps between the decode chips;
    # C28 above U6 (the U6-U5 gap collides with the ADDRESS DECODE label).
    "C26": (144, 62, 0), "C27": (172, 62, 0), "C28": (182, 44, 0),
    "J94": (117, 58, 90),    # decode-mode jumper, in the gap left of U3 (clear of U5)
    "R44": (117, 68, 0),     # MODE_B default pull-down
    "J96": (266, 62, 90),    # clock-select jumper, near the oscillator U50
    # PROM output pull-ups, clustered in the free strip between CLOCK/RESET and VGA.
    "R32": (250, 100, 0), "R33": (250, 107, 0), "R34": (250, 114, 0), "R35": (250, 121, 0),
    "R36": (262, 100, 0), "R37": (262, 107, 0), "R38": (262, 114, 0), "R39": (262, 121, 0),
    "R40": (238, 100, 0), "R41": (238, 107, 0), "R42": (238, 114, 0), "R43": (238, 121, 0),
    # Observability headers: stacked in the clear vertical corridor between the
    # keyboard matrix (right edge x190) and the VGA/LED blocks (left edge x204),
    # away from the board title and block outlines.
    "J95": (198, 158, 0),    # decode-debug (РТ4 outs, РЕ3 byte, REV_OUT) 1x14
    "J97": (198, 198, 0),    # high address + MEM_WR_N 1x10
    "J98": (198, 233, 0),    # Z80 control bus 1x8
}

DECOUPLE_NEAR = {
    "U1": (84, 45, 90), "U2": (115, 29, 90), "SPARE_GLUE1": (140, 36, 0),
    "SPARE_GLUE2": (170, 36, 0), "U5": (225, 31, 90), "U10": (45, 161, 0),
    "U11": (65, 161, 0), "U12": (85, 161, 0), "U13": (105, 161, 0),
    "U14": (125, 161, 0), "U15": (145, 161, 0), "U16": (165, 161, 0),
    "U17": (185, 161, 0), "U20": (68.5, 86, 0), "U21": (98.5, 86, 0),
    "U22": (130, 86, 0), "U23": (155, 86, 0), "U24": (210, 88, 90),
    "SPARE_GLUE3": (220, 86, 0), "U30": (69, 214, 90), "U31": (93.5, 194, 90),
    "U40": (244, 156, 90), "U41": (213.5, 184, 90), "U50": (266, 45, 90),
    "U51": (252, 70, 90),
}

for idx, owner in enumerate(DECOUPLE_NEAR, start=1):
    PLACE[f"C{idx}"] = DECOUPLE_NEAR[owner]


def mm(value):
    return pcbnew.FromMM(value)


def load_footprint(typ, ref=None):
    lib, name = FP_BY_REF.get(ref, FP_BY_TYPE[typ])
    path = os.path.join(ROOT, lib)
    fp = pcbnew.FootprintLoad(path, name)
    if fp is None:
        raise RuntimeError(f"missing footprint {lib}/{name}")
    return fp


def center_footprint(fp, x, y):
    fp.SetPosition(pcbnew.VECTOR2I(mm(x), mm(y)))
    box = fp.GetBoundingBox(False, False)
    center = box.GetCenter()
    fp.SetPosition(pcbnew.VECTOR2I(2 * mm(x) - center.x, 2 * mm(y) - center.y))


def style_field(field, text, x, y, angle, size=1.4):
    field.SetText(text)
    field.SetVisible(True)
    field.SetLayer(pcbnew.F_SilkS)
    field.SetTextPos(pcbnew.VECTOR2I(mm(x), mm(y)))
    field.SetTextAngleDegrees(angle)
    field.SetTextSize(pcbnew.VECTOR2I(mm(size), mm(size)))
    field.SetTextThickness(mm(0.16))
    field.SetHorizJustify(pcbnew.GR_TEXT_H_ALIGN_CENTER)
    field.SetVertJustify(pcbnew.GR_TEXT_V_ALIGN_CENTER)
    field.SetKeepUpright(True)
    field.SetItalic(False)


def value_for_chip(chip):
    if chip["ref"] in SILK_VALUE_BY_REF:
        return SILK_VALUE_BY_REF[chip["ref"]]
    if chip["type"] in SILK_VALUE_BY_TYPE:
        return SILK_VALUE_BY_TYPE[chip["type"]]
    if chip.get("value"):
        return chip["value"]
    return chip["type"]


def place_silk_fields(fp, chip, x, y, rot):
    box = fp.GetBoundingBox(False, False)
    left = pcbnew.ToMM(box.GetLeft())
    top = pcbnew.ToMM(box.GetTop())
    right = pcbnew.ToMM(box.GetRight())
    bottom = pcbnew.ToMM(box.GetBottom())
    cx = (left + right) / 2
    cy = (top + bottom) / 2
    ref = chip["ref"]
    value = value_for_chip(chip)
    non_dip_assembly_part = ref[0] in {"R", "C", "D", "F", "J"} or chip["type"] in {
        "POWER_DEBUG_HEADER",
        "DEBUG_HEADER",
        "POWER_INPUT_TERMINAL",
        "USB_C_POWER_HRO",
        "KEYBOARD_HEADER",
        "VGA_HEADER",
        "TTL640X480_HEADER",
        "OSC_DIP14",
        "RESET_SUPERVISOR_TO92",
    }

    if non_dip_assembly_part:
        if ref == "J1":
            fp.Value().SetVisible(False)
            style_field(fp.Reference(), ref, cx, top - 0.9, 0, size=1.15)
            return

        if ref == "J3":
            # Edge connector: keep both labels inboard (to the right of the body),
            # clear of the board edge on its left.
            style_field(fp.Reference(), ref, right + 5.5, cy - 2.2, 0, size=0.85)
            style_field(fp.Value(), value, right + 5.5, cy + 2.2, 0, size=0.85)
            return

        # Tall 1xN observability headers (J95/J97/J98): the descriptive value runs
        # vertically ALONG the long side, not horizontally across the pins.
        if chip["type"] in {"DEBUG_HEADER_1x8", "DEBUG_HEADER_1x10", "DEBUG_HEADER_1x14"}:
            value_size = 0.85 if len(value) > 6 else 0.95
            style_field(fp.Value(), value, right + 1.4, cy, 90, size=value_size)
            style_field(fp.Reference(), ref, cx, top - 1.4, 0, size=0.8)
            return

        if ref in DOWNSTAIRS_VALUE_REFS or chip["type"] in DOWNSTAIRS_VALUE_TYPES:
            value_size = 0.85 if len(value) > 6 else 0.95
            if len(value) > 9:
                value_size = 0.72
            style_field(fp.Value(), value, cx, bottom + 1.8, 0, size=value_size)
            style_field(fp.Reference(), ref, cx, top - 1.4, 0, size=0.8)
            return

        value_angle = 90 if rot % 180 else 0
        ref_angle = value_angle
        if ref[0] == "D" and chip["type"] == "LED_THT":
            value_angle = 90
            ref_angle = 90
        value_size = 0.85 if len(value) > 6 else 0.95
        if len(value) > 9:
            value_size = 0.72
        style_field(fp.Value(), value, cx, cy, value_angle, size=value_size)

        if rot % 180:
            ref_x = cx
            ref_y = top - 1.8
            ref_angle = 0
        else:
            ref_x = cx
            ref_y = top - 1.8
            ref_angle = 0
        if ref[0] == "R" and rot % 180 == 0:
            ref_y = top - 1.4
        if ref[0] == "F":
            ref_y = top - 0.9
        if ref[0] == "C":
            ref_y = bottom + 1.3
        if ref[0] == "D" and chip["type"] == "LED_THT":
            ref_x = cx
            ref_y = bottom + 1.3
        style_field(fp.Reference(), ref, ref_x, ref_y, ref_angle, size=0.8)
        return

    # Refdes sits on the keyed short side; chip value follows the DIP long axis.
    ref_angle = 90 if rot % 180 else 0
    value_angle = 0 if rot % 180 else 90

    if rot % 180:
        ref_x = left - 2.0
        ref_y = cy
    else:
        ref_x = cx
        ref_y = top - 2.2

    style_field(fp.Reference(), ref, ref_x, ref_y, ref_angle, size=1.15)
    show_chip_value = (
        ref.startswith("U")
        and "DIP" in chip["type"]
        and chip["type"] not in {"OSC_DIP14"}
    )
    if show_chip_value:
        style_field(fp.Value(), value, cx, cy, value_angle, size=1.35)
    else:
        fp.Value().SetVisible(False)


def add_outline(board, width, height):
    def edge(x1, y1, x2, y2):
        shape = pcbnew.PCB_SHAPE(board)
        shape.SetShape(pcbnew.SHAPE_T_SEGMENT)
        shape.SetLayer(pcbnew.Edge_Cuts)
        shape.SetWidth(mm(0.15))
        shape.SetStart(pcbnew.VECTOR2I(mm(x1), mm(y1)))
        shape.SetEnd(pcbnew.VECTOR2I(mm(x2), mm(y2)))
        board.Add(shape)

    edge(0, 0, width, 0)
    edge(width, 0, width, height)
    edge(width, height, 0, height)
    edge(0, height, 0, 0)


def add_mounting_hole(board, x, y):
    hole = pcbnew.PCB_SHAPE(board)
    hole.SetShape(pcbnew.SHAPE_T_CIRCLE)
    hole.SetLayer(pcbnew.Edge_Cuts)
    hole.SetWidth(mm(0.15))
    hole.SetCenter(pcbnew.VECTOR2I(mm(x), mm(y)))
    hole.SetEnd(pcbnew.VECTOR2I(mm(x + 1.6), mm(y)))
    board.Add(hole)


def add_power_zone(board, net, layer, name):
    zone = pcbnew.ZONE(board)
    zone.SetLayer(layer)
    zone.SetNet(net)
    zone.SetZoneName(name)
    for x, y in (
        (ZONE_INSET_MM, ZONE_INSET_MM),
        (BOARD_WIDTH_MM - ZONE_INSET_MM, ZONE_INSET_MM),
        (BOARD_WIDTH_MM - ZONE_INSET_MM, BOARD_HEIGHT_MM - ZONE_INSET_MM),
        (ZONE_INSET_MM, BOARD_HEIGHT_MM - ZONE_INSET_MM),
    ):
        zone.AppendCorner(pcbnew.VECTOR2I(mm(x), mm(y)), -1)
    board.Add(zone)


def add_silk_label(board, text, x, y, angle, layer, size=2.0):
    label = pcbnew.PCB_TEXT(board)
    label.SetLayer(layer)
    label.SetText(text)
    label.SetTextPos(pcbnew.VECTOR2I(mm(x), mm(y)))
    label.SetTextAngleDegrees(angle)
    label.SetTextSize(pcbnew.VECTOR2I(mm(size), mm(size)))
    label.SetTextThickness(mm(0.2))
    label.SetItalic(False)
    board.Add(label)


def add_chip_block_label(board, text, fp):
    box = fp.GetBoundingBox(False, False)
    x = (pcbnew.ToMM(box.GetLeft()) + pcbnew.ToMM(box.GetRight())) / 2
    y = pcbnew.ToMM(box.GetBottom()) + CHIP_BLOCK_LABEL_GAP_MM
    size = 1.45 if len(text) > 12 else 2.0
    label = pcbnew.PCB_TEXT(board)
    label.SetLayer(pcbnew.F_SilkS)
    label.SetText(text)
    label.SetTextPos(pcbnew.VECTOR2I(mm(x), mm(y)))
    label.SetTextAngleDegrees(0)
    label.SetTextSize(pcbnew.VECTOR2I(mm(size), mm(size)))
    label.SetTextThickness(mm(0.2))
    label.SetItalic(False)
    label.SetHorizJustify(pcbnew.GR_TEXT_H_ALIGN_CENTER)
    label.SetVertJustify(pcbnew.GR_TEXT_V_ALIGN_TOP)
    board.Add(label)


# Blocks whose bottom-left corner is occupied (a decoupling cap + its refdes),
# so the block title is printed just BELOW the frame instead of inside it.
SILK_BLOCK_LABEL_BELOW = {"DRAM_BANK"}


def add_silk_block_label(board, text, bounds, name=None):
    left, _, _, bottom = bounds
    label = pcbnew.PCB_TEXT(board)
    label.SetLayer(pcbnew.F_SilkS)
    label.SetText(text)
    if name in SILK_BLOCK_LABEL_BELOW:
        y = bottom + SILK_BLOCK_LABEL_PADDING_MM
        vjust = pcbnew.GR_TEXT_V_ALIGN_TOP
    else:
        y = bottom - SILK_BLOCK_LABEL_PADDING_MM
        vjust = pcbnew.GR_TEXT_V_ALIGN_BOTTOM
    label.SetTextPos(pcbnew.VECTOR2I(mm(left + SILK_BLOCK_LABEL_PADDING_MM), mm(y)))
    label.SetTextAngleDegrees(0)
    label.SetTextSize(pcbnew.VECTOR2I(mm(2.0), mm(2.0)))
    label.SetTextThickness(mm(0.2))
    label.SetItalic(False)
    label.SetHorizJustify(pcbnew.GR_TEXT_H_ALIGN_LEFT)
    label.SetVertJustify(vjust)
    board.Add(label)


def add_silk_segment(board, x1, y1, x2, y2, layer=pcbnew.F_SilkS):
    shape = pcbnew.PCB_SHAPE(board)
    shape.SetShape(pcbnew.SHAPE_T_SEGMENT)
    shape.SetLayer(layer)
    shape.SetWidth(mm(0.15))
    shape.SetStart(pcbnew.VECTOR2I(mm(x1), mm(y1)))
    shape.SetEnd(pcbnew.VECTOR2I(mm(x2), mm(y2)))
    board.Add(shape)


def add_silk_rect(board, left, top, right, bottom, layer=pcbnew.F_SilkS):
    add_silk_segment(board, left, top, right, top, layer)
    add_silk_segment(board, right, top, right, bottom, layer)
    add_silk_segment(board, right, bottom, left, bottom, layer)
    add_silk_segment(board, left, bottom, left, top, layer)


def add_small_silk_label(board, text, x, y, angle=0, layer=pcbnew.F_SilkS):
    label = pcbnew.PCB_TEXT(board)
    label.SetLayer(layer)
    label.SetText(text)
    label.SetTextPos(pcbnew.VECTOR2I(mm(x), mm(y)))
    label.SetTextAngleDegrees(angle)
    label.SetTextSize(
        pcbnew.VECTOR2I(
            mm(POWER_INPUT_PIN_LABEL_SIZE_MM),
            mm(POWER_INPUT_PIN_LABEL_SIZE_MM),
        )
    )
    label.SetTextThickness(mm(POWER_INPUT_PIN_LABEL_THICKNESS_MM))
    label.SetItalic(False)
    board.Add(label)

def main():
    board_json = sys.argv[1] if len(sys.argv) > 1 else "spinoffs/minimal-vga/kicad/rev-a-physical.board.json"
    out = sys.argv[2] if len(sys.argv) > 2 else "spinoffs/minimal-vga/kicad/rev-a-physical.kicad_pcb"
    spec = json.load(open(board_json))

    board = pcbnew.BOARD()
    board.SetCopperLayerCount(4)
    board.GetDesignSettings().SetCopperLayerCount(4)
    placed = {}
    nets = {}
    assigned = 0

    for chip in spec["chips"]:
        ref = chip["ref"]
        typ = chip["type"]
        if typ not in FP_BY_TYPE:
            raise RuntimeError(f"no footprint mapping for {typ}")
        fp = load_footprint(typ, ref)
        fp.SetReference(ref)
        fp.SetValue(chip.get("value", typ))
        x, y, rot = PLACE.get(ref, (30 + len(placed) % 8 * 28, 30 + len(placed) // 8 * 35, 0))
        if rot:
            fp.SetOrientationDegrees(rot)
        board.Add(fp)
        center_footprint(fp, x, y)
        place_silk_fields(fp, chip, x, y, rot)
        placed[ref] = fp

    for net_name, entry in spec["nets"].items():
        net = pcbnew.NETINFO_ITEM(board, net_name)
        board.Add(net)
        nets[net_name] = net
        node_list = entry["nodes"] if isinstance(entry, dict) else entry
        for ref, pin in node_list:
            fp = placed.get(ref)
            if fp is None:
                continue
            matching_pads = [
                pad for pad in fp.Pads() if str(pad.GetNumber()) == str(pin)
            ]
            if not matching_pads:
                # The USB-C shell shield pad is numbered differently across KiCad
                # footprint-library versions ("S1" vs "SH"); accept either so the
                # same board model generates on both the Linux box and macOS.
                aliases = PAD_ALIASES.get(str(pin), ())
                matching_pads = [
                    pad for pad in fp.Pads() if str(pad.GetNumber()) in aliases
                ]
            if not matching_pads:
                footprint_name = str(fp.GetFPID().GetLibItemName())
                raise RuntimeError(f"{ref}.{pin} has no pad on {footprint_name}")
            # Some footprints use one logical pin number on several physical
            # pads (the HRO USB-C shell has four S1 tabs). All of those pads
            # belong to the modeled net; assigning only FindPadByNumber's first
            # result silently left the remaining shell tabs floating.
            for pad in matching_pads:
                pad.SetNet(net)
                assigned += 1

    if os.environ.get("MINIMAL_VGA_NO_ZONES", "0") != "1":
        add_power_zone(board, nets["GND"], pcbnew.In1_Cu, "Rev A GND plane placeholder")
        add_power_zone(board, nets["VCC"], pcbnew.In2_Cu, "Rev A VCC plane placeholder")

    add_outline(board, BOARD_WIDTH_MM, BOARD_HEIGHT_MM)
    for x, y in ((8, 8), (277, 8), (8, 277), (277, 277)):
        add_mounting_hole(board, x, y)
    for label, settings in SILK_LABELS.items():
        x, y, angle, layer, *rest = settings
        size = rest[0] if rest else 2.0
        add_silk_label(board, label, x, y, angle, layer, size)
    for label, ref in CHIP_BLOCK_LABELS.items():
        add_chip_block_label(board, label, placed[ref])
    for name, bounds in SILK_BLOCK_OUTLINES.items():
        left, top, right, bottom = bounds
        add_silk_rect(board, left, top, right, bottom)
        add_silk_block_label(board, SILK_BLOCK_LABELS[name], bounds, name)
    for label, x, y, angle in POWER_INPUT_PIN_LABELS:
        add_small_silk_label(board, label, x, y, angle)

    pcbnew.SaveBoard(out, board)
    board = pcbnew.LoadBoard(out)
    if board.Zones():
        pcbnew.ZONE_FILLER(board).Fill(board.Zones())
    pcbnew.SaveBoard(out, board)
    board = pcbnew.LoadBoard(out)
    board.EmbedFonts()
    pcbnew.SaveBoard(out, board)
    print(f"wrote {out}: {len(placed)} footprints, {board.GetNetCount()} nets, {assigned} pad-net assignments")


if __name__ == "__main__":
    main()
