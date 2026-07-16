#!/usr/bin/env python3
# Generate a KiCad schematic (.kicad_sch) from a board spec JSON.
# Connectivity only -- no nice layout: each chip's pins sit on a horizontal row,
# each connected pin gets a stub wire + a net label; same label name => same net.
# This is a starting point you can re-arrange in the KiCad GUI; it exports the
# same netlist either way.
#
# Board spec JSON:
#   { "chips": [ {"ref":"U1","type":"CPU8080","pins":{"1":"A0", ...}}, ... ],
#     "nets":  { "A0": [["U1","1"],["U2","1"]], ... } }
#
# Usage: gen_kicad_sch.py [--include-power] <board.json> <out.kicad_sch>
import argparse
import json
import sys

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

def instance(ref, typ, px, py, n, pcb_dnp=False, assembly_dnp=False):
    on_board = "no" if pcb_dnp else "yes"
    dnp = "yes" if pcb_dnp or assembly_dnp else "no"
    return (f'\t(symbol (lib_id "juku:{typ}") (at {px} {py} 0) (unit 1)\n'
            f'\t\t(exclude_from_sim no) (in_bom yes) (on_board {on_board}) (dnp {dnp}) (uuid "{uid(n)}")\n'
            f'\t\t(property "Reference" "{ref}" (at {px} {py-7} 0) (effects (font (size 1.27 1.27))))\n'
            f'\t\t(property "Value" "{typ}" (at {px} {py+7} 0) (effects (font (size 1.27 1.27))))\n'
            f'\t\t(instances (project "juku" (path "/" (reference "{ref}") (unit 1)))))')

def wire(x1, y1, x2, y2, n):
    return (f'\t(wire (pts (xy {x1} {y1}) (xy {x2} {y2})) '
            f'(stroke (width 0) (type default)) (uuid "{uid(n)}"))')

def label(t, x, y):
    return f'\t(label "{t}" (at {x} {y} 0) (effects (font (size 1.27 1.27)) (justify left bottom)))'

def no_connect(x, y, n):
    return f'\t(no_connect (at {x} {y}) (uuid "{uid(n)}"))'

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--include-power",
        action="store_true",
        help="emit board-spec nets tagged as power instead of skipping them for LVS",
    )
    parser.add_argument("board_json")
    parser.add_argument("out_sch")
    args = parser.parse_args()

    spec = json.load(open(args.board_json))
    chips = spec["chips"]

    # pin order per type (sorted by numeric pin number) + index lookup. The symbol takes the
    # UNION of pins across all chips of the type -- instances of one type may wire different
    # sections (e.g. D37 vs D7, both LA3_GATE: D37 also uses the 1/2->3 LATCH section).
    type_union = {}
    for c in chips:
        type_union.setdefault(c["type"], {}).update(c["pins"])
    type_pins, pin_index = {}, {}
    for t, pins in type_union.items():
        # sort numeric pins by value; alphanumeric pins (e.g. connector edge-codes "104C")
        # sort after, lexically -- keeps a stable order without requiring integer pin names.
        order = sorted(pins.items(),
                       key=lambda kv: (0, int(kv[0]), "") if kv[0].isdigit() else (1, 0, kv[0]))
        type_pins[t] = order
        pin_index[t] = {num: k for k, (num, _) in enumerate(order)}

    # place chips at (50, 40 + i*40); pins extend right from px
    pos = {c["ref"]: (50, 40 + i * 40) for i, c in enumerate(chips)}
    ctype = {c["ref"]: c["type"] for c in chips}

    # Keep the generated schematic on the KiCad 9 stable file format. Newer KiCad can
    # load older schematics, while KiCad 9 rejects KiCad 10/nightly version tags.
    out = ['(kicad_sch',
           '\t(version 20250114)',
           '\t(generator "eeschema")',
           '\t(generator_version "9.0")',
           f'\t(uuid "{uid(1)}") (paper "A3")', '\t(lib_symbols']
    out += [lib_symbol(t, type_pins[t]) for t in type_pins]
    out += ['\t)']

    n = 100
    for c in chips:
        px, py = pos[c["ref"]]
        out.append(instance(
            c["ref"], c["type"], px, py, n,
            bool(c.get("pcb_dnp")), bool(c.get("assembly_dnp")),
        )); n += 1

    for net, entry in spec["nets"].items():
        if isinstance(entry, dict) and entry.get("power") and not args.include_power:
            continue          # power nets are PCB-only (no power pins in the HDL/LVS compare)
        nodes = entry["nodes"] if isinstance(entry, dict) else entry  # tagged or bare
        for ref, pin in nodes:
            t = ctype[ref]
            if pin not in pin_index[t]:
                continue
            px, py = pos[ref]
            x = px + pin_index[t][pin] * GRID
            out.append(wire(x, py, x, py - STUB, n)); n += 1
            out.append(label(net, x, py - STUB))
    for ref, pin in spec.get("no_connects", []):
        t = ctype[ref]
        if pin not in pin_index[t]:
            continue
        px, py = pos[ref]
        x = px + pin_index[t][pin] * GRID
        out.append(no_connect(x, py, n)); n += 1
    out.append(')')
    open(args.out_sch, "w").write("\n".join(out) + "\n")
    print(f"wrote {args.out_sch}: {len(chips)} chips, {len(spec['nets'])} nets")

if __name__ == "__main__":
    main()
