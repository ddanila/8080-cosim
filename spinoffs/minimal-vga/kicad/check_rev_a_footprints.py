#!/usr/bin/env python3
"""Validate that each Rev-A part's footprint matches the board model.

Runs under the KiCad Python (needs pcbnew). For every chip in the board JSON:
  1. every modelled pin has a matching footprint pad (catches renamed/wrong pins
     such as the USB-C shield S1 vs SH);
  2. DIP/socket pad counts match the declared package (DIP-16 -> 16 pads, etc.);
  3. reports footprint pads that carry no modelled pin (informational -- e.g. an
     unused socket pin), so an accidentally-dropped pin is visible.

This is the footprint half of the pre-fab check: the physical land pattern must
match what the schematic/netlist expects before a bare board is ordered.
"""
import json
import os
import re
import sys

import pcbnew

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gen_rev_a_pcb as gen

# Expected pad count implied by the type name (…DIP16… / DIP-40 / 1x14 / 2x05).
PKG_PAT = [
    (re.compile(r"DIP-?(\d+)"), lambda m: int(m.group(1))),
    (re.compile(r"DIP(\d\d)"), lambda m: int(m.group(1))),
    (re.compile(r"1x(\d+)"), lambda m: int(m.group(1))),
    (re.compile(r"2x(\d+)"), lambda m: 2 * int(m.group(1))),
]


def expected_pads(chip_type):
    for pat, fn in PKG_PAT:
        m = pat.search(chip_type)
        if m:
            return fn(m)
    return None


def main():
    board_json = sys.argv[1] if len(sys.argv) > 1 else \
        "spinoffs/minimal-vga/kicad/rev-a-physical.board.json"
    spec = json.load(open(board_json))

    errors, notes = [], []
    for chip in spec["chips"]:
        ref, typ = chip["ref"], chip["type"]
        lib, name = gen.FP_BY_REF.get(ref, gen.FP_BY_TYPE.get(typ, (None, None)))
        if lib is None:
            errors.append(f"{ref}: no footprint mapping for type {typ}")
            continue
        fp = pcbnew.FootprintLoad(os.path.join(gen.ROOT, lib), name)
        if fp is None:
            errors.append(f"{ref}: footprint {lib}/{name} failed to load")
            continue
        pads = {p.GetNumber() for p in fp.Pads()}
        model_pins = set(chip["pins"].keys())

        # Accept a modelled pin that matches a pad via a known cross-version
        # alias (USB-C shield S1/SH), same as the generator's pad resolution.
        aliased = {pin for pin in model_pins - pads
                   if pads & set(gen.PAD_ALIASES.get(pin, ()))}
        missing = sorted(model_pins - pads - aliased)
        if missing:
            errors.append(f"{ref} ({name}): modelled pins with no pad: {', '.join(missing)}")

        want = expected_pads(typ)
        if want is not None and len(pads) != want:
            # Strict pad count only for socketed DIP ICs. Oscillator cans in a
            # DIP-14 outline populate just 4 pins (OE/GND/OUT/VCC), so exclude.
            if "DIP" in typ and "OSC" not in typ:
                errors.append(f"{ref} ({name}): {len(pads)} pads, expected {want} for {typ}")

        unused = sorted(pads - model_pins, key=lambda s: (len(s), s))
        if unused:
            notes.append(f"{ref} ({name}): footprint pads not in model: {', '.join(unused)}")

    if notes:
        print("Footprint notes (unused pads -- informational):")
        for n in notes:
            print(f"  {n}")
    if errors:
        print(f"Rev A footprint check: FAIL ({len(errors)} issues)")
        for e in errors:
            print(f"  {e}")
        return 1
    print(f"Rev A footprint check: PASS ({len(spec['chips'])} parts, all modelled pins land on pads)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
