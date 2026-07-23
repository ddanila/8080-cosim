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
# Board nets marked `"power": true` remain excluded by default for legacy HDL
# models without supply pins. `--include-power` opts a physical-pin model into
# those rails.
# A map may also contain `no_connects: [[ref, pin], ...]`. For board-direct
# physical LVS, those declarations are compared over the pins actually present
# in the map, so intentional NC pads cannot silently become unowned or wired.
# `complete_instances: [ref, ...]` additionally requires every physical pin on
# each named (non-boundary) instance to be mapped and owned by a net or NC.
# `closed_board_nets: [name, ...]` requires every physical endpoint of each
# named board net to be inside the mapped projection.
# `close_nonpower_nets_of_complete_instances: true` also requires that list to
# include every non-power board net touched by a complete instance.
#
# Usage: lvs.py --hdl <yosys.json> --kicad <net.xml> --map <map.json>
# Exit 0 = in sync, 1 = mismatch.
import sys, json, argparse
import netlist_from_yosys, netlist_from_kicad, netlist_from_board

# Sim-only stimulus pins: artifacts of the runnable model (the die-replica's sampling
# clock, the keyboard/interrupt stimulus) that have NO counterpart on the real chips, so
# they are never in the board netlist. Dropped from the comparison BY NAME -- an explicit,
# documented contract. NOTE: this exempts only these named pins; any *other* pin absent
# from the pinmap is still compared (and thus still flags an incomplete pinmap) -- so the
# check is not weakened, only made honest about the sim scaffolding.
SIM_ONLY = {"SCLK", "KBD_EN", "KBD_PRESSED", "KBD_SHIFT", "KCOL", "KBIT", "FRAME_TICK",
            "VA", "VQ",   # VA/VQ = the sim-only 2nd (video) read port on the РУ5 (physical arbitration open)
            "PHSEL",      # PHSEL = sim-only divider phase bit into D35 (self-clocking waveform lock)
            "SACTIVE",   # SACTIVE = sim-only mem_active qualifier into D53 (structural inputs now per sheet-2)
            "CAS_SIM",   # (see above)
            "RAM_EN_SIM"}  # RAM_EN_SIM = sim-only DRAM-enable into D53 (real G1/G2A = VID_CPU_SEL/Ф2TTL, timing un-modeled)   # CAS_SIM = sim-only CAS scaffold leg out of D53 -> rail-15 net_boundary
