#!/usr/bin/env python3
"""Generate the fail-closed automatic-versus-external completion audit."""

from __future__ import annotations

import argparse
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "docs" / "automatic-completion-audit.md"
TEMPLATES = {
    "docs/replica-order-upload-runbook.md",
    "docs/replica-parts-inventory-template.md",
    "docs/replica-order-evidence-template.md",
}
UNCHECKED_RE = re.compile(r"^\s*[-*]\s+\[ \]\s+(.+?)\s*$", re.MULTILINE)


@dataclass(frozen=True)
class Evidence:
    path: str
    marker: str
    label: str


@dataclass(frozen=True)
class Group:
    label: str
    reason: str
    required_input: str
    evidence: tuple[Evidence, ...]


GROUPS = {
    "connectivity": Group(
        "P0 physical connectivity and reroute",
        "Remaining endpoints are hidden, contradictory under powered behavior, or continuity-only",
        "owner continuity and powered captures from `docs/owner-measurement-shortlist.md`",
        (
            Evidence("docs/owner-measurement-shortlist.md", "Status: **READY**", "owner/bench packet ready"),
            Evidence("docs/replica-bringup-verification-points.md", "RISKS UNRESOLVED", "source-risk net index unresolved"),
            Evidence("docs/main-board-erc-parity.md", "Status: **DESIGN HOLD**", "release parity gate held"),
        ),
    ),
    "firmware": Group(
        "Independent PROM/EPROM corroboration",
        "Repository donor search, history audit, physical small-PROM reads, and deterministic D15/D16 functional images are exhausted",
        "programming-disk files, independent PROM reads, and repeat physical D15/D16 dumps",
        (
            Evidence("docs/firmware-gap-ledger.md", "TIER-3 CORROBORATION PENDING", "Tier-1/2 burnable set guarded; Tier-3 truth absent"),
            Evidence("docs/cartridge-basic-boundary.md", "ARTIFACT OR DOCUMENTED PROCEDURE REQUIRED", "remaining cartridge artifact boundary explicit"),
        ),
    ),
    "release": Group(
        "Main-board release and order",
        "The verified zero-open package is intentionally held by physical-connectivity and sourcing gates",
        "closed P0 evidence, explicit release, vendor upload, and payment",
        (
            Evidence("docs/replica-manufacturing-readiness.md", "Status: **DESIGN HOLD / PACKAGE VERIFIED**", "package verified under design hold"),
        ),
    ),
    "parts": Group(
        "Functional parts kit",
        "No purchase is authorized and seller stock cannot establish fitted historical truth",
        "procurement choice, purchase, receipt, and physical testing",
        (
            Evidence("docs/replica-sourcing-readiness.md", "Status: **PARTIAL / PROGRAMMING AND REVIEW BLOCKED**", "sourcing gate held"),
        ),
    ),
    "bringup": Group(
        "Tier 1, 2, and 3 bring-up",
        "These milestones require a fabricated and assembled physical replica",
        "board, parts, instruments, staged power-up, and surviving-machine comparison",
        (
            Evidence("docs/replica-manufacturing-readiness.md", "Status: **DESIGN HOLD / PACKAGE VERIFIED**", "no released fabrication package"),
        ),
    ),
    "framebuffer": Group(
        "Physical framebuffer readout",
        "D41/shared-DRAM slot timing, `SHIFT_G`, `TIMING_TAG17`, and `D34_SIG` are not evidence-complete",
        "continuity/drawing closure and captured timing; no guessed serializer schedule",
        (
            Evidence("docs/video-slot-timing-audit.md", "PHYSICAL SLOT SCHEDULE PENDING", "physical video-slot schedule pending"),
            Evidence("docs/crt-cvbs-simulation-plan.md", "shared-DRAM video-slot schedule is evidence-complete", "implementation explicitly evidence-gated"),
        ),
    ),
    "community": Group(
        "juku3000 community exchange",
        "Publishing scope and venue are external-facing decisions",
        "owner approval",
        (
            Evidence("docs/factory-drawing-exploitation-plan.md", "Owner decision on scope and", "external publication is owner-gated"),
        ),
    ),
}


# Keys use the complete first line of each Markdown checkbox. Wrapped
# continuation text remains evidence/context, not task identity.
CLASSIFICATIONS = {
    ("PLAN.md", "P0 physical connectivity is complete and rerouted."): "connectivity",
    ("PLAN.md", "Independent programming files/reads corroborate the four factory PROMs"): "firmware",
    ("PLAN.md", "Main-board design release passes; board is ordered."): "release",
    ("PLAN.md", "Functional parts kit is received and tested."): "parts",
    ("PLAN.md", "Replica completes Tier 1 bring-up."): "bringup",
    ("PLAN.md", "Replica completes Tier 2."): "bringup",
    ("PLAN.md", "Replica completes Tier 3."): "bringup",
    ("docs/crt-cvbs-simulation-plan.md", "Replace the simulation-only framebuffer read port only after the"): "framebuffer",
    ("docs/factory-drawing-exploitation-plan.md", "After Stage 1.2, decide what to share on juku3000 #25 (the MAME"): "community",
}


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def markdown_files() -> list[Path]:
    tracked = subprocess.run(
        ["git", "ls-files", "--", "*.md"],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        check=True,
    ).stdout.splitlines()
    files = []
    for relative in tracked:
        if relative.startswith((".git/", "external/")) or relative in TEMPLATES:
            continue
        files.append(ROOT / relative)
    return sorted(files)


