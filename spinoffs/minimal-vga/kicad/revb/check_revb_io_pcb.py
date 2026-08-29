#!/usr/bin/env python3
"""R5.I5 physical gate for the routed, expanded two-layer I/O card.

KiCad DRC owns copper/clearance correctness.  This independent gate owns the
physical policy that DRC cannot express: front-side decouplers (card-stack
clearance), local bypass distance, ordered/accessible POST LEDs, accessible
PIT/sound/jumper controls, bus presentation, and minimum routed geometry.
"""
from __future__ import annotations

import copy
import math
import sys
from pathlib import Path

try:
    import pcbnew
except Exception:
    print("  SKIP  REVB-IO-PCB: pcbnew not importable")
    raise SystemExit(0)


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
PCB = REPO / "fab/minimal-vga/revb/io.kicad_pcb"


def mm(value: int) -> float:
    return pcbnew.ToMM(value)


def close(a: float, b: float, tolerance: float = 0.03) -> bool:
    return math.isclose(a, b, abs_tol=tolerance)


def pad_xy(fp, number: str) -> tuple[float, float]:
    pad = fp.FindPadByNumber(number)
    if pad is None:
        raise ValueError(f"{fp.GetReference()}.{number} is absent")
    point = pad.GetPosition()
    return mm(point.x), mm(point.y)


def inspect(board) -> dict:
    fps = {fp.GetReference(): fp for fp in board.GetFootprints()}
    expected = {
        "J_BUS", "J_EXT", "J_KBD", "J_IOSEL", "J_PIT_TP", "J_SOUND",
        "JP_BAUD", "JP_CLK_SRC", "BZ1", "Q1", "R_SOUND_BASE",
        "R_SOUND_PD", *{f"U{i}" for i in range(1, 10)},
        *{f"C{i}" for i in range(1, 10)}, *{f"D_POST{i}" for i in range(8)},
        *{f"R_POST{i}" for i in range(8)},
    }
    errors = []
    if set(fps) != expected:
        errors.append(f"physical ref set differs: missing={sorted(expected-set(fps))}, extra={sorted(set(fps)-expected)}")

    bypass = {}
    for number in range(1, 10):
        u, cap = fps.get(f"U{number}"), fps.get(f"C{number}")
        if not u or not cap:
            continue
        cpads = [p for p in cap.Pads() if p.GetNetname() == "VCC5"]
        upads = [p for p in u.Pads() if p.GetNetname() == "VCC5"]
        if len(cpads) != 1 or not upads:
            errors.append(f"U{number}/C{number} lacks a unique bypass endpoint")
            continue
        cp = cpads[0].GetPosition()
        distance = min(math.dist((mm(cp.x), mm(cp.y)),
                                 (mm(p.GetPosition().x), mm(p.GetPosition().y)))
                       for p in upads)
        bypass[number] = {"distance": distance,
                          "side": board.GetLayerName(cap.GetLayer())}

    leds = []
    for bit in range(8):
        fp = fps.get(f"D_POST{bit}")
        if fp:
            p = fp.FindPadByNumber("2").GetPosition()
            leds.append({"bit": bit, "x": mm(p.x), "y": mm(p.y),
                         "side": board.GetLayerName(fp.GetLayer())})

    controls = {}
    for ref in ("BZ1", "Q1", "J_SOUND", "J_PIT_TP", "J_IOSEL",
                "JP_BAUD", "JP_CLK_SRC"):
        fp = fps.get(ref)
        if fp:
            box = fp.GetBoundingBox(False, False)
            controls[ref] = {
                "side": board.GetLayerName(fp.GetLayer()),
                "bbox": [mm(box.GetLeft()), mm(box.GetTop()),
                         mm(box.GetRight()), mm(box.GetBottom())],
                "nets": sorted(p.GetNetname() for p in fp.Pads()),
            }

    bus = {}
    for ref in ("J_BUS", "J_EXT"):
        fp = fps.get(ref)
        if fp:
            bus[ref] = {"side": board.GetLayerName(fp.GetLayer()),
                        "angle": fp.GetOrientationDegrees(),
                        "pin1": pad_xy(fp, "1"),
                        "last": pad_xy(fp, "39" if ref == "J_BUS" else "10")}

    tracks, vias = [], []
    for item in board.GetTracks():
        if isinstance(item, pcbnew.PCB_VIA):
            vias.append({"diameter": mm(item.GetWidth(pcbnew.F_Cu)),
                         "drill": mm(item.GetDrillValue())})
        else:
            tracks.append({"width": mm(item.GetWidth()),
                           "layer": board.GetLayerName(item.GetLayer()),
                           "net": item.GetNetname()})
    return {"errors": errors, "copper_layers": board.GetCopperLayerCount(),
            "bypass": bypass, "leds": leds, "controls": controls,
            "bus": bus, "tracks": tracks, "vias": vias}


