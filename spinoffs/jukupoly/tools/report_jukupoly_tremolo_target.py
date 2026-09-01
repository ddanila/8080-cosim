#!/usr/bin/env python3
"""Measure the guarded JPS v2 tremolo target slice in C-cosim."""

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
REPORT = SPINOFF / "OPL-TREMOLO-TARGET-M4.json"
COM_ADDRESS = 0x0100
SONG_ADDRESS = 0x1800
sys.path.insert(0, str(FIRMWARE))

import build_jukupoly as build  # noqa: E402


def build_player(directory: Path, *, tremolo: bool) -> tuple[Path, dict[str, int]]:
    player = directory / ("JUKEBOX-P5.cim" if tremolo else "JUKEBOX-P4.cim")
    command = [
        str(ROOT / "third_party" / "zmac" / "src" / "zmac"),
        "--nmnv", "--zmac", "-8", "-P2=1", "-P4=1", "-L", "-l",
        f"-I{FIRMWARE}", "-o", str(player),
        str(FIRMWARE / "jukupoly-player-0100.asm"),
    ]
    if tremolo:
        command.insert(6, "-P5=1")
    listing = baseline.run(command)
    return player, baseline.symbols(listing)


def build_song(directory: Path, label: str, song: dict,
               *, force_tremolo_capability: bool = False) -> Path:
    generated, metadata = build.compile_song(song)
    payload = bytearray(build.assemble_song_file(generated, metadata))
    if force_tremolo_capability:
        if payload[3] != 2 or payload[7] != build.JPS2_ENVELOPE_CAPABILITY:
            raise RuntimeError("cannot force tremolo on a non-envelope fixture")
        payload[7] |= build.JPS2_TREMOLO_CAPABILITY
    path = directory / f"{label}.jps"
    path.write_bytes(payload)
    return path


def execution_profile(profile: dict) -> dict:
    ignored = {"label", "com_bytes", "mutated_player_bytes"}
    return {key: value for key, value in profile.items() if key not in ignored}


def delta(new: dict, old: dict) -> dict:
    return {
        key: round(new[key] - old[key], 6)
        for key in ("min", "mean", "p99", "max")
    }


