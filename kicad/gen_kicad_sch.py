#!/usr/bin/env python3
# Generate a KiCad 10 schematic (.kicad_sch) from a board spec JSON.
# Connectivity only -- no nice layout: each chip's pins sit on a horizontal row,
# each connected pin gets a stub wire + a net label; same label name => same net.
# This is a starting point you can re-arrange in the KiCad GUI; it exports the
# same netlist either way.
#
# Board spec JSON:
#   { "chips": [ {"ref":"U1","type":"CPU8080","pins":{"1":"A0", ...}}, ... ],
#     "nets":  { "A0": [["U1","1"],["U2","1"]], ... } }
#
# Usage: gen_kicad_sch.py <board.json> <out.kicad_sch>
import sys, json

GRID, STUB = 2.54, 2.54

def uid(n): return f"00000000-0000-0000-0000-{n:012d}"

def lib_symbol(typ, pin_order):
    L = [f'\t\t(symbol "juku:{typ}"',
         '\t\t\t(pin_names (offset 0.254)) (exclude_from_sim no) (in_bom yes) (on_board yes)',
         f'\t\t\t(property "Reference" "U" (at 0 5 0) (effects (font (size 1.27 1.27))))',
         f'\t\t\t(property "Value" "{typ}" (at 0 -5 0) (effects (font (size 1.27 1.27))))',
         f'\t\t\t(symbol "{typ}_1_1"']
    for k, (num, name) in enumerate(pin_order):
        L.append(f'\t\t\t\t(pin bidirectional line (at {k*GRID} 0 0) (length {STUB})'
                 f' (name "{name}" (effects (font (size 1.27 1.27))))'
                 f' (number "{num}" (effects (font (size 1.27 1.27)))))')
    L += ['\t\t\t)', '\t\t)']
    return "\n".join(L)

def instance(ref, typ, px, py, n):
    return (f'\t(symbol (lib_id "juku:{typ}") (at {px} {py} 0) (unit 1)\n'
            f'\t\t(exclude_from_sim no) (in_bom yes) (on_board yes) (dnp no) (uuid "{uid(n)}")\n'
            f'\t\t(property "Reference" "{ref}" (at {px} {py-7} 0) (effects (font (size 1.27 1.27))))\n'
            f'\t\t(property "Value" "{typ}" (at {px} {py+7} 0) (effects (font (size 1.27 1.27))))\n'
            f'\t\t(instances (project "juku" (path "/" (reference "{ref}") (unit 1)))))')

def wire(x1, y1, x2, y2, n):
    return (f'\t(wire (pts (xy {x1} {y1}) (xy {x2} {y2})) '
            f'(stroke (width 0) (type default)) (uuid "{uid(n)}"))')

def label(t, x, y):
    return f'\t(label "{t}" (at {x} {y} 0) (effects (font (size 1.27 1.27)) (justify left bottom)))'

def main():
    spec = json.load(open(sys.argv[1]))
    chips = spec["chips"]

    # pin order per type (sorted by numeric pin number) + index lookup
    type_pins, pin_index = {}, {}
    for c in chips:
        t = c["type"]
        if t not in type_pins:
            order = sorted(c["pins"].items(), key=lambda kv: int(kv[0]))
            type_pins[t] = order
            pin_index[t] = {num: k for k, (num, _) in enumerate(order)}

    # place chips at (50, 40 + i*40); pins extend right from px
    pos = {c["ref"]: (50, 40 + i * 40) for i, c in enumerate(chips)}
    ctype = {c["ref"]: c["type"] for c in chips}

    out = ['(kicad_sch (version 20250610) (generator "eeschema") (generator_version "9.99")',
           f'\t(uuid "{uid(1)}") (paper "A3")', '\t(lib_symbols']
    out += [lib_symbol(t, type_pins[t]) for t in type_pins]
    out += ['\t)']

    n = 100
    for c in chips:
        px, py = pos[c["ref"]]
        out.append(instance(c["ref"], c["type"], px, py, n)); n += 1

    for net, entry in spec["nets"].items():
        nodes = entry["nodes"] if isinstance(entry, dict) else entry  # tagged or bare
        for ref, pin in nodes:
            t = ctype[ref]
            if pin not in pin_index[t]:
                continue
            px, py = pos[ref]
            x = px + pin_index[t][pin] * GRID
            out.append(wire(x, py, x, py - STUB, n)); n += 1
            out.append(label(net, x, py - STUB))
    out.append(')')
    open(sys.argv[2], "w").write("\n".join(out) + "\n")
    print(f"wrote {sys.argv[2]}: {len(chips)} chips, {len(spec['nets'])} nets")

if __name__ == "__main__":
    main()
