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
SUPPORT_FILES = [
    "docs/main-board-unresolved-endpoints.csv",
    "docs/ppi-physical-pin-mapping.json",
    "fab/gerbers/juku_routed-drc.json",
    "fab/audit/main-board-erc.json",
    "fab/audit/main-board-parity-drc.json",
]
REPORTS = [
    ("Fidelity", "docs/board-fidelity-gap-ledger.md"),
    ("Owner checks", "docs/owner-measurement-shortlist.md"),
    ("BOM", "docs/replica-dual-config-bom.md"),
    ("Sourcing", "docs/replica-sourcing-readiness.md"),
    ("Firmware lineage", "docs/firmware-gap-ledger.md"),
    ("EPROM programming", "docs/eprom-programming-images.md"),
    ("PROM procedure", "docs/prom-dump-procedure.md"),
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
SOURCE_STAMP = "fab/gerbers/source-board.sha256"
UPLOAD_SUMS = "fab/gerbers/upload/SHA256SUMS.txt"
PROM_PARTS = {"D2": "d2_037", "D6": "d6_038", "D8": "d8_039", "D94": "d94_092"}
EPROM_PARTS = {"D15": "d15_ekta37_low.bin", "D16": "d16_ekta37_high.bin"}
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


def upload_checksum_matches(zip_hash: str | None) -> bool:
    sums = ROOT / UPLOAD_SUMS
    if not zip_hash or not sums.is_file():
        return False
    entries = [line.split(None, 1) for line in sums.read_text().splitlines() if line.strip()]
    return len(entries) == 1 and entries[0] == [zip_hash, Path(ZIP).name]


def bom_counts() -> dict[str, int]:
    with (ROOT / "docs/replica-dual-config-bom.csv").open(newline="") as f:
        rows = list(csv.DictReader(f))
    return {
        "lines": len(rows),
        "positions": sum(int(r["board_positions"]) for r in rows),
        "populate_now": sum(int(r["populate_now"]) for r in rows),
        "leave_empty": sum(int(r["leave_empty"]) for r in rows),
    }


def programming_evidence() -> dict[str, dict]:
    items: dict[str, dict] = {}
    for ref, stem in PROM_PARTS.items():
        prefix = Path("ref/physical-proms/validated")
        dump_path = prefix / f"{stem}.dump.json"
        dump = json.loads((ROOT / dump_path).read_text())
        raw_path = prefix / f"{stem}.raw.bin"
        asserted_path = prefix / f"{stem}.asserted.bin"
        raw_hash, asserted_hash = sha(ROOT / raw_path), sha(ROOT / asserted_path)
        if raw_hash != dump["raw_pin_level_sha256"] or (
            asserted_hash != dump["active_low_asserted_sha256"]
        ):
            raise SystemExit(f"validated PROM digest differs from dump provenance: {ref}")
        items[ref] = {
            "kind": "validated physical PROM table",
            "raw_path": raw_path.as_posix(), "raw_sha256": raw_hash,
            "asserted_path": asserted_path.as_posix(), "asserted_sha256": asserted_hash,
            "dump_manifest": dump_path.as_posix(), "dump_manifest_sha256": sha(ROOT / dump_path),
            "capture_count": dump["capture_count"],
            "independent_capture_count": dump["independent_capture_count"],
        }
    sum_file = ROOT / "ref/eprom-images/SHA256SUMS"
    expected = {entry.split(None, 1)[1].strip(): entry.split(None, 1)[0]
                for entry in sum_file.read_text().splitlines() if entry.strip()}
    for ref, filename in EPROM_PARTS.items():
        path = Path("ref/eprom-images") / filename
        digest = sha(ROOT / path)
        if digest != expected.get(filename) or (ROOT / path).stat().st_size != 8192:
            raise SystemExit(f"EPROM image does not match checked 8 KiB split: {ref}")
        items[ref] = {"kind": "adopted archive-37 RomBios 3.43m EPROM split",
                      "path": path.as_posix(), "sha256": digest, "bytes": 8192}
    source_rom = ROOT / "roms/ekta37.bin"
    joined = b"".join((ROOT / items[ref]["path"]).read_bytes()
                      for ref in ("D15", "D16"))
    if joined != source_rom.read_bytes() or sha(source_rom) != expected.get("../../roms/ekta37.bin"):
        raise SystemExit("D15/D16 split does not reproduce the adopted archive-37 RomBios 3.43m ROM")
    return items


def build() -> tuple[str, str]:
    source = {p: sha(ROOT / p) for p in SOURCES}
    support = {p: sha(ROOT / p) if (ROOT / p).is_file() else None
               for p in SUPPORT_FILES}
    reports = {name: {"path": p,
                      "sha256": sha(ROOT / p) if (ROOT / p).is_file() else None,
                      "status": status(ROOT / p)}
               for name, p in REPORTS}
    bom = bom_counts()
    programs = programming_evidence()
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
    zip_hash = sha(ROOT / ZIP) if upload_exists else None
    stamp = ROOT / SOURCE_STAMP
    source_stamp_matches = stamp.is_file() and stamp.read_text().strip() == source[SOURCES[3]]
    upload_sums_match = upload_checksum_matches(zip_hash)
    hold_reasons = [f"{name}: {reports[name]['status']} (requires {expected})"
                    for name, expected in RELEASE_EXPECTED.items()
                    if reports[name]["status"] != expected]
    with (ROOT / "docs/main-board-unresolved-endpoints.csv").open(newline="") as f:
        unresolved = list(csv.DictReader(f))
    drc_raw = json.loads((ROOT / "fab/gerbers/juku_routed-drc.json").read_text())
    drc_report = (ROOT / "docs/replica-fab-drc-disposition.md").read_text()
    drc_count = len(drc_raw.get("unconnected_items", []))
    drc_rendered = re.search(r"^\| `unconnected_items` \| (\d+) \|", drc_report, re.M)
    if not drc_rendered or int(drc_rendered.group(1)) != drc_count:
        raise SystemExit("DRC disposition unconnected count differs from raw DRC JSON")
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
    if not source_stamp_matches:
        hold_reasons.append("fabrication source-board stamp does not match the routed PCB")
    if not upload_sums_match:
        hold_reasons.append("upload checksum file does not match the exact ZIP")
    decision = "DESIGN HOLD" if hold_reasons else "EVIDENCE COMPLETE / OWNER APPROVAL PENDING"
    manifest = {
        "schema_version": 1,
        "decision": decision,
        "sources_sha256": source,
        "supporting_files_sha256": support,
        "bom": bom,
        "programming_evidence": programs,
        "eprom_source_rom": {"path": "roms/ekta37.bin", "sha256": sha(ROOT / "roms/ekta37.bin")},
        "bom_csv_sha256": sha(ROOT / "docs/replica-dual-config-bom.csv"),
        "unresolved_singleton_endpoints": len(unresolved),
        "reports": reports,
        "bringup_board_json_hash_matches": bringup_current,
        "manufacturing_routed_pcb_hash_matches": manufacturing_current,
        "upload_zip": {"path": ZIP, "present": upload_exists, "sha256": zip_hash,
                       "checksum_file": UPLOAD_SUMS, "checksum_matches": upload_sums_match},
        "fabrication_source_stamp": {"path": SOURCE_STAMP, "matches_routed_pcb": source_stamp_matches},
        "hold_reasons": hold_reasons,
    }
    json_text = json.dumps(manifest, indent=2, ensure_ascii=False) + "\n"
    lines = [
        "# Replica release evidence packet", "",
        f"Status: **PREPARED / {decision}**", "",
        "Generated by `python3 scripts/report_replica_release_evidence.py`. This is an",
        "index of the current evidence, not an approval to order, assemble, or power a board.",
        "The hashes identify files inventoried by this command. It reads report statuses",
        "and checks the BOM census, selected source identities, and programming-image",
        "digests; it does not rerun the listed design or fabrication checks.",
        "Regenerate this packet",
        "after any source or report change; use `--check` to detect a stale tracked packet.", "",
        "## Source identity", "",
        "| File | SHA256 |", "| --- | --- |",
    ]
    lines += [f"| `{p}` | `{digest}` |" for p, digest in source.items()]
    lines += ["", "## Machine-readable supporting evidence", "",
              "| File | SHA256 |", "| --- | --- |"]
    lines += [f"| `{p}` | {display_hash(digest)} |" for p, digest in support.items()]
    lines += ["", f"The raw routed DRC lists {drc_count} unconnected items, matching the",
              "tracked DRC disposition count."]
    lines += ["", "## Evidence index", "", "| Evidence | Status in report |",
              "| --- | --- |"]
    lines += [f"| {display_report_link(name, p, bool(entry['sha256']))} | {entry['status']} |"
              for name, entry in reports.items() for p in [entry["path"]]]
    lines += ["", "Exact report digests are recorded in the machine-readable manifest linked below.",
              "", "## BOM snapshot", "",
              f"- CSV: [replica-dual-config-bom.csv](replica-dual-config-bom.csv) (`{manifest['bom_csv_sha256']}`)",
              f"- {bom['lines']} lines; {bom['positions']} positions; {bom['populate_now']} planned populated; {bom['leave_empty']} empty or pending.",
              f"- Bring-up report board-JSON hash matches current source: **{'yes' if bringup_current else 'no'}**.",
              f"- Manufacturing report routed-PCB hash matches current source: **{'yes' if manufacturing_current else 'no'}**.",
              f"- Current upload ZIP present: **{'yes' if upload_exists else 'no'}**.", "",
              f"- Fabrication source stamp matches routed PCB: **{'yes' if source_stamp_matches else 'no'}**.",
              f"- Upload checksum matches exact ZIP: **{'yes' if upload_sums_match else 'no'}**.", "",
              "## Programmed part identity", "",
              "The four small-PROM raw tables and asserted interpretations are separately",
              "preserved. The programming procedure determines which bit polarity to write",
              "for the selected device and programmer. D15/D16 are the adopted functional",
              "archive-37 RomBios 3.43m split; their concatenation matches",
              f"`roms/ekta37.bin` (`{manifest['eprom_source_rom']['sha256']}`). Record",
              "the exact installed images in each first-article record.", "",
              "| Ref | Evidence | SHA256 | Provenance |", "| --- | --- | --- | --- |"]
    for ref, item in programs.items():
        if "raw_path" in item:
            lines.append(f"| {ref} | `{item['raw_path']}` (raw) | `{item['raw_sha256']}` | "
                         f"{item['independent_capture_count']} independent captures; "
                         f"[dump record](../{item['dump_manifest']}) |")
            lines.append(f"| {ref} | `{item['asserted_path']}` (asserted) | "
                         f"`{item['asserted_sha256']}` | same validated capture set |")
        else:
            lines.append(f"| {ref} | `{item['path']}` | `{item['sha256']}` | "
                         f"[EPROM split notes](eprom-programming-images.md) |")
    lines += ["",
              "## Portable review archive", "",
              "Run `python3 scripts/build_replica_release_evidence_bundle.py` to write",
              "`fab/evidence/juku-replica-release-evidence.zip` and its `.zip.sha256`",
              "sidecar. Keep both files together when sharing. Run it with `--check`",
              "to verify every archived member against the current workspace and the",
              "archive's checksum list. The archive carries this packet, board sources,",
              "release reports, BOM/backlog CSVs, and programmed-image evidence.",
              "It is a review snapshot and is never the fabrication upload ZIP.", "",
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
