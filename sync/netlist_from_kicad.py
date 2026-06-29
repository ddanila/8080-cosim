#!/usr/bin/env python3
# LVS — KiCad side. Parse a KiCad XML netlist (the format produced by
#   `kicad-cli sch export netlist --format kicadxml`) into the SAME normalized
# shape as netlist_from_yosys: { instance: {"type":..., "pins": {pin: [nets]}} }.
#
# Usage: netlist_from_kicad.py <netlist.net.xml>
import sys, xml.etree.ElementTree as ET

def load(path):
    root = ET.parse(path).getroot()
    insts = {}
    # components -> type (prefer libsource part, fall back to value)
    for comp in root.findall("./components/comp"):
        ref = comp.get("ref")
        ls = comp.find("libsource")
        typ = (ls.get("part") if ls is not None else None) or (
            comp.findtext("value") or "?")
        insts[ref] = {"type": typ, "pins": {}}
    # nets -> per-node (ref,pin)
    for net in root.findall("./nets/net"):
        nname = net.get("name") or f"net{net.get('code')}"
        for node in net.findall("node"):
            ref, pin = node.get("ref"), node.get("pin")
            insts.setdefault(ref, {"type": "?", "pins": {}})
            insts[ref]["pins"].setdefault(pin, []).append(nname)
    return insts

if __name__ == "__main__":
    insts = load(sys.argv[1])
    print(f"# {len(insts)} components")
    for ref in sorted(insts):
        it = insts[ref]
        print(f"{ref}  ({it['type']})")
        for pin, nets in sorted(it["pins"].items()):
            print(f"    pin {pin:>3} -> {', '.join(nets)}")
