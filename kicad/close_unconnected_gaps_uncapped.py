#!/usr/bin/env python3
"""Close PCB gaps only when KiCad's uncapped connectivity count improves."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import shutil
import subprocess
import tempfile

import pcbnew

from close_unconnected_gaps import (
    ROOT,
    ROUTER,
    acceptable,
    board_item_points,
    gap_signature,
    gaps,
    rejection_reason,
    run_drc,
)

UNCONNECTED_HELPER = ROOT / "kicad/report_board_unconnected.py"


def uncapped_unconnected(python: Path, board: Path) -> int:
    return int(
        subprocess.check_output(
            [str(python), str(UNCONNECTED_HELPER), str(board)], text=True
        ).strip()
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--min-distance", type=float, default=0.0)
    parser.add_argument("--max-distance", type=float, default=30.0)
    parser.add_argument("--timeout", type=float, default=30.0)
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument(
        "--max-attempts",
        type=int,
        default=0,
        help="maximum proposals to try; zero means exhaust the candidate set",
    )
    parser.add_argument("--mode", choices=("FB", "M"), default="FB")
    parser.add_argument("--search-margin", type=float, default=30.0)
    parser.add_argument("--grid-step", type=float, default=0.5)
    parser.add_argument("--route-clearance", type=float, default=0.45)
    parser.add_argument("--kicad-cli", type=Path)
    parser.add_argument("--python", type=Path)
    parser.add_argument("--net")
    args = parser.parse_args()

    if args.input.resolve() == args.output.resolve():
        raise SystemExit("input and output must differ")
    if args.min_distance < 0 or args.max_distance < args.min_distance:
        raise SystemExit("distance range must satisfy 0 <= minimum <= maximum")
    if args.timeout <= 0 or args.limit < 0 or args.max_attempts < 0:
        raise SystemExit("timeout must be positive and limits non-negative")
    if args.search_margin <= 0 or args.grid_step <= 0 or args.route_clearance <= 0:
        raise SystemExit("search margin, grid step, and clearance must be positive")

    cli = args.kicad_cli or Path(
        subprocess.check_output(
            [str(ROOT / "scripts/find-kicad-cli.sh")], text=True
        ).strip()
    )
    router_python = args.python or Path(
        subprocess.check_output(
            [str(ROOT / "scripts/find-kicad-python.sh")], text=True
        ).strip()
    )
    shutil.copyfile(args.input, args.output)

    accepted_count = 0
    attempt_count = 0
    attempted: set[tuple] = set()
    with tempfile.TemporaryDirectory(prefix="juku-gap-close-uncapped-") as tmp_name:
        tmp = Path(tmp_name)
        current_report = run_drc(cli, args.output, tmp / "current.json")
        current_board = pcbnew.LoadBoard(str(args.output))
        current_points = board_item_points(current_board)
        current_uncapped = uncapped_unconnected(router_python, args.output)
        initial_uncapped = current_uncapped

        while not args.limit or accepted_count < args.limit:
            if args.max_attempts and attempt_count >= args.max_attempts:
                break
            proposals = gaps(
                current_report,
                args.min_distance,
                args.max_distance,
                args.net,
                current_points,
            )
            proposal = next(
                (item for item in proposals if gap_signature(item) not in attempted),
                None,
            )
            if proposal is None:
                break
            distance, net, x1, y1, x2, y2, start_layer, goal_layer = proposal
            attempted.add(gap_signature(proposal))
            attempt_count += 1
            candidate_board = tmp / "candidate.kicad_pcb"
            command = [
                str(router_python),
                str(ROUTER),
                str(args.output),
                str(candidate_board),
                "gap",
                net,
                f"{x1},{y1}",
                f"{x2},{y2}",
                args.mode,
            ]
            if args.mode == "M":
                command.extend(
                    (
                        str(args.search_margin),
                        str(args.grid_step),
                        str(args.route_clearance),
                        start_layer,
                        goal_layer,
                    )
                )
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
                    f"skip {net} {distance:.3f} mm: "
                    f"{reason[-1] if reason else 'no route'}",
                    flush=True,
                )
                continue

            candidate_report = run_drc(cli, candidate_board, tmp / "candidate.json")
            candidate_points = board_item_points(pcbnew.LoadBoard(str(candidate_board)))
            candidate_uncapped = uncapped_unconnected(router_python, candidate_board)
            if candidate_uncapped >= current_uncapped or not acceptable(
                current_report,
                candidate_report,
                proposal,
                True,
                current_points,
                candidate_points,
            ):
                detail = rejection_reason(current_report, candidate_report)
                print(
                    f"reject {net} {distance:.3f} mm: uncapped "
                    f"{current_uncapped} -> {candidate_uncapped}; {detail}",
                    flush=True,
                )
                continue

            os.replace(candidate_board, args.output)
            current_report = candidate_report
            current_points = candidate_points
            before = current_uncapped
            current_uncapped = candidate_uncapped
            accepted_count += 1
            # Accepted copper changes obstacle geometry, so retry prior failures.
            attempted.clear()
            print(
                f"accept {net} {distance:.3f} mm: uncapped "
                f"{before} -> {current_uncapped}",
                flush=True,
            )

    print(
        f"accepted {accepted_count} route(s) in {attempt_count} attempt(s): "
        f"uncapped {initial_uncapped} -> {current_uncapped}"
    )
    print(f"wrote {args.output}")


if __name__ == "__main__":
    main()
