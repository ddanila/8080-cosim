#!/usr/bin/env python3
"""Resolve every footprint the rev B mem card needs against the KiCad library (TD.7.1).

Reads the card's board.json component types, maps each to a candidate footprint list,
verifies the .kicad_mod exists under $KICAD_FOOTPRINTS, and writes the chosen names to
kicad/revb/footprints.json (consumed by gen_revb_pcb.py, TD.7.2). Skips (not fails)
when $KICAD_FOOTPRINTS is unset. The THT 1x39 header IS in the library, so the D1.23
programmatic-padrow fallback is not needed.
"""
import json, os, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
CARD = sys.argv[1] if len(sys.argv) > 1 else "mem"

FPROOT = os.environ.get("KICAD_FOOTPRINTS", "")
if not FPROOT or not Path(FPROOT).is_dir():
    print(f"  SKIP  footprint probe ({CARD}): KICAD_FOOTPRINTS not set/found")
    sys.exit(0)

# candidate footprints per abstract kind (first existing wins)
CAND = {
    "PIN_1x39": ["Connector_PinHeader_2.54mm:PinHeader_1x39_P2.54mm_Vertical"],
    "PIN_1x10": ["Connector_PinHeader_2.54mm:PinHeader_1x10_P2.54mm_Vertical"],
    "DIP14": ["Package_DIP:DIP-14_W7.62mm"],
    "DIP16": ["Package_DIP:DIP-16_W7.62mm"],
    "DIP20": ["Package_DIP:DIP-20_W7.62mm"],
    "DIP24": ["Package_DIP:DIP-24_W7.62mm", "Package_DIP:DIP-24_W15.24mm"],
    "DIP28": ["Package_DIP:DIP-28_W15.24mm", "Package_DIP:DIP-28_W7.62mm"],
    "DIP32": ["Package_DIP:DIP-32_W15.24mm", "Package_DIP:DIP-32_W7.62mm"],
    "DIP40": ["Package_DIP:DIP-40_W15.24mm", "Package_DIP:DIP-40_W7.62mm"],
    "OSC14": ["Oscillator:Oscillator_DIP-14", "Package_DIP:DIP-14_W7.62mm"],
    "C_DISC": ["Capacitor_THT:C_Disc_D5.0mm_W2.5mm_P5.00mm",
               "Capacitor_THT:C_Disc_D5.0mm_W2.5mm_P2.50mm"],
    # backplane support parts (TF.2)
    "R_AXIAL": ["Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P7.62mm_Horizontal"],
    "LED5": ["LED_THT:LED_D5.0mm"],
    "SW_PUSH6": ["Button_Switch_THT:SW_PUSH_1P1T_6x3.5mm_H4.3_APEM_MJTP1243"],
    "TO92": ["Package_TO_SOT_THT:TO-92_Inline"],
    # USB4085 is a FULLY through-hole USB-C receptacle (USB4125 was SMD — wrong for a
    # hand-soldered THT board).
    "USB_C_THT": ["Connector_USB:USB_C_Receptacle_GCT_USB4085"],
    "PIN_2x2": ["Connector_PinHeader_2.54mm:PinHeader_2x02_P2.54mm_Vertical"],
    "CP_RADIAL": ["Capacitor_THT:CP_Radial_D6.3mm_P2.50mm"],
    "PTC_RADIAL": ["Fuse:Fuse_Bourns_MF-RG300"],
}
# board.json component type -> list of footprint kinds it needs
TYPE_KINDS = {
    "REVB_BUS_39_10": ["PIN_1x39", "PIN_1x10"],
    "Z80_DIP40": ["DIP40"],
    "EPROM_27C256": ["DIP28"], "SRAM_AS6C1008": ["DIP32"], "GAL22V10": ["DIP24"],
    "USART_8251": ["DIP28"], "GAL16V8_IOSEL": ["DIP20"], "OSC_BAUD": ["OSC14"],
    "OSC_CPU": ["OSC14"], "PPI_8255": ["DIP40"], "ENC_74148": ["DIP16"],
    "PIC_8259": ["DIP28"],
    "C_100N": ["C_DISC"],
    # backplane support parts (TF.2); all fixed resistors share one axial footprint
    "USB_C_PWR": ["USB_C_THT"], "R_5K1": ["R_AXIAL"], "R_10K": ["R_AXIAL"],
    "R_4K7": ["R_AXIAL"], "R_2K2": ["R_AXIAL"], "SUPERVISOR_3": ["TO92"],
    "SW_PUSH": ["SW_PUSH6"], "LED": ["LED5"], "JMP_2x2": ["PIN_2x2"],
    "C_ELEC_47U": ["CP_RADIAL"], "PTC_1A": ["PTC_RADIAL"],
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
}


# Physical contract for the non-DIP parts (TH.2 / D1.36): the resolved footprint must
# match the real part's geometry. Each entry (datasheet-sourced) is checked against the
# .kicad_mod: min_tht = minimum through-hole pads (catches an SMD footprint standing in
# for a THT part — the USB-C bug that started this), drill = smallest THT hole must be
# >= the part's lead, pitch = a pad spacing that must appear. Negative-tested.
PKG_PHYS = {
    # type:            (min_tht, min_drill_mm, pitch_mm-or-None, datasheet)
    "USB_C_PWR":  (16, 0.40, 0.85, "GCT USB4085 (THT USB-C, 16 signal pins @0.85mm)"),
    "SW_PUSH":    (2,  1.20, 6.50, "APEM MJTP1243 6mm tactile, 6.5mm terminal span"),
    "LED":        (2,  0.80, 2.54, "5mm THT LED, 2.54mm lead pitch"),
    "JMP_2x2":    (4,  0.90, 2.54, "2x2 0.1in header"),
    "R_5K1":      (2,  0.70, 7.62, "DIN0207 axial, 7.62mm pitch"),
    "R_4K7":      (2,  0.70, 7.62, "DIN0207 axial, 7.62mm pitch"),
    "R_2K2":      (2,  0.70, 7.62, "DIN0207 axial, 7.62mm pitch"),
    "R_10K":      (2,  0.70, 7.62, "DIN0207 axial, 7.62mm pitch"),
    "C_100N":     (2,  0.70, 5.00, "5mm disc ceramic, 5.08mm pitch"),
    "C_ELEC_47U": (2,  0.60, 2.50, "6.3mm radial electrolytic, 2.5mm pitch"),
    "PTC_1A":     (2,  0.70, None, "Bourns MF-RG radial PTC"),
}


def parse_pads(fpname):
    """Return (unique pad numbers, thru-hole pad count, min drill, sorted x-pitches).
    Drill is parsed from the (drill ...) sub-expression that follows (size ...) inside
    each pad block (it is not adjacent to (at ...))."""
    import re
    lib, name = fpname.split(":")
    txt = (Path(FPROOT) / f"{lib}.pretty" / f"{name}.kicad_mod").read_text()
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


def exists(fp):
    lib, name = fp.split(":")
    return (Path(FPROOT) / f"{lib}.pretty" / f"{name}.kicad_mod").is_file()


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
            elif t in PKG_WIDTH and PKG_WIDTH[t] not in fps[0]:
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
        # passives on other cards (R/LED/USB-C/switch) resolve in their card's probe
    if missing:
        print(f"footprint probe ({CARD}) FAILED -- unresolved:")
        for t, c in missing:
            print(f"- {t}: none of {c}")
        return 1
    out = HERE / f"footprints.{CARD}.json"
    out.write_text(json.dumps(chosen, indent=2) + "\n")
    print(f"footprint probe ({CARD}) OK: {len(chosen)} types resolved -> {out.name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
