#!/usr/bin/env python3
"""Guard native semiconductor markings, physical packages, and pin/net maps."""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "ref/schematics/native-semiconductor-registration.json"
BOARD_JSON = ROOT / "kicad/juku.board.json"
PCB = ROOT / "kicad/juku.kicad_pcb"
REPORT = ROOT / "docs/native-semiconductors.md"


def fail(message: str) -> None:
    raise SystemExit(f"NATIVE SEMICONDUCTORS: FAIL: {message}")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def forms(text: str, marker: str) -> list[str]:
    result = []
    offset = 0
    while (found := text.find(marker, offset)) >= 0:
        start = found + marker.index("(")
        depth = 0
        quoted = escaped = False
        for index in range(start, len(text)):
            char = text[index]
            if quoted:
                if escaped:
                    escaped = False
                elif char == "\\":
                    escaped = True
                elif char == '"':
                    quoted = False
            elif char == '"':
                quoted = True
            elif char == "(":
                depth += 1
            elif char == ")":
                depth -= 1
                if depth == 0:
                    result.append(text[start:index + 1])
                    offset = index + 1
                    break
        else:
            fail("unterminated source-PCB form")
    return result


def footprint_map(path: Path) -> dict[str, dict]:
    result = {}
    for block in forms(path.read_text(encoding="utf-8"), "\n\t(footprint "):
        ref = re.search(r'\(property "Reference" "([^"]+)"', block)
        value = re.search(r'\(property "Value" "([^"]*)"', block)
        name = re.match(r'\(footprint "([^"]+)"', block)
        if not (ref and value and name):
            continue
        pads = {}
        for pad in forms("\n\t" + block, "\n\t\t(pad "):
            number = re.match(r'\(pad "([^"]+)"', pad)
            net = re.search(r'\(net \d+ "([^"]+)"\)', pad)
            if number:
                pads[number.group(1)] = net.group(1) if net else ""
        result[ref.group(1)] = {"value": value.group(1), "footprint": name.group(1), "pads": pads}
    return result


evidence = json.loads(EVIDENCE.read_text(encoding="utf-8"))
source = ROOT / evidence["source"]["path"]
if not source.is_file() or sha256(source) != evidence["source"]["sha256"]:
    fail("native sheet-2 source hash drifted")
reset_source = ROOT / evidence["reset_source"]["path"]
if not reset_source.is_file() or sha256(reset_source) != evidence["reset_source"]["sha256"]:
    fail("native sheet-1 reset source hash drifted")
photo_refs = {}
for item in evidence["target_body_sources"]:
    image_path = ROOT / item["path"]
    if not image_path.is_file() or sha256(image_path) != item["sha256"]:
        fail(f"target body source drifted: {item['path']}")
    if item.get("dimensions_px") != [4080, 3072]:
        fail(f"target body dimensions drifted: {item['path']}")
    x0, y0, x1, y1 = item.get("bbox_px", [0, 0, 0, 0])
    if not (0 <= x0 < x1 <= 4080 and 0 <= y0 < y1 <= 3072):
        fail(f"invalid target body box: {item['path']}")
    photo_refs.setdefault(item["ref"], []).append(item)
if set(photo_refs) != {"VD1", "VD4"} or any(len(items) != 2 for items in photo_refs.values()):
    fail("VD1/VD4 each require independent May and July target-body sources")
expected_markings = {
    "VD1": {"КД521В", "designation face C1-obscured"},
    "VD4": {"КД521В", "В suffix"},
}
for ref, items in photo_refs.items():
    if {item.get("visible_marking") for item in items} != expected_markings[ref]:
        fail(f"{ref} direct/corroborating target marking evidence drifted")
physical_source = ROOT / evidence["physical_source"]["path"]
physical_evidence = json.loads(physical_source.read_text(encoding="utf-8"))
if (physical_evidence.get("schema_version") != 2 or
        physical_evidence.get("vt2_component_registration", {}).get("visible_marking") != "Б / 8901"):
    fail("VT2 owner-photo package evidence drifted")

board = json.loads(BOARD_JSON.read_text(encoding="utf-8"))
chips = {chip["ref"]: chip for chip in board["chips"]}
closed = {item["ref"]: item for item in evidence["closed"]}
if set(closed) != {"VD1", "VT1", "VT2", "VD3", "VD4", "VD5"}:
    fail(f"closed set drifted: {sorted(closed)}")
