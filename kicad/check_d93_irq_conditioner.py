#!/usr/bin/env python3
"""Guard the exact sheet-3 D93 DRQ/INTRQ conditioner."""
from __future__ import annotations

import json
from pathlib import Path

from photo_evidence import jpeg_dimensions, photo_sha256

ROOT = Path(__file__).resolve().parents[1]
SPEC = ROOT / "kicad/juku.board.json"
HDL = ROOT / "hdl/juku_top.v"
EVIDENCE = ROOT / "ref/photos/juku-pcb-2/d96-irq-photo-exhaustion.json"

def main() -> None:
    spec = json.loads(SPEC.read_text(encoding="utf-8"))
    nets = spec["nets"]
    expected = {
        "FDC_INTRQ": [["D93", "39"], ["D28", "13"], ["R93", "1"]],
        "FDC_DRQ": [["D93", "38"], ["D28", "11"], ["R94", "1"]],
        "FDC_IRQ_CONDITIONED_N": [
            ["D28", "10"], ["D28", "12"], ["D96", "10"],
            ["D96", "12"], ["R95", "1"],
        ],
        "D96_IRQ_CLOCK_SHEET1_BOUNDARY": [["D96", "11"]],
        "D96_IRQ_Q_SHEET1_BOUNDARY": [["D96", "9"]],
    }
    for name, nodes in expected.items():
        if nets.get(name, {}).get("nodes") != nodes:
            raise SystemExit(f"{name} changed: {nets.get(name, {}).get('nodes')}")
    for retired in ("D10_IR0_FDC_BOUNDARY", "D10_IR1_FDC_BOUNDARY"):
        if retired in nets:
            raise SystemExit(f"retired direct-FDC PIC boundary returned: {retired}")
    for node in (["R93", "2"], ["R94", "2"], ["R95", "2"]):
        if node not in nets["P5V"]["nodes"]:
            raise SystemExit(f"conditioner pull-up missing: {node}")
    chips = {chip["ref"]: chip for chip in spec["chips"]}
    for ref, value in {"R93": "10к", "R94": "10к", "R95": "2к"}.items():
        if chips.get(ref, {}).get("value") != value:
            raise SystemExit(f"{ref} value missing: {chips.get(ref, {}).get('value')}")
    forbidden_nc = {("D28", pin) for pin in ("10", "11", "12", "13")}
    forbidden_nc |= {("D96", pin) for pin in ("9", "10", "11", "12")}
    returned = forbidden_nc & {tuple(node) for node in spec["no_connects"]}
    if returned:
        raise SystemExit(f"source-used pins marked NC: {sorted(returned)}")
    if ["D96", "13"] not in spec["no_connects"]:
        raise SystemExit("sheet-omitted D96.13 is not retained as NC")
    evidence = json.loads(EVIDENCE.read_text(encoding="utf-8"))
    if (evidence.get("schema_version") != 1 or evidence.get("refdes") != "D96" or
            evidence.get("endpoints") != ["9", "11"] or
            evidence.get("status") != "photo-exhausted / continuity required" or
            evidence.get("unresolved") != [
                "D96.9 Q2 remote destination", "D96.11 CLK2 remote source"]):
        raise SystemExit("D96.9/.11 photo-exhaustion evidence header mismatch")
    for key in ("drawing_observation", "component_observation", "solder_observation"):
        observation = evidence.get(key, {})
        image_path = ROOT / observation.get("source", "")
        if not image_path.is_file():
            raise SystemExit(f"D96.9/.11 evidence hash mismatch: {image_path}")
        digest, is_pointer = photo_sha256(image_path)
        if digest != observation.get("sha256"):
            raise SystemExit(f"D96.9/.11 evidence hash mismatch: {image_path}")
        # SOF dimensions can only be parsed from a materialized JPEG, not an LFS
        # pointer; the pointer's oid already proves byte identity above.
        if not is_pointer:
            dimensions = jpeg_dimensions(image_path)
            if observation.get("dimensions_px") != dimensions:
                raise SystemExit(f"D96.9/.11 evidence dimensions mismatch: {image_path}")
    for key in ("component_observation", "solder_observation"):
        observation = evidence[key]
        if set(observation.get("endpoint_px", {})) != {"9", "11"}:
            raise SystemExit(f"D96.9/.11 endpoint registration missing: {key}")
        left, top, right, bottom = observation.get("bbox_px", [])
        for point in observation["endpoint_px"].values():
            if not (left <= point[0] <= right and top <= point[1] <= bottom):
                raise SystemExit(f"D96.9/.11 endpoint outside evidence region: {key}")
    hdl = HDL.read_text(encoding="utf-8")
    for marker in (
        ".d2(d96_irq_conditioned_boundary)",
        ".clk2(d96_irq_clock_boundary)",
        ".pre2_n(d96_irq_conditioned_boundary)",
        ".q2(d96_irq_q_sheet1_boundary)",
    ):
        if marker not in hdl:
            raise SystemExit(f"structural D96 marker missing: {marker}")
    print("D93 IRQ CONDITIONER: PASS — local circuit restored; D96.9/.11 photo-exhausted and continuity-gated")


if __name__ == "__main__":
    main()
