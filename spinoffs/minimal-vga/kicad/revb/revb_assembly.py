#!/usr/bin/env python3
"""Pure-Python expansion of the rev-B human assembly-marking contract."""

import json
import os


HERE = os.path.dirname(os.path.abspath(__file__))
CONTRACT = json.load(open(os.path.join(HERE, "assembly-markings.json")))


def expanded_parts(board_spec):
    """Return physical footprint ref -> type/DNP records, splitting bus pairs."""
    parts = {}
    for component in board_spec["chips"]:
        ref = component["ref"]
        typ = component["type"]
        dnp = bool(component.get("dnp", False))
        if typ == "REVB_BUS_39_10":
            base = "J_BUS" if ref == "J_BUS" else f"{ref}_BUS"
            extension = "J_EXT" if ref == "J_BUS" else f"{ref}_EXT"
            parts[base] = {"type": typ, "dnp": dnp, "bus_part": "base"}
            parts[extension] = {
                "type": typ, "dnp": dnp, "bus_part": "extension"
            }
        else:
            parts[ref] = {"type": typ, "dnp": dnp}
    return parts


def display_value(ref, part):
    override = CONTRACT["values_by_reference"].get(ref)
    if override:
        return override
    if part.get("bus_part"):
        return CONTRACT["bus_split_values"][part["bus_part"]]
    return CONTRACT["values_by_type"][part["type"]]


def marking_text(ref, part, multiline=False):
    separator = "\n" if multiline else " "
    visible_ref = CONTRACT.get("silk_reference_overrides", {}).get(ref, ref)
    text = f"{visible_ref}{separator}{display_value(ref, part)}"
    if part.get("dnp"):
        text += f"{separator}DNP"
    return text


def marking_placement(card, ref):
    """Return an optional reviewed assembly-label placement."""
    return CONTRACT.get("placements_by_card", {}).get(card, {}).get(ref)
