#!/usr/bin/env python3
"""Inventory the exact main-board release evidence without approving fabrication."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
JSON_OUT = ROOT / "docs/replica-release-evidence-manifest.json"
MD_OUT = ROOT / "docs/replica-release-evidence-package.md"

SOURCES = [
    "kicad/juku.board.json",
    "kicad/juku.kicad_sch",
    "kicad/juku.kicad_pcb",
    "kicad/juku_routed.kicad_pcb",
    "kicad/juku_routed_candidate.kicad_pcb",
]
REPORTS = [
    ("Fidelity", "docs/board-fidelity-gap-ledger.md"),
    ("Owner checks", "docs/owner-measurement-shortlist.md"),
    ("BOM", "docs/replica-dual-config-bom.md"),
    ("Sourcing", "docs/replica-sourcing-readiness.md"),
    ("ERC and parity", "docs/main-board-erc-parity.md"),
    ("PPI orientation", "docs/ppi-orientation-audit.md"),
    ("X8 electrolytic geometry", "docs/x8-electrolytic-footprint-audit.md"),
    ("Factory wire construction", "docs/factory-wire-route-fidelity.md"),
    ("DRC disposition", "docs/replica-fab-drc-disposition.md"),
    ("Power trace", "docs/replica-power-trace-readiness.md"),
    ("Package geometry", "docs/replica-package-geometry-readiness.md"),
    ("Bring-up coverage", "docs/replica-bringup-verification-points.md"),
    ("Order readiness", "fab/gerbers/order-readiness.md"),
    ("External Gerber review", "fab/gerbers/external-gerber-review.md"),
    ("Review waivers", "fab/gerbers/review-waivers.md"),
    ("Fabrication inventory", "fab/gerbers/fab-readiness.md"),
    ("Manufacturing", "docs/replica-manufacturing-readiness.md"),
    ("Upload procedure", "docs/replica-order-upload-runbook.md"),
    ("Order evidence", "docs/replica-order-evidence-template.md"),
    ("First article", "docs/replica-first-article-record.md"),
]
ZIP = "fab/gerbers/upload/juku-replica-gerbers-drill.zip"
RELEASE_EXPECTED = {
    "Sourcing": "SOURCING READY",
    "ERC and parity": "READY",
    "PPI orientation": "READY",
    "X8 electrolytic geometry": "READY",
    "Factory wire construction": "FACTORY WIRE CONSTRUCTION PRESERVED",
    "DRC disposition": "READY",
    "Power trace": "READY",
    "Package geometry": "READY",
    "Bring-up coverage": "DESIGN RELEASE RISKS CLOSED",
    "Order readiness": "RELEASED FOR ORDER",
    "External Gerber review": "READY",
    "Review waivers": "ACCEPTED",
    "Manufacturing": "RELEASED FOR UPLOAD",
    "Upload procedure": "PACKAGE VERIFIED / DESIGN RELEASE SEPARATE",
    "Order evidence": "READY FOR RELEASED ORDER RECORD",
}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def status(path: Path) -> str:
    if not path.is_file():
        return "MISSING"
    match = re.search(r"^Status:\s*\*\*(.*?)\*\*", path.read_text(), re.M)
    return match.group(1) if match else "NO STATUS FIELD"


def display_hash(value: str | None) -> str:
    return f"`{value}`" if value else "-"


def display_report_link(name: str, path: str, present: bool) -> str:
    if not present:
        return name
    target = Path(path).name if path.startswith("docs/") else "../" + path
    return f"[{name}]({target})"


def bom_counts() -> dict[str, int]:
    with (ROOT / "docs/replica-dual-config-bom.csv").open(newline="") as f:
        rows = list(csv.DictReader(f))
    return {
        "lines": len(rows),
        "positions": sum(int(r["board_positions"]) for r in rows),
        "populate_now": sum(int(r["populate_now"]) for r in rows),
        "leave_empty": sum(int(r["leave_empty"]) for r in rows),
    }


def build() -> tuple[str, str]:
    source = {p: sha(ROOT / p) for p in SOURCES}
    reports = {name: {"path": p,
                      "sha256": sha(ROOT / p) if (ROOT / p).is_file() else None,
                      "status": status(ROOT / p)}
               for name, p in REPORTS}
    bom = bom_counts()
    modeled_positions = len(json.loads((ROOT / SOURCES[0]).read_text())["chips"])
    if bom["positions"] != modeled_positions or (
        bom["populate_now"] + bom["leave_empty"] != bom["positions"]
    ):
        raise SystemExit(
            f"BOM census differs from board model: {bom}, modeled positions={modeled_positions}"
        )
    bom_report = (ROOT / "docs/replica-dual-config-bom.md").read_text()
    summary_labels = {
        "positions": "Board component positions",
        "populate_now": "Populate for current functional .009 build",
        "leave_empty": "Do not populate now (empty/DNP/pending)",
        "lines": "Unique BOM lines",
    }
    for key, label in summary_labels.items():
        match = re.search(rf"^- {re.escape(label)}: (\d+)$", bom_report, re.M)
        if not match or int(match.group(1)) != bom[key]:
            raise SystemExit(f"BOM report summary differs from CSV: {label}")
    bringup = (ROOT / "docs/replica-bringup-verification-points.md").read_text()
    declared = re.search(r"Source board JSON SHA-256: `([0-9a-f]{64})`", bringup)
    bringup_current = bool(declared and declared.group(1) == source[SOURCES[0]])
    manufacturing = (ROOT / "docs/replica-manufacturing-readiness.md").read_text()
    routed_declared = re.search(
        r"The current routed board is\s*`([0-9a-f]{64})`", manufacturing
    )
    manufacturing_current = bool(
        routed_declared and routed_declared.group(1) == source[SOURCES[3]]
    )
    upload_exists = (ROOT / ZIP).is_file()
    hold_reasons = [f"{name}: {reports[name]['status']} (requires {expected})"
                    for name, expected in RELEASE_EXPECTED.items()
                    if reports[name]["status"] != expected]
    with (ROOT / "docs/main-board-unresolved-endpoints.csv").open(newline="") as f:
        unresolved = list(csv.DictReader(f))
    if unresolved:
        hold_reasons.insert(0, f"{len(unresolved)} unresolved singleton endpoints require evidence-backed disposition")
    inventory = (ROOT / "fab/gerbers/fab-readiness.md").read_text()
    if "Fabrication-file inventory gate: **PASS**" not in inventory:
        hold_reasons.append("fabrication-file inventory gate has not passed")
    if not bringup_current:
        hold_reasons.append("tracked bring-up report does not match the current board JSON SHA256")
    if not manufacturing_current:
        hold_reasons.append("tracked manufacturing report does not identify the current routed PCB SHA256")
    if not upload_exists:
        hold_reasons.append("current Gerber/drill upload ZIP is absent")
    decision = "DESIGN HOLD" if hold_reasons else "EVIDENCE COMPLETE / OWNER APPROVAL PENDING"
    manifest = {
        "schema_version": 1,
        "decision": decision,
        "sources_sha256": source,
        "bom": bom,
        "bom_csv_sha256": sha(ROOT / "docs/replica-dual-config-bom.csv"),
        "unresolved_singleton_endpoints": len(unresolved),
        "reports": reports,
        "bringup_board_json_hash_matches": bringup_current,
        "manufacturing_routed_pcb_hash_matches": manufacturing_current,
        "upload_zip": {"path": ZIP, "present": upload_exists,
                       "sha256": sha(ROOT / ZIP) if upload_exists else None},
        "hold_reasons": hold_reasons,
    }
    json_text = json.dumps(manifest, indent=2, ensure_ascii=False) + "\n"
    lines = [
        "# Replica release evidence packet", "",
        f"Status: **PREPARED / {decision}**", "",
        "Generated by `python3 scripts/report_replica_release_evidence.py`. This is an",
        "index of the current evidence, not an approval to order, assemble, or power a board.",
        "The source hashes identify the exact files reviewed here. Regenerate this packet",
        "after any source or report change; use `--check` to detect a stale tracked packet.", "",
        "## Source identity", "",
        "| File | SHA256 |", "| --- | --- |",
    ]
    lines += [f"| `{p}` | `{digest}` |" for p, digest in source.items()]
    lines += ["", "## Evidence index", "", "| Evidence | Status in report | SHA256 |",
              "| --- | --- | --- |"]
    lines += [f"| {display_report_link(name, p, bool(entry['sha256']))} | {entry['status']} | "
              f"{display_hash(entry['sha256'])} |"
              for name, entry in reports.items() for p in [entry["path"]]]
    lines += ["", "## BOM snapshot", "",
              f"- CSV: [replica-dual-config-bom.csv](replica-dual-config-bom.csv) (`{manifest['bom_csv_sha256']}`)",
              f"- {bom['lines']} lines; {bom['positions']} positions; {bom['populate_now']} planned populated; {bom['leave_empty']} empty or pending.",
              f"- Bring-up report board-JSON hash matches current source: **{'yes' if bringup_current else 'no'}**.",
              f"- Manufacturing report routed-PCB hash matches current source: **{'yes' if manufacturing_current else 'no'}**.",
              f"- Current upload ZIP present: **{'yes' if upload_exists else 'no'}**.", "",
              "## Release holds", ""]
    lines += [f"- {reason}." for reason in hold_reasons]
    lines += ["", "## Closure sequence", "",
              "1. Accept the P0 owner measurements in the [measurement shortlist](owner-measurement-shortlist.md), then correct the board model and both routed variants from those measurements.",
              "2. Regenerate the BOM, sourcing, ERC/parity, DRC, bring-up, and manufacturing reports; resolve or formally disposition every release failure.",
              "3. Generate a new Gerber/drill package from the final routed-board hash, independently inspect the exact ZIP and vendor preview, and record approval in the [order evidence template](replica-order-evidence-template.md).",
              "4. Record each received and assembled unit separately in the [first-article record](replica-first-article-record.md) before staged power-up.", "",
              "The machine-readable snapshot is [replica-release-evidence-manifest.json](replica-release-evidence-manifest.json).", ""]
    return json_text, "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="fail if tracked snapshot is stale")
    args = parser.parse_args()
    expected = dict(zip((JSON_OUT, MD_OUT), build()))
    if args.check:
        stale = [str(p.relative_to(ROOT)) for p, value in expected.items()
                 if not p.exists() or p.read_text() != value]
        if stale:
            raise SystemExit("stale release evidence packet: " + ", ".join(stale))
        print("release evidence packet: current")
    else:
        for path, value in expected.items():
            path.write_text(value)
            print(f"wrote {path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
