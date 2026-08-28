#!/usr/bin/env python3
"""Validate the five rev B fabrication archives and record their exact identity.

The gate checks each frozen two/four-layer production file set, archive paths/content,
Gerber X2 metadata, Excellon tools/hits, job-file dimensions/layer count, and records
source/package/member hashes plus source/tool identity. The same manifest is stored in
the untracked package directory and tracked docs for independent release review.
"""
import hashlib
import json
import os
import re
import subprocess
import sys
import zipfile
from pathlib import Path, PurePosixPath


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
PKG = REPO / "fab" / "minimal-vga" / "revb" / "package"
FAB = PKG.parent
PROFILE_PATH = HERE / "jlcpcb-profile.json"
PROFILE = json.loads(PROFILE_PATH.read_text())
CARDS = PROFILE["boards"]
TRACKED_MANIFEST = REPO / "spinoffs" / "minimal-vga" / "docs" / "rev-b-five-board-package-manifest.json"


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def expected(card):
    suffixes = list(PROFILE["archive"]["two_layer_suffixes"])
    if CARDS[card]["copper_layers"] == 4:
        suffixes += PROFILE["archive"]["four_layer_additional_suffixes"]
    return {f"{card}-{s}" if s != "drl" else f"{card}.drl" for s in suffixes}


def fail(errors, card, message):
    errors.append(f"{card}: {message}")


def validate_card(card, spec, errors):
    board_dir = PKG / card
    archive = PKG / f"{card}.zip"
    wanted = expected(card)
    if not board_dir.is_dir():
        fail(errors, card, f"missing directory {board_dir}")
        return None
    disk_entries = {p.name for p in board_dir.iterdir()}
    disk_files = {p.name for p in board_dir.iterdir() if p.is_file()}
    if disk_entries != wanted or disk_files != wanted:
        fail(errors, card, f"production files differ: missing={sorted(wanted-disk_files)}, "
                           f"unexpected={sorted(disk_entries-wanted)}")
    for name in wanted & disk_files:
        if (board_dir / name).stat().st_size == 0:
            fail(errors, card, f"empty file {name}")

    if not archive.is_file():
        fail(errors, card, f"missing archive {archive}")
        return None
    try:
        with zipfile.ZipFile(archive) as zf:
            members = [n for n in zf.namelist() if not n.endswith("/")]
            expected_members = {f"{card}/{name}" for name in wanted}
            safe = all(not PurePosixPath(n).is_absolute() and ".." not in PurePosixPath(n).parts
                       for n in members)
            if not safe:
                fail(errors, card, "archive contains an unsafe path")
            if set(members) != expected_members or len(members) != len(wanted):
                fail(errors, card, f"archive paths differ: missing={sorted(expected_members-set(members))}, "
                                   f"unexpected={sorted(set(members)-expected_members)}")
            corrupt = zf.testzip()
            if corrupt:
                fail(errors, card, f"archive CRC failure in {corrupt}")
            for member in members:
                name = PurePosixPath(member).name
                if name in disk_files and zf.read(member) != (board_dir / name).read_bytes():
                    fail(errors, card, f"archive member differs from exported file: {name}")
    except zipfile.BadZipFile:
        fail(errors, card, "archive is not a valid ZIP")

    job_path = board_dir / f"{card}-job.gbrjob"
    if job_path.is_file():
        try:
            job = json.loads(job_path.read_text())
            specs = job["GeneralSpecs"]
            if specs.get("LayerNumber") != spec["copper_layers"]:
                fail(errors, card, f"job declares {specs.get('LayerNumber')} copper layers, "
                                   f"expected {spec['copper_layers']}")
            size = specs.get("Size", {})
            if (abs(float(size.get("X", 0)) - spec["width_mm"]) > 0.4 or
                    abs(float(size.get("Y", 0)) - spec["height_mm"]) > 0.4):
                fail(errors, card, f"job size {size.get('X')}x{size.get('Y')} != "
                                   f"{spec['width_mm']}x{spec['height_mm']} mm")
            job_files = {entry["Path"] for entry in job.get("FilesAttributes", [])}
            gerbers = wanted - {f"{card}.drl", f"{card}-job.gbrjob"}
            if job_files != gerbers:
                fail(errors, card, f"job Gerber set differs: missing={sorted(gerbers-job_files)}, "
                                   f"unexpected={sorted(job_files-gerbers)}")
        except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
            fail(errors, card, f"invalid Gerber job file: {exc}")

    for name in wanted:
        if name.endswith((".gtl", ".gbl", ".gts", ".gbs", ".gto", ".gbo", ".gm1")):
            path = board_dir / name
            if path.is_file():
                text = path.read_text(errors="replace")
                if "%TF.GenerationSoftware,KiCad" not in text or "%TF.FileFunction," not in text:
                    fail(errors, card, f"{name} lacks Gerber X2 generation/function metadata")
                if "M02*" not in text:
                    fail(errors, card, f"{name} lacks Gerber end marker")

    drill = board_dir / f"{card}.drl"
    if drill.is_file():
        text = drill.read_text(errors="replace")
        if not text.startswith("M48") or "METRIC" not in text or "M30" not in text:
            fail(errors, card, "drill file lacks expected Excellon header/units/end marker")
        if not re.search(r"^T\d+C\d", text, re.MULTILINE) or not re.search(
                r"^X-?\d+(?:\.\d+)?Y-?\d+(?:\.\d+)?", text, re.MULTILINE):
            fail(errors, card, "drill file has no tool definition or drill hit")

    pcb = FAB / f"{card}.kicad_pcb"
    if not pcb.is_file():
        fail(errors, card, f"missing source PCB {pcb}")
        return None
    members = {}
    for name in sorted(wanted & disk_files):
        data = (board_dir / name).read_bytes()
        members[name] = {"bytes": len(data), "sha256": sha256(data)}
    return {
        "board_mm": [spec["width_mm"], spec["height_mm"]],
        "copper_layers": spec["copper_layers"],
        "source_pcb_sha256": sha256(pcb.read_bytes()),
        "archive_bytes": archive.stat().st_size,
        "archive_sha256": sha256(archive.read_bytes()),
        "members": members,
    }


