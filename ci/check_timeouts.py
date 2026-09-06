#!/usr/bin/env python3
"""Enforce literal time budgets in this repo's block-style Actions workflows.

Uses the same dependency-free job-block reader as the HDL manifest validator;
this is a repository formatting contract, not a general YAML parser.
"""

from __future__ import annotations

import re
from pathlib import Path

from ci.check_hdl_ci import workflow_block_by_job

ROOT = Path(__file__).resolve().parents[1]


def check_workflow(text: str) -> list[str]:
    errors = []
    jobs = workflow_block_by_job(text)
    if not jobs:
        return ["no block-style jobs found"]
    for job, block in jobs.items():
        # Measured ~7m chip-level two-clock boot; retain its full assertions.
        step_limit = 8 if job == "revb-ttl-boot" else 5
        budget = re.findall(r"^    timeout-minutes: (\d+)\s*$", block, re.M)
        if len(budget) != 1 or not 1 <= int(budget[0]) <= 10:
            errors.append(f"{job}: requires a literal job timeout of 1..10 minutes")
        for number, step in enumerate(re.split(r"^      - ", block, flags=re.M)[1:], 1):
            if not re.search(r"^(?:        )?run:", step, re.M):
                continue
            budget = re.findall(r"^        timeout-minutes: (\d+)\s*$", step, re.M)
            if len(budget) != 1 or not 1 <= int(budget[0]) <= step_limit:
                errors.append(f"{job} step {number}: requires a shell timeout of 1..{step_limit} minutes")
    return errors


def main() -> int:
    errors = []
    for path in sorted((ROOT / ".github/workflows").glob("*.y*ml")):
        errors.extend(f"{path.name}: {error}" for error in check_workflow(path.read_text()))
    if errors:
        print("\n".join(errors))
        return 1
    print("CI time budgets: PASS (jobs <=10 min; shell steps <=5 min, TTL boot <=8 min)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
