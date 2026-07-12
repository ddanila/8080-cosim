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
            "Adjacent latch chain context is modeled",
            node_in(board, "LATCH_B", "D40", "11")
            and node_in(board, "LATCH_B", "D37", "2")
            and node_in(board, "LATCH_PRE", "D37", "3")
            and node_in(board, "LATCH_PRE", "D33", "13")
            and node_in(board, "LATCH_SIG", "D33", "12")
            and node_in(board, "LATCH_SIG", "D39", "9"),
            "`LATCH_B`/`LATCH_PRE`/`LATCH_SIG` around D37/D40/D33/D39",
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
    status = "D41 STRAPS/OUTPUTS GUARDED / LD-CK SOURCES PENDING" if ok else "D41 TIMING BOUNDARY FAILED"

    lines = [
        "# D41 timing boundary",
        "",
        "Status date: 2026-07-11.",
        "",
        f"Status: **{status}**",
        "",
        "This generated report isolates the D41 ИР16 timing-chain boundary.",
        "The board model has guarded evidence for D41's two output-side",
        "uses, its fixed straps, and its two remaining timing-source boundaries.",
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
            "  stubs. LD and CK are preserved as distinct timing-bundle boundaries.",
            "- Do not infer the LD/CK remote drivers from the runnable raster model;",
            "  they still need a readable source or continuity pass.",
            "",
        ]
    )
    REPORT.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {REPORT.relative_to(ROOT)}")
    print(f"Status: {status}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
