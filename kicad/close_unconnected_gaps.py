#!/usr/bin/env python3
"""Close short KiCad DRC gaps with the guarded deterministic A* router.

Each proposed route is made on a temporary board and accepted only when a new
KiCad DRC report has fewer unconnected items, no short/clearance/crossing
violations, and no increase in dangling-track or copper-edge findings.
"""

from __future__ import annotations

import argparse
import json
import math
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile


ROOT = Path(__file__).resolve().parents[1]
ROUTER = ROOT / "kicad" / "repair_fdc_route_gaps.py"
BLOCKERS = {"shorting_items", "clearance", "tracks_crossing"}
BOUNDED = {"track_dangling", "copper_edge_clearance"}
NET_RE = re.compile(r"\[([^]]+)\]")


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
        kind = violation.get("type", "unknown")
        counts[kind] = counts.get(kind, 0) + 1
    return counts


def gaps(
    report: dict, minimum: float, maximum: float
) -> list[tuple[float, str, float, float, float, float]]:
    result = []
    for violation in report.get("unconnected_items", []):
        items = violation.get("items", [])
        if len(items) != 2 or "pos" not in items[0] or "pos" not in items[1]:
            continue
        match = NET_RE.search(items[0].get("description", ""))
        if not match:
            continue
        a, b = items[0]["pos"], items[1]["pos"]
        distance = math.hypot(a["x"] - b["x"], a["y"] - b["y"])
        if minimum <= distance <= maximum:
            result.append((distance, match.group(1), a["x"], a["y"], b["x"], b["y"]))
    return sorted(result)


def acceptable(before: dict, after: dict) -> bool:
    if len(after.get("unconnected_items", [])) >= len(
        before.get("unconnected_items", [])
    ):
        return False
    before_counts, after_counts = violation_counts(before), violation_counts(after)
    if any(after_counts.get(kind, 0) for kind in BLOCKERS):
        return False
    return all(
        after_counts.get(kind, 0) <= before_counts.get(kind, 0) for kind in BOUNDED
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--min-distance", type=float, default=0.0)
    parser.add_argument("--max-distance", type=float, default=30.0)
    parser.add_argument(
        "--timeout",
        type=float,
        default=30.0,
        help="seconds allowed for one A* proposal",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=0,
        help="maximum accepted routes; zero means no limit",
    )
    parser.add_argument("--kicad-cli", type=Path)
    args = parser.parse_args()

    cli = args.kicad_cli
    if cli is None:
        cli = Path(
            subprocess.check_output(
                [str(ROOT / "scripts" / "find-kicad-cli.sh")], text=True
            ).strip()
        )
    router_python = Path(
        subprocess.check_output(
            [str(ROOT / "scripts" / "find-kicad-python.sh")], text=True
        ).strip()
    )
    if args.input.resolve() == args.output.resolve():
        raise SystemExit("input and output must differ")
    if args.min_distance < 0 or args.max_distance < args.min_distance:
        raise SystemExit("distance range must satisfy 0 <= minimum <= maximum")
    shutil.copyfile(args.input, args.output)

    accepted = 0
    attempted: set[tuple[str, float, float, float, float]] = set()
    with tempfile.TemporaryDirectory(prefix="juku-gap-close-") as tmp_name:
        tmp = Path(tmp_name)
        current_report = run_drc(cli, args.output, tmp / "current.json")
        initial = len(current_report.get("unconnected_items", []))
        while not args.limit or accepted < args.limit:
            candidates = gaps(current_report, args.min_distance, args.max_distance)
            proposal = next(
                (item for item in candidates if item[1:] not in attempted), None
            )
            if proposal is None:
                break
            distance, net, x1, y1, x2, y2 = proposal
            signature = proposal[1:]
            attempted.add(signature)
            candidate_board = tmp / "candidate.kicad_pcb"
            candidate_report_path = tmp / "candidate.json"
            command = [
                str(router_python),
                str(ROUTER),
                str(args.output),
                str(candidate_board),
                "gap",
                net,
                f"{x1},{y1}",
                f"{x2},{y2}",
                "FB",
            ]
            try:
                proc = subprocess.run(
                    command, text=True, capture_output=True, timeout=args.timeout
                )
            except subprocess.TimeoutExpired:
                print(f"skip {net} {distance:.3f} mm: A* timeout", flush=True)
                continue
            if proc.returncode or not candidate_board.exists():
                reason = (proc.stderr or proc.stdout).strip().splitlines()
                print(
                    f"skip {net} {distance:.3f} mm: {reason[-1] if reason else 'no route'}",
                    flush=True,
                )
                continue
            candidate_report = run_drc(cli, candidate_board, candidate_report_path)
            if not acceptable(current_report, candidate_report):
                print(
                    f"reject {net} {distance:.3f} mm: DRC did not strictly improve",
                    flush=True,
                )
                continue
            before = len(current_report["unconnected_items"])
            after = len(candidate_report["unconnected_items"])
            os.replace(candidate_board, args.output)
            current_report = candidate_report
            accepted += 1
            print(
                f"accept {net} {distance:.3f} mm: unconnected {before} -> {after}",
                flush=True,
            )

    final = len(current_report.get("unconnected_items", []))
    print(f"accepted {accepted} route(s): unconnected {initial} -> {final}")
    print(f"wrote {args.output}")


if __name__ == "__main__":
    main()
