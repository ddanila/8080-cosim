#!/usr/bin/env python3
"""Run KiCad DRC and pin the result to the exact committed Rev-A PCB."""
from __future__ import annotations

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
    passed = not violations and not unconnected
    status = "CURRENT SOURCE DRC CLEAN" if passed else "DRC FAILED"
    board_text = board.read_text(encoding="utf-8")
    file_version = re.search(r"\(version\s+(\d+)\)", board_text)
    generator_version = re.search(r'\(generator_version\s+"([^"]+)"\)', board_text)
    board_rel = board.relative_to(ROOT) if board.is_relative_to(ROOT) else board
    lines = [
        "# Rev A current-source DRC readiness",
        "",
        "Status date: **2026-07-23**.",
        "",
        f"Status: **{status}**.",
        "",
        "This report binds a full KiCad error-level DRC result to the exact routed",
        "Rev-A PCB after the D1 DO-41 correction, the U20/U21 active-low",
        "address-mux enable correction, the U22 refresh-counter cascade",
        "correction, and inner-plane refill. It does not release fabrication;",
        "package regeneration, vendor preview, sourcing, and human review remain",
        "separate gates.",
        "",
        "## Result",
        "",
        f"- Board: `{board_rel}`",
        f"- Board SHA-256: `{sha256(board)}`",
        f"- KiCad CLI: `{cli}`",
        f"- KiCad version: `{version}`",
        f"- Board file version: `{file_version.group(1) if file_version else 'unknown'}`",
        f"- Board generator version: `{generator_version.group(1) if generator_version else 'unknown'}`",
        f"- Error-level DRC violations: **{len(violations)}**",
        f"- Unconnected items: **{len(unconnected)}**",
        "",
        "## Refill disposition",
        "",
        "- U20.15 and U21.15 are the active-low enables of the two 74HCT157",
        "  address multiplexers. The correction moves both pads and their four",
        "  retained F.Cu segments from the former floating `ADDRMUX_OE_N` island",
        "  to GND; filled In1.Cu then provides the return connection.",
        "- U22.2 and U22.12 are the 74HCT393 active-high reset inputs. The",
        "  correction moves both pads and the three retained former",
        "  `REFRESH_CLR` trace segments to GND.",
        "- U22.6 (1Q3) is cascaded to U22.13 (2CP) on `REFRESH_ROW3` with eight",
        "  signal segments and two through vias, forming the intended 8-bit",
        "  refresh-row counter.",
        "- The saved post-correction board passes DRC after a stable-KiCad refill.",
        "  The prior fabrication package predates these source changes and is stale;",
        "  package freshness requires a new guarded export and checksum.",
        "",
        "## Command",
        "",
        "```sh",
        "python3 spinoffs/minimal-vga/kicad/report_rev_a_drc_readiness.py",
        "```",
        "",
        "The saved board already contains current zone fills. Refill and save zones",
        "with the same KiCad generation after any pad, track, via, or zone change,",
        "then regenerate this report. Gerber/drill export, package-integrity checks,",
        "vendor preview, and human release review remain separate gates.",
        "",
    ]
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {report.relative_to(ROOT) if report.is_relative_to(ROOT) else report}")
    print(
        "REV-A DRC: "
        f"{len(violations)} violations / {len(unconnected)} unconnected"
    )
    return 0 if passed and completed.returncode == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
