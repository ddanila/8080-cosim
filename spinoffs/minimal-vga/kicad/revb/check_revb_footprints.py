#!/usr/bin/env python3
"""Resolve every footprint the rev B mem card needs against the KiCad library (TD.7.1).

Reads the card's board.json component types, maps each to a candidate footprint list,
verifies the .kicad_mod exists under $KICAD_FOOTPRINTS (or the checked-in VJUGA.pretty
library), and writes the chosen names to kicad/revb/footprints.<card>.json. Cards use
right-angle male bus headers; the backplane uses vertical female sockets. This physical
orientation distinction is part of the mating contract, not a cosmetic library choice.
"""
import json, os, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SELF_TEST = "--self-test" in sys.argv
CARD = next((arg for arg in sys.argv[1:] if not arg.startswith("--")), "mem")

FPROOT = os.environ.get("KICAD_FOOTPRINTS", "")
if not FPROOT or not Path(FPROOT).is_dir():
    print(f"  SKIP  footprint probe ({CARD}): KICAD_FOOTPRINTS not set/found")
    sys.exit(0)

# candidate footprints per abstract kind (first existing wins)
CAND = {
    "PIN_1x39_RA": ["Connector_PinHeader_2.54mm:PinHeader_1x39_P2.54mm_Horizontal"],
    "PIN_1x10_RA": ["Connector_PinHeader_2.54mm:PinHeader_1x10_P2.54mm_Horizontal"],
    "SOCKET_1x39_VERT": ["Connector_PinSocket_2.54mm:PinSocket_1x39_P2.54mm_Vertical"],
    "SOCKET_1x10_VERT": ["Connector_PinSocket_2.54mm:PinSocket_1x10_P2.54mm_Vertical"],
    "DIP14": ["Package_DIP:DIP-14_W7.62mm"],
    "DIP16": ["Package_DIP:DIP-16_W7.62mm"],
    "DIP20": ["Package_DIP:DIP-20_W7.62mm"],
    "DIP24": ["Package_DIP:DIP-24_W7.62mm", "Package_DIP:DIP-24_W15.24mm"],
    "DIP28": ["Package_DIP:DIP-28_W15.24mm", "Package_DIP:DIP-28_W7.62mm"],
    "DIP32": ["Package_DIP:DIP-32_W15.24mm", "Package_DIP:DIP-32_W7.62mm"],
    "DIP40": ["Package_DIP:DIP-40_W15.24mm", "Package_DIP:DIP-40_W7.62mm"],
    "OSC14": ["Oscillator:Oscillator_DIP-14", "Package_DIP:DIP-14_W7.62mm"],
    "OSC8": ["Oscillator:Oscillator_DIP-8"],
    "C_DISC": (["Capacitor_THT:C_Disc_D3.0mm_W2.0mm_P2.50mm",
                "Capacitor_THT:C_Disc_D5.0mm_W2.5mm_P5.00mm"] if CARD == "video" else
               ["Capacitor_THT:C_Disc_D5.0mm_W2.5mm_P5.00mm",
                "Capacitor_THT:C_Disc_D5.0mm_W2.5mm_P2.50mm"]),
    # backplane support parts (TF.2)
    "R_AXIAL": ["Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P7.62mm_Horizontal"],
    "R_VERT": ["Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P2.54mm_Vertical"],
    "D_DO35_VERT": ["Diode_THT:D_DO-35_SOD27_P2.54mm_Vertical_AnodeUp"],
    "LED5": ["LED_THT:LED_D5.0mm"],
    "SW_PUSH6": ["Button_Switch_THT:SW_PUSH_1P1T_6x3.5mm_H4.3_APEM_MJTP1243"],
    "TO92": ["Package_TO_SOT_THT:TO-92_Inline"],
    # USB4085 is a FULLY through-hole USB-C receptacle (USB4125 was SMD — wrong for a
    # hand-soldered THT board).
    "USB_C_THT": ["Connector_USB:USB_C_Receptacle_GCT_USB4085"],
    "PIN_2x2": ["Connector_PinHeader_2.54mm:PinHeader_2x02_P2.54mm_Vertical"],
    "CP_RADIAL": ["Capacitor_THT:CP_Radial_D6.3mm_P2.50mm"],
    "PTC_RADIAL": ["VJUGA:Fuse_Bourns_MF-R110"],
    "PTC_RADIAL_2A5": ["VJUGA:Fuse_Bourns_MF-R250"],
    "BARREL_WUERTH_5A": ["Connector_BarrelJack:BarrelJack_Wuerth_6941xx301002"],
    "D_DO201_VERT": ["Diode_THT:D_DO-201AD_P5.08mm_Vertical_AnodeUp"],
    "WIRE_LINK_22AWG": ["VJUGA:WireLink_22AWG_P5.08mm"],
    "DSUB15HD_NORCOMP": ["VJUGA:NorComp_200-015-213L537"],
}
# board.json component type -> list of footprint kinds it needs
TYPE_KINDS = {
    "REVB_BUS_39_10": (["SOCKET_1x39_VERT", "SOCKET_1x10_VERT"] if CARD == "backplane"
                        else ["PIN_1x39_RA", "PIN_1x10_RA"]),
    "Z80_DIP40": ["DIP40"],
    "EPROM_27C256": ["DIP28"], "SRAM_AS6C1008": ["DIP32"], "GAL22V10": ["DIP24"],
    "USART_8251": ["DIP28"], "GAL16V8_IOSEL": ["DIP20"], "OSC_BAUD": ["OSC8"],
    "TTL_393_BAUD": ["DIP14"], "HCT125_CONSOLE": ["DIP14"],
    "OSC_CPU": ["OSC14"], "PPI_8255": ["DIP40"], "ENC_74148": ["DIP16"],
    "PIC_8259": ["DIP28"],
    "C_100N": ["C_DISC"],
    # backplane support parts (TF.2); all fixed resistors share one axial footprint
    "USB_C_PWR": ["USB_C_THT"], "R_5K1": ["R_AXIAL"], "R_10K": ["R_AXIAL"],
    "R_4K7": ["R_AXIAL"], "R_2K2": ["R_AXIAL"], "SUPERVISOR_3": ["TO92"],
    "R_1K_VERT": ["R_VERT"], "R_1K8_VERT": ["R_VERT"],
    "R_10K_VERT": ["R_VERT"], "D_1N4148_VERT": ["D_DO35_VERT"],
    "SW_PUSH": ["SW_PUSH6"], "LED": ["LED5"], "JMP_2x2": ["PIN_2x2"],
    "C_ELEC_47U": ["CP_RADIAL"], "PTC_1A": ["PTC_RADIAL"],
    "PTC_2A5": ["PTC_RADIAL_2A5"], "BARREL_5A": ["BARREL_WUERTH_5A"],
    "SCHOTTKY_3A": ["D_DO201_VERT"], "SCHOTTKY_5A": ["D_DO201_VERT"],
    "WIRE_LINK_22AWG": ["WIRE_LINK_22AWG"],
    # Video card (R5.V4): every physical package is explicit, including the exact
    # NorComp connector whose two-row solder-tail fanout is not represented by either
    # generic KiCad high-density D-sub footprint.
    "GAL22V10_HDEC": ["DIP24"], "GAL22V10_VDEC": ["DIP24"],
    "GAL22V10_CTRL": ["DIP24"], "SRAM_FB": ["DIP32"],
    "OSC_25M175": ["OSC14"], "ST_HC393": ["DIP14"],
    "ACT_157": ["DIP16"], "ACT_161": ["DIP16"], "TTL_283": ["DIP16"],
    "ACT_273": ["DIP20"], "ALS_166": ["DIP16"], "HCT_245": ["DIP20"],
    "HCT_08": ["DIP14"], "ACT_08": ["DIP14"],
    "DSUB15HD": ["DSUB15HD_NORCOMP"], "R_470": ["R_AXIAL"],
    "R_33": ["R_AXIAL"],
}
# Datasheet DIP row spacing per chip type — the resolved footprint name MUST contain
# this width token. This is the guard that catches "DRC-green board, chip doesn't fit":
# the 27C256/8251/8259 are 0.6-inch DIP-28s and once silently resolved to the skinny
# W7.62 variant because both widths exist in the KiCad library.
PKG_WIDTH = {
    "Z80_DIP40": "W15.24mm",       # Zilog Z0840004 DIP-40, 600 mil
    "EPROM_27C256": "W15.24mm",    # 27C256 DIP-28, 600 mil
    "SRAM_AS6C1008": "W15.24mm",   # AS6C1008 DIP-32, 600 mil
    "GAL22V10": "W7.62mm",         # GAL22V10/ATF22V10 DIP-24, 300 mil skinny
    "USART_8251": "W15.24mm",      # 8251A/82C51 DIP-28, 600 mil
    "GAL16V8_IOSEL": "W7.62mm",    # GAL16V8/ATF16V8 DIP-20, 300 mil
    "PPI_8255": "W15.24mm",        # 8255A/82C55 DIP-40, 600 mil
    "ENC_74148": "W7.62mm",        # 74HC148 DIP-16, 300 mil
    "PIC_8259": "W15.24mm",        # 8259A/82C59 DIP-28, 600 mil
    "TTL_393_BAUD": "W7.62mm",     # SN74HC393N PDIP-14, 300 mil
    "HCT125_CONSOLE": "W7.62mm",   # SN74HCT125N PDIP-14, 300 mil
    "GAL22V10_HDEC": "W7.62mm", "GAL22V10_VDEC": "W7.62mm",
    "GAL22V10_CTRL": "W7.62mm", "SRAM_FB": "W15.24mm",
    "ST_HC393": "W7.62mm", "ACT_157": "W7.62mm", "ACT_161": "W7.62mm",
    "TTL_283": "W7.62mm", "ACT_273": "W7.62mm", "ALS_166": "W7.62mm",
    "HCT_245": "W7.62mm", "HCT_08": "W7.62mm", "ACT_08": "W7.62mm",
}