def command_output(command):
    try:
        return subprocess.check_output(command, cwd=REPO, text=True,
                                       stderr=subprocess.DEVNULL).strip()
    except (OSError, subprocess.CalledProcessError):
        return "unavailable"


def tool_identity():
    kicad_cli = os.environ.get("KICAD_CLI", "kicad-cli")
    kicad_python = os.environ.get("KICAD_PYTHON", "python3")
    pcbnew_version = command_output(
        [kicad_python, "-c", "import pcbnew; print(pcbnew.Version())"])
    zip_lines = command_output(["zip", "-v"]).splitlines()
    zip_version = next((line.strip() for line in zip_lines if "This is Zip" in line),
                       zip_lines[0] if zip_lines else "unavailable")
    return {
        "git": command_output(["git", "--version"]),
        "kicad_cli": command_output([kicad_cli, "--version"]),
        "pcbnew": pcbnew_version,
        "python": command_output([kicad_python, "--version"]),
        "zip": zip_version,
    }


def main():
    errors = []
    cards = {card: validate_card(card, spec, errors) for card, spec in CARDS.items()}
    if errors:
        print("rev B fabrication package FAILED:")
        for error in errors:
            print(f"- {error}")
        return 1
    manifest = {
        "schema": 2,
        "status": "R5.J2 five-board bare-PCB release candidate; ORDER HOLD",
        "source_revision": command_output(["git", "rev-parse", "HEAD"]),
        "jlcpcb_profile_sha256": sha256(PROFILE_PATH.read_bytes()),
        "order_options": PROFILE["order_options"],
        "tool_versions": tool_identity(),
        "cards": cards,
    }
    rendered = json.dumps(manifest, indent=2, sort_keys=True) + "\n"
    (PKG / "manifest.json").write_text(rendered)
    TRACKED_MANIFEST.write_text(rendered)
    sums = "".join(f"{cards[c]['archive_sha256']}  {c}.zip\n" for c in CARDS)
    (PKG / "SHA256SUMS").write_text(sums)
    print("rev B fabrication package PASS: 5 archives (four 2-layer, one 4-layer)")
    for card, data in cards.items():
        print(f"  {card}.zip  {data['archive_sha256']}  ({data['archive_bytes']} bytes)")
    print("  wrote package/manifest.json, package/SHA256SUMS and tracked release manifest")
    return 0


if __name__ == "__main__":
    sys.exit(main())
