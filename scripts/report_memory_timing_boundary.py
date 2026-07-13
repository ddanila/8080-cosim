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
    d36 = chips["D36"]
    d59 = chips["D59"]
    hex_contract = {
        "1": "I1", "2": "O2", "3": "I3", "4": "O4", "5": "I5", "6": "O6",
        "9": "I9", "8": "O8",
    }
    d59_contract = dict(hex_contract, **{"1": "XIN", "2": "OSC"})
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
            "D36 К531ЛА12 package contract is the SN74S37-compatible quad 2-input NAND",
            d36.get("pins", {}) == {
                "1": "A2", "2": "B2", "3": "Y2",
                "4": "B", "5": "A", "6": "Y",
                "9": "A3", "10": "B3", "8": "Y3",
                "12": "A4", "13": "B4", "11": "Y4",
            }
            and "SN74S37" in d36.get("prov", {}).get("refdes", "")
            and has_nodes(board, "GND", {("D36", "7")})
            and has_nodes(board, "P5V", {("D36", "14")}),
            "inputs 1/2,4/5,9/10,12/13; outputs 3/6/8/11; GND7/VCC14",
        ),
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
            "E1 MA7/DRAM-size selector retains all three source endpoints",
            has_nodes(board, "P5V", {("E1", "1")})
            and has_nodes(board, "MA7", {("E1", "2")})
            and has_nodes(board, "MA6", {("E1", "3"), ("D51", "9")}),
            "sheet-2: E1.1=+5 V, E1.2=MA7 rail 28, E1.3=D51.9/MA6",
        ),
        (
            "E14 video-mux enable retains the drawn 1-3 strap",
            has_nodes(board, "VID_MUX_G", {("E14", "1"), ("E14", "3"), ("D50", "15"), ("D51", "15")})
            and has_nodes(board, "P5V", {("E14", "2")})
            and has_nodes(board, "GND", {("E14", "4")}),
            "sheet-2: E14.1-E14.3 fitted strap; E14.2=+5 V; E14.4=GND",
        ),
        (
            "D53 RAS/CAS ladder outputs are guarded",
            all(has_nodes(board, name, expected) for name, expected in d53_outputs.items()),
            "`D53_Y0_R49`..`D53_Y3_R52`",
        ),
        (
            "D53 unused Y4-Y7 outputs remain source-proved no-connects",
            all(["D53", pin] in board.get("no_connects", []) for pin in ("7", "9", "10", "11"))
            and not any(ref == "D53" and pin in {"7", "9", "10", "11"}
                        for net in board["nets"].values() for ref, pin in net.get("nodes", [])),
            "sheet-2 complete D53 symbol draws only Y0-Y3; pins11/10/9/7 have no stubs",
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
            "D39 remaining NAND inputs are source-closed onto control rails 3 and 1",
            has_nodes(board, "XTAL16M", {("D39", "10"), ("D42", "9"), ("D43", "9")})
            and has_nodes(board, "GND", {("D39", "2"), ("D43", "1")}),
            "sheet-2 direct junctions: D39.10 -> local rail3/XTAL16M; D39.2 -> grounded rail1",
        ),
        (
            "D38 load gate is source-closed except for the remote origin of rail 2",
            has_nodes(board, "D39_MEMCYC", {("D39", "3"), ("D39", "4"), ("D38", "5")})
            and has_nodes(board, "TIMING_TAG2", {("D38", "4")})
            and has_nodes(board, "GND", {("D38", "2")})
            and has_nodes(board, "CAS", {("D38", "1")}),
            "D38 pins5/4/2/1 <- numbered rails4/2/1/15; only rail2 remote origin remains",
        ),
        (
            "D56 one-shot RC networks are guarded",
            all(has_nodes(board, name, expected) for name, expected in d56_rc.items()),
            "`D56_CLR`, `D56_RC1/C1`, `D56_RC2/C2`",
        ),
        (
            "D56 active outputs reach both gate-3 XOR inputs",
            has_nodes(board, "D56_Q2_D34", {("D56", "5"), ("D34", "9")})
            and has_nodes(board, "D56_Q2N_D34", {("D56", "12"), ("D34", "10")})
            and all(["D56", pin] in board.get("no_connects", []) for pin in ("1", "9", "13")),
            "sheet-2: D56.5/.12 -> D34.9/.10; undrawn D56.1/.9/.13 are NC",
        ),
    ]
    boundary_checks = [
        (
            "D35/D59 complete inverter package roles remain visible",
            all(d35.get("pins", {}).get(pin) == role for pin, role in hex_contract.items())
            and all(d59.get("pins", {}).get(pin) == role for pin, role in d59_contract.items())
            and has_nodes(board, "VID_MIX2", {("D35", "4"), ("R39", "1")})
            and all(["D35", pin] in board.get("no_connects", []) for pin in ("1", "2", "5", "6", "8", "9")),
            "D35.4->R39.1 is guarded; D59.5/.6 are source-proved NC; D59.10 remains a continuity boundary",
        ),
        (
            "D36_CAS_IN remains source-boundary only",
            set(nodes(board, "D36_CAS_IN")) == {("D36", "12"), ("D36", "13")},
            endpoint_text(board, "D36_CAS_IN"),
        ),
        (
            "D56_QN remains unresolved one-shot output",
            set(nodes(board, "D56_QN")) == {("D56", "4")},
            endpoint_text(board, "D56_QN"),
        ),
    ]
    ok = all(result for _, result, _ in guarded_checks + boundary_checks)
    status = "MEMORY TIMING GUARDED / CAS-D56 SOURCE BOUNDARY PENDING" if ok else "MEMORY TIMING BOUNDARY FAILED"

    lines = [
        "# Memory timing boundary",
        "",
        "Status date: 2026-07-13.",
        "",
        f"Status: **{status}**",
        "",
        "This generated report narrows the remaining DRAM/clock timing risks.",
        "The board model preserves the traced E1/E14 selector straps, RAS/CAS ladder, write rail,",
        "PHI2TTL fanout, and D56 one-shot RC networks. It also keeps the",
        "unread CAS input and D56 Q_N destination as",
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
        "XTAL16M",
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
            "- The exact CAS-driver input source (`D36_CAS_IN`) and D56 Q_N",
            "  destination are still",
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
