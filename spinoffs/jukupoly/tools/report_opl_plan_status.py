#!/usr/bin/env python3
"""Cross-check the committed OPL reduction plan evidence and open gate."""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
SPINOFF = ROOT / "spinoffs" / "jukupoly"
FIRMWARE = SPINOFF / "firmware"
DEFAULT_REPORT = SPINOFF / "OPL-PLAN-STATUS.json"


def load(name: str) -> dict:
    return json.loads((SPINOFF / name).read_text())


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def digest(value: object) -> str:
    return hashlib.sha256(json.dumps(
        value, sort_keys=True, separators=(",", ":"), allow_nan=False,
    ).encode()).hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def all_true(record: dict, context: str) -> None:
    failed = sorted(key for key, value in record.items() if value is not True)
    require(not failed, f"{context} gates failed: {', '.join(failed)}")


def player(report: dict) -> dict:
    for key in ("player", "enhanced_player", "experimental_player"):
        if key in report:
            return report[key]
    raise ValueError("report has no player record")


def no_track_literals(paths: list[Path]) -> bool:
    forbidden = {
        "The Imp's Song", "Nobody Told Me About id", "Dark Halls",
        "Suspense", "At Doom's Gate", "Opening to Hell",
    }
    for path in paths:
        tree = ast.parse(path.read_text(), filename=str(path))
        strings = {
            node.value for node in ast.walk(tree)
            if isinstance(node, ast.Constant) and isinstance(node.value, str)
        }
        if forbidden & strings:
            return False
    return True


def evidence(name: str) -> dict:
    path = SPINOFF / name
    return {"path": name, "sha256": sha256(path)}


