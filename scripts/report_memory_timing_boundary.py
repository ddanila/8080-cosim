#!/usr/bin/env python3
"""Generate the DRAM/clock timing boundary report."""
from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BOARD = ROOT / "kicad" / "juku.board.json"
REPORT = ROOT / "docs" / "memory-timing-boundary.md"


def load_board() -> dict:
    return json.loads(BOARD.read_text(encoding="utf-8"))


def nodes(board: dict, net_name: str) -> list[tuple[str, str]]:
    return [tuple(node) for node in board["nets"].get(net_name, {}).get("nodes", [])]


def has_nodes(board: dict, net_name: str, expected: set[tuple[str, str]]) -> bool:
    return expected <= set(nodes(board, net_name))


def endpoint_text(board: dict, net_name: str) -> str:
    rendered = [f"{ref}.{pin}" for ref, pin in nodes(board, net_name)]
    if not rendered:
        return "-"
    if len(rendered) <= 10:
        return ", ".join(rendered)
    return ", ".join(rendered[:10]) + f", ... (+{len(rendered) - 10})"


def row(values: list[object]) -> str:
    return "| " + " | ".join(str(value).replace("|", "/") for value in values) + " |"


def main() -> int:
    board = load_board()
    chips = {chip.get("ref"): chip for chip in board["chips"]}
    d35 = chips["D35"]
    d53 = next(chip for chip in board["chips"] if chip.get("ref") == "D53")
    d59 = chips["D59"]
    hex_contract = {
        "1": "I1", "2": "O2", "3": "I3", "4": "O4", "5": "I5", "6": "O6",
        "9": "I9", "8": "O8",
    }
    d59_contract = dict(hex_contract, **{"1": "XIN", "2": "OSC"})
    d53_contract = {
        "7": "Y_N7", "9": "Y_N6", "10": "Y_N5", "11": "Y_N4",
        "12": "Y_N3", "13": "Y_N2", "14": "Y_N1", "15": "Y_N0",
    }
    d53_outputs = {
        "D53_Y0_R49": {("D53", "15"), ("R49", "1")},
        "D53_Y1_R50": {("D53", "14"), ("R50", "1")},
        "D53_Y2_R51": {("D53", "13"), ("R51", "1")},
        "D53_Y3_R52": {("D53", "12"), ("R52", "1")},
    }
    d56_rc = {
        "D56_CLR": {("D56", "3"), ("D56", "11"), ("R61", "2")},
        "D56_RC1": {("D56", "15"), ("R59", "1"), ("C8", "1")},
        "D56_C1": {("D56", "14"), ("C8", "2")},
        "D56_RC2": {("D56", "7"), ("R47", "1"), ("C7", "1")},
        "D56_C2": {("D56", "6"), ("C7", "2")},
    }
    guarded_checks = [
        (
            "All 32 DRAM sockets retain complete option-rail roles",
            all(
                chips[f"D{ref}"].get("pins", {}).get("1") == "NC_VBB_OPTION"
                and chips[f"D{ref}"].get("pins", {}).get("8") == "VCC_OPTION"
                and chips[f"D{ref}"].get("pins", {}).get("16") == "VSS_GND"
                and (f"D{ref}", "1") in set(nodes(board, "RAIL_H"))
                and (f"D{ref}", "8") in set(nodes(board, "RAIL_G"))
                and (f"D{ref}", "16") in set(nodes(board, "RAIL_E"))
                for ref in range(60, 92)
            ),
            "D60-D91 pins 1/8/16 -> RAIL_H/RAIL_G/RAIL_E; pin 1 is internal NC for populated РУ5",
        ),
        (
            "D53 RAS/CAS ladder outputs are guarded",
            all(has_nodes(board, name, expected) for name, expected in d53_outputs.items()),
            "`D53_Y0_R49`..`D53_Y3_R52`",
        ),
        (
            "D36 write rail is guarded to all modeled DRAM W pins",
            has_nodes(board, "W_RAIL16", {("D36", "8")})
            and sum(1 for ref, pin in nodes(board, "W_RAIL16") if pin == "3" and ref.startswith("D")) >= 32,
            "`W_RAIL16` includes D36.8 plus DRAM pin-3 fanout",
        ),
        (
            "D36 CAS pre-driver reaches R57",
            has_nodes(board, "CAS_PRE", {("D36", "11"), ("R57", "1")}),
            "`CAS_PRE`: D36.11 -> R57.1",
        ),
        (
            "Shared CAS rail is guarded to all modeled DRAM C pins",
            has_nodes(board, "CAS", {("D36", "1"), ("R57", "2"), ("R58", "1")})
            and sum(1 for ref, pin in nodes(board, "CAS") if pin == "15" and ref.startswith("D")) >= 32,
            "`CAS` includes D36.1/R57.2/R58.1 plus DRAM pin-15 fanout",
        ),
        (
            "PHI2TTL timing gate fanout is guarded",
            has_nodes(board, "PHI2TTL", {("D35", "13"), ("D39", "1"), ("D92", "2"), ("D92", "3"), ("D53", "4")}),
            "`PHI2TTL` source-risk net",
        ),
        (
            "D39 latch/output context is guarded",
            has_nodes(board, "D39_O8", {("D39", "8"), ("D59", "11")})
            and has_nodes(board, "D39Y", {("D39", "11"), ("D38", "10"), ("D38", "13")}),
            "`D39_O8` and `D39Y`",
        ),
        (
            "D56 one-shot RC networks are guarded",
            all(has_nodes(board, name, expected) for name, expected in d56_rc.items()),
            "`D56_CLR`, `D56_RC1/C1`, `D56_RC2/C2`",
        ),
    ]
    boundary_checks = [
        (
            "D35/D59 complete inverter package roles remain visible",
            all(d35.get("pins", {}).get(pin) == role for pin, role in hex_contract.items())
            and all(d59.get("pins", {}).get(pin) == role for pin, role in d59_contract.items())
            and has_nodes(board, "VID_MIX2", {("D35", "4"), ("R39", "1")}),
            "D35.4->R39.1 is guarded; other restored sections remain continuity boundaries",
        ),
        (
            "D53 Y4-Y7 remain explicit unresolved functional pins",
            all(d53.get("pins", {}).get(pin) == role for pin, role in d53_contract.items())
            and not any(ref == "D53" and pin in {"7", "9", "10", "11"}
                        for net in board["nets"].values() for ref, pin in net.get("nodes", [])),
            "D53.11/.10/.9/.7 require traced destinations or explicit NC proof",
        ),
        (
            "D36_CAS_IN remains source-boundary only",
            set(nodes(board, "D36_CAS_IN")) == {("D36", "12"), ("D36", "13")},
            endpoint_text(board, "D36_CAS_IN"),
        ),
        (
            "D39_MEMCYC remains source-boundary only",
            set(nodes(board, "D39_MEMCYC")) == {("D39", "3"), ("D39", "4")},
            endpoint_text(board, "D39_MEMCYC"),
        ),
        (
            "D56_QN remains unresolved one-shot output",
            set(nodes(board, "D56_QN")) == {("D56", "4")},
            endpoint_text(board, "D56_QN"),
        ),
    ]
    ok = all(result for _, result, _ in guarded_checks + boundary_checks)
    status = "MEMORY TIMING GUARDED / CAS-MEMCYC SOURCE BOUNDARY PENDING" if ok else "MEMORY TIMING BOUNDARY FAILED"

    lines = [
        "# Memory timing boundary",
        "",
        "Status date: 2026-07-11.",
        "",
        f"Status: **{status}**",
        "",
        "This generated report narrows the remaining DRAM/clock timing risks.",
        "The board model preserves the traced RAS/CAS ladder, write rail,",
        "PHI2TTL fanout, and D56 one-shot RC networks. It also keeps the",
        "unread CAS input, memory-cycle gate, and D56 Q_N destination as",
        "explicit source boundaries instead of silently promoting them.",
        "",
        "## Command",
        "",
        "```sh",
        "python3 scripts/report_memory_timing_boundary.py",
        "```",
        "",
        "## Guarded Checks",
        "",
        "| Check | Result | Evidence |",
        "| --- | --- | --- |",
    ]
    lines.extend(row([name, "PASS" if result else "FAIL", evidence]) for name, result, evidence in guarded_checks)
    lines.extend(
        [
            "",
            "## Pending Boundary Checks",
            "",
            "| Boundary | Result | Current endpoints |",
            "| --- | --- | --- |",
        ]
    )
    lines.extend(row([name, "PASS" if result else "FAIL", evidence]) for name, result, evidence in boundary_checks)
    lines.extend(
        [
            "",
            "## Current Timing Nets",
            "",
            "| Net | Endpoints | Source note |",
            "| --- | --- | --- |",
        ]
    )
    for name in (
        "D53_Y0_R49",
        "D53_Y1_R50",
        "D53_Y2_R51",
        "D53_Y3_R52",
        "W_RAIL16",
        "CAS_PRE",
        "CAS",
        "D36_CAS_IN",
        "D39_MEMCYC",
        "PHI2TTL",
        "D39_O8",
        "D39Y",
        "D56_CLR",
        "D56_RC1",
        "D56_C1",
        "D56_RC2",
        "D56_C2",
        "D56_QN",
    ):
        net = board["nets"].get(name, {})
        lines.append(row([f"`{name}`", f"`{endpoint_text(board, name)}`", net.get("src", "-")]))

    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- The functional board model has enough traced structure for fabrication",
            "  and staged bring-up: RAS/CAS ladder endpoints, the DRAM write rail,",
            "  and the key PHI2TTL/D56 support nets are guarded.",
            "- The exact CAS-driver input source (`D36_CAS_IN`), D39 memory-cycle",
            "  source/destinations (`D39_MEMCYC`), and D56 Q_N destination are still",
            "  not historical-source-complete.",
            "- Do not replace these boundaries with a behavioral timing guess from the",
            "  runnable twin. They need a readable sheet-2 source pass, macro photo,",
            "  continuity check, or scope trace before being removed from the",
            "  fidelity gap ledger.",
            "",
        ]
    )
    REPORT.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {REPORT.relative_to(ROOT)}")
    print(f"Status: {status}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
