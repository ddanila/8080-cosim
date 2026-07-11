#!/usr/bin/env python3
"""Generate the board-fidelity gap ledger from board JSON provenance."""

from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BOARD = ROOT / "kicad" / "juku.board.json"
REPORT = ROOT / "docs" / "board-fidelity-gap-ledger.md"

RISK_RE = re.compile(
    r"assumed|boundar(?:y|ies)|deferred|untraced|not traced|pending|unread|await|owner-verify|mame|approx|refine|dump|source confirmation|requires? (?:source|continuity)",
    re.I,
)
FDC_SUPPORT_REFS = {"D28", "D95", "D96", "D97", "D98", "D99", "D101", "D102", "D106"}


def table_row(values: list[object]) -> str:
    return "| " + " | ".join(str(value).replace("|", "/") for value in values) + " |"


def short(text: str, limit: int = 160) -> str:
    compact = " ".join(str(text).split())
    if len(compact) <= limit:
        return compact
    return compact[: limit - 3].rstrip() + "..."


def chip_prov_text(chip: dict) -> str:
    prov = chip.get("prov", {})
    prov_type = str(prov.get("type", "")).strip()
    parts = []
    for key in ("refdes", "pins", "note", "value"):
        value = str(prov.get(key, "")).strip()
        if value == prov_type:
            continue
        if value and value not in parts:
            parts.append(value)
    return " ".join(parts)


def category_for_chip(chip: dict, text: str) -> str:
    ref = str(chip.get("ref", ""))
    ctype = str(chip.get("type", ""))
    prov_type = str(chip.get("prov", {}).get("type", "missing"))
    upper = f"{ref} {ctype} {text}".upper()
    if prov_type == "missing":
        return "missing provenance"
    if ref in FDC_SUPPORT_REFS:
        return "FDC owner-continuity"
    if "UNPOPULATED" in upper:
        return "unpopulated sockets"
    if "D2" == ref or "D94" == ref or re.search(r"\bPROM\b|РТ4|РЕ3", upper):
        return "PROM truth"
    if "ANALOG" in upper or ref.startswith(("VT", "VD", "L")):
        return "analog/source"
    if ref.startswith("C") and "PER-POSITION/REFDES" in upper:
        return "placement/refdes"
    if ref.startswith("C") or "DECOUPLING" in upper:
        return "placement/value"
    if "VIDEO" in upper or "MUX" in upper or "TIMING" in upper:
        return "video/timing"
    if "CONN" in ctype or ref.startswith("X"):
        return "connector boundary"
    return "logic/source"


def category_for_net(name: str, text: str) -> str:
    upper = f"{name} {text}".upper()
    if name.startswith("FDC_"):
        return "FDC owner-continuity"
    if "PROM" in upper or "D6" in upper or "D2" in upper or "D94" in upper:
        return "PROM/decode"
    if "VIDEO" in upper or "SYNC" in upper or "RF" in upper or "ANALOG" in upper:
        return "video/analog"
    if "SOUND" in upper or "SND" in upper or "SPKR" in upper:
        return "sound/analog"
    if "MEM" in upper or "RAM" in upper or "RAS" in upper or "CAS" in upper:
        return "memory/timing"
    if "PIT" in upper or "CLK" in upper or "BAUD" in upper:
        return "clock/I/O"
    return "logic/source"


def nodes_summary(nodes: list[list[str]]) -> str:
    rendered = [f"{ref}.{pin}" for ref, pin in nodes]
    if len(rendered) <= 6:
        return ", ".join(rendered)
    return ", ".join(rendered[:6]) + f", ... (+{len(rendered) - 6})"


def netted_pins_by_ref(board: dict) -> dict[str, set[str]]:
    netted: dict[str, set[str]] = defaultdict(set)
    for net in board["nets"].values():
        for ref, pin in net.get("nodes", []):
            netted[str(ref)].add(str(pin))
    return netted


def no_connect_pins_by_ref(board: dict) -> dict[str, set[str]]:
    no_connects: dict[str, set[str]] = defaultdict(set)
    for ref, pin in board.get("no_connects", []):
        no_connects[str(ref)].add(str(pin))
    return no_connects


