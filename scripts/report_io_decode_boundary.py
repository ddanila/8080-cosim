#!/usr/bin/env python3
"""Generate the sheet-1 I/O decode boundary report."""
from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BOARD = ROOT / "kicad" / "juku.board.json"
REPORT = ROOT / "docs" / "io-decode-boundary.md"


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


def endpoint_text(board: dict, name: str) -> str:
    rendered = [f"{ref}.{pin}" for ref, pin in sorted(nodes(board, name))]
    if not rendered:
        return "-"
    if len(rendered) <= 10:
        return ", ".join(rendered)
    return ", ".join(rendered[:10]) + f", ... (+{len(rendered) - 10})"


def row(values: list[object]) -> str:
    return "| " + " | ".join(str(value).replace("|", "/") for value in values) + " |"


def main() -> int:
    board = load_board()
    d9 = chip(board, "D9")
    d7 = chip(board, "D7")
    d5 = chip(board, "D5")
    checks = [
        (
            "D5 system-controller power contract is routed",
            d5.get("pins", {}).get("14") == "VSS_GND"
            and d5.get("pins", {}).get("28") == "VCC_5V"
            and has_nodes(board, "GND", {("D5", "14")})
            and has_nodes(board, "P5V", {("D5", "28")}),
            "D5.14 GND / D5.28 +5V",
        ),
        (
            "D9 is the physical К555ИД7 I/O decoder",
            d9.get("type") == "IO_DEC138" and "D2 is a separate" in d9.get("prov", {}).get("refdes", ""),
            "`kicad/juku.board.json` D9 provenance",
        ),
        (
            "D7 strobe-NAND output reaches the R17/C99 D9.G1 RC node",
            has_nodes(board, "PROM_EN", {("D7", "11"), ("R17", "2")})
            and has_nodes(board, "V3_RC", {("R17", "1"), ("C99", "1"), ("D9", "6")}),
            "`PROM_EN` -> `V3_RC`",
        ),
        (
            "D9 region-enable inputs are tied to REV",
            has_nodes(board, "REV", {("D6", "10"), ("D9", "4"), ("D9", "5"), ("R13", "2")}),
            "`REV`: D6.10 -> D9.4/D9.5",
        ),
        (
            "D9 select inputs are BA10..BA12",
            has_nodes(board, "BA10", {("D9", "1")})
            and has_nodes(board, "BA11", {("D9", "2")})
            and has_nodes(board, "BA12", {("D9", "3")}),
            "`BA10`, `BA11`, `BA12` into D9.A/B/C",
        ),
        (
            "D7 input strobes are wired to IOWR/IORD",
            has_nodes(board, "IOWR", {("D7", "10"), ("D11", "10"), ("D26", "36"), ("D27", "36")})
            and has_nodes(board, "IORD", {("D7", "9"), ("D11", "13"), ("D26", "5"), ("D27", "5")}),
            "`IOWR`/`IORD` fanout",
        ),
        (
            "D9 chip-select outputs are routed to the modeled peripherals",
            has_nodes(board, "CS_D10", {("D9", "15"), ("D10", "1")})
            and has_nodes(board, "CS_D26", {("D9", "14"), ("D26", "6")})
            and has_nodes(board, "CS_D11", {("D9", "13"), ("D11", "11")})
            and has_nodes(board, "CS_D27", {("D9", "12"), ("D27", "6")})
            and has_nodes(board, "CS_D54", {("D9", "11"), ("D54", "21")})
            and has_nodes(board, "CS_D55", {("D9", "10"), ("D55", "21")})
            and has_nodes(board, "CS_D57", {("D9", "9"), ("D57", "21")})
            and has_nodes(board, "CS_FDC", {("D9", "7")})
            and has_nodes(board, "FDC_RE_N", {("D94", "1"), ("D93", "4")})
            and has_nodes(board, "FDC_CS_N", {("D94", "2"), ("D93", "3")})
            and has_nodes(board, "FDC_WE_N", {("D94", "3"), ("D93", "2")}),
            "`CS_D10`..`CS_FDC` plus private D94-to-D93 controls",
        ),
        (
            "D25 bus turnaround handoff is guarded",
            has_nodes(board, "D25_T", {("D7", "6"), ("D25", "11")}),
            "`D25_T`: D7.6 -> D25.11",
        ),
    ]
    boundaries = [
        (
            "D7 fourth-gate strobe inputs are source-proven",
            d7.get("pins", {}).get("9") == "A4"
            and d7.get("pins", {}).get("10") == "B4"
            and "full-resolution" in board["nets"]["IOWR"]["src"]
            and "full-resolution" in board["nets"]["IORD"]["src"],
            "IORD/IOWR are on D7.9/D7.10 from the full-resolution sheet",
        ),
        (
            "C99 far physical pad is preserved without assuming ground",
            has_nodes(board, "V3_RC", {("C99", "1")})
            and set(nodes(board, "C99_FAR")) == {("C99", "2")}
            and not any(ref == "C99" and pin == "2" for ref, pin in nodes(board, "V3_RC")),
            "C99.1 is on V3_RC; native scan shows C99.2 as a conductor-less plate on singleton C99_FAR",
        ),
        (
            "D25_T MEMW input is source-proven without crossing-rail overmerge",
            has_nodes(board, "D25_T", {("D7", "6"), ("D25", "11")})
            and has_nodes(board, "MEMW", {("D7", "4"), ("D29", "1")})
            and "terminates as a T" in board["nets"]["D25_T"]["src"]
            and "without a junction" in board["nets"]["D25_T"]["src"],
            "Native sheet proves D7.4 -> MEMW/D29.1; D7.5 remains on the distinct -INHIB junction",
        ),
    ]
    ok = all(result for _, result, _ in checks + boundaries)
    status = "IO DECODE GUARDED / SMALL SOURCE BOUNDARIES PENDING" if ok else "IO DECODE BOUNDARY FAILED"

    lines = [
        "# I/O decode boundary",
        "",
        "Status date: 2026-07-13.",
        "",
        f"Status: **{status}**",
        "",
        "This generated report isolates the sheet-1 I/O decode cluster.",
        "It guards the current D9 К555ИД7 decoder model and the D7/R17/C99",
        "strobe-enable path while keeping the small remaining source boundaries",
        "visible.",
        "",
        "## Command",
        "",
        "```sh",
        "python3 scripts/report_io_decode_boundary.py",
        "```",
        "",
        "## Guarded Checks",
        "",
        "| Check | Result | Evidence |",
        "| --- | --- | --- |",
    ]
    lines.extend(row([name, "PASS" if result else "FAIL", evidence]) for name, result, evidence in checks)
    lines.extend(
        [
            "",
            "## Pending Boundary Checks",
            "",
            "| Boundary | Result | Current evidence |",
            "| --- | --- | --- |",
        ]
    )
    lines.extend(row([name, "PASS" if result else "FAIL", evidence]) for name, result, evidence in boundaries)
    lines.extend(
        [
            "",
            "## Current Decode Nets",
            "",
            "| Net | Endpoints | Source note |",
            "| --- | --- | --- |",
        ]
    )
    for name in (
        "PROM_EN",
        "V3_RC",
        "C99_FAR",
        "REV",
        "BA10",
        "BA11",
        "BA12",
        "IOWR",
        "IORD",
        "D25_T",
        "CS_D10",
        "CS_D26",
        "CS_D11",
        "CS_D27",
        "CS_D54",
        "CS_D55",
        "CS_D57",
        "CS_FDC",
    ):
        net = board["nets"].get(name, {})
        lines.append(row([f"`{name}`", f"`{endpoint_text(board, name)}`", net.get("src", "-")]))

    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- D9, not D2, is the physical I/O chip-select decoder in the current",
            "  board model; this report guards that D2-as-I/O-decode is not revived.",
            "- The I/O decoder enable is the traced D7.11 -> R17/C99 -> D9.6 path,",
            "  with REV on D9.4/D9.5 and BA10..BA12 selecting the eight I/O groups.",
            "- Remaining work is now narrow: trace the independent D7.12/D7.13",
            "  boundaries, read or continuity-check C99.2, and identify the upstream",
            "  source shared by D7.5/D29.3. Native 5150x3603 geometry closes D7.4",
            "  onto MEMW/D29.1 without merging the crossed D29.3 rail. None of the",
            "  remaining boundaries should be replaced by a simulator-only guess.",
            "",
        ]
    )
    REPORT.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {REPORT.relative_to(ROOT)}")
    print(f"Status: {status}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
