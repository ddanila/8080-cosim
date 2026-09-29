#!/usr/bin/env python3
"""Generate the sheet-1 I/O decode boundary report."""
from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BOARD = ROOT / "kicad" / "juku.board.json"
HDL_TOP = ROOT / "hdl" / "juku_top.v"
LVS_MAP = ROOT / "sync" / "map.json"
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
    hdl_top = HDL_TOP.read_text(encoding="utf-8")
    lvs_map = json.loads(LVS_MAP.read_text(encoding="utf-8"))
    d9 = chip(board, "D9")
    d7 = chip(board, "D7")
    d5 = chip(board, "D5")
    d105 = chip(board, "D105")
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
            "Runnable HDL and LVS use the physical D9 identity and traced pins",
            "io_dec138 U_D9" in hdl_top
            and ".a(BA[10]), .b(BA[11]), .c(BA[12])" in hdl_top
            and ".g1(d9_g1_w), .g2a_n(rev), .g2b_n(rev)" in hdl_top
            and lvs_map.get("instances", {}).get("D9") == "U_D9"
            and "U_DID7" not in hdl_top,
            "U_D9: BA10/11/12, G1=V3_RC, G2A/G2B=REV; no placeholder refdes",
        ),
        (
            "D7 strobe-NAND output reaches the R17/C99 D9.G1 RC node",
            has_nodes(board, "PROM_EN", {("D7", "11"), ("D7", "13"), ("R17", "2")})
            and has_nodes(board, "V3_RC", {("R17", "1"), ("C99", "1"), ("D9", "6")})
            and board["nets"]["PROM_EN"].get("source_risk") is False
            and board["nets"]["V3_RC"].get("source_risk") is False,
            "`PROM_EN` -> `V3_RC`",
        ),
        (
            "D7 first-gate SYNC/feedback topology is source-proven",
            has_nodes(board, "SYNC", {("D1", "19"), ("D7", "12")})
            and has_nodes(board, "PROM_EN", {("D7", "11"), ("D7", "13")})
            and "feedback strobe" in board["nets"]["PROM_EN"]["src"],
            "D1.19 SYNC -> D7.12; D7.11 -> D7.13 feedback before R17",
        ),
        (
            "D7 second-gate provenance preserves the owner-disproved D29.5 split",
            "disproves the former D7.3-to-D29.5 interpretation" in d7.get("prov", {}).get("pins", "")
            and "AMW_N/D29.5" not in d7.get("prov", {}).get("pins", "")
            and set(nodes(board, "AMW_N")) == {("D7", "3"), ("D29", "2")}
            and has_nodes(board, "IOWR", {("D29", "5"), ("D105", "3")}),
            "exact .009 joins D7.3 to D29.2; owner continuity separates D29.5 on qualified IOWR",
        ),
        (
            "D9 region-enable inputs are tied to REV",
            has_nodes(board, "REV", {("D6", "10"), ("D9", "4"), ("D9", "5"), ("R13", "2")})
            and board["nets"]["REV"].get("source_risk") is False,
            "native sheet-1 code-2 branch: D6.10/R13.2 -> D9.4/D9.5",
        ),
        (
            "D9 select inputs are BA10..BA12",
            has_nodes(board, "BA10", {("D9", "1")})
            and has_nodes(board, "BA11", {("D9", "2")})
            and has_nodes(board, "BA12", {("D9", "3")}),
            "`BA10`, `BA11`, `BA12` into D9.A/B/C",
        ),
        (
            "D7 fourth-gate inputs are wired to raw IOWR_N/IORD_N",
            has_nodes(board, "IOWR_RAW_N", {("D5", "27"), ("D7", "10")})
            and has_nodes(board, "IORD", {("D7", "9"), ("D11", "13"), ("D26", "5"), ("D27", "5")}),
            "`IOWR_RAW_N`/`IORD` inputs",
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
            and has_nodes(board, "FDC_CS_N", {("D9", "7"), ("D94", "15"), ("D93", "3")})
            and has_nodes(board, "FDC_RE_N", {("D94", "3"), ("D93", "4")})
            and has_nodes(board, "FDC_CS_N", {("D94", "15"), ("D93", "3")})
            and has_nodes(board, "D94_D1_D99_A2N", {("D94", "2"), ("D99", "9"), ("R89", "1")})
            and has_nodes(board, "FDC_WE_N", {("D94", "4"), ("D93", "2")}),
            "`CS_D10`..`FDC_CS_N`; exact .009 CS7 path D9.7→D94.15/D93.3, owner-confirmed D94.15-D93.3, and corrected D94.2-D99.9/R89 node",
        ),
        (
            "D25 bus turnaround handoff is guarded",
            has_nodes(board, "D25_T", {("D7", "6"), ("D25", "11")})
            and board["nets"]["D25_T"].get("source_risk") is False,
            "`D25_T`: D7.6 -> D25.11",
        ),
    ]
    boundaries = [
        (
            "D7 fourth-gate strobe inputs are source-proven",
            d7.get("pins", {}).get("9") == "A4"
            and d7.get("pins", {}).get("10") == "B4"
            and "owner continuity 2026-07-19" in board["nets"]["IOWR_RAW_N"]["src"]
            and "full-resolution" in board["nets"]["IORD"]["src"],
            "IORD_N/IOWR_N are on D7.9/D7.10; raw D5.27 is distinct from qualified D105.3",
        ),
        (
            "C99 far plate uses the exact-sheet ground symbol",
            has_nodes(board, "V3_RC", {("C99", "1")})
            and has_nodes(board, "GND", {("C99", "2")})
            and "C99_FAR" not in board["nets"]
            and not any(ref == "C99" and pin == "2" for ref, pin in nodes(board, "V3_RC")),
            "C99.1 is on V3_RC; C99.2 ground bar matches R16's ground symbol in the exact .009 sheet",
        ),
        (
            "D25_T MEMW input is source-proven without crossing-rail overmerge",
            has_nodes(board, "D25_T", {("D7", "6"), ("D25", "11")})
            and has_nodes(board, "MEMW", {("D7", "4"), ("D29", "8")})
            and "terminates as a T" in board["nets"]["D25_T"]["src"]
            and "without a junction" in board["nets"]["D25_T"]["src"],
            "Native sheet proves D7.4 -> MEMW/D29.8; D7.5 remains on the distinct -INHIB junction",
        ),
        (
            "D7.8 I/O-cycle qualifier and D105.3 qualified /WR are owner-closed",
            set(nodes(board, "IO_CYCLE_H")) == {("D7", "8"), ("D105", "1"), ("D6", "15")}
            and has_nodes(board, "IOWR", {("D105", "3"), ("D94", "13"), ("D29", "5")})
            and set(nodes(board, "IOWR_RAW_N")) == {("D5", "27"), ("D7", "10")}
            and "output3 is the qualified active-low peripheral IOWR rail" in d105.get("prov", {}).get("pins", "")
            and "output3 remains a boundary" not in d105.get("prov", {}).get("pins", ""),
            "Owner continuity 2026-07-19 separates raw D5.27 from qualified D105.3 and closes D7.8 to D105.1/D6.15",
        ),
    ]
    ok = all(result for _, result, _ in checks + boundaries)
    status = "IO DECODE GUARDED / SMALL SOURCE BOUNDARIES PENDING" if ok else "IO DECODE BOUNDARY FAILED"

    lines = [
        "# I/O decode boundary",
        "",
        "Status date: 2026-07-22.",
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
        "SYNC",
        "V3_RC",
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
        "FDC_CS_N",
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
            "- The exact `.009` assembly view `PXL_20260711_114556899.jpg` places a",
            "  horizontal C99 immediately below D9 and left of upright R17. Both",
            "  May close-up `201933909` and overlapping July component views",
            "  (`200411500` and `200415237`) show no fitted C99 body. A plausible",
            "  bare horizontal pair repeats below D9 and left of R17: May joints near",
            "  `(1440,1990)`/`(1600,1990)`, July joints near `(2508,1782)`/",
            "  `(2680,1782)`. The right joint visibly links to R17's lower physical",
            "  lead; the upper lead runs under D9 without a visible numbered pin",
            "  junction. Corrected native D9 package anchors project the July C99",
            "  left/right candidates near `(3038,1497)`/`(2868,1497)` in solder tile",
            "  `200525009`, within about 5–7 px of separate joints `(3040,1492)`/",
            "  `(2875,1495)`. A third joint near `(2818,1515)` matches R17 lower",
            "  and has a short visible B.Cu link to the right C99 candidate. The",
            "  older 40–55 px mismatch came from retired D9 component anchors.",
            "  The left solder candidate has an uninterrupted B.Cu route to the",
            "  third contact of D2's reflected left row, pin14, grounded by exact",
            "  `.009` sheet 1. Three-feature geometry strongly favors the pair, but",
            "  front-to-back same-hole identity and population need confirmation;",
            "  owner ground continuity has not been metered.",
            "  See `ref/photos/juku-pcb-2/c99-assembly-photo-review.json`.",
            "- Remaining work is now narrow: identify the C99 physical landing and",
            "  identify the upstream source shared by D7.5/D29.3. Native 5150x3603",
            "  geometry closes D7.12 onto SYNC, D7.13 onto its pin11 feedback node, and D7.4",
            "  onto MEMW/D29.8 without merging the crossed D29.3 rail. None of the",
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
