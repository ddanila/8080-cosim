#!/usr/bin/env python3
"""Close D30.1 onto the native D38-side status-strobe island."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BOARD = ROOT / "kicad" / "juku.board.json"
SCHEMATIC = ROOT / "kicad" / "juku.kicad_sch"
PCBS = (
    ROOT / "kicad" / "juku.kicad_pcb",
    ROOT / "kicad" / "juku_routed.kicad_pcb",
    ROOT / "kicad" / "juku_routed_candidate.kicad_pcb",
)
SOURCE = "SSTB_N"
DESTINATION = "STSTB_D38"
MEASURED_SOURCES = ("READY_PRE_N", "D30B_D_PRE_N")


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected one exact phrase, found {count}")
    return text.replace(old, new)


def merge_or_rename_pcb(path: Path, source_name: str = SOURCE) -> None:
    text = path.read_text()
    source = re.search(rf'^\s*\(net (\d+) "{source_name}"\)$', text, re.MULTILINE)
    destination = re.search(rf'^\s*\(net (\d+) "{DESTINATION}"\)$', text, re.MULTILINE)
    if not source:
        raise SystemExit(f"{path}: missing {source_name} declaration")
    source_id = source.group(1)
    if destination:
        destination_id = destination.group(1)
        text = text.replace(source.group(0) + "\n", "", 1)
        text = text.replace(f'(net {source_id} "{source_name}")', f'(net {destination_id} "{DESTINATION}")')
        text = text.replace(f"(net {source_id})", f"(net {destination_id})")
        text = text.replace(f'(net_name "{source_name}")', f'(net_name "{DESTINATION}")')
    else:
        text = text.replace(f'(net {source_id} "{source_name}")', f'(net {source_id} "{DESTINATION}")')
        text = text.replace(f'(net_name "{source_name}")', f'(net_name "{DESTINATION}")')
    if source_name in text:
        raise SystemExit(f"{path}: residual {source_name} text")
    path.write_text(text)


def apply_measured_common() -> None:
    board = json.loads(BOARD.read_text())
    expected = {
        ("D38", "8"), ("W8", "2"), ("D30", "1"), ("D30", "4"),
        ("D30", "10"), ("D30", "12"), ("R5", "2")
    }
    if set(map(tuple, board["nets"][DESTINATION]["nodes"])) != expected:
        raise SystemExit("board JSON does not contain the measured common D30 conductor")
    if any(name in board["nets"] for name in MEASURED_SOURCES):
        raise SystemExit("board JSON still contains a pre-measurement D30 net")
    for pcb in PCBS[1:]:
        text = pcb.read_text()
        for source_name in MEASURED_SOURCES:
            if source_name in text:
                merge_or_rename_pcb(pcb, source_name)


def apply() -> None:
    text = BOARD.read_text()
    board = json.loads(text)
    if board["nets"].get(SOURCE, {}).get("nodes") != [["D30", "1"]]:
        raise SystemExit("SSTB_N is no longer the expected D30.1 singleton")
    destination = board["nets"][DESTINATION]["nodes"]
    if destination != [["D38", "8"], ["W8", "2"]]:
        raise SystemExit("STSTB_D38 endpoint set changed")
    text = replace_once(
        text,
        '  "SSTB_N": {\n   "src": "sheet-1 label -SSTB enters D30.1; off-sheet source on sheet 2 remains boundary",\n   "nodes": [["D30", "1"]]\n  },\n',
        "",
        "SSTB_N board block",
    )
    text = replace_once(
        text,
        '    ["D38", "8"],\n    ["W8", "2"]\n',
        '    ["D38", "8"],\n    ["W8", "2"],\n    ["D30", "1"]\n',
        "STSTB_D38 endpoints",
    )
    text = replace_once(
        text,
        "section A: D input2 receives physical D2.12 through the R6 pull-up node, CLK3=PHI2TTL, /CLR1=-SSTB boundary, /PRE4 remains a continuity boundary",
        "section A: D input2 receives physical D2.12 through the R6 pull-up node, CLK3=PHI2TTL, /CLR1=-SSTB is source-closed to D38.8 on the D38-side A:8 island, /PRE4 remains a continuity boundary",
        "D30 provenance",
    )
    text = replace_once(
        text,
        '"src": "factory wire А:8 D38-side copper island",',
        '"src": "native cross-sheet closure: sheet-2 D38.8 exports active-low STB to sheet-1 -SSTB/D30.1 on the D38-side factory-wire А:8 copper island",',
        "STSTB_D38 provenance",
    )
    BOARD.write_text(text)
    json.loads(text)

    schematic = SCHEMATIC.read_text()
    schematic = replace_once(
        schematic,
        '(label "SSTB_N" (at 50.0 11557.46 0)',
        '(label "STSTB_D38" (at 50.0 11557.46 0)',
        "D30 schematic label",
    )
    SCHEMATIC.write_text(schematic)
    for pcb in PCBS:
        merge_or_rename_pcb(pcb)


def check() -> None:
    board = json.loads(BOARD.read_text())
    failures = []
    if SOURCE in board["nets"]:
        failures.append(f"board retains {SOURCE}")
    expected = {
        ("D38", "8"), ("W8", "2"), ("D30", "1"), ("D30", "4"),
        ("D30", "10"), ("D30", "12"), ("R5", "2")
    }
    actual = set(map(tuple, board["nets"][DESTINATION]["nodes"]))
    if actual != expected:
        failures.append(f"{DESTINATION} endpoints differ: {sorted(actual)}")
    schematic = SCHEMATIC.read_text()
    if '(label "SSTB_N"' in schematic:
        failures.append("schematic retains SSTB_N label")
    if schematic.count('(label "STSTB_D38"') < 3:
        failures.append("schematic does not join D30.1 to both D38-side labels")
    for pcb in PCBS:
        text = pcb.read_text()
        if SOURCE in text:
            failures.append(f"{pcb.relative_to(ROOT)} retains {SOURCE}")
        for source_name in MEASURED_SOURCES:
            if source_name in text:
                failures.append(f"{pcb.relative_to(ROOT)} retains {source_name}")
    if failures:
        raise SystemExit("\n".join(failures))
    print("D30-STATUS-STROBE: PASS (D30.1/.4/.10/.12 and R5 join D38.8/W8.2, not the D5-side island)")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true", help="perform the one-time closure")
    parser.add_argument(
        "--apply-measured-common", action="store_true",
        help="merge the measured D30.4/.10/.12 branches into STSTB_D38 on routed PCBs",
    )
    args = parser.parse_args()
    if args.apply:
        apply()
    if args.apply_measured_common:
        apply_measured_common()
    check()


if __name__ == "__main__":
    main()
