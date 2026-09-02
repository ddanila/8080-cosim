#!/usr/bin/env python3
"""Build guarded, automatically calibrated enhanced candidates for two packs."""

from __future__ import annotations

import argparse
import concurrent.futures
import hashlib
import json
import os
import signal
import subprocess
import sys
import tempfile
import threading
import zipfile
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
SPINOFF = ROOT / "spinoffs" / "jukupoly"
FIRMWARE = SPINOFF / "firmware"
IMPORTER = FIRMWARE / "import_jukupoly_vgz.py"
ARCHIVE_HASHES = {
    "doom1": "04ffbf72e47727b3e93c1e99a68311a460b85fc31fd9a1645e3d872231c0e12a",
    "doom2": "3d255c644e52adc2967df8394086d99d7995da71c4adf83bec0fe3bccc51c365",
}
EXPECTED_TRACKS = {"doom1": 23, "doom2": 21}
CPU_HZ = 1_700_000
INITIAL_FRAME_SAMPLES = 143
INITIAL_SAMPLE_RATE = 7170
ACTIVE_LOCK = threading.Lock()
ACTIVE_PROCESSES: set[subprocess.Popen[str]] = set()
CANCELLED = threading.Event()
sys.path.insert(0, str(FIRMWARE))
sys.path.insert(0, str(SPINOFF / "tools"))

import build_jukupoly as build  # noqa: E402
import report_jukupoly_baseline as baseline  # noqa: E402
import report_jukupoly_envelope as envelope_report  # noqa: E402


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def extract(pack: str, archive: Path, destination: Path) -> list[dict]:
    result = []
    with zipfile.ZipFile(archive) as source:
        names = sorted(
            name for name in source.namelist()
            if Path(name).suffix.lower() == ".vgz" and "/" not in name
        )
        if len(names) != EXPECTED_TRACKS[pack]:
            raise ValueError(
                f"{archive.name}: expected {EXPECTED_TRACKS[pack]} tracks, "
                f"found {len(names)}"
            )
        for local_track, name in enumerate(names, 1):
            path = destination / f"{pack}-{local_track:02d}.vgz"
            path.write_bytes(source.read(name))
            result.append({
                "pack": pack,
                "local_track": local_track,
                "label": f"{pack}-{local_track:02d}",
                "source_name": name,
                "path": path,
            })
    return result


def convert(item: dict, score: Path, oracle: Path, frame_samples: int,
            sample_rate: int) -> str:
    command = [
        sys.executable, str(IMPORTER), str(item["path"]), str(score),
        "--enhanced-envelopes", "--enhanced-rearticulation",
        "--enhanced-target-envelope-shape", "--enhanced-detuned-layers",
        "--enhanced-frame-samples", str(frame_samples),
        "--enhanced-sample-rate", str(sample_rate),
        "--opl-oracle", str(oracle),
    ]
    if CANCELLED.is_set():
        raise RuntimeError("pack build cancelled")
    process = subprocess.Popen(
        command, cwd=ROOT, text=True, stdout=subprocess.PIPE,
        start_new_session=True,
    )
    with ACTIVE_LOCK:
        ACTIVE_PROCESSES.add(process)
    try:
        stdout, _stderr = process.communicate()
    finally:
        with ACTIVE_LOCK:
            ACTIVE_PROCESSES.discard(process)
    if process.returncode:
        raise subprocess.CalledProcessError(
            process.returncode, command, output=stdout,
        )
    return stdout.strip()


def cancel_processes(_signal: int, _frame: object) -> None:
    CANCELLED.set()
    with ACTIVE_LOCK:
        processes = tuple(ACTIVE_PROCESSES)
    for process in processes:
        try:
            os.killpg(process.pid, signal.SIGTERM)
        except ProcessLookupError:
            pass
    raise KeyboardInterrupt


def compile_payload(score_path: Path) -> tuple[bytes | None, dict, str | None]:
    score = json.loads(score_path.read_text())
    try:
        generated, metadata = build.compile_song(score)
        return build.assemble_song_file(generated, metadata), score, None
    except ValueError as exc:
        return None, score, str(exc)


def reusable_score(path: Path, item: dict, frame_samples: int,
                   sample_rate: int) -> bool:
    if not path.is_file():
        return False
    try:
        score = json.loads(path.read_text())
        conversion = score["conversion"]
        return (
            score.get("schema") == "jukupoly-song-v2" and
            score.get("frame_samples") == frame_samples and
            score.get("sample_rate_hz") == sample_rate and
            score["source"]["compressed_sha256"] == sha256(item["path"]) and
            not conversion["melodic_signature_overrides"] and
            conversion["voice_selection_policy"] ==
            "sustaining-note continuity before newly articulated notes" and
            "enhanced_detuned_layers" in conversion
        )
    except (KeyError, OSError, ValueError, json.JSONDecodeError):
        return False