def verify(data: dict) -> list[str]:
    errors = list(data.get("errors", []))
    if data.get("copper_layers") != 2:
        errors.append("I/O card is not two copper layers")
    bypass = data.get("bypass", {})
    if set(bypass) != set(range(1, 10)):
        errors.append("physical bypass coverage is not C1..C9")
    for number, row in bypass.items():
        if row.get("side") != "F.Cu":
            errors.append(f"C{number} is not front-side; card-stack clearance is lost")
        if row.get("distance", 999) > 19.0:
            errors.append(f"C{number} is not local to U{number} VCC ({row.get('distance'):.2f} mm)")

    leds = data.get("leds", [])
    if [row.get("bit") for row in leds] != list(range(8)):
        errors.append("POST LED set/order differs from bits 0..7")
    elif (not all(row.get("side") == "F.Cu" for row in leds)
          or not all(close(row["y"], leds[0]["y"]) for row in leds)
          or not all(7.9 <= b["x"] - a["x"] <= 8.1 for a, b in zip(leds, leds[1:]))):
        errors.append("POST LEDs are not an accessible ordered front-side row")

    controls = data.get("controls", {})
    expected_nets = {
        "J_PIT_TP": {"GND", "PIT_BAUD", "PIT_CLK0", "PIT_OUT2_TP", "PIT_SOUND"},
        "JP_BAUD": {"BAUD_19200", "BAUD_DIRECT", "BAUD_9600"},
        "JP_CLK_SRC": {"BAUD_DIRECT", "PIT_BAUD", "BAUDCLK"},
        "J_SOUND": {"SOUND_LOW", "VCC5"},
    }
    for ref, nets in expected_nets.items():
        row = controls.get(ref, {})
        if row.get("side") != "F.Cu" or set(row.get("nets", [])) != nets:
            errors.append(f"{ref} is not the accessible front-side frozen interface")
    for ref in ("J_PIT_TP", "J_IOSEL", "JP_BAUD", "JP_CLK_SRC"):
        box = controls.get(ref, {}).get("bbox", [0, 0, 0, 0])
        if box[0] < 65.0 or box[1] < 70.0 or box[2] > 99.5 or box[3] > 90.5:
            errors.append(f"{ref} escaped the unobstructed lower-right service area")

    bus = data.get("bus", {})
    base, ext = bus.get("J_BUS", {}), bus.get("J_EXT", {})
    if base.get("side") != "F.Cu" or ext.get("side") != "B.Cu":
        errors.append("base/extension bus headers are not on opposite faces")
    if not close(base.get("angle", 999) % 360, 270) or not close(ext.get("angle", 999) % 360, 270):
        errors.append("bus header orientation differs")
    if base and (not close(base["pin1"][1], 96.0) or not close(base["last"][1], 96.0)):
        errors.append("J_BUS row is not at the frozen edge offset")
    if ext and (not close(ext["pin1"][1], 91.0) or not close(ext["last"][1], 91.0)):
        errors.append("J_EXT row is not at the frozen edge offset")

    tracks = data.get("tracks", [])
    if len(tracks) < 500:
        errors.append("routed I/O copper is absent or implausibly incomplete")
    if any(t.get("width", 0) < 0.199 for t in tracks):
        errors.append("I/O signal route below the frozen 0.20-mm floor")
    if any(t.get("layer") not in {"F.Cu", "B.Cu"} for t in tracks):
        errors.append("signal track escaped the two-layer stack")
    for via in data.get("vias", []):
        if via.get("diameter", 0) < 0.599 or via.get("drill", 0) < 0.299:
            errors.append("via below the frozen 0.60/0.30-mm geometry")
            break
    return errors


def main() -> int:
    if not PCB.exists():
        print(f"REVB-IO-PCB: FAIL missing {PCB}", file=sys.stderr)
        return 1
    data = inspect(pcbnew.LoadBoard(str(PCB)))
    errors = verify(data)
    if "--self-test" in sys.argv:
        mutations = []
        wrong_stack = copy.deepcopy(data); wrong_stack["copper_layers"] = 4
        mutations.append(("layer mutation", wrong_stack))
        rear_cap = copy.deepcopy(data); rear_cap["bypass"][8]["side"] = "B.Cu"
        mutations.append(("rear-cap mutation", rear_cap))
        remote_cap = copy.deepcopy(data); remote_cap["bypass"][2]["distance"] = 20.0
        mutations.append(("remote-cap mutation", remote_cap))
        led_swap = copy.deepcopy(data); led_swap["leds"][6]["x"], led_swap["leds"][7]["x"] = led_swap["leds"][7]["x"], led_swap["leds"][6]["x"]
        mutations.append(("LED-order mutation", led_swap))
        lost_tp = copy.deepcopy(data); lost_tp["controls"]["J_PIT_TP"]["nets"].remove("PIT_SOUND")
        mutations.append(("test-point mutation", lost_tp))
        thin = copy.deepcopy(data); thin["tracks"][0]["width"] = 0.15
        mutations.append(("route-width mutation", thin))
        for label, mutation in mutations:
            if not verify(mutation):
                errors.append(f"{label} escaped")
    if errors:
        for error in errors:
            print(f"REVB-IO-PCB: FAIL {error}", file=sys.stderr)
        return 1
    suffix = " + six negative controls" if "--self-test" in sys.argv else ""
    print("REVB-IO-PCB: PASS 2L routed geometry, nine front/local bypasses, "
          "ordered POST row, accessible PIT/sound/jumpers and exact bus presentation" + suffix)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
