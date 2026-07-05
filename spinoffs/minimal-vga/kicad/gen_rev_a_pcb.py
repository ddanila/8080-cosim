#!/usr/bin/env python3
import json
import os
import sys

import pcbnew


ROOT = "/usr/share/kicad/footprints"
BOARD_WIDTH_MM = 285
BOARD_HEIGHT_MM = 285
ZONE_INSET_MM = 3
EDGE_CLEARANCE_MM = 14
SILK_LABELS = {
    "VJUGA REV A": (25, 76, 0, pcbnew.F_SilkS),
    "Z80 + 4164 DRAM REFRESH TESTBED": (25, 82, 0, pcbnew.F_SilkS),
    "POWER": (22, 32.7, 0, pcbnew.F_SilkS),
    "FUSE": (24, 42.0, 0, pcbnew.F_SilkS),
    "CPU": (55, 75.5, 0, pcbnew.F_SilkS),
    "ROM": (100, 75.5, 0, pcbnew.F_SilkS),
    "DRAM REFRESH + TIMING": (150, 116, 0, pcbnew.F_SilkS),
    "DRAM BANK": (115, 166, 0, pcbnew.F_SilkS),
    "KEYBOARD MATRIX": (116, 247, 0, pcbnew.F_SilkS),
    "VGA OUT": (260, 198, 0, pcbnew.F_SilkS),
    "DIAGNOSTIC LEDS": (236, 260, 0, pcbnew.F_SilkS),
    "DEBUG HEADERS": (32, 274, 0, pcbnew.F_SilkS),
    "DEFAULT STROKE SILK": (22, 260, 0, pcbnew.B_SilkS),
}

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
    "GAL22V10_DIP24_DECODE": "GAL22V10 DEC",
    "GAL22V10_DIP24_DRAMSEQ": "GAL22V10 DRAM",
    "74HCT245_DIP20": "74HCT245",
    "74HCT573_DIP20": "74HCT573",
    "DRAM4164_DIP16": "KM4164B",
    "74HCT157_DIP16_ADDRMUX": "74HCT157",
    "74HCT148_DIP16": "74HCT148",
    "74HCT166_DIP16_PIXSHIFT": "74HCT166",
    "74HCT393_DIP14_REFRESH_LOW": "74HCT393 REF",
    "74HCT393_DIP14_VIDEO_LOW": "74HCT393 VID",
    "74HCT00_DIP14_DRAMGATE": "74HCT00",
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
}

FP_BY_TYPE = {
    "Z80_DIP40": ("Package_DIP.pretty", "DIP-40_W15.24mm_Socket"),
    "PPI_82C55_DIP40": ("Package_DIP.pretty", "DIP-40_W15.24mm_Socket"),
    "ROM_28C256_DIP28": ("Package_DIP.pretty", "DIP-28_W15.24mm_Socket"),
    "GAL22V10_DIP24_DECODE": ("Package_DIP.pretty", "DIP-24_W15.24mm_Socket"),
    "GAL22V10_DIP24_DRAMSEQ": ("Package_DIP.pretty", "DIP-24_W15.24mm_Socket"),
    "74HCT245_DIP20": ("Package_DIP.pretty", "DIP-20_W7.62mm_Socket"),
    "74HCT573_DIP20": ("Package_DIP.pretty", "DIP-20_W7.62mm_Socket"),
    "DRAM4164_DIP16": ("Package_DIP.pretty", "DIP-16_W7.62mm_Socket"),
    "74HCT157_DIP16_ADDRMUX": ("Package_DIP.pretty", "DIP-16_W7.62mm_Socket"),
    "74HCT148_DIP16": ("Package_DIP.pretty", "DIP-16_W7.62mm_Socket"),
    "74HCT166_DIP16_PIXSHIFT": ("Package_DIP.pretty", "DIP-16_W7.62mm_Socket"),
    "74HCT393_DIP14_REFRESH_LOW": ("Package_DIP.pretty", "DIP-14_W7.62mm_Socket"),
    "74HCT393_DIP14_VIDEO_LOW": ("Package_DIP.pretty", "DIP-14_W7.62mm_Socket"),
    "74HCT00_DIP14_DRAMGATE": ("Package_DIP.pretty", "DIP-14_W7.62mm_Socket"),
    "TTL640X480_HEADER": ("Connector_PinHeader_2.54mm.pretty", "PinHeader_2x05_P2.54mm_Vertical"),
    "DEBUG_HEADER": ("Connector_PinHeader_2.54mm.pretty", "PinHeader_2x05_P2.54mm_Vertical"),
    "POWER_INPUT_TERMINAL": ("TerminalBlock.pretty", "TerminalBlock_MaiXu_MX126-5.0-02P_1x02_P5.00mm"),
    "USB_C_POWER_HRO": ("Connector_USB.pretty", "USB_C_Receptacle_HRO_TYPE-C-31-M-17"),
    "KEYBOARD_HEADER": ("Connector_PinHeader_2.54mm.pretty", "PinHeader_1x15_P2.54mm_Vertical"),
    "VGA_HEADER": ("Connector_PinHeader_2.54mm.pretty", "PinHeader_1x06_P2.54mm_Vertical"),
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
}

