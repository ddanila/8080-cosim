#!/usr/bin/env python3
"""Qualify the parser/state-only M5 vibrato target checkpoint."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import sys
import tempfile
from pathlib import Path

import report_jukupoly_baseline as baseline


ROOT = Path(__file__).resolve().parents[3]
SPINOFF = ROOT / "spinoffs" / "jukupoly"
FIRMWARE = SPINOFF / "firmware"
FIXTURE = FIRMWARE / "jukupoly-vibrato-parser-v2-test.json"
REPORT = SPINOFF / "OPL-VIBRATO-PARSER-M5.json"
COM_ADDRESS = 0x0100
SONG_ADDRESS = 0x1800
sys.path.insert(0, str(FIRMWARE))

import build_jukupoly as build  # noqa: E402


def build_player(directory: Path, label: str, *, tremolo: bool = False,
                 vibrato_parser: bool = False) -> tuple[Path, dict[str, int]]:
    player = directory / f"{label}.cim"
    command = [
        str(ROOT / "third_party" / "zmac" / "src" / "zmac"),
        "--nmnv", "--zmac", "-8", "-P2=1", "-P4=1", "-L", "-l",
        f"-I{FIRMWARE}", "-o", str(player),
        str(FIRMWARE / "jukupoly-player-0100.asm"),
    ]
    if tremolo:
        command.insert(6, "-P5=1")
    if vibrato_parser:
        command.insert(6, "-P6=1")
    listing = baseline.run(command)
    return player, baseline.symbols(listing)


def build_score(directory: Path, label: str, score: dict
                ) -> tuple[Path, str, dict]:
    generated, metadata = build.compile_song(score)
    song = directory / f"{label}.jps"
    song.write_bytes(build.assemble_song_file(generated, metadata))
    return song, generated, metadata


def build_standalone_parser(directory: Path, generated: str) -> Path:
    source = directory / "jukupoly-player-0100.asm"
    envelope = directory / "jukupoly-envelope-v2.inc"
    include = directory / "jukupoly-song-generated.inc"
    source.write_bytes((FIRMWARE / source.name).read_bytes())
    envelope.write_bytes((FIRMWARE / envelope.name).read_bytes())
    include.write_text(generated)
    image = directory / "vibrato-parser.cim"
    baseline.run([
        str(ROOT / "third_party" / "zmac" / "src" / "zmac"),
        "--nmnv", "--zmac", "-8", "-P3=1", "-P4=1", "-P6=1",
        f"-I{directory}", "-o", str(image), str(source),
    ])
    return image


def execution_profile(profile: dict) -> dict:
    ignored = {"label", "com_bytes", "mutated_player_bytes"}
    return {key: value for key, value in profile.items() if key not in ignored}


def generate() -> dict:
    frozen = json.loads((SPINOFF / "OPL-BASELINE.json").read_text())
    source = json.loads(FIXTURE.read_text())
    combined = copy.deepcopy(source)
    combined["title"] = "Synthetic combined tremolo/vibrato parser fixture"
    combined["rows"][0]["tone1"]["opl_tremolo_depth"] = 1

    with tempfile.TemporaryDirectory(
            prefix="jukupoly-vibrato-parser-report.") as name:
        directory = Path(name)
        profiler, _renderer = baseline.build_tools(directory)
        p4, p4_symbols = build_player(directory, "p4")
        p5, p5_symbols = build_player(directory, "p5", tremolo=True)
        p6, p6_symbols = build_player(
            directory, "p6", vibrato_parser=True,
        )
        p56, p56_symbols = build_player(
            directory, "p56", tremolo=True, vibrato_parser=True,
        )
        _v1_com, v1 = baseline.build_fixture(
            directory, "v1", "jukupoly-library-v1-test.json",
        )
        envelope_song, _envelope_generated, _envelope_metadata = build_score(
            directory, "envelope",
            json.loads((FIRMWARE / "jukupoly-envelope-v2-test.json").read_text()),
        )
        tremolo_song, _tremolo_generated, _tremolo_metadata = build_score(
            directory, "tremolo",
            json.loads((FIRMWARE / "jukupoly-tremolo-v2-test.json").read_text()),
        )
        pitch_song, pitch_generated, pitch_metadata = build_score(
            directory, "pitch", source,
        )
        combined_song, _combined_generated, combined_metadata = build_score(
            directory, "combined", combined,
        )
        standalone = build_standalone_parser(directory, pitch_generated)

        def profile(player: Path, symbols: dict[str, int], song: Path,
                    label: str) -> dict:
            return json.loads(baseline.run([
                str(profiler), str(player), str(song),
                f"{symbols['player_start']:x}", label,
                f"{symbols['envelope_dispatch_init']:x}",
            ]))

        profiles = {
            "p4_v1": profile(p4, p4_symbols, v1, "p4-v1"),
            "p4_cap1": profile(p4, p4_symbols, envelope_song, "p4-cap1"),
            "p5_cap1": profile(p5, p5_symbols, envelope_song, "p5-cap1"),
            "p5_cap3": profile(p5, p5_symbols, tremolo_song, "p5-cap3"),
            "p6_v1": profile(p6, p6_symbols, v1, "p6-v1"),
            "p6_cap1": profile(p6, p6_symbols, envelope_song, "p6-cap1"),
            "p6_cap5_parser_only": profile(
                p6, p6_symbols, pitch_song, "p6-cap5-parser-only",
            ),
            "p56_v1": profile(p56, p56_symbols, v1, "p56-v1"),
            "p56_cap1": profile(p56, p56_symbols, envelope_song, "p56-cap1"),
            "p56_cap3": profile(p56, p56_symbols, tremolo_song, "p56-cap3"),
            "p56_cap5_parser_only": profile(
                p56, p56_symbols, pitch_song, "p56-cap5-parser-only",
            ),
            "p56_cap7_parser_only": profile(
                p56, p56_symbols, combined_song, "p56-cap7-parser-only",
            ),
        }

        parser_test = directory / "jukupoly_vibrato_parser_test"
        library_test = directory / "jukupoly_library_test"
        common = ["cc", "-std=c11", "-O2", "-Wall", "-Wextra", "-Werror"]
        baseline.run(common + [
            "-o", str(parser_test), "tests/jukupoly_vibrato_parser_test.c",
            "cosim/i8080.c",
        ], stdout=False)
        baseline.run(common + [
            "-o", str(library_test), "tests/jukupoly_library_test.c",
            "cosim/i8080.c",
        ], stdout=False)
        parser_trace = baseline.run([str(parser_test), str(standalone)]).strip()
        valid_preflight = baseline.run([
            str(library_test), str(p6), str(pitch_song),
        ]).strip()
        corruptions = (
            "invalid-vibrato-mode",
            "invalid-vibrato-underflow",
            "invalid-vibrato-overflow",
            "invalid-vibrato-missing-delta",
            "invalid-vibrato-unadvertised",
            "invalid-tremolo-unadvertised",
        )
        rejected = {
            corruption: baseline.run([
                str(library_test), str(p6), str(pitch_song), corruption,
            ]).strip()
            for corruption in corruptions
        }

        target_refused = False
        try:
            build.assemble(
                pitch_generated,
                enhanced_envelopes=pitch_metadata["enhanced_envelopes"],
                enhanced_vibrato=pitch_metadata["enhanced_vibrato"],
            )
        except build.SongError as exc:
            target_refused = "not implemented" in str(exc)

        binaries = {
            "p4": p4.read_bytes(),
            "p5": p5.read_bytes(),
            "p6": p6.read_bytes(),
            "p56": p56.read_bytes(),
        }
        symbols = {
            "p4": p4_symbols, "p5": p5_symbols,
            "p6": p6_symbols, "p56": p56_symbols,
        }
        pitch_payload = pitch_song.read_bytes()
        combined_payload = combined_song.read_bytes()

    loop_hashes = {}
    players = {}
    for label, payload in binaries.items():
        symbol = symbols[label]
        start = symbol["sample_loop"] - COM_ADDRESS
        end = symbol["frame_tick"] - COM_ADDRESS
        loop_hashes[label] = hashlib.sha256(payload[start:end]).hexdigest()
        players[label] = {
            "bytes": len(payload),
            "end_address_exclusive": hex(COM_ADDRESS + len(payload)),
            "song_window_margin_bytes": SONG_ADDRESS - (
                COM_ADDRESS + len(payload)
            ),
            "declared_state_bytes": (
                symbol["test_manifest"] - symbol["saved_sp"]
            ),
            "sample_loop_sha256": loop_hashes[label],
        }

    gates = {
        "existing_p4_size_exact": players["p4"]["bytes"] == 4537,
        "existing_p5_size_exact": players["p5"]["bytes"] == 4863,
        "all_sample_loop_hashes_exact": all(
            digest == frozen["player"]["sample_loop_sha256"]
            for digest in loop_hashes.values()
        ),
        "pitch_only_state_is_54_bytes": (
            players["p6"]["declared_state_bytes"] == 54
        ),
        "combined_state_is_exactly_56_bytes": (
            players["p56"]["declared_state_bytes"] == 56
        ),
        "experimental_players_below_song_window": (
            players["p6"]["song_window_margin_bytes"] > 0 and
            players["p56"]["song_window_margin_bytes"] > 0
        ),
        "p6_cap1_profile_exact": execution_profile(
            profiles["p6_cap1"]
        ) == execution_profile(profiles["p4_cap1"]),
        "p6_v1_profile_exact": execution_profile(
            profiles["p6_v1"]
        ) == execution_profile(profiles["p4_v1"]),
        "p56_cap1_profile_exact": execution_profile(
            profiles["p56_cap1"]
        ) == execution_profile(profiles["p4_cap1"]),
        "p56_cap3_profile_exact": execution_profile(
            profiles["p56_cap3"]
        ) == execution_profile(profiles["p5_cap3"]),
        "p56_v1_profile_exact": execution_profile(
            profiles["p56_v1"]
        ) == execution_profile(profiles["p4_v1"]),
        "capabilities_are_05_and_07": (
            pitch_payload[7] == 5 and combined_payload[7] == 7
        ),
        "conditional_parser_trace_exact": (
            "JUKUPOLY-VIBRATO-PARSER: PASS" in parser_trace
        ),
        "valid_cap05_preflight_plays": (
            "JUKUPOLY-LIBRARY: PASS mode=complete" in valid_preflight
        ),
        "all_malformed_inputs_rejected_before_io": all(
            "mode=invalid-preflight" in output and
            "pit-writes=0 key-polls=0" in output
            for output in rejected.values()
        ),
        "normal_target_build_remains_refused": target_refused,
        "parser_phase_remains_inactive": "phase-inactive" in parser_trace,
    }
    if not all(gates.values()):
        failed = ", ".join(key for key, value in gates.items() if not value)
        raise RuntimeError("vibrato parser gate failure: " + failed)

    return {
        "schema": "jukupoly-opl-vibrato-parser-m5-report-v1",
        "status": (
            "capability 05h/07h parser, preflight, and bounded state pass; "
            "runtime LFO deliberately inactive and unsupported"
        ),
        "fixture": {
            "score": FIXTURE.name,
            "score_sha256": hashlib.sha256(FIXTURE.read_bytes()).hexdigest(),
            "jps_bytes": len(pitch_payload),
            "capability": pitch_payload[7],
            "conditional_deltas": [1, 256, 7, 16],
            "frames": sum(row["frames"] for row in source["rows"]),
        },
        "players": players,
        "profiles": profiles,
        "preflight": {
            "valid": valid_preflight,
            "rejected": rejected,
        },
        "parser_trace": parser_trace,
        "runtime_boundary": {
            "shared_phase_advanced": False,
            "temporary_steps_applied": False,
            "normal_build_enabled": False,
            "next_gate": (
                "exact eight-position shared-phase temporary-step trace, "
                "then combined cycle qualification"
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
        if args.output.read_text() != rendered:
            raise SystemExit(f"{args.output} is missing or stale")
        action = "checked"
    else:
        args.output.write_text(rendered)
        action = "wrote"
    print(
        f"JUKUPOLY-VIBRATO-PARSER-REPORT: {action} {args.output} "
        f"p6={result['players']['p6']['bytes']} bytes "
        f"p56={result['players']['p56']['bytes']} bytes "
        f"state={result['players']['p56']['declared_state_bytes']} bytes"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
