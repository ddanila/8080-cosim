#!/usr/bin/env python3
# LVS connectivity check: does the KiCad schematic describe the SAME circuit as
# the structural Verilog? Compares NET MEMBERSHIP, not names -- two netlists are
# equivalent iff they partition the (instance, pin) endpoints into nets the same
# way. Net names are irrelevant; only the grouping matters.
#
# A mapping file (JSON) supplies:
#   instances : { kicad_refdes : hdl_instance }              (which chip is which)
#   pinmaps.kicad : { type : { pin_number : LOGICAL_PIN } }  (KiCad pin# -> name)
#   (HDL logical pins are derived automatically: A[0]->A0, ior_n->IOR_N, ...)
#
# Only instances present in `instances` are compared (lets us check a subset).
#
# Usage: lvs.py --hdl <yosys.json> --kicad <net.xml> --map <map.json>
# Exit 0 = in sync, 1 = mismatch.
import sys, json, argparse
import netlist_from_yosys, netlist_from_kicad, netlist_from_board

def canon_hdl_pin(p):                 # ior_n->IOR_N ; portc_lo->PORTC_LO
    return p.replace("[", "").replace("]", "").upper()

def hdl_pin(inst, t, p, i, w):        # bus bit -> name+index (A,i=3 -> A3); scalar -> name
    base = canon_hdl_pin(p)
    return base + (str(i) if w > 1 else "")

def nets_of(side_insts, inst_map, pin_of):
    """Return {frozenset(endpoints)} -- one frozenset per net, restricted to
    mapped instances, keeping only nets with >=2 endpoints (real connections).
    A bus pin (width>1, e.g. CPU 'A' -> 16 nets) expands to per-bit endpoints."""
    net2eps = {}
    for inst, info in side_insts.items():
        canon_inst = inst_map.get(inst)
        if canon_inst is None:        # instance not in scope of this check
            continue
        for pin, nets in info["pins"].items():
            w = len(nets)
            for i, n in enumerate(nets):
                if n.startswith("const:"):
                    continue
                lp = pin_of(inst, info["type"], pin, i, w)
                if lp is None:
                    continue
                net2eps.setdefault(n, set()).add(f"{canon_inst}.{lp}")
    return {frozenset(eps) for eps in net2eps.values() if len(eps) >= 2}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--hdl", required=True)
    ap.add_argument("--kicad", help="KiCad XML netlist (kicad-cli output)")
    ap.add_argument("--board", help="board spec JSON (KiCad-free; same connectivity)")
    ap.add_argument("--map", required=True)
    a = ap.parse_args()
    if not (a.kicad or a.board):
        ap.error("need --kicad or --board")
    mp = json.load(open(a.map))

    _, hdl = netlist_from_yosys.load(a.hdl)
    kic = netlist_from_kicad.load(a.kicad) if a.kicad else netlist_from_board.load(a.board)

    # HDL: instance name maps to itself (canonical); pins auto-canonicalized.
    hdl_imap = {i: i for i in hdl if i in set(mp["instances"].values())}
    hdl_nets = nets_of(hdl, hdl_imap, hdl_pin)

    # KiCad: refdes -> hdl instance; pin number -> logical name via pinmap.
    # Per-instance overrides (pinmaps.kicad_instance[refdes]) win over type-level
    # (pinmaps.kicad[type]) -- needed where chips of one type wire pins differently
    # for PCB routing (e.g. the two 8286 address buffers).
    kpm = mp["pinmaps"]["kicad"]
    kinst = mp["pinmaps"].get("kicad_instance", {})
    kic_nets = nets_of(kic, mp["instances"],
                       lambda inst, t, p, i, w: kinst.get(inst, {}).get(p) or kpm.get(t, {}).get(p))

    matched   = hdl_nets & kic_nets
    only_hdl  = hdl_nets - kic_nets
    only_kic  = kic_nets - hdl_nets

    print(f"LVS connectivity check ({len(mp['instances'])} mapped instances)")
    print(f"  matched nets    : {len(matched)}")
    print(f"  only in HDL     : {len(only_hdl)}")
    print(f"  only in KiCad   : {len(only_kic)}")
    for label, s in (("HDL-only", only_hdl), ("KiCad-only", only_kic)):
        for net in sorted(s, key=lambda x: sorted(x)):
            print(f"    [{label}] {{{', '.join(sorted(net))}}}")
    ok = not only_hdl and not only_kic
    print("\n==> IN SYNC" if ok else "\n==> MISMATCH")
    return 0 if ok else 1

if __name__ == "__main__":
    sys.exit(main())
