#!/usr/bin/python3
"""Verify source endpoint parity and electrical DRC for the routed candidate."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import tempfile

import pcbnew


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "kicad" / "juku.kicad_pcb"
CANDIDATE = ROOT / "kicad" / "juku_routed_candidate.kicad_pcb"
BLOCKERS = {
    "shorting_items",
    "clearance",
    "tracks_crossing",
    "hole_clearance",
    "hole_to_hole",
    "track_dangling",
    "via_dangling",
    "copper_edge_clearance",
}


def pads(board: pcbnew.BOARD) -> dict[tuple[str, str], tuple[str, float, float]]:
    return {
        (footprint.GetReference(), pad.GetNumber()):
        (
            pad.GetNetname(),
            pcbnew.ToMM(pad.GetPosition().x),
            pcbnew.ToMM(pad.GetPosition().y),
        )
        for footprint in board.GetFootprints()
        for pad in footprint.Pads()
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=SOURCE)
    parser.add_argument("--candidate", type=Path, default=CANDIDATE)
    parser.add_argument("--kicad-cli", type=Path)
    args = parser.parse_args()

    cli = args.kicad_cli
    if cli is None:
        cli = Path(
            subprocess.check_output(
                [str(ROOT / "scripts" / "find-kicad-cli.sh")], text=True
            ).strip()
        )
    source = pcbnew.LoadBoard(str(args.source))
    candidate = pcbnew.LoadBoard(str(args.candidate))
    source_pads, candidate_pads = pads(source), pads(candidate)
    if source_pads.keys() != candidate_pads.keys():
        missing = sorted(source_pads.keys() - candidate_pads.keys())
        extra = sorted(candidate_pads.keys() - source_pads.keys())
        raise SystemExit(f"pad identity mismatch: missing={missing} extra={extra}")
    net_mismatches = {
        key: (source_pads[key][0], candidate_pads[key][0])
        for key in source_pads
        if source_pads[key][0] != candidate_pads[key][0]
    }
    if net_mismatches:
        raise SystemExit(f"pad-net mismatches: {net_mismatches}")
    max_delta = max(
        max(
            abs(source_pads[key][1] - candidate_pads[key][1]),
            abs(source_pads[key][2] - candidate_pads[key][2]),
        )
        for key in source_pads
    )
    if max_delta > 0.00005:
        raise SystemExit(f"pad coordinate delta {max_delta:.9f} mm exceeds 50 nm")

    with tempfile.TemporaryDirectory(prefix="juku-routed-candidate-check-") as tmp_name:
        report_path = Path(tmp_name) / "drc.json"
        proc = subprocess.run(
            [
                str(cli),
                "pcb",
                "drc",
                "--format",
                "json",
                "--output",
                str(report_path),
                str(args.candidate),
            ],
            text=True,
            capture_output=True,
        )
        if not report_path.exists():
            raise SystemExit(f"KiCad DRC produced no report: {proc.stdout}{proc.stderr}")
        report = json.loads(report_path.read_text())

    if report.get("unconnected_items"):
        raise SystemExit(
            f"candidate has {len(report['unconnected_items'])} unconnected item(s)"
        )
    counts: dict[str, int] = {}
    for violation in report.get("violations", []):
        kind = violation.get("type", "unknown")
        counts[kind] = counts.get(kind, 0) + 1
    failures = {kind: counts.get(kind, 0) for kind in BLOCKERS if counts.get(kind)}
    if failures:
        raise SystemExit(f"candidate electrical DRC failures: {failures}")

    print(
        "ROUTED CANDIDATE: PASS; "
        f"footprints={len(candidate.GetFootprints())}, pads={len(candidate_pads)}, "
        f"copper={sum(1 for _ in candidate.GetTracks())}, opens=0, "
        f"electrical=0, max-pad-delta-mm={max_delta:.9f}"
    )


if __name__ == "__main__":
    main()
