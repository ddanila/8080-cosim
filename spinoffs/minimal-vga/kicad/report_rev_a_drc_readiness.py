#!/usr/bin/env python3
"""Run KiCad DRC and pin the result to the exact committed Rev-A PCB."""
from __future__ import annotations

from datetime import datetime, timezone

import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
BOARD = ROOT / "spinoffs" / "minimal-vga" / "kicad" / "rev-a-physical.kicad_pcb"
REPORT = ROOT / "spinoffs" / "minimal-vga" / "docs" / "rev-a-drc-readiness.md"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def find_cli() -> str:
    configured = os.environ.get("KICAD_CLI")
    if configured:
        return configured
    result = subprocess.run(
        [str(ROOT / "scripts" / "find-kicad-cli.sh")],
        cwd=ROOT,
        check=True,
        text=True,
        stdout=subprocess.PIPE,
    )
    return result.stdout.strip()


def main() -> int:
    board = Path(sys.argv[1]) if len(sys.argv) > 1 else BOARD
    report = Path(sys.argv[2]) if len(sys.argv) > 2 else REPORT
    cli = find_cli()
    version = subprocess.run(
        [cli, "--version"],
        check=True,
        text=True,
        stdout=subprocess.PIPE,
    ).stdout.strip()
    major = re.match(r"(\d+)", version)
    if not major or int(major.group(1)) < 10:
        raise SystemExit(f"Rev-A source requires KiCad 10 or newer; found {version}")

    with tempfile.TemporaryDirectory(prefix="rev-a-drc-") as temp:
        json_path = Path(temp) / "drc.json"
        completed = subprocess.run(
            [
                cli,
                "pcb",
                "drc",
                "--severity-error",
                "--format",
                "json",
                "--output",
                str(json_path),
                str(board),
            ],
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=False,
        )
        if not json_path.exists():
            raise SystemExit(completed.stdout or "KiCad did not produce a DRC report")
        result = json.loads(json_path.read_text(encoding="utf-8"))

    violations = result.get("violations", [])
    unconnected = result.get("unconnected_items", [])
    passed = completed.returncode == 0 and not violations and not unconnected
    status = "CURRENT SOURCE DRC CLEAN" if passed else "DRC FAILED"
    board_text = board.read_text(encoding="utf-8")
    file_version = re.search(r"\(version\s+(\d+)\)", board_text)
    generator_version = re.search(r'\(generator_version\s+"([^"]+)"\)', board_text)
    board_rel = board.relative_to(ROOT) if board.is_relative_to(ROOT) else board
    lines = [
        "# Rev A current-source DRC readiness",
        "",
        f"Checked (UTC): **{datetime.now(timezone.utc).date().isoformat()}**.",
        "",
        f"Status: **{status}**.",
        "",
        "This report binds KiCad's error-level DRC result to the exact PCB hash below.",
        "It does not include warning-level violations, refill zones or qualify fabrication.",
        "See [manufacturing readiness](rev-a-manufacturing-readiness.md) for release gates.",
        "",
        "## Result",
        "",
        f"- Board: `{board_rel}`",
        f"- Board SHA-256: `{sha256(board)}`",
        f"- KiCad CLI: `{cli}`",
        f"- KiCad version: `{version}`",
        f"- DRC command exit code: `{completed.returncode}`",
        f"- Board file version: `{file_version.group(1) if file_version else 'unknown'}`",
        f"- Board generator version: `{generator_version.group(1) if generator_version else 'unknown'}`",
        f"- Error-level DRC violations: **{len(violations)}**",
        f"- Unconnected items: **{len(unconnected)}**",
        "",
        "## Command",
        "",
        "```sh",
        "python3 spinoffs/minimal-vga/kicad/report_rev_a_drc_readiness.py",
        "```",
        "",
        "Run from the repository root with KiCad 10 or newer; `KICAD_CLI` overrides",
        "the repository locator. Optional positional arguments select the PCB and output",
        "report paths. The command overwrites this report by default, including on DRC failure.",
        "",
        "Refill and save zones with a compatible KiCad version after pad, track, via or",
        "zone changes before running this check. A clean result requires command success,",
        "zero error-level violations and zero unconnected items. Package freshness, vendor",
        "preview and human release review remain separate gates.",
        "",
    ]
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {report.relative_to(ROOT) if report.is_relative_to(ROOT) else report}")
    print(
        "REV-A DRC: "
        f"{len(violations)} violations / {len(unconnected)} unconnected"
    )
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
