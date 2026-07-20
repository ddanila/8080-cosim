#!/usr/bin/env python3
"""Prune migrated dangling copper with an uncapped connectivity guard."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import shutil
import subprocess
import tempfile

from prune_dangling_tracks import (
    BLOCKERS,
    DEFAULT_SOURCE,
    board_track_uuids,
    counts,
    dangling_uuids,
    remove_track,
    remove_tracks,
    run_drc,
)

ROOT = Path(__file__).resolve().parents[1]
UNCONNECTED_HELPER = ROOT / "kicad/report_board_unconnected.py"


def uncapped_unconnected(python: Path, board: Path) -> int:
    return int(
        subprocess.check_output(
            [str(python), str(UNCONNECTED_HELPER), str(board)], text=True
        ).strip()
    )


def acceptable(
    before: dict, after: dict, before_uncapped: int, after_uncapped: int
) -> bool:
    if after_uncapped > before_uncapped:
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
    parser.add_argument("--python", type=Path)
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--batch-size", type=int, default=1)
    parser.add_argument("--max-removals", type=int, default=0)
    parser.add_argument("--adaptive-batch", action="store_true")
    args = parser.parse_args()
    if args.input.resolve() == args.output.resolve():
        raise SystemExit("input and output must differ")
    if args.batch_size <= 0 or args.max_removals < 0:
        raise SystemExit("batch size must be positive and max removals non-negative")
    cli = args.kicad_cli or Path(
        subprocess.check_output([str(ROOT / "scripts/find-kicad-cli.sh")], text=True).strip()
    )
    router_python = args.python or Path(
        subprocess.check_output([str(ROOT / "scripts/find-kicad-python.sh")], text=True).strip()
    )
    shutil.copyfile(args.input, args.output)
    with tempfile.TemporaryDirectory(prefix="juku-prune-uncapped-") as tmp_name:
        tmp = Path(tmp_name)
        current = run_drc(cli, args.output, tmp / "current.json")
        current_uncapped = uncapped_unconnected(router_python, args.output)
        source_uuids = board_track_uuids(
            router_python, args.source, tmp / "source-track-uuids.json"
        )
        protected = set(dangling_uuids(current)) & source_uuids
        if protected:
            raise SystemExit(
                f"refusing to prune {len(protected)} dangling source-copper item(s)"
            )
        initial = len(dangling_uuids(current))
        initial_opens = current_uncapped
        accepted = 0
        batch_size = args.batch_size
        while dangling_uuids(current):
            progress = False
            eligible = [uuid for uuid in dangling_uuids(current) if uuid not in source_uuids]
            for offset in range(0, len(eligible), batch_size):
                batch = eligible[offset : offset + batch_size]
                candidate = tmp / "candidate.kicad_pcb"
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
                candidate_report = run_drc(cli, candidate, tmp / "candidate.json")
                candidate_uncapped = uncapped_unconnected(router_python, candidate)
                if not acceptable(
                    current, candidate_report, current_uncapped, candidate_uncapped
                ):
                    continue
                os.replace(candidate, args.output)
                current = candidate_report
                current_uncapped = candidate_uncapped
                accepted += len(batch)
                progress = True
                if args.adaptive_batch and len(batch) < batch_size:
                    batch_size = len(batch)
                print(
                    f"accept prune batch={len(batch)}: dangling -> "
                    f"{len(dangling_uuids(current))}; uncapped opens -> {current_uncapped}",
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
    print(
        f"accepted {accepted} prune(s): dangling {initial} -> {final}; "
        f"uncapped opens {initial_opens} -> {current_uncapped}"
    )
    print(f"wrote {args.output}")
    if final and not (args.max_removals and accepted >= args.max_removals):
        raise SystemExit(f"{final} dangling item(s) could not be pruned safely")


if __name__ == "__main__":
    main()
