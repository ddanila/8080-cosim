#!/usr/bin/env python3
"""Measure the real 30-second Imp JPS v1/v2/oracle M3 checkpoint."""

from __future__ import annotations

import argparse
import hashlib
import json
import tempfile
from pathlib import Path

import report_jukupoly_baseline as baseline
import report_jukupoly_envelope as envelope_report


ROOT = Path(__file__).resolve().parents[3]
SPINOFF = ROOT / "spinoffs" / "jukupoly"
FIRMWARE = SPINOFF / "firmware"
DEFAULT_V1 = FIRMWARE / "jukupoly-imp-30s-v1.json"
DEFAULT_V2 = FIRMWARE / "jukupoly-imp-30s-v2.json"
DEFAULT_REPORT = SPINOFF / "OPL-IMP-M3.json"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def first_tone_frame(score: dict) -> int | None:
    frame = 0
    for row in score["rows"]:
        if any(field in row for field in ("tone1", "tone2", "tone3")):
            return frame
        frame += row["frames"]
    return None


def build_score(directory: Path, label: str, score_path: Path
                ) -> tuple[Path, Path]:
    standalone = directory / f"{label}.com"
    song = directory / f"{label}.jps"
    baseline.run([
        "python3", str(FIRMWARE / "build_jukupoly.py"),
        "--song", str(score_path),
        "--generated", str(directory / f"{label}.inc"),
        "--output", str(standalone), "--song-output", str(song),
    ])
    return standalone, song