def generate() -> dict:
    baseline = load("OPL-BASELINE.json")
    envelope = load("OPL-ENVELOPE-M3.json")
    imp = load("OPL-IMP-M3.json")
    tremolo_target = load("OPL-TREMOLO-TARGET-M4.json")
    tremolo_full = load("OPL-TREMOLO-FULL-M4.json")
    vibrato_full = load("OPL-VIBRATO-FULL-M5.json")
    mixed = load("OPL-M6-MIXED-LIBRARY.json")
    pack_scan = load("OPL-M7-PACK-SCAN.json")
    modes = load("OPL-M7-MODES.json")
    detuned_spares = load("OPL-M7-DETUNED-SPARES.json")
    detuned_full = load("OPL-IMP-DETUNED-FULL-M7.json")
    nobody = load("OPL-NOBODY-REARTICULATION-M7.json")
    attack_pcm = load("OPL-M7-ATTACK-PCM.json")
    physical_ab = load("OPL-IMP-M7-PHYSICAL-AB.json")
    physical_result_path = (
        SPINOFF / "sessions" / "cs00000-jukupoly-m6-physical" / "result.txt"
    )
    physical_result = physical_result_path.read_text()

    require(baseline["schema"] == "jukupoly-opl-baseline-v1",
            "wrong baseline schema")
    expected_loop = baseline["player"]["sample_loop_sha256"]
    loop_reports = (
        envelope, tremolo_target, tremolo_full, vibrato_full, mixed,
        detuned_full,
    )
    loop_hashes = [player(item)["sample_loop_sha256"] for item in loop_reports]
    require(all(item == expected_loop for item in loop_hashes),
            "a committed feature report changed the frozen sample loop")

    all_true(envelope["gates"], "M3 target")
    all_true(tremolo_target["gates"], "M4 target")
    all_true(tremolo_full["gates"], "M4 full track")
    all_true(vibrato_full["gates"], "M5 full track")
    all_true(mixed["aggregate_gates"], "M6 mixed library")
    all_true(detuned_full["gates"], "M7 detuned full track")

    require(imp["delivery"] == {
        "enhanced_candidate_qualified": False,
        "qualified": True,
        "reason": (
            "one compact ADSR cannot represent renewed keyed rises whose "
            "per-note mean error exceeds the two-level delivery limit"
        ),
        "strategy": "unchanged-v1-fit-fallback",
    }, "M3 Imp fallback changed")
    require(nobody["delivery"]["strategy"] == "unchanged-v1-fit-fallback",
            "rejected Nobody candidate no longer uses its v1 fallback")

    players = [baseline["player"], *(player(item) for item in loop_reports)]
    maximum_player_end = max(
        int(item["end_address_exclusive"], 16) for item in players
    )
    require(maximum_player_end < 0x1800, "a player reaches the song window")
    maximum_mixed_jps = max(track["jps_bytes"] for track in mixed["tracks"])
    require(maximum_mixed_jps < 32_768, "a delivered mixed-library JPS is too large")
    require(detuned_full["jps"]["v2"]["bytes"] < 30 * 1024,
            "the M7 detuned candidate exceeds the soft JPS ceiling")

    require(modes["totals"] == {
        "four_operator_enabled_samples": 0,
        "four_operator_tracks": 0,
        "hardware_rhythm_tracks": 0,
        "opl3_tracks": 44,
        "rhythm_enabled_samples": 0,
        "tracks": 44,
    }, "M7 unsupported-mode pack evidence changed")
    require(detuned_spares["totals"]["tracks"] == 44 and
            detuned_spares["totals"]["missed_protected_onsets"] == 0,
            "M7 detuned opportunity audit is incomplete")
    require(attack_pcm["tracks"] == 44 and
            attack_pcm["missed_protected_onsets"] == 0,
            "M7 attack-PCM audit is incomplete")
    require(pack_scan["summary"]["tracks"] == 44,
            "M7 re-articulation scan is incomplete")

    production_paths = [
        FIRMWARE / "opl_enhanced.py", FIRMWARE / "opl_envelope.py",
        FIRMWARE / "opl_tremolo.py", FIRMWARE / "opl_vibrato.py",
    ]
    require(no_track_literals(production_paths),
            "enhanced production reducer contains a track-title literal")

    capabilities = [track["capability"] for track in mixed["tracks"]]
    require(capabilities.count(3) == 3 and capabilities.count(5) == 1,
            "M6 enhanced capability distribution changed")
    require("02 passed subjective listening" in physical_result and
            "04 and 06 were acceptable/inconclusive" in physical_result and
            "03 failed subjective enhanced-fit qualification" in physical_result,
            "M6 physical result boundary is missing or changed")
    require(physical_ab["disk"]["cpm_round_trip_verified"] is True,
            "M7 physical A/B disk has no CP/M round-trip evidence")
    require([item["strategy"] for item in physical_ab["files"]] == [
        "unchanged-v1", "bounded-rearticulation", "detuned-source-members",
    ], "M7 physical A/B order changed")

    guards = [
        {
            "id": "G0", "status": "pass",
            "finding": "baseline cycle, memory, rate, and WAV evidence locked",
            "evidence": ["OPL-BASELINE.json"],
        },
        {
            "id": "G1", "status": "pass",
            "finding": f"all feature reports retain frozen loop {expected_loop}",
            "evidence": [
                "OPL-ENVELOPE-M3.json", "OPL-TREMOLO-TARGET-M4.json",
                "OPL-VIBRATO-FULL-M5.json", "OPL-M6-MIXED-LIBRARY.json",
                "OPL-IMP-DETUNED-FULL-M7.json",
            ],
        },
        {
            "id": "G2", "status": "pass",
            "finding": "delivered and M7 candidate full-track rate/timing gates pass",
            "evidence": [
                "OPL-TREMOLO-FULL-M4.json", "OPL-VIBRATO-FULL-M5.json",
                "OPL-M6-MIXED-LIBRARY.json", "OPL-IMP-DETUNED-FULL-M7.json",
            ],
        },
        {
            "id": "G3", "status": "physical-pending",
            "finding": (
                "percussion and Escape remain measured; M7 iteration change "
                "still requires the prepared physical A/B"
            ),
            "evidence": [
                "OPL-IMP-DETUNED-FULL-M7.json",
                "OPL-IMP-M7-PHYSICAL-AB.json",
            ],
        },
        {
            "id": "G4", "status": "pass",
            "finding": (
                f"largest player ends at {maximum_player_end:#06x}, below 0x1800"
            ),
            "evidence": ["OPL-M6-MIXED-LIBRARY.json"],
        },
        {
            "id": "G5", "status": "pass-with-fallbacks",
            "finding": (
                f"largest delivered JPS is {maximum_mixed_jps} bytes; oversized "
                "or poor-quality candidates retain v1"
            ),
            "evidence": [
                "OPL-M6-MIXED-LIBRARY.json",
                "OPL-NOBODY-REARTICULATION-M7.json",
            ],
        },
        {
            "id": "G6", "status": "pass",
            "finding": "all 44 mixed JPS1/JPS2 payloads complete C-cosim",
            "evidence": ["OPL-ENVELOPE-M3.json", "OPL-M6-MIXED-LIBRARY.json"],
        },
        {
            "id": "G7", "status": "pass",
            "finding": (
                "44-track audits complete and enhanced reducers contain no "
                "track-title string literal"
            ),
            "evidence": [
                "OPL-M7-PACK-SCAN.json", "OPL-M7-MODES.json",
                "OPL-M7-DETUNED-SPARES.json", "OPL-M7-ATTACK-PCM.json",
            ],
        },
        {
            "id": "G8", "status": "physical-pending",
            "finding": (
                "M3 fallback and delivered M4/M5/M6 payloads have physical "
                "evidence; the M7 Imp candidate does not"
            ),
            "evidence": [
                "sessions/cs00000-jukupoly-m6-physical/result.txt",
                "OPL-IMP-M7-PHYSICAL-AB.json",
            ],
        },
    ]
    milestones = [
        {"id": "M0", "status": "complete", "finding": "reproducible baseline"},
        {"id": "M1", "status": "complete", "finding": "pinned oracle and register model"},
        {"id": "M2", "status": "complete", "finding": "inspectable logical voices and allocation"},
        {
            "id": "M3", "status": "qualified-fallback",
            "finding": "enhanced Imp failed physically; unchanged v1 is delivered",
        },
        {
            "id": "M4", "status": "physical-evidence-acceptable-inconclusive",
            "finding": (
                "three capability-03 tracks delivered; Dark Halls and "
                "Suspense were assessed acceptable but difficult to judge"
            ),
        },
        {
            "id": "M5", "status": "physically-qualified",
            "finding": "complete capability-05 At Doom's Gate passed physical listening",
        },
        {
            "id": "M6", "status": "qualified-progressive",
            "finding": "44 tracks: four enhanced and 40 explicit v1 fallbacks",
        },
        {
            "id": "M7", "status": "physical-pending",
            "finding": (
                "full detuned Imp passes offline; modes and attack PCM have "
                "documented no-demand/capacity fallbacks"
            ),
        },
    ]
    evidence_names = sorted({
        name for guard in guards for name in guard["evidence"]
        if not name.startswith("sessions/")
    })
    result = {
        "schema": "jukupoly-opl-plan-status-v1",
        "plan": evidence("OPL-REDUCTION-PLAN.md"),
        "guards": guards,
        "milestones": milestones,
        "automated_status": "pass",
        "overall_status": "physical-qualification-pending",
        "remaining_required_actions": [{
            "id": "M7-IMP-PHYSICAL-AB",
            "action": (
                "boot the hash-locked comparison disk on CS00000, run IMPV1, "
                "IMPREAR, and IMPDET at one volume, record sound assessment, "
                "Escape behavior, and CP/M return"
            ),
            "prepared_evidence": "OPL-IMP-M7-PHYSICAL-AB.json",
            "requires_external_state": "powered physical CS00000 and operator",
        }],
        "evidence": [evidence(name) for name in evidence_names] + [{
            "path": str(physical_result_path.relative_to(SPINOFF)),
            "sha256": sha256(physical_result_path),
        }],
        "derived": {
            "frozen_sample_loop_sha256": expected_loop,
            "maximum_player_end_exclusive": hex(maximum_player_end),
            "maximum_delivered_jps_bytes": maximum_mixed_jps,
            "mixed_capabilities": {
                "00": capabilities.count(0),
                "03": capabilities.count(3),
                "05": capabilities.count(5),
            },
        },
    }
    result["report_sha256"] = digest(result)
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    try:
        result = generate()
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
        parser.error(str(exc))
    rendered = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.check:
        if args.output.read_text() != rendered:
            raise SystemExit(f"{args.output} is missing or stale")
        action = "checked"
    else:
        args.output.write_text(rendered)
        action = "wrote"
    print(
        f"JUKUPOLY-OPL-PLAN: {action} {args.output} "
        f"automated={result['automated_status']} "
        f"overall={result['overall_status']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
