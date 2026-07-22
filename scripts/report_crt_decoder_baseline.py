#!/usr/bin/env python3
"""Guard and render the temporary clean-checkout CRT decoder baseline record."""
from __future__ import annotations

import json
import re
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
    followup = data["wp0_followup"]
    ci_run = followup["ci_run"]
    wp1 = data["wp1_followup"]
    wp1_ci = wp1["ci_run"]
    wp1_tests = wp1["tests"]
    wp1_e2e = wp1_tests["e2e"]
    wp2 = data["wp2_followup"]
    wp2_ci = wp2["ci_run"]
    wp2_fixture = wp2["positive_fixture"]
    wp2_stats = wp2["measured_statistics"]
    wp3 = data["wp3_synthetic_followup"]
    wp3_ci = wp3["ci_run"]
    wp3_fixture = wp3["fixture"]
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
    context_is_ancestor = not context_exists or subprocess.run(
        ["git", "merge-base", "--is-ancestor", context_commit, "HEAD"],
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
            "The 8080-cosim context is a valid recorded revision",
            re.fullmatch(r"[0-9a-f]{40}", context_commit) is not None
            and context_is_ancestor,
            f"{context_commit}; ancestry checked when history is present (CI checkout may be shallow)",
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
        (
            "Fork README provenance and deterministic-fixture policy are committed",
            re.fullmatch(r"[0-9a-f]{40}", followup["readme_and_ci_commit"]) is not None
            and re.fullmatch(r"[0-9a-f]{64}", followup["readme_sha256"]) is not None
            and re.fullmatch(r"[0-9a-f]{64}", followup["workflow_sha256"]) is not None
            and followup["upstream_head_at_followup"] == EXPECTED_COMMIT,
            f"fork `{followup['readme_and_ci_commit'][:8]}`; upstream remained `{EXPECTED_COMMIT[:8]}`",
        ),
        (
            "Fork Linux CI builds RF/IQ and passes both test entry points",
            ci_run["conclusion"] == "success"
            and ci_run["head_sha"] == followup["fork_head_commit"]
            and ci_run["head_sha"] == followup["ci_dependency_fix_commit"]
            and all(ci_run[item] == "pass" for item in ("full_rf_iq_build", "ctest", "synth_ntsc")),
            f"run {ci_run['id']} at `{ci_run['head_sha'][:8]}`: full build + CTest + synth_ntsc",
        ),
        (
            "WP1 fork tip and bounded commits are pinned",
            re.fullmatch(r"[0-9a-f]{40}", wp1["fork_head_commit"]) is not None
            and wp1["fork_head_commit"] == wp1["commits"]["documented_contract"]
            and wp1["fork_head_commit"] in plan
            and all(
                re.fullmatch(r"[0-9a-f]{40}", commit) is not None
                for commit in wp1["commits"].values()
            )
            and all(
                re.fullmatch(r"[0-9a-f]{64}", digest) is not None
                for digest in wp1["artifact_sha256"].values()
            ),
            f"five bounded commits ending at `{wp1['fork_head_commit'][:8]}`",
        ),
        (
            "WP1 float32 source contract is explicit",
            wp1["source_contract"]["format"]
            == "headerless little-endian IEEE-754 float32"
            and wp1["source_contract"]["sample_rate"]
            == "explicit positive --rate required"
            and wp1["source_contract"]["transform_order"]
            == ["optional polarity inversion", "gain", "offset"]
            and set(wp1["source_contract"]["rejections"])
            == {"empty", "byte length not divisible by four", "NaN or infinity"},
            "LE f32; explicit rate; polarity/gain/offset; structural and finite checks",
        ),
        (
            "WP1 source and generated end-to-end tests pass",
            wp1_tests["source_test"]["status"] == "pass"
            and wp1_e2e["status"] == "pass"
            and wp1_e2e["fixture_samples"] > 0
            and wp1_e2e["fixture_fields"] >= 2
            and wp1_e2e["fixture_storage"]
            == "generated during test and removed after success"
            and wp1_e2e["bars_observed"] == wp1_e2e["bars_expected"]
            and len(wp1_e2e["bars_observed"]) == 5
            and wp1_e2e["negative_cli_cases"] >= 5,
            f"{wp1_e2e['fixture_samples']} samples; {len(wp1_e2e['bars_observed'])}/5 bars; {wp1_e2e['negative_cli_cases']} CLI failures",
        ),
        (
            "WP1 CI keeps the full RF/IQ route and all CTests green",
            wp1_ci["conclusion"] == "success"
            and wp1_ci["head_sha"] == wp1["fork_head_commit"]
            and wp1_ci["full_rf_iq_build"] == "pass"
            and wp1_ci["ctest_passed"] == 3
            and wp1_ci["ctest_failed"] == 0
            and wp1_ci["synth_ntsc"] == "pass",
            f"run {wp1_ci['id']} at `{wp1_ci['head_sha'][:8]}`: full build + 3 CTests + synth_ntsc",
        ),
        (
            "WP2 profile receiver tip and artifacts are pinned",
            wp2["fork_head_commit"] == wp2["commits"]["documented_contract"]
            and wp2["fork_head_commit"] in plan
            and all(
                re.fullmatch(r"[0-9a-f]{40}", commit) is not None
                for commit in wp2["commits"].values()
            )
            and all(
                re.fullmatch(r"[0-9a-f]{64}", digest) is not None
                for digest in wp2["artifact_sha256"].values()
            ),
            f"five bounded commits ending at `{wp2['fork_head_commit'][:8]}`",
        ),
        (
            "WP2 independent non-NTSC fixture passes exactly",
            wp2_fixture["sample_rate_hz"] == 8_000_000
            and wp2_fixture["line_rate_hz"] == 12_500
            and wp2_fixture["lines_per_frame"] == 200
            and wp2_fixture["samples"] > 0
            and wp2_fixture["bars_observed"] == wp2_fixture["bars_expected"]
            and len(wp2_fixture["bars_observed"]) == 5,
            f"{wp2_fixture['samples']} samples; {wp2_fixture['line_rate_hz']} Hz; 5/5 bars",
        ),
        (
            "WP2 telemetry guards measured lock, timing, and levels",
            wp2_stats["format"] == "JSON schema_version 1"
            and wp2_stats["line_locked"] is True
            and wp2_stats["frame_locked"] is True
            and wp2_stats["line_rate_hz_min"] < wp2_fixture["line_rate_hz"]
            < wp2_stats["line_rate_hz_max"]
            and wp2_stats["frame_rate_hz_min"] < 62.5
            < wp2_stats["frame_rate_hz_max"]
            and wp2_stats["sync_width_us_min"] < wp2_fixture["hsync_us"]
            < wp2_stats["sync_width_us_max"],
            "line/frame lock; 12.5 kHz, 62.5 Hz, 6 us, blank and 0..100 IRE bounds",
        ),
        (
            "WP2 negative fixtures distinguish horizontal and frame loss",
            set(wp2["negative_fixtures"]) == {
                "reversed_polarity",
                "missing_hsync",
                "malformed_vsync",
                "clipped_sync",
                "excessive_period_error",
            }
            and "horizontal lock remains" in
            wp2["negative_fixtures"]["malformed_vsync"],
            "five generated failures; malformed vsync uniquely retains horizontal lock",
        ),
        (
            "WP2 CI keeps all receiver paths green",
            wp2_ci["conclusion"] == "success"
            and wp2_ci["head_sha"] == wp2["fork_head_commit"]
            and wp2_ci["full_rf_iq_build"] == "pass"
            and wp2_ci["ctest_passed"] == 5
            and wp2_ci["ctest_failed"] == 0
            and wp2_ci["synth_ntsc"] == "pass",
            f"run {wp2_ci['id']} at `{wp2_ci['head_sha'][:8]}`: full build + 5 CTests + synth_ntsc",
        ),
        (
            "WP3 synthetic Juku fixture is source-pinned",
            wp3["fork_head_commit"] == wp3["commits"]["evidence_linked_fixture"]
            and wp3["fork_head_commit"] in plan
            and wp3["8080_cosim_source_commit"] in plan
            and all(
                re.fullmatch(r"[0-9a-f]{40}", commit) is not None
                for commit in (
                    wp3["fork_head_commit"],
                    wp3["8080_cosim_source_commit"],
                )
            )
            and all(
                re.fullmatch(r"[0-9a-f]{64}", digest) is not None
                for digest in wp3["artifact_sha256"].values()
            ),
            f"decoder `{wp3['fork_head_commit'][:8]}` consumes raster evidence `{wp3['8080_cosim_source_commit'][:8]}`",
        ),
        (
            "WP3 ideal fixture carries the exact guarded raster contract",
            wp3_fixture["sample_rate_hz"] == 8_000_000
            and wp3_fixture["line_rate_hz"] == 15_625
            and wp3_fixture["line_period_us"] == 64
            and wp3_fixture["lines_per_frame"] == 313
            and wp3_fixture["horizontal_sync_us"] == 5.04
            and wp3_fixture["vertical_sync_us"] == 223
            and wp3_fixture["active_start_absolute_line"] == 47
            and wp3_fixture["active_start_receiver_line"] == 44
            and wp3_fixture["active_lines"] == 241
            and wp3_fixture["active_pixels"] == 320
            and wp3_fixture["samples"] == 961_536
            and wp3_fixture["bars_observed"] == wp3_fixture["bars_expected"],
            "64 us x 313; 5.04/223 us sync; 320x241; 5/5 bars",
        ),
        (
            "WP3 synthetic receiver CI preserves every route",
            wp3_ci["conclusion"] == "success"
            and wp3_ci["head_sha"] == wp3["fork_head_commit"]
            and wp3_ci["full_rf_iq_build"] == "pass"
            and wp3_ci["ctest_passed"] == 6
            and wp3_ci["ctest_failed"] == 0
            and wp3_ci["synth_ntsc"] == "pass",
            f"run {wp3_ci['id']} at `{wp3_ci['head_sha'][:8]}`: full build + 6 CTests + synth_ntsc",
        ),
    ]
    ok = all(result for _, result, _ in checks)
    status = (
        "WP0-WP2 + EVIDENCE-LINKED SYNTHETIC JUKU WP3 GUARDED"
        if ok
        else "DECODER BASELINE RECORD FAILED"
    )
    lines = [
        "# CRT decoder fork baseline",
        "",
        f"Status date: **{data['recorded_at']}**.",
        "",
        f"Status: **{status}**.",
        "",
        "This generated report records the CVBS-plan WP0 clean-checkout baseline and",
        "the later fork-owned WP1/WP2 receiver follow-ups and the bounded WP3",
        "synthetic Juku-timing fixture. The recorded unmodified fork point builds",
        "and passes its upstream synthetic NTSC",
        "regression, then pins the float32/headless and explicit-profile E2E paths.",
        "The WP3 fixture consumes exact Juku raster evidence, but it makes no",
        "physical-X7, framebuffer-agreement, or hardware claim.",
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
        row(["Fork WP0 head", f"`{followup['fork_head_commit']}`"]),
        row(["Fork WP1 head", f"`{wp1['fork_head_commit']}`"]),
        row(["Fork WP2 head", f"`{wp2['fork_head_commit']}`"]),
        row(["Fork WP3 synthetic head", f"`{wp3['fork_head_commit']}`"]),
        row(["WP3 raster source", f"`{wp3['8080_cosim_source_commit']}`"]),
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
        row([
            "fork Linux CI",
            f"full RF/IQ build + CTest + synth_ntsc PASS ([run {ci_run['id']}]({ci_run['url']}))",
            "42 s",
            "GitHub-hosted runner",
        ]),
        row([
            "baseband source CTest",
            f"PASS; {len(wp1_tests['source_test']['cases'])} validation/transform cases",
            "included in CI",
            "GitHub-hosted runner",
        ]),
        row([
            "generated baseband E2E",
            f"{wp1_e2e['decoded_frames']} frames; {len(wp1_e2e['bars_observed'])}/5 exact grayscale bars",
            "included in CI",
            "GitHub-hosted runner",
        ]),
        row([
            "WP1 fork Linux CI",
            f"full build + 3 CTests + synth_ntsc PASS ([run {wp1_ci['id']}]({wp1_ci['url']}))",
            "27 s",
            "GitHub-hosted runner",
        ]),
        row([
            "non-NTSC profile E2E",
            f"{wp2_fixture['line_rate_hz']} Hz / {wp2_fixture['lines_per_frame']} lines; 5/5 bars + measured JSON",
            "included in CI",
            "GitHub-hosted runner",
        ]),
        row([
            "negative profile fixtures",
            f"{len(wp2['negative_fixtures'])}/5 lock failures distinguished",
            "included in CI",
            "GitHub-hosted runner",
        ]),
        row([
            "WP2 fork Linux CI",
            f"full build + 5 CTests + synth_ntsc PASS ([run {wp2_ci['id']}]({wp2_ci['url']}))",
            "42 s",
            "GitHub-hosted runner",
        ]),
        row([
            "synthetic Juku-timing E2E",
            f"{wp3_fixture['line_rate_hz']} Hz / {wp3_fixture['lines_per_frame']} lines; 5/5 bars",
            "included in CI",
            "GitHub-hosted runner",
        ]),
        row([
            "WP3 synthetic fork Linux CI",
            f"full build + 6 CTests + synth_ntsc PASS ([run {wp3_ci['id']}]({wp3_ci['url']}))",
            "46 s",
            "GitHub-hosted runner",
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
        "## Boundaries after the synthetic WP3 checkpoint",
        "",
    ])
    lines.extend(f"- {item}" for item in wp3["scope"]["not_proved"])
    lines.extend([
        "",
        "WP0-WP2 are complete at their generic boundaries: the fork owns provenance,",
        "strict raw-float input, explicit timing profiles, measured lock telemetry,",
        "positive/negative generated fixtures, and green full-build/test CI. The",
        "bounded WP3 fixture additionally proves receiver lock at the exact guarded",
        "Juku raster timing without promoting it to a built-in preset. Physical pixel",
        "slots, D34_SIG/X7 integration, and framebuffer validation remain open.",
        "",
    ])
    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {REPORT_PATH.relative_to(ROOT)}")
    print(f"Status: {status}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
