#!/usr/bin/env python3
"""Transactionally prune KiCad tracks/vias that remain as disconnected tails."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
REMOVE_HELPER = ROOT / "kicad" / "remove_board_item.py"
BLOCKERS = {
    "shorting_items",
    "clearance",
    "tracks_crossing",
    "hole_clearance",
    "hole_to_hole",
    "copper_edge_clearance",
}


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


def counts(report: dict) -> dict[str, int]:
    result: dict[str, int] = {}
    for violation in report.get("violations", []):
        kind = violation.get("type", "unknown")
        result[kind] = result.get(kind, 0) + 1
    return result


def dangling_uuids(report: dict) -> list[str]:
    result = []
    for violation in report.get("violations", []):
        if violation.get("type") not in {"track_dangling", "via_dangling"}:
            continue
        items = violation.get("items", [])
        if len(items) != 1 or not items[0].get("uuid"):
            continue
        result.append(items[0]["uuid"])
    return result


def remove_track(
    python: Path, input_board: Path, output_board: Path, uuid: str
) -> None:
    subprocess.run(
        [str(python), str(REMOVE_HELPER), str(input_board), str(output_board), uuid],
        text=True,
        check=True,
    )


def acceptable(before: dict, after: dict) -> bool:
    if after.get("unconnected_items"):
        return False
    before_counts, after_counts = counts(before), counts(after)
    if any(after_counts.get(kind, 0) for kind in BLOCKERS):
        return False
    return all(
        after_counts.get(kind, 0) <= before_counts.get(kind, 0)
        for kind in before_counts.keys() | after_counts.keys()
        if kind not in {"track_dangling", "via_dangling"}
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--kicad-cli", type=Path)
    parser.add_argument("--python", type=Path, help="Python interpreter with pcbnew")
    args = parser.parse_args()

    if args.input.resolve() == args.output.resolve():
        raise SystemExit("input and output must differ")
    cli = args.kicad_cli
    if cli is None:
        cli = Path(
            subprocess.check_output(
                [str(ROOT / "scripts" / "find-kicad-cli.sh")], text=True
            ).strip()
        )
    router_python = args.python
    if router_python is None:
        router_python = Path(
            subprocess.check_output(
                [str(ROOT / "scripts" / "find-kicad-python.sh")], text=True
            ).strip()
        )
    shutil.copyfile(args.input, args.output)

    with tempfile.TemporaryDirectory(prefix="juku-prune-dangling-") as tmp_name:
        tmp = Path(tmp_name)
        current = run_drc(cli, args.output, tmp / "current.json")
        if current.get("unconnected_items"):
            raise SystemExit("refusing to prune before the board reaches zero opens")
        initial = len(dangling_uuids(current))
        accepted = 0
        while dangling_uuids(current):
            progress = False
            for uuid in dangling_uuids(current):
                candidate = tmp / "candidate.kicad_pcb"
                candidate_report_path = tmp / "candidate.json"
                remove_track(router_python, args.output, candidate, uuid)
                candidate_report = run_drc(cli, candidate, candidate_report_path)
                if not acceptable(current, candidate_report):
                    continue
                os.replace(candidate, args.output)
                current = candidate_report
                accepted += 1
                progress = True
                print(
                    f"accept prune {uuid}: dangling -> "
                    f"{len(dangling_uuids(current))}",
                    flush=True,
                )
                break
            if not progress:
                break

    final = len(dangling_uuids(current))
    print(f"accepted {accepted} prune(s): dangling {initial} -> {final}")
    print(f"wrote {args.output}")
    if final:
        raise SystemExit(f"{final} dangling track(s) could not be pruned safely")


if __name__ == "__main__":
    main()
