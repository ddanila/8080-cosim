#!/usr/bin/env python3
"""Generate the replica bring-up verification-point checklist."""
from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BOARD_JSON = ROOT / "kicad" / "juku.board.json"
PCB = ROOT / "kicad" / "juku.kicad_pcb"
ROUTED_PCB = ROOT / "kicad" / "juku_routed.kicad_pcb"
REPORT = ROOT / "docs" / "replica-bringup-verification-points.md"

RISK_RE = re.compile(
    r"assumed|boundary|deferred|untraced|not traced|pending|unread|owner-verify|mame|approx|refine|dump",
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


def matching_block(text: str, start: int) -> str:
    depth = 0
    in_string = False
    escaped = False
    for pos in range(start, len(text)):
        char = text[pos]
        if in_string:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
            continue
        if char == '"':
            in_string = True
        elif char == "(":
            depth += 1
        elif char == ")":
            depth -= 1
            if depth == 0:
                return text[start : pos + 1]
    raise ValueError("unterminated S-expression")


def pcb_pin_nets(path: Path) -> dict[tuple[str, str], str]:
    text = path.read_text(errors="replace")
    found: dict[tuple[str, str], str] = {}
    pos = 0
    while True:
        start = text.find("\n\t(footprint ", pos)
        if start < 0:
            break
        block = matching_block(text, start + 1)
        pos = start + len(block) + 1
        ref = re.search(r'\(property\s+"Reference"\s+"([^"]+)"', block)
        if not ref:
            continue
        for match in re.finditer(r'\n\t\t\(pad\s+"([^"]+)"', block):
            pad_block = matching_block(block, match.start() + 3)
            net = re.search(r'\(net\s+"([^"]+)"\)', pad_block)
            if net:
                found[(ref.group(1), match.group(1))] = net.group(1)
    return found


def endpoint_coverage(board: dict, pcb_nets: dict[tuple[str, str], str]) -> dict[str, object]:
    checked = 0
    missing = []
    mismatched = []
    for name, net in sorted(board["nets"].items()):
        for ref, pin in net.get("nodes", []):
            checked += 1
            pcb_net = pcb_nets.get((ref, pin))
            if pcb_net is None:
                missing.append(f"{name}: {ref}.{pin}")
            elif pcb_net != name:
                mismatched.append(f"{ref}.{pin}: `{pcb_net}` != `{name}`")
    return {
        "checked": checked,
        "missing": missing,
        "mismatched": mismatched,
        "ok": not missing and not mismatched,
    }


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
    pcb_nets = pcb_pin_nets(PCB)
    routed_pcb_nets = pcb_pin_nets(ROUTED_PCB)
    source_coverage = endpoint_coverage(board, pcb_nets)
    routed_coverage = endpoint_coverage(board, routed_pcb_nets)
    rows = []
    pcb_checked = 0
    pcb_missing = []
    pcb_mismatched = []
    for name, net in sorted(board["nets"].items()):
        source = net.get("src", "")
        note = net.get("note", "")
        risk_text = f"{source} {note}"
        if not RISK_RE.search(risk_text):
            continue
        for ref, pin in net.get("nodes", []):
            pcb_checked += 1
            pcb_net = pcb_nets.get((ref, pin))
            if pcb_net is None:
                pcb_missing.append(f"{ref}.{pin}")
            elif pcb_net != name:
                pcb_mismatched.append(f"{ref}.{pin}: `{pcb_net}` != `{name}`")
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
    pcb_ok = not pcb_missing and not pcb_mismatched
    full_pcb_ok = bool(source_coverage["ok"] and routed_coverage["ok"])
    status = "READY" if pcb_ok and full_pcb_ok else "NOT READY"
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
        f"- Final PCB source: `{PCB.relative_to(ROOT)}`",
        f"- Routed PCB source: `{ROUTED_PCB.relative_to(ROOT)}`",
        f"- Verification-point nets: `{len(rows)}`",
        f"- Verification-point endpoints checked in PCB: `{pcb_checked}`",
        f"- PCB endpoint coverage: `{'PASS' if pcb_ok else 'FAIL'}`",
        f"- All board endpoints checked in source PCB: `{source_coverage['checked']}`",
        f"- All board endpoints checked in routed PCB: `{routed_coverage['checked']}`",
        f"- Full PCB endpoint coverage: `{'PASS' if full_pcb_ok else 'FAIL'}`",
        "",
        "| Category | Nets |",
        "| --- | ---: |",
    ]
    for category, count in sorted(category_counts.items()):
        lines.append(table_row([category, count]))

    lines.extend(
        [
            "",
            "## KiCad PCB Endpoint Coverage",
            "",
            "Every source-risk endpoint listed below is checked against the final",
            "`kicad/juku.kicad_pcb` footprint pad net assignment. This proves the",
            "fabrication source preserves the same residual-risk connectivity as",
            "`kicad/juku.board.json`; it does not prove the historical assumption",
            "behind a risk note.",
            "",
            "| Check | Result | Evidence |",
            "| --- | --- | --- |",
            table_row(["Risk endpoints present on PCB pads", "PASS" if not pcb_missing else "FAIL", f"{pcb_checked - len(pcb_missing)}/{pcb_checked} matched a footprint pad net"]),
            table_row(["Risk endpoint net names match board JSON", "PASS" if not pcb_mismatched else "FAIL", f"{pcb_checked - len(pcb_mismatched)}/{pcb_checked} net names matched"]),
        ]
    )
    if pcb_missing:
        lines.extend(["", "Missing PCB pad-net endpoints:"])
        lines.extend(f"- `{item}`" for item in pcb_missing)
    if pcb_mismatched:
        lines.extend(["", "Mismatched PCB pad-net endpoints:"])
        lines.extend(f"- {item}" for item in pcb_mismatched)

    lines.extend(
        [
            "",
            "## Full Board Endpoint Coverage",
            "",
            "Every modeled `kicad/juku.board.json` endpoint is also checked against",
            "the generated source PCB and the routed fabrication PCB. This is a",
            "fabrication-source coverage gate, not a historical-source proof.",
            "",
            "| PCB | Present | Matching net names | Result |",
            "| --- | ---: | ---: | --- |",
            table_row([
                f"`{PCB.relative_to(ROOT)}`",
                f"{source_coverage['checked'] - len(source_coverage['missing'])}/{source_coverage['checked']}",
                f"{source_coverage['checked'] - len(source_coverage['missing']) - len(source_coverage['mismatched'])}/{source_coverage['checked']}",
                "PASS" if source_coverage["ok"] else "FAIL",
            ]),
            table_row([
                f"`{ROUTED_PCB.relative_to(ROOT)}`",
                f"{routed_coverage['checked'] - len(routed_coverage['missing'])}/{routed_coverage['checked']}",
                f"{routed_coverage['checked'] - len(routed_coverage['missing']) - len(routed_coverage['mismatched'])}/{routed_coverage['checked']}",
                "PASS" if routed_coverage["ok"] else "FAIL",
            ]),
        ]
    )
    for label, coverage in ((PCB.relative_to(ROOT), source_coverage), (ROUTED_PCB.relative_to(ROOT), routed_coverage)):
        if coverage["missing"]:
            lines.extend(["", f"Missing endpoints in `{label}`:"])
            lines.extend(f"- `{item}`" for item in coverage["missing"])
        if coverage["mismatched"]:
            lines.extend(["", f"Mismatched endpoints in `{label}`:"])
            lines.extend(f"- {item}" for item in coverage["mismatched"])

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
