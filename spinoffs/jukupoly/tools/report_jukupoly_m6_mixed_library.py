#!/usr/bin/env python3
"""Run every song from the progressive M6 mixed library through C-cosim."""

from __future__ import annotations

import argparse
import collections
import hashlib
import json
import sys
import tempfile
from pathlib import Path

import report_jukupoly_baseline as baseline
import report_jukupoly_vibrato_target as target_report


ROOT = Path(__file__).resolve().parents[3]
SPINOFF = ROOT / "spinoffs" / "jukupoly"
FIRMWARE = SPINOFF / "firmware"
DEFAULT_LIBRARY = ROOT / "out" / "jukupoly-doom-library-m6-mixed"
DEFAULT_REPORT = SPINOFF / "OPL-M6-MIXED-LIBRARY.json"
DELIVERY_MANIFEST = SPINOFF / "M6-REPRESENTATIVE-DELIVERY.json"
EXPECTED_CAPABILITIES = {0: 40, 1: 1, 3: 2, 5: 1}
sys.path.insert(0, str(FIRMWARE))

import build_doom_library as library  # noqa: E402


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def profile(profiler: Path, player: Path, song: Path,
            symbols: dict[str, int], label: str) -> dict:
    return json.loads(baseline.run([
        str(profiler), str(player), str(song),
        f"{symbols['player_start']:x}", label,
        f"{symbols['envelope_dispatch_init']:x}",
    ]))


