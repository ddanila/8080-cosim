#!/usr/bin/env python3
"""Validate explicit deployment profiles for the four recorded Juku boards."""

from __future__ import annotations

from datetime import date
import hashlib
import json
from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]
PROFILE_DIR = ROOT / "docs/machines"
EXPECTED = {"CS00000", "CS00014", "CS00015", "CS00024"}
SHA256 = re.compile(r"^[0-9a-f]{64}$")


def resolve_evidence(value: str) -> Path:
    path = (ROOT / value).resolve()
    if path.is_file():
        return path
    sibling = (ROOT.parent / value.removeprefix("../")).resolve()
    if sibling.is_file():
        return sibling
    raise AssertionError(f"missing profile evidence: {value}")


def main() -> int:
    schema_path = PROFILE_DIR / "machine-profile.schema.json"
    schema = json.loads(schema_path.read_text())
    if schema.get("$schema") != "https://json-schema.org/draft/2020-12/schema":
        raise AssertionError("machine profile schema is not draft 2020-12")

    paths = sorted(PROFILE_DIR.glob("CS*.json"))
    if {path.stem for path in paths} != EXPECTED:
        raise AssertionError("machine profile set differs from the four-board ledger")
    digests: list[str] = []
    for path in paths:
        record = json.loads(path.read_text())
        if record.get("schema") != "juku-machine-profile-v1":
            raise AssertionError(f"wrong schema in {path.name}")
        if record.get("machine_id") != path.stem:
            raise AssertionError(f"machine identity differs in {path.name}")
        date.fromisoformat(record["updated"])
        firmware = record.get("fitted_firmware", {})
        if set(firmware) != {"identity", "sha256", "confidence"}:
            raise AssertionError(f"incomplete firmware record in {path.name}")
        if firmware["confidence"] not in {"physical-record", "owner-report", "unknown"}:
            raise AssertionError(f"invalid confidence in {path.name}")
        if firmware["sha256"] is not None and not SHA256.fullmatch(firmware["sha256"]):
            raise AssertionError(f"invalid firmware SHA-256 in {path.name}")
        if not record.get("deployment_role") or not record.get("evidence"):
            raise AssertionError(f"profile lacks role or evidence: {path.name}")
        for evidence in record["evidence"]:
            resolve_evidence(evidence)
        digests.append(hashlib.sha256(path.read_bytes()).hexdigest()[:8])

    c15 = json.loads((PROFILE_DIR / "CS00015.json").read_text())
    if c15["fitted_firmware"]["identity"] != "JukuNet C5 D15/D16":
        raise AssertionError("CS00015 fitted firmware regressed to a pre-C5 record")
    c24 = json.loads((PROFILE_DIR / "CS00024.json").read_text())
    if not any("D57" in item for item in c24["open_investigations"]):
        raise AssertionError("CS00024 corrected D57 rerun is not retained")

    print(
        "MACHINE-PROFILES: PASS "
        f"({', '.join(sorted(EXPECTED))}; records {'/'.join(digests)})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
