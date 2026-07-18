#!/usr/bin/env python3
"""Guard and report resistor values read directly from the native sheets."""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "ref/schematics/native-resistor-value-registration.json"
BOARD_JSON = ROOT / "kicad/juku.board.json"
PCB = ROOT / "kicad/juku.kicad_pcb"
REPORT = ROOT / "docs/native-resistor-values.md"


def fail(message: str) -> None:
    raise SystemExit(f"NATIVE RESISTOR VALUES: FAIL: {message}")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def footprint_blocks(text: str) -> list[str]:
    """Extract top-level footprint forms while ignoring parentheses in strings."""
    blocks: list[str] = []
    offset = 0
    marker = "\n\t(footprint "
    while (found := text.find(marker, offset)) >= 0:
        start = found + 2
        depth = 0
        quoted = False
        escaped = False
        for index in range(start, len(text)):
            char = text[index]
            if quoted:
                if escaped:
                    escaped = False
                elif char == "\\":
                    escaped = True
                elif char == '"':
                    quoted = False
                continue
            if char == '"':
                quoted = True
            elif char == "(":
                depth += 1
            elif char == ")":
                depth -= 1
                if depth == 0:
                    blocks.append(text[start : index + 1])
                    offset = index + 1
                    break
        else:
            fail("unterminated footprint form in source PCB")
    return blocks


def pcb_values(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for block in footprint_blocks(path.read_text(encoding="utf-8")):
        reference = re.search(r'\(property "Reference" "([^"]+)"', block)
        value = re.search(r'\(property "Value" "([^"]*)"', block)
        if reference and value:
            values[reference.group(1)] = value.group(1)
    return values


evidence = json.loads(EVIDENCE.read_text(encoding="utf-8"))
for source in evidence["sources"]:
    path = ROOT / source["path"]
    if not path.is_file() or sha256(path) != source["sha256"]:
        fail(f"source hash drifted: {source['path']}")

expected: dict[str, str] = {}
source_sheet: dict[str, int] = {}
group_name: dict[str, str] = {}
for group in evidence["groups"]:
    for refdes, value in group["refs"].items():
        if refdes in expected:
            fail(f"duplicate evidence row for {refdes}")
        expected[refdes] = value
        source_sheet[refdes] = group["source_sheet"]
        group_name[refdes] = group["name"]
if len(expected) != 24:
    fail(f"expected 24 promoted values, found {len(expected)}")

board = json.loads(BOARD_JSON.read_text(encoding="utf-8"))
chips = {chip["ref"]: chip for chip in board["chips"]}
for refdes, value in expected.items():
    chip = chips.get(refdes)
    if chip is None or chip.get("type") != "R_AXIAL":
        fail(f"{refdes} is missing or is not R_AXIAL in board JSON")
    if chip.get("value") != value:
        fail(f"{refdes} board value is {chip.get('value')!r}, expected {value!r}")

held = {item["ref"] for item in evidence["held"]}
missing_values = {
    chip["ref"]
    for chip in board["chips"]
    if chip.get("type") == "R_AXIAL" and not chip.get("value")
}
if missing_values != held:
    fail(
        "unvalued resistor set drifted: "
        f"found {sorted(missing_values)}, expected {sorted(held)}"
    )

physical_values = pcb_values(PCB)
for refdes, value in expected.items():
    if physical_values.get(refdes) != value:
        fail(
            f"{refdes} source-PCB value is {physical_values.get(refdes)!r}, "
            f"expected {value!r}"
        )

lines = [
    "# Native schematic resistor values",
    "",
    "Status: **24 VALUES SOURCE-CLOSED / 0 TARGET HOLDS**",
    "",
    "The native electrical sheets and target-board photos close 24 values that",
    "were formerly blank in the machine-readable board model. This report checksum-guards those sources,",
    "checks the board JSON and generated source PCB agree, and keeps ambiguous or",
    "revision-sensitive values out of the promoted set.",
    "",
    "## Command",
    "",
    "```sh",
    "python3 scripts/report_native_resistor_values.py",
    "```",
    "",
    "## Closed values",
    "",
    "| Ref | Value | Sheet | Circuit group |",
    "| --- | ---: | ---: | --- |",
]
for refdes in sorted(expected, key=lambda item: int(item[1:])):
    lines.append(
        f"| `{refdes}` | `{expected[refdes]}` | {source_sheet[refdes]} | "
        f"{group_name[refdes]} |"
    )

lines.extend(["", "## Deliberate holds", ""])
if evidence["held"]:
    lines.extend(["| Ref | Why it remains unvalued |", "| --- | --- |"])
    for item in evidence["held"]:
        lines.append(f"| `{item['ref']}` | {item['reason']} |")
else:
    lines.append("None. Every modeled axial resistor now has literal source evidence.")

lines.extend(
    [
        "",
        "## Evidence boundary",
        "",
        "- Sheet 1 closes R11-R14 and R17 directly; these are not values inferred",
        "  from open-collector behavior.",
        "- Sheet 2 closes the R40-R45 common 15 kΩ group, correcting stale 13 kΩ",
        "  prose, plus the D56, FRAME_INT, video-summing, and beeper networks.",
        "- The factory-identified target R67 body reads `4K7` independently in July",
        "  and May views. This supersedes the `.006` sheet's 2 kΩ R67 value without",
        "  promoting the target part's still-unresolved pin-2 destination.",
        "- Connectivity is unchanged. This milestone only replaces absent value",
        "  metadata with literal scan/photo evidence.",
        "- R48's `8,2 Ом` label is independently corroborated by the traced beeper",
        "  boundary. No modeled axial resistor remains unvalued.",
        "",
    ]
)

REPORT.write_text("\n".join(lines), encoding="utf-8")
print(
    "NATIVE RESISTOR VALUES: PASS — 24 literal source values agree across "
    "evidence, board JSON, and source PCB; no axial resistor remains held"
)
