#!/usr/bin/env python3
"""Keep HDL report writers, freshness checks, and deep regeneration aligned."""

from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HDL_WORKFLOW = ROOT / ".github" / "workflows" / "hdl.yml"
REGEN = ROOT / "scripts" / "regen_all.sh"

# Each command below rewrites committed evidence during hdl.yml. Its output
# must be checked by a git-diff freshness assertion and the same writer must be
# reachable through regen_all.sh --deep. This explicit contract is deliberately
# small and dependency-free so generic CI can catch list drift before the
# expensive HDL job runs.
WRITERS: dict[str, tuple[str, ...]] = {
    "./sync/ekdos_fdc_probe.py": ("docs/ekdos-fdc-probe.md",),
    "./sync/ekdos_jbasic_command_probe.py": ("docs/ekdos-jbasic-command-probe.md",),
    "./sync/ekdos_timing_reference.py": (
        "docs/ekdos-timing-reference.md",
        "sync/ekdos_timing_expected.json",
    ),
    "python3 scripts/report_juku_top_fdc_alignment.py": ("docs/juku-top-fdc-alignment.md",),
    "./sync/ekdos_checkpoint_reference.py": ("docs/ekdos-checkpoint-reference.md",),
    "./sync/ekdos_ioseq_reference.py": ("docs/ekdos-ioseq-reference.md",),
    "./sync/juku_top_checkpoint_load_check.py": ("docs/juku-top-checkpoint-load.md",),
    "./sync/juku_top_checkpoint_resume_probe.py": ("docs/juku-top-checkpoint-resume.md",),
    "./sync/fdc_check.sh": ("docs/fdc-readiness.md",),
    "./sync/basic_cart_check.sh": ("docs/basic-cart-readiness.md",),
    "./sync/d2_ready_path_check.sh": ("docs/d2-ready-path-check.md",),
    "python3 scripts/report_d6_runtime_path.py": ("docs/d6-runtime-path-diagnostic.md",),
    "./sync/beeper_check.sh": ("docs/beeper-readiness.md",),
    "./sync/serial_check.sh": ("docs/serial-handoff.md",),
    "./sync/ie7_check.sh": ("docs/ie7-counter-readiness.md",),
    "./sync/d96_check.sh": ("docs/d96-read-clock-readiness.md",),
    "./sync/ie10_check.sh": ("docs/ie10-counter-readiness.md",),
    "./sync/ag3_check.sh": ("docs/ag3-oneshot-readiness.md",),
    "./sync/juku_top_periph_bus_check.sh": ("docs/juku-top-periph-bus-check.md",),
    "./sync/jmon33_hdl_probe.sh": ("docs/jmon33-hdl-probe.md",),
    "./sync/jmon33_interrupt_probe.py": ("docs/jmon33-interrupt-probe.md",),
    "./sync/jmon33_ready_probe.py": ("docs/jmon33-ready-probe.md",),
    "./sync/jmon33_command_probe.py": ("docs/jmon33-command-probe.md",),
    "./sync/jmon33_idle_command_probe.py": ("docs/jmon33-idle-command-probe.md",),
    "./sync/ir16_check.sh": ("docs/ir16-readiness.md",),
    "./sync/kp14_check.sh": ("docs/kp14-readiness.md",),
    "./sync/video_timing_check.sh": ("docs/video-timing-reference.md",),
    "./sync/video_readout_check.sh": ("docs/video-readout-readiness.md",),
    "python3 scripts/report_video_physical_probes.py": ("docs/video-physical-probes.md",),
    "python3 scripts/report_video_pit_timing.py": ("docs/video-pit-timing.md",),
}


def diff_checked_paths(workflow: str) -> set[str]:
    """Return paths named by git diff --exit-code freshness commands."""
    checked: set[str] = set()
    lines = workflow.splitlines()
    for index, line in enumerate(lines):
        if "git diff --exit-code --" not in line:
            continue
        while True:
            checked.update(re.findall(r"(?:docs|ref|sync)/[A-Za-z0-9_.-]+", line))
            if not line.rstrip().endswith("\\"):
                break
            index += 1
            if index >= len(lines):
                break
            line = lines[index]
    return checked


def main() -> int:
    workflow = HDL_WORKFLOW.read_text(encoding="utf-8")
    regen = REGEN.read_text(encoding="utf-8")
    checked = diff_checked_paths(workflow)
    workflow_commands = {line.strip() for line in workflow.splitlines()}
    regen_commands = {line.strip() for line in regen.splitlines()}
    errors: list[str] = []

    for command, outputs in WRITERS.items():
        if command not in workflow_commands:
            errors.append(f"HDL workflow does not run writer: {command}")
        if f"run {command}" not in regen_commands:
            errors.append(f"regen_all.sh --deep does not run writer: {command}")
        for output in outputs:
            if output not in checked:
                errors.append(f"HDL workflow does not freshness-check {output} (writer: {command})")

    if errors:
        raise SystemExit("generated-report coverage mismatch:\n  - " + "\n  - ".join(errors))

    print(f"Generated-report coverage is aligned: {len(WRITERS)} writers, {sum(map(len, WRITERS.values()))} artifacts.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
