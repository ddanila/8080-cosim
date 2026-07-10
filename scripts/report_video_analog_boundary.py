#!/usr/bin/env python3
"""Generate the sheet-2 analog video/RF handoff boundary report."""
from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BOARD = ROOT / "kicad" / "juku.board.json"
REPORT = ROOT / "docs" / "video-analog-boundary.md"

ANALOG_NETS = (
    "D34_SYNC",
    "D34_SIG",
    "VT2_BASE",
    "VIDEO_OUT",
    "SOUND_CLAMP",
    "SND_MIX",
    "VT3_BASE",
    "RF_RAIL",
    "VT3_E",
    "VT4_B",
    "RF_TANK",
    "HF_OUT",
    "VT4_E",
)

REQUIRED_NODES = {
    "D34_SYNC": {("D34", "8"), ("R62", "1")},
    "D34_SIG": {("D34", "11"), ("R63", "1"), ("R69", "1")},
    "VT2_BASE": {("R62", "2"), ("R63", "2"), ("R64", "1"), ("VT2", "2")},
    "VIDEO_OUT": {("VT2", "1"), ("R65", "1"), ("X7", "1")},
    "SOUND_CLAMP": {("R66", "2"), ("VD3", "2"), ("R67", "1")},
    "SND_MIX": {("R67", "2"), ("R68", "1")},
    "VT3_BASE": {("R68", "2"), ("R69", "2"), ("R70", "2"), ("R71", "1"), ("C13", "1"), ("VT3", "2")},
    "RF_RAIL": {("VT3", "3"), ("C9", "2"), ("R72", "2"), ("C10", "1"), ("R73", "1"), ("C11", "1")},
    "VT3_E": {("VT3", "1"), ("R74", "1")},
    "VT4_B": {("R73", "2"), ("VT4", "2"), ("C10", "2")},
    "RF_TANK": {("VT4", "3"), ("C11", "2"), ("C12", "1"), ("L1", "1"), ("R76", "1"), ("C15", "1")},
    "HF_OUT": {("R76", "2"), ("R77", "1"), ("X6", "1")},
    "VT4_E": {("VT4", "1"), ("R75", "1"), ("C14", "1"), ("C15", "2")},
}


def load_board() -> dict:
    return json.loads(BOARD.read_text(encoding="utf-8"))


def chip(board: dict, ref: str) -> dict:
    for item in board["chips"]:
        if item.get("ref") == ref:
            return item
    raise KeyError(ref)


def nodes(board: dict, name: str) -> set[tuple[str, str]]:
    return {tuple(node) for node in board["nets"].get(name, {}).get("nodes", [])}


def endpoint_text(board: dict, name: str) -> str:
    rendered = [f"{ref}.{pin}" for ref, pin in sorted(nodes(board, name))]
    return ", ".join(rendered) if rendered else "-"


def row(values: list[object]) -> str:
    return "| " + " | ".join(str(value).replace("|", "/") for value in values) + " |"


def has_pin(board: dict, ref: str, pin: str) -> bool:
    return any((ref, pin) in nodes(board, name) for name in board["nets"])


