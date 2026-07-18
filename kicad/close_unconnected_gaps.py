#!/usr/bin/env python3
"""Close short KiCad DRC gaps with the guarded deterministic A* router.

Each proposed route is made on a temporary board and accepted only when a new
KiCad DRC report has fewer unconnected items, no short/clearance/crossing
violations, and no increase in any other DRC finding.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile

import pcbnew

from drc_gap_geometry import board_item_points, resolved_item_pair


ROOT = Path(__file__).resolve().parents[1]
ROUTER = ROOT / "kicad" / "repair_fdc_route_gaps.py"
BLOCKERS = {"shorting_items", "clearance", "tracks_crossing"}
NET_RE = re.compile(r"\[([^]]+)\]")
LAYER_RE = re.compile(r" on ([FB])\.Cu(?:,|$)")
KICAD_UNCONNECTED_REPORT_CAP = 499


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_attempt_state(
    path: Path,
    board_sha256: str,
    config: dict[str, object],
    router_sha256: str,
    closer_sha256: str,
) -> dict[tuple[str, float, float, float, float, str, str], str]:
    if not path.exists():
        return {}
    state = json.loads(path.read_text())
    if state.get("schema_version") != 3:
        raise SystemExit(f"{path}: unsupported attempted-state schema")
    if state.get("board_sha256") != board_sha256:
        raise SystemExit(
            f"{path}: attempted state belongs to a different input board"
        )
    if (
        state.get("config") != config
        or state.get("router_sha256") != router_sha256
        or state.get("closer_sha256") != closer_sha256
    ):
        raise SystemExit(
            f"{path}: attempted state uses different router parameters or code"
        )
    attempts = {}
    for item in state.get("attempts", []):
        signature = tuple(item["signature"])
        if len(signature) != 7:
            raise SystemExit(f"{path}: malformed attempted-gap signature")
        attempts[signature] = str(item["outcome"])
    return attempts


def save_attempt_state(
    path: Path,
    board_sha256: str,
    config: dict[str, object],
    router_sha256: str,
    closer_sha256: str,
    attempts: dict[tuple[str, float, float, float, float, str, str], str],
) -> None:
    state = {
        "schema_version": 3,
        "board_sha256": board_sha256,
        "config": config,
        "router_sha256": router_sha256,
        "closer_sha256": closer_sha256,
        "attempts": [
            {"signature": list(signature), "outcome": attempts[signature]}
            for signature in sorted(attempts)
        ],
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp")
    temporary.write_text(json.dumps(state, indent=2) + "\n")
    os.replace(temporary, path)


def gap_signature(
    proposal: tuple[float, str, float, float, float, float, str, str],
) -> tuple[str, float, float, float, float, str, str]:
    _, net, x1, y1, x2, y2, layer1, layer2 = proposal
    endpoint1 = (x1, y1, layer1)
    endpoint2 = (x2, y2, layer2)
    if endpoint2 < endpoint1:
        endpoint1, endpoint2 = endpoint2, endpoint1
    return (
        net,
        endpoint1[0],
        endpoint1[1],
        endpoint2[0],
        endpoint2[1],
        endpoint1[2],
        endpoint2[2],
    )


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
    report: dict,
    minimum: float,
    maximum: float,
    net_filter: str | None = None,
    points_by_uuid: dict[str, tuple[tuple[float, float], ...]] | None = None,
) -> list[tuple[float, str, float, float, float, float, str, str]]:
    result = []
    for violation in report.get("unconnected_items", []):
        items = violation.get("items", [])
        if len(items) != 2 or "pos" not in items[0] or "pos" not in items[1]:
            continue
        match = NET_RE.search(items[0].get("description", ""))
        if not match:
            continue
        if net_filter is not None and match.group(1) != net_filter:
            continue
        layer_a = LAYER_RE.search(items[0].get("description", ""))
        layer_b = LAYER_RE.search(items[1].get("description", ""))
        a, b = resolved_item_pair(items[0], items[1], points_by_uuid)
        distance = math.dist(a, b)
        if minimum <= distance <= maximum:
            result.append(
                (
                    distance,
                    match.group(1),
                    a[0],
                    a[1],
                    b[0],
                    b[1],
                    layer_a.group(1) if layer_a else "A",
                    layer_b.group(1) if layer_b else "A",
                )
            )
    return sorted(result)


def same_endpoint_pair(
    left: tuple[float, float, float, float],
    right: tuple[float, float, float, float],
    tolerance: float = 0.000_001,
) -> bool:
    def point_equal(a: tuple[float, float], b: tuple[float, float]) -> bool:
        return abs(a[0] - b[0]) <= tolerance and abs(a[1] - b[1]) <= tolerance

    left_a, left_b = left[:2], left[2:]
    right_a, right_b = right[:2], right[2:]
    return (point_equal(left_a, right_a) and point_equal(left_b, right_b)) or (
        point_equal(left_a, right_b) and point_equal(left_b, right_a)
    )


def exact_gap_present(
    report: dict,
    proposal: tuple,
    points_by_uuid: dict[str, tuple[tuple[float, float], ...]],
) -> bool:
    _, net, x1, y1, x2, y2, _, _ = proposal
    endpoints = (x1, y1, x2, y2)
    return any(
        candidate[1] == net and same_endpoint_pair(endpoints, candidate[2:6])
        for candidate in gaps(report, 0.0, math.inf, net, points_by_uuid)
    )


def acceptable(
    before: dict,
    after: dict,
    proposal: tuple,
    accept_capped_progress: bool,
    before_points: dict[str, tuple[tuple[float, float], ...]],
    after_points: dict[str, tuple[tuple[float, float], ...]],
) -> bool:
    before_open = len(before.get("unconnected_items", []))
    after_open = len(after.get("unconnected_items", []))
    count_improved = after_open < before_open
    capped_gap_improved = (
        accept_capped_progress
        and before_open == KICAD_UNCONNECTED_REPORT_CAP
        and after_open == KICAD_UNCONNECTED_REPORT_CAP
        and exact_gap_present(before, proposal, before_points)
        and not exact_gap_present(after, proposal, after_points)
    )
    if not count_improved and not capped_gap_improved:
        return False
    before_counts, after_counts = violation_counts(before), violation_counts(after)
    if any(after_counts.get(kind, 0) for kind in BLOCKERS):
        return False
    return all(
        after_counts.get(kind, 0) <= before_counts.get(kind, 0)
        for kind in before_counts.keys() | after_counts.keys()
    )


def rejection_reason(before: dict, after: dict) -> str:
    reasons = []
    before_open = len(before.get("unconnected_items", []))
    after_open = len(after.get("unconnected_items", []))
    if after_open >= before_open:
        reasons.append(f"unconnected {before_open} -> {after_open}")
    before_counts, after_counts = violation_counts(before), violation_counts(after)
    for kind in sorted(before_counts.keys() | after_counts.keys()):
        delta = after_counts.get(kind, 0) - before_counts.get(kind, 0)
        if delta > 0:
            reasons.append(f"{kind} +{delta}")
    return ", ".join(reasons) or "acceptance invariant failed"


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
    parser.add_argument(
        "--mode",
        choices=("FB", "M"),
        default="FB",
        help="route on either single copper layer (FB), or permit vias (M)",
    )
    parser.add_argument(
        "--search-margin",
        type=float,
        default=30.0,
        help="multilayer search corridor beyond the endpoint bounds, in mm",
    )
    parser.add_argument(
        "--grid-step",
        type=float,
        default=0.5,
        help="multilayer A* grid spacing, in mm",
    )
    parser.add_argument(
        "--route-clearance",
        type=float,
        default=0.45,
        help="obstacle clearance used by the proposal router, in mm",
    )
    parser.add_argument("--kicad-cli", type=Path)
    parser.add_argument("--net", help="attempt only DRC gaps on this exact net")
    parser.add_argument(
        "--accept-capped-progress",
        action="store_true",
        help=(
            "while KiCad reports exactly 499 unconnected markers, accept a route "
            "whose exact proposed gap disappears without increasing any DRC count"
        ),
    )
    parser.add_argument(
        "--attempted-state",
        type=Path,
        help=(
            "persist attempted gap signatures between additive routing passes; "
            "the state is bound to the exact input/output lineage, router code, "
            "and proposal parameters"
        ),
    )
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
    if args.search_margin <= 0:
        raise SystemExit("search margin must be positive")
    if args.grid_step <= 0:
        raise SystemExit("grid step must be positive")
    if args.route_clearance <= 0:
        raise SystemExit("route clearance must be positive")
    board_sha256 = file_sha256(args.input)
    route_config = {
        "mode": args.mode,
        "search_margin": args.search_margin,
        "grid_step": args.grid_step,
        "route_clearance": args.route_clearance,
        "timeout": args.timeout,
    }
    router_sha256 = file_sha256(ROUTER)
    closer_sha256 = file_sha256(Path(__file__))
    attempt_outcomes = (
        load_attempt_state(
            args.attempted_state,
            board_sha256,
            route_config,
            router_sha256,
            closer_sha256,
        )
        if args.attempted_state
        else {}
    )
    shutil.copyfile(args.input, args.output)

    accepted = 0
    attempted = set(attempt_outcomes)

    def record_attempt(
        signature: tuple[str, float, float, float, float, str, str],
        outcome: str,
    ) -> None:
        nonlocal board_sha256
        attempt_outcomes[signature] = outcome
        if outcome == "accepted":
            # A new obstacle can force A* away from a formerly DRC-invalid
            # shortest path and thereby make the same endpoint pair legal.
            # It can also change timeout behavior.  A proven graph search with
            # no path remains monotonic as this additive workflow only adds
            # obstacles, so retain only router-failed history across accepts.
            stale = {
                attempted_signature
                for attempted_signature, attempted_outcome in attempt_outcomes.items()
                if attempted_outcome in {"drc-rejected", "timeout"}
            }
            for attempted_signature in stale:
                attempt_outcomes.pop(attempted_signature)
            attempted.difference_update(stale)
            board_sha256 = file_sha256(args.output)
        if args.attempted_state:
            save_attempt_state(
                args.attempted_state,
                board_sha256,
                route_config,
                router_sha256,
                closer_sha256,
                attempt_outcomes,
            )

    with tempfile.TemporaryDirectory(prefix="juku-gap-close-") as tmp_name:
        tmp = Path(tmp_name)
        current_report = run_drc(cli, args.output, tmp / "current.json")
        current_points = board_item_points(pcbnew.LoadBoard(str(args.output)))
        initial = len(current_report.get("unconnected_items", []))
        while not args.limit or accepted < args.limit:
            candidates = gaps(
                current_report,
                args.min_distance,
                args.max_distance,
                args.net,
                current_points,
            )
            proposal = next(
                (item for item in candidates if gap_signature(item) not in attempted),
                None,
            )
            if proposal is None:
                break
            distance, net, x1, y1, x2, y2, start_layer, goal_layer = proposal
            signature = gap_signature(proposal)
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
                record_attempt(signature, "timeout")
                continue
            if proc.returncode or not candidate_board.exists():
                reason = (proc.stderr or proc.stdout).strip().splitlines()
                print(
                    f"skip {net} {distance:.3f} mm: {reason[-1] if reason else 'no route'}",
                    flush=True,
                )
                record_attempt(signature, "router-failed")
                continue
            candidate_report = run_drc(cli, candidate_board, candidate_report_path)
            candidate_points = board_item_points(
                pcbnew.LoadBoard(str(candidate_board))
            )
            if not acceptable(
                current_report,
                candidate_report,
                proposal,
                args.accept_capped_progress,
                current_points,
                candidate_points,
            ):
                print(
                    f"reject {net} {distance:.3f} mm: "
                    f"{rejection_reason(current_report, candidate_report)}",
                    flush=True,
                )
                record_attempt(signature, "drc-rejected")
                continue
            before = len(current_report["unconnected_items"])
            after = len(candidate_report["unconnected_items"])
            os.replace(candidate_board, args.output)
            current_report = candidate_report
            current_points = candidate_points
            accepted += 1
            record_attempt(signature, "accepted")
            capped_note = (
                " (capped marker set advanced)"
                if before == after == KICAD_UNCONNECTED_REPORT_CAP
                else ""
            )
            print(
                f"accept {net} {distance:.3f} mm: "
                f"unconnected {before} -> {after}{capped_note}",
                flush=True,
            )

    final = len(current_report.get("unconnected_items", []))
    print(f"accepted {accepted} route(s): unconnected {initial} -> {final}")
    if args.attempted_state:
        print(
            f"recorded {len(attempt_outcomes)} attempted gap(s) in "
            f"{args.attempted_state}"
        )
    print(f"wrote {args.output}")


if __name__ == "__main__":
    main()