def choose_timing(profile: dict) -> tuple[int, int, list[dict]]:
    old_samples = profile["frame_samples"]
    old_cycles = CPU_HZ / profile["music_frame_hz"]
    loop_cycles = profile["sample_loop_cycles"]["mean"]
    choices = []
    for frame_samples in range(129, 144):
        cycles = old_cycles + (frame_samples - old_samples) * loop_cycles
        frame_hz = CPU_HZ / cycles
        choices.append({
            "frame_samples": frame_samples,
            "predicted_music_frame_hz": frame_hz,
            "predicted_sample_rate_hz": frame_samples * frame_hz,
        })
    selected = min(
        choices,
        key=lambda item: (
            abs(item["predicted_music_frame_hz"] - 50.0),
            -item["predicted_sample_rate_hz"],
        ),
    )
    return (
        selected["frame_samples"],
        round(selected["predicted_sample_rate_hz"]),
        choices,
    )


def quality(score: dict) -> dict:
    conversion = score["conversion"]
    fit = conversion["enhanced_envelope_fit"]
    allocation = conversion["enhanced_allocation"]
    notes = fit["notes"]
    detuned = fit["detuned_layer_analysis"]
    return {
        "no_song_specific_melodic_overrides":
            not conversion["melodic_signature_overrides"],
        "generic_continuity_allocator": conversion["voice_selection_policy"] ==
            "sustaining-note continuity before newly articulated notes",
        "no_protected_onset_regression":
            allocation["missed_protected_onsets"] == 0,
        "no_unrepresentable_rearticulations":
            fit["unrepresentable_rearticulation_notes"] == 0,
        "all_logical_notes_within_two_level_mean_error": all(
            note["mean_absolute_error"] <= fit["delivery_note_mae_limit"]
            for note in notes
        ),
        "all_significant_envelope_directions_match":
            fit["direction_mismatches"] == 0,
        "detuned_member_mean_error_below_one_level":
            detuned["member_sample_weighted_mean_absolute_error"] <= 1.0,
    }


def timing_quality(profile: dict, score: dict, floor: float) -> dict:
    source_seconds = score["conversion"]["source_duration_seconds"]
    return {
        "sample_rate_above_shared_floor":
            profile["effective_sample_hz"] >= floor,
        "music_clock_within_one_percent":
            abs(profile["music_frame_hz"] - 50.0) <= 0.5,
        "phase_table_within_one_percent": abs(
            profile["effective_sample_hz"] - score["sample_rate_hz"]
        ) <= profile["effective_sample_hz"] * 0.01,
        "duration_within_one_percent": abs(
            profile["duration_seconds"] - source_seconds
        ) <= source_seconds * 0.01,
        "escape_polling_present":
            profile["keyboard_polls"] >= profile["frames"],
    }


def profile_song(profiler: Path, player: Path, symbols: dict[str, int],
                 song: Path, label: str) -> dict:
    return envelope_report.enhanced_profile(
        profiler, player, song, symbols, label,
    )