def unnetted_functional_pins(
    chip: dict,
    netted: dict[str, set[str]],
    no_connects: dict[str, set[str]],
) -> list[str]:
    ref = str(chip.get("ref", ""))
    pins = chip.get("pins", {})
    used = netted.get(ref, set())
    intentional_nc = no_connects.get(ref, set())
    missing = []
    def pin_sort_key(item: tuple[str, object]) -> object:
        pin = str(item[0])
        return int(pin) if pin.isdigit() else pin

    for pin, signal in sorted(pins.items(), key=pin_sort_key):
        if str(pin) not in used and str(pin) not in intentional_nc:
            missing.append(f"{pin}:{signal}")
    return missing


def main() -> int:
    board = json.loads(BOARD.read_text(encoding="utf-8"))
    netted = netted_pins_by_ref(board)
    no_connects = no_connect_pins_by_ref(board)
    chip_prov_counts = Counter(str(chip.get("prov", {}).get("type", "missing")) for chip in board["chips"])
    chip_gap_rows: list[dict[str, object]] = []
    for chip in board["chips"]:
        text = chip_prov_text(chip)
        prov_type = str(chip.get("prov", {}).get("type", "missing"))
        if prov_type != "missing" and not RISK_RE.search(text):
            continue
        chip_gap_rows.append(
            {
                "ref": chip.get("ref", "-"),
                "type": chip.get("type", "-"),
                "category": category_for_chip(chip, text),
                "prov_type": prov_type,
                "note": text or "no provenance block",
                "unnetted": unnetted_functional_pins(chip, netted, no_connects),
            }
        )

    net_gap_rows: list[dict[str, object]] = []
    for name, net in board["nets"].items():
        text = f"{net.get('src', '')} {net.get('note', '')}"
        if not RISK_RE.search(text):
            continue
        net_gap_rows.append(
            {
                "name": name,
                "category": category_for_net(name, text),
                "nodes": net.get("nodes", []),
                "note": text,
            }
        )

    chip_categories = Counter(str(row["category"]) for row in chip_gap_rows)
    net_categories = Counter(str(row["category"]) for row in net_gap_rows)
    status = "BOARD FIDELITY GAPS CATALOGED"

    grouped_chips: dict[str, list[dict[str, object]]] = defaultdict(list)
    for row in chip_gap_rows:
        grouped_chips[str(row["category"])].append(row)

    lines = [
        "# Board fidelity gap ledger",
        "",
        f"Status: **{status}**",
        "",
        "This generated ledger records the remaining board-fidelity surfaces that",
        "are explicit in `kicad/juku.board.json`: chip-level provenance that is",
        "still assumed, boundary-only, deferred, untraced, or dump-dependent, and",
        "net-level source risks already carried into the bring-up checklist. It",
        "is not a release decision by itself; its P0 rows feed `PLAN.md` and",
        "prevent current gaps from hiding behind a green endpoint-coverage gate.",
        "",
        "## Command",
        "",
        "```sh",
        "python3 scripts/report_board_fidelity_gap_ledger.py",
        "```",
        "",
        "## Summary",
        "",
        f"- Board JSON: `{BOARD.relative_to(ROOT)}`",
        f"- Chips modeled: `{len(board['chips'])}`",
        f"- Nets modeled: `{len(board['nets'])}`",
        f"- Chip-level fidelity gaps: `{len(chip_gap_rows)}`",
        f"- Net-level source-risk gaps: `{len(net_gap_rows)}`",
        f"- Documented intentional no-connect pins: `{sum(map(len, no_connects.values()))}`",
        "",
        "## Chip Provenance Types",
        "",
        "| Provenance type | Chips |",
        "| --- | ---: |",
    ]
    for key, count in sorted(chip_prov_counts.items()):
        lines.append(table_row([key, count]))

    lines.extend(["", "## Gap Categories", "", "| Category | Chip gaps | Net gaps |", "| --- | ---: | ---: |"])
    for category in sorted(set(chip_categories) | set(net_categories)):
        lines.append(table_row([category, chip_categories.get(category, 0), net_categories.get(category, 0)]))

    lines.extend(
        [
            "",
            "## Chip-Level Gaps",
            "",
            "These are package/source/provenance gaps, not necessarily routed-copper",
            "failures. Large repeated groups, such as unpopulated DRAM sockets and",
            "decoupling capacitors, are still listed because they affect faithful",
            "parts placement and Tier-3 reproduction.",
        ]
    )
    for category in sorted(grouped_chips):
        rows = grouped_chips[category]
        lines.extend(["", f"### {category}", "", "| Ref | Type | Provenance | Note |", "| --- | --- | --- | --- |"])
        for row in sorted(rows, key=lambda item: str(item["ref"])):
            lines.append(table_row([f"`{row['ref']}`", f"`{row['type']}`", row["prov_type"], short(str(row["note"]))]))

    pin_gap_rows = [
        row
        for row in chip_gap_rows
        if row["unnetted"] and str(row["category"]) not in {"placement/refdes", "placement/value"}
    ]
    if pin_gap_rows:
        lines.extend(
            [
                "",
                "## Unnetted Functional Pins",
                "",
                "The full PCB endpoint coverage gate checks every modeled net endpoint,",
                "but it cannot check package pins that are still deliberately absent",
                "from `kicad/juku.board.json` nets. These rows expose the remaining",
                "functional pins on non-placement chip gaps that still need scan,",
                "continuity, PROM-dump, or implementation evidence before the board",
                "model is historical-source-complete.",
                "",
                "| Ref | Category | Unnetted modeled pins |",
                "| --- | --- | --- |",
            ]
        )
        for row in sorted(pin_gap_rows, key=lambda item: str(item["ref"])):
            lines.append(
                table_row(
                    [
                        f"`{row['ref']}`",
                        row["category"],
                        "`" + ", ".join(str(item) for item in row["unnetted"]) + "`",
                    ]
                )
            )

    if no_connects:
        lines.extend(
            [
                "",
                "## Documented Intentional No-Connects",
                "",
                "These package pins are visibly unused in the authoritative schematic.",
                "They are excluded from the unnetted-functional-pin list and emitted as",
                "explicit KiCad schematic no-connect markers.",
                "",
                "| Ref | Pins |",
                "| --- | --- |",
            ]
        )
        for ref in sorted(no_connects):
            pins = sorted(no_connects[ref], key=lambda pin: int(pin) if pin.isdigit() else pin)
            lines.append(table_row([f"`{ref}`", "`" + ", ".join(pins) + "`"] ))

    lines.extend(
        [
            "",
            "## Net-Level Source Risks",
            "",
            "This mirrors the net-risk surface used by",
            "`docs/replica-bringup-verification-points.md`, but keeps it in the",
            "same fidelity ledger as the chip provenance gaps.",
            "",
            "| Net | Category | Endpoints | Source risk |",
            "| --- | --- | --- | --- |",
        ]
    )
    for row in sorted(net_gap_rows, key=lambda item: str(item["name"])):
        lines.append(
            table_row(
                [
                    f"`{row['name']}`",
                    row["category"],
                    f"`{nodes_summary(row['nodes'])}`",
                    short(str(row["note"])),
                ]
            )
        )

    lines.extend(
        [
            "",
            "## Automatic Closure Rule",
            "",
            "- If a gap can be closed from existing scans/docs/code, update",
            "  `kicad/juku.board.json` first, then regenerate this report and the",
            "  manufacturing readiness packet.",
            "- If a gap depends on PROM contents, hidden routing, owner continuity,",
            "  analog measurement, or vendor/order evidence, keep it listed here",
            "  until that stronger evidence exists.",
            "- Endpoint coverage remains necessary but not sufficient: it proves the",
            "  PCB preserves modeled connectivity, while this ledger records where",
            "  the model is still not fully historical-source-proven.",
            "",
        ]
    )

    REPORT.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {REPORT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
