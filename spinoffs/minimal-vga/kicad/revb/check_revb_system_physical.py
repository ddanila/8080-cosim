#!/usr/bin/env python3
"""R5.V6 five-board mechanical/power gate.

Run with KiCad's Python (the repository env resolves it):

    python3 check_revb_system_physical.py --self-test

The checker deliberately models the routed copper rather than estimating a
Manhattan length.  Every segment becomes a resistor from its actual length,
width and one-ounce copper thickness; vias and plated pads join the two layers.
It then solves the VCC_BUS and GND_BUS networks with the frozen card currents.
"""
from __future__ import annotations

import argparse
import copy
import json
import math
import os
import sys
from collections import defaultdict

try:
    import numpy as np
    import pcbnew
except Exception as exc:  # pragma: no cover - exercised on non-CAD hosts
    print(f"R5.V6 system physical: required KiCad Python/numpy unavailable: {exc}")
    raise SystemExit(2)

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
PCB = os.path.join(REPO, "fab", "minimal-vga", "revb", "backplane.kicad_pcb")
CONTRACT_PATH = os.path.join(HERE, "five-board-physical.json")
BOARD_JSON = os.path.join(HERE, "backplane.board.json")
MATING_PATH = os.path.join(HERE, "mating.json")


def mm(value):
    return pcbnew.ToMM(value)


def component_map():
    spec = json.load(open(BOARD_JSON, encoding="utf-8"))
    return {c["ref"]: c for c in spec["chips"]}


def pad_node(board, ref, number, nodes):
    fps = {fp.GetReference(): fp for fp in board.GetFootprints()}
    fp = fps.get(ref)
    if fp is None:
        raise ValueError(f"missing footprint {ref}")
    pad = fp.FindPadByNumber(str(number))
    if pad is None:
        raise ValueError(f"{ref}: missing pad {number}")
    pos = pad.GetPosition()
    candidates = ((pos.x, pos.y, pcbnew.F_Cu), (pos.x, pos.y, pcbnew.B_Cu))
    for node in candidates:
        if node in nodes:
            return node
    raise ValueError(f"{ref}.{number}: no routed node at pad centre")


def copper_graph(board, netname, contract):
    """Return (nodes, resistive edges, ordinary track widths)."""
    rho = contract["distribution"]["copper_resistivity_ohm_mm"]
    thickness = contract["distribution"]["copper_thickness_mm"]
    nodes, edges, widths = set(), [], []
    for item in board.Tracks():
        if item.GetNetname() != netname:
            continue
        if isinstance(item, pcbnew.PCB_VIA):
            pos = item.GetPosition()
            a = (pos.x, pos.y, pcbnew.F_Cu)
            z = (pos.x, pos.y, pcbnew.B_Cu)
            resistance = 0.0005  # conservative small plated-barrel allowance
        else:
            start, end, layer = item.GetStart(), item.GetEnd(), item.GetLayer()
            a = (start.x, start.y, layer)
            z = (end.x, end.y, layer)
            length = mm(round(math.hypot(end.x - start.x, end.y - start.y)))
            width = mm(item.GetWidth())
            widths.append(width)
            resistance = (rho * length / (width * thickness)) if length else 1e-9
        nodes.update((a, z))
        edges.append((a, z, resistance))

    # Every PTH pad is a real inter-layer bridge.  The tiny allowance prevents an
    # ideal zero-ohm edge from destabilising the conductance matrix.
    for fp in board.GetFootprints():
        for pad in fp.Pads():
            if (pad.GetNetname() != netname or not pad.HasHole()
                    or pad.GetAttribute() != pcbnew.PAD_ATTRIB_PTH):
                continue
            pos = pad.GetPosition()
            a = (pos.x, pos.y, pcbnew.F_Cu)
            z = (pos.x, pos.y, pcbnew.B_Cu)
            nodes.update((a, z))
            edges.append((a, z, 0.0001))
    return nodes, edges, widths


