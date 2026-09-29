#!/usr/bin/python3
"""Audit physical right-notch PPI pins against the current left-notch copper."""

import json
from pathlib import Path

import pcbnew


ROOT = Path(__file__).resolve().parents[1]
BOARD = ROOT / "kicad/juku_routed.kicad_pcb"
OUTPUT = ROOT / "docs/ppi-physical-pin-mapping.json"
VARIANTS = (
    ROOT / "kicad/juku.kicad_pcb",
    BOARD,
    ROOT / "kicad/juku_routed_candidate.kicad_pcb",
)


def mm(point):
    return (point.x / 1e6, point.y / 1e6)


def audit(footprint):
    pads = {int(p.GetNumber()): p for p in footprint.Pads() if p.GetNumber().isdigit()}
    if set(pads) != set(range(1, 41)):
        raise SystemExit(f"{footprint.GetReference()}: expected DIP-40 pad numbers")
    p1 = mm(pads[1].GetPosition())
    p21 = mm(pads[21].GetPosition())
    center = ((p1[0] + p21[0]) / 2, (p1[1] + p21[1]) / 2)
    rows = []
    for physical_pin in range(1, 41):
        routed_pad = (physical_pin + 19) % 40 + 1
        nominal = pads[physical_pin]
        at_hole = pads[routed_pad]
        nominal_xy = mm(nominal.GetPosition())
        at_hole_xy = mm(at_hole.GetPosition())
        rotated_xy = (2 * center[0] - nominal_xy[0], 2 * center[1] - nominal_xy[1])
        error = max(abs(rotated_xy[i] - at_hole_xy[i]) for i in (0, 1))
        if error > 0.001:
            raise SystemExit(f"{footprint.GetReference()}.{physical_pin}: 180-degree hole mapping failed")
        rows.append({
            "physical_pin": physical_pin,
            "routed_pad_at_same_hole": routed_pad,
            "intended_net_by_pin_number": nominal.GetNetname(),
            "routed_net_at_same_hole": at_hole.GetNetname(),
            "net_matches": nominal.GetNetname() == at_hole.GetNetname(),
        })
    return {
        "refdes": footprint.GetReference(),
        "routed_array_center_mm": [round(v, 3) for v in center],
        "matching_pin_nets": sum(r["net_matches"] for r in rows),
        "different_pin_nets": sum(not r["net_matches"] for r in rows),
        "key_pins": [r for r in rows if r["physical_pin"] in (7, 26)],
        "pin_mapping": rows,
    }


def main():
    board = pcbnew.LoadBoard(str(BOARD))
    footprints = {f.GetReference(): f for f in board.GetFootprints()}
    audits = [audit(footprints[ref]) for ref in ("D26", "D27")]
    orientations = {}
    for path in VARIANTS:
        variant = pcbnew.LoadBoard(str(path))
        parts = {f.GetReference(): f for f in variant.GetFootprints()}
        orientations[str(path.relative_to(ROOT))] = {
            ref: {
                "degrees": parts[ref].GetOrientationDegrees(),
                "right_notch_expected": parts[ref].GetOrientationDegrees() % 360 == 270,
            }
            for ref in ("D26", "D27")
        }
    report = {
        "schema_version": 1,
        "board": str(BOARD.relative_to(ROOT)),
        "status": "FABRICATION HOLD",
        "evidence": "Factory .009 assembly and owner photos show both PPIs right-notched; routed DIP-40s are left-notched.",
        "variant_orientation": orientations,
        "audits": audits,
    }
    OUTPUT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print("PPI physical pin mapping HOLD: " + ", ".join(
        f"{a['refdes']} {a['different_pin_nets']}/40 mismatched" for a in audits))


if __name__ == "__main__":
    main()