POWER_ONLY = {"VSS_GND", "VBB_M5V", "VCC_5V", "VDD_12V", "NC_VBB_OPTION", "VCC_OPTION"}  # physical voltage/option rails; guarded by board/power reports, not logic LVS
                         # (the real rail-15 driver is D36.11 -> R57; the sim cannot reproduce that
                         # RC/delay chain, so the behavioral strobe rides this documented sim pin)
            # SA/SB/SC RETIRED 2026-07: D9 decodes from the real A10-A12 rails (sheet-1)

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
                if lp.rstrip("0123456789") in SIM_ONLY or lp in POWER_ONLY:
                    continue
                net2eps.setdefault(n, set()).add(f"{canon_inst}.{lp}")
    return {frozenset(eps) for eps in net2eps.values() if len(eps) >= 2}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--hdl", required=True)
    ap.add_argument("--kicad", help="KiCad XML netlist (kicad-cli output)")
    ap.add_argument("--board", help="board spec JSON (KiCad-free; same connectivity)")
    ap.add_argument("--map", required=True)
    ap.add_argument("--include-power", action="store_true",
                    help="include board nets marked as power (physical-pin LVS)")
    a = ap.parse_args()
    if not (a.kicad or a.board):
        ap.error("need --kicad or --board")
    mp = json.load(open(a.map))

    _, hdl = netlist_from_yosys.load(a.hdl)
    kic = (netlist_from_kicad.load(a.kicad) if a.kicad
           else netlist_from_board.load(a.board, include_power=a.include_power))

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
    nc_ok = True
    matched_nc = set()
    missing_nc = set()
    unexpected_nc = set()
    complete_ok = True
    complete_errors = []
    closed_ok = True
    closed_errors = []
    board = None
    chip_by_ref = {}
    mapped_pins_by_ref = {}

    if (
        "no_connects" in mp
        or "complete_instances" in mp
        or "closed_board_nets" in mp
        or mp.get("close_nonpower_nets_of_complete_instances")
    ):
        if not a.board:
            ap.error("map no_connects/complete_instances/closed_board_nets requires --board")
        board = json.load(open(a.board))
        chip_by_ref = {chip["ref"]: chip for chip in board["chips"]}
        for ref in mp["instances"]:
            chip_type = chip_by_ref.get(ref, {}).get("type", "")
            pinmap = kinst.get(ref, {}) or kpm.get(chip_type, {})
            mapped_pins_by_ref[ref] = {str(pin) for pin in pinmap}

    if "no_connects" in mp:
        mapped_pins = {
            (ref, pin) for ref, pins in mapped_pins_by_ref.items() for pin in pins
        }
        expected_nc = {tuple(item) for item in mp["no_connects"]}
        invalid_expected = expected_nc - mapped_pins
        if invalid_expected:
            refs = ", ".join(f"{ref}.{pin}" for ref, pin in sorted(invalid_expected))
            ap.error(f"map no_connects outside mapped pin scope: {refs}")

        actual_nc = {
            tuple(item) for item in board.get("no_connects", [])
            if tuple(item) in mapped_pins
        }
        matched_nc = expected_nc & actual_nc
        missing_nc = expected_nc - actual_nc
        unexpected_nc = actual_nc - expected_nc
        nc_ok = not missing_nc and not unexpected_nc

    complete_refs = set(mp.get("complete_instances", []))
    if complete_refs:
        invalid_refs = complete_refs - set(mp["instances"])
        if invalid_refs:
            ap.error("complete_instances outside instance map: " + ", ".join(sorted(invalid_refs)))

        endpoint_owner = {
            (ref, str(pin))
            for entry in board["nets"].values()
            for ref, pin in (entry["nodes"] if isinstance(entry, dict) else entry)
        }
        actual_all_nc = {tuple(item) for item in board.get("no_connects", [])}
        for ref in sorted(complete_refs):
            chip = chip_by_ref.get(ref)
            if chip is None:
                complete_errors.append(f"{ref}: absent from board")
                continue
            physical_pins = {str(pin) for pin in chip["pins"]}
            mapped_pins = mapped_pins_by_ref.get(ref, set())
            for pin in sorted(physical_pins - mapped_pins):
                complete_errors.append(f"{ref}.{pin}: physical pin is not mapped")
            for pin in sorted(mapped_pins - physical_pins):
                complete_errors.append(f"{ref}.{pin}: mapped pin is absent from board")
            for pin in sorted(
                physical_pins
                - {p for r, p in endpoint_owner if r == ref}
                - {p for r, p in actual_all_nc if r == ref}
            ):
                complete_errors.append(f"{ref}.{pin}: neither connected nor declared NC")
        complete_ok = not complete_errors

    closed_nets = set(mp.get("closed_board_nets", []))
    if closed_nets:
        mapped_pin_scope = {
            (ref, pin) for ref, pins in mapped_pins_by_ref.items() for pin in pins
        }
        for net in sorted(closed_nets):
            entry = board["nets"].get(net)
            if entry is None:
                closed_errors.append(f"{net}: absent from board")
                continue
            net_nodes = entry["nodes"] if isinstance(entry, dict) else entry
            for ref, pin in sorted(
                {tuple(item) for item in net_nodes} - mapped_pin_scope
            ):
                closed_errors.append(f"{net}: endpoint {ref}.{pin} is outside map")

    if mp.get("close_nonpower_nets_of_complete_instances"):
        touched_nonpower = set()
        for net, entry in board["nets"].items():
            if isinstance(entry, dict) and entry.get("power"):
                continue
            net_nodes = entry["nodes"] if isinstance(entry, dict) else entry
            if any(ref in complete_refs for ref, _ in net_nodes):
                touched_nonpower.add(net)
        for net in sorted(touched_nonpower - closed_nets):
            closed_errors.append(f"{net}: touches complete instance but is not declared closed")
    closed_ok = not closed_errors

    print(f"LVS connectivity check ({len(mp['instances'])} mapped instances)")
    print(f"  matched nets    : {len(matched)}")
    print(f"  only in HDL     : {len(only_hdl)}")
    print(f"  only in KiCad   : {len(only_kic)}")
    if "no_connects" in mp:
        print(f"  matched NC pads : {len(matched_nc)}")
        for label, items in (("missing NC", missing_nc), ("unexpected NC", unexpected_nc)):
            for ref, pin in sorted(items):
                print(f"    [{label}] {ref}.{pin}")
    if "complete_instances" in mp:
        print(f"  complete refs   : {len(complete_refs) if complete_ok else 0}")
        for error in complete_errors:
            print(f"    [incomplete] {error}")
    if "closed_board_nets" in mp:
        print(f"  closed nets     : {len(closed_nets) if closed_ok else 0}")
        for error in closed_errors:
            print(f"    [open scope] {error}")
    for label, s in (("HDL-only", only_hdl), ("KiCad-only", only_kic)):
        for net in sorted(s, key=lambda x: sorted(x)):
            print(f"    [{label}] {{{', '.join(sorted(net))}}}")
    ok = not only_hdl and not only_kic and nc_ok and complete_ok and closed_ok
    print("\n==> IN SYNC" if ok else "\n==> MISMATCH")
    return 0 if ok else 1

if __name__ == "__main__":
    sys.exit(main())
