#!/usr/bin/env python3
"""Generate the S4 external-interrupt switch boundary report."""
from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BOARD = ROOT / "kicad" / "juku.board.json"
REPORT = ROOT / "docs" / "s4-interrupt-boundary.md"


def load_board() -> dict:
    return json.loads(BOARD.read_text(encoding="utf-8"))


def chip(board: dict, ref: str) -> dict:
    for item in board["chips"]:
        if item.get("ref") == ref:
            return item
    raise KeyError(ref)


def nodes(board: dict, name: str) -> set[tuple[str, str]]:
    return {tuple(node) for node in board["nets"].get(name, {}).get("nodes", [])}


def has_nodes(board: dict, name: str, expected: set[tuple[str, str]]) -> bool:
    return expected <= nodes(board, name)


def pin_is_netted(board: dict, ref: str, pin: str) -> bool:
    return any((ref, pin) in nodes(board, name) for name in board["nets"])


def endpoint_text(board: dict, name: str) -> str:
    rendered = [f"{ref}.{pin}" for ref, pin in sorted(nodes(board, name))]
    return ", ".join(rendered) if rendered else "-"


def row(values: list[object]) -> str:
    return "| " + " | ".join(str(value).replace("|", "/") for value in values) + " |"


def main() -> int:
    board = load_board()
    s4 = chip(board, "S4")
    d3 = chip(board, "D3")
    d10 = chip(board, "D10")

    guarded_checks = [
        (
            "S4 is present as the scanned interrupt-path switch",
            s4.get("type") == "SW"
            and "ВДМ1-2" in s4.get("prov", {}).get("pins", "")
            and "D3-buffered IR7/IR6" in s4.get("prov", {}).get("pins", ""),
            "S4 provenance block",
        ),
        (
            "INT7 raw expansion input reaches D3",
            has_nodes(board, "INT7_RAW", {("X1", "113B"), ("D3", "13")}),
            "`INT7_RAW`: X1.113B -> D3.13",
        ),
        (
            "D3 buffered IR7 reaches PIC IR7",
            has_nodes(board, "IR7", {("D3", "12"), ("D10", "25")}),
            "`IR7`: D3.12 -> D10.25",
        ),
        (
            "INT6 raw expansion input reaches D3",
            has_nodes(board, "INT6_RAW", {("X1", "113C"), ("D3", "1")}),
            "`INT6_RAW`: X1.113C -> D3.1",
        ),
        (
            "D3 buffered IR6 reaches PIC IR6",
            has_nodes(board, "IR6", {("D3", "2"), ("D10", "24")}),
            "`IR6`: D3.2 -> D10.24",
        ),
        (
            "D3 and D10 package roles match the interrupt path",
            d3.get("type") == "LN2" and d10.get("type") == "PIC8259",
            "D3 inverter sections feed D10 PIC inputs",
        ),
    ]
    boundary_checks = [
        (
            "S4 pins remain unnetted until source/continuity proof",
            not pin_is_netted(board, "S4", "1") and not pin_is_netted(board, "S4", "2"),
            "S4.1/S4.2 are known switch pins, but their exact insertion into IR6/IR7 remains pending",
        ),
        (
            "Do not infer S4 wiring from MAME or behavior",
            "via D3+S4" in d10.get("prov", {}).get("pins", ""),
            "current model preserves the note but does not replace continuity evidence",
        ),
    ]

    ok = all(result for _, result, _ in guarded_checks + boundary_checks)
    status = "S4 INTERRUPT PATH GUARDED / SWITCH CONTINUITY PENDING" if ok else "S4 INTERRUPT BOUNDARY FAILED"

    lines = [
        "# S4 interrupt boundary",
        "",
        "Status date: 2026-07-09.",
        "",
        f"Status: **{status}**",
        "",
        "This generated report isolates the external interrupt receive path",
        "around S4. It guards the current X1 -> D3 -> D10 IR6/IR7 evidence",
        "while keeping the two S4 switch pins as explicit source-read or",
        "continuity work.",
        "",
        "## Command",
        "",
        "```sh",
        "python3 scripts/report_s4_interrupt_boundary.py",
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
            "| Boundary | Result | Current evidence |",
            "| --- | --- | --- |",
        ]
    )
    lines.extend(row([name, "PASS" if result else "FAIL", evidence]) for name, result, evidence in boundary_checks)

    lines.extend(
        [
            "",
            "## Current Interrupt Nets",
            "",
            "| Net | Endpoints | Source note |",
            "| --- | --- | --- |",
        ]
    )
    for name in ("INT7_RAW", "IR7", "INT6_RAW", "IR6"):
        net = board["nets"].get(name, {})
        lines.append(row([f"`{name}`", f"`{endpoint_text(board, name)}`", net.get("src", "-")]))

    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- The modeled interrupt path carries expansion `INT7`/`INT6` through D3",
            "  inverter sections to PIC inputs IR7/IR6.",
            "- S4 is physically present and associated with that path, but its two",
            "  switch pins are deliberately not promoted into the netlist yet.",
            "- Closing this boundary requires a sheet read, macro photo, or continuity",
            "  check of S4.1/S4.2 on a .009 processor board.",
            "",
        ]
    )

    REPORT.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {REPORT.relative_to(ROOT)}")
    print(f"Status: {status}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
