#!/usr/bin/env python3
"""Guard and render the temporary clean-checkout CRT decoder baseline record."""
from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "ref" / "video" / "decoder-fork-baseline.json"
PLAN_PATH = ROOT / "docs" / "crt-cvbs-simulation-plan.md"
REPORT_PATH = ROOT / "docs" / "crt-decoder-baseline.md"
EXPECTED_FORK = "https://github.com/ddanila/famicom-rf-hackrf-decoder"
EXPECTED_UPSTREAM = "https://github.com/GOROman/famicom-rf-hackrf-decoder"
EXPECTED_COMMIT = "6cce72d4a0e35ed364d086470191d61e3f6cd116"


def row(values: list[Any]) -> str:
    return "| " + " | ".join(str(value).replace("|", "/") for value in values) + " |"


def main() -> int:
    data = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    plan = PLAN_PATH.read_text(encoding="utf-8")
    decoder = data["decoder"]
    results = data["results"]
    synth = results["synth_ntsc"]
    context_commit = data["8080_cosim_context_commit"]
    context_exists = subprocess.run(
        ["git", "cat-file", "-e", f"{context_commit}^{{commit}}"],
        cwd=ROOT,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    ).returncode == 0
    checks = [
        (
            "Fork URL and fork point match the CVBS plan",
            decoder["fork_url"] == EXPECTED_FORK
            and decoder["upstream_url"] == EXPECTED_UPSTREAM
            and decoder["commit"] == EXPECTED_COMMIT
            and all(item in plan for item in (EXPECTED_FORK, EXPECTED_UPSTREAM, EXPECTED_COMMIT)),
            "fork, upstream, and 40-hex commit are identical in plan and record",
        ),
        (
            "The 8080-cosim context commit exists",
            len(context_commit) == 40 and context_exists,
            context_commit,
        ),
        (
            "Decoder source stayed unmodified",
            decoder["checkout_mode"] == "detached clean checkout"
            and decoder["source_tree_clean_after_tests"] is True,
            "temporary detached checkout remained clean after build and test",
        ),
        (
            "Full fork build passed",
            results["cmake_configure"] == "pass"
            and results["full_build"] == "pass"
            and set(results["built_targets"]) == {"fam_dsp", "famidec", "synth_ntsc"},
            "CMake configured and built fam_dsp, famidec, and synth_ntsc",
        ),
        (
            "Upstream CTest passed",
            results["ctest"]["passed"] == 1 and results["ctest"]["failed"] == 0,
            "1/1 synth_ntsc test passed",
        ),
        (
            "Direct synthetic NTSC result is internally complete",
            synth["status"] == "pass"
            and synth["decoded_frames"] >= 10
            and synth["bars_passed"] == synth["bars_total"] == 7,
            f"{synth['decoded_frames']} frames; {synth['bars_passed']}/{synth['bars_total']} bars",
        ),
        (
            "Temporary dependencies did not mutate host package state",
            data["host"]["dependency_setup"].startswith("No host packages installed."),
            "development packages were extracted only below /tmp",
        ),
    ]
    ok = all(result for _, result, _ in checks)
    status = "UPSTREAM BASELINE REPRODUCED / FORK README AND CI PENDING" if ok else "DECODER BASELINE RECORD FAILED"
    lines = [
        "# CRT decoder fork baseline",
        "",
        f"Status date: **{data['recorded_at']}**.",
        "",
        f"Status: **{status}**.",
        "",
        "This generated report records CVBS-plan WP0 work performed in a temporary,",
        "detached checkout. It proves that the recorded unmodified decoder fork point",
        "builds and passes its upstream synthetic NTSC regression on the named host.",
        "It makes no Juku baseband, X7, receiver-lock, or hardware claim.",
        "",
        "## Command",
        "",
        "```sh",
        "python3 scripts/report_crt_decoder_baseline.py",
        "```",
        "",
        "## Provenance checks",
        "",
        "| Check | Result | Evidence |",
        "| --- | --- | --- |",
    ]
    lines.extend(row([name, "PASS" if result else "FAIL", evidence]) for name, result, evidence in checks)
    lines.extend([
        "",
        "## Recorded environment",
        "",
        row(["Item", "Value"]),
        row(["---", "---"]),
        row(["Decoder fork", decoder["fork_url"]]),
        row(["Upstream", decoder["upstream_url"]]),
        row(["Decoder commit", f"`{decoder['commit']}`"]),
        row(["8080-cosim context", f"`{context_commit}`"]),
        row(["Host", data["host"]["os"]]),
        row(["CMake", data["host"]["cmake"]]),
        row(["Compiler", data["host"]["compiler"]]),
        row(["Dependency isolation", data["host"]["dependency_setup"]]),
        "",
        "## Results",
        "",
        "| Test | Result | Time | Max RSS |",
        "| --- | --- | ---: | ---: |",
        row([
            "CTest",
            f"{results['ctest']['passed']}/1 passed",
            f"{results['ctest']['elapsed_seconds']:.2f} s",
            f"{results['ctest']['max_rss_kib']} KiB",
        ]),
        row([
            "direct synth_ntsc",
            f"{synth['decoded_frames']} frames; {synth['decoded_lines']} lines; {synth['bars_passed']}/{synth['bars_total']} bars",
            f"{synth['elapsed_seconds']:.2f} s",
            f"{synth['max_rss_kib']} KiB",
        ]),
        "",
        "The direct run reported 87 coasted lines and still recovered all seven",
        "golden color bars within the upstream tolerance.",
        "",
        "## Compiler warnings",
        "",
    ])
    lines.extend(f"- {warning}" for warning in data["build_warnings"])
    lines.extend([
        "",
        "These HUD-format warnings do not affect `synth_ntsc`, but they should be",
        "resolved in the decoder fork before treating GCC 15 warnings as a clean CI",
        "baseline.",
        "",
        "## Remaining WP0 work",
        "",
    ])
    lines.extend(f"- {item}" for item in data["scope"]["not_proved"])
    lines.extend([
        "",
        "The fork's README provenance and CI are intentionally not changed from this",
        "repository. Those are separate-repository writes and remain pending.",
        "",
    ])
    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {REPORT_PATH.relative_to(ROOT)}")
    print(f"Status: {status}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