# Physical contract for the non-DIP parts (TH.2 / D1.36): the resolved footprint must
# match the real part's geometry. Each entry (datasheet-sourced) is checked against the
# .kicad_mod: min_tht = minimum through-hole pads (catches an SMD footprint standing in
# for a THT part — the USB-C bug that started this), drill = smallest THT hole must be
# >= the part's lead, pitch = a pad spacing that must appear. Negative-tested.
PKG_PHYS = {
    # type:            (min_tht, min_drill_mm, pitch_mm-or-None, datasheet)
    "USB_C_PWR":  (16, 0.40, 0.85, "GCT USB4085 THT USB-C, 16 signal @0.85mm; VBUS=A4/A9/"
                                   "B4/B9 GND=A1/A12/B1/B12 CC1=A5 CC2=B5 (GCT_usb4085.pdf)"),
    "SUPERVISOR_3": (3, 0.70, 1.27, "DS1813-5 TO-92: pin1=/RST pin2=VCC pin3=GND (ds1813.pdf)"),
    "SW_PUSH":    (2,  1.20, 6.50, "APEM MJTP1243 6mm tactile, 6.5mm terminal span"),
    "LED":        (2,  0.80, 2.54, "5mm THT LED, 2.54mm lead pitch"),
    "JMP_2x2":    (4,  0.90, 2.54, "2x2 0.1in header"),
    "R_5K1":      (2,  0.70, 7.62, "DIN0207 axial, 7.62mm pitch"),
    "R_4K7":      (2,  0.70, 7.62, "DIN0207 axial, 7.62mm pitch"),
    "R_2K2":      (2,  0.70, 7.62, "DIN0207 axial, 7.62mm pitch"),
    "R_10K":      (2,  0.70, 7.62, "DIN0207 axial, 7.62mm pitch"),
    "C_100N":     ((2, 0.70, 2.50, "Video 3mm disc ceramic, 2.5mm pitch")
                    if CARD == "video" else
                    (2, 0.70, 5.00, "5mm disc ceramic, 5.08mm pitch")),
    "C_ELEC_47U": (2,  0.60, 2.50, "6.3mm radial electrolytic, 2.5mm pitch"),
    "PTC_1A":     (2,  0.70, 5.10, "Bourns MF-R110: 5.1mm lead pitch, 0.51mm leads (mf_r.pdf)"),
    "PTC_2A5":    (2,  1.00, 5.10, "Bourns MF-R250: 5.1mm pitch, 0.81mm leads (mf-r.pdf)"),
    "BARREL_5A":  (3,  0.80, 4.80, "Wurth 694106301002: three blade terminals; "
                                            "4.8mm switched-contact X offset"),
    "SCHOTTKY_3A": (2, 1.32, 5.08, "Vishay 1N5822 DO-201AD, 1.32mm maximum lead; vertical"),
    "SCHOTTKY_5A": (2, 1.32, 5.08, "Vishay SB560 DO-201AD, 1.32mm maximum lead; vertical"),
    "WIRE_LINK_22AWG": (2, 1.00, 5.08, "insulated 22-AWG tinned-copper assembly link"),
    "OSC_BAUD":   (4,  0.80, 7.62, "ECS-2200B-049 half-size DIP-8: pins 1/4/5/8 on 7.62mm grid"),
    "R_1K_VERT":  (2,  0.70, 2.54, "DIN0207 vertical, 2.54mm pad pitch"),
    "R_1K8_VERT": (2,  0.70, 2.54, "DIN0207 vertical, 2.54mm pad pitch"),
    "R_10K_VERT": (2,  0.70, 2.54, "DIN0207 vertical, 2.54mm pad pitch"),
    "D_1N4148_VERT": (2, 0.70, 2.54, "1N4148 DO-35 vertical, 2.54mm pad pitch"),
    "OSC_25M175": (4, 0.80, 15.24, "ECS-100A-251.7 full DIP-14 can: pins 1/7/8/14; "
                                           "7.62mm row spacing checked by R5.V4 gate"),
    "DSUB15HD": (15, 0.70, 0.762, "NorComp 200-015-213L537: 15 x 0.70mm signal PTH, "
                                      "2 x 2.10mm NPTH board locks, 0.762mm stagger"),
    "R_470": (2, 0.70, 7.62, "DIN0207 axial, 7.62mm pitch"),
    "R_33": (2, 0.70, 7.62, "DIN0207 axial 33-ohm source terminator, 7.62mm pitch"),
}


