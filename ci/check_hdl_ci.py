#!/usr/bin/env python3
"""Validate the HDL CI manifest against the workflow and selector rules."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from ci.select_hdl_jobs import load_manifest, select_jobs  # noqa: E402


WORKFLOW = ROOT / ".github" / "workflows" / "hdl.yml"
ENTRYPOINT_RE = re.compile(
    r"(?<![A-Za-z0-9_.-])((?:sync|scripts|spinoffs)/[^\s\"'`\\]+?\.(?:sh|py))(?=\s|$)"
)
JOB_RE = re.compile(r"^  ([A-Za-z0-9_-]+):\s*$")
RUN_RE = re.compile(r"^        run:\s*(.*)$")


def workflow_run_text_by_job(text: str) -> dict[str, str]:
    jobs: dict[str, list[str]] = {}
    current_job: str | None = None
    lines = text.splitlines()
    index = 0
    in_jobs = False

    while index < len(lines):
        line = lines[index]
        if line == "jobs:":
            in_jobs = True
            index += 1
            continue
        if in_jobs:
            match = JOB_RE.match(line)
            if match:
                current_job = match.group(1)
                jobs.setdefault(current_job, [])
                index += 1
                continue
            run_match = RUN_RE.match(line)
            if current_job and run_match:
                value = run_match.group(1)
                if value not in {"|", ">", "|-", ">-"}:
                    jobs[current_job].append(value)
                    index += 1
                    continue
                index += 1
                body: list[str] = []
                while index < len(lines):
                    nested = lines[index]
                    if nested.strip() and len(nested) - len(nested.lstrip()) <= 8:
                        break
                    body.append(nested.strip())
                    index += 1
                jobs[current_job].append("\n".join(body))
                continue
        index += 1
    return {job: "\n".join(parts) for job, parts in jobs.items()}


def workflow_block_by_job(text: str) -> dict[str, str]:
    blocks: dict[str, list[str]] = {}
    current_job: str | None = None
    in_jobs = False
    for line in text.splitlines():
        if line == "jobs:":
            in_jobs = True
            continue
        if not in_jobs:
            continue
        match = JOB_RE.match(line)
        if match:
            current_job = match.group(1)
            blocks[current_job] = [line]
        elif current_job:
            blocks[current_job].append(line)
    return {job: "\n".join(lines) for job, lines in blocks.items()}


def main() -> int:
    manifest = load_manifest()
    workflow_text = WORKFLOW.read_text(encoding="utf-8")
    run_text = workflow_run_text_by_job(workflow_text)
    job_blocks = workflow_block_by_job(workflow_text)
    errors: list[str] = []

    manifest_jobs = set(manifest["jobs"])
    missing_jobs = manifest_jobs - set(run_text)
    if missing_jobs:
        errors.append(f"manifest jobs absent from workflow: {sorted(missing_jobs)}")

    for job, job_data in manifest["jobs"].items():
        expected = set(job_data["entrypoints"])
        discovered = set(ENTRYPOINT_RE.findall(run_text.get(job, "")))
        if expected != discovered:
            missing = sorted(expected - discovered)
            extra = sorted(discovered - expected)
            if missing:
                errors.append(f"{job}: manifest-only entrypoints: {missing}")
            if extra:
                errors.append(f"{job}: unmanifested workflow entrypoints: {extra}")
        for entrypoint in expected:
            if not (ROOT / entrypoint).is_file():
                errors.append(f"{job}: missing entrypoint file: {entrypoint}")
            selection = select_jobs([entrypoint], manifest)
            if not selection["jobs"].get(job, False):
                errors.append(f"{job}: selector does not select owner for {entrypoint}")
        output = "run_" + job.replace("-", "_")
        expected_condition = f"if: needs.changes.outputs.{output} == 'true'"
        block = job_blocks.get(job, "")
        if "needs: changes" not in block:
            errors.append(f"{job}: must depend on the selector job")
        if expected_condition not in block:
            errors.append(f"{job}: missing selector condition: {expected_condition}")
        if f"{output}: ${{{{ steps.selector.outputs.{output} }}}}" not in job_blocks.get(
            "changes", ""
        ):
            errors.append(f"changes: missing exported selector output: {output}")

    known_jobs = manifest_jobs | {"*"}
    rule_names: set[str] = set()
    for rule in manifest["rules"]:
        if rule["name"] in rule_names:
            errors.append(f"duplicate rule name: {rule['name']}")
        rule_names.add(rule["name"])
        unknown = set(rule["jobs"]) - known_jobs
        if unknown:
            errors.append(f"rule {rule['name']}: unknown jobs: {sorted(unknown)}")

    for required in (
        "ci/__init__.py",
        "ci/hdl-ci.json",
        "ci/select_hdl_jobs.py",
        "ci/check_hdl_ci.py",
        "ci/test_select_hdl_jobs.py",
    ):
        if workflow_text.count(f"- '{required}'") != 2:
            errors.append(f"workflow must path-gate {required} for push and pull_request")

    for required_full_path in (".github/workflows/hdl.yml", "ci/hdl-ci.json"):
        if not select_jobs([required_full_path], manifest)["full"]:
            errors.append(f"control path must force full suite: {required_full_path}")

    results_block = job_blocks.get("results", "")
    for job in manifest_jobs | {"changes"}:
        if f"      - {job}" not in results_block:
            errors.append(f"results: missing required dependency: {job}")

    if errors:
        print("HDL CI manifest validation FAILED:")
        for error in errors:
            print(f"- {error}")
        return 1

    print(
        f"HDL CI manifest OK: {len(manifest_jobs)} lanes, "
        f"{sum(len(data['entrypoints']) for data in manifest['jobs'].values())} entrypoints"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
