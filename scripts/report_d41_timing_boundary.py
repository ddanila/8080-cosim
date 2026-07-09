#!/usr/bin/env python3
"""Generate the D41 latch-chain timing boundary report."""
from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BOARD = ROOT / "kicad" / "juku.board.json"
REPORT = ROOT / "docs" / "d41-timing-boundary.md"


EXPECTED_UNNETTED = {
    "1": "DS",
    "2": "A",
    "3": "B",
    "4": "C",
    "5": "D",
    "6": "LD",
    "8": "G",
    "9": "CK",
}


def load_board() -> dict:
    return json.loads(BOARD.read_text(encoding="utf-8"))


def find_chip(board: dict, ref: str) -> dict:
    for chip in board["chips"]:
        if chip.get("ref") == ref:
            return chip
    raise KeyError(ref)


def net_nodes(board: dict, name: str) -> list[tuple[str, str]]:
    return [tuple(node) for node in board["nets"].get(name, {}).get("nodes", [])]


def node_in(board: dict, name: str, ref: str, pin: str) -> bool:
    return (ref, pin) in net_nodes(board, name)


def d41_netted_pins(board: dict) -> set[str]:
    pins: set[str] = set()
    for net in board["nets"].values():
        for ref, pin in net.get("nodes", []):
            if ref == "D41":
                pins.add(str(pin))
    return pins


def table_row(values: list[object]) -> str:
    return "| " + " | ".join(str(value).replace("|", "/") for value in values) + " |"


def main() -> int:
    board = load_board()
    chip = find_chip(board, "D41")
    netted = d41_netted_pins(board)
    unnetted = {pin: name for pin, name in chip["pins"].items() if pin not in netted}

    checks = [
        (
            "D41 exists as an ИР16 timing-chain chip",
            chip.get("type") == "IR16" and "LATCH chain" in chip.get("prov", {}).get("pins", ""),
            "`kicad/juku.board.json` D41",
        ),
        (
            "D41 QA output is wired to the video address mux select",
            node_in(board, "W10_QA_SEL", "D41", "13") and node_in(board, "W10_QA_SEL", "D50", "1"),
            "`W10_QA_SEL`: D41.13 -> D50.1",
        ),
        (
            "D41 QB output is wired into the latch/preload chain",
            node_in(board, "LATCH_A", "D41", "12") and node_in(board, "LATCH_A", "D37", "1"),
            "`LATCH_A`: D41.12 -> D37.1",
        ),
        (
            "Adjacent latch chain context is modeled",
            node_in(board, "LATCH_B", "D40", "11")
            and node_in(board, "LATCH_B", "D37", "2")
            and node_in(board, "LATCH_PRE", "D37", "3")
            and node_in(board, "LATCH_PRE", "D33", "13"),
            "`LATCH_B`/`LATCH_PRE` around D37/D40/D33",
        ),
        (
            "Only D41 output pins are currently netted",
            netted == {"12", "13"},
            ", ".join(f"D41.{pin}" for pin in sorted(netted)),
        ),
        (
            "D41 input/control pins remain an explicit source boundary",
            unnetted == EXPECTED_UNNETTED,
            ", ".join(f"{pin}:{name}" for pin, name in sorted(unnetted.items(), key=lambda item: int(item[0]))),
        ),
    ]
    ok = all(result for _, result, _ in checks)
    status = "D41 OUTPUTS GUARDED / INPUT TIMING BUS PENDING" if ok else "D41 TIMING BOUNDARY FAILED"

    lines = [
        "# D41 timing boundary",
        "",
        "Status date: 2026-07-09.",
        "",
        f"Status: **{status}**",
        "",
        "This generated report isolates the D41 ИР16 timing-chain boundary.",
        "The board model has guarded evidence for D41's two output-side",
        "uses, but it still lacks historical-source-complete nets for the",
        "parallel inputs and control pins that come from the sheet-2 timing bus.",
        "",
        "## Command",
        "",
        "```sh",
        "python3 scripts/report_d41_timing_boundary.py",
        "```",
        "",
        "## Checks",
        "",
        "| Check | Result | Evidence |",
        "| --- | --- | --- |",
    ]
    lines.extend(table_row([name, "PASS" if result else "FAIL", evidence]) for name, result, evidence in checks)
    lines.extend(
        [
            "",
            "## Netted D41 Pins",
            "",
            "| Pin | Signal | Net | Evidence |",
            "| --- | --- | --- | --- |",
            table_row(["12", chip["pins"]["12"], "LATCH_A", "D41.QB feeds D37.1 in the modeled latch/preload chain"]),
            table_row(["13", chip["pins"]["13"], "W10_QA_SEL", "D41.QA selects D50 video/uP mux input via documented wire 10"]),
            "",
            "## Pending D41 Pins",
            "",
            "| Pin | Signal | Boundary |",
            "| --- | --- | --- |",
        ]
    )
    for pin, name in sorted(EXPECTED_UNNETTED.items(), key=lambda item: int(item[0])):
        lines.append(table_row([pin, name, "sheet-2 timing-bus continuity/source read required"]))

    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- D41 is not a generic unresolved video chip anymore: its output-side",
            "  effects are modeled and route-checked.",
            "- The remaining D41 gap is specific to pins 1-6/8/9: serial input,",
            "  parallel inputs, load, gate, and clock from the timing-wire bus.",
            "- Do not infer these input/control nets from the runnable raster model;",
            "  they need a readable sheet-2 timing-chain source, macro photo, or",
            "  continuity pass before D41 can leave the board-fidelity gap ledger.",
            "",
        ]
    )
    REPORT.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {REPORT.relative_to(ROOT)}")
    print(f"Status: {status}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