def main() -> int:
    signal.signal(signal.SIGINT, cancel_processes)
    signal.signal(signal.SIGTERM, cancel_processes)
    parser = argparse.ArgumentParser()
    parser.add_argument("--doom", type=Path, required=True)
    parser.add_argument("--doom2", type=Path, required=True)
    parser.add_argument("--opl-oracle", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--jobs", type=int, default=8)
    args = parser.parse_args()
    if not 1 <= args.jobs <= 12:
        parser.error("--jobs must be 1..12")
    archives = {"doom1": args.doom.resolve(), "doom2": args.doom2.resolve()}
    for pack, archive in archives.items():
        if not archive.is_file() or sha256(archive) != ARCHIVE_HASHES[pack]:
            parser.error(f"missing or hash-mismatched archive: {archive}")
    oracle = args.opl_oracle.resolve()
    if not oracle.is_file():
        parser.error(f"OPL oracle is missing: {oracle}")

    output = args.output_dir.resolve()
    sources = output / "sources"
    initial_scores = output / "initial-scores"
    final_scores = output / "scores"
    payloads = output / "payloads"
    for directory in (sources, initial_scores, final_scores, payloads):
        directory.mkdir(parents=True, exist_ok=True)
    items = []
    for pack, archive in archives.items():
        items.extend(extract(pack, archive, sources))

    pending_initial = [
        item for item in items
        if not reusable_score(
            initial_scores / f"{item['label']}.json", item,
            INITIAL_FRAME_SAMPLES, INITIAL_SAMPLE_RATE,
        )
    ]
    print(
        f"JUKUPOLY-GENERIC-PACK: reuse-initial="
        f"{len(items) - len(pending_initial)} pending={len(pending_initial)}",
        flush=True,
    )
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.jobs) as executor:
        futures = {
            executor.submit(
                convert, item, initial_scores / f"{item['label']}.json",
                oracle, INITIAL_FRAME_SAMPLES, INITIAL_SAMPLE_RATE,
            ): item for item in pending_initial
        }
        for future in concurrent.futures.as_completed(futures):
            item = futures[future]
            print(
                f"JUKUPOLY-GENERIC-PACK: initial {item['label']} "
                f"{future.result()}", flush=True,
            )

    floor = json.loads((SPINOFF / "OPL-ENVELOPE-M3.json").read_text())[
        "v2_sample_rate_floor_hz"
    ]
    initial: dict[str, dict] = {}
    with tempfile.TemporaryDirectory(prefix="jukupoly-generic-profile.") as name:
        temporary = Path(name)
        profiler, _renderer = baseline.build_tools(temporary)
        player, symbols = envelope_report.build_enhanced_player(temporary)
        player_record = {
            "bytes": player.stat().st_size,
            "sha256": sha256(player),
        }
        for item in items:
            score_path = initial_scores / f"{item['label']}.json"
            payload, score, size_error = compile_payload(score_path)
            entry = {"score": score, "payload": payload, "size_error": size_error}
            if payload is not None:
                song = temporary / f"{item['label']}-initial.jps"
                song.write_bytes(payload)
                profile = profile_song(
                    profiler, player, symbols, song, item["label"] + "-initial",
                )
                frame_samples, sample_rate, choices = choose_timing(profile)
                entry.update({
                    "profile": profile,
                    "frame_samples": frame_samples,
                    "sample_rate": sample_rate,
                    "timing_choices": choices,
                    "timing_gates": timing_quality(profile, score, floor),
                })
            initial[item["label"]] = entry

        convertible = [
            item for item in items
            if initial[item["label"]]["payload"] is not None and
            all(quality(initial[item["label"]]["score"]).values())
        ]
        needs_calibration = [
            item for item in convertible
            if not all(initial[item["label"]]["timing_gates"].values())
        ]
        pending_final = [
            item for item in convertible
            if item in needs_calibration
            if not reusable_score(
                final_scores / f"{item['label']}.json", item,
                initial[item["label"]]["frame_samples"],
                initial[item["label"]]["sample_rate"],
            )
        ]
        print(
            f"JUKUPOLY-GENERIC-PACK: early-qualified={len(convertible)} "
            f"initial-timing-qualified="
            f"{len(convertible) - len(needs_calibration)} "
            f"reuse-calibrated={len(needs_calibration) - len(pending_final)} "
            f"pending={len(pending_final)}",
            flush=True,
        )
        with concurrent.futures.ThreadPoolExecutor(
                max_workers=args.jobs) as executor:
            futures = {
                executor.submit(
                    convert, item, final_scores / f"{item['label']}.json",
                    oracle, initial[item["label"]]["frame_samples"],
                    initial[item["label"]]["sample_rate"],
                ): item for item in pending_final
            }
            for future in concurrent.futures.as_completed(futures):
                item = futures[future]
                print(
                    f"JUKUPOLY-GENERIC-PACK: calibrated {item['label']} "
                    f"{future.result()}", flush=True,
                )

        records = []
        replacements = []
        fallback_counts: Counter[str] = Counter()
        for item in items:
            first = initial[item["label"]]
            initial_quality = quality(first["score"])
            if first["payload"] is None or not all(initial_quality.values()):
                gates = dict(initial_quality)
                gates["jps_below_hard_limit"] = first["payload"] is not None
                fallback_reasons = [
                    name for name, passed in gates.items() if not passed
                ]
                final_profile = None
                payload = None
                score = first["score"]
                size_error = first["size_error"]
            elif all(first["timing_gates"].values()):
                payload = first["payload"]
                score = first["score"]
                size_error = None
                final_profile = first["profile"]
                gates = {**initial_quality, **first["timing_gates"]}
                fallback_reasons = []
            else:
                score_path = final_scores / f"{item['label']}.json"
                payload, score, size_error = compile_payload(score_path)
                quality_gates = quality(score)
                gates = dict(quality_gates)
                gates["jps_below_hard_limit"] = payload is not None
                final_profile = None
                if payload is not None:
                    song = temporary / f"{item['label']}-final.jps"
                    song.write_bytes(payload)
                    final_profile = profile_song(
                        profiler, player, symbols, song, item["label"] + "-final",
                    )
                    gates.update(timing_quality(final_profile, score, floor))
                fallback_reasons = [name for name, passed in gates.items()
                                    if not passed]
            accepted = not fallback_reasons
            if accepted:
                payload_path = payloads / f"{item['label']}.jps"
                assert payload is not None
                payload_path.write_bytes(payload)
                replacement = {
                    "pack": item["pack"],
                    "local_track": item["local_track"],
                    "source_name": item["source_name"],
                    "payload": payload_path.name,
                    "bytes": len(payload),
                    "sha256": sha256(payload_path),
                    "capability": payload[7],
                }
                replacements.append(replacement)
            else:
                fallback_counts.update(fallback_reasons)
            fit = score["conversion"]["enhanced_envelope_fit"]
            records.append({
                "label": item["label"],
                "pack": item["pack"],
                "local_track": item["local_track"],
                "source_name": item["source_name"],
                "source_sha256": sha256(item["path"]),
                "delivery": "enhanced" if accepted else "generic-v1-fallback",
                "fallback_reasons": fallback_reasons,
                "initial_timing": {
                    "frame_samples": INITIAL_FRAME_SAMPLES,
                    "sample_rate_hz": INITIAL_SAMPLE_RATE,
                    "profile": first.get("profile"),
                    "choices": first.get("timing_choices"),
                },
                "calibrated_timing": {
                    "frame_samples": score["frame_samples"],
                    "sample_rate_hz": score["sample_rate_hz"],
                    "profile": final_profile,
                },
                "candidate": {
                    "bytes": None if payload is None else len(payload),
                    "sha256": None if payload is None else hashlib.sha256(
                        payload
                    ).hexdigest(),
                    "size_error": size_error,
                    "logical_notes": fit["selected_logical_notes"],
                    "extra_detuned_voices": fit[
                        "detuned_layer_analysis"
                    ]["extra_voices"],
                    "rearticulation_packets": fit["rearticulation"][
                        "emitted_packets"
                    ],
                    "mean_error": fit["sample_weighted_mean_absolute_error"],
                    "member_mean_error": fit[
                        "detuned_layer_analysis"
                    ]["member_sample_weighted_mean_absolute_error"],
                },
                "gates": gates,
            })

    replacement_manifest = {
        "schema": "jukupoly-library-replacements-v1",
        "tracks": replacements,
    }
    replacement_path = output / "replacement-manifest.json"
    replacement_path.write_text(
        json.dumps(replacement_manifest, indent=2, sort_keys=True) + "\n"
    )
    report = {
        "schema": "jukupoly-generic-enhanced-pack-v1",
        "status": (
            "every source received one shared enhanced policy and measured "
            "timing calibration; failed common guards use generic v1"
        ),
        "archives": {
            pack: {"name": path.name, "sha256": sha256(path),
                   "tracks": EXPECTED_TRACKS[pack]}
            for pack, path in archives.items()
        },
        "policy": {
            "enhancements": [
                "fitted envelopes", "bounded re-articulation",
                "target envelope-shape selection", "detuned spare layers",
            ],
            "song_specific_overrides": [],
            "timing": (
                "measure the complete initial candidate, predict every "
                "129..143 sample batch, choose closest to 50 Hz, and rebuild "
                "source-aware phase steps at the predicted effective rate"
            ),
            "fallback": "generic v1 on any common quality, size, or timing failure",
        },
        "player": {
            **player_record,
            "shared_sample_rate_floor_hz": floor,
        },
        "summary": {
            "tracks": len(records),
            "enhanced": len(replacements),
            "generic_v1_fallback": len(records) - len(replacements),
            "fallback_gate_counts": dict(sorted(fallback_counts.items())),
        },
        "tracks": records,
    }
    args.report.resolve().write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n"
    )
    print(
        f"JUKUPOLY-GENERIC-PACK: PASS tracks={len(records)} "
        f"enhanced={len(replacements)} fallback={len(records)-len(replacements)} "
        f"manifest={replacement_path}",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
