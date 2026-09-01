#!/usr/bin/env python3
"""Build and profile bounded 30-second re-articulation scans for both packs."""

from __future__ import annotations

import argparse
import concurrent.futures
import hashlib
import json
import subprocess
import sys
import tempfile
import zipfile
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
SPINOFF = ROOT / "spinoffs" / "jukupoly"
FIRMWARE = SPINOFF / "firmware"
IMPORTER = FIRMWARE / "import_jukupoly_vgz.py"
DEFAULT_WORK = ROOT / "out" / "jukupoly-m7-pack-scan"
DEFAULT_REPORT = SPINOFF / "OPL-M7-PACK-SCAN.json"
ARCHIVE_HASHES = {
    "doom1": "04ffbf72e47727b3e93c1e99a68311a460b85fc31fd9a1645e3d872231c0e12a",
    "doom2": "3d255c644e52adc2967df8394086d99d7995da71c4adf83bec0fe3bccc51c365",
}
EXPECTED_TRACKS = {"doom1": 23, "doom2": 21}
MELODIC_OVERRIDES = {
    ("doom1", 1): ("d357f6e830b6", "22c93b76b58b", "514d6277991a"),
}
ARTICULATION_PRIORITY = {("doom1", 4)}
sys.path.insert(0, str(FIRMWARE))
sys.path.insert(0, str(SPINOFF / "tools"))

import build_jukupoly as build  # noqa: E402
import report_jukupoly_baseline as baseline  # noqa: E402
import report_jukupoly_envelope as envelope_report  # noqa: E402


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def extract(pack: str, archive: Path, destination: Path) -> list[dict]:
    result = []
    with zipfile.ZipFile(archive) as source:
        names = sorted(
            name for name in source.namelist()
            if Path(name).suffix.lower() == ".vgz" and "/" not in name
        )
        if len(names) != EXPECTED_TRACKS[pack]:
            raise ValueError(
                f"{archive.name} has {len(names)} VGZ tracks, expected "
                f"{EXPECTED_TRACKS[pack]}"
            )
        for name in names:
            local_track = int(name[:2])
            path = destination / f"{pack}-{name}"
            path.write_bytes(source.read(name))
            result.append({
                "pack": pack, "local_track": local_track,
                "source_name": name, "path": path,
                "label": f"{pack}-{local_track:02d}",
            })
    return result


def convert(item: dict, scores: Path, oracle: Path) -> str:
    output = scores / f"{item['label']}.json"
    command = [
        sys.executable, str(IMPORTER), str(item["path"]), str(output),
        "--seconds", "30", "--enhanced-envelopes",
        "--enhanced-rearticulation", "--enhanced-frame-samples", "143",
        "--enhanced-sample-rate", "7170", "--opl-oracle", str(oracle),
    ]
    for identifier in MELODIC_OVERRIDES.get(
            (item["pack"], item["local_track"]), ()):
        command.extend(("--melodic-signature", identifier))
    if (item["pack"], item["local_track"]) in ARTICULATION_PRIORITY:
        command.append("--prioritize-articulations")
    completed = subprocess.run(
        command, cwd=ROOT, check=True, text=True, stdout=subprocess.PIPE,
    )
    return completed.stdout.strip()