for ref, expected in closed.items():
    actual = chips.get(ref, {})
    for field in ("type", "value", "pins"):
        if actual.get(field) != expected[field]:
            fail(f"{ref} {field} is {actual.get(field)!r}, expected {expected[field]!r}")
if evidence.get("held"):
    fail(f"unexpected held native semiconductors: {evidence['held']}")

expected_nets = {
    "VD1": {"1": "P5V", "2": "RES_RC"},
    "VT1": {"1": "SND_OUT", "2": "P5V", "3": "SND_BASE"},
    "VT2": {"1": "VIDEO_OUT", "2": "P5V", "3": "VT2_BASE"},
    "VD3": {"1": "GND", "2": "SOUND_CLAMP"},
    "VD4": {"1": "SND_CLAMP", "2": "SND_BASE"},
    "VD5": {"1": "GND", "2": "M5V_DERIVED"},
}
nodes = {}
for name, net in board["nets"].items():
    for ref, pin in net.get("nodes", []):
        if ref in expected_nets:
            nodes.setdefault(ref, {})[pin] = name
if nodes != expected_nets:
    fail(f"board pin/net map drifted: {nodes}")

physical = footprint_map(PCB)
for ref, expected in closed.items():
    actual = physical.get(ref, {})
    if actual.get("value") != expected["value"]:
        fail(f"{ref} source-PCB value drifted: {actual.get('value')!r}")
    if not actual.get("footprint", "").endswith(expected["footprint"]):
        fail(f"{ref} source-PCB footprint drifted: {actual.get('footprint')!r}")
    if actual.get("pads") != expected_nets[ref]:
        fail(f"{ref} source-PCB pad/net map drifted: {actual.get('pads')!r}")

lines = [
    "# Native semiconductor designations and pinouts", "",
    "Status: **6 DESIGNATIONS + 2 TRANSISTOR PINOUTS SOURCE-CLOSED**", "",
    "The native sheets and registered target bodies name the retained reset, power,",
    "video, and beeper semiconductors. This guard",
    "keeps those markings, the physical E-C-B transistor lead order, the KT-27/KT-13",
    "package choices, and every generated PCB pad/net assignment synchronized.", "",
    "## Command", "", "```sh", "python3 scripts/report_native_semiconductors.py", "```", "",
    "## Closed devices", "", "| Ref | Device | Package | Physical pins | PCB nets by pin |",
    "| --- | --- | --- | --- | --- |",
]
for ref in ("VD1", "VT1", "VT2", "VD3", "VD4", "VD5"):
    item = closed[ref]
    pins = ", ".join(f"{pin}={name}" for pin, name in item["pins"].items())
    nets = ", ".join(f"{pin}={name}" for pin, name in expected_nets[ref].items())
    lines.append(f"| `{ref}` | `{item['value']}` | `{item['footprint']}` | {pins} | {nets} |")
lines += [
    "", "## Evidence boundary", "",
    "- VT1 uses the stock horizontal TO-126 footprint because the КТ972 datasheet",
    "  identifies the КТ-27 case and the factory mounting detail lays that body flat.",
    "- VT2 retains the stock КТ-13 outline but replaces its generic drilled row with",
    "  the three exact owner-photo component-side lap joints. The yellow body is visibly",
    "  marked `Б / 8901`; it was formerly misidentified as C94.",
    "- VD1 was absent from the former board model. Sheet 1 fixes its cathode on +5 V",
    "  and anode on the reset-RC junction; the May target view directly reads `КД521В`,",
    "  while registered July coverage independently proves the populated body at `(12.5,216.1)` mm.",
    "- VD4 is independently target-photo closed as `КД521В`; the older sheet remains",
    "  the polarity/connectivity source because it draws the clamp but omits a value.",
    "- VD5 retains the sheet-1 `КС147` designation and derived -5 V clamp polarity.", "",
]
REPORT.write_text("\n".join(lines), encoding="utf-8")
print("NATIVE SEMICONDUCTORS: PASS — markings, packages, E-C-B pinouts, and PCB nets agree")
