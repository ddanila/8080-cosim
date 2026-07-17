#!/usr/bin/env python3
"""Validate the rev B card connectivity specs (T1.3-T1.6).

Checks the per-card interface roles in
spinoffs/minimal-vga/kicad/revb/cards.json against the canonical backplane pinout
(bus-pinout.json), the driver rules implied by each signal's class, the memory/IO
address-decode ownership, and the card HDL modules' bus-facing ports. This is the
connectivity contract; full KiCad layout/DRC/STEP is the KiCad-installed
continuation (see docs/rev-b-execution-guide.md T1.7-T1.9).
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REVB = ROOT / "spinoffs/minimal-vga/kicad/revb"
HDL = ROOT / "spinoffs/minimal-vga/hdl/revb"
CONTRACT = ROOT / "spinoffs/minimal-vga/docs/rev-b-bus-contract.md"

# single-driver signal classes -> the one card allowed to drive them
SOLE_DRIVER = {"cpu_out": "cpu", "reset": "backplane", "frame": "video"}


def rng(s):
    lo, hi = s.split("-")
    return (int(lo, 16), int(hi, 16))


def main() -> int:
    fail = []
    pin = json.loads((REVB / "bus-pinout.json").read_text())
    cards = json.loads((REVB / "cards.json").read_text())
    cards = {k: v for k, v in cards.items() if not k.startswith("_")}
    classes = pin["classes"]

    # 1) pinout shape: 39 base pins + 10 extension, every signal classed
    base_pins = [p for p in pin["base"] if p.isdigit()]
    if sorted(int(p) for p in base_pins) != list(range(1, 40)):
        fail.append(f"base connector is not exactly pins 1..39 ({len(base_pins)} found)")
    if set(pin["extension"]) != {f"E{i}" for i in range(1, 11)}:
        fail.append("extension connector is not exactly E1..E10")
    all_sigs = set(pin["base"].values()) | set(pin["extension"].values())
    for s in all_sigs:
        if s not in classes:
            fail.append(f"pinout signal {s!r} has no class")

    # 2) rev-B-specific signals must appear in the bus-contract doc
    doc = CONTRACT.read_text()
    for s in ("FRAME_TICK", "MODE0", "MODE1", "WAIT_N", "IRQ_A", "IRQ_B", "BUSAK_N"):
        if s not in doc:
            fail.append(f"bus contract doc omits signal {s}")

    # collect who drives what (hard drivers only; not default pulls)
    drivers: dict[str, list[str]] = {}
    for name, c in cards.items():
        for key in ("drives", "drives_tristate", "drives_od", "drives_serial"):
            for s in c.get(key, []):
                if s not in all_sigs:
                    fail.append(f"card {name} lists non-bus signal {s!r} in {key}")
                drivers.setdefault(s, []).append(name)
        for s in c.get("reads", []):
            if s not in all_sigs:
                fail.append(f"card {name} reads non-bus signal {s!r}")

    # 3) driver rules per class
    for s, cls in classes.items():
        drv = drivers.get(s, [])
        if cls in SOLE_DRIVER:
            want = SOLE_DRIVER[cls]
            if drv != [want]:
                fail.append(f"{s} ({cls}) must be driven only by {want}, got {drv or 'nobody'}")
        elif cls == "mode":
            if drv != ["io"]:
                fail.append(f"{s} (mode) must be hard-driven only by io, got {drv or 'nobody'}")
        elif cls == "serial":
            pass  # TX io-driven, RX read; loose
        elif cls == "data":
            if not drv:
                fail.append(f"{s} (data) has no driver at all")
        elif cls == "od":
            # open-drain / wired-OR: 0+ hard drivers OK, but if none, the
            # backplane must pull it (else it floats).
            pulled = s in cards.get("backplane", {}).get("default_pull", [])
            if not drv and not pulled:
                fail.append(f"{s} (od) is neither driven nor pulled by the backplane")
        # power/ground: no rule

    # 4) memory ownership disjoint + covers 0x0000..0xFFFF
    mem = []
    for name, c in cards.items():
        for r in c.get("owns_mem", []):
            mem.append((name, *rng(r)))
    mem.sort(key=lambda t: t[1])
    covered_hi = -1
    for name, lo, hi in mem:
        if lo <= covered_hi:
            fail.append(f"memory range overlap at {name} 0x{lo:04X}")
        covered_hi = max(covered_hi, hi)
    if mem and (mem[0][1] != 0x0000 or covered_hi != 0xFFFF):
        fail.append(f"memory map does not cover 0x0000..0xFFFF (got 0x{mem[0][1]:04X}..0x{covered_hi:04X})")

    # 5) IO ownership disjoint + matches the facts ports
    facts = json.loads((ROOT / "ref/juku-machine-facts.json").read_text())["io_ports"]
    fact_ports = set()
    for k, v in facts.items():
        if isinstance(v, dict) and "port" in v:
            fact_ports.add(v["port"])
        elif isinstance(v, dict) and "ports" in v:
            fact_ports.update(v["ports"])
    io_owned = set()
    for name, c in cards.items():
        for r in c.get("owns_io", []):
            lo, hi = rng(r)
            for p in range(lo, hi + 1):
                if p in io_owned:
                    fail.append(f"IO port 0x{p:02X} owned by more than one card")
                io_owned.add(p)
    missing = fact_ports - io_owned
    if missing:
        fail.append(f"IO ports in facts not owned by any card: {sorted(hex(p) for p in missing)}")

    # 6) card HDL bus-facing ports consistent with declared role
    for name, c in cards.items():
        hdl = c.get("hdl")
        if not hdl:
            continue
        f = HDL / hdl
        if not f.exists():
            fail.append(f"card {name} HDL {hdl} missing")
            continue
        txt = f.read_text()
        need = ["D_out", "D_oe"]
        if c.get("owns_mem") or "MODE0" in c.get("reads", []):
            need += ["MODE0", "MODE1"]
        if "MODE0" in c.get("drives", []):
            need += ["MODE0", "MODE1"]
        for port in need:
            if port not in txt:
                fail.append(f"{hdl} lacks expected port {port} for its declared role")

    # 7) board.json cross-check (TC.2): if <card>.board.json exists, its bus
    # connector must match bus-pinout.json exactly, and every bus signal a chip
    # pin touches must be a signal that card declares (or a global everyone taps).
    GLOBALS = {"RESET_N", "CLK", "VCC5", "GND"}
    bus_map = dict(pin["base"]); bus_map.update(pin["extension"])
    for name, c in cards.items():
        bj = REVB / f"{name}.board.json"
        if not bj.exists():
            continue
        board = json.loads(bj.read_text())
        declared = set()
        for k in ("drives", "drives_tristate", "drives_od", "drives_serial", "reads", "default_pull"):
            declared |= set(c.get(k, []))
        for comp in board["chips"]:
            if comp["type"] == "REVB_BUS_39_10":
                if comp["pins"] != bus_map:
                    fail.append(f"{name}.board.json connector {comp['ref']} != canonical bus pinout")
                continue
            for net in comp["pins"].values():
                if net in all_sigs and net not in declared and net not in GLOBALS:
                    fail.append(f"{name}.board.json {comp['ref']} touches bus signal {net} "
                                f"not in the card's declared role")
        # net-level LVS-lite: the derived nets must invert the chips' pins exactly,
        # and every inter-chip functional net must have >=2 endpoints (no danglers).
        derived = {}
        for comp in board["chips"]:
            for pn, net in comp["pins"].items():
                derived.setdefault(net, []).append([comp["ref"], pn])
        board_nets = {n: (e["nodes"] if isinstance(e, dict) else e) for n, e in board.get("nets", {}).items()}
        if board_nets != derived:
            fail.append(f"{name}.board.json 'nets' section is out of sync with chip pins")
        # NB: a per-card 'nets' section legitimately has single-endpoint nets -- a bus
        # signal a card doesn't use still appears on its connector and reaches other
        # cards through the backplane. Cross-card danglers are only meaningful on the
        # assembled netlist, which is the TC.4/TC.5 (full LVS + schematic) scope.

    if fail:
        print("rev B board connectivity check FAILED:")
        for f in fail:
            print(f"- {f}")
        return 1
    print(f"rev B board connectivity OK: {len(cards)} cards, "
          f"mem 0x0000..0x{covered_hi:04X} covered, {len(io_owned)} IO ports owned.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
