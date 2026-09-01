#!/usr/bin/env python3
"""Report selected detuned OPL layers coinciding with spare Juku voices."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import math
import sys
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
FIRMWARE = ROOT / "spinoffs" / "jukupoly" / "firmware"
DEFAULT_REPORT = ROOT / "spinoffs" / "jukupoly" / "OPL-M7-DETUNED-SPARES.json"
TARGET_SAMPLE_RATE = 7_170
KNOWN_PACKS = {
    "04ffbf72e47727b3e93c1e99a68311a460b85fc31fd9a1645e3d872231c0e12a":
        "doom1",
    "3d255c644e52adc2967df8394086d99d7995da71c4adf83bec0fe3bccc51c365":
        "doom2",
}
sys.path.insert(0, str(FIRMWARE))

import build_doom_library as doom_library  # noqa: E402
import import_jukupoly_vgz as vgz  # noqa: E402
import opl_voices  # noqa: E402


def digest(value: object) -> str:
    return hashlib.sha256(json.dumps(
        value, sort_keys=True, separators=(",", ":"), allow_nan=False,
    ).encode()).hexdigest()


def pitch_at_frame(segment: opl_voices.NoteSegment, frame: int) -> float | None:
    result = None
    for point in segment.pitches:
        if opl_voices.analysis_frame(point.sample) > frame:
            break
        result = point.midi_pitch
    return result


def phase_step(pitch: float) -> int:
    frequency = 440.0 * 2.0 ** ((pitch - 69.0) / 12.0)
    return round(frequency * 65536.0 / TARGET_SAMPLE_RATE)


def analyze_track(pack: str, local_track: int, name: str, payload: bytes) -> dict:
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
    notes = opl_voices.group_layers(segments, relations)
    voices, _assignments = opl_voices.assign_logical_voices(notes)
    melodic_notes = set(opl_voices.melodic_logical_note_evidence(
        segments, notes, melodic_keys,
    ))
    score = vgz.compile_score(
        info, writes, Path(name), hashlib.sha256(payload).hexdigest(),
        hashlib.sha256(data).hexdigest(), overrides, {},
        (pack, local_track) in doom_library.ARTICULATION_PRIORITY,
    )
    protected = vgz.score_note_onsets(score) & {
        (opl_voices.analysis_frame(note.start),
         vgz.playable_note(round(note.initial_pitch)))
        for note in notes
        if note.identifier in melodic_notes and note.initial_pitch is not None
    }
    allocation = opl_voices.allocate_three_voices(
        notes, voices, melodic_notes, protected, vgz.playable_note,
    )
    by_note = {note.identifier: note for note in notes}
    by_segment = {segment.identifier: segment for segment in segments}
    decisions = {item["frame"]: item["selected"] for item in allocation["frames"]}
    frames = math.ceil(info.total_samples / opl_voices.ANALYSIS_FRAME)
    current: list[dict] = []
    candidate_notes: set[int] = set()
    candidate_frames = 0
    duplicate_voice_frames = 0
    maximum_detune_cents = 0.0
    maximum_step_spread = 0
    for frame in range(frames):
        if frame in decisions:
            current = decisions[frame]
        spare = 3 - len(current)
        if spare <= 0:
            continue
        frame_candidates = []
        sample = frame * opl_voices.ANALYSIS_FRAME
        for selected in current:
            note = by_note[selected["logical_note"]]
            pitches = [
                pitch_at_frame(by_segment[identifier], frame)
                for identifier in note.members
                if (by_segment[identifier].start <= sample <
                    by_segment[identifier].end)
            ]
            pitches = [pitch for pitch in pitches if pitch is not None]
            if len(pitches) < 2:
                continue
            octave_offset = selected["midi_note"] - round(note.initial_pitch)
            steps = sorted(set(phase_step(pitch + octave_offset)
                               for pitch in pitches))
            base_step = phase_step(
                sum(pitches) / len(pitches) + octave_offset
            )
            variants = [step for step in steps if step != base_step]
            if not variants:
                continue
            candidate_notes.add(note.identifier)
            frame_candidates.extend(variants)
            maximum_detune_cents = max(
                maximum_detune_cents, (max(pitches) - min(pitches)) * 100,
            )
            maximum_step_spread = max(
                maximum_step_spread,
                max((*steps, base_step)) - min((*steps, base_step)),
            )
        if frame_candidates:
            candidate_frames += 1
            duplicate_voice_frames += min(spare, len(frame_candidates))
    return {
        "name": name, "compressed_sha256": hashlib.sha256(payload).hexdigest(),
        "vgm_sha256": hashlib.sha256(data).hexdigest(),
        "duration_frames": frames,
        "selected_detuned_logical_notes": len(candidate_notes),
        "candidate_frames": candidate_frames,
        "duplicate_voice_frames": duplicate_voice_frames,
        "maximum_detune_cents": maximum_detune_cents,
        "maximum_target_step_spread": maximum_step_spread,
        "missed_protected_onsets": allocation["missed_protected_onsets"],
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
    result = {
        "schema": "jukupoly-opl-m7-detuned-spare-report-v1",
        "target_sample_rate_hz": TARGET_SAMPLE_RATE,
        "policy": (
            "analysis only: count selected proven logical layers only when "
            "their member pitches quantize to distinct target phase steps "
            "and the three-voice allocation has spare capacity"
        ),
        "archives": archives,
        "totals": {
            "tracks": len(tracks),
            "candidate_tracks": sum(
                item["duplicate_voice_frames"] > 0 for item in tracks
            ),
            "selected_detuned_logical_notes": sum(
                item["selected_detuned_logical_notes"] for item in tracks
            ),
            "candidate_frames": sum(item["candidate_frames"] for item in tracks),
            "duplicate_voice_frames": sum(
                item["duplicate_voice_frames"] for item in tracks
            ),
            "missed_protected_onsets": sum(
                item["missed_protected_onsets"] for item in tracks
            ),
        },
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
    except (OSError, ValueError, zipfile.BadZipFile, vgz.VgmError) as exc:
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
    totals = result["totals"]
    print(
        f"JUKUPOLY-M7-DETUNED: {action} {output} "
        f"tracks={totals['candidate_tracks']}/{totals['tracks']} "
        f"duplicate-frames={totals['duplicate_voice_frames']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
