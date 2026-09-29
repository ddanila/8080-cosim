#!/usr/bin/python3
"""Guard bracket X6 and its two surface cable joints."""
from __future__ import annotations

import json
from pathlib import Path

import pcbnew


ROOT = Path(__file__).resolve().parents[1]
BOARD = ROOT / "kicad/juku.kicad_pcb"
SPEC = ROOT / "kicad/juku.board.json"
EVIDENCE = ROOT / "ref/photos/juku-pcb-2/x6-cable-registration.json"
EXPECTED = {
    "AX603": ((280.233, 123.791), "X6_A3_BOUNDARY", ("X6", "1"), "A:3"),
    "AX604": ((285.606, 122.617), "GND", ("X6", "2"), "A:4"),
}


def mm(value: int) -> float:
    return pcbnew.ToMM(value)


def main() -> int:
    board = pcbnew.LoadBoard(str(BOARD))
    spec = json.loads(SPEC.read_text(encoding="utf-8"))
    evidence = json.loads(EVIDENCE.read_text(encoding="utf-8"))
    failures: list[str] = []
    if board.FindFootprintByReference("X6") is not None:
        failures.append("off-board X6 still has a PCB footprint")
    if board.FindFootprintByReference("X7") is not None or any(chip["ref"] == "X7" for chip in spec["chips"]):
        failures.append("unsupported physical X7 connector returned")
    if next(chip for chip in spec["chips"] if chip["ref"] == "X6")["type"] != "DISPLAY_CONN":
        failures.append("X6 lost its documented display-connector role")

    for refdes, (expected_xy, net, remote, point) in EXPECTED.items():
        footprint = board.FindFootprintByReference(refdes)
        pad = footprint.FindPadByNumber("1") if footprint is not None else None
        if pad is None:
            failures.append(f"{refdes}.1 landing is missing")
            continue
        position = pad.GetPosition()
        actual = (mm(position.x), mm(position.y))
        if any(abs(got - want) > 0.002 for got, want in zip(actual, expected_xy)):
            failures.append(f"{refdes}.1 position {actual} != {expected_xy}")
        if pad.GetNetname() != net:
            failures.append(f"{refdes}.1 net {pad.GetNetname()!r} != {net!r}")
        if pad.GetAttribute() != pcbnew.PAD_ATTRIB_SMD or pad.GetDrillSize().x != 0:
            failures.append(f"{refdes}.1 is not the photographed undrilled surface joint")
        nodes = {tuple(node) for node in spec["nets"][net]["nodes"]}
        required = {(refdes, "1"), remote}
        if not required <= nodes:
            failures.append(f"{net} lacks cable nodes {sorted(required - nodes)}")
        mapping = evidence.get("logical_mapping", {}).get(point, {})
        expected_evidence_net = None if point == "A:3" else net
        if mapping.get("footprint") != f"{refdes}.1" or mapping.get("net") != expected_evidence_net:
            failures.append(f"{point} evidence mapping drifted")

    clamp = {tuple(node) for node in spec["nets"]["SOUND_CLAMP"]["nodes"]}
    if {( "AX603", "1"), ("X6", "1")} & clamp:
        failures.append("rejected A:3/X6.1 SOUND_CLAMP join returned")

    if failures:
        for failure in failures:
            print("FAIL:", failure)
        return 1
    print("X6 LANDINGS: PASS — bracket X6 A:3 isolated pending continuity; A:4 ground")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