def solve_net(board, netname, source, loads, contract):
    """Solve copper voltage drop with source fixed at zero volts.

    loads maps (ref, pad) to current drawn in amperes.  The returned pad drops are
    positive magnitudes from the source pad through the routed copper.
    """
    nodes, edges, widths = copper_graph(board, netname, contract)
    if not nodes or not edges:
        raise ValueError(f"{netname}: no routed copper")
    source_node = pad_node(board, source[0], source[1], nodes)
    adjacency = defaultdict(list)
    for a, z, resistance in edges:
        adjacency[a].append(z)
        adjacency[z].append(a)
    seen, stack = {source_node}, [source_node]
    while stack:
        for other in adjacency[stack.pop()]:
            if other not in seen:
                seen.add(other)
                stack.append(other)
    if seen != nodes:
        raise ValueError(f"{netname}: routed copper has {len(nodes) - len(seen)} isolated nodes")

    unknown = sorted(n for n in seen if n != source_node)
    index = {node: i for i, node in enumerate(unknown)}
    conductance = np.zeros((len(unknown), len(unknown)), dtype=float)
    current = np.zeros(len(unknown), dtype=float)
    for a, z, resistance in edges:
        g = 1.0 / resistance
        if a != source_node:
            conductance[index[a], index[a]] += g
        if z != source_node:
            conductance[index[z], index[z]] += g
        if a != source_node and z != source_node:
            conductance[index[a], index[z]] -= g
            conductance[index[z], index[a]] -= g
    load_nodes = {}
    for endpoint, amps in loads.items():
        node = pad_node(board, endpoint[0], endpoint[1], nodes)
        load_nodes[endpoint] = node
        if node != source_node:
            current[index[node]] += amps
    voltage = np.linalg.solve(conductance, current)
    drops = {endpoint: (0.0 if node == source_node else float(voltage[index[node]]))
             for endpoint, node in load_nodes.items()}
    return {"drops": drops, "widths": widths, "max_node_drop": float(max(voltage, default=0.0))}


def effective_resistance(board, netname, source, sink, contract):
    solved = solve_net(board, netname, source, {(sink[0], sink[1]): 1.0}, contract)
    return solved["drops"][(sink[0], sink[1])]


def check_pin(fails, comps, ref, expected):
    got = comps.get(ref, {}).get("pins")
    if got != expected:
        fails.append(f"{ref} pinout {got!r} != {expected!r}")


