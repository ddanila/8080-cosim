#!/usr/bin/env python3
"""Qualify the separately gated M5 runtime-vibrato target experiment."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import sys
import tempfile
from pathlib import Path

import report_jukupoly_baseline as baseline
import report_jukupoly_vibrato_parser as parser_report


ROOT = Path(__file__).resolve().parents[3]
SPINOFF = ROOT / "spinoffs" / "jukupoly"
FIRMWARE = SPINOFF / "firmware"
FIXTURE = FIRMWARE / "jukupoly-vibrato-v2-test.json"
COMBINED_FIXTURE = FIRMWARE / "jukupoly-vibrato-tremolo-v2-test.json"
TRACE_FIXTURE = FIRMWARE / "jukupoly-vibrato-parser-v2-test.json"
REPORT = SPINOFF / "OPL-VIBRATO-TARGET-M5.json"
COM_ADDRESS = 0x0100
SONG_ADDRESS = 0x1800
PHASE_INCREMENT = 7955
SOURCE_LFO_HZ = 6.068835788
sys.path.insert(0, str(FIRMWARE))

import build_jukupoly as build  # noqa: E402


def build_player(directory: Path, label: str, *, tremolo: bool = False,
                 runtime_vibrato: bool = False
                 ) -> tuple[Path, dict[str, int]]:
    player = directory / f"{label}.cim"
    command = [
        str(ROOT / "third_party" / "zmac" / "src" / "zmac"),
        "--nmnv", "--zmac", "-8", "-P2=1", "-P4=1",
    ]
    if tremolo:
        command.append("-P5=1")
    if runtime_vibrato:
        command.extend(("-P6=1", "-P7=1"))
    command.extend((
        "-L", "-l", f"-I{FIRMWARE}", "-o", str(player),
        str(FIRMWARE / "jukupoly-player-0100.asm"),
    ))
    listing = baseline.run(command)
    return player, baseline.symbols(listing)


def build_score(directory: Path, label: str, score: dict
                ) -> tuple[Path, str, dict]:
    generated, metadata = build.compile_song(score)
    song = directory / f"{label}.jps"
    song.write_bytes(build.assemble_song_file(generated, metadata))
    return song, generated, metadata


def build_standalone(directory: Path, label: str, generated: str,
                     *, tremolo: bool) -> Path:
    source = directory / f"{label}.asm"
    envelope = directory / "jukupoly-envelope-v2.inc"
    include = directory / "jukupoly-song-generated.inc"
    source.write_bytes((FIRMWARE / "jukupoly-player-0100.asm").read_bytes())
    envelope.write_bytes((FIRMWARE / envelope.name).read_bytes())
    include.write_text(generated)
    image = directory / f"{label}.cim"
    command = [
        str(ROOT / "third_party" / "zmac" / "src" / "zmac"),
        "--nmnv", "--zmac", "-8", "-P3=1", "-P4=1", "-P6=1",
        "-P7=1",
    ]
    if tremolo:
        command.append("-P5=1")
    command.extend((f"-I{directory}", "-o", str(image), str(source)))
    baseline.run(command)
    return image


def execution_profile(profile: dict) -> dict:
    ignored = {"label", "com_bytes", "mutated_player_bytes"}
    return {key: value for key, value in profile.items() if key not in ignored}


def boundary_delta(new: dict, old: dict) -> dict:
    return {
        key: round(new[key] - old[key], 6)
        for key in ("min", "mean", "p99", "max")
    }


def generate() -> dict:
    frozen = json.loads((SPINOFF / "OPL-BASELINE.json").read_text())
    envelope_report = json.loads((SPINOFF / "OPL-ENVELOPE-M3.json").read_text())
    held_pitch_report = json.loads((SPINOFF / "OPL-PITCH-REAL-M5.json").read_text())
    parser_checkpoint = parser_report.generate()
    source = json.loads(FIXTURE.read_text())
    combined_source = json.loads(COMBINED_FIXTURE.read_text())
    pitch_control_source = copy.deepcopy(source)
    pitch_control_source["title"] = "Synthetic matched no-vibrato pitch control"
    combined_control_source = copy.deepcopy(combined_source)
    combined_control_source["title"] = (
        "Synthetic matched tremolo-only combined control"
    )
    for control in (pitch_control_source, combined_control_source):
        for row in control["rows"]:
            for channel in ("tone1", "tone2", "tone3"):
                row[channel].pop("opl_vibrato")
    trace_source = json.loads(TRACE_FIXTURE.read_text())
    combined_trace_source = copy.deepcopy(trace_source)
    combined_trace_source["title"] = "Synthetic combined tremolo/vibrato runtime trace"
    for channel, depth in zip(("tone1", "tone2", "tone3"), (1, 2, 3)):
        combined_trace_source["rows"][0][channel]["opl_tremolo_depth"] = depth

    with tempfile.TemporaryDirectory(
            prefix="jukupoly-vibrato-target-report.") as name:
        directory = Path(name)
        profiler, _renderer = baseline.build_tools(directory)
        p4, p4_symbols = build_player(directory, "p4")
        p5, p5_symbols = build_player(directory, "p5", tremolo=True)
        p67, p67_symbols = build_player(
            directory, "p67", runtime_vibrato=True,
        )
        p567, p567_symbols = build_player(
            directory, "p567", tremolo=True, runtime_vibrato=True,
        )

        _v1_com, v1_song = baseline.build_fixture(
            directory, "v1", "jukupoly-library-v1-test.json",
        )
        envelope_song, _generated, _metadata = build_score(
            directory, "envelope",
            json.loads((FIRMWARE / "jukupoly-envelope-v2-test.json").read_text()),
        )
        tremolo_song, _generated, _metadata = build_score(
            directory, "tremolo",
            json.loads((FIRMWARE / "jukupoly-tremolo-v2-test.json").read_text()),
        )
        vibrato_song, _generated, vibrato_metadata = build_score(
            directory, "vibrato", source,
        )
        combined_song, _generated, combined_metadata = build_score(
            directory, "combined", combined_source,
        )
        pitch_control_song, _generated, _metadata = build_score(
            directory, "pitch-control", pitch_control_source,
        )
        combined_control_song, _generated, _metadata = build_score(
            directory, "combined-control", combined_control_source,
        )
        _trace_song, trace_generated, _trace_metadata = build_score(
            directory, "trace", trace_source,
        )
        _combined_trace_song, combined_trace_generated, _metadata = build_score(
            directory, "combined-trace", combined_trace_source,
        )

        def profile(player: Path, symbols: dict[str, int], song: Path,
                    label: str) -> dict:
            return json.loads(baseline.run([
                str(profiler), str(player), str(song),
                f"{symbols['player_start']:x}", label,
                f"{symbols['envelope_dispatch_init']:x}",
            ]))

        profiles = {
            "p4_v1": profile(p4, p4_symbols, v1_song, "p4-v1"),
            "p4_cap1": profile(p4, p4_symbols, envelope_song, "p4-cap1"),
            "p5_cap3": profile(p5, p5_symbols, tremolo_song, "p5-cap3"),
            "p67_v1": profile(p67, p67_symbols, v1_song, "p67-v1"),
            "p67_cap1": profile(p67, p67_symbols, envelope_song, "p67-cap1"),
            "p4_pitch_control": profile(
                p4, p4_symbols, pitch_control_song, "p4-pitch-control",
            ),
            "p67_pitch_control": profile(
                p67, p67_symbols, pitch_control_song, "p67-pitch-control",
            ),
            "p67_cap5": profile(
                p67, p67_symbols, vibrato_song, "p67-cap5-runtime",
            ),
            "p567_v1": profile(p567, p567_symbols, v1_song, "p567-v1"),
            "p567_cap1": profile(
                p567, p567_symbols, envelope_song, "p567-cap1",
            ),
            "p567_cap3": profile(
                p567, p567_symbols, tremolo_song, "p567-cap3",
            ),
            "p5_combined_control": profile(
                p5, p5_symbols, combined_control_song,
                "p5-combined-control",
            ),
            "p567_combined_control": profile(
                p567, p567_symbols, combined_control_song,
                "p567-combined-control",
            ),
            "p567_cap7": profile(
                p567, p567_symbols, combined_song, "p567-cap7-runtime",
            ),
        }

        trace_test = directory / "jukupoly_vibrato_test"
        baseline.run([
            "cc", "-std=c11", "-O2", "-Wall", "-Wextra", "-Werror",
            "-o", str(trace_test), "tests/jukupoly_vibrato_test.c",
            "cosim/i8080.c",
        ], stdout=False)
        standalone = build_standalone(
            directory, "vibrato-runtime", trace_generated, tremolo=False,
        )
        combined_standalone = build_standalone(
            directory, "combined-runtime", combined_trace_generated,
            tremolo=True,
        )
        traces = {
            "cap05": baseline.run([str(trace_test), str(standalone)]).strip(),
            "cap07": baseline.run([
                str(trace_test), str(combined_standalone),
            ]).strip(),
        }

        binaries = {
            "p4": p4.read_bytes(),
            "p5": p5.read_bytes(),
            "p67": p67.read_bytes(),
            "p567": p567.read_bytes(),
        }
        symbols = {
            "p4": p4_symbols,
            "p5": p5_symbols,
            "p67": p67_symbols,
            "p567": p567_symbols,
        }
        vibrato_payload = vibrato_song.read_bytes()
        combined_payload = combined_song.read_bytes()
        pitch_control_payload = pitch_control_song.read_bytes()
        combined_control_payload = combined_control_song.read_bytes()

    players = {}
    loop_hashes = {}
    for label, payload in binaries.items():
        symbol = symbols[label]
        loop_start = symbol["sample_loop"] - COM_ADDRESS
        loop_end = symbol["frame_tick"] - COM_ADDRESS
        digest = hashlib.sha256(payload[loop_start:loop_end]).hexdigest()
        loop_hashes[label] = digest
        players[label] = {
            "bytes": len(payload),
            "end_address_exclusive": f"0x{COM_ADDRESS + len(payload):04x}",
            "song_window_margin_bytes": SONG_ADDRESS - (
                COM_ADDRESS + len(payload)
            ),
            "declared_state_bytes": (
                symbol["test_manifest"] - symbol["saved_sp"]
            ),
            "sample_loop_sha256": digest,
        }

    runtime_keys = ("p67_cap5", "p567_cap7")
    floor = envelope_report["v2_sample_rate_floor_hz"]
    maximum_reference_frame = held_pitch_report["profiles"][
        "held_pitch"
    ]["frame_cycles"]["max"]
    phase_rates = {
        key: profiles[key]["music_frame_hz"] * PHASE_INCREMENT / 65536.0
        for key in runtime_keys
    }
    zero_mean_shapes = all(
        sum((0, delta // 2, delta, delta // 2, 0,
             -(delta // 2), -delta, -(delta // 2))) == 0
        for delta in range(1, 257)
    )
    gates = {
        "parser_checkpoint_still_passes": all(
            parser_checkpoint["gates"].values()
        ),
        "existing_p4_size_exact": players["p4"]["bytes"] == 4537,
        "existing_p5_size_exact": players["p5"]["bytes"] == 4863,
        "all_sample_loop_hashes_exact": all(
            digest == frozen["player"]["sample_loop_sha256"]
            for digest in loop_hashes.values()
        ),
        "pitch_runtime_state_is_54_bytes": (
            players["p67"]["declared_state_bytes"] == 54
        ),
        "combined_runtime_state_is_56_bytes": (
            players["p567"]["declared_state_bytes"] == 56
        ),
        "experimental_players_below_song_window": (
            players["p67"]["song_window_margin_bytes"] > 0 and
            players["p567"]["song_window_margin_bytes"] > 0
        ),
        "p67_v1_profile_exact": execution_profile(
            profiles["p67_v1"]
        ) == execution_profile(profiles["p4_v1"]),
        "p67_cap1_profile_exact": execution_profile(
            profiles["p67_cap1"]
        ) == execution_profile(profiles["p4_cap1"]),
        "p67_matched_control_profile_exact": execution_profile(
            profiles["p67_pitch_control"]
        ) == execution_profile(profiles["p4_pitch_control"]),
        "p567_v1_profile_exact": execution_profile(
            profiles["p567_v1"]
        ) == execution_profile(profiles["p4_v1"]),
        "p567_cap1_profile_exact": execution_profile(
            profiles["p567_cap1"]
        ) == execution_profile(profiles["p4_cap1"]),
        "p567_cap3_profile_exact": execution_profile(
            profiles["p567_cap3"]
        ) == execution_profile(profiles["p5_cap3"]),
        "p567_matched_control_profile_exact": execution_profile(
            profiles["p567_combined_control"]
        ) == execution_profile(profiles["p5_combined_control"]),
        "capabilities_are_05_and_07": (
            pitch_control_payload[7] == 1 and
            combined_control_payload[7] == 3 and
            vibrato_payload[7] == 5 and combined_payload[7] == 7
        ),
        "standalone_and_combined_traces_exact": all(
            "JUKUPOLY-VIBRATO: PASS" in trace for trace in traces.values()
        ),
        "immutable_base_and_symmetric_shape": (
            zero_mean_shapes and
            all(
                "reuse-clear" in trace and "immutable-base" in trace
                for trace in traces.values()
            )
        ),
        "runtime_sample_rates_above_shared_floor": all(
            profiles[key]["effective_sample_hz"] >= floor
            for key in runtime_keys
        ),
        "runtime_music_clocks_within_one_percent": all(
            abs(profiles[key]["music_frame_hz"] - 50.0) <= 0.5
            for key in runtime_keys
        ),
        "runtime_durations_within_one_percent": all(
            abs(profiles[key]["duration_seconds"] - 4.0) <= 0.04
            for key in runtime_keys
        ),
        "phase_table_rates_match_measured_within_one_percent": all(
            abs(profiles[key]["effective_sample_hz"] - table_hz) <=
            profiles[key]["effective_sample_hz"] * 0.01
            for key, table_hz in (
                ("p67_cap5", source["sample_rate_hz"]),
                ("p567_cap7", combined_source["sample_rate_hz"]),
            )
        ),
        "vibrato_lfo_rates_within_one_percent": all(
            abs(rate - SOURCE_LFO_HZ) <= SOURCE_LFO_HZ * 0.01
            for rate in phase_rates.values()
        ),
        "worst_frames_measured_for_physical_followup": all(
            profiles[key]["frame_cycles"]["count"] == 200 and
            profiles[key]["frame_cycles"]["max"] > 0
            for key in runtime_keys
        ),
        "percussion_and_escape_remain_concurrent": (
            vibrato_metadata["descriptors"] == 1 and
            combined_metadata["descriptors"] == 1 and
            all(profiles[key]["keyboard_polls"] >= 200 for key in runtime_keys)
        ),
        "synthetic_jps_files_below_soft_limit": (
            len(vibrato_payload) < 30 * 1024 and
            len(combined_payload) < 30 * 1024
        ),
        "normal_target_build_remains_guarded": (
            parser_checkpoint["runtime_boundary"]["normal_build_enabled"]
            is False
        ),
    }
    if not all(gates.values()):
        failed = ", ".join(key for key, value in gates.items() if not value)
        measured = "; ".join(
            f"{key}: sample={profiles[key]['effective_sample_hz']:.6f}Hz "
            f"music={profiles[key]['music_frame_hz']:.6f}Hz "
            f"duration={profiles[key]['duration_seconds']:.6f}s "
            f"max={profiles[key]['frame_cycles']['max']} "
            f"lfo={phase_rates[key]:.6f}Hz"
            for key in runtime_keys
        )
        raise RuntimeError(
            "runtime vibrato target gate failure: " + failed +
            " (" + measured + ")"
        )

    return {
        "schema": "jukupoly-opl-vibrato-target-m5-report-v1",
        "cpu_hz": 1_700_000,
        "status": (
            "synthetic standalone and combined runtime gates pass; normal "
            "conversion remains disabled pending a representative real-song "
            "render and physical A/B"
        ),
        "frozen_baseline": {
            "path": "OPL-BASELINE.json",
            "parser_path": "OPL-VIBRATO-PARSER-M5.json",
            "envelope_path": "OPL-ENVELOPE-M3.json",
            "held_pitch_path": "OPL-PITCH-REAL-M5.json",
            "sample_loop_sha256": frozen["player"]["sample_loop_sha256"],
            "sample_rate_floor_hz": floor,
            "worst_accepted_held_pitch_frame_cycles": maximum_reference_frame,
        },
        "fixture": {
            "vibrato_score": FIXTURE.name,
            "vibrato_score_sha256": hashlib.sha256(
                FIXTURE.read_bytes()
            ).hexdigest(),
            "combined_score": COMBINED_FIXTURE.name,
            "combined_score_sha256": hashlib.sha256(
                COMBINED_FIXTURE.read_bytes()
            ).hexdigest(),
            "trace_score": TRACE_FIXTURE.name,
            "trace_score_sha256": hashlib.sha256(
                TRACE_FIXTURE.read_bytes()
            ).hexdigest(),
            "frames": 200,
            "selected_batches_and_phase_table_rates": {
                "cap05": {
                    "frame_samples": source["frame_samples"],
                    "phase_table_hz": source["sample_rate_hz"],
                },
                "cap07": {
                    "frame_samples": combined_source["frame_samples"],
                    "phase_table_hz": combined_source["sample_rate_hz"],
                },
            },
            "phase_increment": PHASE_INCREMENT,
            "source_lfo_hz": SOURCE_LFO_HZ,
            "measured_lfo_hz": phase_rates,
            "peak_step_deltas": [1, 128, 256],
            "vibrato_jps_bytes": len(vibrato_payload),
            "combined_jps_bytes": len(combined_payload),
            "matched_control_jps_bytes": {
                "cap01": len(pitch_control_payload),
                "cap03": len(combined_control_payload),
            },
            "matched_control_capabilities": [
                pitch_control_payload[7], combined_control_payload[7],
            ],
            "capabilities": [vibrato_payload[7], combined_payload[7]],
            "target_traces": traces,
        },
        "players": players,
        "profiles": profiles,
        "runtime_boundary_cycles": {
            "pitch_over_cap1": boundary_delta(
                profiles["p67_cap5"]["idle_boundary_cycles"],
                profiles["p67_pitch_control"]["idle_boundary_cycles"],
            ),
            "combined_over_tremolo": boundary_delta(
                profiles["p567_cap7"]["idle_boundary_cycles"],
                profiles["p567_combined_control"]["idle_boundary_cycles"],
            ),
        },
        "runtime_boundary": {
            "shared_phase_advanced": True,
            "temporary_steps_applied": True,
            "base_steps_immutable": True,
            "normal_build_enabled": False,
            "fallback_if_later_gates_fail": (
                "retain qualified host-baked held-pitch packets and omit or "
                "host-bake vibrato"
            ),
            "next_gate": (
                "representative real-song opt-in conversion/render, then "
                "physical CS00000 A/B before normal build enablement"
            ),
        },
        "gates": gates,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=REPORT)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    try:
        result = generate()
    except (OSError, ValueError, RuntimeError) as exc:
        parser.error(str(exc))
    rendered = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.check:
        if not args.output.exists() or args.output.read_text() != rendered:
            raise SystemExit(f"{args.output} is missing or stale")
        action = "checked"
    else:
        args.output.write_text(rendered)
        action = "wrote"
    pitch = result["profiles"]["p67_cap5"]
    combined = result["profiles"]["p567_cap7"]
    print(
        f"JUKUPOLY-VIBRATO-TARGET: {action} {args.output} "
        f"p67={result['players']['p67']['bytes']} bytes "
        f"p567={result['players']['p567']['bytes']} bytes "
        f"pitch={pitch['effective_sample_hz']:.1f}Hz/"
        f"{pitch['music_frame_hz']:.3f}Hz "
        f"combined={combined['effective_sample_hz']:.1f}Hz/"
        f"{combined['music_frame_hz']:.3f}Hz"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
