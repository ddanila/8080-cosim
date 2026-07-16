#!/usr/bin/env python3
import json
import math
import os
import sys

import pcbnew


# Footprint library root. Defaults to the Linux/CI location; override with
# KICAD_FOOTPRINTS for other installs (e.g. the macOS app bundle at
# .../KiCad.app/Contents/SharedSupport/footprints).
ROOT = os.environ.get("KICAD_FOOTPRINTS", "/usr/share/kicad/footprints")
BOARD_WIDTH_MM = 200
BOARD_HEIGHT_MM = 200
ZONE_INSET_MM = 3
EDGE_CLEARANCE_MM = 5
CHIP_BLOCK_LABEL_GAP_MM = 2.0
SILK_LABELS = {
    # Board banner along the top edge, above the CPU/ROM decoupling caps.
    "VJUGA REV A": (100, 2.4, 0, pcbnew.F_SilkS, 1.8),
    "Z80 + 4164 DRAM REFRESH TESTBED": (100, 5.0, 0, pcbnew.F_SilkS, 1.5),
    # Back-silk stroke-style marker (does not collide with front-side parts).
    "DEFAULT STROKE SILK": (100, 196, 0, pcbnew.B_SilkS),
}
# Single-chip block titles printed under the named chip (no enclosing rectangle).
CHIP_BLOCK_LABELS = {
    "CPU": "U1",
    "ROM": "U2",
    "ADDRESS DECODE": "U5",
    "DRAM CONTROL": "U24",
    "PARALLEL INTERFACE": "U30",
}

# Functional-block members. The block's silk rectangle is the grid-snapped
# bounding box of these parts (see compute_block_outlines); far-flung support
# parts (left resistor field, spares) intentionally sit outside any block.
BLOCK_MEMBERS = {
    "POWER": ["J1", "J3", "F1", "D1", "C50", "R6", "R30", "R31"],
    "CLOCK_RESET": ["U50", "U51", "R4", "R5", "J96", "C24", "C25"],
    "DRAM_REFRESH_TIMING": ["U20", "U21", "U22", "U23", "U24",
                             "C14", "C15", "C16", "C17", "C18"],
    "DRAM_BANK": ["U10", "U11", "U12", "U13", "U14", "U15", "U16", "U17",
                   "C6", "C7", "C8", "C9", "C10", "C11", "C12", "C13"],
    "KEYBOARD_MATRIX": ["U30", "U31", "J30", "C20", "C21"],
    "VGA_OUT": ["U40", "U41", "J40", "C22", "C23"],
    # DIAGNOSTIC_LEDS has no frame: the LEDs sit in a tight right-edge corner
    # between VGA and the keyboard where no clean rectangle fits; the LEDs carry
    # descriptive silk values (PWR/CLK/RESET/...) instead, like the CPU/ROM chips.
    "DEBUG_HEADERS": ["J90", "J91", "J92", "J93", "J95", "J97", "J98"],
}
BLOCK_EDGE_CONNECTORS = {"J3"}   # overhang the board edge; excluded from frames
BLOCK_PAD_MM = 1.5
# Block borders snap to the 0.1" DIP sub-grid (half the 0.2" placement grid). On
# the compact board a full-0.2" snap would inflate neighbouring boxes until they
# overlapped; the sub-grid still lines every border up with the pin grid.
BLOCK_SNAP_MM = 2.54

# Filled at build time from the placed footprints (grid-snapped cluster bboxes).
SILK_BLOCK_OUTLINES = {}


