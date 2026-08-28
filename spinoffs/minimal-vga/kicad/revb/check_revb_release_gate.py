#!/usr/bin/env python3
"""Validate the held R5.R1 release record without granting authorization.

The default success state is TECHNICAL PASS / ORDER HOLD. --require-released
additionally requires a hash-bound owner authorization and the controlling plan
to say RELEASED FOR UPLOAD. This tool never changes either state.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import re
import sys
from pathlib import Path


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
RECORD_PATH = REPO / "spinoffs" / "minimal-vga" / "docs" / "rev-b-five-board-release-gate.json"
EXPECTED_CARDS = {"cpu", "mem", "io", "backplane", "video"}
EXPECTED_GATES = {
    "R5.S1_serial_path",
    "R5.S2_serial_electrical",
    "R5.S3_serial_c10",
    "R5.P1_programmable_logic",
    "R5.V1_video_connectivity",
    "R5.V2_video_power_rgb",
    "R5.V3_video_gals",
    "R5.V4_exact_parts",
    "R5.V5_video_pcb",
    "R5.V6_system_physical_power",
    "R5.J1_jlcpcb_profile",
    "R5.J2_five_archives",
    "R5.J3_independent_review_quote",
}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def repo_path(value: str) -> Path:
    path = (REPO / value).resolve()
    if path != REPO and REPO not in path.parents:
        raise ValueError(f"path escapes repository: {value}")
    return path


def verify(record: dict, package_root: Path | None = None) -> list[str]:
    errors: list[str] = []
    if record.get("schema") != 1:
        errors.append("release record schema is not 1")
    status = record.get("status")
    if status not in {"ORDER HOLD", "RELEASED FOR UPLOAD"}:
        errors.append(f"unknown release status {status!r}")

    candidate = record.get("candidate", {})
    evidence = record.get("evidence", {})
    policy = record.get("release_policy", {})
    try:
        manifest_path = repo_path(candidate.get("package_manifest", ""))
        plan_path = repo_path(evidence.get("controlling_plan", ""))
        review_path = repo_path(evidence.get("preupload_review", ""))
        bom_path = repo_path(evidence.get("bom_contract", ""))
        profile_path = repo_path(evidence.get("jlcpcb_profile", ""))
    except (TypeError, ValueError) as exc:
        return [str(exc)]
    for label, path in (("manifest", manifest_path), ("plan", plan_path),
                        ("review", review_path), ("BOM", bom_path),
                        ("profile", profile_path)):
        if not path.is_file():
            errors.append(f"{label} evidence missing: {path}")
    if errors:
        return errors

    if digest(manifest_path) != candidate.get("package_manifest_sha256"):
        errors.append("package manifest hash differs from release record")
    if digest(review_path) != evidence.get("preupload_review_sha256"):
        errors.append("pre-upload review hash differs from release record")
    if digest(profile_path) != candidate.get("jlcpcb_profile_sha256"):
        errors.append("JLCPCB profile hash differs from release record")

    try:
        manifest = json.loads(manifest_path.read_text())
        json.loads(bom_path.read_text())
        json.loads(profile_path.read_text())
    except json.JSONDecodeError as exc:
        return errors + [f"tracked JSON evidence is invalid: {exc}"]
    archives = candidate.get("archives", {})
    manifest_archives = {
        card: spec.get("archive_sha256")
        for card, spec in manifest.get("cards", {}).items()
    }
    if set(archives) != EXPECTED_CARDS or archives != manifest_archives:
        errors.append("candidate archive hashes differ from the five-card manifest")
    if candidate.get("source_revision") != manifest.get("source_revision"):
        errors.append("candidate source revision differs from manifest")
    if candidate.get("jlcpcb_profile_sha256") != manifest.get("jlcpcb_profile_sha256"):
        errors.append("candidate profile hash differs from manifest")
    if "ORDER HOLD" not in manifest.get("status", ""):
        errors.append("package manifest no longer identifies an ORDER HOLD candidate")

    if package_root is not None:
        package_root = package_root.resolve()
        for card, wanted in archives.items():
            archive = package_root / f"{card}.zip"
            if not archive.is_file():
                errors.append(f"release archive missing: {archive}")
            elif digest(archive) != wanted:
                errors.append(f"{card}.zip differs from release hash")

    gates = record.get("technical_gates", {})
    if set(gates) != EXPECTED_GATES:
        errors.append(f"technical-gate set differs: {sorted(set(gates) ^ EXPECTED_GATES)}")
    if any(value != "PASS" for value in gates.values()):
        errors.append("not every technical gate is PASS")

    plan = plan_path.read_text()
    review = review_path.read_text()
    for gate in EXPECTED_GATES:
        task = gate.split("_", 1)[0]
        if not re.search(rf"\*\*{re.escape(task)}[^*]*DONE \d{{4}}-\d{{2}}-\d{{2}}", plan):
            errors.append(f"controlling plan does not mark {task} DONE")
    if "Status: **PASS / ORDER HOLD**" not in review or "Review signature:" not in review:
        errors.append("pre-upload review lacks held PASS status or signature")
    for card, wanted in archives.items():
        if wanted not in review or wanted not in plan:
            errors.append(f"{card}: exact release hash is not cross-recorded")

    required_text = policy.get("required_authorization_text")
    if policy.get("required_status") != "RELEASED FOR UPLOAD" or not required_text:
        errors.append("release policy is incomplete")
    authorization = record.get("owner_authorization")
    if status == "ORDER HOLD":
        if authorization is not None:
            errors.append("ORDER HOLD record must not contain owner authorization")
        if "Status: **ACTIVE PLAN / ORDER HOLD**" not in plan:
            errors.append("controlling plan no longer agrees with ORDER HOLD")
        if "**PENDING:** The owner explicitly authorizes upload" not in plan:
            errors.append("controlling plan no longer exposes the owner authorization hold")
    elif status == "RELEASED FOR UPLOAD":
        if not isinstance(authorization, dict):
            errors.append("released record lacks owner authorization")
        else:
            if not str(authorization.get("authorized_by", "")).strip():
                errors.append("owner authorization lacks authorized_by")
            if not re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}[+-]\d{2}:\d{2}",
                                str(authorization.get("authorized_at", ""))):
                errors.append("owner authorization lacks an ISO-8601 timestamp")
            if authorization.get("authorization_text") != required_text:
                errors.append("owner authorization text is not the exact required phrase")
            if authorization.get("archives") != archives:
                errors.append("owner authorization is not bound to the exact five hashes")
        if "Status: **RELEASED FOR UPLOAD**" not in plan:
            errors.append("controlling plan does not say RELEASED FOR UPLOAD")
        if "**PENDING:** The owner explicitly authorizes upload" in plan:
            errors.append("controlling plan still marks owner authorization pending")
    return errors


def self_test(record: dict) -> list[str]:
    failures: list[str] = []
    mutated = copy.deepcopy(record)
    mutated["candidate"]["archives"]["video"] = "0" * 64
    if not any("archive hashes differ" in error for error in verify(mutated)):
        failures.append("stale Video hash mutation was accepted")
    mutated = copy.deepcopy(record)
    mutated["status"] = "RELEASED FOR UPLOAD"
    if not any("lacks owner authorization" in error for error in verify(mutated)):
        failures.append("release without owner authorization was accepted")
    mutated = copy.deepcopy(record)
    mutated["owner_authorization"] = {"authorization_text": "release it"}
    if not any("must not contain owner authorization" in error for error in verify(mutated)):
        failures.append("authorization smuggled into ORDER HOLD was accepted")
    mutated = copy.deepcopy(record)
    mutated["candidate"]["package_manifest_sha256"] = "f" * 64
    if not any("manifest hash differs" in error for error in verify(mutated)):
        failures.append("stale manifest hash mutation was accepted")
    return failures


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--package-root", type=Path)
    parser.add_argument("--require-released", action="store_true")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    try:
        record = json.loads(RECORD_PATH.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        print(f"R5.R1 release gate FAILED: {exc}")
        return 1
    errors = verify(record, args.package_root)
    if args.self_test:
        errors.extend(f"self-test: {error}" for error in self_test(record))
    if errors:
        print("R5.R1 release gate FAILED:")
        for error in errors:
            print(f"- {error}")
        return 1
    if record["status"] == "ORDER HOLD":
        print("R5.R1 release gate: TECHNICAL PASS / ORDER HOLD — exact five hashes verified; owner authorization absent")
        if args.self_test:
            print("R5.R1 negative controls PASS: stale hash/manifest and unauthorized-release mutations rejected")
        return 3 if args.require_released else 0
    print("R5.R1 release gate: RELEASED FOR UPLOAD — explicit owner authorization matches exact five hashes")
    if args.self_test:
        print("R5.R1 negative controls PASS: stale hash/manifest and unauthorized-release mutations rejected")
    return 0


if __name__ == "__main__":
    sys.exit(main())
