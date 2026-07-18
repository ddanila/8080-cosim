#!/usr/bin/python3
"""Transactionally remove migrated copper that violates the current PCB.

The input is expected to be a source-based candidate emitted by
``refresh_routed_from_source.py --allow-drc-salvage``.  Tracks and vias whose
UUIDs are absent from the authoritative source PCB are treated as migrated.
KiCad DRC owns every removal decision: each round removes only migrated items
named by a configured copper blocker, then reruns DRC until no blocker remains.
Source-owned copper is never removed. Migrated dangling tails are deliberately
retained for the subsequent reconnection pass; pruning them before zero opens
would recursively erase otherwise useful routed chains.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

import pcbnew


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "kicad" / "juku.kicad_pcb"
REMOVE_HELPER = ROOT / "kicad" / "remove_board_items.py"
BLOCKERS = {
    "shorting_items",
    "clearance",
    "tracks_crossing",
    "hole_clearance",
    "hole_to_hole",
    "copper_edge_clearance",
}
DANGLING = {"track_dangling", "via_dangling"}


def uuid(item: pcbnew.BOARD_ITEM) -> str:
    return item.m_Uuid.AsString()


def run_drc(cli: Path, board: Path, report: Path) -> dict:
    report.unlink(missing_ok=True)
    proc = subprocess.run(
        [
            str(cli),
            "pcb",
            "drc",
            "--format",
            "json",
            "--output",
            str(report),
            str(board),
        ],
        text=True,
        capture_output=True,
    )
    if not report.exists():
        raise RuntimeError(f"KiCad DRC produced no report: {proc.stdout}{proc.stderr}")
    return json.loads(report.read_text())


def violation_counts(report: dict) -> dict[str, int]:
    counts: dict[str, int] = {}
    for violation in report.get("violations", []):
        kind = str(violation.get("type", "unknown"))
        counts[kind] = counts.get(kind, 0) + 1
    return counts


def implicated_migrated_uuids(
    report: dict, migrated: set[str], kinds: set[str]
) -> set[str]:
    result: set[str] = set()
    for violation in report.get("violations", []):
        if violation.get("type") not in kinds:
            continue
        for item in violation.get("items", []):
            item_uuid = str(item.get("uuid", ""))
            if item_uuid in migrated:
                result.add(item_uuid)
    return result


def remaining_counts(report: dict, kinds: set[str]) -> dict[str, int]:
    counts = violation_counts(report)
    return {kind: counts.get(kind, 0) for kind in sorted(kinds) if counts.get(kind)}


def remove_items(
    input_board: Path, output_board: Path, uuid_path: Path, requested: set[str]
) -> int:
    uuid_path.write_text(json.dumps(sorted(requested)) + "\n")
    subprocess.run(
        [
            sys.executable,
            str(REMOVE_HELPER),
            str(input_board),
            str(output_board),
            str(uuid_path),
        ],
        check=True,
        text=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return len(requested)


def unconnected_count(board: pcbnew.BOARD) -> int:
    board.BuildConnectivity()
    return board.GetConnectivity().GetUnconnectedCount(False)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--source", type=Path, default=SOURCE)
    parser.add_argument("--kicad-cli", type=Path)
    parser.add_argument(
        "--max-rounds",
        type=int,
        default=50,
        help="maximum DRC/removal rounds for geometric blockers",
    )
    parser.add_argument(
        "--summary",
        type=Path,
        help="write a machine-readable result summary",
    )
    args = parser.parse_args()

    if args.input.resolve() == args.output.resolve():
        raise SystemExit("input and output must differ")
    if args.max_rounds <= 0:
        raise SystemExit("--max-rounds must be positive")
    cli = args.kicad_cli
    if cli is None:
        cli = Path(
            subprocess.check_output(
                [str(ROOT / "scripts" / "find-kicad-cli.sh")], text=True
            ).strip()
        )

    source = pcbnew.LoadBoard(str(args.source))
    source_uuids = {uuid(item) for item in source.GetTracks()}
    shutil.copyfile(args.input, args.output)
    board = pcbnew.LoadBoard(str(args.output))
    initial_tracks = sum(1 for _ in board.GetTracks())
    migrated = {uuid(item) for item in board.GetTracks()} - source_uuids
    if not migrated:
        raise SystemExit("input contains no migrated track/via UUIDs")
    initial_opens = unconnected_count(board)
    del board
    total_removed = 0
    blocker_rounds = 0

    with tempfile.TemporaryDirectory(prefix="juku-copper-salvage-") as tmp_name:
        tmp = Path(tmp_name)
        report_path = tmp / "drc.json"
        report = run_drc(cli, args.output, report_path)

        while remaining_counts(report, BLOCKERS):
            if blocker_rounds >= args.max_rounds:
                raise SystemExit(
                    f"blocker cleanup exceeded {args.max_rounds} rounds: "
                    f"{remaining_counts(report, BLOCKERS)}"
                )
            implicated = implicated_migrated_uuids(report, migrated, BLOCKERS)
            if not implicated:
                raise SystemExit(
                    "current DRC blockers contain no removable migrated item: "
                    f"{remaining_counts(report, BLOCKERS)}"
                )
            candidate_path = tmp / "candidate.kicad_pcb"
            removed = remove_items(
                args.output, candidate_path, tmp / "remove.json", implicated
            )
            os.replace(candidate_path, args.output)
            migrated -= implicated
            total_removed += removed
            blocker_rounds += 1
            report = run_drc(cli, args.output, report_path)
            print(
                f"blocker round {blocker_rounds}: removed {removed}, "
                f"remaining {remaining_counts(report, BLOCKERS)}",
                flush=True,
            )

    board = pcbnew.LoadBoard(str(args.output))
    final_tracks = sum(1 for _ in board.GetTracks())
    final_opens = unconnected_count(board)
    final_counts = violation_counts(report)
    summary = {
        "schema_version": 1,
        "source": str(args.source),
        "input": str(args.input),
        "output": str(args.output),
        "initial_tracks": initial_tracks,
        "final_tracks": final_tracks,
        "initial_unconnected": initial_opens,
        "final_unconnected": final_opens,
        "migrated_items_removed": total_removed,
        "migrated_items_retained": len(migrated),
        "blocker_rounds": blocker_rounds,
        "electrical_blockers": remaining_counts(report, BLOCKERS),
        "dangling_findings": remaining_counts(report, DANGLING),
        "violation_counts": dict(sorted(final_counts.items())),
    }
    if args.summary:
        args.summary.parent.mkdir(parents=True, exist_ok=True)
        args.summary.write_text(json.dumps(summary, indent=2) + "\n")
        print(f"wrote {args.summary}")
    print(
        "ROUTED COPPER SALVAGE: PASS; "
        f"tracks={initial_tracks}->{final_tracks}, "
        f"opens={initial_opens}->{final_opens}, removed={total_removed}, "
        f"blockers={summary['electrical_blockers']}, "
        f"dangling={summary['dangling_findings']}"
    )
    print(f"wrote {args.output}")


if __name__ == "__main__":
    main()