def compute_block_outlines(placed):
    """Grid-aligned rectangle around each block's member footprints."""
    outlines = {}
    for name, refs in BLOCK_MEMBERS.items():
        # Edge connectors (USB-C J3) overhang the board edge; exclude them so the
        # frame and its title stay on-board.
        boxes = [
            placed[r].GetBoundingBox(False, False)
            for r in refs
            if r in placed and r not in BLOCK_EDGE_CONNECTORS
        ]
        if not boxes:
            continue
        left = min(pcbnew.ToMM(b.GetLeft()) for b in boxes) - BLOCK_PAD_MM
        top = min(pcbnew.ToMM(b.GetTop()) for b in boxes) - BLOCK_PAD_MM
        right = max(pcbnew.ToMM(b.GetRight()) for b in boxes) + BLOCK_PAD_MM
        bottom = max(pcbnew.ToMM(b.GetBottom()) for b in boxes) + BLOCK_PAD_MM
        outlines[name] = (
            round(math.floor(left / BLOCK_SNAP_MM) * BLOCK_SNAP_MM, 3),
            round(math.floor(top / BLOCK_SNAP_MM) * BLOCK_SNAP_MM, 3),
            round(math.ceil(right / BLOCK_SNAP_MM) * BLOCK_SNAP_MM, 3),
            round(math.ceil(bottom / BLOCK_SNAP_MM) * BLOCK_SNAP_MM, 3),
        )
    return outlines