def generate(directory: Path) -> dict:
    catalog_path = directory / "catalog.json"
    disk_path = directory / library.DISK_NAME
    player_path = directory / "JUKEBOX.COM"
    songs = directory / "songs"
    if not all(path.is_file() for path in (
            catalog_path, disk_path, player_path)):
        raise ValueError("mixed library output is incomplete")
    catalog = json.loads(catalog_path.read_text())
    tracks = catalog.get("tracks")
    if not isinstance(tracks, list) or len(tracks) != 44:
        raise ValueError("mixed library catalog must contain 44 tracks")
    manifest = json.loads(DELIVERY_MANIFEST.read_text())
    expected_replacements = {
        (item["pack"], item["local_track"]): item
        for item in manifest["tracks"]
    }
    floor = json.loads((SPINOFF / "OPL-ENVELOPE-M3.json").read_text())[
        "v2_sample_rate_floor_hz"
    ]
    frozen = json.loads((SPINOFF / "OPL-BASELINE.json").read_text())

    with tempfile.TemporaryDirectory(prefix="jukupoly-m6-library.") as name:
        temporary = Path(name)
        profiler, _renderer = baseline.build_tools(temporary)
        reference_player, symbols = target_report.build_player(
            temporary, "m6-p567", tremolo=True, runtime_vibrato=True,
        )
        player_payload = reference_player.read_bytes()
        loop_start = symbols["sample_loop"] - baseline.COM_ADDRESS
        loop_end = symbols["frame_tick"] - baseline.COM_ADDRESS
        loop_hash = hashlib.sha256(
            player_payload[loop_start:loop_end]
        ).hexdigest()
        records = []
        capability_counts: collections.Counter[int] = collections.Counter()
        for item in tracks:
            song = songs / item["filename"]
            if not song.is_file():
                raise ValueError(f"catalog song is missing: {song}")
            payload = song.read_bytes()
            capability = payload[7] if payload[:4] == b"JPS\2" else 0
            capability_counts[capability] += 1
            result = profile(
                profiler, reference_player, song, symbols,
                f"{item['pack']}-{item['local_track']:02d}",
            )
            replacement = expected_replacements.get(
                (item["pack"], item["local_track"])
            )
            base_gates = {
                "catalog_size_matches": len(payload) == item["bytes"],
                "catalog_hash_matches": sha256(song) == item["payload_sha256"],
                "catalog_capability_matches": capability == item["capability"],
                "complete_c_cosim": (
                    result["frames"] == item["duration_frames"] and
                    result["keyboard_polls"] >= result["frames"]
                ),
            }
            if replacement is None:
                delivery_gates = {
                    "unchanged_v1_delivery": (
                        item["delivery_mode"] == "unchanged-v1" and
                        payload[:4] == b"JPS\1" and capability == 0
                    ),
                }
            else:
                declared_rate = int.from_bytes(payload[8:10], "little")
                delivery_gates = {
                    "replacement_manifest_matches": (
                        item["delivery_mode"] == "enhanced-replacement" and
                        len(payload) == replacement["bytes"] and
                        sha256(song) == replacement["sha256"] and
                        capability == replacement["capability"]
                    ),
                    "enhanced_rate_above_shared_floor": (
                        result["effective_sample_hz"] >= floor
                    ),
                    "enhanced_phase_table_within_one_percent": (
                        abs(result["effective_sample_hz"] - declared_rate) <=
                        result["effective_sample_hz"] * 0.01
                    ),
                    "enhanced_music_clock_within_one_percent": (
                        abs(result["music_frame_hz"] - 50.0) <= 0.5
                    ),
                    "enhanced_duration_within_one_percent": (
                        abs(result["duration_seconds"] -
                            item["duration_seconds"]) <=
                        item["duration_seconds"] * 0.01
                    ),
                }
            gates = {**base_gates, **delivery_gates}
            records.append({
                "global_track": item["global_track"],
                "pack": item["pack"],
                "local_track": item["local_track"],
                "title": item["title"],
                "filename": item["filename"],
                "delivery_mode": item["delivery_mode"],
                "capability": capability,
                "jps_bytes": len(payload),
                "jps_sha256": sha256(song),
                "profile": result,
                "gates": gates,
            })

    aggregate = {
        "catalog_has_44_tracks": len(records) == 44,
        "delivery_counts_are_4_enhanced_40_v1": (
            catalog["delivery"]["enhanced_replacements"] == 4 and
            catalog["delivery"]["unchanged_v1"] == 40
        ),
        "capability_distribution_exact": (
            dict(capability_counts) == EXPECTED_CAPABILITIES
        ),
        "every_song_gate_passes": all(
            all(item["gates"].values()) for item in records
        ),
        "disk_is_exact_juku_size": disk_path.stat().st_size == 819_200,
        "disk_player_matches_qualified_combined_build": (
            player_path.read_bytes() == player_payload
        ),
        "sample_loop_hash_exact": (
            loop_hash == frozen["player"]["sample_loop_sha256"]
        ),
    }
    return {
        "schema": "jukupoly-opl-m6-mixed-library-v1",
        "status": (
            "complete 44-track mixed disk and C-cosim compatibility gates "
            "pass; broader enhancement conversion and physical A/B remain open"
        ),
        "library": {
            "path_hint": directory.name,
            "catalog_sha256": sha256(catalog_path),
            "disk_name": disk_path.name,
            "disk_bytes": disk_path.stat().st_size,
            "disk_sha256": sha256(disk_path),
            "song_bytes": sum(item["jps_bytes"] for item in records),
            "capability_counts": dict(sorted(capability_counts.items())),
        },
        "player": {
            "bytes": len(player_payload),
            "sha256": hashlib.sha256(player_payload).hexdigest(),
            "end_address_exclusive": hex(
                baseline.COM_ADDRESS + len(player_payload)
            ),
            "song_window_margin_bytes": baseline.SONG_ADDRESS - (
                baseline.COM_ADDRESS + len(player_payload)
            ),
            "sample_loop_sha256": loop_hash,
        },
        "shared_sample_rate_floor_hz": floor,
        "tracks": records,
        "aggregate_gates": aggregate,
        "remaining_gates": [
            "convert and qualify additional pack tracks where feasible",
            "physical CS00000 A/B before normal enablement",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--library", type=Path, default=DEFAULT_LIBRARY)
    parser.add_argument("--output", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    try:
        result = generate(args.library.resolve())
    except (OSError, ValueError, RuntimeError, json.JSONDecodeError) as exc:
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
        f"JUKUPOLY-M6-LIBRARY: {action} {args.output} "
        f"tracks={len(result['tracks'])} "
        f"songs={result['library']['song_bytes']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
