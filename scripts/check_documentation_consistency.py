#!/usr/bin/env python3
"""Guard public status in both a working tree and a clean Git checkout.

The fabrication tree is intentionally ignored.  Tracked status/checksum records
must therefore be internally consistent without it; byte-level package and
order-report checks are added when the local fabrication tree is available.
"""

from __future__ import annotations

import csv
import hashlib
import json
import re
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SHA256_RE = re.compile(r"(?<![0-9a-f])[0-9a-f]{64}(?![0-9a-f])", re.I)


def read(path: str) -> str:
    target = ROOT / path
    return target.read_text(encoding="utf-8", errors="replace") if target.exists() else ""


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    failures: list[str] = []
    core = {
        "README.md": read("README.md"),
        "PLAN.md": read("PLAN.md"),
        "docs/README.md": read("docs/README.md"),
    }
    evidence = {
        "WAIT/READY edges": read("docs/d2-reconstruction-constraints.md"),
        "D94": read("docs/d94-reconstruction-constraints.md"),
        "unmodeled ICs": read("docs/unmodeled-footprint-inventory.md"),
        "source-risk nets": read("docs/replica-bringup-verification-points.md"),
        "sourcing": read("docs/replica-sourcing-readiness.md"),
        "source PCB placement": read("docs/source-pcb-drc.md"),
        "factory wire routing": read("docs/factory-wire-route-fidelity.md"),
    }

    photo_endpoints = ROOT / "ref/photos/juku-pcb-2/endpoints.csv"
    if not photo_endpoints.exists():
        failures.append("photo endpoint evidence table is missing")
    else:
        with photo_endpoints.open(newline="", encoding="utf-8") as handle:
            photo_rows = list(csv.DictReader(handle))
        state_counts = Counter(row.get("review_state", "") for row in photo_rows)
        confidence_counts = Counter(row.get("confidence", "") for row in photo_rows)
        photo_doc = read("docs/photo-registration.md")
        expected_photo_markers = (
            f"endpoint table contains {len(photo_rows)} reviewed rows",
            f"| `accepted` | {state_counts['accepted']} |",
            f"| `measurement` | {state_counts['measurement']} |",
            f"Confidence metadata consists of {confidence_counts['local-package-fit']} `local-package-fit`, {confidence_counts['registration-only']}",
            f"`registration-only`, and {confidence_counts['registration+unique-hole-snap']} `registration+unique-hole-snap` rows",
        )
        for expected in expected_photo_markers:
            if expected not in photo_doc:
                failures.append(f"photo-registration summary is stale; missing {expected!r}")
        plan = core["PLAN.md"]
        for expected in (
            f"{len(photo_rows)} observations have dispositions",
            f"{state_counts['accepted']} rows are accepted evidence",
            f"other {state_counts['measurement']} remain",
        ):
            if expected not in plan:
                failures.append(f"PLAN photo-evidence totals are stale; missing {expected!r}")

    # Byte-level truth for all four board PROMs is now physical evidence, not a
    # reconstruction TODO. Guard both the artifacts and the legacy provenance
    # notes that previously called those dumps absent/open. Circuit adoption is
    # intentionally checked elsewhere and must not be conflated with content.
    physical_proms = {
        "D2 .037": ("ref/physical-proms/validated/d2_037.raw.bin", 256),
        "D6 .038": ("ref/physical-proms/validated/d6_038.raw.bin", 256),
        "D8 .039": ("ref/physical-proms/validated/d8_039.raw.bin", 32),
        "D94 .092": ("ref/physical-proms/validated/d94_092.raw.bin", 32),
    }
    for label, (path, expected_size) in physical_proms.items():
        artifact = ROOT / path
        if not artifact.exists():
            failures.append(f"validated physical PROM is missing: {label} ({path})")
        elif artifact.stat().st_size != expected_size:
            failures.append(
                f"validated physical PROM has wrong size: {label} "
                f"({artifact.stat().st_size}, expected {expected_size})"
            )

    stale_prom_claims = {
        "ref/photos/juku-pcb-2/BODGE-TRIAGE.md": (
            "signal wiring and contents still open",
            "original dump absent",
            "enable, outputs, and contents still open",
            "D2 and D94 remain incomplete",
        ),
        "ref/ekdos-source/README.md": ("D2/D6/D8/D94 PROM-truth gap",),
        "ref/photos/juku-pcb-2/SURVEY.md": (
            "Photo sighting alone does not close D2/D94 contents",
        ),
        "ref/baltijets-tech-docs/README.md": (
            "remain dump-or-disk items",
            "remains the needed D8",
            "owner/community dump request remains necessary",
        ),
        "ref/firmware/README.md": (
            "Dumping the socketed chip confirms or refutes",
        ),
    }
    for path, phrases in stale_prom_claims.items():
        text = read(path)
        for phrase in phrases:
            if phrase in text:
                failures.append(f"{path} retains stale physical-PROM claim: {phrase!r}")

    blockers = {
        "WAIT/READY edges": "Status: **D2 RECONSTRUCTION READY**" not in evidence["WAIT/READY edges"],
        "D94": "Status: **D94 RECONSTRUCTION READY**" not in evidence["D94"],
        "unmodeled ICs": "Status: **READY FOR DESIGN RELEASE**" not in evidence["unmodeled ICs"],
        "source-risk nets": "Status: **DESIGN RELEASE RISKS CLOSED**" not in evidence["source-risk nets"],
        "sourcing": "Status: **SOURCING READY**" not in evidence["sourcing"],
        "source PCB placement": "Status: **PASS**" not in evidence["source PCB placement"],
        "factory wire routing": "Status: **FACTORY WIRE CONSTRUCTION PRESERVED**" not in evidence["factory wire routing"],
    }
    design_held = any(blockers.values())

    for path, text in core.items():
        if not text:
            failures.append(f"missing core document: {path}")
            continue
        if design_held and "hold" not in text.lower() and "not released" not in text.lower():
            failures.append(f"{path} does not expose the active design hold")

    lvs_scope: dict[str, tuple[int, int]] = {}
    for path in ("README.md", "PLAN.md", "sync/README.md"):
        match = re.search(
            r"(\d+) mapped instances and (\d+) (?:matched |compared )?nets",
            read(path),
        )
        if not match:
            failures.append(f"{path} does not expose the current LVS scope")
        else:
            lvs_scope[path] = (int(match.group(1)), int(match.group(2)))
    if len(set(lvs_scope.values())) > 1:
        failures.append(
            "LVS scope disagrees across public docs: "
            + ", ".join(f"{path}={scope[0]}/{scope[1]}" for path, scope in lvs_scope.items())
        )

    manufacturing = read("docs/replica-manufacturing-readiness.md")
    recorded_package_digests: dict[str, set[str]] = {}
    for path in ("README.md", "PLAN.md", "docs/replica-manufacturing-readiness.md"):
        recorded_package_digests[path] = {digest.lower() for digest in SHA256_RE.findall(read(path))}
    shared_package_digests = set.intersection(*recorded_package_digests.values())
    if not shared_package_digests:
        failures.append("tracked release documents do not share a recorded package SHA256")

    fab_root = ROOT / "fab"
    upload_zip = fab_root / "gerbers/upload/juku-replica-gerbers-drill.zip"
    if fab_root.exists() and not upload_zip.exists():
        failures.append("local fabrication tree exists but main-board upload ZIP is missing")
    elif upload_zip.exists():
        digest = sha256(upload_zip)
        for path in ("README.md", "PLAN.md", "docs/replica-manufacturing-readiness.md"):
            if digest not in read(path):
                failures.append(f"{path} does not contain current upload ZIP SHA256 {digest}")

    order = read("fab/gerbers/order-readiness.md")
    if design_held:
        manufacturing_held = any(
            status in manufacturing
            for status in (
                "Status: **DESIGN HOLD / PACKAGE VERIFIED**",
                "Status: **PACKAGE INVALID**",
            )
        )
        if not manufacturing_held:
            failures.append("manufacturing report exposes neither design hold nor package invalidity")
        order_held = any(
            status in order
            for status in (
                "Status: **PACKAGE READY / DESIGN HOLD**",
                "Status: **PACKAGE INCOMPLETE**",
                "Status: **NOT READY**",
            )
        )
        if fab_root.exists() and not order_held:
            failures.append("order-readiness report exposes neither design hold nor package blockers")
        for path, text in core.items():
            if "READY TO UPLOAD" in text or "ORDER READY" in text:
                failures.append(f"{path} contains obsolete release language")
    else:
        if "Status: **RELEASED FOR UPLOAD**" not in manufacturing:
            failures.append("all release evidence passes but manufacturing report is not released")
        if fab_root.exists() and "Status: **RELEASED FOR ORDER**" not in order:
            failures.append("all release evidence passes but order report is not released")

    removed_live_docs = [
        "docs/project-status.md",
        "docs/roadmap.md",
        "docs/milestone-ledger.md",
        "docs/grind-backlog.md",
        "docs/phase-b.md",
        "docs/digitization-plan.md",
        "docs/boot-findings.md",
        "docs/bom-toward-76.md",
        "docs/emaplaat-harvest.md",
        "docs/re3-decode.md",
        "docs/mame-interface-map.md",
        "docs/basic-low-stub-inspection.md",
        "docs/basic-cartridge-tail-hypotheses.md",
        "docs/basic-launch-probe.md",
        "docs/basic-factory-command-probe.md",
        "spinoffs/minimal-vga/docs/manufacturing-roadmap.md",
        "spinoffs/minimal-vga/docs/rev-a-bare-pcb-order.md",
    ]
    for path in removed_live_docs:
        if (ROOT / path).exists():
            failures.append(f"superseded live-status document still exists: {path}")

    board = read("kicad/juku.board.json")
    try:
        board_model = json.loads(board)
    except json.JSONDecodeError as exc:
        failures.append(f"board JSON is invalid: {exc}")
        board_model = {"nets": {}}
    board_nets = board_model.get("nets", {})
    plan = core["PLAN.md"]
    for stale in (
        "joined-conductor D8/D13/D92 timing reconstruction",
        "After the joined\n   conductor's downstream",
        "boot exercises only physical modes `000`/`001`",
    ):
        if stale in plan:
            failures.append(f"PLAN retains stale D6 topology/mode claim: {stale!r}")
    for required in (
        "separate D6.12/D8 ROM-select and D6.9/D13/D37/D58 timing paths",
        "boot firmware observes A6/A5 suffixes `11` and `10`",
    ):
        if required not in plan:
            failures.append(f"PLAN omits current guarded D6 evidence: {required!r}")

    d26 = next((chip for chip in board_model.get("chips", []) if chip.get("ref") == "D26"), {})
    d26_provenance = d26.get("prov", {}).get("pins", "")
    if not all(
        marker in d26_provenance
        for marker in (
            "chip-removed .009 owner continuity supersedes only the D6 legs",
            "D6 A5/A6 now trace to D3.6/D3.4",
            "D6 A7 to D105.1",
            "PC2/3/4 remain on D28",
        )
    ):
        failures.append("D26 provenance does not distinguish the retired D6 mode bundle from live D28 routes")

    expected_d94_boundaries = {
        "BA0": None,
        "BA1": None,
        "IORD": None,
        "D94_A3_D104_X4_PULLUP": [["D94", "13"], ["D104", "7"]],
        "D94_A4_D101_Q0_PULLUP": [["D94", "14"], ["D101", "7"]],
    }
    for net_name, expected_nodes in expected_d94_boundaries.items():
        actual_nodes = board_nets.get(net_name, {}).get("nodes")
        pin = {"BA0": "10", "BA1": "11", "IORD": "12"}.get(net_name)
        if expected_nodes is None:
            ok = ["D94", pin] in (actual_nodes or [])
        else:
            ok = actual_nodes == expected_nodes
        if not ok:
            failures.append(
                f"board JSON does not preserve measured D94 input mapping on {net_name}"
            )
    for net_name in ("BA11", "BA12", "BA13", "BA14", "BA15"):
        nodes = board_nets.get(net_name, {}).get("nodes", [])
        if any(node[0] == "D94" and node[1] in {"10", "11", "12", "13", "14"} for node in nodes):
            failures.append(f"board JSON restores unsupported {net_name}-to-D94 address mapping")
    source_pcb = ROOT / "kicad/juku.kicad_pcb"
    source_drc = evidence["source PCB placement"]
    source_drc_hash = re.search(r"Board SHA256: `([0-9a-f]{64})`", source_drc)
    if not source_drc_hash:
        failures.append("source-PCB DRC report is missing its board checksum")
    elif source_pcb.exists() and source_drc_hash.group(1) != sha256(source_pcb):
        failures.append("source-PCB DRC report is stale for kicad/juku.kicad_pcb")
    dual_bom = read("docs/replica-dual-config-bom.csv")
    if "D84-D91 are populated" not in board or "D60-D83 are empty" not in board:
        failures.append("board JSON does not state the .158/.009 D84-D91 population")
    if '"D84, D85, D86, D87, D88, D89, D90, D91"' not in dual_bom:
        failures.append("dual-config BOM does not select D84-D91 as the populated RAM row")

    unmodeled = evidence["unmodeled ICs"]
    expected_unmodeled = ("D28", "D95", "D96", "D97", "D98", "D99", "D101", "D102", "D106")
    unmodeled_count_match = re.search(r"and `(\d+)` promoted FDC devices", unmodeled)
    unmodeled_count = None
    if unmodeled_count_match:
        unmodeled_count = int(unmodeled_count_match.group(1))
        if unmodeled_count and not re.search(
            rf"{unmodeled_count}\s+official\s+FDC-support\s+ICs",
            core["README.md"],
        ):
            failures.append("README does not expose the current untraced FDC-device count")
    if unmodeled_count == len(expected_unmodeled):
        for ref in expected_unmodeled:
            if f"| `{ref}` |" not in unmodeled:
                failures.append(
                    f"unmodeled-footprint report count is {unmodeled_count} but omits {ref}"
                )
    if unmodeled_count and f"{unmodeled_count} official FDC devices with untraced functional pins" not in board:
        failures.append("board JSON does not expose all untraced FDC devices as a design boundary")

    risk_match = re.search(r"Verification-point nets: `(\d+)`", evidence["source-risk nets"])
    if risk_match:
        risk_count = int(risk_match.group(1))
        if risk_count and not re.search(
            rf"{risk_count}\s+modeled\s+nets retain source-risk annotations",
            core["README.md"],
        ):
            failures.append("README does not expose the current residual source-risk net count")
        for path in ("PLAN.md", "hdl/README.md"):
            if not re.search(rf"\b{risk_count}\b[^\n]*source-risk", read(path)):
                failures.append(f"{path} does not expose the current residual source-risk net count")

    vjuga = {
        "spinoffs/minimal-vga/README.md": read("spinoffs/minimal-vga/README.md"),
        "spinoffs/minimal-vga/docs/rev-a-manufacturing-readiness.md": read(
            "spinoffs/minimal-vga/docs/rev-a-manufacturing-readiness.md"
        ),
        "spinoffs/minimal-vga/kicad/fab-notes.md": read("spinoffs/minimal-vga/kicad/fab-notes.md"),
    }
    for path, text in vjuga.items():
        if "hold" not in text.lower():
            failures.append(f"{path} does not expose the VJUGA design hold")
        if "READY TO UPLOAD" in text or "READY FOR VENDOR PREVIEW" in text:
            failures.append(f"{path} contains obsolete VJUGA release language")
    if "No real Juku ROM has booted" not in vjuga["spinoffs/minimal-vga/docs/rev-a-manufacturing-readiness.md"]:
        failures.append("VJUGA readiness does not state that real-ROM boot is unproven")
    vjuga_zip = ROOT / "fab" / "minimal-vga" / "upload" / "vjuga-rev-a-gerbers-drill.zip"
    if vjuga_zip.exists():
        vjuga_digest = sha256(vjuga_zip)
        if vjuga_digest not in vjuga["spinoffs/minimal-vga/docs/rev-a-manufacturing-readiness.md"]:
            failures.append(f"VJUGA readiness does not contain current Gerber ZIP SHA256 {vjuga_digest}")

    cartridge = read("docs/cartridge-basic-boundary.md")
    cartridge_image = ROOT / "roms" / "jbasic11.bin"
    if "Status: **ARTIFACT OR DOCUMENTED PROCEDURE REQUIRED**" not in cartridge:
        failures.append("consolidated cartridge BASIC boundary is missing or stale")
    if cartridge_image.exists() and sha256(cartridge_image) not in cartridge:
        failures.append("cartridge BASIC boundary does not contain the current jbasic11 SHA256")

    if failures:
        print("Documentation consistency check failed:")
        for failure in failures:
            print(f"- {failure}")
        return 1

    held = ", ".join(name for name, active in blockers.items() if active)
    if "Status: **PACKAGE INVALID**" in manufacturing:
        package_scope = "local package invalidity exposed"
    elif upload_zip.exists():
        package_scope = "local package verified"
    else:
        package_scope = "tracked package record verified"
    print(f"Documentation status is consistent; design hold: {held or 'none'}; {package_scope}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