def generate(v1_path: Path, v2_path: Path,
             oracle_reference: Path | None) -> dict:
    v1_score = json.loads(v1_path.read_text())
    v2_score = json.loads(v2_path.read_text())
    if v1_score["schema"] != "jukupoly-song-v1":
        raise ValueError("v1 score has the wrong schema")
    if v2_score["schema"] != "jukupoly-song-v2":
        raise ValueError("v2 score has the wrong schema")
    if v1_score["source"]["vgm_sha256"] != v2_score["source"]["vgm_sha256"]:
        raise ValueError("v1 and v2 scores do not identify the same VGM")
    if oracle_reference is not None and not oracle_reference.is_file():
        raise ValueError(f"oracle reference is missing: {oracle_reference}")

    frozen = json.loads(baseline.BASELINE.read_text())
    fit = v2_score["conversion"]["enhanced_envelope_fit"]
    allocation = v2_score["conversion"]["enhanced_allocation"]
    with tempfile.TemporaryDirectory(prefix="jukupoly-imp-m3-report.") as name:
        directory = Path(name)
        profiler, renderer = baseline.build_tools(directory)
        player, symbols = envelope_report.build_enhanced_player(directory)
        player_bytes = player.read_bytes()
        loop_start = symbols["sample_loop"] - baseline.COM_ADDRESS
        loop_end = symbols["frame_tick"] - baseline.COM_ADDRESS
        loop_hash = hashlib.sha256(
            player_bytes[loop_start:loop_end]
        ).hexdigest()

        images = {}
        songs = {}
        profiles = {}
        wavs = {}
        for label, path in (("v1", v1_path), ("v2", v2_path)):
            images[label], songs[label] = build_score(directory, label, path)
            profiles[label] = envelope_report.enhanced_profile(
                profiler, player, songs[label], symbols, f"imp-30s-{label}",
            )
            wav = directory / f"{label}.wav"
            baseline.run([
                str(renderer), "--sample-rate", "48000", "--lead", "0",
                "--tail", "0", str(images[label]), str(wav),
            ])
            wavs[label] = {
                "sample_rate_hz": 48_000,
                "bytes": wav.stat().st_size,
                "sha256": sha256(wav),
            }

    source_seconds = v2_score["conversion"]["duration_seconds"]
    v1_floor = profiles["v1"]["effective_sample_hz"] * 0.9
    gates = {
        "same_source_vgm": (
            v1_score["source"]["vgm_sha256"] ==
            v2_score["source"]["vgm_sha256"]
        ),
        "v1_first_tone_at_14_12_seconds": first_tone_frame(v1_score) == 706,
        "v2_intro_tone_at_frame_zero": first_tone_frame(v2_score) == 0,
        "v2_intro_envelope_not_constant": (
            fit["notes"][0]["packet"]["peak_level"] !=
            fit["notes"][0]["packet"]["sustain_level"] or
            fit["notes"][0]["packet"]["attack_period_frames"] != 0
        ),
        "no_protected_onset_regression": (
            allocation["missed_protected_onsets"] == 0
        ),
        "envelope_directions_match": fit["direction_mismatches"] == 0,
        "sample_loop_hash_exact": (
            loop_hash == frozen["player"]["sample_loop_sha256"]
        ),
        "v2_sample_rate_above_fixture_floor": (
            profiles["v2"]["effective_sample_hz"] >= v1_floor
        ),
        "v2_duration_within_one_percent": (
            abs(profiles["v2"]["duration_seconds"] - source_seconds) <=
            source_seconds * 0.01
        ),
        "v2_music_clock_within_one_percent": (
            abs(profiles["v2"]["music_frame_hz"] - 50.0) <= 0.5
        ),
        "player_below_song_window": (
            baseline.COM_ADDRESS + len(player_bytes) < baseline.SONG_ADDRESS
        ),
        "v2_jps_below_soft_limit": profiles["v2"]["jps_bytes"] < 30 * 1024,
    }
    if not all(gates.values()):
        failed = ", ".join(key for key, value in gates.items() if not value)
        raise RuntimeError("Imp M3 gate failure: " + failed)

    reference = None
    if oracle_reference is not None:
        reference = {
            "path_hint": oracle_reference.name,
            "bytes": oracle_reference.stat().st_size,
            "sha256": sha256(oracle_reference),
        }
    return {
        "schema": "jukupoly-opl-imp-m3-report-v1",
        "source": {
            "name": v2_score["source"]["name"],
            "vgm_sha256": v2_score["source"]["vgm_sha256"],
            "excerpt_seconds": source_seconds,
        },
        "player": {
            "bytes": len(player_bytes),
            "end_address_exclusive": hex(
                baseline.COM_ADDRESS + len(player_bytes)
            ),
            "sample_loop_sha256": loop_hash,
        },
        "first_tone_frame": {
            "v1": first_tone_frame(v1_score),
            "v2": first_tone_frame(v2_score),
        },
        "allocation": allocation,
        "envelope_fit": fit,
        "profiles": profiles,
        "fixture_sample_rate_floor_hz": v1_floor,
        "target_wavs": wavs,
        "opl_reference_wav": reference,
        "gates": gates,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--v1", type=Path, default=DEFAULT_V1)
    parser.add_argument("--v2", type=Path, default=DEFAULT_V2)
    parser.add_argument("--oracle-reference", type=Path)
    parser.add_argument("--output", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    try:
        result = generate(args.v1, args.v2, args.oracle_reference)
    except (OSError, ValueError, RuntimeError) as exc:
        parser.error(str(exc))
    rendered = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.check:
        if args.oracle_reference is not None:
            parser.error("--check uses the committed report's reference hash")
        committed = json.loads(args.output.read_text())
        result["opl_reference_wav"] = committed["opl_reference_wav"]
        rendered = json.dumps(result, indent=2, sort_keys=True) + "\n"
        if args.output.read_text() != rendered:
            raise SystemExit(f"{args.output} is missing or stale")
        action = "checked"
    else:
        args.output.write_text(rendered)
        action = "wrote"
    print(
        f"JUKUPOLY-IMP-M3: {action} {args.output} "
        f"first={result['first_tone_frame']['v1']}->"
        f"{result['first_tone_frame']['v2']} "
        f"sample={result['profiles']['v2']['effective_sample_hz']:.1f}Hz "
        f"duration={result['profiles']['v2']['duration_seconds']:.3f}s"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