def report(items: list[dict], work: Path) -> dict:
    frozen = json.loads(baseline.BASELINE.read_text())
    floor = json.loads((SPINOFF / "OPL-ENVELOPE-M3.json").read_text())[
        "v2_sample_rate_floor_hz"
    ]
    with tempfile.TemporaryDirectory(prefix="jukupoly-m7-pack-profile.") as name:
        directory = Path(name)
        profiler, _renderer = baseline.build_tools(directory)
        player, symbols = envelope_report.build_enhanced_player(directory)
        player_data = player.read_bytes()
        loop_start = symbols["sample_loop"] - baseline.COM_ADDRESS
        loop_end = symbols["frame_tick"] - baseline.COM_ADDRESS
        loop_hash = hashlib.sha256(player_data[loop_start:loop_end]).hexdigest()
        records = []
        for item in items:
            score_path = work / "scores" / f"{item['label']}.json"
            score = json.loads(score_path.read_text())
            generated, metadata = build.compile_song(score)
            payload = build.assemble_song_file(generated, metadata)
            song_path = directory / f"{item['label']}.jps"
            song_path.write_bytes(payload)
            profile = envelope_report.enhanced_profile(
                profiler, player, song_path, symbols, item["label"],
            )
            fit = score["conversion"]["enhanced_envelope_fit"]
            allocation = score["conversion"]["enhanced_allocation"]
            articulated = [
                note for note in fit["notes"]
                if note.get("articulation_packets")
            ]
            source_seconds = score["conversion"]["source_duration_seconds"]
            gates = {
                "source_hash_matches": score["source"]["compressed_sha256"] ==
                sha256(item["path"]),
                "no_protected_onset_regression":
                allocation["missed_protected_onsets"] == 0,
                "no_unrepresentable_rearticulations":
                fit["unrepresentable_rearticulation_notes"] == 0,
                "jps_below_soft_limit": len(payload) < 30 * 1024,
                "jps_below_hard_limit": len(payload) < 32_768,
                "sample_rate_above_shared_floor":
                profile["effective_sample_hz"] >= floor,
                "music_clock_within_one_percent":
                abs(profile["music_frame_hz"] - 50.0) <= 0.5,
                "duration_within_one_percent":
                abs(profile["duration_seconds"] - source_seconds) <=
                source_seconds * 0.01,
                "escape_polling_present":
                profile["keyboard_polls"] >= profile["frames"],
            }
            records.append({
                "label": item["label"], "pack": item["pack"],
                "local_track": item["local_track"],
                "source_name": item["source_name"],
                "source_sha256": sha256(item["path"]),
                "score_sha256": sha256(score_path),
                "source_seconds": source_seconds,
                "selected_logical_notes": fit["selected_logical_notes"],
                "notes_with_significant_rearticulation": sum(
                    note["significant_rearticulations"] > 0
                    for note in fit["notes"]
                ),
                "articulated_notes": len(articulated),
                "emitted_rearticulation_packets":
                fit["rearticulation"]["emitted_packets"],
                "unrepresentable_rearticulation_notes":
                fit["unrepresentable_rearticulation_notes"],
                "single_packet_sample_weighted_mae":
                fit["single_packet_sample_weighted_mean_absolute_error"],
                "articulated_sample_weighted_mae":
                fit["sample_weighted_mean_absolute_error"],
                "maximum_error": fit["maximum_error"],
                "jps_bytes": len(payload),
                "percussion_descriptors": metadata["descriptors"],
                "jps_sha256": hashlib.sha256(payload).hexdigest(),
                "profile": profile,
                "gates": gates,
            })
    beneficial = [
        item for item in records
        if item["emitted_rearticulation_packets"] > 0
    ]
    return {
        "schema": "jukupoly-opl-m7-pack-scan-v1",
        "scope": (
            "first 30 seconds (or complete shorter source), envelope-only "
            "bounded re-articulation; candidate discovery, not delivery"
        ),
        "archives": {
            pack: {"sha256": ARCHIVE_HASHES[pack],
                   "tracks": EXPECTED_TRACKS[pack]}
            for pack in sorted(ARCHIVE_HASHES)
        },
        "player": {
            "bytes": len(player_data),
            "end_address_exclusive": hex(
                baseline.COM_ADDRESS + len(player_data)
            ),
            "sample_loop_sha256": loop_hash,
            "sample_loop_hash_exact":
                loop_hash == frozen["player"]["sample_loop_sha256"],
        },
        "summary": {
            "tracks": len(records),
            "tracks_with_emitted_rearticulation": len(beneficial),
            "emitted_packets": sum(
                item["emitted_rearticulation_packets"] for item in records
            ),
            "unrepresentable_notes": sum(
                item["unrepresentable_rearticulation_notes"]
                for item in records
            ),
            "all_tracks_pass": all(
                all(item["gates"].values()) for item in records
            ),
            "failed_gate_counts": dict(sorted(Counter(
                key for item in records for key, value in item["gates"].items()
                if not value
            ).items())),
        },
        "tracks": records,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--doom", type=Path, required=True)
    parser.add_argument("--doom2", type=Path, required=True)
    parser.add_argument("--opl-oracle", type=Path, required=True)
    parser.add_argument("--work", type=Path, default=DEFAULT_WORK)
    parser.add_argument("--output", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--jobs", type=int, default=8)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    archives = {"doom1": args.doom.resolve(), "doom2": args.doom2.resolve()}
    for pack, archive in archives.items():
        if not archive.is_file() or sha256(archive) != ARCHIVE_HASHES[pack]:
            parser.error(f"missing or hash-mismatched {pack} archive: {archive}")
    oracle = args.opl_oracle.resolve()
    if not oracle.is_file():
        parser.error(f"OPL oracle is missing: {oracle}")
    if not 1 <= args.jobs <= 12:
        parser.error("--jobs must be 1..12")
    work = args.work.resolve()
    sources, scores = work / "sources", work / "scores"
    sources.mkdir(parents=True, exist_ok=True)
    scores.mkdir(parents=True, exist_ok=True)
    try:
        items = []
        for pack, archive in archives.items():
            items.extend(extract(pack, archive, sources))
        if not args.check:
            with concurrent.futures.ThreadPoolExecutor(
                    max_workers=args.jobs) as executor:
                futures = [
                    executor.submit(convert, item, scores, oracle)
                    for item in items
                ]
                for future in concurrent.futures.as_completed(futures):
                    print(future.result())
        result = report(items, work)
    except (OSError, ValueError, subprocess.CalledProcessError) as exc:
        parser.error(str(exc))
    rendered = json.dumps(result, indent=2, sort_keys=True) + "\n"
    output = args.output.resolve()
    if args.check:
        if output.read_text() != rendered:
            raise SystemExit(f"{output} is missing or stale")
        action = "checked"
    else:
        output.write_text(rendered)
        action = "wrote"
    print(
        f"JUKUPOLY-M7-PACK-SCAN: {action} {output} "
        f"tracks={result['summary']['tracks']} "
        f"articulated={result['summary']['tracks_with_emitted_rearticulation']} "
        f"packets={result['summary']['emitted_packets']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