def audit(board, contract, quiet=False):
    fails, notes = [], []
    mating = json.load(open(MATING_PATH, encoding="utf-8"))
    comps = component_map()
    fps = {fp.GetReference(): fp for fp in board.GetFootprints()}

    # Mechanical assignment and same-facing component envelopes.
    stack = contract["board_stack"]
    if abs(stack["slot_pitch_mm"] - mating["slot_pitch"]) > 1e-9:
        fails.append("system slot pitch differs from mating.json")
    if int(stack["video_slot"]) != 5 or stack["slot_assignment"]["5"]["card"] != "video":
        fails.append("Video must occupy end slot 5")
    if int(stack["video_buffer_slot"]) != 4 or stack["slot_assignment"]["4"]["card"] != "empty":
        fails.append("slot 4 must remain the first-article Video clearance buffer")
    occupied = []
    for slot_text, item in stack["slot_assignment"].items():
        if item["card"] == "empty":
            continue
        occupied.append((int(slot_text), item["card"]))
    minimum_gap = float("inf")
    gap_rows = []
    envelopes = stack["card_step_envelopes_mm"]
    for (left_slot, left_card), (right_slot, right_card) in zip(occupied, occupied[1:]):
        left = envelopes[left_card]
        right = envelopes[right_card]
        gap = ((right_slot - left_slot) * stack["slot_pitch_mm"] + right["z_min"]
               - left["z_max"])
        minimum_gap = min(minimum_gap, gap)
        gap_rows.append((left_card, right_card, gap))
        if gap < stack["minimum_adjacent_clearance_mm"]:
            fails.append(f"{left_card}->{right_card} assembled clearance {gap:.3f} mm")
    if abs(stack["vga_shell_projection_mm"] - 5.80) > 1e-9:
        fails.append("VGA mating-face projection differs from the exact footprint contract")
    if mating["card_base_side"] == mating["card_ext_side"]:
        fails.append("base and extension card headers must remain on opposite faces")

    # Exact, fused and directionally protected input topology.
    check_pin(fails, comps, "J_PWR", {"1": "PWR_RAW", "2": "GND_BUS"})
    check_pin(fails, comps, "F_MAIN", {"1": "PWR_RAW", "2": "VCC_BUS"})
    check_pin(fails, comps, "D_REV", {"1": "VCC_BUS", "2": "GND_BUS"})
    check_pin(fails, comps, "F_VBUS", {"1": "VBUS_IN", "2": "USB_FUSED"})
    check_pin(fails, comps, "D_USB", {"1": "VCC_BUS", "2": "USB_FUSED"})
    check_pin(fails, comps, "W_VCC", {"1": "VCC_BUS", "2": "VCC5"})
    check_pin(fails, comps, "W_GND", {"1": "GND_BUS", "2": "GND"})
    raw_nodes = set(tuple(x) for x in json.load(open(BOARD_JSON, encoding="utf-8"))["nets"]["PWR_RAW"]["nodes"])
    if raw_nodes != {("J_PWR", "1"), ("F_MAIN", "1")}:
        fails.append(f"PWR_RAW has an unfused branch: {sorted(raw_nodes)}")
    vbus_nodes = set(tuple(x) for x in json.load(open(BOARD_JSON, encoding="utf-8"))["nets"]["VBUS_IN"]["nodes"])
    expected_vbus = {("F_VBUS", "1"), ("J_USBC", "VBUS")}
    if vbus_nodes != expected_vbus:
        fails.append(f"VBUS_IN bypasses F_VBUS: {sorted(vbus_nodes)}")

    expected_footprints = {
        "J_PWR": "BarrelJack_Wuerth_6941xx301002",
        "F_MAIN": "Fuse_Bourns_MF-R250",
        "F_VBUS": "Fuse_Bourns_MF-R110",
        "D_REV": "D_DO-201AD_P5.08mm_Vertical_AnodeUp",
        "D_USB": "D_DO-201AD_P5.08mm_Vertical_AnodeUp",
        "W_VCC": "WireLink_22AWG_P5.08mm",
        "W_GND": "WireLink_22AWG_P5.08mm",
    }
    for ref, wanted in expected_footprints.items():
        if ref not in fps:
            fails.append(f"missing protected-power footprint {ref}")
        else:
            actual = str(fps[ref].GetFPID().GetLibItemName())
            if actual != wanted:
                fails.append(f"{ref} footprint is {actual}, expected {wanted}")

    supply = contract["supply"]
    normal = contract["normal_input"]
    usb = contract["usb_service_input"]
    dist = contract["distribution"]
    total_a = stack["total_current_ma"] / 1000.0
    summed_a = (stack["backplane_local_current_ma"]
                + sum(item["current_ma"] for item in stack["slot_assignment"].values())) / 1000.0
    if abs(summed_a - total_a) > 1e-9:
        fails.append(f"five-board current rows sum to {summed_a:.3f} A, not {total_a:.3f} A")
    if abs(supply["receipt_test_load_a"] - total_a) > 1e-9:
        fails.append("supply receipt-test load does not equal the frozen machine budget")
    if supply["rated_current_a"] < 2.0 or supply["rated_current_a"] < total_a:
        fails.append("qualified supply lacks current headroom")
    if normal["connector_rating_a"] < supply["rated_current_a"]:
        fails.append("barrel connector rating is below qualified supply current")
    if normal["fuse_hold_a_70c"] <= total_a:
        fails.append("F_MAIN cannot hold the five-board load at 70 C")
    if normal["reverse_protection_rating_a"] < supply["rated_current_a"]:
        fails.append("D_REV current rating is below qualified supply current")
    if usb["system_power_qualified"] or usb["fuse_hold_a_23c"] >= total_a:
        fails.append("USB service input is incorrectly qualified for the full machine")

    card_loads = {f"J_S{slot}_BUS": item["current_ma"] / 1000.0
                  for slot, item in ((int(k), v) for k, v in stack["slot_assignment"].items())}
    vcc_loads = {(ref, "18"): amps for ref, amps in card_loads.items() if amps}
    gnd_loads = {(ref, "17"): amps for ref, amps in card_loads.items() if amps}
    local_a = stack["backplane_local_current_ma"] / 1000.0
    vcc_loads[(dist["vcc_local_link"], "1")] = local_a
    gnd_loads[(dist["gnd_local_link"], "1")] = local_a
    try:
        vcc = solve_net(board, dist["vcc_net"], dist["vcc_source"], vcc_loads, contract)
        gnd = solve_net(board, dist["gnd_net"], dist["gnd_source"], gnd_loads, contract)
        raw_r = effective_resistance(board, dist["raw_net"], dist["raw_source"],
                                     dist["raw_sink"], contract)
    except (ValueError, np.linalg.LinAlgError) as exc:
        fails.append(str(exc))
        vcc = gnd = {"drops": {}, "widths": [], "max_node_drop": float("inf")}
        raw_r = float("inf")

    for name, solved, minimum in (
            (dist["vcc_net"], vcc, dist["minimum_bus_track_width_mm"]),
            (dist["gnd_net"], gnd, dist["minimum_bus_track_width_mm"])):
        if not solved["widths"] or min(solved["widths"], default=0) + 1e-6 < minimum:
            fails.append(f"{name} minimum routed width is {min(solved['widths'], default=0):.3f} mm")
    _, _, raw_widths = copper_graph(board, dist["raw_net"], contract)
    if not raw_widths or min(raw_widths) + 1e-6 < dist["minimum_raw_track_width_mm"]:
        fails.append(f"PWR_RAW minimum routed width is {min(raw_widths, default=0):.3f} mm")

    shared_r = (raw_r + normal["fuse_resistance_ohm_max_initial"]
                + 2.0 * normal["connector_contact_resistance_ohm_max_per_conductor"])
    shared_drop = total_a * shared_r
    ripple_half = supply["ripple_noise_mv_pp_max"] / 2000.0
    slot_results = {}
    worst_margin = float("inf")
    for slot, item in ((int(k), v) for k, v in stack["slot_assignment"].items()):
        if item["card"] == "empty":
            continue
        vkey, gkey = (f"J_S{slot}_BUS", "18"), (f"J_S{slot}_BUS", "17")
        if vkey not in vcc["drops"] or gkey not in gnd["drops"]:
            fails.append(f"slot {slot} lacks solved VCC/GND drops")
            continue
        amps = item["current_ma"] / 1000.0
        copper_drop = vcc["drops"][vkey] + gnd["drops"][gkey]
        contact_drop = 2.0 * dist["bus_contact_resistance_ohm_max_each_credited"] * amps
        trough = (supply["receipt_test_minimum_v_at_1_351a"] - ripple_half
                  - shared_drop - copper_drop - contact_drop)
        margin = trough - dist["minimum_logic_rail_v"]
        worst_margin = min(worst_margin, margin)
        slot_results[slot] = {"card": item["card"], "copper_drop_v": copper_drop,
                              "modeled_trough_v": trough, "margin_v": margin}
        if margin + 1e-9 < dist["minimum_modeled_trough_margin_v"]:
            fails.append(f"slot {slot} {item['card']} trough margin only {margin:.3f} V")

    # The broad published tolerance is recorded honestly; acceptance is the explicit
    # delivered-unit load test, not an implication that every -5% unit is adequate.
    datasheet_min = supply["output_nominal_v"] * (1 - supply["voltage_tolerance_percent"] / 100)
    worst_other = 0.0
    if slot_results:
        worst_other = max(shared_drop + row["copper_drop_v"]
                          + 2 * dist["bus_contact_resistance_ohm_max_each_credited"]
                          * (stack["slot_assignment"][str(slot)]["current_ma"] / 1000)
                          for slot, row in slot_results.items())
    datasheet_corner_trough = datasheet_min - ripple_half - worst_other
    notes.append(f"supply headroom {supply['rated_current_a'] - total_a:.3f} A")
    notes.append(f"raw effective resistance {raw_r * 1000:.3f} mOhm")
    notes.append(f"shared input drop {shared_drop * 1000:.2f} mV at {total_a:.3f} A")
    notes.append(f"minimum modeled slot trough {min((r['modeled_trough_v'] for r in slot_results.values()), default=0):.3f} V")
    notes.append(f"published -5% corner including ripple would be {datasheet_corner_trough:.3f} V; receipt test is mandatory")
    notes.append("adjacent gaps " + ", ".join(f"{a}->{b} {g:.2f} mm" for a, b, g in gap_rows))

    result = {"fails": fails, "notes": notes, "slot_results": slot_results,
              "minimum_gap_mm": minimum_gap, "worst_margin_v": worst_margin,
              "raw_resistance_ohm": raw_r}
    if not quiet:
        if fails:
            print(f"R5.V6 system physical: {len(fails)} violation(s) -> FAIL")
            for failure in fails:
                print(f"    {failure}")
        else:
            print("R5.V6 system physical OK")
            for note in notes:
                print(f"    {note}")
            for slot, row in sorted(slot_results.items()):
                print(f"    S{slot} {row['card']}: copper {row['copper_drop_v']*1000:.2f} mV, "
                      f"trough {row['modeled_trough_v']:.3f} V, margin {row['margin_v']:.3f} V")
    return result