def footprint_path(fpname):
    """Resolve standard libraries plus the repo-owned VJUGA.pretty library."""
    lib, name = fpname.split(":")
    root = HERE if lib == "VJUGA" else Path(FPROOT)
    return root / f"{lib}.pretty" / f"{name}.kicad_mod"


def parse_pads(fpname):
    """Return (unique pad numbers, thru-hole pad count, min drill, sorted x-pitches).
    Drill is parsed from the (drill ...) sub-expression that follows (size ...) inside
    each pad block (it is not adjacent to (at ...))."""
    import re
    txt = footprint_path(fpname).read_text()
    nums, tht, drills, xs = set(), 0, [], []
    for m in re.finditer(
            r'\(pad\s+"([^"]*)"\s+(\S+)\s+\S+\s+\(at\s+([-\d.]+)\s+([-\d.]+)', txt):
        num, typ, x = m.group(1), m.group(2), float(m.group(3))
        nums.add(num); xs.append(x)
        if typ == "thru_hole":
            tht += 1
            seg = txt[m.end():m.end() + 240]        # rest of this pad block
            dm = re.search(r'\(drill\s+(?:oval\s+)?([-\d.]+)', seg)
            if dm:
                drills.append(float(dm.group(1)))
    xs = sorted(set(round(x, 2) for x in xs))
    pitches = sorted({round(b - a, 2) for a, b in zip(xs, xs[1:])})
    return nums, tht, (min(drills) if drills else 0.0), pitches


