#!/usr/bin/env python3
"""Build a portable, deterministic review snapshot; never a fabrication ZIP."""

from __future__ import annotations

import argparse
import hashlib
import json
import zipfile
from pathlib import Path

import report_replica_release_evidence as packet


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "fab/evidence/juku-replica-release-evidence.zip"
SUMS_MEMBER = "EVIDENCE-SHA256SUMS.txt"
README_MEMBER = "EVIDENCE-README.txt"


def members(manifest: dict) -> list[str]:
    paths = set(packet.SOURCES)
    paths.update(entry["path"] for entry in manifest["reports"].values()
                 if entry["sha256"])
    paths.update({
        "docs/replica-release-evidence-manifest.json",
        "docs/replica-release-evidence-package.md",
        "docs/replica-dual-config-bom.csv",
        "docs/main-board-unresolved-endpoints.csv",
        "ref/eprom-images/SHA256SUMS",
        "ref/physical-proms/SHA256SUMS",
        "scripts/report_replica_release_evidence.py",
        "scripts/build_replica_release_evidence_bundle.py",
        manifest["eprom_source_rom"]["path"],
    })
    for item in manifest["programming_evidence"].values():
        paths.update(item[key] for key in ("raw_path", "asserted_path", "dump_manifest", "path")
                     if key in item)
    return sorted(paths)


def zip_info(name: str) -> zipfile.ZipInfo:
    info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
    info.compress_type = zipfile.ZIP_DEFLATED
    info.external_attr = 0o100644 << 16
    return info


def checked_packet() -> dict:
    expected_json, expected_md = packet.build()
    if (packet.JSON_OUT.read_text() != expected_json or
            packet.MD_OUT.read_text() != expected_md):
        raise SystemExit("release evidence packet is stale; regenerate it before bundling")
    return json.loads(expected_json)


def build(output: Path, manifest: dict) -> None:
    files = members(manifest)
    sums = []
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED,
                         compresslevel=9, strict_timestamps=True) as archive:
        for relative in files:
            data = (ROOT / relative).read_bytes()
            archive.writestr(zip_info(relative), data)
            sums.append(f"{hashlib.sha256(data).hexdigest()}  {relative}")
        readme = ("Juku replica release evidence snapshot\n"
                  f"Decision: {manifest['decision']}\n"
                  "This archive is for review. It is not the Gerber/drill upload ZIP.\n"
                  "Read docs/replica-release-evidence-package.md first.\n").encode()
        archive.writestr(zip_info(README_MEMBER), readme)
        sums.append(f"{hashlib.sha256(readme).hexdigest()}  {README_MEMBER}")
        archive.writestr(zip_info(SUMS_MEMBER), ("\n".join(sums) + "\n").encode())


def verify(output: Path, manifest: dict) -> None:
    if not output.is_file():
        raise SystemExit(f"evidence bundle missing: {output}")
    expected = set(members(manifest)) | {README_MEMBER, SUMS_MEMBER}
    with zipfile.ZipFile(output) as archive:
        names = archive.namelist()
        if len(names) != len(expected) or set(names) != expected:
            raise SystemExit("evidence bundle member inventory differs from current packet")
        sums = archive.read(SUMS_MEMBER).decode().splitlines()
        recorded = {}
        for line in sums:
            digest, sep, path = line.partition("  ")
            if not sep or path in recorded:
                raise SystemExit("malformed or duplicate evidence checksum entry")
            recorded[path] = digest
        if set(recorded) != expected - {SUMS_MEMBER}:
            raise SystemExit("evidence checksum inventory differs from archive")
        for path, digest in recorded.items():
            data = archive.read(path)
            if hashlib.sha256(data).hexdigest() != digest:
                raise SystemExit(f"evidence bundle checksum mismatch: {path}")
            if path != README_MEMBER and data != (ROOT / path).read_bytes():
                raise SystemExit(f"evidence bundle differs from current source: {path}")
    print(f"evidence bundle: {output} ({hashlib.sha256(output.read_bytes()).hexdigest()})")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    manifest = checked_packet()
    if not args.check:
        build(args.output, manifest)
    verify(args.output, manifest)


if __name__ == "__main__":
    main()
