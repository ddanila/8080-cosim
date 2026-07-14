#!/usr/bin/env python3
"""Close the final INTR gap by guarded conflict-derived rip-up and recovery."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[1]
ROUTER = ROOT / "kicad" / "repair_fdc_route_gaps.py"
CLOSER = ROOT / "kicad" / "close_unconnected_gaps.py"
REMOVE_HELPER = ROOT / "kicad" / "remove_board_item.py"
PRUNER = ROOT / "kicad" / "prune_dangling_tracks.py"
NET_RE = re.compile(r"\[([^]]+)\]")
LAYER_RE = re.compile(r" on ([FB])\.Cu(?:,|$)")
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


def sole_intr_gap(report: dict) -> tuple[float, float, float, float, str, str]:
    matches = []
    for gap in report.get("unconnected_items", []):
        items = gap.get("items", [])
        if len(items) != 2 or "pos" not in items[0] or "pos" not in items[1]:
            continue
        net = NET_RE.search(items[0].get("description", ""))
        if net is None or net.group(1) != "INTR":
            continue
        layers = []
        for item in items:
            layer = LAYER_RE.search(item.get("description", ""))
            layers.append(layer.group(1) if layer else "A")
        matches.append(
            (
                items[0]["pos"]["x"],
                items[0]["pos"]["y"],
                items[1]["pos"]["x"],
                items[1]["pos"]["y"],
                layers[0],
                layers[1],
            )
        )
    if len(matches) != 1:
        raise SystemExit(f"expected exactly one INTR gap, found {len(matches)}")
    return matches[0]


def conflict_uuids(report: dict) -> list[str]:
    result = set()
    for violation in report.get("violations", []):
        if violation.get("type") != "clearance":
            continue
        for item in violation.get("items", []):
            description = item.get("description", "")
            if not description.startswith(("Track ", "Via ")):
                continue
            net = NET_RE.search(description)
            if net is not None and net.group(1) == "INTR":
                continue
            if item.get("uuid"):
                result.add(item["uuid"])
    if not result:
        raise SystemExit("diagnostic INTR route exposed no removable copper conflicts")
    return sorted(result)


def run_closer(
    input_board: Path,
    output_board: Path,
    clearance: float,
    cli: Path,
    net: str | None = None,
) -> None:
    command = [
        sys.executable,
        str(CLOSER),
        str(input_board),
        str(output_board),
        "--max-distance",
        "400",
        "--mode",
        "M",
        "--search-margin",
        "60",
        "--grid-step",
        "0.10",
        "--route-clearance",
        str(clearance),
        "--timeout",
        "180",
        "--kicad-cli",
        str(cli),
    ]
    if net is not None:
        command.extend(("--net", net))
    subprocess.run(command, check=True)


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

    with tempfile.TemporaryDirectory(prefix="juku-close-intr-") as tmp_name:
        tmp = Path(tmp_name)
        initial_report = run_drc(cli, args.input, tmp / "initial.json")
        if len(initial_report.get("unconnected_items", [])) != 1:
            raise SystemExit("INTR rip-up expects the verified one-open candidate")
        x1, y1, x2, y2, layer1, layer2 = sole_intr_gap(initial_report)

        diagnostic_board = tmp / "intr-diagnostic.kicad_pcb"
        subprocess.run(
            [
                str(router_python),
                str(ROUTER),
                str(args.input),
                str(diagnostic_board),
                "gap",
                "INTR",
                f"{x1},{y1}",
                f"{x2},{y2}",
                "M",
                "60",
                "0.10",
                "0.15",
                layer1,
                layer2,
            ],
            check=True,
        )
        diagnostic_report = run_drc(cli, diagnostic_board, tmp / "diagnostic.json")
        conflicts = conflict_uuids(diagnostic_report)
        print(f"INTR diagnostic selected {len(conflicts)} conflicting copper items")

        ripped_board = tmp / "intr-ripped.kicad_pcb"
        subprocess.run(
            [
                str(router_python),
                str(REMOVE_HELPER),
                str(args.input),
                str(ripped_board),
                *conflicts,
            ],
            check=True,
        )
        intr_board = tmp / "intr-routed.kicad_pcb"
        run_closer(ripped_board, intr_board, 0.21, cli, "INTR")

        restored_board = tmp / "restored-020.kicad_pcb"
        run_closer(intr_board, restored_board, 0.20, cli)
        restored_margin_board = tmp / "restored-021.kicad_pcb"
        run_closer(restored_board, restored_margin_board, 0.21, cli)

        subprocess.run(
            [
                sys.executable,
                str(PRUNER),
                str(restored_margin_board),
                str(args.output),
                "--kicad-cli",
                str(cli),
                "--python",
                str(router_python),
            ],
            check=True,
        )

    final_report = run_drc(cli, args.output, args.output.with_suffix(".drc.json"))
    if final_report.get("unconnected_items"):
        raise SystemExit("final INTR transaction did not reach zero opens")
    final_counts: dict[str, int] = {}
    for violation in final_report.get("violations", []):
        kind = violation.get("type", "unknown")
        final_counts[kind] = final_counts.get(kind, 0) + 1
    remaining_blockers = {
        kind: final_counts.get(kind, 0)
        for kind in BLOCKERS
        if final_counts.get(kind, 0)
    }
    if remaining_blockers:
        raise SystemExit(f"final INTR transaction has blockers: {remaining_blockers}")
    print(
        f"closed INTR transactionally: conflicts={len(conflicts)} "
        f"unconnected=0 electrical_blockers=0"
    )
    print(f"wrote {args.output}")


if __name__ == "__main__":
    main()
