#!/usr/bin/env python3
"""Guard the factory insulated-link endpoint map from the .009 wire table."""
from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BOARD = ROOT / "kicad/juku.board.json"
WIRE_TABLE = ROOT / "ref/schematics/dgsh5-109-009-sb-wire-table.md"

# Conductor position, assembly-board point, nominal length, electrical net,
# and the package/connector endpoints proved by the drawing plus owner reads.
LINKS = [
    (3, 7, "~24", "PHI1", {("D1", "22"), ("D35", "10")}),
    (4, 8, "~19", "STSTB", {("D5", "1"), ("D38", "8")}),
    (5, 9, "~12", "SYNC", {("D1", "19"), ("D38", "12")}),
    (6, 10, "~11.5", "W10_QA_SEL", {("D41", "13"), ("D50", "1")}),
    (7, 11, "~11.5", "MEMR", {("D7", "1"), ("D92", "13")}),
    (8, 12, "~20", "RAM_OUT_EN", {("D13", "2"), ("D37", "4")}),
    (9, 13, "~15", "ROE", {("D13", "1"), ("D92", "1")}),
    (10, 14, "~23", "PHI2", {("D1", "15"), ("D35", "12")}),
    (13, 19, "~9.5", "MEMW", {("D5", "26"), ("D7", "2")}),
    # The owner read was made through the installed X3 harness. A23 is the
    # photographed PCB landing between D3.10 and remote connector pin X3.3.
    (14, 20, "~6", "S_TTL", {("D3", "10"), ("A23", "1"), ("X3", "3")}),
]


def main() -> int:
    board = json.loads(BOARD.read_text(encoding="utf-8"))
    table = WIRE_TABLE.read_text(encoding="utf-8")
    errors: list[str] = []

    for position, point, length, net_name, expected in LINKS:
        net = board["nets"].get(net_name)
        if net is None:
            errors.append(f"position {position} / A:{point}: missing net {net_name}")
            continue
        actual = {tuple(node) for node in net.get("nodes", [])}
        missing = expected - actual
        if missing:
            formatted = ", ".join(f"{ref}.{pin}" for ref, pin in sorted(missing))
            errors.append(
                f"position {position} / A:{point}: {net_name} missing {formatted}"
            )
        row = f"| {position} | А:{point} | А:{point} | {length} |"
        if row not in table:
            errors.append(f"wire-table transcription missing exact row: {row}")

    if errors:
        for error in errors:
            print(f"FACTORY-WIRE-LINKS: FAIL: {error}")
        return 1

    print(
        "FACTORY-WIRE-LINKS: PASS: "
        f"{len(LINKS)} on-board insulated links mapped to guarded endpoints"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
