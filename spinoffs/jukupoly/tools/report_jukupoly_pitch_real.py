#!/usr/bin/env python3
"""Qualify host-baked held-note pitch packets on a complete OPL track."""

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
DEFAULT_SCORE = FIRMWARE / "jukupoly-doomgate-held-pitch-m5.json"
DEFAULT_REPORT = SPINOFF / "OPL-PITCH-REAL-M5.json"
sys.path.insert(0, str(FIRMWARE))

import build_jukupoly as build  # noqa: E402


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _append_row(rows: list[dict], row: dict) -> None:
    """Append a row while merging only representable adjacent waits."""
    if (set(row) == {"frames"} and rows and
            set(rows[-1]) == {"frames"} and
            rows[-1]["frames"] + row["frames"] <= 255):
        rows[-1]["frames"] += row["frames"]
    else:
        rows.append(row)


def fixed_pitch_control(score: dict) -> tuple[dict, int]:
    """Remove only held-key legato packets, preserving every onset packet."""
    result = copy.deepcopy(score)
    rows = []
    removed = 0
    for source_row in result["rows"]:
        row = dict(source_row)
        for channel in ("tone1", "tone2", "tone3"):
            event = row.get(channel)
            if isinstance(event, dict) and event.get("legato") is True:
                del row[channel]
                removed += 1
        _append_row(rows, row)
    result["rows"] = rows
    result["title"] = result["title"].replace(
        "held-pitch", "fixed-pitch comparison",
    )
    result["arrangement"] = (
        "Controlled M5 comparison retaining the same allocation, onset "
        "phase steps, envelopes, percussion, sample batch, and target player, "
        "but removing every held-key legato pitch update"
    )
    result["notes"] = (
        "Controlled M5 comparison: only held-key legato tone packets are "
        "removed; source duration and all note-on packets are unchanged."
    )
    held = result["conversion"]["enhanced_held_pitch"]
    held["enabled"] = False
    held["emitted_legato_packets"] = 0
    return result, removed


def build_score(directory: Path, label: str, score: dict
                ) -> tuple[Path, Path, dict]:
    generated, metadata = build.compile_song(score)
    standalone = directory / f"{label}.com"
    song = directory / f"{label}.jps"
    standalone.write_bytes(build.assemble(
        generated, metadata["mod_effects"], metadata["enhanced_envelopes"],
        metadata["enhanced_tremolo"], metadata["enhanced_vibrato"],
    ))
    song.write_bytes(build.assemble_song_file(generated, metadata))
    return standalone, song, metadata


def count_legato_packets(score: dict) -> int:
    return sum(
        isinstance(row.get(channel), dict) and
        row[channel].get("legato") is True
        for row in score["rows"]
        for channel in ("tone1", "tone2", "tone3")
    )