def self_test(contract):
    baseline = pcbnew.LoadBoard(PCB)
    if audit(baseline, contract, quiet=True)["fails"]:
        print("self-test setup: real board is not green")
        return False

    narrow = pcbnew.LoadBoard(PCB)
    victim = next(t for t in narrow.Tracks()
                  if not isinstance(t, pcbnew.PCB_VIA) and t.GetNetname() == "VCC_BUS")
    victim.SetWidth(pcbnew.FromMM(0.20))
    if not audit(narrow, contract, quiet=True)["fails"]:
        print("self-test failed: narrow VCC_BUS mutation was accepted")
        return False

    narrow_raw = copy.deepcopy(contract)
    narrow_raw["distribution"]["minimum_raw_track_width_mm"] = 2.5
    if not audit(pcbnew.LoadBoard(PCB), narrow_raw, quiet=True)["fails"]:
        print("self-test failed: inadequate raw-input width was accepted")
        return False

    collision = copy.deepcopy(contract)
    collision["board_stack"]["slot_pitch_mm"] = 12.0
    if not audit(pcbnew.LoadBoard(PCB), collision, quiet=True)["fails"]:
        print("self-test failed: wrong slot pitch was accepted")
        return False

    low_supply = copy.deepcopy(contract)
    low_supply["supply"]["receipt_test_minimum_v_at_1_351a"] = 4.60
    if not audit(pcbnew.LoadBoard(PCB), low_supply, quiet=True)["fails"]:
        print("self-test failed: low delivered-unit voltage was accepted")
        return False

    stale_budget = copy.deepcopy(contract)
    stale_budget["board_stack"]["slot_assignment"]["5"]["current_ma"] += 1
    if not audit(pcbnew.LoadBoard(PCB), stale_budget, quiet=True)["fails"]:
        print("self-test failed: stale total-current row was accepted")
        return False
    print("R5.V6 negative controls OK: narrow bus, narrow raw path, 12-mm pitch, "
          "low supply and stale current total all rejected")
    return True


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if not os.path.isfile(PCB):
        print(f"missing routed backplane: {PCB}")
        return 1
    contract = json.load(open(CONTRACT_PATH, encoding="utf-8"))
    result = audit(pcbnew.LoadBoard(PCB), contract)
    if result["fails"]:
        return 1
    if args.self_test and not self_test(contract):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
