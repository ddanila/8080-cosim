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

board = json.loads(BOARD_JSON.read_text(encoding="utf-8"))
chips = {chip["ref"]: chip for chip in board["chips"]}
closed = {item["ref"]: item for item in evidence["closed"]}
if set(closed) != {"VT1", "VT2", "VD3"}:
    fail(f"closed set drifted: {sorted(closed)}")
for ref, expected in closed.items():
    actual = chips.get(ref, {})
    for field in ("type", "value", "pins"):
        if actual.get(field) != expected[field]:
            fail(f"{ref} {field} is {actual.get(field)!r}, expected {expected[field]!r}")
if chips.get("VD4", {}).get("value"):
    fail("VD4 exact designation was promoted without source evidence")

expected_nets = {
    "VT1": {"1": "SND_OUT", "2": "P5V", "3": "SND_BASE"},
    "VT2": {"1": "VIDEO_OUT", "2": "P5V", "3": "VT2_BASE"},
    "VD3": {"1": "GND", "2": "SOUND_CLAMP"},
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
    "Status: **3 DESIGNATIONS + 2 TRANSISTOR PINOUTS SOURCE-CLOSED / VD4 HELD**", "",
    "The native sheet names the retained video and beeper semiconductors. This guard",
    "keeps those markings, the physical E-C-B transistor lead order, the KT-27/KT-13",
    "package choices, and every generated PCB pad/net assignment synchronized.", "",
    "## Command", "", "```sh", "python3 scripts/report_native_semiconductors.py", "```", "",
    "## Closed devices", "", "| Ref | Device | Package | Physical pins | PCB nets by pin |",
    "| --- | --- | --- | --- | --- |",
]
for ref in ("VT1", "VT2", "VD3"):
    item = closed[ref]
    pins = ", ".join(f"{pin}={name}" for pin, name in item["pins"].items())
    nets = ", ".join(f"{pin}={name}" for pin, name in expected_nets[ref].items())
    lines.append(f"| `{ref}` | `{item['value']}` | `{item['footprint']}` | {pins} | {nets} |")
lines += [
    "", "## Evidence boundary", "",
    "- VT1 uses the stock horizontal TO-126 footprint because the КТ972 datasheet",
    "  identifies the КТ-27 case and the factory mounting detail lays that body flat.",
    "- VT2 retains the stock 2.54 mm outer-span inline footprint as a pad-row stand-in",
    "  for the flat КТ-13 body; its exact photo placement remains a separate open task.",
    "- VD4 remains deliberately blank: neither the retained sheet nor current owner",
    "  imagery closes an exact designation.", "",
]
REPORT.write_text("\n".join(lines), encoding="utf-8")
print("NATIVE SEMICONDUCTORS: PASS — markings, packages, E-C-B pinouts, and PCB nets agree")
