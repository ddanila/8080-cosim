#!/usr/bin/env python3
"""Guard capacitor values read directly from retained native-sheet circuits."""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "ref/schematics/native-capacitor-value-registration.json"
BOARD_JSON = ROOT / "kicad/juku.board.json"
PCB = ROOT / "kicad/juku.kicad_pcb"
REPORT = ROOT / "docs/native-capacitor-values.md"


def fail(message: str) -> None:
    raise SystemExit(f"NATIVE CAPACITOR VALUES: FAIL: {message}")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def footprint_blocks(text: str) -> list[str]:
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
                    blocks.append(text[start:index + 1])
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

closed = {item["ref"]: item for item in evidence["closed"]}
if set(closed) != {"C7", "C8", "C99"}:
    fail(f"closed set drifted: {sorted(closed)}")

board = json.loads(BOARD_JSON.read_text(encoding="utf-8"))
chips = {chip["ref"]: chip for chip in board["chips"]}
for refdes, item in closed.items():
    chip = chips.get(refdes)
    if chip is None or chip.get("type") != "C_KM":
        fail(f"{refdes} is missing or is not C_KM in board JSON")
    if chip.get("value") != item["value"]:
        fail(f"{refdes} board value is {chip.get('value')!r}, expected {item['value']!r}")

held = {item["ref"] for item in evidence["held"]}
unvalued = {
    chip["ref"] for chip in board["chips"]
    if chip.get("type") == "C_KM" and not chip.get("value")
}
if unvalued != held:
    fail(f"unvalued C_KM set drifted: found {sorted(unvalued)}, expected {sorted(held)}")

physical_values = pcb_values(PCB)
for refdes, item in closed.items():
    if physical_values.get(refdes) != item["value"]:
        fail(
            f"{refdes} source-PCB value is {physical_values.get(refdes)!r}, "
            f"expected {item['value']!r}"
        )

lines = [
    "# Native schematic capacitor values",
    "",
    "Status: **3 VALUES SOURCE-CLOSED / 9 TARGET HOLDS**",
    "",
    "The retained native circuits print three capacitor values that were blank in",
    "the machine-readable board model. This report checksum-guards the source scans",
    "and requires the board JSON and generated source PCB to preserve those literals.",
    "",
    "## Command",
    "",
    "```sh",
    "python3 scripts/report_native_capacitor_values.py",
    "```",
    "",
    "## Closed values",
    "",
    "| Ref | Board literal | Normalized | Sheet | Circuit |",
    "| --- | ---: | ---: | ---: | --- |",
]
for refdes in sorted(closed, key=lambda item: int(item[1:])):
    item = closed[refdes]
    lines.append(
        f"| `{refdes}` | `{item['value']}` | {item['normalized']} | "
        f"{item['source_sheet']} | {item['circuit']} |"
    )

lines += [
    "",
    "## Deliberate holds",
    "",
    "| Ref | Why it remains unvalued |",
    "| --- | --- |",
]
for item in evidence["held"]:
    lines.append(f"| `{item['ref']}` | {item['reason']} |")

lines += [
    "",
    "## Evidence boundary",
    "",
    "- C7 and C8 are the already traced D56 one-shot timing capacitors; this",
    "  closes their sourcing metadata without changing their endpoints.",
    "- C99's `160` label is independent of its unresolved far plate. The value",
    "  is promoted while `C99_FAR` remains a continuity ask.",
    "- The nine holds are target-revision, obscured-body, or incomplete-marking cases. Values",
    "  from the superseded `.006` RF option are deliberately not copied into them.",
    "",
]

REPORT.write_text("\n".join(lines), encoding="utf-8")
print(
    "NATIVE CAPACITOR VALUES: PASS — 3 literal scan values agree across "
    "evidence, board JSON, and source PCB; 9 target values remain held"
)
