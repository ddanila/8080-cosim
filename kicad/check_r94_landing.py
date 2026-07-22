#!/usr/bin/python3
"""Guard corrected R94 and the separately preserved unidentified 220-ohm body."""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path

import pcbnew
from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
BOARDS = (ROOT / "kicad/juku.kicad_pcb", ROOT / "kicad/juku_routed.kicad_pcb")
EVIDENCE = ROOT / "ref/photos/juku-pcb-2/r94-photo-exhaustion.json"


def midpoint(footprint: pcbnew.FOOTPRINT) -> tuple[float, float]:
    pads = list(footprint.Pads())
    return (
        sum(pcbnew.ToMM(pad.GetPosition().x) for pad in pads) / len(pads),
        sum(pcbnew.ToMM(pad.GetPosition().y) for pad in pads) / len(pads),
    )


def pad_nets(footprint: pcbnew.FOOTPRINT) -> dict[str, str]:
    return {pad.GetNumber(): pad.GetNetname() for pad in footprint.Pads()}


def main() -> int:
    failures: list[str] = []
    for board_path in BOARDS:
        board = pcbnew.LoadBoard(str(board_path))
        r94 = board.FindFootprintByReference("R94")
        unknown = board.FindFootprintByReference("RUNK1")
        d98 = board.FindFootprintByReference("D98")
        label = board_path.name
        if r94 is None:
            failures.append(f"{label}: corrected R94 footprint is missing")
        else:
            actual = midpoint(r94)
            if math.dist(actual, (271.987, 54.141)) > 0.002:
                failures.append(f"{label}: R94 midpoint {actual} != (271.987, 54.141)")
            if r94.GetValue() != "10к":
                failures.append(f"{label}: R94 value {r94.GetValue()!r} != '10к'")
            if pad_nets(r94) != {"1": "FDC_DRQ", "2": "P5V"}:
                failures.append(f"{label}: corrected R94 endpoints changed: {pad_nets(r94)}")
        if unknown is None:
            failures.append(f"{label}: unidentified 220-ohm body placeholder is missing")
        else:
            actual = midpoint(unknown)
            if math.dist(actual, (297.6, 56.4)) > 0.002:
                failures.append(f"{label}: RUNK1 midpoint {actual} != (297.6, 56.4)")
            if unknown.GetValue() != "220":
                failures.append(f"{label}: RUNK1 value {unknown.GetValue()!r} != '220'")
            expected = {"1": "RUNK1_P1_BOUNDARY", "2": "RUNK1_P2_BOUNDARY"}
            if pad_nets(unknown) != expected:
                failures.append(f"{label}: RUNK1 boundaries changed: {pad_nets(unknown)}")
        d98_pad3 = d98.FindPadByNumber("3") if d98 is not None else None
        if d98_pad3 is None or d98_pad3.GetNetname() != "D98_Y1_D28_READY":
            failures.append(f"{label}: D98.3 is not on the corrected READY path")

    evidence = json.loads(EVIDENCE.read_text(encoding="utf-8"))
    if (evidence.get("schema_version") != 1 or
            evidence.get("refdes") != "UNASSIGNED_220_NEAR_D98" or
            evidence.get("endpoint") != "formerly modeled as R94.2" or
            evidence.get("board_mm") != [297.6, 61.48] or
            evidence.get("status") != "superseded R94 identification / retained photo evidence"):
        failures.append("unidentified 220-ohm evidence header mismatch")
    observations = [*evidence.get("component_observations", []),
                    *evidence.get("solder_observations", [])]
    if len(evidence.get("component_observations", [])) != 2 or len(evidence.get("solder_observations", [])) != 2:
        failures.append("unidentified 220-ohm body needs two component and two solder observations")
    for observation in observations:
        image_path = ROOT / observation.get("source", "")
        if (not image_path.is_file() or
                hashlib.sha256(image_path.read_bytes()).hexdigest() != observation.get("sha256")):
            failures.append(f"unidentified-body evidence hash mismatch: {image_path}")
            continue
        with Image.open(image_path) as image:
            width, height = image.size
        if observation.get("dimensions_px") != [width, height]:
            failures.append(f"unidentified-body evidence dimensions mismatch: {image_path}")
        bbox = observation.get("bbox_px", [])
        point = observation.get("review_point_px", [])
        if (len(bbox) != 4 or len(point) != 2 or
                not (0 <= bbox[0] <= point[0] <= bbox[2] <= width and
                     0 <= bbox[1] <= point[1] <= bbox[3] <= height)):
            failures.append(f"unidentified-body invalid evidence region: {image_path}")
    expected_unresolved = ["reference identity and both endpoints of photographed 220-ohm body"]
    if evidence.get("unresolved") != expected_unresolved:
        failures.append("unidentified 220-ohm boundaries are not guarded")

    if failures:
        for failure in failures:
            print("FAIL:", failure)
        return 1
    print("R94 LANDING: PASS — 10k DRQ pull-up restored; separate 220-ohm body preserved with explicit boundaries")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
