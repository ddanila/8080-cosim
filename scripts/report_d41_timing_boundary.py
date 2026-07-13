#!/usr/bin/env python3
"""Generate the D41 latch-chain timing boundary report."""
from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BOARD = ROOT / "kicad" / "juku.board.json"
REPORT = ROOT / "docs" / "d41-timing-boundary.md"


EXPECTED_UNNETTED = {
    "10": "QD",
    "11": "QC",
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
    local_report = json.loads((ROOT / "docs/photo-registration/local-packages/report.json").read_text())
    d41_fits = [item for item in local_report.get("fits", []) if item.get("refdes") == "D41"]
    d41_photo_fit_ok = (
        len(d41_fits) == 2
        and {item.get("side") for item in d41_fits} == {"component", "solder"}
        and {item.get("model") for item in d41_fits} == {"similarity", "similarity_reflected"}
    )

    checks = [
        (
            "D41 exists as an ИР16 timing-chain chip",
            chip.get("type") == "IR16" and "complete sheet-2 package census" in chip.get("prov", {}).get("pins", ""),
            "`kicad/juku.board.json` D41",
        ),
        (
            "D41 QA output is wired to both video address mux selects",
            node_in(board, "W10_QA_SEL", "D41", "13")
            and node_in(board, "W10_QA_SEL", "D50", "1")
            and node_in(board, "W10_QA_SEL", "D51", "1"),
            "`W10_QA_SEL`: D41.13 -> D50.1 + D51.1",
        ),
        (
            "D41 QB output is wired into the latch/preload chain",
            node_in(board, "LATCH_A", "D41", "12") and node_in(board, "LATCH_A", "D37", "1"),
            "`LATCH_A`: D41.12 -> D37.1",
        ),
        (
            "D41 LD is source-traced onto timing-bundle rail 17",
            node_in(board, "TIMING_TAG17", "D41", "6")
            and node_in(board, "TIMING_TAG17", "D36", "2"),
            "`TIMING_TAG17`: D41.6 + D36.2",
        ),
        (
            "D41 CK is source-traced onto timing-bundle rail 8",
            node_in(board, "SHIFT_G", "D41", "9")
            and node_in(board, "SHIFT_G", "D42", "8")
            and node_in(board, "SHIFT_G", "D43", "8"),
            "`SHIFT_G` / numbered rail 8: D41.9 + D42.8 + D43.8",
        ),
        (
            "Factory tag 7 closes the D40/D37/D54 1 MHz clock net",
            node_in(board, "LATCH_B", "D40", "11")
            and node_in(board, "LATCH_B", "D37", "2")
            and node_in(board, "LATCH_B", "D54", "9")
            and node_in(board, "LATCH_B", "D54", "15")
            and node_in(board, "LATCH_B", "D54", "18")
            and "scan sheet-2 full-resolution source closure" in board["nets"]["LATCH_B"].get("src", "")
            and "tag 7" in board["nets"]["LATCH_B"].get("src", "")
            and "1MHz" in board["nets"]["LATCH_B"].get("src", "")
            and node_in(board, "LATCH_PRE", "D37", "3")
            and node_in(board, "LATCH_PRE", "D33", "13")
            and node_in(board, "LATCH_SIG", "D33", "12")
            and node_in(board, "LATCH_SIG", "D39", "9"),
            "sheet 2: tag 7 joins D40.11/D37.2 and tied D54 CLK0/1/2 pins 9/15/18; adjacent `LATCH_PRE`/`LATCH_SIG` retained",
        ),
        (
            "D41 proved straps, outputs, and timing boundaries are netted",
            netted == {"1", "2", "3", "4", "5", "6", "8", "9", "12", "13"},
            ", ".join(f"D41.{pin}" for pin in sorted(netted)),
        ),
        (
            "D41 unused QC/QD outputs remain intentional no-connects",
            unnetted == EXPECTED_UNNETTED,
            ", ".join(f"{pin}:{name}" for pin, name in sorted(unnetted.items(), key=lambda item: int(item[0]))),
        ),
        (
            "D41 package landing is locally registered on both sides",
            d41_photo_fit_ok,
            "validated notch-right component fit plus reflected solder fit in `docs/photo-registration/local-packages/report.json`",
        ),
    ]
    ok = all(result for _, result, _ in checks)
    status = "D41 PACKAGE CONNECTIVITY SOURCE-CLOSED" if ok else "D41 TIMING BOUNDARY FAILED"

    lines = [
        "# D41 timing boundary",
        "",
        "Status date: 2026-07-13.",
        "",
        f"Status: **{status}**",
        "",
        "This generated report isolates the D41 ИР16 timing-chain boundary.",
        "The board model has guarded evidence for D41's two output-side",
        "uses, its fixed straps, and both numbered timing-bundle inputs.",
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
            table_row(["13", chip["pins"]["13"], "W10_QA_SEL", "D41.QA selects both D50/D51 video/uP mux inputs via documented wire 10"]),
            table_row(["6", chip["pins"]["6"], "TIMING_TAG17", "Direct sheet-2 junction to numbered rail 17 shared with D36.2"]),
            table_row(["9", chip["pins"]["9"], "SHIFT_G", "Direct sheet-2 junction to numbered rail 8 shared with D42.8/D43.8"]),
            "",
            "## Intentional No-Connect D41 Pins",
            "",
            "| Pin | Signal | Boundary |",
            "| --- | --- | --- |",
        ]
    )
    for pin, name in sorted(EXPECTED_UNNETTED.items(), key=lambda item: int(item[0])):
        boundary = "sheet-2 package census shows no external stub"
        lines.append(table_row([pin, name, boundary]))

    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- D41 is not a generic unresolved video chip anymore: its output-side",
            "  effects are modeled and route-checked.",
            "- The corrected two-sided package fits replace global projections",
            "  that landed in the parallel-rail field left/right of the actual IC.",
            "- A-D are grounded, DS/G are tied high, and QC/QD have no external",
            "  stubs. LD joins numbered timing rail 17; CK joins numbered rail 8.",
            "- Sheet-2 conductor tag 7 closes D40 QD/pin11 and D37.2 to the tied",
            "  D54 CLK0/CLK1/CLK2 pins 9/15/18 on the labeled 1 MHz rail.",
            "- The complete D41 package pin disposition is now source-closed. The remote",
            "  origin of rail 17 remains a wider timing-chain boundary at D36.2/D41.6.",
            "",
        ]
    )
    REPORT.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {REPORT.relative_to(ROOT)}")
    print(f"Status: {status}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
