#!/usr/bin/env python3
"""Check that the living project summary mirrors guarded evidence."""

from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROJECT_STATUS = ROOT / "docs" / "project-status.md"
MANUFACTURING = ROOT / "docs" / "replica-manufacturing-readiness.md"
BASIC_MISSING = ROOT / "docs" / "basic-cartridge-missing-page-constraints.md"
BRINGUP = ROOT / "docs" / "replica-bringup-verification-points.md"


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def require(condition: bool, message: str, failures: list[str]) -> None:
    if not condition:
        failures.append(message)


def extract_zip_sha(text: str) -> str:
    match = re.search(r"Final upload ZIP SHA256: `([0-9a-f]{64})`", text)
    if not match:
        raise SystemExit("Could not find final upload ZIP SHA in manufacturing report")
    return match.group(1)


def extract_int(text: str, label: str) -> int:
    match = re.search(rf"- {re.escape(label)}: `([0-9,]+)`", text)
    if not match:
        raise SystemExit(f"Could not find {label} in bring-up report")
    return int(match.group(1).replace(",", ""))


def main() -> int:
    project = read(PROJECT_STATUS)
    manufacturing = read(MANUFACTURING)
    basic_missing = read(BASIC_MISSING)
    bringup = read(BRINGUP)
    failures: list[str] = []

    upload_sha = extract_zip_sha(manufacturing)
    risk_nets = extract_int(bringup, "Verification-point nets")
    risk_endpoints = extract_int(bringup, "Verification-point endpoints checked in PCB")
    board_endpoints = extract_int(bringup, "All board endpoints checked in source PCB")
    require(
        upload_sha in project,
        f"project status does not mention current upload ZIP SHA {upload_sha}",
        failures,
    )
    require(
        "READY TO UPLOAD" in project and "ORDER READY" in project,
        "project status does not mirror manufacturing/order readiness states",
        failures,
    )
    require(
        f"{risk_nets} source-risk verification points" in project
        and f"{risk_endpoints} listed source-risk endpoints" in project
        and f"{board_endpoints:,} modeled board endpoints" in project
        and "X2/P5V" in project,
        "project status does not mirror bring-up endpoint coverage and X2/P5V closure",
        failures,
    )

    require(
        "docs/basic-cartridge-missing-page-constraints.md" in project,
        "project status does not mention BASIC missing-page report path",
        failures,
    )
    for marker in ("0x2100..0x21FF", "0x2000..0x20FF", "0x2000..0x2018", "JNZ 0x2009"):
        require(
            marker in project,
            f"project status does not mention BASIC missing-page marker {marker}",
            failures,
        )
        require(
            marker in basic_missing,
            f"BASIC missing-page report no longer contains expected marker {marker}",
            failures,
        )

    if failures:
        print("Project status freshness check failed:")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("Project status mirrors current manufacturing and BASIC boundary evidence.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
