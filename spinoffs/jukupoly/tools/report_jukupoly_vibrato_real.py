#!/usr/bin/env python3
"""Qualify a bounded real OPL-vibrato reduction and target render."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
import sys
import tempfile
from pathlib import Path

import report_jukupoly_baseline as baseline
import report_jukupoly_vibrato_target as target_report


ROOT = Path(__file__).resolve().parents[3]
SPINOFF = ROOT / "spinoffs" / "jukupoly"
FIRMWARE = SPINOFF / "firmware"
DEFAULT_SCORE = FIRMWARE / "jukupoly-doomgate-30s-vibrato-m5.json"
DEFAULT_REPORT = SPINOFF / "OPL-VIBRATO-REAL-M5.json"
CONTROL_SAMPLE_RATE = 6970
CONTROL_FRAME_SAMPLES = 139
sys.path.insert(0, str(FIRMWARE))

import build_jukupoly as build  # noqa: E402


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rescale_midi_step(step: int, old_rate: int, new_rate: int) -> int:
    """Recover the integer mapped MIDI note, then regenerate its phase step."""
    frequency = step * old_rate / 65536.0
    if frequency <= 0:
        raise ValueError("vibrato score contains a nonpositive phase step")
    midi = round(69.0 + 12.0 * math.log2(frequency / 440.0))
    mapped = round(
        440.0 * 2.0 ** ((midi - 69.0) / 12.0) * 65536.0 / new_rate
    )
    if not 0 < mapped < 0x8000:
        raise ValueError("control phase step exceeds target range")
    return mapped


def vibrato_control_score(score: dict, *, sample_rate: int,
                           frame_samples: int) -> tuple[dict, int]:
    """Remove only vibrato and its now-redundant held-setting packets."""
    if score.get("schema") != "jukupoly-song-v2":
        raise ValueError("real vibrato fixture must use jukupoly-song-v2")
    analysis = score.get("conversion", {}).get("enhanced_vibrato", {})
    if not analysis.get("enabled") or not analysis.get("packets_with_vibrato"):
        raise ValueError("real vibrato fixture contains no emitted vibrato")
    if score["conversion"]["enhanced_held_pitch"]["enabled"]:
        raise ValueError("vibrato control does not rewrite held-pitch scores")
    old_rate = score["sample_rate_hz"]
    result = copy.deepcopy(score)
    state: list[dict | None] = [None, None, None]
    rows = []
    removed = 0
    for source_row in result["rows"]:
        row = {"frames": source_row["frames"]}
        for key, value in source_row.items():
            if key == "frames":
                continue
            if key not in ("tone1", "tone2", "tone3"):
                row[key] = value
                continue
            channel = int(key[-1]) - 1
            event = value
            if event.get("note") == "---":
                state[channel] = None
                row[key] = event
                continue
            event.pop("opl_vibrato", None)
            event["phase_step"] = rescale_midi_step(
                event["phase_step"], old_rate, sample_rate,
            )
            semantic = dict(event)
            semantic.pop("legato", None)
            if event.get("legato") and semantic == state[channel]:
                removed += 1
                continue
            state[channel] = semantic
            row[key] = event
        if len(row) == 1 and rows and rows[-1]["frames"] + row["frames"] <= 255:
            rows[-1]["frames"] += row["frames"]
        else:
            rows.append(row)

    result["title"] = result["title"].replace(
        "envelope+vibrato", "envelope-only comparison",
    )
    result["arrangement"] = (
        "Same allocation and fitted envelopes as the M5 experiment, with "
        "vibrato removed and target timing independently calibrated"
    )
    result["notes"] = (
        "Controlled M5 comparison: identical allocation and envelope fits; "
        "vibrato fields and redundant setting-only legato packets removed."
    )
    result["sample_rate_hz"] = sample_rate
    result["frame_samples"] = frame_samples
    result["rows"] = rows
    result["conversion"]["enhanced_vibrato"] = dict(analysis)
    result["conversion"]["enhanced_vibrato"].update({
        "enabled": False,
        "phase_step_generation_hz": None,
        "packets_with_vibrato": 0,
        "held_setting_updates": 0,
        "held_disable_updates": 0,
    })
    result["conversion"]["enhanced_limitations"] = (
        "Controlled envelope-only comparison; OPL vibrato is not reproduced"
    )
    return result, removed


def build_song(directory: Path, label: str, score: dict
               ) -> tuple[Path, str, dict]:
    generated, metadata = build.compile_song(score)
    song = directory / f"{label}.jps"
    song.write_bytes(build.assemble_song_file(generated, metadata))
    return song, generated, metadata


def build_standalone(directory: Path, label: str, generated: str,
                     *, runtime: bool) -> Path:
    source = directory / f"{label}.asm"
    include = directory / "jukupoly-song-generated.inc"
    envelope = directory / "jukupoly-envelope-v2.inc"
    source.write_bytes((FIRMWARE / "jukupoly-player-0100.asm").read_bytes())
    include.write_text(generated)
    envelope.write_bytes((FIRMWARE / envelope.name).read_bytes())
    image = directory / f"{label}.cim"
    command = [
        str(ROOT / "third_party" / "zmac" / "src" / "zmac"),
        "--nmnv", "--zmac", "-8", "-P3=1", "-P4=1",
    ]
    if runtime:
        command.extend(("-P6=1", "-P7=1"))
    command.extend((f"-I{directory}", "-o", str(image), str(source)))
    baseline.run(command)
    return image


def tone_events(score: dict) -> list[dict]:
    result = []
    for row in score["rows"]:
        for channel in ("tone1", "tone2", "tone3"):
            event = row.get(channel)
            if isinstance(event, dict) and event.get("note") != "---":
                result.append(event)
    return result


def generate(score_path: Path, output_dir: Path | None,
             oracle_reference: Path | None) -> dict:
    score = json.loads(score_path.read_text())
    if oracle_reference is not None and not oracle_reference.is_file():
        raise ValueError(f"oracle reference is missing: {oracle_reference}")
    control, removed_updates = vibrato_control_score(
        score, sample_rate=CONTROL_SAMPLE_RATE,
        frame_samples=CONTROL_FRAME_SAMPLES,
    )
    analysis = score["conversion"]["enhanced_vibrato"]
    allocation = score["conversion"]["enhanced_allocation"]
    source_seconds = score["conversion"]["duration_seconds"]

    with tempfile.TemporaryDirectory(
            prefix="jukupoly-vibrato-real-report.") as name:
        directory = Path(name)
        profiler, renderer = baseline.build_tools(directory)
        player, symbols = target_report.build_player(
            directory, "p67-real", runtime_vibrato=True,
        )
        control_song, control_generated, control_metadata = build_song(
            directory, "control", control,
        )
        vibrato_song, vibrato_generated, vibrato_metadata = build_song(
            directory, "vibrato", score,
        )
        control_image = build_standalone(
            directory, "control", control_generated, runtime=False,
        )
        vibrato_image = build_standalone(
            directory, "vibrato", vibrato_generated, runtime=True,
        )

        def profile(song: Path, label: str) -> dict:
            return json.loads(baseline.run([
                str(profiler), str(player), str(song),
                f"{symbols['player_start']:x}", label,
                f"{symbols['envelope_dispatch_init']:x}",
            ]))

        profiles = {
            "envelope_control": profile(
                control_song, "doomgate-30s-envelope-control",
            ),
            "vibrato": profile(
                vibrato_song, "doomgate-30s-vibrato",
            ),
        }
        player_payload = player.read_bytes()
        control_payload = control_song.read_bytes()
        vibrato_payload = vibrato_song.read_bytes()
        render_directory = output_dir if output_dir is not None else directory
        render_directory.mkdir(parents=True, exist_ok=True)
        wavs = {}
        for label, image in (
                ("envelope_control", control_image),
                ("vibrato", vibrato_image)):
            wav = render_directory / f"doomgate-30s-{label}.wav"
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

        target_refused = False
        try:
            build.assemble(
                vibrato_generated,
                enhanced_envelopes=vibrato_metadata["enhanced_envelopes"],
                enhanced_vibrato=vibrato_metadata["enhanced_vibrato"],
            )
        except build.SongError as exc:
            target_refused = "not implemented" in str(exc)

    loop_start = symbols["sample_loop"] - baseline.COM_ADDRESS
    loop_end = symbols["frame_tick"] - baseline.COM_ADDRESS
    loop_hash = hashlib.sha256(
        player_payload[loop_start:loop_end]
    ).hexdigest()
    frozen = json.loads((SPINOFF / "OPL-BASELINE.json").read_text())
    envelope_report = json.loads((SPINOFF / "OPL-ENVELOPE-M3.json").read_text())
    floor = envelope_report["v2_sample_rate_floor_hz"]
    events = tone_events(score)
    vibrato_events = [event for event in events if "opl_vibrato" in event]
    new_profile = profiles["vibrato"]
    control_profile = profiles["envelope_control"]
    measured_lfo = (
        new_profile["music_frame_hz"] * analysis["phase_increment"] / 65536.0
    )
    gates = {
        "generic_direct_candidates_emitted": (
            analysis["direct_logical_notes"] > 0 and
            analysis["emitted_logical_notes"] > 0 and
            analysis["packets_with_vibrato"] == len(vibrato_events)
        ),
        "no_protected_onset_regression": (
            allocation["missed_protected_onsets"] == 0
        ),
        "every_packet_delta_and_bounds_safe": all(
            1 <= event["opl_vibrato"]["peak_step_delta"] <= 256 and
            event["phase_step"] -
            event["opl_vibrato"]["peak_step_delta"] > 0 and
            event["phase_step"] +
            event["opl_vibrato"]["peak_step_delta"] < 0x8000
            for event in vibrato_events
        ),
        "control_removes_every_setting_only_update": (
            removed_updates == analysis["held_setting_updates"]
        ),
        "capabilities_are_01_and_05": (
            control_payload[7] == build.JPS2_ENVELOPE_CAPABILITY and
            vibrato_payload[7] == (
                build.JPS2_ENVELOPE_CAPABILITY |
                build.JPS2_PITCH_CAPABILITY
            )
        ),
        "phase_steps_generated_at_declared_rate": (
            analysis["phase_step_generation_hz"] == score["sample_rate_hz"]
        ),
        "sample_loop_hash_exact": (
            loop_hash == frozen["player"]["sample_loop_sha256"]
        ),
        "runtime_sample_rate_above_shared_floor": (
            new_profile["effective_sample_hz"] >= floor
        ),
        "runtime_phase_table_matches_within_one_percent": (
            abs(new_profile["effective_sample_hz"] -
                score["sample_rate_hz"]) <=
            new_profile["effective_sample_hz"] * 0.01
        ),
        "runtime_music_clock_within_one_percent": (
            abs(new_profile["music_frame_hz"] - 50.0) <= 0.5
        ),
        "runtime_duration_within_one_percent": (
            abs(new_profile["duration_seconds"] - source_seconds) <=
            source_seconds * 0.01
        ),
        "runtime_lfo_rate_within_one_percent": (
            abs(measured_lfo - analysis["source_lfo_hz"]) <=
            analysis["source_lfo_hz"] * 0.01
        ),
        "control_phase_table_matches_within_one_percent": (
            abs(control_profile["effective_sample_hz"] -
                control["sample_rate_hz"]) <=
            control_profile["effective_sample_hz"] * 0.01
        ),
        "control_music_clock_within_one_percent": (
            abs(control_profile["music_frame_hz"] - 50.0) <= 0.5
        ),
        "control_duration_within_one_percent": (
            abs(control_profile["duration_seconds"] - source_seconds) <=
            source_seconds * 0.01
        ),
        "runtime_jps_below_soft_limit": len(vibrato_payload) < 30 * 1024,
        "player_below_song_window": (
            baseline.COM_ADDRESS + len(player_payload) < baseline.SONG_ADDRESS
        ),
        "percussion_and_escape_remain_concurrent": (
            vibrato_metadata["descriptors"] > 0 and
            new_profile["keyboard_polls"] >= new_profile["frames"]
        ),
        "target_wavs_differ": (
            wavs["envelope_control"]["sha256"] != wavs["vibrato"]["sha256"]
        ),
        "normal_target_build_remains_guarded": target_refused,
    }
    if not all(gates.values()):
        failed = ", ".join(key for key, value in gates.items() if not value)
        measured = "; ".join(
            f"{key}: sample={profile['effective_sample_hz']:.6f}Hz "
            f"music={profile['music_frame_hz']:.6f}Hz "
            f"duration={profile['duration_seconds']:.6f}s"
            for key, profile in profiles.items()
        )
        raise RuntimeError(
            "real vibrato gate failure: " + failed + " (" + measured + ")"
        )

    reference = None if oracle_reference is None else {
        "path_hint": oracle_reference.name,
        "bytes": oracle_reference.stat().st_size,
        "sha256": sha256(oracle_reference),
    }
    return {
        "schema": "jukupoly-opl-vibrato-real-m5-report-v1",
        "status": (
            "bounded real C-cosim and render gates pass; normal target build "
            "and physical CS00000 A/B remain guarded"
        ),
        "source": {
            "score": score_path.name,
            "score_sha256": sha256(score_path),
            "name": score["source"]["name"],
            "vgm_sha256": score["source"]["vgm_sha256"],
            "seconds": source_seconds,
        },
        "policy": analysis,
        "allocation": allocation,
        "format": {
            "control_capability": control_payload[7],
            "vibrato_capability": vibrato_payload[7],
            "control_jps_bytes": len(control_payload),
            "vibrato_jps_bytes": len(vibrato_payload),
            "jps_growth_over_calibrated_control": (
                len(vibrato_payload) - len(control_payload)
            ),
            "removed_control_updates": removed_updates,
            "control_frame_samples": control_metadata["frame_samples"],
            "control_phase_table_hz": control_metadata["target_sample_hz"],
            "vibrato_frame_samples": vibrato_metadata["frame_samples"],
            "vibrato_phase_table_hz": vibrato_metadata["target_sample_hz"],
        },
        "player": {
            "bytes": len(player_payload),
            "end_address_exclusive": hex(
                baseline.COM_ADDRESS + len(player_payload)
            ),
            "song_window_margin_bytes": baseline.SONG_ADDRESS - (
                baseline.COM_ADDRESS + len(player_payload)
            ),
            "declared_state_bytes": (
                symbols["test_manifest"] - symbols["saved_sp"]
            ),
            "sample_loop_sha256": loop_hash,
        },
        "profiles": profiles,
        "shared_sample_rate_floor_hz": floor,
        "measured_vibrato_lfo_hz": measured_lfo,
        "target_wavs": wavs,
        "opl_reference_wav": reference,
        "runtime_boundary": {
            "normal_build_enabled": False,
            "physical_ab_passed": False,
            "fallback": "envelope control plus qualified host-baked pitch",
        },
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
    profile = result["profiles"]["vibrato"]
    print(
        f"JUKUPOLY-VIBRATO-REAL: {action} {args.output} "
        f"notes={result['policy']['emitted_logical_notes']} "
        f"packets={result['policy']['packets_with_vibrato']} "
        f"jps={result['format']['vibrato_jps_bytes']} "
        f"sample={profile['effective_sample_hz']:.1f}Hz "
        f"music={profile['music_frame_hz']:.3f}Hz "
        f"duration={profile['duration_seconds']:.3f}s"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
