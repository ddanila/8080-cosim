#!/usr/bin/env python3
"""R5.V5 physical gate for the routed four-layer Video card.

This complements netlist LVS and KiCad DRC with invariants that those tools do
not express directly: fixed plane layers, one continuous filled island per
plane, no signal copper on the plane layers, the exact edge-mounted VGA and bus
presentation, local bypass placement, and the deliberately narrow VGA escapes.
"""
from __future__ import annotations

import copy
import json
import math
import sys
from pathlib import Path

try:
    import pcbnew
except Exception:
    print("  SKIP  REVB-VIDEO-PCB: pcbnew not importable")
    raise SystemExit(0)

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
PCB = REPO / "fab/minimal-vga/revb/video.kicad_pcb"
PROJECT = REPO / "fab/minimal-vga/revb/video.kicad_pro"
BACKSIDE_BYPASS = {5, 7, 8, 9, 10, 11, 21}
PLANE_CONTRACT = {
    "GND": ("In1.Cu", "VJUGA rev B Video GND plane"),
    "VCC5": ("In2.Cu", "VJUGA rev B Video VCC5 plane"),
}


def mm(value: int) -> float:
    return pcbnew.ToMM(value)


def close(a: float, b: float, tolerance: float = 0.02) -> bool:
    return math.isclose(a, b, abs_tol=tolerance)


def pad_xy(footprint, number: str) -> tuple[float, float]:
    pad = footprint.FindPadByNumber(number)
    if pad is None:
        raise ValueError(f"{footprint.GetReference()}.{number} is absent")
    point = pad.GetPosition()
    return mm(point.x), mm(point.y)


def inspect(board) -> dict:
    footprints = {fp.GetReference(): fp for fp in board.GetFootprints()}
    errors: list[str] = []
    required = {"J_VGA", "J_BUS", "J_EXT", "R_CLK", "U1", *
                {f"U{i}" for i in range(1, 24)}, *
                {f"C{i}" for i in range(1, 24)}}
    if required - footprints.keys():
        errors.append(f"missing physical refs {sorted(required - footprints.keys())}")

    zones = []
    for zone in board.Zones():
        if zone.GetIsRuleArea():
            continue
        layer = board.GetLayerName(zone.GetLayer())
        outline = zone.Outline().BBox()
        filled_outlines = 0
        if zone.IsFilled():
            filled_outlines = zone.GetFilledPolysList(zone.GetLayer()).OutlineCount()
        zones.append({
            "net": zone.GetNetname(), "layer": layer,
            "name": zone.GetZoneName(), "pad_connection": int(zone.GetPadConnection()),
            "island_mode": int(zone.GetIslandRemovalMode()),
            "filled": bool(zone.IsFilled()), "filled_outlines": filled_outlines,
            "bbox": [mm(outline.GetX()), mm(outline.GetY()),
                     mm(outline.GetWidth()), mm(outline.GetHeight())],
        })

    tracks = []
    vias = []
    for item in board.GetTracks():
        if isinstance(item, pcbnew.PCB_VIA):
            vias.append({"diameter": mm(item.GetWidth(pcbnew.F_Cu)),
                         "drill": mm(item.GetDrillValue())})
            continue
        tracks.append({
            "net": item.GetNetname(), "layer": board.GetLayerName(item.GetLayer()),
            "width": mm(item.GetWidth()), "length": mm(item.GetLength()),
            "locked": bool(item.IsLocked()),
        })

    bypass = {}
    for number in range(1, 24):
        u = footprints.get(f"U{number}")
        cap = footprints.get(f"C{number}")
        if not u or not cap:
            continue
        upads = [p for p in u.Pads() if p.GetNetname() == "VCC5"]
        cpads = [p for p in cap.Pads() if p.GetNetname() == "VCC5"]
        if not upads or len(cpads) != 1:
            errors.append(f"U{number}/C{number} lacks a unique VCC5 endpoint")
            continue
        cpoint = cpads[0].GetPosition()
        distance = min(math.dist((mm(cpoint.x), mm(cpoint.y)),
                                 (mm(p.GetPosition().x), mm(p.GetPosition().y)))
                       for p in upads)
        bypass[number] = {
            "distance": distance,
            "side": board.GetLayerName(cap.GetLayer()),
        }

    vga = footprints.get("J_VGA")
    vga_record = {}
    if vga:
        numeric = {p.GetNumber(): [*map(mm, (p.GetPosition().x, p.GetPosition().y))]
                   for p in vga.Pads() if p.GetNumber().isdigit()}
        locks = [[*map(mm, (p.GetPosition().x, p.GetPosition().y))]
                 for p in vga.Pads() if not p.GetNumber()]
        vga_record = {
            "side": board.GetLayerName(vga.GetLayer()),
            "angle": vga.GetOrientationDegrees(), "numeric": numeric,
            "locks": sorted(locks),
        }

    bus = {}
    for ref in ("J_BUS", "J_EXT"):
        fp = footprints.get(ref)
        if fp:
            bus[ref] = {
                "side": board.GetLayerName(fp.GetLayer()),
                "angle": fp.GetOrientationDegrees(),
                "pin1": pad_xy(fp, "1"),
                "last": pad_xy(fp, "39" if ref == "J_BUS" else "10"),
            }

    clock_distance = None
    if footprints.get("U1") and footprints.get("R_CLK"):
        clock_distance = math.dist(pad_xy(footprints["U1"], "8"),
                                   pad_xy(footprints["R_CLK"], "1"))

    return {
        "errors": errors,
        "copper_layers": board.GetCopperLayerCount(),
        "zones": zones, "tracks": tracks, "vias": vias,
        "bypass": bypass, "vga": vga_record, "bus": bus,
        "clock_distance": clock_distance,
    }


