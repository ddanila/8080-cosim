#!/usr/bin/python3
"""Close an exhausted PCB gap by guarded conflict-derived copper rip-up.

The tool first proposes one route with a board-legal but less conservative
clearance than the global sweeps.  Only pre-existing, non-source copper items
that KiCad names as direct blockers of newly proposed route UUIDs are eligible
for removal.  It then routes the target net, restores every affected net, and
normally publishes the transaction only when total opens fall and no DRC class
grows.  An opt-in equal-open mode supports guarded topology exploration without
ever allowing the open count to increase.
"""

from __future__ import annotations

import argparse
from collections import Counter
import json
import math
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile

import pcbnew

from drc_gap_geometry import board_item_points, resolved_item_pair


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "kicad" / "juku.kicad_pcb"
ROUTER = ROOT / "kicad" / "repair_fdc_route_gaps.py"
CLOSER = ROOT / "kicad" / "close_unconnected_gaps.py"
REMOVE_HELPER = ROOT / "kicad" / "remove_board_items.py"
NET_RE = re.compile(r"\[([^]]+)\]")
LAYER_RE = re.compile(r" on ([FB])\.Cu(?:,|$)")
ELECTRICAL_BLOCKERS = {
    "shorting_items",
    "clearance",
    "tracks_crossing",
    "hole_clearance",
    "hole_to_hole",
    "copper_edge_clearance",
}


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


def violation_counts(report: dict) -> Counter[str]:
    return Counter(
        str(violation.get("type", "unknown"))
        for violation in report.get("violations", [])
    )


def violation_item_uuids(report: dict, kind: str) -> set[str]:
    return {
        str(item.get("uuid", ""))
        for violation in report.get("violations", [])
        if violation.get("type") == kind
        for item in violation.get("items", [])
        if item.get("uuid")
    }


def net_gaps(
    report: dict,
    netname: str,
    points_by_uuid: dict[str, tuple[tuple[float, float], ...]] | None = None,
) -> list[tuple[float, float, float, float, float, str, str]]:
    result = []
    for gap in report.get("unconnected_items", []):
        items = gap.get("items", [])
        if len(items) != 2 or "pos" not in items[0] or "pos" not in items[1]:
            continue
        net = NET_RE.search(str(items[0].get("description", "")))
        if net is None or net.group(1) != netname:
            continue
        layers = []
        for item in items:
            layer = LAYER_RE.search(str(item.get("description", "")))
            layers.append(layer.group(1) if layer else "A")
        a, b = resolved_item_pair(items[0], items[1], points_by_uuid)
        result.append(
            (
                math.dist(a, b),
                a[0],
                a[1],
                b[0],
                b[1],
                layers[0],
                layers[1],
            )
        )
    return sorted(result)


def track_nets(board: pcbnew.BOARD) -> dict[str, str]:
    return {uuid(item): item.GetNetname() for item in board.GetTracks()}


def discard_temporary_board(path: Path, directory: Path) -> None:
    if path.parent == directory:
        path.unlink(missing_ok=True)


def direct_conflicts(
    report: dict,
    new_route_uuids: set[str],
    baseline_tracks: dict[str, str],
    source_uuids: set[str],
    target_net: str,
) -> tuple[set[str], set[str], set[str]]:
    removable: set[str] = set()
    affected_nets: set[str] = set()
    unremovable: set[str] = set()
    relevant = 0
    for violation in report.get("violations", []):
        if violation.get("type") not in ELECTRICAL_BLOCKERS:
            continue
        items = violation.get("items", [])
        item_uuids = {str(item.get("uuid", "")) for item in items}
        if not (item_uuids & new_route_uuids):
            continue
        relevant += 1
        found_removable = False
        for item in items:
            item_uuid = str(item.get("uuid", ""))
            if item_uuid in new_route_uuids:
                continue
            netname = baseline_tracks.get(item_uuid)
            if (
                netname is not None
                and netname != target_net
                and item_uuid not in source_uuids
            ):
                removable.add(item_uuid)
                affected_nets.add(netname)
                found_removable = True
            else:
                unremovable.add(str(item.get("description", item_uuid or "item")))
        if not found_removable:
            unremovable.add(
                f"{violation.get('type', 'blocker')} has no removable baseline copper"
            )
    if relevant == 0:
        return set(), set(), set()
    return removable, affected_nets, unremovable


