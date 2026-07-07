#!/usr/bin/env python3
"""Generate the replica bring-up verification-point checklist."""
from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BOARD_JSON = ROOT / "kicad" / "juku.board.json"
REPORT = ROOT / "docs" / "replica-bringup-verification-points.md"

RISK_RE = re.compile(
    r"assumed|boundary|pending|unread|approx|owner-verify|refine|chase|mame",
    re.I,
)


def table_row(values: list[object]) -> str:
    escaped = [str(value).replace("|", "/") if value not in (None, "") else "-" for value in values]
    return "| " + " | ".join(escaped) + " |"


def endpoint_summary(nodes: list[list[str]]) -> str:
    rendered = [f"{ref}.{pin}" for ref, pin in nodes]
    if len(rendered) <= 6:
        return ", ".join(rendered)
    return ", ".join(rendered[:6]) + f", ... (+{len(rendered) - 6})"


def short(text: str, limit: int = 180) -> str:
    one_line = " ".join(text.split())
    if len(one_line) <= limit:
        return one_line
    return one_line[: limit - 3].rstrip() + "..."


def category_for(name: str, source: str) -> str:
    text = f"{name} {source}".upper()
    if name.startswith("FDC_"):
        return "FDC"
    if "SOUND" in text or "SND" in text or "SPKR" in text:
        return "sound/analog"
    if "PIT" in text or "FRAME" in text or "BAUD" in text or "CLK" in text:
        return "timing/I/O"
    if "MEM" in text or "RAM" in text or "CAS" in text or "RAS" in text or "ROE" in text:
        return "memory/decode"
    if (
        "VIDEO" in text
        or "VT" in text
        or "RF" in text
        or "SYNC" in text
        or "XTAL" in text
        or "ANALOG" in text
    ):
        return "video/analog"
    return "logic"


def action_for(category: str, name: str, source: str) -> str:
    if name in {"FDC_INTRQ", "FDC_DRQ"}:
        return "Continuity-check WD1793 pin to 8259 input before EKDOS bring-up."
    if name == "FDC_DDEN":
        return "Confirm density-control level against drive/emulator behavior."
    if category == "sound/analog":
        return "Bench-check waveform/current path with speaker disconnected first."
    if category == "video/analog":
        return "Scope/capture video or timing node during video bring-up."
    if category == "memory/decode":
        return "Probe during ROM/RAM stage; compare address/control timing to twin."
    if "owner-verify" in source.lower():
        return "Prefer owner continuity check or board measurement before relying on it."
    if "mame" in source.lower():
        return "Cross-check against hardware when the peripheral path is exercised."
    return "Verify with continuity, scope, or logic-analyzer trace during staged bring-up."


def main() -> int:
    board = json.loads(BOARD_JSON.read_text())
    rows = []
    for name, net in sorted(board["nets"].items()):
        source = net.get("src", "")
        note = net.get("note", "")
        risk_text = f"{source} {note}"
        if not RISK_RE.search(risk_text):
            continue
        category = category_for(name, risk_text)
        rows.append(
            {
                "name": name,
                "category": category,
                "nodes": net.get("nodes", []),
                "source": risk_text,
                "action": action_for(category, name, risk_text),
            }
        )

    category_counts = Counter(row["category"] for row in rows)
    status = "READY"
    lines = [
        "# Replica bring-up verification points",
        "",
        f"Status: **{status}**",
        "",
        "This report is generated from `kicad/juku.board.json`. It turns the",
        "remaining source-risk annotations into an explicit checklist for vendor",
        "preview, owner continuity sessions, and staged bring-up. It does not mark",
        "these points as independently verified; it makes the residual risks",
        "visible and actionable before manufacturing and first power-on.",
        "",
        "## Summary",
        "",
        f"- Source board JSON: `{BOARD_JSON.relative_to(ROOT)}`",
        f"- Verification-point nets: `{len(rows)}`",
        "",
        "| Category | Nets |",
        "| --- | ---: |",
    ]
    for category, count in sorted(category_counts.items()):
        lines.append(table_row([category, count]))

    lines.extend(
        [
            "",
            "## Checklist",
            "",
            "| Net | Category | Endpoints | Source risk | Bring-up action |",
            "| --- | --- | --- | --- | --- |",
        ]
    )
    for row in rows:
        lines.append(
            table_row(
                [
                    f"`{row['name']}`",
                    row["category"],
                    f"`{endpoint_summary(row['nodes'])}`",
                    short(row["source"]),
                    row["action"],
                ]
            )
        )

    lines.extend(
        [
            "",
            "## Manufacturing Disposition",
            "",
            "- These items do not block PCB fabrication: the package is socketed,",
            "  bodge-friendly, and the digital twin/CI gates cover the boot path.",
            "- Save any vendor-preview, owner-continuity, oscilloscope, or logic-analyzer",
            "  evidence against this checklist as bring-up progresses.",
            "- If a point is corrected in source, update `kicad/juku.board.json` first",
            "  and regenerate this report through the manufacturing readiness gate.",
            "",
        ]
    )
    REPORT.write_text("\n".join(lines))
    print(f"Wrote {REPORT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