def generate() -> dict:
    frozen = json.loads((SPINOFF / "OPL-BASELINE.json").read_text())
    envelope_report = json.loads(
        (SPINOFF / "OPL-ENVELOPE-M3.json").read_text()
    )
    source = json.loads(
        (FIRMWARE / "jukupoly-tremolo-v2-test.json").read_text()
    )
    with tempfile.TemporaryDirectory(prefix="jukupoly-tremolo-target.") as name:
        directory = Path(name)
        profiler, _renderer = baseline.build_tools(directory)
        p4, p4_symbols = build_player(directory, tremolo=False)
        p5, p5_symbols = build_player(directory, tremolo=True)
        p5_binary = p5.read_bytes()

        _standalone, v1_song = baseline.build_fixture(
            directory, "doomgate", "jukupoly-doomgate-vgz.json",
        )
        envelope_song = build_song(
            directory, "envelope",
            json.loads((FIRMWARE / "jukupoly-envelope-v2-test.json").read_text()),
        )

        zero_score = copy.deepcopy(source)
        zero_score["sample_rate_hz"] = 7000
        for channel in ("tone1", "tone2", "tone3"):
            zero_score["rows"][0][channel]["opl_tremolo_depth"] = 0
        disabled_zero_song = build_song(directory, "disabled-zero", zero_score)
        enabled_zero_song = build_song(
            directory, "enabled-zero", zero_score,
            force_tremolo_capability=True,
        )

        one_score = copy.deepcopy(zero_score)
        one_score["sample_rate_hz"] = 6990
        one_score["rows"][0]["tone1"]["opl_tremolo_depth"] = 1
        one_song = build_song(directory, "one-depth", one_score)
        three_song = build_song(directory, "three-depth", source)
        selected_three_score = copy.deepcopy(source)
        selected_three_score["sample_rate_hz"] = 6970
        selected_three_score["frame_samples"] = 140
        selected_three_song = build_song(
            directory, "three-depth-selected", selected_three_score,
        )

        empty_score = copy.deepcopy(zero_score)
        empty_score["sample_rate_hz"] = 7160
        empty_score["frame_samples"] = 143
        empty_score["rows"] = [{"frames": 200}]
        empty_song = build_song(
            directory, "empty", empty_score,
            force_tremolo_capability=True,
        )

        def profile(player: Path, symbols: dict[str, int], song: Path,
                    label: str) -> dict:
            output = baseline.run([
                str(profiler), str(player), str(song),
                f"{symbols['player_start']:x}", label,
                f"{symbols['envelope_dispatch_init']:x}",
            ])
            return json.loads(output)

        profiles = {
            "p5_v1_doomgate": profile(
                p5, p5_symbols, v1_song, "p5-v1-doomgate",
            ),
            "p4_envelope": profile(
                p4, p4_symbols, envelope_song, "p4-envelope",
            ),
            "p5_envelope": profile(
                p5, p5_symbols, envelope_song, "p5-envelope",
            ),
            "disabled_zero": profile(
                p5, p5_symbols, disabled_zero_song, "p5-cap1-zero",
            ),
            "enabled_empty": profile(
                p5, p5_symbols, empty_song, "p5-cap3-empty",
            ),
            "enabled_zero": profile(
                p5, p5_symbols, enabled_zero_song, "p5-cap3-zero",
            ),
            "enabled_one": profile(
                p5, p5_symbols, one_song, "p5-cap3-one",
            ),
            "enabled_three": profile(
                p5, p5_symbols, three_song, "p5-cap3-three",
            ),
            "selected_three": profile(
                p5, p5_symbols, selected_three_song,
                "p5-cap3-three-selected",
            ),
        }

        test_binary = directory / "jukupoly_tremolo_test"
        baseline.run([
            "cc", "-std=c11", "-O2", "-Wall", "-Wextra", "-Werror",
            "-o", str(test_binary), "tests/jukupoly_tremolo_test.c",
            "cosim/i8080.c",
        ], stdout=False)
        generated, metadata = build.compile_song(source)
        standalone = directory / "tremolo.com"
        standalone.write_bytes(build.assemble(
            generated, metadata["mod_effects"],
            metadata["enhanced_envelopes"], metadata["enhanced_tremolo"],
        ))
        trace_output = baseline.run([str(test_binary), str(standalone)])

        loop_start = p5_symbols["sample_loop"] - COM_ADDRESS
        loop_end = p5_symbols["frame_tick"] - COM_ADDRESS
        loop_hash = hashlib.sha256(
            p5_binary[loop_start:loop_end]
        ).hexdigest()
        floor = envelope_report["v2_sample_rate_floor_hz"]
        enabled = [
            profiles[key] for key in (
                "enabled_empty", "enabled_zero", "enabled_one",
                "enabled_three", "selected_three",
            )
        ]
        selected = {
            "enabled_empty": empty_score,
            "enabled_zero": zero_score,
            "enabled_one": one_score,
            "selected_three": selected_three_score,
        }
        gates = {
            "p5_v1_profile_exact": execution_profile(
                profiles["p5_v1_doomgate"]
            ) == execution_profile(
                envelope_report["v1_compatibility_profile"]
            ),
            "p5_cap1_profile_exact": execution_profile(
                profiles["p5_envelope"]
            ) == execution_profile(profiles["p4_envelope"]),
            "sample_loop_hash_exact": (
                loop_hash == frozen["player"]["sample_loop_sha256"]
            ),
            "player_below_song_window": (
                COM_ADDRESS + len(p5_binary) < SONG_ADDRESS
            ),
            "declared_state_is_51_bytes": (
                p5_symbols["test_manifest"] - p5_symbols["saved_sp"] == 51
            ),
            "enabled_sample_rates_above_floor": all(
                item["effective_sample_hz"] >= floor for item in enabled
            ),
            "enabled_music_clocks_within_one_percent": all(
                abs(profiles[key]["music_frame_hz"] - 50.0) <= 0.5
                for key in selected
            ),
            "phase_table_rates_match_measured_within_one_percent": all(
                abs(profiles[key]["effective_sample_hz"] -
                    score["sample_rate_hz"]) <=
                profiles[key]["effective_sample_hz"] * 0.01
                for key, score in selected.items()
            ),
            "zero_packet_growth": (
                disabled_zero_song.stat().st_size ==
                enabled_zero_song.stat().st_size ==
                one_song.stat().st_size == three_song.stat().st_size
            ),
            "target_trace_exact": "JUKUPOLY-TREMOLO: PASS" in trace_output,
        }
        if not all(gates.values()):
            failed = ", ".join(key for key, value in gates.items() if not value)
            clocks = ", ".join(
                f"{item['label']}={item['music_frame_hz']:.6f}Hz"
                for item in enabled
            )
            raise RuntimeError(
                "JPS v2 tremolo target gate failure: " + failed +
                " (enabled clocks: " + clocks + ")"
            )

        disabled = profiles["disabled_zero"]
        return {
            "schema": "jukupoly-opl-tremolo-target-m4-report-v1",
            "cpu_hz": 1_700_000,
            "status": "synthetic target gates pass; real render and physical A/B pending",
            "frozen_baseline": {
                "path": "OPL-BASELINE.json",
                "envelope_path": "OPL-ENVELOPE-M3.json",
                "sample_loop_sha256": frozen["player"][
                    "sample_loop_sha256"
                ],
                "sample_rate_floor_hz": floor,
            },
            "experimental_player": {
                "build": "library ABI v1+v2 tremolo (-P2=1 -P4=1 -P5=1)",
                "bytes": len(p5_binary),
                "growth_from_envelope_player_bytes": (
                    len(p5_binary) - envelope_report["enhanced_player"]["bytes"]
                ),
                "end_address_exclusive": (
                    f"0x{COM_ADDRESS + len(p5_binary):04x}"
                ),
                "song_window_margin_bytes": SONG_ADDRESS - (
                    COM_ADDRESS + len(p5_binary)
                ),
                "declared_state_region_bytes": (
                    p5_symbols["test_manifest"] - p5_symbols["saved_sp"]
                ),
                "sample_loop_bytes": loop_end - loop_start,
                "sample_loop_sha256": loop_hash,
            },
            "fixture": {
                "frames": 200,
                "frame_samples": source["frame_samples"],
                "disabled_and_enabled_jps_bytes": three_song.stat().st_size,
                "phase_increment": 4850,
                "depths": [0, 1, 2, 3],
                "selected_batches_and_phase_table_rates": {
                    key: {
                        "frame_samples": score["frame_samples"],
                        "phase_table_hz": score["sample_rate_hz"],
                    }
                    for key, score in selected.items()
                },
                "target_trace_test": trace_output.strip(),
            },
            "profiles": profiles,
            "incremental_boundary_cycles_from_cap1_zero": {
                key: delta(
                    profiles[key]["idle_boundary_cycles"],
                    disabled["idle_boundary_cycles"],
                )
                for key in (
                    "enabled_zero", "enabled_one", "enabled_three",
                )
            },
            "gates": gates,
        }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=REPORT)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    result = generate()
    rendered = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.check:
        if not args.output.exists() or args.output.read_text() != rendered:
            raise SystemExit(f"{args.output} is missing or stale")
        action = "checked"
    else:
        args.output.write_text(rendered)
        action = "wrote"
    profile = result["profiles"]["selected_three"]
    print(
        f"JUKUPOLY-TREMOLO-TARGET: {action} {args.output} "
        f"player={result['experimental_player']['bytes']} bytes "
        f"sample={profile['effective_sample_hz']:.1f}Hz "
        f"music={profile['music_frame_hz']:.3f}Hz "
        f"max-frame={profile['frame_cycles']['max']} cycles"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