def run_closer(
    input_board: Path,
    output_board: Path,
    netname: str,
    cli: Path,
    search_margin: float,
    grid_step: float,
    clearance: float,
    timeout: float,
) -> None:
    subprocess.run(
        [
            sys.executable,
            str(CLOSER),
            str(input_board),
            str(output_board),
            "--min-distance",
            "0",
            "--max-distance",
            "450",
            "--mode",
            "M",
            "--search-margin",
            str(search_margin),
            "--grid-step",
            str(grid_step),
            "--route-clearance",
            str(clearance),
            "--timeout",
            str(timeout),
            "--net",
            netname,
            "--kicad-cli",
            str(cli),
        ],
        check=True,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--net", required=True, help="target net with an open gap")
    parser.add_argument(
        "--gap-index",
        type=int,
        default=0,
        help="zero-based distance-sorted gap index on the target net",
    )
    parser.add_argument(
        "--gap-report",
        type=Path,
        help=(
            "select the target marker from this retained KiCad DRC JSON; the "
            "fresh live DRC still governs counts and every publication gate"
        ),
    )
    parser.add_argument("--source", type=Path, default=SOURCE)
    parser.add_argument("--search-margin", type=float, default=60.0)
    parser.add_argument("--grid-step", type=float, default=0.10)
    parser.add_argument(
        "--diagnostic-grid-step",
        type=float,
        help=(
            "lattice used only to expose blockers; defaults to --grid-step "
            "and may differ from the legal target-route lattice"
        ),
    )
    parser.add_argument(
        "--restore-grid-steps",
        help=(
            "comma-separated grid phases for each displaced-net restoration; "
            "defaults to --grid-step"
        ),
    )
    parser.add_argument(
        "--restore-net-priority",
        help=(
            "comma-separated affected nets to restore first; all remaining "
            "affected nets follow in sorted order"
        ),
    )
    parser.add_argument(
        "--diagnostic-clearance",
        type=float,
        help=(
            "proposal clearance used only to expose blockers; defaults to the "
            "final route clearance"
        ),
    )
    parser.add_argument("--route-clearance", type=float, default=0.21)
    parser.add_argument("--timeout", type=float, default=180.0)
    parser.add_argument("--max-conflicts", type=int, default=8)
    parser.add_argument(
        "--diagnose-only",
        action="store_true",
        help=(
            "classify the diagnostic path's removable and fixed blockers, "
            "write --summary when requested, and perform no rip-up"
        ),
    )
    parser.add_argument(
        "--allow-mixed-diagnostic-blockers",
        action="store_true",
        help=(
            "attempt the bounded removable-copper subset even when the "
            "diagnostic path also touches fixed blockers; final DRC invariants "
            "still govern publication"
        ),
    )
    parser.add_argument(
        "--allow-equal-open-swap",
        action="store_true",
        help=(
            "publish a DRC-neutral transaction with the same open count when "
            "the selected target gap is gone, for a subsequent guarded sweep"
        ),
    )
    parser.add_argument("--kicad-cli", type=Path)
    parser.add_argument("--python", type=Path, help="Python interpreter with pcbnew")
    parser.add_argument(
        "--diagnostic-report",
        type=Path,
        help="retain the diagnostic KiCad DRC JSON even when the transaction fails",
    )
    parser.add_argument(
        "--transaction-board",
        type=Path,
        help=(
            "retain the restored pre-acceptance board for diagnosis even when "
            "a final publication invariant fails"
        ),
    )
    parser.add_argument(
        "--transaction-report",
        type=Path,
        help=(
            "retain the restored pre-acceptance KiCad DRC JSON even when a "
            "final publication invariant fails"
        ),
    )
    parser.add_argument("--summary", type=Path)
    args = parser.parse_args()

    if args.input.resolve() == args.output.resolve():
        raise SystemExit("input and output must differ")
    if args.transaction_board and args.transaction_board.resolve() in {
        args.input.resolve(),
        args.output.resolve(),
    }:
        raise SystemExit("transaction diagnostic board must differ from input/output")
    if args.gap_index < 0:
        raise SystemExit("--gap-index must be non-negative")
    diagnostic_grid_step = (
        args.grid_step
        if args.diagnostic_grid_step is None
        else args.diagnostic_grid_step
    )
    if (
        args.search_margin <= 0
        or args.grid_step <= 0
        or diagnostic_grid_step <= 0
    ):
        raise SystemExit("search margin and grid step must be positive")
    try:
        restore_grid_steps = (
            [float(value) for value in args.restore_grid_steps.split(",")]
            if args.restore_grid_steps
            else [args.grid_step]
        )
    except ValueError as error:
        raise SystemExit("restore grid steps must be comma-separated numbers") from error
    if not restore_grid_steps or any(step <= 0 for step in restore_grid_steps):
        raise SystemExit("restore grid steps must be positive")
    restore_net_priority = (
        [value.strip() for value in args.restore_net_priority.split(",")]
        if args.restore_net_priority
        else []
    )
    if any(not value for value in restore_net_priority):
        raise SystemExit("restore net priority must be comma-separated net names")
    if len(set(restore_net_priority)) != len(restore_net_priority):
        raise SystemExit("restore net priority contains duplicates")
    diagnostic_clearance = (
        args.route_clearance
        if args.diagnostic_clearance is None
        else args.diagnostic_clearance
    )
    if diagnostic_clearance <= 0 or args.route_clearance <= 0 or args.timeout <= 0:
        raise SystemExit(
            "diagnostic clearance, route clearance, and timeout must be positive"
        )
    if args.max_conflicts <= 0:
        raise SystemExit("--max-conflicts must be positive")
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

    with tempfile.TemporaryDirectory(prefix="juku-gap-ripup-") as tmp_name:
        tmp = Path(tmp_name)
        initial_report = run_drc(cli, args.input, tmp / "initial.json")
        initial_counts = violation_counts(initial_report)
        initial_open = len(initial_report.get("unconnected_items", []))
        initial_target_open = len(net_gaps(initial_report, args.net))
        baseline = pcbnew.LoadBoard(str(args.input))
        baseline_points = board_item_points(baseline)
        if args.gap_report:
            try:
                gap_report = json.loads(args.gap_report.read_text())
            except (OSError, json.JSONDecodeError) as error:
                raise SystemExit(
                    f"cannot read --gap-report {args.gap_report}: {error}"
                ) from error
        else:
            gap_report = initial_report
        gaps = net_gaps(gap_report, args.net, baseline_points)
        if args.gap_index >= len(gaps):
            raise SystemExit(
                f"{args.net} has {len(gaps)} gap(s), index {args.gap_index} is invalid"
            )
        if initial_target_open == 0:
            raise SystemExit(f"live DRC reports no open gap on target net {args.net}")
        selected = gaps[args.gap_index]
        distance, x1, y1, x2, y2, layer1, layer2 = selected

        baseline_tracks = track_nets(baseline)
        initial_tracks = len(baseline_tracks)
        source = pcbnew.LoadBoard(str(args.source))
        source_uuids = set(track_nets(source))

        diagnostic_board = tmp / "diagnostic.kicad_pcb"
        try:
            subprocess.run(
                [
                    str(router_python),
                    str(ROUTER),
                    str(args.input),
                    str(diagnostic_board),
                    "gap",
                    args.net,
                    f"{x1},{y1}",
                    f"{x2},{y2}",
                    "M",
                    str(args.search_margin),
                    str(diagnostic_grid_step),
                    str(diagnostic_clearance),
                    layer1,
                    layer2,
                ],
                check=True,
                timeout=args.timeout,
            )
        except subprocess.CalledProcessError as error:
            raise SystemExit(
                f"diagnostic router could not propose {args.net} gap "
                f"{args.gap_index} at {diagnostic_clearance} mm clearance"
            ) from error
        except subprocess.TimeoutExpired as error:
            raise SystemExit(
                f"diagnostic router timed out on {args.net} gap "
                f"{args.gap_index} after {args.timeout:g} seconds"
            ) from error
        diagnostic = pcbnew.LoadBoard(str(diagnostic_board))
        diagnostic_tracks = track_nets(diagnostic)
        new_route_uuids = set(diagnostic_tracks) - set(baseline_tracks)
        if not new_route_uuids:
            raise SystemExit("diagnostic route added no track/via UUIDs")
        diagnostic_report_path = tmp / "diagnostic.json"
        diagnostic_report = run_drc(cli, diagnostic_board, diagnostic_report_path)
        if args.diagnostic_report:
            args.diagnostic_report.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(diagnostic_report_path, args.diagnostic_report)
            print(f"wrote {args.diagnostic_report}")
        conflicts, affected_nets, unremovable = direct_conflicts(
            diagnostic_report,
            new_route_uuids,
            baseline_tracks,
            source_uuids,
            args.net,
        )
        print(
            f"{args.net} diagnostic: gap={distance:.3f} mm, "
            f"new_items={len(new_route_uuids)}, conflicts={len(conflicts)}, "
            f"affected_nets={sorted(affected_nets)}"
        )
        if args.diagnose_only:
            diagnostic_summary = {
                "schema_version": 1,
                "mode": "diagnose-only",
                "input": str(args.input),
                "target_net": args.net,
                "target_gap_index": args.gap_index,
                "target_gap_distance_mm": distance,
                "target_gap_report": str(args.gap_report) if args.gap_report else None,
                "initial_target_net_gaps": initial_target_open,
                "diagnostic_clearance_mm": diagnostic_clearance,
                "diagnostic_grid_step_mm": diagnostic_grid_step,
                "route_clearance_mm": args.route_clearance,
                "route_grid_step_mm": args.grid_step,
                "diagnostic_new_items": len(new_route_uuids),
                "diagnostic_unremovable_blockers": sorted(unremovable),
                "removable_conflicts": [
                    {"uuid": item_uuid, "net": baseline_tracks[item_uuid]}
                    for item_uuid in sorted(conflicts)
                ],
                "affected_nets": sorted(affected_nets),
                "within_max_conflicts": len(conflicts) <= args.max_conflicts,
            }
            if args.summary:
                args.summary.parent.mkdir(parents=True, exist_ok=True)
                args.summary.write_text(json.dumps(diagnostic_summary, indent=2) + "\n")
                print(f"wrote {args.summary}")
            print(
                "GAP DIAGNOSTIC: PASS; "
                f"net={args.net}, conflicts={len(conflicts)}, "
                f"fixed={len(unremovable)}"
            )
            return
        if unremovable and not args.allow_mixed_diagnostic_blockers:
            raise SystemExit(
                "diagnostic route has source-owned, pad, edge, self, or other "
                f"unremovable blockers: {sorted(unremovable)}"
            )
        if unremovable and not conflicts:
            raise SystemExit(
                "diagnostic route exposed fixed blockers but no removable "
                f"copper conflicts: {sorted(unremovable)}"
            )
        if unremovable:
            print(
                "mixed diagnostic: retaining fixed blockers and trying only "
                f"the removable subset; fixed={sorted(unremovable)}"
            )
        unknown_restore_nets = set(restore_net_priority) - affected_nets
        if unknown_restore_nets:
            raise SystemExit(
                "restore net priority names are not affected by this transaction: "
                f"{sorted(unknown_restore_nets)}"
            )
        restore_net_order = restore_net_priority + sorted(
            affected_nets - set(restore_net_priority)
        )
        if len(conflicts) > args.max_conflicts:
            raise SystemExit(
                f"diagnostic route needs {len(conflicts)} conflicts removed; "
                f"limit is {args.max_conflicts}"
            )
        current = args.input
        if conflicts:
            remove_json = tmp / "remove.json"
            remove_json.write_text(json.dumps(sorted(conflicts)) + "\n")
            ripped = tmp / "ripped.kicad_pcb"
            subprocess.run(
                [
                    str(router_python),
                    str(REMOVE_HELPER),
                    str(args.input),
                    str(ripped),
                    str(remove_json),
                ],
                check=True,
            )
            current = ripped

        target_routed = tmp / "target-routed.kicad_pcb"
        target_input = current
        run_closer(
            current,
            target_routed,
            args.net,
            cli,
            args.search_margin,
            args.grid_step,
            args.route_clearance,
            args.timeout,
        )
        discard_temporary_board(target_input, tmp)
        target_report = run_drc(cli, target_routed, tmp / "target-routed.json")
        if len(net_gaps(target_report, args.net)) >= initial_target_open:
            raise SystemExit(
                "target-net gap count did not decrease after removing its "
                "diagnostic conflicts"
            )
        current = target_routed
        for net_index, netname in enumerate(restore_net_order, 1):
            for grid_index, restore_grid_step in enumerate(restore_grid_steps, 1):
                restored = tmp / f"restored-{net_index}-{grid_index}.kicad_pcb"
                previous = current
                run_closer(
                    current,
                    restored,
                    netname,
                    cli,
                    args.search_margin,
                    restore_grid_step,
                    args.route_clearance,
                    args.timeout,
                )
                current = restored
                discard_temporary_board(previous, tmp)

        final_report_path = tmp / "final.json"
        final_report = run_drc(cli, current, final_report_path)
        newly_dangling_vias = (
            violation_item_uuids(final_report, "via_dangling")
            - violation_item_uuids(initial_report, "via_dangling")
        )
        removable_dangling_vias = {
            item_uuid
            for item_uuid in newly_dangling_vias
            if item_uuid in baseline_tracks
            and item_uuid not in source_uuids
            and baseline_tracks[item_uuid] in affected_nets
        }
        if removable_dangling_vias:
            cleanup_json = tmp / "remove-newly-dangling-vias.json"
            cleanup_json.write_text(json.dumps(sorted(removable_dangling_vias)) + "\n")
            cleaned = tmp / "cleaned-newly-dangling-vias.kicad_pcb"
            subprocess.run(
                [
                    str(router_python),
                    str(REMOVE_HELPER),
                    str(current),
                    str(cleaned),
                    str(cleanup_json),
                ],
                check=True,
            )
            discard_temporary_board(current, tmp)
            current = cleaned
            final_report = run_drc(cli, current, final_report_path)
            print(
                "removed transaction-orphaned migrated vias: "
                f"{sorted(removable_dangling_vias)}"
            )
        if args.transaction_board:
            args.transaction_board.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(current, args.transaction_board)
            print(f"wrote {args.transaction_board}")
        if args.transaction_report:
            args.transaction_report.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(final_report_path, args.transaction_report)
            print(f"wrote {args.transaction_report}")
        final_counts = violation_counts(final_report)
        final_open = len(final_report.get("unconnected_items", []))
        blockers = {
            kind: final_counts[kind]
            for kind in sorted(ELECTRICAL_BLOCKERS)
            if final_counts[kind]
        }
        increases = {
            kind: (initial_counts[kind], final_counts[kind])
            for kind in sorted(set(initial_counts) | set(final_counts))
            if final_counts[kind] > initial_counts[kind]
        }
        if final_open > initial_open or (
            final_open == initial_open and not args.allow_equal_open_swap
        ):
            raise SystemExit(
                f"rip-up transaction did not reduce opens: {initial_open}->{final_open}"
            )
        if blockers or increases:
            raise SystemExit(
                f"rip-up transaction failed DRC invariants: blockers={blockers}, "
                f"increases={increases}"
            )
        final_target_open = len(net_gaps(final_report, args.net))
        if final_target_open >= initial_target_open:
            raise SystemExit(
                "target-net gap count did not decrease after rip-up transaction"
            )

        final_board = pcbnew.LoadBoard(str(current))
        final_tracks = len(track_nets(final_board))
        args.output.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(current, args.output)
        summary = {
            "schema_version": 1,
            "input": str(args.input),
            "output": str(args.output),
            "target_net": args.net,
            "target_gap_index": args.gap_index,
            "target_gap_distance_mm": distance,
            "target_gap_report": str(args.gap_report) if args.gap_report else None,
            "initial_target_net_gaps": initial_target_open,
            "final_target_net_gaps": final_target_open,
            "diagnostic_clearance_mm": diagnostic_clearance,
            "diagnostic_grid_step_mm": diagnostic_grid_step,
            "route_clearance_mm": args.route_clearance,
            "route_grid_step_mm": args.grid_step,
            "restore_grid_steps_mm": restore_grid_steps,
            "restore_net_order": restore_net_order,
            "diagnostic_new_items": len(new_route_uuids),
            "diagnostic_unremovable_blockers": sorted(unremovable),
            "removed_conflicts": [
                {"uuid": item_uuid, "net": baseline_tracks[item_uuid]}
                for item_uuid in sorted(conflicts)
            ],
            "removed_newly_dangling_vias": [
                {"uuid": item_uuid, "net": baseline_tracks[item_uuid]}
                for item_uuid in sorted(removable_dangling_vias)
            ],
            "restored_nets": sorted(affected_nets),
            "initial_tracks": initial_tracks,
            "final_tracks": final_tracks,
            "initial_unconnected": initial_open,
            "final_unconnected": final_open,
            "equal_open_swap": final_open == initial_open,
            "electrical_blockers": blockers,
            "drc_count_increases": increases,
        }
        if args.summary:
            args.summary.parent.mkdir(parents=True, exist_ok=True)
            args.summary.write_text(json.dumps(summary, indent=2) + "\n")
            print(f"wrote {args.summary}")

    print(
        f"GAP RIP-UP: PASS; net={args.net}, opens={initial_open}->{final_open}, "
        f"conflicts={len(conflicts)}, restored={sorted(affected_nets)}"
    )
    print(f"wrote {args.output}")


if __name__ == "__main__":
    main()
