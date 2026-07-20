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
    bringup_source_hashes = {
        "Source board JSON": ROOT / "kicad/juku.board.json",
        "Final PCB source": ROOT / "kicad/juku.kicad_pcb",
        "Routed PCB source": ROOT / "kicad/juku_routed.kicad_pcb",
    }
    for label, source_path in bringup_source_hashes.items():
        match = re.search(
            rf"^- {re.escape(label)} SHA-256: `([0-9a-f]{{64}})`$",
            evidence["source-risk nets"],
            re.MULTILINE,
        )
        if not match or match.group(1) != sha256(source_path):
            failures.append(f"bring-up report has stale {label} SHA-256")
    inventory_source_hashes = {
        "Board JSON": ROOT / "kicad/juku.board.json",
        "Source PCB": ROOT / "kicad/juku.kicad_pcb",
        "Routed PCB": ROOT / "kicad/juku_routed.kicad_pcb",
        "DSN": ROOT / "kicad/juku.dsn",
    }
    for label, source_path in inventory_source_hashes.items():
        match = re.search(
            rf"^- {re.escape(label)} SHA-256: `([0-9a-f]{{64}})`$",
            evidence["unmodeled ICs"],
            re.MULTILINE,
        )
        if not match or match.group(1) != sha256(source_path):
            failures.append(f"unmodeled-footprint report has stale {label} SHA-256")
    routed_refresh = read("docs/routed-refresh-audit.md")
    routed_refresh_hashes = {
        "Source PCB": ROOT / "kicad/juku.kicad_pcb",
        "Routed-snapshot PCB": ROOT / "kicad/juku_routed.kicad_pcb",
    }
    for label, source_path in routed_refresh_hashes.items():
        match = re.search(
            rf"^\| {re.escape(label)} SHA-256 \| `([0-9a-f]{{64}})` \|$",
            routed_refresh,
            re.MULTILINE,
        )
        if not match or match.group(1) != sha256(source_path):
            failures.append(f"routed-refresh table has stale {label} SHA-256")

    system_bus_report = read("ref/schematics/system-bus-connector-map.md")
    for marker in (
        "SIGNAL CORE MATCHES / POWER MAP IS A DOCUMENTED VARIANT CONFLICT",
        "| `132C` | `-D0` | `DAT0` | PASS |",
        "| `117B` | `-ADRF` | `ADR_HI7` | PASS |",
        "conflict directly at `101A, 102A, 103A`",
        "A2.2 removable memory expander E6201",
    ):
        if marker not in system_bus_report:
            failures.append(f"system-bus connector report lost guarded marker: {marker!r}")

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

    # The corrected physical D6 table directly replaced the functional decoder
    # and the former sim-only D0/D3 fit on 2026-07-19.
    d6_top = read("hdl/juku_top.v")
    d6_devices = read("hdl/devices.v")
    if (
        "decode_prom U_DECODE" not in d6_top
        or "wire        rom_sel_n = d6_rom_select_n;" not in d6_top
        or "wire        roe_n     = d6_roe_physical;" not in d6_top
        or "~d6_rom_select_n" in d6_top
        or "~d6_roe_physical" in d6_top
        or re.search(r"decode_prom_functional\s+U_", d6_top)
    ):
        failures.append("runnable D6 corrected direct-table contract drifted")
    if "module decode_prom_functional" not in d6_devices:
        failures.append("D6 B37A diagnostic comparison model is missing")
    stale_d6_adoption_claims = {
        "PLAN.md": (
            "selects still come from the non-LVS `decode_prom_functional` oracle",
            "the one remaining memory-map stand-in",
        ),
        "hdl/README.md": (
            "Runnable simulation uses the explicitly non-LVS",
        ),
        "docs/d6-input-continuity.md": (
            "runnable memory-decode oracle remains in place",
        ),
        "docs/firmware-gap-ledger.md": (
            "before retiring the functional decoder",
        ),
        "docs/owner-measurement-shortlist.md": (
            "before retiring the D6 runnable oracle",
        ),
    }
    for path, phrases in stale_d6_adoption_claims.items():
        text = read(path)
        for phrase in phrases:
            if phrase in text:
                failures.append(f"{path} retains stale D6 runnable-path claim: {phrase!r}")

    stale_d6_a7_claims = {
        "PLAN.md": ("Close the physical D6 A7 driver", "D105.1/A7 driver (P0", "D105.1 conductor remains"),
        "docs/d6-physical-decode.md": ("driver or pull source is still unresolved", "unresolved A7"),
        "docs/d6-input-continuity.md": ("A7 SOURCE BOUNDARY", "A7 source remains open"),
        "docs/owner-measured-facts.md": ("driver/pull source NOT yet measured",),
    }
    for path, phrases in stale_d6_a7_claims.items():
        text = read(path)
        for phrase in phrases:
            if phrase in text:
                failures.append(f"{path} retains stale D6 A7 boundary claim: {phrase!r}")

    stale_d93_dal_claims = {
        "PLAN.md": (
            "actual CPU↔D93 DAL transform must be recovered",
            "actual CPU↔D93 DAL wiring now that",
            "verify the source-drawn direct CPU↔D93 DAL wiring",
        ),
        "docs/fdc-bus-polarity.md": ("physical D93 data-bus wiring remains open",),
    }
    for path, phrases in stale_d93_dal_claims.items():
        text = read(path)
        for phrase in phrases:
            if phrase in text:
                failures.append(f"{path} retains stale direct D93 DAL boundary claim: {phrase!r}")

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
    plan = core["PLAN.md"]
    architecture = read("docs/architecture.md")
    if "Status: **PACKAGE INVALID**" in manufacturing:
        if "Release status: **DESIGN HOLD / PACKAGE INVALID**" not in plan:
            failures.append("PLAN does not expose generated package invalidity")
        if "**DESIGN HOLD / PACKAGE INVALID**" not in architecture:
            failures.append("architecture summary does not expose generated package invalidity")
        if re.search(
            r"(?m)^- \[x\] Current engineering PCB package .*DRC-clean",
            plan,
        ):
            failures.append("PLAN marks the invalid current PCB package DRC-clean")
    elif "Status: **DESIGN HOLD / PACKAGE VERIFIED**" in manufacturing:
        if "Release status: **DESIGN HOLD / PACKAGE VERIFIED**" not in plan:
            failures.append("PLAN does not expose generated package verification state")

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
        "revision-3 captures and the direct full-boot comparison",
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
        "IOWR": None,
        "D94_A4_D101_Q0": [["D94", "14"], ["D101", "7"]],
    }
    for net_name, expected_nodes in expected_d94_boundaries.items():
        actual_nodes = board_nets.get(net_name, {}).get("nodes")
        pin = {"BA0": "10", "BA1": "11", "IORD": "12", "IOWR": "13"}.get(net_name)
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
    if unmodeled_count and not re.search(
        rf"The {unmodeled_count} official FDC devices with remaining source-risk pins",
        evidence["source-risk nets"],
    ):
        failures.append("bring-up checklist exposes a stale untraced FDC-device count")
    if unmodeled_count and not re.search(
        rf"`unmodeled-footprint-inventory\.md` \({unmodeled_count} FDC devices\)",
        read("PLAN.md"),
    ):
        failures.append("PLAN active-report index exposes a stale untraced FDC-device count")

    risk_match = re.search(r"Verification-point nets: `(\d+)`", evidence["source-risk nets"])
    if risk_match:
        risk_count = int(risk_match.group(1))
        fidelity_ledger = read("docs/board-fidelity-gap-ledger.md")
        ledger_risk_match = re.search(r"Net-level source-risk gaps: `(\d+)`", fidelity_ledger)
        if not ledger_risk_match or int(ledger_risk_match.group(1)) != risk_count:
            failures.append("fidelity ledger and bring-up checklist disagree on source-risk net count")
        closed_overrides = [
            (name, net)
            for name, net in board_model.get("nets", {}).items()
            if net.get("source_risk") is False
        ]
        closed_match = re.search(
            r"Explicitly dispositioned closed net risks: `(\d+)`", fidelity_ledger
        )
        if not closed_match or int(closed_match.group(1)) != len(closed_overrides):
            failures.append("fidelity ledger explicit source-risk closure count is stale")
        for name, net in closed_overrides:
            if not str(net.get("risk_disposition", "")).strip():
                failures.append(f"{name} has source_risk=false without a disposition")
        if risk_count and not re.search(
            rf"{risk_count}\s+modeled\s+nets retain source-risk annotations",
            core["README.md"],
        ):
            failures.append("README does not expose the current residual source-risk net count")
        for path in ("PLAN.md", "hdl/README.md"):
            if not re.search(rf"\b{risk_count}\b[^\n]*source-risk", read(path)):
                failures.append(f"{path} does not expose the current residual source-risk net count")

    endpoint_match = re.search(
        r"All board endpoints checked in source PCB: `(\d+)`",
        evidence["source-risk nets"],
    )
    if not endpoint_match:
        failures.append("bring-up checklist is missing the source-PCB endpoint count")
    else:
        endpoint_count = int(endpoint_match.group(1))
        if not re.search(
            rf"all {endpoint_count}/{endpoint_count}\s+PCB-scoped board-JSON endpoints",
            core["PLAN.md"],
        ):
            failures.append("PLAN exposes a stale source-PCB endpoint count")
    excluded_match = re.search(
        r"Intentional non-PCB or placement-pending endpoints excluded: `(\d+)`",
        evidence["source-risk nets"],
    )
    if not excluded_match:
        failures.append("bring-up checklist is missing the excluded endpoint count")
    else:
        excluded_count = int(excluded_match.group(1))
        if not re.search(
            rf"with {excluded_count} non-PCB or placement-held\s+endpoints intentionally excluded",
            core["PLAN.md"],
        ):
            failures.append("PLAN exposes a stale excluded endpoint count")

    # The preserved zero-open routing candidate intentionally drifts from the
    # current source. Its generated factory-wire report owns those counts; keep
    # the public summaries and routed-refresh narrative synchronized with it.
    candidate_net_match = re.search(
        r"Candidate/source pad-net mismatches: `(\d+)`",
        evidence["factory wire routing"],
    )
    candidate_moved_match = re.search(
        r"Candidate/source moved pads \(>50 nm\): `(\d+)`",
        evidence["factory wire routing"],
    )
    if not candidate_net_match or not candidate_moved_match:
        failures.append("factory-wire report omits candidate/source drift counts")
    else:
        candidate_net_count = int(candidate_net_match.group(1))
        candidate_moved_count = int(candidate_moved_match.group(1))
        public_drift = re.compile(
            rf"\b{candidate_net_count}\s+pad-net mismatches and "
            rf"{candidate_moved_count}\s+moved\s+pads"
        )
        for path in ("README.md", "PLAN.md"):
            if not public_drift.search(read(path)):
                failures.append(
                    f"{path} candidate/source drift counts disagree with factory-wire report"
                )
        routed_refresh = read("docs/routed-refresh-audit.md")
        if not re.search(
            rf"finds {candidate_net_count} changed pad-net assignments and "
            rf"{candidate_moved_count} pads",
            routed_refresh,
        ):
            failures.append(
                "routed-refresh post-checkpoint drift counts disagree with factory-wire report"
            )

    routing_exhaustion_path = ROOT / "ref/routing/current23-grid01125-exhaustion.json"
    if not routing_exhaustion_path.exists():
        failures.append("current 23-gap routing-exhaustion evidence is missing")
    else:
        routing_exhaustion = json.loads(routing_exhaustion_path.read_text(encoding="utf-8"))
        config = routing_exhaustion.get("router_config", {})
        outcomes = routing_exhaustion.get("outcomes", {})
        attempted_nets = routing_exhaustion.get("attempted_nets", [])
        if (
            routing_exhaustion.get("schema_version") != 1
            or routing_exhaustion.get("initial_unconnected") != 23
            or routing_exhaustion.get("final_unconnected") != 23
            or routing_exhaustion.get("accepted_routes") != 0
            or config.get("grid_step_mm") != 0.1125
            or config.get("route_clearance_mm") != 0.2
            or outcomes.get("router_failed") != 21
            or outcomes.get("timeout") != 2
            or len(attempted_nets) != 23
        ):
            failures.append("current 23-gap routing-exhaustion summary is malformed")
        for relative, expected in routing_exhaustion.get("tool_sha256", {}).items():
            tool_path = ROOT / relative
            if not tool_path.is_file() or sha256(tool_path) != expected:
                failures.append(f"routing-exhaustion tool hash changed: {relative}")
        for path in ("PLAN.md", "docs/routed-refresh-audit.md"):
            if "current23-grid01125-exhaustion.json" not in read(path):
                failures.append(f"{path} omits the current routing-exhaustion evidence")

    edge_phase_path = ROOT / "ref/routing/current23-grid-edge-phase-exhaustion.json"
    if not edge_phase_path.exists():
        failures.append("current 23-gap edge-phase routing evidence is missing")
    else:
        edge = json.loads(edge_phase_path.read_text(encoding="utf-8"))
        expected_board = "3dc2475580ce6217ad84484146d353a30b12237a5c4def2dbb40872ef763d37c"
        phases = edge.get("phases", {})
        fine = phases.get("0.0875", {})
        coarse = phases.get("0.1625", {})
        if (
            edge.get("schema_version") != 1
            or edge.get("board_sha256") != expected_board
            or edge.get("initial_unconnected") != 23
            or edge.get("final_unconnected") != 23
            or edge.get("accepted_routes") != 0
            or (fine.get("router_failed"), fine.get("timeout")) != (2, 21)
            or (coarse.get("router_failed"), coarse.get("timeout")) != (23, 0)
            or any(phase.get("output_board_sha256") != expected_board for phase in (fine, coarse))
            or len(edge.get("attempted_nets", [])) != 23
        ):
            failures.append("current 23-gap edge-phase routing summary is malformed")
        for relative, expected in edge.get("tool_sha256", {}).items():
            tool_path = ROOT / relative
            if not tool_path.is_file() or sha256(tool_path) != expected:
                failures.append(f"edge-phase routing tool hash changed: {relative}")
        for path in ("PLAN.md", "docs/routed-refresh-audit.md"):
            if "current23-grid-edge-phase-exhaustion.json" not in read(path):
                failures.append(f"{path} omits the edge-phase routing evidence")

    csd57_path = ROOT / "ref/routing/current23-cs-d57-transaction.json"
    if not csd57_path.exists():
        failures.append("current 23-gap CS_D57 transaction evidence is missing")
    else:
        csd57 = json.loads(csd57_path.read_text(encoding="utf-8"))
        diagnostic = csd57.get("diagnostic", {})
        phases = csd57.get("target_phases", {})
        trials = csd57.get("restoration_trials", {})
        default = trials.get("sorted_default", {})
        priority = trials.get("cs_d55_gnd_roe_sync_first", {})
        if (
            csd57.get("schema_version") != 1
            or csd57.get("input_unconnected") != 23
            or diagnostic.get("removable_conflicts") != 33
            or diagnostic.get("fixed_blockers") != 0
            or len(diagnostic.get("affected_nets", [])) != 14
            or phases.get("0.1375", {}).get("result") != "accepted"
            or [phases.get(k, {}).get("added_clearance_findings") for k in ("0.10", "0.125", "0.15")] != [4, 2, 1]
            or default.get("final_unconnected") != 26
            or priority.get("final_unconnected") != 27
            or any(priority.get("drc", {}).get(kind) != 0 for kind in ("short", "clearance", "track_crossing", "hole_clearance", "copper_edge_clearance"))
        ):
            failures.append("current 23-gap CS_D57 transaction summary is malformed")
        for relative, expected in csd57.get("tool_sha256", {}).items():
            tool_path = ROOT / relative
            if not tool_path.is_file() or sha256(tool_path) != expected:
                failures.append(f"CS_D57 transaction tool hash changed: {relative}")
        for path in ("PLAN.md", "docs/routed-refresh-audit.md"):
            if "current23-cs-d57-transaction.json" not in read(path):
                failures.append(f"{path} omits the CS_D57 transaction evidence")

    live_salvage_path = ROOT / "ref/routing/current-source-salvage-baseline.json"
    if not live_salvage_path.exists():
        failures.append("current-source salvage baseline evidence is missing")
    else:
        live = json.loads(live_salvage_path.read_text(encoding="utf-8"))
        identity = live.get("identity", {})
        source = live.get("source", {})
        raw = live.get("raw_candidate", {})
        salvaged = live.get("salvaged", {})
        classification = live.get("classification", {})
        if (
            live.get("schema_version") != 1
            or live.get("source_board_sha256") != sha256(ROOT / "kicad/juku.kicad_pcb")
            or live.get("routed_snapshot_sha256") != sha256(ROOT / "kicad/juku_routed.kicad_pcb")
            or (identity.get("footprints"), identity.get("pads")) != (321, 2434)
            or source.get("uncapped_unconnected") != 1814
            or raw.get("uncapped_unconnected") != 653
            or salvaged.get("uncapped_unconnected") != 883
            or salvaged.get("routed_items") != 7839
            or salvaged.get("migrated_items_removed") != 558
            or (salvaged.get("track_dangling"), salvaged.get("via_dangling")) != (199, 56)
            or classification.get("compatible_raw_nets") != 304
            or classification.get("common_pad_mismatches") != 381
            or any(salvaged.get(kind) != 0 for kind in ("short", "clearance", "track_crossing", "hole_clearance", "hole_to_hole", "copper_edge_clearance"))
        ):
            failures.append("current-source salvage baseline summary is malformed or stale")
        for relative, expected in live.get("tool_sha256", {}).items():
            tool_path = ROOT / relative
            if not tool_path.is_file() or sha256(tool_path) != expected:
                failures.append(f"current-source salvage tool hash changed: {relative}")
        for path in ("PLAN.md", "docs/routed-refresh-audit.md"):
            if "current-source-salvage-baseline.json" not in read(path):
                failures.append(f"{path} omits the current-source salvage baseline")

    live_prune_path = ROOT / "ref/routing/current-source-uncapped-prune.json"
    if not live_prune_path.exists():
        failures.append("current-source uncapped-prune evidence is missing")
    else:
        live_prune = json.loads(live_prune_path.read_text(encoding="utf-8"))
        identity = live_prune.get("identity", {})
        initial = live_prune.get("initial", {})
        pruned = live_prune.get("pruned", {})
        final = live_prune.get("final", {})
        probe = live_prune.get("route_probe", {})
        if (
            live_prune.get("schema_version") != 1
            or live_prune.get("source_board_sha256") != sha256(ROOT / "kicad/juku.kicad_pcb")
            or live_prune.get("input_board_sha256")
            != "eae597ab1667cf770211ff52bb21e89a6f1332762207decb4c47446ae62c0bf2"
            or live_prune.get("output_board_size") != 8008258
            or (identity.get("footprints"), identity.get("pads")) != (321, 2434)
            or initial.get("uncapped_unconnected") != 883
            or pruned.get("uncapped_unconnected") != 677
            or final.get("uncapped_unconnected") != 242
            or final.get("routed_nets") != 324
            or initial.get("routed_items") - pruned.get("routed_items") != 2872
            or live_prune.get("removed_items") != 2872
            or live_prune.get("removed_source_items") != 0
            or (pruned.get("track_dangling"), pruned.get("via_dangling")) != (0, 0)
            or (final.get("track_dangling"), final.get("via_dangling")) != (0, 0)
            or probe.get("accepted_routes_by_uncapped_guard") != 435
            or probe.get("uncapped_unconnected_before") - probe.get("uncapped_unconnected_after") != 435
            or probe.get("search_ceiling_mm") != 130
            or probe.get("multilayer_exhausted_through_mm") != 30
            or probe.get("promoted") is not True
            or any(final.get(kind) != 0 for kind in ("short", "clearance", "track_crossing", "hole_clearance", "hole_to_hole", "copper_edge_clearance"))
        ):
            failures.append("current-source uncapped-prune summary is malformed or stale")
        for relative, expected in live_prune.get("tool_sha256", {}).items():
            tool_path = ROOT / relative
            if not tool_path.is_file() or sha256(tool_path) != expected:
                failures.append(f"current-source uncapped-prune tool hash changed: {relative}")
        for path in ("PLAN.md", "docs/routed-refresh-audit.md"):
            if "current-source-uncapped-prune.json" not in read(path):
                failures.append(f"{path} omits the current-source uncapped-prune evidence")

    prune_path = ROOT / "ref/routing/current21-dangling-prune.json"
    if not prune_path.exists():
        failures.append("current 21-gap dangling-prune evidence is missing")
    else:
        prune = json.loads(prune_path.read_text(encoding="utf-8"))
        initial = prune.get("initial", {})
        final = prune.get("final", {})
        config = prune.get("config", {})
        if (
            prune.get("schema_version") != 1
            or initial.get("unconnected") != 23
            or final.get("unconnected") != 21
            or prune.get("removed_items") != 641
            or prune.get("removed_source_items") != 0
            or (initial.get("track_dangling"), initial.get("via_dangling")) != (199, 45)
            or (final.get("track_dangling"), final.get("via_dangling")) != (87, 11)
            or config.get("batch_size") != 32
            or config.get("max_removals") != 641
            or any(final.get(kind) != 0 for kind in ("short", "clearance", "track_crossing", "hole_clearance", "hole_to_hole", "copper_edge_clearance"))
            or len(prune.get("residual_nets", [])) != 21
        ):
            failures.append("current 21-gap dangling-prune summary is malformed")
        for relative, expected in prune.get("tool_sha256", {}).items():
            tool_path = ROOT / relative
            if not tool_path.is_file() or sha256(tool_path) != expected:
                failures.append(f"dangling-prune tool hash changed: {relative}")
        for path in ("PLAN.md", "docs/routed-refresh-audit.md"):
            if "current21-dangling-prune.json" not in read(path):
                failures.append(f"{path} omits the dangling-prune evidence")

    deep_prune_path = ROOT / "ref/routing/current21-deep-dangling-prune.json"
    if not deep_prune_path.exists():
        failures.append("current 21-gap deep-prune evidence is missing")
    else:
        deep = json.loads(deep_prune_path.read_text(encoding="utf-8"))
        initial = deep.get("initial", {})
        final = deep.get("final", {})
        config = deep.get("config", {})
        sweep = deep.get("post_prune_sweep", {})
        if (
            deep.get("schema_version") != 1
            or (initial.get("unconnected"), final.get("unconnected")) != (21, 21)
            or deep.get("removed_items") != 614
            or deep.get("removed_source_items") != 0
            or (initial.get("track_dangling"), initial.get("via_dangling")) != (87, 11)
            or (final.get("track_dangling"), final.get("via_dangling")) != (23, 2)
            or config.get("batch_size") != 16
            or config.get("adaptive_batch") is not True
            or config.get("max_removals") != 614
            or sweep.get("attempted_gaps") != 21
            or sweep.get("accepted_routes") != 0
            or sweep.get("output_board_sha256") != deep.get("output_board_sha256")
            or any(final.get(kind) != 0 for kind in ("short", "clearance", "track_crossing", "hole_clearance", "hole_to_hole", "copper_edge_clearance"))
            or len(deep.get("residual_nets", [])) != 21
        ):
            failures.append("current 21-gap deep-prune summary is malformed")
        for relative, expected in deep.get("tool_sha256", {}).items():
            tool_path = ROOT / relative
            if not tool_path.is_file() or sha256(tool_path) != expected:
                failures.append(f"deep-prune tool hash changed: {relative}")
        for relative, expected in deep.get("sweep_tool_sha256", {}).items():
            tool_path = ROOT / relative
            if not tool_path.is_file() or sha256(tool_path) != expected:
                failures.append(f"deep-prune sweep tool hash changed: {relative}")
        for path in ("PLAN.md", "docs/routed-refresh-audit.md"):
            if "current21-deep-dangling-prune.json" not in read(path):
                failures.append(f"{path} omits the deep dangling-prune evidence")

    fine_prune_path = ROOT / "ref/routing/current21-fine-dangling-prune.json"
    if not fine_prune_path.exists():
        failures.append("current 21-gap fine-prune evidence is missing")
    else:
        fine = json.loads(fine_prune_path.read_text(encoding="utf-8"))
        initial = fine.get("initial", {})
        final = fine.get("final", {})
        config = fine.get("config", {})
        sweep = fine.get("post_prune_sweep", {})
        if (
            fine.get("schema_version") != 1
            or (initial.get("unconnected"), final.get("unconnected")) != (21, 21)
            or fine.get("removed_items") != 160
            or fine.get("removed_source_items") != 0
            or (initial.get("track_dangling"), initial.get("via_dangling")) != (23, 2)
            or (final.get("track_dangling"), final.get("via_dangling")) != (14, 0)
            or config.get("batch_size") != 4
            or config.get("adaptive_batch") is not True
            or config.get("max_removals") != 160
            or sweep.get("attempted_gaps") != 21
            or sweep.get("accepted_routes") != 0
            or sweep.get("output_board_sha256") != fine.get("output_board_sha256")
            or any(final.get(kind) != 0 for kind in ("short", "clearance", "track_crossing", "hole_clearance", "hole_to_hole", "copper_edge_clearance"))
            or len(fine.get("residual_nets", [])) != 21
        ):
            failures.append("current 21-gap fine-prune summary is malformed")
        for key in ("tool_sha256", "sweep_tool_sha256"):
            for relative, expected in fine.get(key, {}).items():
                tool_path = ROOT / relative
                if not tool_path.is_file() or sha256(tool_path) != expected:
                    failures.append(f"fine-prune tool hash changed: {relative}")
        for path in ("PLAN.md", "docs/routed-refresh-audit.md"):
            if "current21-fine-dangling-prune.json" not in read(path):
                failures.append(f"{path} omits the fine dangling-prune evidence")

    twoitem_path = ROOT / "ref/routing/current21-twoitem-dangling-prune.json"
    if not twoitem_path.exists():
        failures.append("current 21-gap two-item-prune evidence is missing")
    else:
        twoitem = json.loads(twoitem_path.read_text(encoding="utf-8"))
        initial = twoitem.get("initial", {})
        final = twoitem.get("final", {})
        config = twoitem.get("config", {})
        sweep = twoitem.get("post_prune_sweep", {})
        if (
            twoitem.get("schema_version") != 1
            or (initial.get("unconnected"), final.get("unconnected")) != (21, 21)
            or twoitem.get("removed_items") != 102
            or twoitem.get("removed_source_items") != 0
            or (initial.get("track_dangling"), initial.get("via_dangling")) != (14, 0)
            or (final.get("track_dangling"), final.get("via_dangling")) != (13, 0)
            or config.get("batch_size") != 2
            or config.get("adaptive_batch") is not True
            or config.get("max_removals") != 102
            or sweep.get("attempted_gaps") != 21
            or sweep.get("accepted_routes") != 0
            or sweep.get("output_board_sha256") != twoitem.get("output_board_sha256")
            or any(final.get(kind) != 0 for kind in ("short", "clearance", "track_crossing", "hole_clearance", "hole_to_hole", "copper_edge_clearance"))
            or len(twoitem.get("residual_nets", [])) != 21
        ):
            failures.append("current 21-gap two-item-prune summary is malformed")
        for key in ("tool_sha256", "sweep_tool_sha256"):
            for relative, expected in twoitem.get(key, {}).items():
                tool_path = ROOT / relative
                if not tool_path.is_file() or sha256(tool_path) != expected:
                    failures.append(f"two-item-prune tool hash changed: {relative}")
        for path in ("PLAN.md", "docs/routed-refresh-audit.md"):
            if "current21-twoitem-dangling-prune.json" not in read(path):
                failures.append(f"{path} omits the two-item dangling-prune evidence")

    eleven_path = ROOT / "ref/routing/current21-eleven-tail-prune.json"
    if not eleven_path.exists():
        failures.append("current 21-gap eleven-tail-prune evidence is missing")
    else:
        eleven = json.loads(eleven_path.read_text(encoding="utf-8"))
        initial = eleven.get("initial", {})
        final = eleven.get("final", {})
        config = eleven.get("config", {})
        sweep = eleven.get("post_prune_sweep", {})
        if (
            eleven.get("schema_version") != 1
            or (initial.get("unconnected"), final.get("unconnected")) != (21, 21)
            or eleven.get("removed_items") != 70
            or eleven.get("removed_source_items") != 0
            or (initial.get("track_dangling"), initial.get("via_dangling")) != (13, 0)
            or (final.get("track_dangling"), final.get("via_dangling")) != (10, 1)
            or config.get("batch_size") != 2
            or config.get("adaptive_batch") is not True
            or config.get("max_removals") != 70
            or sweep.get("attempted_gaps") != 21
            or sweep.get("accepted_routes") != 0
            or sweep.get("output_board_sha256") != eleven.get("output_board_sha256")
            or any(final.get(kind) != 0 for kind in ("short", "clearance", "track_crossing", "hole_clearance", "hole_to_hole", "copper_edge_clearance"))
            or len(eleven.get("residual_nets", [])) != 21
        ):
            failures.append("current 21-gap eleven-tail-prune summary is malformed")
        for key in ("tool_sha256", "sweep_tool_sha256"):
            for relative, expected in eleven.get(key, {}).items():
                tool_path = ROOT / relative
                if not tool_path.is_file() or sha256(tool_path) != expected:
                    failures.append(f"eleven-tail-prune tool hash changed: {relative}")
        for path in ("PLAN.md", "docs/routed-refresh-audit.md"):
            if "current21-eleven-tail-prune.json" not in read(path):
                failures.append(f"{path} omits the eleven-tail dangling-prune evidence")

    ten_path = ROOT / "ref/routing/current21-ten-tail-prune.json"
    if not ten_path.exists():
        failures.append("current 21-gap ten-tail-prune evidence is missing")
    else:
        ten = json.loads(ten_path.read_text(encoding="utf-8"))
        initial = ten.get("initial", {})
        final = ten.get("final", {})
        config = ten.get("config", {})
        phases = config.get("phases", [])
        sweep = ten.get("post_prune_sweep", {})
        if (
            ten.get("schema_version") != 1
            or (initial.get("unconnected"), final.get("unconnected")) != (21, 21)
            or ten.get("removed_items") != 13
            or ten.get("removed_source_items") != 0
            or (initial.get("track_dangling"), initial.get("via_dangling")) != (10, 1)
            or (final.get("track_dangling"), final.get("via_dangling")) != (10, 0)
            or phases != [{"batch_size": 2, "removed_items": 6}, {"batch_size": 1, "removed_items": 7}]
            or sweep.get("attempted_gaps") != 21
            or sweep.get("accepted_routes") != 0
            or sweep.get("output_board_sha256") != ten.get("output_board_sha256")
            or any(final.get(kind) != 0 for kind in ("short", "clearance", "track_crossing", "hole_clearance", "hole_to_hole", "copper_edge_clearance"))
            or len(ten.get("residual_nets", [])) != 21
        ):
            failures.append("current 21-gap ten-tail-prune summary is malformed")
        for key in ("tool_sha256", "sweep_tool_sha256"):
            for relative, expected in ten.get(key, {}).items():
                tool_path = ROOT / relative
                if not tool_path.is_file() or sha256(tool_path) != expected:
                    failures.append(f"ten-tail-prune tool hash changed: {relative}")
        for path in ("PLAN.md", "docs/routed-refresh-audit.md"):
            if "current21-ten-tail-prune.json" not in read(path):
                failures.append(f"{path} omits the ten-tail dangling-prune evidence")

    plateau_path = ROOT / "ref/routing/current21-ten-tail-plateau-prune.json"
    if not plateau_path.exists():
        failures.append("current 21-gap ten-tail plateau evidence is missing")
    else:
        plateau = json.loads(plateau_path.read_text(encoding="utf-8"))
        initial = plateau.get("initial", {})
        final = plateau.get("final", {})
        config = plateau.get("config", {})
        sweep = plateau.get("post_prune_sweep", {})
        if (
            plateau.get("schema_version") != 1
            or (initial.get("unconnected"), final.get("unconnected")) != (21, 21)
            or plateau.get("removed_items") != 30
            or plateau.get("removed_source_items") != 0
            or (initial.get("track_dangling"), initial.get("via_dangling")) != (10, 0)
            or (final.get("track_dangling"), final.get("via_dangling")) != (10, 0)
            or sum(phase.get("removed_items", 0) for phase in config.get("phases", [])) != 30
            or sweep.get("attempted_gaps") != 21
            or sweep.get("accepted_routes") != 0
            or sweep.get("output_board_sha256") != plateau.get("output_board_sha256")
            or any(final.get(kind) != 0 for kind in ("short", "clearance", "track_crossing", "hole_clearance", "hole_to_hole", "copper_edge_clearance"))
            or len(plateau.get("residual_nets", [])) != 21
        ):
            failures.append("current 21-gap ten-tail plateau summary is malformed")
        for key in ("tool_sha256", "sweep_tool_sha256"):
            for relative, expected in plateau.get(key, {}).items():
                tool_path = ROOT / relative
                if not tool_path.is_file() or sha256(tool_path) != expected:
                    failures.append(f"ten-tail plateau tool hash changed: {relative}")
        for path in ("PLAN.md", "docs/routed-refresh-audit.md"):
            if "current21-ten-tail-plateau-prune.json" not in read(path):
                failures.append(f"{path} omits the ten-tail plateau evidence")

    nine_path = ROOT / "ref/routing/current21-nine-tail-prune.json"
    if not nine_path.exists():
        failures.append("current 21-gap nine-tail-prune evidence is missing")
    else:
        nine = json.loads(nine_path.read_text(encoding="utf-8"))
        initial = nine.get("initial", {})
        final = nine.get("final", {})
        config = nine.get("config", {})
        sweep = nine.get("post_prune_sweep", {})
        if (
            nine.get("schema_version") != 1
            or (initial.get("unconnected"), final.get("unconnected")) != (21, 21)
            or nine.get("removed_items") != 14
            or nine.get("removed_source_items") != 0
            or (initial.get("track_dangling"), initial.get("via_dangling")) != (10, 0)
            or (final.get("track_dangling"), final.get("via_dangling")) != (9, 0)
            or config.get("batch_size") != 2
            or config.get("max_removals") != 14
            or sweep.get("attempted_gaps") != 21
            or sweep.get("accepted_routes") != 0
            or sweep.get("output_board_sha256") != nine.get("output_board_sha256")
            or any(final.get(kind) != 0 for kind in ("short", "clearance", "track_crossing", "hole_clearance", "hole_to_hole", "copper_edge_clearance"))
            or len(nine.get("residual_nets", [])) != 21
        ):
            failures.append("current 21-gap nine-tail-prune summary is malformed")
        for key in ("tool_sha256", "sweep_tool_sha256"):
            for relative, expected in nine.get(key, {}).items():
                tool_path = ROOT / relative
                if not tool_path.is_file() or sha256(tool_path) != expected:
                    failures.append(f"nine-tail-prune tool hash changed: {relative}")
        for path in ("PLAN.md", "docs/routed-refresh-audit.md"):
            if "current21-nine-tail-prune.json" not in read(path):
                failures.append(f"{path} omits the nine-tail dangling-prune evidence")

    nine_plateau_path = ROOT / "ref/routing/current21-nine-tail-plateau-prune.json"
    if not nine_plateau_path.exists():
        failures.append("current 21-gap nine-tail plateau evidence is missing")
    else:
        plateau = json.loads(nine_plateau_path.read_text(encoding="utf-8"))
        initial = plateau.get("initial", {})
        final = plateau.get("final", {})
        config = plateau.get("config", {})
        sweep = plateau.get("post_prune_sweep", {})
        if (
            plateau.get("schema_version") != 1
            or (initial.get("unconnected"), final.get("unconnected")) != (21, 21)
            or plateau.get("removed_items") != 30
            or plateau.get("removed_source_items") != 0
            or (initial.get("track_dangling"), initial.get("via_dangling")) != (9, 0)
            or (final.get("track_dangling"), final.get("via_dangling")) != (9, 0)
            or config.get("accepted_batch_size") != 1
            or config.get("max_removals") != 30
            or sweep.get("attempted_gaps") != 21
            or sweep.get("accepted_routes") != 0
            or sweep.get("output_board_sha256") != plateau.get("output_board_sha256")
            or any(final.get(kind) != 0 for kind in ("short", "clearance", "track_crossing", "hole_clearance", "hole_to_hole", "copper_edge_clearance"))
            or len(plateau.get("residual_nets", [])) != 21
        ):
            failures.append("current 21-gap nine-tail plateau summary is malformed")
        for key in ("tool_sha256", "sweep_tool_sha256"):
            for relative, expected in plateau.get(key, {}).items():
                tool_path = ROOT / relative
                if not tool_path.is_file() or sha256(tool_path) != expected:
                    failures.append(f"nine-tail plateau tool hash changed: {relative}")
        for path in ("PLAN.md", "docs/routed-refresh-audit.md"):
            if "current21-nine-tail-plateau-prune.json" not in read(path):
                failures.append(f"{path} omits the nine-tail plateau evidence")

    eight_path = ROOT / "ref/routing/current21-eight-tail-prune.json"
    if not eight_path.exists():
        failures.append("current 21-gap eight-tail-prune evidence is missing")
    else:
        eight = json.loads(eight_path.read_text(encoding="utf-8"))
        initial = eight.get("initial", {})
        final = eight.get("final", {})
        config = eight.get("config", {})
        sweep = eight.get("post_prune_sweep", {})
        if (
            eight.get("schema_version") != 1
            or (initial.get("unconnected"), final.get("unconnected")) != (21, 21)
            or eight.get("removed_items") != 56
            or eight.get("removed_source_items") != 0
            or (initial.get("track_dangling"), initial.get("via_dangling")) != (9, 0)
            or (final.get("track_dangling"), final.get("via_dangling")) != (8, 0)
            or config.get("batch_size") != 1
            or sum(phase.get("removed_items", 0) for phase in config.get("phases", [])) != 56
            or sweep.get("attempted_gaps") != 21
            or sweep.get("accepted_routes") != 0
            or sweep.get("output_board_sha256") != eight.get("output_board_sha256")
            or any(final.get(kind) != 0 for kind in ("short", "clearance", "track_crossing", "hole_clearance", "hole_to_hole", "copper_edge_clearance"))
            or len(eight.get("residual_nets", [])) != 21
        ):
            failures.append("current 21-gap eight-tail-prune summary is malformed")
        for key in ("tool_sha256", "sweep_tool_sha256"):
            for relative, expected in eight.get(key, {}).items():
                tool_path = ROOT / relative
                if not tool_path.is_file() or sha256(tool_path) != expected:
                    failures.append(f"eight-tail-prune tool hash changed: {relative}")
        for path in ("PLAN.md", "docs/routed-refresh-audit.md"):
            if "current21-eight-tail-prune.json" not in read(path):
                failures.append(f"{path} omits the eight-tail dangling-prune evidence")

    seven_path = ROOT / "ref/routing/current21-seven-tail-prune.json"
    if not seven_path.exists():
        failures.append("current 21-gap seven-tail-prune evidence is missing")
    else:
        seven = json.loads(seven_path.read_text(encoding="utf-8"))
        initial = seven.get("initial", {})
        final = seven.get("final", {})
        config = seven.get("config", {})
        sweep = seven.get("post_prune_sweep", {})
        if (
            seven.get("schema_version") != 1
            or (initial.get("unconnected"), final.get("unconnected")) != (21, 21)
            or seven.get("removed_items") != 27
            or seven.get("removed_source_items") != 0
            or (initial.get("track_dangling"), initial.get("via_dangling")) != (8, 0)
            or (final.get("track_dangling"), final.get("via_dangling")) != (7, 0)
            or config.get("batch_size") != 1
            or config.get("max_removals") != 27
            or sweep.get("attempted_gaps") != 21
            or sweep.get("accepted_routes") != 0
            or sweep.get("output_board_sha256") != seven.get("output_board_sha256")
            or any(final.get(kind) != 0 for kind in ("short", "clearance", "track_crossing", "hole_clearance", "hole_to_hole", "copper_edge_clearance"))
            or len(seven.get("residual_nets", [])) != 21
        ):
            failures.append("current 21-gap seven-tail-prune summary is malformed")
        for key in ("tool_sha256", "sweep_tool_sha256"):
            for relative, expected in seven.get(key, {}).items():
                tool_path = ROOT / relative
                if not tool_path.is_file() or sha256(tool_path) != expected:
                    failures.append(f"seven-tail-prune tool hash changed: {relative}")
        for path in ("PLAN.md", "docs/routed-refresh-audit.md"):
            if "current21-seven-tail-prune.json" not in read(path):
                failures.append(f"{path} omits the seven-tail dangling-prune evidence")

    seven_plateau_path = ROOT / "ref/routing/current21-seven-tail-plateau-prune.json"
    if not seven_plateau_path.exists():
        failures.append("current 21-gap seven-tail plateau evidence is missing")
    else:
        plateau = json.loads(seven_plateau_path.read_text(encoding="utf-8"))
        initial = plateau.get("initial", {})
        final = plateau.get("final", {})
        config = plateau.get("config", {})
        sweep = plateau.get("post_prune_sweep", {})
        if (
            plateau.get("schema_version") != 1
            or (initial.get("unconnected"), final.get("unconnected")) != (21, 21)
            or plateau.get("removed_items") != 60
            or plateau.get("removed_source_items") != 0
            or (initial.get("track_dangling"), initial.get("via_dangling")) != (7, 0)
            or (final.get("track_dangling"), final.get("via_dangling")) != (7, 0)
            or config.get("batch_size") != 1
            or sum(phase.get("removed_items", 0) for phase in config.get("phases", [])) != 60
            or sweep.get("attempted_gaps") != 21
            or sweep.get("accepted_routes") != 0
            or sweep.get("output_board_sha256") != plateau.get("output_board_sha256")
            or any(final.get(kind) != 0 for kind in ("short", "clearance", "track_crossing", "hole_clearance", "hole_to_hole", "copper_edge_clearance"))
            or len(plateau.get("residual_nets", [])) != 21
        ):
            failures.append("current 21-gap seven-tail plateau summary is malformed")
        for key in ("tool_sha256", "sweep_tool_sha256"):
            for relative, expected in plateau.get(key, {}).items():
                tool_path = ROOT / relative
                if not tool_path.is_file() or sha256(tool_path) != expected:
                    failures.append(f"seven-tail plateau tool hash changed: {relative}")
        for path in ("PLAN.md", "docs/routed-refresh-audit.md"):
            if "current21-seven-tail-plateau-prune.json" not in read(path):
                failures.append(f"{path} omits the seven-tail plateau evidence")

    seven_deep_path = ROOT / "ref/routing/current21-seven-tail-deep-prune.json"
    if not seven_deep_path.exists():
        failures.append("current 21-gap seven-tail deep-prune evidence is missing")
    else:
        deep = json.loads(seven_deep_path.read_text(encoding="utf-8"))
        initial = deep.get("initial", {})
        final = deep.get("final", {})
        config = deep.get("config", {})
        sweep = deep.get("post_prune_sweep", {})
        if (
            deep.get("schema_version") != 1
            or (initial.get("unconnected"), final.get("unconnected")) != (21, 21)
            or deep.get("removed_items") != 30
            or deep.get("removed_source_items") != 0
            or (initial.get("track_dangling"), initial.get("via_dangling")) != (7, 0)
            or (final.get("track_dangling"), final.get("via_dangling")) != (7, 0)
            or config.get("batch_size") != 1
            or config.get("max_removals") != 30
            or sweep.get("attempted_gaps") != 21
            or sweep.get("accepted_routes") != 0
            or sweep.get("output_board_sha256") != deep.get("output_board_sha256")
            or any(final.get(kind) != 0 for kind in ("short", "clearance", "track_crossing", "hole_clearance", "hole_to_hole", "copper_edge_clearance"))
            or len(deep.get("residual_nets", [])) != 21
        ):
            failures.append("current 21-gap seven-tail deep-prune summary is malformed")
        for key in ("tool_sha256", "sweep_tool_sha256"):
            for relative, expected in deep.get(key, {}).items():
                tool_path = ROOT / relative
                if not tool_path.is_file() or sha256(tool_path) != expected:
                    failures.append(f"seven-tail deep-prune tool hash changed: {relative}")
        for path in ("PLAN.md", "docs/routed-refresh-audit.md"):
            if "current21-seven-tail-deep-prune.json" not in read(path):
                failures.append(f"{path} omits the seven-tail deep-prune evidence")

    vjuga = {
        "spinoffs/minimal-vga/README.md": read("spinoffs/minimal-vga/README.md"),
        "spinoffs/minimal-vga/docs/rev-a-manufacturing-readiness.md": read(
            "spinoffs/minimal-vga/docs/rev-a-manufacturing-readiness.md"
        ),
        "spinoffs/minimal-vga/kicad/fab-notes.md": read("spinoffs/minimal-vga/kicad/fab-notes.md"),
    }
    vjuga_boot_docs = {
        **vjuga,
        "spinoffs/minimal-vga/hdl/README.md": read("spinoffs/minimal-vga/hdl/README.md"),
        "spinoffs/minimal-vga/sim/README.md": read("spinoffs/minimal-vga/sim/README.md"),
    }
    for path, text in vjuga.items():
        if "hold" not in text.lower():
            failures.append(f"{path} does not expose the VJUGA design hold")
        if "READY TO UPLOAD" in text or "READY FOR VENDOR PREVIEW" in text:
            failures.append(f"{path} contains obsolete VJUGA release language")
    stale_vjuga_boot_claims = (
        "No real Juku ROM has booted",
        "real Juku ROM boot on the T80/VJUGA top is unproven",
        "next meaningful simulation milestone is a real Juku ROM boot",
    )
    for path, text in vjuga_boot_docs.items():
        for claim in stale_vjuga_boot_claims:
            if claim.lower() in text.lower():
                failures.append(f"{path} retains stale VJUGA boot claim: {claim!r}")
    vjuga_readiness = vjuga["spinoffs/minimal-vga/docs/rev-a-manufacturing-readiness.md"]
    for marker in ("sim/boot_check.sh", "sim/vjuga_boot_check.sh", "6000 writes"):
        if marker not in vjuga_readiness:
            failures.append(f"VJUGA readiness omits real-ROM boot evidence {marker!r}")
    vjuga_gal = read("spinoffs/minimal-vga/docs/rev-a-gal-equations.md")
    for marker in (
        "Status: **DECODE + DRAM TIMING SIMULATED / PROGRAMMING UNVALIDATED**",
        "sim/u24_dram_timing_check.sh",
        "Pin 13 is the GAL22V10's twelfth input/OE pin",
        "CPU request colliding",
    ):
        if marker not in vjuga_gal:
            failures.append(f"VJUGA GAL contract omits U24 evidence {marker!r}")
    if "U24's Gray-coded DRAM timing contract passes" not in vjuga_readiness:
        failures.append("VJUGA readiness does not expose passing U24 timing evidence")
    vjuga_board_path = ROOT / "spinoffs/minimal-vga/kicad/rev-a-physical.board.json"
    if vjuga_board_path.exists():
        vjuga_board = json.loads(vjuga_board_path.read_text(encoding="utf-8"))
        vjuga_refs = len(vjuga_board.get("chips", {}))
        vjuga_nets = len(vjuga_board.get("nets", {}))
        for path in (
            "PLAN.md",
            "spinoffs/minimal-vga/README.md",
            "spinoffs/minimal-vga/docs/rev-a-manufacturing-readiness.md",
        ):
            text = read(path)
            if not re.search(
                rf"{vjuga_refs} refs?\s*(?:/|and)\s*{vjuga_nets}\s+(?:modeled\s+)?nets",
                text,
            ):
                failures.append(
                    f"{path} does not expose current VJUGA scope "
                    f"{vjuga_refs} refs/{vjuga_nets} nets"
                )
    vjuga_pcb_path = ROOT / "spinoffs/minimal-vga/kicad/rev-a-physical.kicad_pcb"
    if vjuga_pcb_path.exists():
        vjuga_pcb = vjuga_pcb_path.read_text(encoding="utf-8", errors="replace")
        vjuga_tracks = len(re.findall(r"(?m)^\s*\((?:segment|arc|via)\b", vjuga_pcb))
        vjuga_zones = len(re.findall(r"(?m)^\s*\(zone\b", vjuga_pcb))
        if f"{vjuga_tracks:,} tracks" not in read("PLAN.md"):
            failures.append(f"PLAN does not expose current VJUGA track total {vjuga_tracks:,}")
        readiness = read("spinoffs/minimal-vga/docs/rev-a-manufacturing-readiness.md")
        if f"{vjuga_tracks:,} F.Cu/B.Cu tracks" not in readiness:
            failures.append(
                f"VJUGA readiness does not expose current track total {vjuga_tracks:,}"
            )
        if vjuga_zones != 2 or "filled In1.Cu GND and In2.Cu VCC planes" not in readiness:
            failures.append("VJUGA readiness does not expose the two filled power planes")
    vjuga_zip = ROOT / "fab" / "minimal-vga" / "upload" / "vjuga-rev-a-gerbers-drill.zip"
    if vjuga_zip.exists():
        vjuga_digest = sha256(vjuga_zip)
        if vjuga_digest not in vjuga["spinoffs/minimal-vga/docs/rev-a-manufacturing-readiness.md"]:
            failures.append(f"VJUGA readiness does not contain current Gerber ZIP SHA256 {vjuga_digest}")

    cartridge = read("docs/cartridge-basic-boundary.md")
    cartridge_lineage = read("docs/cartridge-basic-firmware-lineage.md")
    jmon22_reconstruction = read("docs/jmon22-reconstruction.md")
    cartridge_image = ROOT / "roms" / "jbasic11.bin"
    if "Status: **ARTIFACT OR DOCUMENTED PROCEDURE REQUIRED**" not in cartridge:
        failures.append("consolidated cartridge BASIC boundary is missing or stale")
    if cartridge_image.exists() and sha256(cartridge_image) not in cartridge:
        failures.append("cartridge BASIC boundary does not contain the current jbasic11 SHA256")
    if "Status: **ONBOARD BASIC LINEAGE PINNED / MISSING PAGE NOT DERIVED**" not in cartridge_lineage:
        failures.append("cartridge BASIC firmware-lineage audit is missing or stale")
    if cartridge_image.exists():
        cartridge_bytes = cartridge_image.read_bytes()
        monitor33_path = ROOT / "roms" / "jmon33.bin"
        monitor22_path = ROOT / "roms" / "jmon22.bin"
        if len(cartridge_bytes) != 0x2000:
            failures.append("jbasic11 image is no longer the audited 8 KiB shape")
        elif not monitor33_path.exists() or not monitor22_path.exists():
            failures.append("cartridge BASIC lineage monitor input is missing")
        else:
            monitor33 = monitor33_path.read_bytes()
            monitor22 = monitor22_path.read_bytes()
            body = cartridge_bytes[0x0100:0x1D38]
            if body != monitor33[0x03C8:0x2000]:
                failures.append("jbasic11/Monitor 3.3 exact BASIC-body lineage changed")
            mismatch_count = sum(
                left != right
                for left, right in zip(body, monitor22[0x03C8:0x2000], strict=True)
            )
            if mismatch_count != 1:
                failures.append(
                    "jbasic11/Monitor 2.2 BASIC-body lineage no longer has one mismatch"
                )
            if any(cartridge_bytes[0x1D38:0x1F00]):
                failures.append("jbasic11 padding before the relocation bootstrap is no longer zero")
            loop_tail = bytes.fromhex("7e 12 23 13 0b 78 b1 c2 09 20 c3 00 01")
            if cartridge_bytes[0x1F09:0x1F16] != loop_tail:
                failures.append("jbasic11 relocation bootstrap survival bytes changed")
            for marker in (
                "`7224` bytes (`0x1C38`)",
                "cartridge `0x1C34=0xDA`; Monitor ROM `0x1EFC=0x9A`",
                "blocks 3, 6, and 7",
            ):
                if marker not in cartridge_lineage:
                    failures.append(
                        f"cartridge BASIC firmware-lineage report is stale; missing {marker!r}"
                    )
    for marker in (
        "Status: **ONE BYTE PROVEN / ROM BLOCKS 6-7 UNRESOLVED**",
        "block 3 `0xF3` -> stored `0x33`",
        "UNRESOLVED (checksum delta `+0x40`)",
        "UNRESOLVED (checksum delta `+0xA3`)",
        "| `6` | `+0x40` | `2048` | `2048` | `898` | `0` | `0` |",
        "| `7` | `+0xA3` | `2048` | `2045` | `0` | `6` | `0` |",
        "changing `0x3BAA` from `0x21` to `0xC4`",
        "`LXI H,$FF21; SHLD $0031`",
        "jmon22-consensus-patch.json",
    ):
        if marker not in jmon22_reconstruction:
            failures.append(f"Monitor 2.2 reconstruction audit is stale; missing {marker!r}")

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
