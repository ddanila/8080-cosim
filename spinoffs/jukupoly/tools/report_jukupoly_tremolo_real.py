#!/usr/bin/env python3
"""Measure a real old/new JPS v2 tremolo excerpt and render target WAVs."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import sys
import tempfile
from pathlib import Path

import report_jukupoly_baseline as baseline
import report_jukupoly_tremolo_target as target_report


ROOT = Path(__file__).resolve().parents[3]
SPINOFF = ROOT / "spinoffs" / "jukupoly"
FIRMWARE = SPINOFF / "firmware"
DEFAULT_SCORE = FIRMWARE / "jukupoly-opening-66s-tremolo-m4.json"
DEFAULT_REPORT = SPINOFF / "OPL-TREMOLO-REAL-M4.json"
sys.path.insert(0, str(FIRMWARE))

import build_jukupoly as build  # noqa: E402


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def envelope_only_score(score: dict) -> tuple[dict, int]:
    """Reverse emitted joint fits to their recorded envelope-only baselines."""
    result = copy.deepcopy(score)
    fit = result["conversion"]["enhanced_envelope_fit"]
    measurements = fit["emitted_notes"]
    by_frame: dict[int, list[dict]] = {}
    for item in measurements:
        by_frame.setdefault(item["selected_frame"], []).append(item)

    replacements = 0
    frame = 0
    for row in result["rows"]:
        for channel in ("tone1", "tone2", "tone3"):
            event = row.get(channel)
            if not isinstance(event, dict) or not event.get(
                    "opl_tremolo_depth"):
                continue
            candidates = [
                item for item in by_frame.get(frame, [])
                if item["packet"] == event.get("opl_envelope") and
                item["tremolo_analysis"]["emitted_depth_levels"] ==
                event["opl_tremolo_depth"]
            ]
            if len(candidates) != 1:
                raise ValueError(
                    f"cannot uniquely reverse tremolo event at frame {frame}"
                )
            event["opl_envelope"] = candidates[0]["baseline_packet"]
            del event["opl_tremolo_depth"]
            replacements += 1
        frame += row["frames"]
    if replacements != len(measurements):
        raise ValueError(
            f"reversed {replacements} events, expected {len(measurements)}"
        )
    result["title"] = result["title"].replace(
        "envelope+tremolo", "envelope-only comparison",
    )
    result["arrangement"] = (
        "Same allocation and target timing as the M4 experiment, with each "
        "emitted joint fit restored to its recorded envelope-only baseline"
    )
    result["notes"] = (
        "Controlled M4 comparison: identical rows and frame batch, with "
        "tremolo disabled and baseline fitted envelopes restored."
    )
    fit["tremolo_analysis"] = dict(fit["tremolo_analysis"])
    fit["tremolo_analysis"]["enabled"] = False
    fit["tremolo_analysis"]["emitted_notes"] = 0
    return result, replacements


def build_score(directory: Path, label: str, score: dict
                ) -> tuple[Path, Path, dict]:
    generated, metadata = build.compile_song(score)
    standalone = directory / f"{label}.com"
    song = directory / f"{label}.jps"
    standalone.write_bytes(build.assemble(
        generated, metadata["mod_effects"], metadata["enhanced_envelopes"],
        metadata["enhanced_tremolo"],
    ))
    song.write_bytes(build.assemble_song_file(generated, metadata))
    return standalone, song, metadata


def first_tremolo_frame(score: dict) -> int | None:
    frame = 0
    for row in score["rows"]:
        if any(
            isinstance(row.get(channel), dict) and
            row[channel].get("opl_tremolo_depth", 0) > 0
            for channel in ("tone1", "tone2", "tone3")
        ):
            return frame
        frame += row["frames"]
    return None


def generate(score_path: Path, output_dir: Path | None,
             oracle_reference: Path | None) -> dict:
    score = json.loads(score_path.read_text())
    if score.get("schema") != "jukupoly-song-v2":
        raise ValueError("real tremolo fixture must use jukupoly-song-v2")
    if oracle_reference is not None and not oracle_reference.is_file():
        raise ValueError(f"oracle reference is missing: {oracle_reference}")
    old_score, replacements = envelope_only_score(score)
    fit = score["conversion"]["enhanced_envelope_fit"]
    emitted = fit["emitted_notes"]
    source_seconds = score["conversion"]["duration_seconds"]

    with tempfile.TemporaryDirectory(prefix="jukupoly-tremolo-real.") as name:
        directory = Path(name)
        profiler, renderer = baseline.build_tools(directory)
        player, symbols = target_report.build_player(directory, tremolo=True)
        old_com, old_jps, old_metadata = build_score(
            directory, "envelope", old_score,
        )
        new_com, new_jps, new_metadata = build_score(
            directory, "tremolo", score,
        )

        def profile(song: Path, label: str) -> dict:
            return json.loads(baseline.run([
                str(profiler), str(player), str(song),
                f"{symbols['player_start']:x}", label,
                f"{symbols['envelope_dispatch_init']:x}",
            ]))

        profiles = {
            "envelope": profile(old_jps, "opening-66s-envelope"),
            "tremolo": profile(new_jps, "opening-66s-tremolo"),
        }
        player_bytes = player.read_bytes()
        old_jps_payload = old_jps.read_bytes()
        new_jps_payload = new_jps.read_bytes()

        render_directory = output_dir if output_dir is not None else directory
        render_directory.mkdir(parents=True, exist_ok=True)
        wavs = {}
        for label, image in (("envelope", old_com), ("tremolo", new_com)):
            wav = render_directory / f"opening-66s-{label}.wav"
            baseline.run([
                str(renderer), "--sample-rate", "48000", "--lead", "0",
                "--tail", "0", str(image), str(wav),
            ])
            wavs[label] = {
                "path_hint": wav.name,
                "sample_rate_hz": 48_000,
                "bytes": wav.stat().st_size,
                "sha256": sha256(wav),
            }

    loop_start = symbols["sample_loop"] - baseline.COM_ADDRESS
    loop_end = symbols["frame_tick"] - baseline.COM_ADDRESS
    loop_hash = hashlib.sha256(
        player_bytes[loop_start:loop_end]
    ).hexdigest()
    old_profile = profiles["envelope"]
    new_profile = profiles["tremolo"]
    floor = old_profile["effective_sample_hz"] * 0.9
    gates = {
        "generic_emitted_candidates_exist": len(emitted) > 0,
        "every_emitted_note_has_direct_quantized_benefit": all(
            item["tremolo_analysis"]["directly_audible_am_path"] and
            item["tremolo_analysis"]["source_changed_frames_4bit"] > 0 and
            item["tremolo_analysis"]["squared_error_improvement"] > 0 and
            item["tremolo_analysis"]["emitted_depth_levels"] > 0
            for item in emitted
        ),
        "known_candidate_100_retained": any(
            item["logical_note"] == 100 for item in emitted
        ),
        "directions_preserved": fit["direction_mismatches"] == 0,
        "comparison_reverses_every_emitted_note": replacements == len(emitted),
        "capabilities_are_01_and_03": (
            old_jps_payload[7] == build.JPS2_ENVELOPE_CAPABILITY and
            new_jps_payload[7] == (
                build.JPS2_ENVELOPE_CAPABILITY |
                build.JPS2_TREMOLO_CAPABILITY
            )
        ),
        "zero_packet_and_jps_growth": len(old_jps_payload) == len(new_jps_payload),
        "sample_loop_hash_exact": (
            loop_hash == json.loads(
                (SPINOFF / "OPL-BASELINE.json").read_text()
            )["player"]["sample_loop_sha256"]
        ),
        "new_sample_rate_above_comparison_floor": (
            new_profile["effective_sample_hz"] >= floor
        ),
        "phase_table_rate_matches_measured_within_one_percent": (
            abs(new_profile["effective_sample_hz"] -
                score["sample_rate_hz"]) <=
            new_profile["effective_sample_hz"] * 0.01
        ),
        "both_music_clocks_within_one_percent": all(
            abs(profile["music_frame_hz"] - 50.0) <= 0.5
            for profile in profiles.values()
        ),
        "both_durations_within_one_percent": all(
            abs(profile["duration_seconds"] - source_seconds) <=
            source_seconds * 0.01
            for profile in profiles.values()
        ),
        "new_jps_below_soft_limit": len(new_jps_payload) < 30 * 1024,
        "player_below_song_window": (
            baseline.COM_ADDRESS + len(player_bytes) < baseline.SONG_ADDRESS
        ),
        "target_wavs_differ": wavs["envelope"]["sha256"] != wavs["tremolo"]["sha256"],
    }
    if not all(gates.values()):
        failed = ", ".join(key for key, value in gates.items() if not value)
        measurements = ", ".join(
            f"{key}:sample={profile['effective_sample_hz']:.3f},"
            f"music={profile['music_frame_hz']:.6f},"
            f"duration={profile['duration_seconds']:.6f}"
            for key, profile in profiles.items()
        )
        raise RuntimeError(
            "real tremolo gate failure: " + failed + " (" +
            measurements + ")"
        )

    reference = None if oracle_reference is None else {
        "path_hint": oracle_reference.name,
        "bytes": oracle_reference.stat().st_size,
        "sha256": sha256(oracle_reference),
    }
    return {
        "schema": "jukupoly-opl-tremolo-real-m4-report-v1",
        "status": "C-cosim and render gates pass; physical A/B pending",
        "source": {
            "score": score_path.name,
            "score_sha256": sha256(score_path),
            "name": score["source"]["name"],
            "vgm_sha256": score["source"]["vgm_sha256"],
            "seconds": source_seconds,
        },
        "policy": {
            "selected_logical_notes": fit["selected_logical_notes"],
            "semantic_candidates": fit["tremolo_analysis"]["semantic_candidates"],
            "emitted_notes": len(emitted),
            "first_tremolo_frame": first_tremolo_frame(score),
            "maximum_depth_levels": max(
                item["tremolo_analysis"]["emitted_depth_levels"]
                for item in emitted
            ),
            "total_source_changed_frames_4bit": sum(
                item["tremolo_analysis"]["source_changed_frames_4bit"]
                for item in emitted
            ),
            "total_squared_error_improvement": sum(
                item["tremolo_analysis"]["squared_error_improvement"]
                for item in emitted
            ),
            "logical_notes": [item["logical_note"] for item in emitted],
        },
        "format": {
            "envelope_capability": old_jps_payload[7],
            "tremolo_capability": new_jps_payload[7],
            "envelope_jps_bytes": len(old_jps_payload),
            "tremolo_jps_bytes": len(new_jps_payload),
            "frame_samples": new_metadata["frame_samples"],
            "phase_table_hz": new_metadata["target_sample_hz"],
        },
        "player": {
            "bytes": len(player_bytes),
            "end_address_exclusive": hex(
                baseline.COM_ADDRESS + len(player_bytes)
            ),
            "sample_loop_sha256": loop_hash,
        },
        "profiles": profiles,
        "comparison_sample_rate_floor_hz": floor,
        "target_wavs": wavs,
        "opl_reference_wav": reference,
        "gates": gates,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--score", type=Path, default=DEFAULT_SCORE)
    parser.add_argument("--output", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--oracle-reference", type=Path)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    try:
        result = generate(args.score, args.output_dir, args.oracle_reference)
    except (OSError, ValueError, RuntimeError) as exc:
        parser.error(str(exc))
    if args.check:
        if args.oracle_reference is not None:
            parser.error("--check uses the committed oracle reference hash")
        committed = json.loads(args.output.read_text())
        result["opl_reference_wav"] = committed["opl_reference_wav"]
    rendered = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.check:
        if args.output.read_text() != rendered:
            raise SystemExit(f"{args.output} is missing or stale")
        action = "checked"
    else:
        args.output.write_text(rendered)
        action = "wrote"
    profile = result["profiles"]["tremolo"]
    print(
        f"JUKUPOLY-TREMOLO-REAL: {action} {args.output} "
        f"notes={result['policy']['emitted_notes']} "
        f"jps={result['format']['tremolo_jps_bytes']} "
        f"sample={profile['effective_sample_hz']:.1f}Hz "
        f"music={profile['music_frame_hz']:.3f}Hz "
        f"duration={profile['duration_seconds']:.3f}s"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