def main() -> int:
    board = load_board()

    guarded_checks = []
    for name in ANALOG_NETS:
        required = REQUIRED_NODES[name]
        guarded_checks.append(
            (
                f"`{name}` carries the traced analog-corner endpoints",
                required <= nodes(board, name),
                f"`{endpoint_text(board, name)}`",
            )
        )

    package_checks = [
        (
            "VT2 video emitter follower is modeled",
            chip(board, "VT2").get("type") == "Q_TO92"
            and "video emitter follower" in chip(board, "VT2").get("prov", {}).get("pins", ""),
            "VT2 provenance: sheet-2 analog corner",
        ),
        (
            "VT3 RF/video stage is modeled",
            chip(board, "VT3").get("type") == "Q_TO92"
            and "RF/video transistor stage" in chip(board, "VT3").get("prov", {}).get("pins", ""),
            "VT3 provenance: sheet-2 analog corner",
        ),
        (
            "VT4 RF oscillator/output stage is modeled",
            chip(board, "VT4").get("type") == "Q_TO92"
            and "RF oscillator/output transistor stage" in chip(board, "VT4").get("prov", {}).get("pins", ""),
            "VT4 provenance: sheet-2 analog corner",
        ),
        (
            "VIDEO_OUT connector maps to X7",
            ("X7", "1") in nodes(board, "VIDEO_OUT") and ("X7", "2") in nodes(board, "GND"),
            "X7.1 signal / X7.2 return",
        ),
        (
            "HF_OUT connector maps to X6",
            ("X6", "1") in nodes(board, "HF_OUT") and ("X6", "2") in nodes(board, "GND"),
            "X6.1 signal / X6.2 return",
        ),
    ]

    boundary_checks = [
        (
            "Analog-corner SOUND injection remains source-boundary only",
            not has_pin(board, "R66", "1"),
            "R66.1 source is still not netted; do not merge with beeper SOUND without source evidence",
        ),
        (
            "Composite/RF electrical levels remain bench-only",
            True,
            "transistor bias, RF tank tuning, and output level/current are not digital-netlist facts",
        ),
        (
            "X6/X7 connector identity remains assembly-drawing bounded",
            "board 7.102.100; .158 delta possible" in board["nets"]["VIDEO_OUT"]["src"]
            and "board 7.102.100; .158 delta possible" in board["nets"]["HF_OUT"]["src"],
            "connector labels are guarded but need bring-up/photo confirmation for the .158 board",
        ),
    ]

    ok = all(result for _, result, _ in guarded_checks + package_checks + boundary_checks)
    status = "ANALOG VIDEO/RF HANDOFF GUARDED / BENCH MEASUREMENT PENDING" if ok else "ANALOG VIDEO/RF HANDOFF FAILED"

    lines = [
        "# Video analog boundary",
        "",
        "Status date: 2026-07-10.",
        "",
        f"Status: **{status}**",
        "",
        "This generated report isolates the sheet-2 analog video, RF, and",
        "analog-corner sound-mix handoff. It guards the traced board endpoints",
        "that feed the composite-video connector and RF output while keeping",
        "electrical levels, RF tuning, and the unresolved R66.1 source as",
        "bring-up or source-read boundaries.",
        "",
        "## Command",
        "",
        "```sh",
        "python3 scripts/report_video_analog_boundary.py",
        "```",
        "",
        "## Guarded Net Checks",
        "",
        "| Check | Result | Evidence |",
        "| --- | --- | --- |",
    ]
    lines.extend(row([name, "PASS" if result else "FAIL", evidence]) for name, result, evidence in guarded_checks)

    lines.extend(
        [
            "",
            "## Package / Connector Checks",
            "",
            "| Check | Result | Evidence |",
            "| --- | --- | --- |",
        ]
    )
    lines.extend(row([name, "PASS" if result else "FAIL", evidence]) for name, result, evidence in package_checks)

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
            "## Current Analog-Corner Nets",
            "",
            "| Net | Endpoints | Source note |",
            "| --- | --- | --- |",
        ]
    )
    for name in ANALOG_NETS:
        net = board["nets"].get(name, {})
        lines.append(row([f"`{name}`", f"`{endpoint_text(board, name)}`", net.get("src", "-")]))

    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- The digital video-readout guards prove byte-to-pixel behavior; this report",
            "  is only the analog board handoff from D34 through VT2/VT3/VT4 and X6/X7.",
            "- `VIDEO_OUT` and `HF_OUT` are routed to the modeled connectors, but real",
            "  composite/RF amplitude, polarity margins, and tank adjustment still need",
            "  bench capture during bring-up.",
            "- The analog-corner `SOUND_CLAMP` path is not the same as the already guarded",
            "  beeper speaker driver. R66.1 remains unnetted until source evidence proves",
            "  the analog sound-mix input.",
            "",
        ]
    )

    REPORT.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {REPORT.relative_to(ROOT)}")
    print(f"Status: {status}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