SILK_BLOCK_LABELS = {
    "POWER": "POWER",
    "CLOCK_RESET": "CLOCK + RESET",
    "DRAM_REFRESH_TIMING": "DRAM REFRESH + TIMING",
    "DRAM_BANK": "DRAM BANK",
    "KEYBOARD_MATRIX": "KEYBOARD MATRIX",
    "VGA_OUT": "VGA OUT",
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

# Re-added (grid-aligned to the new J1 terminal) once the 200x200 placement is
# frozen; empty meanwhile so stale coordinates can't collide with parts.
POWER_INPUT_PIN_LABELS = ()
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

# ============================ Compact 200x200 floorplan ============================
# Everything snaps to a 0.2" (5.08 mm) grid -- 2x the DIP pin pitch, so chips are
# grid-aligned AND their pins stay on the native 0.1" grid. Positions below are in
# GRID CELLS (col, row); PLACE is built from them in millimetres. Decoupling caps
# are auto-placed at the short (top) side of their IC, near the power pins
# (adequate at 4 MHz; the high-freq via/proximity rules do not apply here).
GRID = 5.08


def g(col, row, rot=0):
    return (round(col * GRID, 3), round(row * GRID, 3), rot)


# Each IC's decoupling cap; auto-placed at the IC short side (direction below).
IC_CAP = {
    "U1": "C1", "U2": "C2", "U3": "C26", "U4": "C27", "U5": "C5", "U6": "C28",
    "U10": "C6", "U11": "C7", "U12": "C8", "U13": "C9", "U14": "C10", "U15": "C11",
    "U16": "C12", "U17": "C13", "U20": "C14", "U21": "C15", "U22": "C16",
    "U23": "C17", "U24": "C18", "U30": "C20", "U31": "C21", "U40": "C22",
    "U41": "C23", "U50": "C24", "U51": "C25",
}
# Cap direction relative to its IC: default "up" (place above the body). The top
# logic band hugs the board's top edge, so its caps drop "down" into the gap
# below instead; a few tight spots push their cap sideways.
CAP_DIR = {
    "U1": "up", "U2": "up",              # caps above CPU/ROM, clearing the chip labels below
    "U40": "left", "U41": "left",        # VGA column: caps inboard, off the LED strip
    "U50": "left", "U51": "down",        # clock/reset: caps clear of the edge
}
SPARE_CAPS = ["C3", "C4", "C19"]   # extra decouplers, tucked in open spots

# ---------------------------------------------------------------------------
# Auto-packer: computes grid-aligned positions from real footprint sizes so no
# two bodies overlap by construction. Bands pack left-to-right; fields pack as
# grids; caps land at each IC's short side. Everything snaps to the 5.08 mm grid.
# ---------------------------------------------------------------------------
LABEL_MM = 5.0   # extra room reserved around a part for its silk labels


def build_placement(spec):
    type_of = {c["ref"]: c["type"] for c in spec["chips"]}
    _sz = {}

    def size(ref, rot=0):
        key = FP_BY_REF.get(ref, FP_BY_TYPE[type_of[ref]])
        if key not in _sz:
            fp = load_footprint(type_of[ref], ref)
            bb = fp.GetBoundingBox(False, False)
            _sz[key] = (pcbnew.ToMM(bb.GetWidth()), pcbnew.ToMM(bb.GetHeight()))
        w, h = _sz[key]
        return (h, w) if rot % 180 else (w, h)

    cell = {}

    def put(ref, col, row, rot=0):
        cell[ref] = (round(col), round(row), rot)

    def cells(mm):
        return math.ceil(mm / GRID)

    def row(items, col0, rowc, gap_mm=3.5):
        # Pack items left-to-right on integer grid cells; advancing by whole
        # cells guarantees the requested body gap survives the grid snap.
        cur = pw = None
        for ref, rot in items:
            w, _ = size(ref, rot)
            c = col0 + cells(w / 2) if cur is None else cur + cells(pw / 2 + w / 2 + gap_mm)
            put(ref, c, rowc, rot)
            cur, pw = c, w
        return cur

    def grid(refs, col0, row0, ncols, colp, rowp, rot=0):
        for i, ref in enumerate(refs):
            put(ref, col0 + (i % ncols) * colp, row0 + (i // ncols) * rowp, rot)

    # Board is 39 cells (200 mm) square. The two DIP-40s, the DIP-28 ROM and the
    # two DIP-24 GALs are laid HORIZONTAL (rot 90) so every logic band is only
    # ~18 mm tall; DIP-16/14 stay vertical. Resistor banks pack as vertical
    # resistors down the left field; the header banks run along the bottom edge.

    # -- power entry (top-left); keep cols 3-5 / rows 6-8 clear for J3's label --
    put("J3", 0.6, 7, 270)          # USB-C, mouth out the left edge
    put("J1", 5, 3, 90)             # 5 V screw terminal
    put("F1", 8, 3); put("D1", 8, 6, 90); put("C50", 8, 9)
    put("R6", 2, 11, 90); put("R30", 4, 11, 90); put("R31", 6, 11, 90)

    # -- CPU band: Z80 + ROM (horizontal) --
    row([("U1", 90), ("U2", 90)], 10, 5)

    # -- decode band: РТ4 / РЕ3 PROMs, 74HC04 (vertical), decode GAL (horizontal) --
    row([("U3", 0), ("U4", 0), ("U6", 0), ("U5", 90)], 10, 12)
    put("J94", 28, 12, 90)          # decode mode jumper

    # -- refresh/timing band: address muxes + counters (vertical), seq GAL (horiz) --
    row([("U20", 0), ("U21", 0), ("U22", 0), ("U23", 0), ("U24", 90)], 10, 19)

    # -- DRAM bank: eight 4164 (vertical) --
    row([(f"U1{i}", 0) for i in range(8)], 8, 26)

    # -- keyboard / parallel interface: 8255 (horizontal), 74148, keyboard header --
    row([("U30", 90), ("U31", 0), ("J30", 90)], 10, 33)

    # -- clock + reset (top-right) --
    put("U50", 35, 4); put("U51", 37, 8); put("J96", 35, 11, 90)
    put("R4", 33, 8, 90); put("R5", 35, 8, 90)

    # -- VGA out (far-right column; caps to the left, off the DRAM bank edge) --
    put("U40", 37, 15); put("U41", 37, 20); put("J40", 37, 25)

    # -- left resistor field: keyboard pull-ups/series, decode pull-ups and the
    #    VGA series resistors, packed as one grid of vertical resistors (cols
    #    2/4/6, clear of every band box, whose left edges start at col 8) --
    left_resistors = (
        [f"R{i}" for i in range(7, 15)] + [f"R{i}" for i in range(16, 24)] + ["R15"]
        + [f"R{i}" for i in range(32, 44)] + ["R44"]
        + ["R1", "R2", "R3"]
    )
    grid(left_resistors, 2, 14, 3, 2, 2, rot=90)

    # -- diagnostic LEDs (far-right strip below VGA) --
    grid([f"D{i}" for i in range(2, 8)], 34, 28, 2, 2, 2, rot=0)
    # -- LED limit resistors in the narrow void between clock and the DRAM bank --
    grid([f"R{i}" for i in range(24, 30)], 31, 15, 2, 1, 2, rot=90)

    # -- debug + observability headers along the bottom edge (horizontal) --
    row([("J95", 90), ("J97", 90), ("J98", 90),
         ("J90", 90), ("J91", 90), ("J92", 90), ("J93", 90)], 2, 37)

    # -- spare decouplers, in the thin gap below CPU/ROM (above the decode caps;
    #    columns chosen to clear the CPU/ROM titles and the decode caps) --
    put("C3", 13, 8); put("C4", 20, 8); put("C19", 27, 8)

    # -- decoupling caps next to each IC (short side; low-freq, so exact side
    #    doesn't matter electrically -- we just keep them off the neighbours) --
    for ic, cap in IC_CAP.items():
        col, r, rot = cell[ic]
        iw, ih = size(ic, rot)
        cw, ch = size(cap, 0)
        d = CAP_DIR.get(ic, "up")
        if d == "right":
            put(cap, col + cells(iw / 2 + cw / 2 + 2.0), r)
        elif d == "left":
            put(cap, col - cells(iw / 2 + cw / 2 + 2.0), r)
        elif d == "down":
            put(cap, col, r + cells(ih / 2 + ch / 2 + 2.0))
        else:
            put(cap, col, r - cells(ih / 2 + ch / 2 + 2.0))

    return {r: g(c, rw, rt) for r, (c, rw, rt) in cell.items()}


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
            ref_y = top - 1.3   # decoupling caps sit above their IC; label upward
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


# On the compact board there is no clear space inside the block frames for a
# title, so each title is printed just ABOVE the frame's top-left corner (in the
# inter-band gap). Titles that would still collide there are dropped.
# VGA_OUT sits in a tight right-edge corner where even an above-frame title
# collides with a neighbour, so its frame is drawn untitled.
SILK_BLOCK_LABEL_DROP = {"VGA_OUT"}


def silk_block_label_anchor(bounds):
    """Lower-left of the title text, printed just above the frame's top edge."""
    left, top, _, _ = bounds
    return (left + SILK_BLOCK_LABEL_PADDING_MM, top - SILK_BLOCK_LABEL_PADDING_MM)


def add_silk_block_label(board, text, bounds, name=None):
    if name in SILK_BLOCK_LABEL_DROP:
        return
    x, y = silk_block_label_anchor(bounds)
    label = pcbnew.PCB_TEXT(board)
    label.SetLayer(pcbnew.F_SilkS)
    label.SetText(text)
    label.SetTextPos(pcbnew.VECTOR2I(mm(x), mm(y)))
    label.SetTextAngleDegrees(0)
    label.SetTextSize(pcbnew.VECTOR2I(mm(2.0), mm(2.0)))
    label.SetTextThickness(mm(0.2))
    label.SetItalic(False)
    label.SetHorizJustify(pcbnew.GR_TEXT_H_ALIGN_LEFT)
    label.SetVertJustify(pcbnew.GR_TEXT_V_ALIGN_BOTTOM)
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

    place_map = build_placement(spec)

    for chip in spec["chips"]:
        ref = chip["ref"]
        typ = chip["type"]
        if typ not in FP_BY_TYPE:
            raise RuntimeError(f"no footprint mapping for {typ}")
        fp = load_footprint(typ, ref)
        fp.SetReference(ref)
        fp.SetValue(chip.get("value", typ))
        x, y, rot = place_map.get(ref, (30 + len(placed) % 8 * 28, 30 + len(placed) // 8 * 35, 0))
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
    for x, y in ((8, 8), (192, 8), (8, 192), (192, 192)):
        add_mounting_hole(board, x, y)
    for label, settings in SILK_LABELS.items():
        x, y, angle, layer, *rest = settings
        size = rest[0] if rest else 2.0
        add_silk_label(board, label, x, y, angle, layer, size)
    for label, ref in CHIP_BLOCK_LABELS.items():
        add_chip_block_label(board, label, placed[ref])
    outlines = compute_block_outlines(placed)
    for name, bounds in outlines.items():
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
