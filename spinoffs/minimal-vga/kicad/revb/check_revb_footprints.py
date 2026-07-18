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
    "DIP28": ["Package_DIP:DIP-28_W7.62mm", "Package_DIP:DIP-28_W15.24mm"],
    "DIP32": ["Package_DIP:DIP-32_W15.24mm", "Package_DIP:DIP-32_W7.62mm"],
    "DIP40": ["Package_DIP:DIP-40_W15.24mm", "Package_DIP:DIP-40_W7.62mm"],
    "OSC14": ["Oscillator:Oscillator_DIP-14", "Package_DIP:DIP-14_W7.62mm"],
    "C_DISC": ["Capacitor_THT:C_Disc_D5.0mm_W2.5mm_P5.00mm",
               "Capacitor_THT:C_Disc_D5.0mm_W2.5mm_P2.50mm"],
}
# board.json component type -> list of footprint kinds it needs
TYPE_KINDS = {
    "REVB_BUS_39_10": ["PIN_1x39", "PIN_1x10"],
    "EPROM_27C256": ["DIP28"], "SRAM_AS6C1008": ["DIP32"], "GAL22V10": ["DIP24"],
    "USART_8251": ["DIP28"], "GAL16V8_IOSEL": ["DIP20"], "OSC_BAUD": ["OSC14"],
    "OSC_CPU": ["OSC14"], "PPI_8255": ["DIP40"], "ENC_74148": ["DIP16"],
    "PIC_8259": ["DIP28"],
    "C_100N": ["C_DISC"],
}


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
            chosen[t] = fps if len(fps) > 1 else fps[0]
        elif t == "HDR_1xN":
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
