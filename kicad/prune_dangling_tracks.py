#!/usr/bin/env python3
"""Transactionally prune non-source tracks/vias that are disconnected tails."""

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
REMOVE_BATCH_HELPER = ROOT / "kicad" / "remove_board_items.py"
UUID_HELPER = ROOT / "kicad" / "report_board_track_uuids.py"
DEFAULT_SOURCE = ROOT / "kicad" / "juku.kicad_pcb"
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


def board_track_uuids(python: Path, board: Path, output: Path) -> set[str]:
    subprocess.run(
        [str(python), str(UUID_HELPER), str(board), str(output)],
        text=True,
        check=True,
    )
    return set(json.loads(output.read_text()))


def remove_track(
    python: Path, input_board: Path, output_board: Path, uuid: str
) -> None:
    subprocess.run(
        [str(python), str(REMOVE_HELPER), str(input_board), str(output_board), uuid],
        text=True,
        check=True,
    )


def remove_tracks(
    python: Path,
    input_board: Path,
    output_board: Path,
    uuids: list[str],
    uuid_file: Path,
) -> None:
    uuid_file.write_text(json.dumps(sorted(uuids)) + "\n")
    subprocess.run(
        [
            str(python),
            str(REMOVE_BATCH_HELPER),
            str(input_board),
            str(output_board),
            str(uuid_file),
        ],
        text=True,
        check=True,
    )


def acceptable(before: dict, after: dict, allow_open: bool) -> bool:
    before_opens = len(before.get("unconnected_items", []))
    after_opens = len(after.get("unconnected_items", []))
    if (not allow_open and after_opens) or after_opens > before_opens:
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
    parser.add_argument(
        "--source",
        type=Path,
        default=DEFAULT_SOURCE,
        help="source PCB whose routed-item UUIDs may never be removed",
    )
    parser.add_argument(
        "--allow-open",
        action="store_true",
        help="permit a nonzero but never increasing unconnected-item count",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=1,
        help="try this many dangling items per transaction, halving on rejection",
    )
    parser.add_argument(
        "--max-removals",
        type=int,
        default=0,
        help="stop after this many accepted removals; zero means exhaust the board",
    )
    parser.add_argument(
        "--adaptive-batch",
        action="store_true",
        help="keep a smaller accepted remainder as the next transaction size",
    )
    args = parser.parse_args()

    if args.input.resolve() == args.output.resolve():
        raise SystemExit("input and output must differ")
    if args.batch_size <= 0:
        raise SystemExit("--batch-size must be positive")
    if args.max_removals < 0:
        raise SystemExit("--max-removals must be non-negative")
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
        if current.get("unconnected_items") and not args.allow_open:
            raise SystemExit("refusing to prune before the board reaches zero opens")
        source_uuids = board_track_uuids(
            router_python, args.source, tmp / "source-track-uuids.json"
        )
        protected = set(dangling_uuids(current)) & source_uuids
        if protected:
            raise SystemExit(
                f"refusing to prune {len(protected)} dangling source-copper item(s)"
            )
        initial = len(dangling_uuids(current))
        initial_opens = len(current.get("unconnected_items", []))
        accepted = 0
        batch_size = args.batch_size
        while dangling_uuids(current):
            progress = False
            eligible = [uuid for uuid in dangling_uuids(current) if uuid not in source_uuids]
            for offset in range(0, len(eligible), batch_size):
                batch = eligible[offset : offset + batch_size]
                candidate = tmp / "candidate.kicad_pcb"
                candidate_report_path = tmp / "candidate.json"
                if len(batch) == 1:
                    remove_track(router_python, args.output, candidate, batch[0])
                else:
                    remove_tracks(
                        router_python,
                        args.output,
                        candidate,
                        batch,
                        tmp / "batch-uuids.json",
                    )
                candidate_report = run_drc(cli, candidate, candidate_report_path)
                if not acceptable(current, candidate_report, args.allow_open):
                    continue
                os.replace(candidate, args.output)
                current = candidate_report
                accepted += len(batch)
                progress = True
                if args.adaptive_batch and len(batch) < batch_size:
                    batch_size = len(batch)
                print(
                    f"accept prune batch={len(batch)}: dangling -> "
                    f"{len(dangling_uuids(current))}",
                    flush=True,
                )
                break
            if args.max_removals and accepted >= args.max_removals:
                break
            if not progress:
                if batch_size == 1:
                    break
                batch_size = max(1, batch_size // 2)
                print(f"no acceptable batch; retry size={batch_size}", flush=True)

    final = len(dangling_uuids(current))
    final_opens = len(current.get("unconnected_items", []))
    print(
        f"accepted {accepted} prune(s): dangling {initial} -> {final}; "
        f"opens {initial_opens} -> {final_opens}"
    )
    print(f"wrote {args.output}")
    reached_bound = bool(args.max_removals and accepted >= args.max_removals)
    if final and not reached_bound:
        raise SystemExit(f"{final} dangling track(s) could not be pruned safely")


if __name__ == "__main__":
    main()
