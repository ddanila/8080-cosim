#!/usr/bin/env python3
"""Guard the exact sheet-3 D93 DRQ/INTRQ conditioner."""
from __future__ import annotations

import hashlib
import json
import re
import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = ROOT / "kicad/juku.board.json"
HDL = ROOT / "hdl/juku_top.v"
EVIDENCE = ROOT / "ref/photos/juku-pcb-2/d96-irq-photo-exhaustion.json"


def jpeg_dimensions(path: Path) -> list[int]:
    """Read JPEG SOF dimensions without optional image-library dependencies."""
    data = path.read_bytes()
    offset = 2
    while offset + 9 < len(data):
        if data[offset] != 0xFF:
            offset += 1
            continue
        marker = data[offset + 1]
        offset += 2
        if marker in {0xD8, 0xD9} or 0xD0 <= marker <= 0xD7:
            continue
        length = struct.unpack(">H", data[offset:offset + 2])[0]
        if marker in {0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7,
                    0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF}:
            height, width = struct.unpack(">HH", data[offset + 3:offset + 7])
            return [width, height]
        offset += length
    raise SystemExit(f"cannot read JPEG dimensions: {path}")


def photo_sha256(path: Path) -> tuple[str, bool]:
    """Return (sha256, is_lfs_pointer), tolerating an unmaterialized LFS object.

    The generic CI job does not fetch Git LFS, so ``ref/photos/**/*.jpg`` may be a
    pointer whose ``oid sha256`` already equals the object hash; read it directly
    there. Mirrors the sibling FDC photo guards (e.g. check_fdc_unused_pins.py)."""
    payload = path.read_bytes()
    if payload.startswith(b"version https://git-lfs.github.com/spec/v1\n"):
        match = re.search(r"^oid sha256:([0-9a-f]{64})$", payload.decode("ascii"),
                        re.MULTILINE)
        return (match.group(1) if match else "invalid-lfs-pointer"), True
    return hashlib.sha256(payload).hexdigest(), False


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