PLACE = {
    "J1": (22, 25.6, 90),
    "J3": (24, 100, 0),
    "U1": (55, 45, 0),
    "U2": (100, 45, 0),
    "U3": (140, 45, 90),
    "U4": (170, 45, 90),
    "U5": (210, 45, 0),
    "U20": (75, 95, 90),
    "U21": (105, 95, 90),
    "U22": (135, 95, 90),
    "U23": (160, 95, 90),
    "U24": (195, 95, 0),
    "U25": (225, 95, 90),
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
}

DECOUPLE_NEAR = {
    "U1": (70, 22, 0), "U2": (115, 22, 0), "U3": (130, 58, 90),
    "U4": (160, 58, 90), "U5": (225, 22, 0), "U10": (45, 124, 0),
    "U11": (65, 124, 0), "U12": (85, 124, 0), "U13": (105, 124, 0),
    "U14": (125, 124, 0), "U15": (145, 124, 0), "U16": (165, 124, 0),
    "U17": (185, 124, 0), "U20": (70, 108, 90), "U21": (100, 108, 90),
    "U22": (135, 108, 90), "U23": (160, 108, 90), "U24": (210, 108, 0),
    "U25": (225, 108, 90), "U30": (70, 182, 0), "U31": (100, 220, 90),
    "U40": (215, 145, 90), "U41": (220, 210, 90), "U50": (266, 45, 0),
    "U51": (258, 70, 0),
}

for idx, owner in enumerate(DECOUPLE_NEAR, start=1):
    PLACE[f"C{idx}"] = DECOUPLE_NEAR[owner]


def mm(value):
    return pcbnew.FromMM(value)


def load_footprint(typ):
    lib, name = FP_BY_TYPE[typ]
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


def add_silk_label(board, text, x, y, angle, layer):
    label = pcbnew.PCB_TEXT(board)
    label.SetLayer(layer)
    label.SetText(text)
    label.SetTextPos(pcbnew.VECTOR2I(mm(x), mm(y)))
    label.SetTextAngleDegrees(angle)
    label.SetTextSize(pcbnew.VECTOR2I(mm(2.0), mm(2.0)))
    label.SetTextThickness(mm(0.2))
    label.SetItalic(False)
    board.Add(label)


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
        fp = load_footprint(typ)
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
            pad = fp.FindPadByNumber(str(pin))
            if pad is None:
                raise RuntimeError(f"{ref}.{pin} has no pad on {fp.GetFPID().Format()}")
            pad.SetNet(net)
            assigned += 1

    if os.environ.get("MINIMAL_VGA_NO_ZONES", "0") != "1":
        add_power_zone(board, nets["GND"], pcbnew.In1_Cu, "Rev A GND plane placeholder")
        add_power_zone(board, nets["VCC"], pcbnew.In2_Cu, "Rev A VCC plane placeholder")

    add_outline(board, BOARD_WIDTH_MM, BOARD_HEIGHT_MM)
    for x, y in ((8, 8), (277, 8), (8, 277), (277, 277)):
        add_mounting_hole(board, x, y)
    for label, (x, y, angle, layer) in SILK_LABELS.items():
        add_silk_label(board, label, x, y, angle, layer)
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