def generate(score_path: Path, output_dir: Path | None) -> dict:
    score = json.loads(score_path.read_text())
    if score.get("schema") != "jukupoly-song-v2":
        raise ValueError("held-pitch fixture must use jukupoly-song-v2")
    held = score.get("conversion", {}).get("enhanced_held_pitch", {})
    if not held.get("enabled"):
        raise ValueError("held-pitch fixture does not enable held pitch")
    emitted = count_legato_packets(score)
    if emitted != held.get("emitted_legato_packets"):
        raise ValueError("held-pitch packet count disagrees with metadata")
    control, removed = fixed_pitch_control(score)
    source_seconds = score["conversion"].get(
        "source_duration_seconds", score["conversion"]["duration_seconds"],
    )
    artifact_stem = f"doomgate-{round(source_seconds)}s"

    with tempfile.TemporaryDirectory(prefix="jukupoly-pitch-real.") as name:
        directory = Path(name)
        profiler, renderer = baseline.build_tools(directory)
        player, symbols = target_report.build_player(directory, tremolo=False)
        control_com, control_jps, control_metadata = build_score(
            directory, "fixed-pitch", control,
        )
        held_com, held_jps, held_metadata = build_score(
            directory, "held-pitch", score,
        )

        def profile(song: Path, label: str) -> dict:
            return json.loads(baseline.run([
                str(profiler), str(player), str(song),
                f"{symbols['player_start']:x}", label,
                f"{symbols['envelope_dispatch_init']:x}",
            ]))

        profiles = {
            "fixed_pitch": profile(
                control_jps, f"{artifact_stem}-fixed-pitch",
            ),
            "held_pitch": profile(
                held_jps, f"{artifact_stem}-held-pitch",
            ),
        }
        player_bytes = player.read_bytes()
        control_payload = control_jps.read_bytes()
        held_payload = held_jps.read_bytes()

        render_directory = output_dir if output_dir is not None else directory
        render_directory.mkdir(parents=True, exist_ok=True)
        wavs = {}
        for label, image in (
                ("fixed_pitch", control_com), ("held_pitch", held_com)):
            wav = render_directory / f"{artifact_stem}-{label}.wav"
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
    frozen = json.loads((SPINOFF / "OPL-BASELINE.json").read_text())
    envelope = json.loads((SPINOFF / "OPL-ENVELOPE-M3.json").read_text())
    floor = envelope["v2_sample_rate_floor_hz"]
    held_profile = profiles["held_pitch"]
    control_profile = profiles["fixed_pitch"]
    gates = {
        "generic_held_pitch_packets_exist": emitted > 0,
        "comparison_removes_every_held_pitch_packet": removed == emitted,
        "comparison_preserves_total_frames": (
            sum(row["frames"] for row in control["rows"]) ==
            sum(row["frames"] for row in score["rows"])
        ),
        "both_capabilities_remain_01": (
            control_payload[7] == build.JPS2_ENVELOPE_CAPABILITY and
            held_payload[7] == build.JPS2_ENVELOPE_CAPABILITY
        ),
        "no_new_target_player": len(player_bytes) == envelope[
            "enhanced_player"
        ]["bytes"],
        "sample_loop_hash_exact": (
            loop_hash == frozen["player"]["sample_loop_sha256"]
        ),
        "held_sample_rate_above_combined_floor": (
            held_profile["effective_sample_hz"] >= floor
        ),
        "held_sample_rate_above_90_percent_of_control": (
            held_profile["effective_sample_hz"] >=
            control_profile["effective_sample_hz"] * 0.9
        ),
        "phase_table_rate_matches_measured_within_one_percent": (
            abs(held_profile["effective_sample_hz"] -
                score["sample_rate_hz"]) <=
            held_profile["effective_sample_hz"] * 0.01
        ),
        "phase_steps_generated_for_declared_rate": (
            held.get("phase_step_generation_hz") == score["sample_rate_hz"]
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
        "held_jps_below_soft_limit": len(held_payload) < 30 * 1024,
        "player_below_song_window": (
            baseline.COM_ADDRESS + len(player_bytes) < baseline.SONG_ADDRESS
        ),
        "target_wavs_differ": (
            wavs["fixed_pitch"]["sha256"] != wavs["held_pitch"]["sha256"]
        ),
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
            "real held-pitch gate failure: " + failed + " (" +
            measurements + ")"
        )

    allocation = score["conversion"]["enhanced_allocation"]
    fit = score["conversion"]["enhanced_envelope_fit"]
    return {
        "schema": "jukupoly-opl-pitch-real-m5-report-v1",
        "status": (
            "host-baked held-pitch C-cosim and render gates pass; "
            "physical A/B pending"
        ),
        "source": {
            "score": score_path.name,
            "score_sha256": sha256(score_path),
            "name": score["source"]["name"],
            "vgm_sha256": score["source"]["vgm_sha256"],
            "seconds": source_seconds,
        },
        "policy": {
            "emitted_legato_packets": emitted,
            "source_onsets": allocation["source_onsets"],
            "protected_onsets": allocation["protected_onsets"],
            "retained_onsets": allocation["retained_onsets"],
            "gained_onsets": allocation["gained_onsets"],
            "missed_protected_onsets": allocation["missed_protected_onsets"],
            "selected_logical_notes": fit["selected_logical_notes"],
            "song_specific_rules": False,
        },
        "format": {
            "fixed_pitch_capability": control_payload[7],
            "held_pitch_capability": held_payload[7],
            "fixed_pitch_jps_bytes": len(control_payload),
            "held_pitch_jps_bytes": len(held_payload),
            "jps_growth_bytes": len(held_payload) - len(control_payload),
            "frame_samples": held_metadata["frame_samples"],
            "phase_table_hz": held_metadata["target_sample_hz"],
            "control_phase_table_hz": control_metadata["target_sample_hz"],
        },
        "player": {
            "build": "existing library ABI v1+v2 envelope (-P2=1 -P4=1)",
            "bytes": len(player_bytes),
            "end_address_exclusive": hex(
                baseline.COM_ADDRESS + len(player_bytes)
            ),
            "sample_loop_sha256": loop_hash,
            "new_target_code_bytes": 0,
            "new_target_state_bytes": 0,
        },
        "profiles": profiles,
        "combined_sample_rate_floor_hz": floor,
        "target_wavs": wavs,
        "gates": gates,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--score", type=Path, default=DEFAULT_SCORE)
    parser.add_argument("--output", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    try:
        result = generate(args.score, args.output_dir)
    except (OSError, ValueError, RuntimeError) as exc:
        parser.error(str(exc))
    rendered = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.check:
        if args.output.read_text() != rendered:
            raise SystemExit(f"{args.output} is missing or stale")
        action = "checked"
    else:
        args.output.write_text(rendered)
        action = "wrote"
    profile = result["profiles"]["held_pitch"]
    print(
        f"JUKUPOLY-PITCH-REAL: {action} {args.output} "
        f"packets={result['policy']['emitted_legato_packets']} "
        f"jps={result['format']['held_pitch_jps_bytes']} "
        f"sample={profile['effective_sample_hz']:.1f}Hz "
        f"music={profile['music_frame_hz']:.3f}Hz "
        f"duration={profile['duration_seconds']:.3f}s"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
