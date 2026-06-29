#!/usr/bin/env python3
# LVS — Verilog side. Turn a Yosys JSON netlist into a normalized connectivity
# table: per top-level instance, each pin -> the board net(s) it connects to.
# This is half of the KiCad<->HDL connectivity checker (see ../docs/architecture.md).
#
# Usage: netlist_from_yosys.py <juku_top.json> [top_module]
import json, sys

def load(path, top=None):
    data = json.load(open(path))
    mods = data["modules"]
    if not top:   # prefer the module Yosys flagged as top (attributes.top == 1)
        top = next((n for n, mm in mods.items()
                    if str(mm.get("attributes", {}).get("top", 0)) in ("1", "00000000000000000000000000000001")), None)
        top = top or next(n for n in mods if not n.startswith("$"))
    m = mods[top]

    # bit-id -> net name (single-bit nets named name[i] for buses)
    bit2net = {}
    for nname, n in m["netnames"].items():
        for i, bit in enumerate(n["bits"]):
            if isinstance(bit, int):
                bit2net[bit] = nname if len(n["bits"]) == 1 else f"{nname}[{i}]"

    def netof(bit):
        if isinstance(bit, str):      # constant "0"/"1"/"x"/"z"
            return f"const:{bit}"
        return bit2net.get(bit, f"net#{bit}")

    insts = {}
    for cname, c in m["cells"].items():
        if c["type"].startswith("$"):     # skip yosys-synthesized glue gates
            continue
        pins = {p: [netof(b) for b in bits] for p, bits in c["connections"].items()}
        insts[cname] = {"type": c["type"], "pins": pins}
    return top, insts

if __name__ == "__main__":
    top, insts = load(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None)
    print(f"# normalized netlist for top '{top}': {len(insts)} instances\n")
    for name in sorted(insts):
        it = insts[name]
        print(f"{name}  ({it['type']})")
        for pin, nets in it["pins"].items():
            print(f"    {pin:10} -> {', '.join(nets)}")
        print()
