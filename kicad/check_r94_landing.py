#!/usr/bin/python3
"""Guard the photo-proved R94 load and photo-exhausted far endpoint."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pcbnew
from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
BOARD = ROOT / "kicad/juku.kicad_pcb"
EVIDENCE = ROOT / "ref/photos/juku-pcb-2/r94-photo-exhaustion.json"


def mm(value: int) -> float:
    return pcbnew.ToMM(value)


def main() -> int:
    board = pcbnew.LoadBoard(str(BOARD))
    failures: list[str] = []
    r94 = board.FindFootprintByReference("R94")
    d98 = board.FindFootprintByReference("D98")
    if r94 is None:
        failures.append("R94 footprint is missing")
    else:
        position = r94.GetPosition()
        actual = (mm(position.x), mm(position.y), r94.GetOrientationDegrees())
        expected = (297.6, 51.32, -90.0)
        if any(abs(got - want) > 0.002 for got, want in zip(actual, expected)):
            failures.append(f"R94 placement {actual} != {expected}")
        if r94.GetValue() != "220":
            failures.append(f"R94 value {r94.GetValue()!r} != '220'")
        pad1 = r94.FindPadByNumber("1")
        pad2 = r94.FindPadByNumber("2")
        if pad1 is None or pad1.GetNetname() != "D98_Y1_R94":
            failures.append("R94.1 is not assigned to D98_Y1_R94")
        if pad2 is None or pad2.GetNetname() != "R94_P2_BOUNDARY":
            failures.append("R94.2 must remain on its explicit measurement boundary")
        if pad1 is not None:
            position1 = pad1.GetPosition()
            actual1 = (mm(position1.x), mm(position1.y))
            if any(abs(got - want) > 0.002 for got, want in zip(actual1, (297.6, 51.32))):
                failures.append(f"R94.1 position {actual1} != (297.6, 51.32)")
        if pad2 is not None:
            position2 = pad2.GetPosition()
            actual2 = (mm(position2.x), mm(position2.y))
            if any(abs(got - want) > 0.002 for got, want in zip(actual2, (297.6, 61.48))):
                failures.append(f"R94.2 position {actual2} != (297.6, 61.48)")

    d98_pad3 = d98.FindPadByNumber("3") if d98 is not None else None
    if d98_pad3 is None or d98_pad3.GetNetname() != "D98_Y1_R94":
        failures.append("D98.3 is not assigned to D98_Y1_R94")

    evidence = json.loads(EVIDENCE.read_text(encoding="utf-8"))
    if (evidence.get("schema_version") != 1 or evidence.get("refdes") != "R94" or
            evidence.get("endpoint") != "2" or evidence.get("board_mm") != [297.6, 61.48] or
            evidence.get("status") != "photo-exhausted / continuity required"):
        failures.append("R94.2 photo-exhaustion evidence header mismatch")
    observations = [*evidence.get("component_observations", []),
                    *evidence.get("solder_observations", [])]
    if len(evidence.get("component_observations", [])) != 2 or len(evidence.get("solder_observations", [])) != 2:
        failures.append("R94.2 needs two component and two solder observations")
    for observation in observations:
        image_path = ROOT / observation.get("source", "")
        if (not image_path.is_file() or
                hashlib.sha256(image_path.read_bytes()).hexdigest() != observation.get("sha256")):
            failures.append(f"R94.2 evidence hash mismatch: {image_path}")
            continue
        with Image.open(image_path) as image:
            width, height = image.size
        if observation.get("dimensions_px") != [width, height]:
            failures.append(f"R94.2 evidence dimensions mismatch: {image_path}")
        bbox = observation.get("bbox_px", [])
        point = observation.get("review_point_px", [])
        if (len(bbox) != 4 or len(point) != 2 or
                not (0 <= bbox[0] <= point[0] <= bbox[2] <= width and
                     0 <= bbox[1] <= point[1] <= bbox[3] <= height)):
            failures.append(f"R94.2 invalid evidence region: {image_path}")
    if evidence.get("unresolved") != ["R94.2 remote destination"]:
        failures.append("R94.2 remote boundary is not guarded")

    if failures:
        for failure in failures:
            print("FAIL:", failure)
        return 1
    print("R94 LANDING: PASS — 220 ohm from D98.3; far terminal is photo-exhausted and continuity-gated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
