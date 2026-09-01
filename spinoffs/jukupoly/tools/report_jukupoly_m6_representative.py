#!/usr/bin/env python3
"""Profile the guarded M6 representative enhanced-score set.

The expensive oracle conversions live under ``out/`` and are intentionally
not source-controlled.  This report pins their source/score hashes, compiles
both v1 controls and enhanced JPS files, and runs every complete score through
C-cosim.  Reference and listening renders remain a later M6 checkpoint.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

import report_jukupoly_baseline as baseline
import report_jukupoly_vibrato_target as target_report


ROOT = Path(__file__).resolve().parents[3]
SPINOFF = ROOT / "spinoffs" / "jukupoly"
FIRMWARE = SPINOFF / "firmware"
DEFAULT_WORK = ROOT / "out" / "jukupoly-m6-representative"
DEFAULT_REPORT = SPINOFF / "OPL-M6-REPRESENTATIVE-PROFILE.json"
sys.path.insert(0, str(FIRMWARE))

import build_jukupoly as build  # noqa: E402
import import_jukupoly_vgz as vgz  # noqa: E402


@dataclass(frozen=True)
class Track:
    label: str
    source_name: str
    score_name: str
    prioritize_articulations: bool = False


TRACKS = (
    Track("doom1-03-imp", "03 The Imp's Song.vgz", "doom1-03-imp.json"),
    Track(
        "doom1-04-dark-halls", "04 Dark Halls.vgz",
        "doom1-04-dark-halls.json", True,
    ),
    Track("doom1-06-suspense", "06 Suspense.vgz", "doom1-06-suspense.json"),
    Track(
        "doom2-10-dave-taylor", "10 The Dave D. Taylor Blues.vgz",
        "doom2-10-dave-taylor.json",
    ),
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def v1_score(source: Path, *, prioritize_articulations: bool) -> dict:
    data, compressed_sha = vgz.decode_source(source)
    info, writes = vgz.parse_vgm(data)
    return vgz.compile_score(
        info, writes, source, compressed_sha, hashlib.sha256(data).hexdigest(),
        set(), {}, prioritize_articulations,
    )


def compile_jps(directory: Path, label: str, score: dict
                ) -> tuple[Path, bytes, dict]:
    generated, metadata = build.compile_song(score)
    payload = build.assemble_song_file(generated, metadata)
    path = directory / f"{label}.jps"
    path.write_bytes(payload)
    return path, payload, metadata


def profile(profiler: Path, player: Path, song: Path, entry: int,
            label: str, prepare: int | None = None) -> dict:
    command = [
        str(profiler), str(player), str(song), f"{entry:x}", label,
    ]
    if prepare is not None:
        command.append(f"{prepare:x}")
    return json.loads(baseline.run(command))


def generate(work: Path) -> dict:
    sources = work / "sources"
    scores = work / "scores"
    songs = work / "songs"
    songs.mkdir(parents=True, exist_ok=True)
    floor = json.loads((SPINOFF / "OPL-ENVELOPE-M3.json").read_text())[
        "v2_sample_rate_floor_hz"
    ]
    frozen = json.loads((SPINOFF / "OPL-BASELINE.json").read_text())

    with tempfile.TemporaryDirectory(prefix="jukupoly-m6-profile.") as name:
        directory = Path(name)
        profiler, _renderer = baseline.build_tools(directory)
        old_player, _listing, old_symbols = baseline.build_player(directory)
        new_player, new_symbols = target_report.build_player(
            directory, "m6-p567", tremolo=True, runtime_vibrato=True,
        )
        player_payload = new_player.read_bytes()
        loop_start = new_symbols["sample_loop"] - baseline.COM_ADDRESS
        loop_end = new_symbols["frame_tick"] - baseline.COM_ADDRESS
        loop_hash = hashlib.sha256(
            player_payload[loop_start:loop_end]
        ).hexdigest()

        records = []
        for item in TRACKS:
            source_path = sources / item.source_name
            score_path = scores / item.score_name
            if not source_path.is_file() or not score_path.is_file():
                raise ValueError(
                    f"missing M6 input for {item.label}: "
                    f"{source_path} or {score_path}"
                )
            enhanced = json.loads(score_path.read_text())
            control = v1_score(
                source_path,
                prioritize_articulations=item.prioritize_articulations,
            )
            old_song, old_payload, old_metadata = compile_jps(
                directory, item.label + "-v1", control,
            )
            old_profile = profile(
                profiler, old_player, old_song,
                old_symbols["player_start"], item.label + "-v1",
            )

            rejected = None
            new_payload = None
            new_metadata = None
            new_profile = None
            try:
                new_song, new_payload, new_metadata = compile_jps(
                    directory, item.label + "-enhanced", enhanced,
                )
                (songs / f"{item.label}.jps").write_bytes(new_payload)
                new_profile = profile(
                    profiler, new_player, new_song,
                    new_symbols["player_start"], item.label + "-enhanced",
                    new_symbols["envelope_dispatch_init"],
                )
            except build.SongError as exc:
                rejected = str(exc)

            conversion = enhanced["conversion"]
            envelope = conversion["enhanced_envelope_fit"]
            allocation = conversion["enhanced_allocation"]
            vibrato = conversion["enhanced_vibrato"]
            source_seconds = conversion["source_duration_seconds"]
            gates = {
                "source_hash_matches": (
                    enhanced["source"]["compressed_sha256"] ==
                    sha256(source_path)
                ),
                "no_protected_onset_regression": (
                    allocation["missed_protected_onsets"] == 0
                ),
                "jps_compiles_below_hard_limit": (
                    new_payload is not None and len(new_payload) < 0x8000
                ),
                "jps_below_soft_limit": (
                    new_payload is not None and len(new_payload) < 30 * 1024
                ),
                "sample_rate_above_shared_floor": (
                    new_profile is not None and
                    new_profile["effective_sample_hz"] >= floor
                ),
                "phase_table_matches_within_one_percent": (
                    new_profile is not None and new_metadata is not None and
                    abs(new_profile["effective_sample_hz"] -
                        new_metadata["target_sample_hz"]) <=
                    new_profile["effective_sample_hz"] * 0.01
                ),
                "music_clock_within_one_percent": (
                    new_profile is not None and
                    abs(new_profile["music_frame_hz"] - 50.0) <= 0.5
                ),
                "duration_within_one_percent": (
                    new_profile is not None and
                    abs(new_profile["duration_seconds"] - source_seconds) <=
                    source_seconds * 0.01
                ),
                "percussion_and_escape_remain_concurrent": (
                    new_profile is not None and new_metadata is not None and
                    new_metadata["descriptors"] > 0 and
                    new_profile["keyboard_polls"] >= new_profile["frames"]
                ),
            }
            enhanced_passed = all(gates.values())
            size_fallback = (
                not enhanced_passed and rejected is not None and
                "library limit is 32767" in rejected and
                len(old_payload) < 30 * 1024 and
                old_metadata["descriptors"] > 0 and
                old_profile["keyboard_polls"] >= old_profile["frames"]
            )
            delivery = {
                "mode": (
                    "enhanced" if enhanced_passed else
                    "unchanged-v1-size-fallback" if size_fallback else
                    "unqualified"
                ),
                "qualified": enhanced_passed or size_fallback,
                "reason": (
                    None if enhanced_passed else
                    rejected if size_fallback else
                    "one or more enhanced gates failed without a qualified "
                    "hard-size fallback"
                ),
                "jps_bytes": (
                    len(new_payload) if enhanced_passed else
                    len(old_payload) if size_fallback else None
                ),
                "jps_sha256": (
                    hashlib.sha256(new_payload).hexdigest()
                    if enhanced_passed and new_payload is not None else
                    hashlib.sha256(old_payload).hexdigest()
                    if size_fallback else None
                ),
            }
            records.append({
                "label": item.label,
                "source": {
                    "name": source_path.name,
                    "sha256": sha256(source_path),
                    "seconds": source_seconds,
                },
                "enhanced_score": {
                    "name": score_path.name,
                    "sha256": sha256(score_path),
                    "bytes": score_path.stat().st_size,
                    "frame_samples": enhanced["frame_samples"],
                    "phase_table_hz": enhanced["sample_rate_hz"],
                },
                "allocation": allocation,
                "envelope_fit": {
                    key: envelope[key] for key in (
                        "selected_logical_notes", "mean_absolute_error",
                        "maximum_error", "direction_mismatches",
                        "tremolo_analysis",
                    )
                },
                "vibrato": vibrato,
                "format": {
                    "v1_jps_bytes": len(old_payload),
                    "v1_jps_sha256": hashlib.sha256(old_payload).hexdigest(),
                    "enhanced_jps_bytes": (
                        None if new_payload is None else len(new_payload)
                    ),
                    "enhanced_jps_sha256": (
                        None if new_payload is None else
                        hashlib.sha256(new_payload).hexdigest()
                    ),
                    "enhanced_capability": (
                        None if new_payload is None else new_payload[7]
                    ),
                    "enhanced_rejection": rejected,
                },
                "profiles": {"v1": old_profile, "enhanced": new_profile},
                "gates": gates,
                "delivery": delivery,
            })

    aggregate = {
        "all_sources_match": all(
            item["gates"]["source_hash_matches"] for item in records
        ),
        "no_protected_onset_regressions": all(
            item["gates"]["no_protected_onset_regression"] for item in records
        ),
        "all_scores_compile_below_hard_limit": all(
            item["gates"]["jps_compiles_below_hard_limit"] for item in records
        ),
        "all_scores_below_soft_limit": all(
            item["gates"]["jps_below_soft_limit"] for item in records
        ),
        "all_runtime_sample_rates_pass": all(
            item["gates"]["sample_rate_above_shared_floor"] for item in records
        ),
        "all_runtime_timing_passes": all(
            item["gates"]["phase_table_matches_within_one_percent"] and
            item["gates"]["music_clock_within_one_percent"] and
            item["gates"]["duration_within_one_percent"]
            for item in records
        ),
        "all_percussion_and_escape_paths_present": all(
            item["gates"]["percussion_and_escape_remain_concurrent"]
            for item in records
        ),
        "sample_loop_hash_exact": (
            loop_hash == frozen["player"]["sample_loop_sha256"]
        ),
        "all_tracks_have_qualified_delivery": all(
            item["delivery"]["qualified"] for item in records
        ),
    }
    return {
        "schema": "jukupoly-opl-m6-representative-profile-v1",
        "status": (
            "representative host conversion and complete C-cosim profile; "
            "failed calibrations remain explicit and renders/physical A/B "
            "are still open"
        ),
        "selection": (
            "Imp, Dark Halls, and Suspense are named by M6; Dave D. Taylor "
            "Blues has the highest v1 percussion-row count (2030) across "
            "both source packs"
        ),
        "shared_sample_rate_floor_hz": floor,
        "player": {
            "bytes": len(player_payload),
            "end_address_exclusive": hex(
                baseline.COM_ADDRESS + len(player_payload)
            ),
            "song_window_margin_bytes": baseline.SONG_ADDRESS - (
                baseline.COM_ADDRESS + len(player_payload)
            ),
            "declared_state_bytes": (
                new_symbols["test_manifest"] - new_symbols["saved_sp"]
            ),
            "sample_loop_sha256": loop_hash,
        },
        "tracks": records,
        "aggregate_gates": aggregate,
        "remaining_gates": [
            "resolve only measured per-capability timing failures",
            "old/new/pinned-Nuked excerpts for all four tracks",
            "complete two-pack enhanced build",
            "physical CS00000 A/B before normal enablement",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--work", type=Path, default=DEFAULT_WORK)
    parser.add_argument("--output", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    try:
        result = generate(args.work)
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
    passed = sum(all(item["gates"].values()) for item in result["tracks"])
    delivered = sum(item["delivery"]["qualified"] for item in result["tracks"])
    print(
        f"JUKUPOLY-M6-REPRESENTATIVE: {action} {args.output} "
        f"enhanced={passed}/{len(result['tracks'])} "
        f"delivered={delivered}/{len(result['tracks'])}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
