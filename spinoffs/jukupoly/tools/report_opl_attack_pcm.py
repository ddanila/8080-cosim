#!/usr/bin/env python3
"""Report structural feasibility of melodic OPL attack PCM on JukuPoly."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import math
import sys
import zipfile
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
FIRMWARE = ROOT / "spinoffs" / "jukupoly" / "firmware"
DEFAULT_REPORT = ROOT / "spinoffs" / "jukupoly" / "OPL-M7-ATTACK-PCM.json"
FRAME_SAMPLES = 141
ATTACK_LENGTHS = (1, 2, 3)
DRUM_FRAMES = {1: 4, 2: 3, 3: 1}
KNOWN_PACKS = {
    "04ffbf72e47727b3e93c1e99a68311a460b85fc31fd9a1645e3d872231c0e12a":
        "doom1",
    "3d255c644e52adc2967df8394086d99d7995da71c4adf83bec0fe3bccc51c365":
        "doom2",
}
sys.path.insert(0, str(FIRMWARE))

import build_doom_library as doom_library  # noqa: E402
import build_jukupoly  # noqa: E402
import import_jukupoly_vgz as vgz  # noqa: E402
import opl_voices  # noqa: E402


def digest(value: object) -> str:
    return hashlib.sha256(json.dumps(
        value, sort_keys=True, separators=(",", ":"), allow_nan=False,
    ).encode()).hexdigest()


def score_events(score: dict) -> tuple[dict[int, dict], set[int]]:
    percussion = {}
    row_starts = set()
    frame = 0
    for row in score["rows"]:
        row_starts.add(frame)
        if "percussion" in row:
            percussion[frame] = row["percussion"]
        frame += row["frames"]
    return percussion, row_starts


def selected_onsets(allocation: dict) -> dict[int, list[dict]]:
    result: dict[int, list[dict]] = defaultdict(list)
    for decision in allocation["frames"]:
        for choice in decision["selected"]:
            if choice["new_onset"]:
                result[decision["frame"]].append(choice)
    return result


def sample_identity(choice: dict, notes: dict[int, opl_voices.LogicalNote]
                    ) -> str:
    note = notes[choice["logical_note"]]
    return digest({
        "patches": note.patches,
        "target_midi_note": choice["midi_note"],
    })[:16]


def schedule_attacks(
        frames: int, length: int, percussion: dict[int, dict],
        onsets: dict[int, list[dict]], row_starts: set[int],
        notes: dict[int, opl_voices.LogicalNote], base_jps_bytes: int,
) -> dict:
    pcm_remaining = 0
    scheduled = 0
    percussion_conflicts = 0
    attack_tail_conflicts = 0
    additional_concurrent_onsets = 0
    split_rows = 0
    identities = set()
    for frame in range(frames):
        drum_started = percussion.get(frame)
        if drum_started is not None:
            pcm_remaining = DRUM_FRAMES[drum_started["sample"]]
        choices = onsets.get(frame, [])
        if choices:
            additional_concurrent_onsets += max(0, len(choices) - 1)
            if pcm_remaining:
                percussion_conflicts += 1 if drum_started else 0
                attack_tail_conflicts += 0 if drum_started else 1
            elif any(next_frame in percussion
                     for next_frame in range(frame + 1, frame + length)):
                percussion_conflicts += 1
            else:
                choice = max(choices, key=lambda item: (
                    item["protected_onset"], item["attack_rate"],
                    item["level_8bit"], -item["logical_note"],
                ))
                identities.add(sample_identity(choice, notes))
                scheduled += 1
                split_rows += int(frame not in row_starts)
                pcm_remaining = length
        pcm_remaining = max(0, pcm_remaining - 1)
    sample_bytes = len(identities) * length * FRAME_SAMPLES
    projected_jps = (
        base_jps_bytes + sample_bytes + len(identities) * 3 +
        scheduled * 2 + split_rows * 2
    )
    onset_frames = len(onsets)
    return {
        "attack_frames": length,
        "attack_milliseconds": length * 20,
        "selected_onset_frames": onset_frames,
        "scheduled_attack_frames": scheduled,
        "coverage_percent": (
            scheduled * 100.0 / onset_frames if onset_frames else 0.0
        ),
        "percussion_conflict_frames": percussion_conflicts,
        "prior_attack_tail_conflict_frames": attack_tail_conflicts,
        "additional_concurrent_selected_onsets": additional_concurrent_onsets,
        "unique_patch_pitch_samples": len(identities),
        "sample_id_limit_pass": len(identities) <= 96,
        "projected_attack_pcm_bytes": sample_bytes,
        "projected_jps_bytes": projected_jps,
        "soft_size_limit_pass": projected_jps < 30 * 1024,
        "hard_size_limit_pass": projected_jps < 32_768,
    }


def analyze_track(pack: str, local_track: int, name: str, payload: bytes
                  ) -> dict:
    data = gzip.decompress(payload)
    info, writes = vgz.parse_vgm(data)
    events, counts = vgz.key_events(writes, info)
    melodic = vgz.melodic_signatures(events, counts)
    signatures = {vgz.signature_id(signature): signature for signature in counts}
    overrides = doom_library.MELODIC_OVERRIDES.get((pack, local_track), set())
    melodic.update(signatures[identifier] for identifier in overrides)
    melodic_keys = {
        (event.start, event.bank, event.channel) for event in events
        if event.signature in melodic
    }
    segments = opl_voices.reconstruct_segments(
        writes, info.banks, info.total_samples, info.clock,
        info.frequency_divider,
    )
    relations = opl_voices.candidate_relations(segments)
    logical_notes = opl_voices.group_layers(segments, relations)
    voices, _assignments = opl_voices.assign_logical_voices(logical_notes)
    melodic_notes = set(opl_voices.melodic_logical_note_evidence(
        segments, logical_notes, melodic_keys,
    ))
    score = vgz.compile_score(
        info, writes, Path(name), hashlib.sha256(payload).hexdigest(),
        hashlib.sha256(data).hexdigest(), overrides, {},
        (pack, local_track) in doom_library.ARTICULATION_PRIORITY,
    )
    protected = vgz.score_note_onsets(score) & {
        (opl_voices.analysis_frame(note.start),
         vgz.playable_note(round(note.initial_pitch)))
        for note in logical_notes
        if note.identifier in melodic_notes and note.initial_pitch is not None
    }
    allocation = opl_voices.allocate_three_voices(
        logical_notes, voices, melodic_notes, protected, vgz.playable_note,
    )
    generated, metadata = build_jukupoly.compile_song(score)
    base_jps_bytes = len(build_jukupoly.assemble_song_file(generated, metadata))
    percussion, row_starts = score_events(score)
    onsets = selected_onsets(allocation)
    frames = math.ceil(info.total_samples / opl_voices.ANALYSIS_FRAME)
    notes = {note.identifier: note for note in logical_notes}
    return {
        "name": name,
        "compressed_sha256": hashlib.sha256(payload).hexdigest(),
        "vgm_sha256": hashlib.sha256(data).hexdigest(),
        "duration_frames": frames,
        "base_v1_jps_bytes": base_jps_bytes,
        "percussion_trigger_frames": len(percussion),
        "selected_onsets": sum(len(items) for items in onsets.values()),
        "missed_protected_onsets": allocation["missed_protected_onsets"],
        "candidates": [
            schedule_attacks(
                frames, length, percussion, onsets, row_starts, notes,
                base_jps_bytes,
            )
            for length in ATTACK_LENGTHS
        ],
    }


def generate(paths: list[Path]) -> dict:
    archives = []
    for path in paths:
        archive_hash = hashlib.sha256(path.read_bytes()).hexdigest()
        pack = KNOWN_PACKS.get(archive_hash)
        if pack is None:
            raise ValueError(f"unrecognized archive hash: {path}")
        with zipfile.ZipFile(path) as source:
            names = sorted(
                name for name in source.namelist()
                if name.lower().endswith(".vgz") and "/" not in name
            )
            tracks = [
                analyze_track(pack, index, name, source.read(name))
                for index, name in enumerate(names, 1)
            ]
        archives.append({
            "pack": pack, "name": path.name, "sha256": archive_hash,
            "tracks": tracks,
        })
    tracks = [track for archive in archives for track in archive["tracks"]]
    totals = {}
    for candidate_index, length in enumerate(ATTACK_LENGTHS):
        candidates = [track["candidates"][candidate_index] for track in tracks]
        selected_frames = sum(item["selected_onset_frames"] for item in candidates)
        scheduled = sum(item["scheduled_attack_frames"] for item in candidates)
        totals[str(length)] = {
            "attack_frames": length,
            "attack_milliseconds": length * 20,
            "selected_onset_frames": selected_frames,
            "scheduled_attack_frames": scheduled,
            "coverage_percent": (
                scheduled * 100.0 / selected_frames if selected_frames else 0.0
            ),
            "percussion_conflict_frames": sum(
                item["percussion_conflict_frames"] for item in candidates
            ),
            "prior_attack_tail_conflict_frames": sum(
                item["prior_attack_tail_conflict_frames"]
                for item in candidates
            ),
            "additional_concurrent_selected_onsets": sum(
                item["additional_concurrent_selected_onsets"]
                for item in candidates
            ),
            "tracks_with_no_schedulable_attack": sum(
                item["scheduled_attack_frames"] == 0 for item in candidates
            ),
            "tracks_over_sample_id_limit": sum(
                not item["sample_id_limit_pass"] for item in candidates
            ),
            "tracks_over_soft_size_limit": sum(
                not item["soft_size_limit_pass"] for item in candidates
            ),
            "tracks_over_hard_size_limit": sum(
                not item["hard_size_limit_pass"] for item in candidates
            ),
            "tracks_passing_id_and_hard_size_limits": sum(
                item["sample_id_limit_pass"] and
                item["hard_size_limit_pass"] for item in candidates
            ),
        }
    result = {
        "schema": "jukupoly-opl-m7-attack-pcm-feasibility-v1",
        "frame_samples": FRAME_SAMPLES,
        "sample_ids_available": 96,
        "tracks": len(tracks),
        "missed_protected_onsets": sum(
            track["missed_protected_onsets"] for track in tracks
        ),
        "policy": (
            "structural upper bound only: preserve existing percussion, "
            "allow one non-overlapping fixed-pitch PCM attack at a selected "
            "onset, and require a distinct sample for each source patch plus "
            "folded target pitch; no PCM is synthesized or emitted"
        ),
        "projection": (
            "projected JPS adds one raw u4 byte per attack sample point, one "
            "three-byte descriptor per unique patch/pitch, one two-byte row "
            "pointer per scheduled attack, and a two-byte row header when an "
            "onset is not already a v1 row boundary"
        ),
        "archives": archives,
        "totals_by_attack_frames": totals,
    }
    result["report_sha256"] = digest(result)
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("archives", nargs="+", type=Path)
    parser.add_argument("--output", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    try:
        result = generate([path.resolve() for path in args.archives])
    except (OSError, ValueError, zipfile.BadZipFile, vgz.VgmError,
            build_jukupoly.SongError) as exc:
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
    totals = result["totals_by_attack_frames"]["1"]
    print(
        f"JUKUPOLY-M7-ATTACK-PCM: {action} {output} "
        f"one-frame={totals['scheduled_attack_frames']}/"
        f"{totals['selected_onset_frames']} "
        f"hard-size-fail={totals['tracks_over_hard_size_limit']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