def phys_ok(typ, fpname):
    """Check a resolved footprint against PKG_PHYS. Returns a list of failure strings."""
    if typ not in PKG_PHYS:
        return []
    min_tht, min_drill, pitch, note = PKG_PHYS[typ]
    _, tht, drill, pitches = parse_pads(fpname)
    fails = []
    if tht < min_tht:
        fails.append(f"{typ}: {tht} through-hole pads < {min_tht} required ({note})")
    if drill + 1e-6 < min_drill:
        fails.append(f"{typ}: min drill {drill:.2f} < {min_drill:.2f} mm ({note})")
    if pitch is not None and not any(abs(p - pitch) < 0.06 for p in pitches):
        fails.append(f"{typ}: no {pitch:.2f} mm pad pitch found in {pitches} ({note})")
    return fails


def width_ok(typ, fpname):
    """Return whether a DIP footprint has the datasheet-required row spacing."""
    return typ not in PKG_WIDTH or PKG_WIDTH[typ] in fpname


def exists(fp):
    return footprint_path(fp).is_file()


def resolve_kind(kind):
    for fp in CAND[kind]:
        if exists(fp):
            return fp
    return None


def main():
    board = json.loads((HERE / f"{CARD}.board.json").read_text())
    chosen, missing = {}, []
    for comp in board["chips"]:
        t = comp["type"]
        if t in TYPE_KINDS:
            fps = [resolve_kind(k) for k in TYPE_KINDS[t]]
            if None in fps:
                missing.append((t, TYPE_KINDS[t]))
            elif not width_ok(t, fps[0]):
                missing.append((f"{t} [datasheet width {PKG_WIDTH[t]}]", fps))
            else:
                for f in phys_ok(t, fps[0]):
                    missing.append((f, [fps[0]]))
            chosen[t] = fps if len(fps) > 1 else fps[0]
        elif t == "HDR_1xN" or t.startswith("HDR_1x"):
            n = len(comp["pins"])
            fp = f"Connector_PinHeader_2.54mm:PinHeader_1x{n:02d}_P2.54mm_Vertical"
            if not exists(fp):
                missing.append((f"{t}({n})", [fp]))
            chosen[f"HDR_1x{n}"] = fp
        else:
            # Do not silently omit a newly introduced physical class. That failure
            # once let the R5.V6 power parts disappear when this probe rewrote the
            # generated footprint map.
            missing.append((f"{t} [no resolver contract]", []))
    if missing:
        print(f"footprint probe ({CARD}) FAILED -- unresolved:")
        for t, c in missing:
            print(f"- {t}: none of {c}")
        return 1
    out = HERE / f"footprints.{CARD}.json"
    out.write_text(json.dumps(chosen, indent=2) + "\n")
    print(f"footprint probe ({CARD}) OK: {len(chosen)} types resolved -> {out.name}")
    return 0