def verify(data: dict) -> list[str]:
    errors = list(data.get("errors", []))
    if data.get("copper_layers") != 4:
        errors.append("Video stack is not four copper layers")
    rules = data.get("project_rules", {})
    if rules != {"min_track_width": 0.15, "min_copper_edge_clearance": 0.3}:
        errors.append("KiCad project does not freeze 0.15-mm track/0.30-mm edge limits")

    zones = data.get("zones", [])
    if len(zones) != 2:
        errors.append(f"expected two power planes, found {len(zones)}")
    for net, (layer, name) in PLANE_CONTRACT.items():
        found = [z for z in zones if z.get("net") == net]
        if len(found) != 1:
            errors.append(f"{net}: expected one plane")
            continue
        zone = found[0]
        if zone.get("layer") != layer or zone.get("name") != name:
            errors.append(f"{net}: plane layer/name differs")
        if zone.get("pad_connection") != int(pcbnew.ZONE_CONNECTION_FULL):
            errors.append(f"{net}: plane is not solid-connected")
        if zone.get("island_mode") != int(pcbnew.ISLAND_REMOVAL_MODE_ALWAYS):
            errors.append(f"{net}: isolated copper is not removed")
        if not zone.get("filled") or zone.get("filled_outlines") != 1:
            errors.append(f"{net}: filled plane is not one continuous island")
        bbox = zone.get("bbox", [])
        if len(bbox) != 4 or any(not close(a, b) for a, b in zip(bbox, (0.8, 0.8, 98.4, 98.4))):
            errors.append(f"{net}: plane does not cover the frozen 0.8-mm inset")

    tracks = data.get("tracks", [])
    if len(tracks) < 100:
        errors.append("routed signal copper is absent/incomplete")
    inner = [t for t in tracks if t.get("layer") in {"In1.Cu", "In2.Cu"}]
    if inner:
        errors.append(f"{len(inner)} signal tracks consume reserved plane layers")
    narrow = [t for t in tracks if t.get("width", 0) < 0.199]
    if any(t.get("width", 0) < 0.149 for t in tracks):
        errors.append("track below the 0.15-mm absolute floor")
    if any(t.get("net") not in {"VID_G", "HSYNC_N"} or
           t.get("layer") != "B.Cu" or not t.get("locked") or
           not close(t.get("width", 0), 0.15, 0.006) for t in narrow):
        errors.append("0.15-mm routing escaped the two locked VGA necks")
    for net in ("VID_G", "HSYNC_N"):
        if not any(t.get("net") == net and close(t.get("width", 0), 0.15, 0.006)
                   for t in narrow):
            errors.append(f"{net}: deterministic VGA neck is missing")
    for via in data.get("vias", []):
        if via.get("diameter", 0) < 0.599 or via.get("drill", 0) < 0.299:
            errors.append("via below the frozen 0.60/0.30-mm geometry")
            break

    bypass = data.get("bypass", {})
    if set(bypass) != set(range(1, 24)):
        errors.append("physical bypass coverage is not C1..C23")
    for number, record in bypass.items():
        if record.get("distance", 999) > 13.0:
            errors.append(f"C{number}: VCC path is not local ({record.get('distance'):.2f} mm)")
        expected = "B.Cu" if number in BACKSIDE_BYPASS else "F.Cu"
        if record.get("side") != expected:
            errors.append(f"C{number}: expected {expected} placement")

    vga = data.get("vga", {})
    if vga.get("side") != "F.Cu" or not close(vga.get("angle", 999), 180):
        errors.append("J_VGA edge presentation differs")
    numeric = vga.get("numeric", {})
    if set(numeric) != {str(i) for i in range(1, 16)}:
        errors.append("J_VGA signal pad set differs")
    else:
        if not close(numeric["1"][1], 2.5) or not close(numeric["2"][1], 1.0):
            errors.append("J_VGA signal rows are not 2.50/1.00 mm from the edge")
    locks = vga.get("locks", [])
    if len(locks) != 2 or not all(close(p[1], 1.0) for p in locks) or \
            not close(abs(locks[1][0] - locks[0][0]), 16.0):
        errors.append("J_VGA board locks are not tangent/aligned to the top edge")

    bus = data.get("bus", {})
    base, ext = bus.get("J_BUS", {}), bus.get("J_EXT", {})
    if base.get("side") != "F.Cu" or ext.get("side") != "B.Cu":
        errors.append("base/extension bus headers are not on opposite faces")
    if not close(base.get("angle", 999) % 360, 270) or \
            not close(ext.get("angle", 999) % 360, 270):
        errors.append("card bus posts do not point out through the bottom edge")
    if base and (not close(base["pin1"][1], 96.0) or
                 not close(base["last"][1], 96.0) or base["pin1"][0] <= base["last"][0]):
        errors.append("J_BUS row/pin direction differs")
    if ext and (not close(ext["pin1"][1], 91.0) or
                not close(ext["last"][1], 91.0) or ext["pin1"][0] >= ext["last"][0]):
        errors.append("J_EXT row/pin direction differs")

    if data.get("clock_distance") is None or data["clock_distance"] > 7.0:
        errors.append("R_CLK is not source-local to oscillator U1.8")
    raw_length = sum(t["length"] for t in tracks if t.get("net") == "DOTCLK_RAW")
    if raw_length <= 0 or raw_length > 15.0:
        errors.append(f"DOTCLK_RAW route is absent/long ({raw_length:.2f} mm)")
    route_ceilings = {
        "DOTCLK": 200.0, "PIXEL": 30.0, "VID_PIXEL": 45.0,
        "VID_R_DRV": 20.0, "VID_G_DRV": 20.0, "VID_B_DRV": 20.0,
    }
    for net, ceiling in route_ceilings.items():
        length = sum(t["length"] for t in tracks if t.get("net") == net)
        if length <= 0 or length > ceiling:
            errors.append(f"{net}: route {length:.2f} mm exceeds {ceiling:.0f} mm")
    return errors