def active_tasks() -> list[tuple[str, str]]:
    tasks: list[tuple[str, str]] = []
    for path in markdown_files():
        tasks.extend((rel(path), task) for task in UNCHECKED_RE.findall(path.read_text(encoding="utf-8")))
    return tasks


def validate(tasks: list[tuple[str, str]]) -> tuple[dict[str, list[tuple[str, str]]], int]:
    unknown = sorted(set(tasks) - set(CLASSIFICATIONS))
    if unknown:
        details = "\n".join(f"  - {path}: {task}" for path, task in unknown)
        raise SystemExit(f"unclassified active unchecked task(s):\n{details}")

    grouped: dict[str, list[tuple[str, str]]] = {}
    for task in tasks:
        grouped.setdefault(CLASSIFICATIONS[task], []).append(task)

    failures: list[str] = []
    for group_name in grouped:
        for item in GROUPS[group_name].evidence:
            path = ROOT / item.path
            if not path.exists() or item.marker not in path.read_text(encoding="utf-8", errors="replace"):
                failures.append(f"{group_name}: missing {item.marker!r} in {item.path}")

    template_count = 0
    for path_name in sorted(TEMPLATES):
        path = ROOT / path_name
        if not path.exists():
            failures.append(f"missing operator template: {path_name}")
            continue
        template_count += len(UNCHECKED_RE.findall(path.read_text(encoding="utf-8")))
    if grouped and template_count != 28:
        failures.append(
            f"operator-template state changed ({template_count} unchecked, expected 28); "
            "reclassify physical/order progress before claiming automatic exhaustion"
        )

    if failures:
        raise SystemExit("automatic-completion evidence check failed:\n  - " + "\n  - ".join(failures))
    return grouped, template_count


def render(tasks: list[tuple[str, str]], grouped: dict[str, list[tuple[str, str]]], template_count: int) -> str:
    plan_count = len({path for path, _ in tasks})
    lines = [
        "# Automatic completion audit",
        "",
        "Status: **AUTOMATIC CHECKLIST EXHAUSTED / EXTERNAL ACTION REQUIRED**",
        "",
        "This generated audit answers a narrow question: whether any tracked project",
        "Markdown outside vendored `external/` material and operator templates contains",
        "an unchecked implementation task that can be completed from repository evidence",
        "and tools. It does not declare the replica complete or release the PCB.",
        "",
        "## Command",
        "",
        "```sh",
        "python3 scripts/report_automatic_completion_audit.py",
        "```",
        "",
        "## Active unchecked work",
        "",
        f"There are {len(tasks)} unchecked items in the active project plans: seven in",
        "`PLAN.md`, one in the CRT/CVBS subordinate plan, and one external community",
        "coordination decision. Every one now requires evidence, hardware, purchasing,",
        "fabrication, or owner authorization.",
        "",
        "| Plan item | Tasks | Why automation must stop | Required next input |",
        "| --- | ---: | --- | --- |",
    ]
    for group_name in GROUPS:
        if group_name not in grouped:
            continue
        group = GROUPS[group_name]
        lines.append(
            f"| {group.label} | {len(grouped[group_name])} | {group.reason} | {group.required_input} |"
        )

    lines += [
        "",
        "## Machine-checked classification",
        "",
        "| Plan | Unchecked task | Class | External-boundary evidence |",
        "| --- | --- | --- | --- |",
    ]
    for path, task in tasks:
        group_name = CLASSIFICATIONS[(path, task)]
        evidence = "; ".join(f"`{item.path}` ({item.label})" for item in GROUPS[group_name].evidence)
        lines.append(f"| `{path}` | {task} | `{group_name}` | {evidence} |")

    lines += [
        "",
        f"The {template_count} unchecked boxes in the order, order-evidence, and parts-inventory",
        "documents are operator templates. They deliberately remain blank until an",
        "authorized physical order/assembly record exists; they are not repository",
        "implementation backlog.",
        "",
        "## Automatically closed scope",
        "",
        "- Source/routed PCB identity, zero-open copper, fabrication-package integrity,",
        "  burnable Tier-1/2 firmware, and runnable HDL/cosim behavior have dedicated",
        "  generated reports and CI guards.",
        "- Firmware reconstruction has consumed every defensible repository donor;",
        "  unresolved physical ROM truth remains unpatched rather than guessed.",
        "- Physical shared-DRAM video timing and analog-output fidelity remain explicitly",
        "  evidence-gated rather than replaced with a simulation convenience path.",
        "",
        "## Guard",
        "",
        f"This writer scanned {plan_count} Markdown file(s) containing active unchecked tasks.",
        "Any new unchecked task outside the three operator templates must have an exact",
        "classification and all cited evidence markers must exist, otherwise generation",
        "fails closed. `scripts/check_documentation_consistency.py` runs this writer in",
        "`--check` mode, and `scripts/regen_all.sh` regenerates the committed report.",
        "",
        "The practical next action is therefore the owner/bench shortlist—not another",
        "inference pass over the same files.",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="fail if the committed report is stale")
    args = parser.parse_args()
    tasks = active_tasks()
    grouped, template_count = validate(tasks)
    output = render(tasks, grouped, template_count)
    if args.check:
        if not REPORT.exists() or REPORT.read_text(encoding="utf-8") != output:
            raise SystemExit("automatic-completion audit is stale; regenerate it")
        print(f"Automatic completion audit is current: {len(tasks)} external task(s), {template_count} template checkbox(es).")
    else:
        REPORT.write_text(output, encoding="utf-8")
        print(f"Wrote {rel(REPORT)}: {len(tasks)} external task(s), {template_count} template checkbox(es)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
