#!/usr/bin/env python3
# LVS — board-spec side (KiCad-free). Read the board spec JSON directly into the
# same normalized shape as netlist_from_kicad / netlist_from_yosys. The board spec
# is exactly what gen_kicad_sch.py lays out into a schematic, so this yields the
# identical connectivity the kicad-cli netlist would -- but with no KiCad install
# (used in CI, where the KiCad version may not match our schematic format).
#
# Usage: netlist_from_board.py <board.json>
import sys, json

def load(path):
    b = json.load(open(path))
    insts = {c["ref"]: {"type": c["type"], "pins": {}} for c in b["chips"]}
    for name, entry in b["nets"].items():
        nodes = entry["nodes"] if isinstance(entry, dict) else entry
        for ref, pin in nodes:
            insts.setdefault(ref, {"type": "?", "pins": {}})
            insts[ref]["pins"].setdefault(str(pin), []).append(name)
    return insts

if __name__ == "__main__":
    insts = load(sys.argv[1])
    print(f"# {len(insts)} components (from board spec)")
    for ref in sorted(insts):
        print(f"{ref}  ({insts[ref]['type']})")
        for pin, nets in sorted(insts[ref]["pins"].items()):
            print(f"    pin {pin:>3} -> {', '.join(nets)}")