def main() -> int:
    if not PCB.exists():
        print(f"REVB-VIDEO-PCB: FAIL missing {PCB}", file=sys.stderr)
        return 1
    data = inspect(pcbnew.LoadBoard(str(PCB)))
    if PROJECT.exists():
        rules = json.loads(PROJECT.read_text())["board"]["design_settings"]["rules"]
        data["project_rules"] = {
            key: rules.get(key) for key in
            ("min_track_width", "min_copper_edge_clearance")}
    errors = verify(data)
    if "--self-test" in sys.argv:
        mutations = []
        two_layer = copy.deepcopy(data); two_layer["copper_layers"] = 2
        mutations.append(("two-layer mutation", two_layer))
        wrong_rules = copy.deepcopy(data); wrong_rules["project_rules"]["min_track_width"] = 0.2
        mutations.append(("project-rule mutation", wrong_rules))
        broken_plane = copy.deepcopy(data); broken_plane["zones"][0]["filled_outlines"] = 2
        mutations.append(("split-plane mutation", broken_plane))
        inner_track = copy.deepcopy(data); inner_track["tracks"].append({
            "net":"DOTCLK", "layer":"In1.Cu", "width":0.2, "length":1.0, "locked":False})
        mutations.append(("inner-signal mutation", inner_track))
        wrong_bypass = copy.deepcopy(data); wrong_bypass["bypass"][9]["side"] = "F.Cu"
        mutations.append(("bypass-side mutation", wrong_bypass))
        wide_escape = copy.deepcopy(data)
        for track in wide_escape["tracks"]:
            if track["net"] == "VID_G" and close(track["width"], 0.15, 0.006):
                track["net"] = "DOTCLK"; break
        mutations.append(("thin-net mutation", wide_escape))
        long_pixel = copy.deepcopy(data)
        long_pixel["tracks"].append({
            "net":"PIXEL", "layer":"F.Cu", "width":0.2,
            "length":30.0, "locked":False})
        mutations.append(("pixel-length mutation", long_pixel))
        for label, mutation in mutations:
            if not verify(mutation):
                errors.append(f"{label} escaped")
    if errors:
        for error in errors:
            print(f"REVB-VIDEO-PCB: FAIL {error}", file=sys.stderr)
        return 1
    suffix = " + negative controls" if "--self-test" in sys.argv else ""
    print("REVB-VIDEO-PCB: PASS 4L F/GND/VCC/B, two continuous planes, "
          "23 local bypasses, exact VGA/bus geometry, constrained 0.15-mm necks" + suffix)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