def self_test():
    """Prove the two high-consequence guards reject known-wrong library parts."""
    wrong_dip = "Package_DIP:DIP-28_W7.62mm"
    wrong_usb = "Connector_USB:USB_C_Receptacle_GCT_USB4125-xx-x_6P_TopMnt_Horizontal"
    wrong_dsub = ("Connector_Dsub:DSUB-15-HD_Socket_Horizontal_P2.29x1.90mm_"
                   "EdgePinOffset3.03mm_Housed_MountingHolesOffset4.94mm")
    failures = []
    if width_ok("EPROM_27C256", wrong_dip):
        failures.append("DIP width guard accepted a 300 mil footprint for a 600 mil DIP-28")
    if not exists(wrong_usb):
        failures.append(f"negative-test fixture missing: {wrong_usb}")
    elif not phys_ok("USB_C_PWR", wrong_usb):
        failures.append("physical guard accepted the known-wrong SMD USB-C footprint")
    if not exists(wrong_dsub):
        failures.append(f"negative-test fixture missing: {wrong_dsub}")
    elif not phys_ok("DSUB15HD", wrong_dsub):
        failures.append("physical guard accepted the wrong 1.90mm-row generic HD15 footprint")
    if failures:
        print("footprint guard negative self-test FAILED:")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print("footprint guard negative self-test PASS: wrong DIP width, SMD USB-C and generic HD15 rejected")
    return 0


if __name__ == "__main__":
    result = main()
    if result == 0 and SELF_TEST:
        result = self_test()
    sys.exit(result)
