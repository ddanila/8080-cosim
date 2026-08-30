#!/usr/bin/env python3
"""Select the conservative HDL CI lanes affected by a set of changed paths."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = ROOT / "ci" / "hdl-ci.json"


def load_manifest(path: Path = DEFAULT_MANIFEST) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def _matches(path: str, rule: dict[str, Any]) -> bool:
    if path in rule.get("exclude_exact", []):
        return False
    return (
        path in rule.get("exact", [])
        or any(path.startswith(prefix) for prefix in rule.get("prefixes", []))
        or any(path.endswith(suffix) for suffix in rule.get("suffixes", []))
    )


def select_jobs(
    changed_paths: Iterable[str],
    manifest: dict[str, Any],
    *,
    force_full: bool = False,
    skip_all: bool = False,
) -> dict[str, Any]:
    """Return a fail-open selection for the supplied repository-relative paths."""

    jobs = tuple(manifest["jobs"])
    normalized_paths = []
    for raw_path in changed_paths:
        path = raw_path.strip()
        if path.startswith("./"):
            path = path[2:]
        if path:
            normalized_paths.append(path)
    paths = sorted(set(normalized_paths))
    selected: set[str] = set()
    matched_rules: set[str] = set()
    unmatched: list[str] = []
    full_reason = ""

    skip_reason = ""
    if skip_all:
        skip_reason = "full sentinel already succeeded for this exact SHA"
    elif force_full:
        full_reason = "forced full run"
    elif not paths:
        full_reason = "no trustworthy changed-file set"
    else:
        for path in paths:
            matching_rules = [
                rule for rule in manifest["rules"] if _matches(path, rule)
            ]
            exclusive_rules = [
                rule for rule in matching_rules if rule.get("exclusive", False)
            ]
            if exclusive_rules:
                matching_rules = exclusive_rules
            path_matched = bool(matching_rules)
            for rule in matching_rules:
                matched_rules.add(rule["name"])
                if "*" in rule["jobs"]:
                    full_reason = f"shared/control path: {path}"
                else:
                    selected.update(rule["jobs"])
            if not path_matched:
                unmatched.append(path)

        if unmatched and not full_reason:
            full_reason = f"unclassified path: {unmatched[0]}"

    full = bool(full_reason) and not skip_all
    if full:
        selected = set(jobs)

    return {
        "full": full,
        "full_reason": full_reason,
        "skip_reason": skip_reason,
        "jobs": {job: job in selected for job in jobs},
        "changed_paths": paths,
        "matched_rules": sorted(matched_rules),
        "unmatched_paths": unmatched,
    }


def _read_paths(path: str) -> list[str]:
    if path == "-":
        import sys

        return sys.stdin.read().splitlines()
    return Path(path).read_text(encoding="utf-8").splitlines()


def _output_name(job: str) -> str:
    return "run_" + job.replace("-", "_")


def _write_github_outputs(path: Path, selection: dict[str, Any]) -> None:
    contract = {
        "full": selection["full"],
        "skip_reason": selection["skip_reason"],
        "jobs": selection["jobs"],
    }
    compact = json.dumps(contract, sort_keys=True, separators=(",", ":"))
    with path.open("a", encoding="utf-8") as handle:
        handle.write(f"run_full={'true' if selection['full'] else 'false'}\n")
        for job, enabled in selection["jobs"].items():
            handle.write(f"{_output_name(job)}={'true' if enabled else 'false'}\n")
        handle.write(f"selection_json={compact}\n")


def _write_summary(path: Path, selection: dict[str, Any]) -> None:
    with path.open("a", encoding="utf-8") as handle:
        handle.write("## HDL CI selection\n\n")
        if selection["full"]:
            handle.write(f"Full suite: `{selection['full_reason']}`\n\n")
        elif selection["skip_reason"]:
            handle.write(f"No lanes needed: `{selection['skip_reason']}`\n\n")
        else:
            rules = ", ".join(selection["matched_rules"]) or "none"
            handle.write(f"Scoped suite; matched rules: `{rules}`\n\n")
        handle.write("| Lane | Selected |\n|---|---|\n")
        for job, enabled in selection["jobs"].items():
            handle.write(f"| `{job}` | {'yes' if enabled else 'no'} |\n")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--paths-file", default="-")
    parser.add_argument("--force-full", action="store_true")
    parser.add_argument("--skip-all", action="store_true")
    parser.add_argument("--github-output", type=Path)
    parser.add_argument("--step-summary", type=Path)
    args = parser.parse_args()

    selection = select_jobs(
        _read_paths(args.paths_file),
        load_manifest(args.manifest),
        force_full=args.force_full,
        skip_all=args.skip_all,
    )
    print(json.dumps(selection, indent=2, sort_keys=True))
    if args.github_output:
        _write_github_outputs(args.github_output, selection)
    if args.step_summary:
        _write_summary(args.step_summary, selection)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
