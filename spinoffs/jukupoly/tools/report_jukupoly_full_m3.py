#!/usr/bin/env python3
"""Record a compact full-song JPS v1/v2 M3 feasibility report."""

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
DEFAULT_REPORT = SPINOFF / "OPL-IMP-FULL-M3.json"


def digest(value: object) -> str:
    return hashlib.sha256(json.dumps(
        value, sort_keys=True, separators=(",", ":"), allow_nan=False,
    ).encode()).hexdigest()


def file_digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build_score(directory: Path, label: str, source: Path
                ) -> tuple[Path, Path]:
    standalone = directory / f"{label}.com"
    song = directory / f"{label}.jps"
    baseline.run([
        "python3", str(FIRMWARE / "build_jukupoly.py"),
        "--song", str(source), "--generated", str(directory / f"{label}.inc"),
        "--output", str(standalone), "--song-output", str(song),
    ])
    return standalone, song


def generate(v1_path: Path, v2_path: Path,
             conversion_seconds: float | None) -> dict:
    v1 = json.loads(v1_path.read_text())
    v2 = json.loads(v2_path.read_text())
    if v1["schema"] != "jukupoly-song-v1" or v2["schema"] != "jukupoly-song-v2":
        raise ValueError("expected one JukuPoly v1 and one v2 score")
    if v1["source"]["vgm_sha256"] != v2["source"]["vgm_sha256"]:
        raise ValueError("scores do not identify the same source VGM")
    fit = v2["conversion"]["enhanced_envelope_fit"]
    allocation = v2["conversion"]["enhanced_allocation"]
    source_seconds = v2["conversion"].get(
        "source_duration_seconds",
        v1["conversion"]["duration_seconds"],
    )
    frozen = json.loads(baseline.BASELINE.read_text())

    with tempfile.TemporaryDirectory(prefix="jukupoly-full-m3.") as name:
        directory = Path(name)
        profiler, _renderer = baseline.build_tools(directory)
        player, symbols = envelope_report.build_enhanced_player(directory)
        player_data = player.read_bytes()
        loop_start = symbols["sample_loop"] - baseline.COM_ADDRESS
        loop_end = symbols["frame_tick"] - baseline.COM_ADDRESS
        loop_hash = hashlib.sha256(
            player_data[loop_start:loop_end]
        ).hexdigest()
        profiles = {}
        jps = {}
        for label, source in (("v1", v1_path), ("v2", v2_path)):
            _standalone, song = build_score(directory, label, source)
            profiles[label] = envelope_report.enhanced_profile(
                profiler, player, song, symbols, f"full-song-{label}",
            )
            jps[label] = {
                "bytes": song.stat().st_size,
                "sha256": file_digest(song),
            }

    floor = profiles["v1"]["effective_sample_hz"] * 0.9
    gates = {
        "same_source_vgm": (
            v1["source"]["vgm_sha256"] == v2["source"]["vgm_sha256"]
        ),
        "no_protected_onset_regression": (
            allocation["missed_protected_onsets"] == 0
        ),
        "significant_envelope_directions_match": (
            fit["direction_mismatches"] == 0
        ),
        "sample_loop_hash_exact": (
            loop_hash == frozen["player"]["sample_loop_sha256"]
        ),
        "v2_sample_rate_above_fixture_floor": (
            profiles["v2"]["effective_sample_hz"] >= floor
        ),
        "v2_duration_within_one_percent": (
            abs(profiles["v2"]["duration_seconds"] - source_seconds) <=
            source_seconds * 0.01
        ),
        "v2_music_clock_within_one_percent": (
            abs(profiles["v2"]["music_frame_hz"] - 50.0) <= 0.5
        ),
        "player_below_song_window": (
            baseline.COM_ADDRESS + len(player_data) < baseline.SONG_ADDRESS
        ),
        "v2_jps_below_soft_limit": jps["v2"]["bytes"] < 30 * 1024,
        "v2_jps_below_hard_limit": jps["v2"]["bytes"] < 32_768,
    }
    if not all(gates.values()):
        failed = ", ".join(key for key, value in gates.items() if not value)
        raise RuntimeError("full-song M3 gate failure: " + failed)
    return {
        "schema": "jukupoly-opl-full-song-m3-report-v1",
        "source": {
            "name": v2["source"]["name"],
            "vgm_sha256": v2["source"]["vgm_sha256"],
            "duration_seconds": source_seconds,
            "frames": v2["conversion"]["duration_frames"],
        },
        "host_conversion": {
            "measured_wall_seconds": conversion_seconds,
            "v1_score_sha256": file_digest(v1_path),
            "v2_score_sha256": file_digest(v2_path),
        },
        "player": {
            "bytes": len(player_data),
            "end_address_exclusive": hex(
                baseline.COM_ADDRESS + len(player_data)
            ),
            "sample_loop_sha256": loop_hash,
        },
        "allocation": allocation,
        "envelope_fit": {
            key: fit[key] for key in (
                "selected_logical_notes", "mean_absolute_error",
                "maximum_error", "direction_mismatches",
            )
        } | {"note_measurements_sha256": digest(fit["notes"])},
        "jps": jps,
        "profiles": profiles,
        "fixture_sample_rate_floor_hz": floor,
        "gates": gates,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("v1", type=Path)
    parser.add_argument("v2", type=Path)
    parser.add_argument("--conversion-seconds", type=float)
    parser.add_argument("--output", type=Path, default=DEFAULT_REPORT)
    args = parser.parse_args()
    try:
        result = generate(args.v1, args.v2, args.conversion_seconds)
    except (OSError, ValueError, RuntimeError) as exc:
        parser.error(str(exc))
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    profile = result["profiles"]["v2"]
    print(
        f"JUKUPOLY-FULL-M3: wrote {args.output} "
        f"jps={result['jps']['v2']['bytes']} "
        f"sample={profile['effective_sample_hz']:.1f}Hz "
        f"duration={profile['duration_seconds']:.3f}s"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
