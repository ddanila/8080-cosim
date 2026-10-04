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
if set(closed) != {"C5", "C6", "C7", "C8", "C99"}:
    fail(f"closed set drifted: {sorted(closed)}")
source_only = {item["ref"]: item for item in evidence["source_nominal_without_footprint"]}
if set(source_only) != {"C29"}:
    fail(f"source-only set drifted: {sorted(source_only)}")
target_held_nominals = {item["ref"]: item for item in evidence["source_nominal_target_value_held"]}
if {ref: item["sheet_literal"] for ref, item in target_held_nominals.items()} != {"C16": "27", "C19": "22", "C20": "22", "C22": "22"}:
    fail("sheet-3 target-held nominal set drifted")
if "1Н5" not in evidence.get("retracted_target_reading", ""):
    fail("C20/C22 retracted marking claim is missing")

board = json.loads(BOARD_JSON.read_text(encoding="utf-8"))
chips = {chip["ref"]: chip for chip in board["chips"]}
for refdes, item in closed.items():
    chip = chips.get(refdes)
    if chip is None or chip.get("type") != "C_KM":
        fail(f"{refdes} is missing or is not C_KM in board JSON")
    if chip.get("value") != item["value"]:
        fail(f"{refdes} board value is {chip.get('value')!r}, expected {item['value']!r}")
for refdes, item in source_only.items():
    chip = chips.get(refdes)
    if chip is None or chip.get("type") != "C_KM":
        fail(f"{refdes} is missing or is not C_KM in board JSON")
    if chip.get("value") != item["value"] or not chip.get("pcb_placement_pending"):
        fail(f"{refdes} source nominal or footprint hold drifted")

held = {item["ref"] for item in evidence["held"]}
unvalued = {
    chip["ref"] for chip in board["chips"]
    if chip.get("type") == "C_KM" and not chip.get("value")
}
if not held <= unvalued:
    fail(f"registered holds unexpectedly valued: {sorted(held - unvalued)}")
if not set(target_held_nominals) <= held:
    fail("source nominal is no longer guarded as an installed-value hold")

physical_values = pcb_values(PCB)
for refdes, item in closed.items():
    if physical_values.get(refdes) != item["value"]:
        fail(
            f"{refdes} source-PCB value is {physical_values.get(refdes)!r}, "
            f"expected {item['value']!r}"
        )
for refdes in source_only:
    if refdes in physical_values:
        fail(f"{refdes} unexpectedly has a source-PCB footprint")

lines = [
    "# Native schematic capacitor values",
    "",
    "Status: **5 PLACED VALUES SOURCE-CLOSED / 5 ADDITIONAL SOURCE NOMINALS / 11 REGISTERED TARGET HOLDS**",
    "",
    "The retained native circuits print five registered capacitor values.",
    "This report checksum-guards the source scans and requires the board JSON",
    "and source PCB to preserve those literals. Here, placed means that a source-PCB",
    "footprint exists; it does not establish the physical pad pair or population.",
    "The guard does not measure installed capacitance or qualify circuit timing.",
    "C29 has a source nominal but no registered footprint or owner-board value.",
    "Sheet 3 also supplies C16/C19/C20/C22 nominals; their installed values remain held.",
    "Its hold list covers only the registered cases below; other unvalued capacitors",
    "in the expanded board model are tracked in the board-fidelity ledger.",
    "",
    "## Command",
    "",
    "Run from the repository root with Python 3 (standard library only).",
    "The guard reads the source PCB text directly; KiCad is not required.",
    "It overwrites this report after the source and model checks pass.",
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
    "## Source nominal awaiting physical registration",
    "",
    "| Ref | Board literal | Normalized source nominal | Why the footprint is held |",
    "| --- | ---: | ---: | --- |",
]
for refdes, item in source_only.items():
    lines.append(
        f"| `{refdes}` | `{item['value']}` | {item['normalized']} | "
        "Owner-board population, pad pair, and physical value unproved |"
    )

lines += [
    "",
    "## Sheet 3 nominals with installed values held",
    "",
    "| Ref | Sheet literal | Source nominal | Why the installed value remains held |",
    "| --- | ---: | ---: | --- |",
]
for refdes, item in target_held_nominals.items():
    lines.append(f"| `{refdes}` | `{item['sheet_literal']}` | {item['normalized_source_nominal']} | {item['reason']} |")

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
    "- Exact `.009` sheet 2 prints bare `560` beside C5 and bare `56` beside C6;",
    "  the native-sheet convention interprets these as pF values.",
    "- C7 and C8 are the already traced D56 one-shot timing capacitors; this",
    "  closes their sourcing metadata without changing their endpoints.",
    "- C99's `160` label and grounded far plate are both shown on exact `.009`",
    "  sheet 1. Its physical population and pad identity still need inspection.",
    "- Exact `.009` sheet 3 prints C16=`27` and C19/C20/C22=`22`; its bare",
    "  values follow the native picofarad convention. Installed values need",
    "  independent measurement or complete body markings. GOST 11076-69 §2",
    "  requires a unit letter for a coded capacitance mark; the visible `±5`",
    "  and `±10` tolerance lines on C20/C22 do not supply one.",
    "- The eleven registered holds are target-revision, obscured-body, or incomplete-marking cases. Values",
    "  from the superseded `.006` RF option are deliberately not copied into them.",
    "",
]

REPORT.write_text("\n".join(lines), encoding="utf-8")
print(
    "NATIVE CAPACITOR VALUES: PASS — 5 literal scan values agree across "
    "evidence, board JSON, and source PCB; C29/C16/C19/C20/C22 nominals recorded; "
    "C20/C22 false marking retracted; 11 registered target values remain held"
)
