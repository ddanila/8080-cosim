#!/usr/bin/env python3
"""Report deterministic M2 logical-voice evidence for VGM pack archives."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import sys
import zipfile
from dataclasses import asdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
FIRMWARE = ROOT / "spinoffs" / "jukupoly" / "firmware"
sys.path.insert(0, str(FIRMWARE))

import import_jukupoly_vgz as vgz  # noqa: E402
import build_doom_library as doom_library  # noqa: E402
import opl_voices  # noqa: E402


KNOWN_PACKS = {
    "04ffbf72e47727b3e93c1e99a68311a460b85fc31fd9a1645e3d872231c0e12a":
        "doom1",
    "3d255c644e52adc2967df8394086d99d7995da71c4adf83bec0fe3bccc51c365":
        "doom2",
}


def digest(value: object) -> str:
    encoded = json.dumps(
        value, sort_keys=True, separators=(",", ":"), allow_nan=False,
    ).encode()
    return hashlib.sha256(encoded).hexdigest()


def analyze_track(name: str, payload: bytes,
                  melodic_overrides: set[str] | None = None,
                  prioritize_articulations: bool = False) -> dict:
    try:
        data = gzip.decompress(payload)
    except (EOFError, OSError) as exc:
        raise ValueError(f"{name}: invalid VGZ stream: {exc}") from exc
    info, writes = vgz.parse_vgm(data)
    overrides = melodic_overrides or set()
    events, counts = vgz.key_events(writes, info)
    melodic = vgz.melodic_signatures(events, counts)
    signatures = {vgz.signature_id(signature): signature for signature in counts}
    unknown = sorted(overrides - set(signatures))
    if unknown:
        raise ValueError(f"{name}: unknown melodic overrides: {unknown}")
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
    logical_voices, assignments = opl_voices.assign_logical_voices(logical_notes)
    melodic_evidence = opl_voices.melodic_logical_note_evidence(
        segments, logical_notes, melodic_keys,
    )
    melodic_notes = set(melodic_evidence)
    extended_notes = {
        identifier for identifier, evidence in melodic_evidence.items()
        if "member classified melodic by v1 importer" not in evidence
    }
    score = vgz.compile_score(
        info, writes, Path(name), hashlib.sha256(payload).hexdigest(),
        hashlib.sha256(data).hexdigest(), overrides, {},
        prioritize_articulations,
    )
    old_commands = vgz.score_note_onsets(score)
    source_onsets = {
        (opl_voices.analysis_frame(note.start),
         vgz.playable_note(round(note.initial_pitch)))
        for note in logical_notes
        if note.identifier in melodic_notes and note.initial_pitch is not None
    }
    protected = old_commands & source_onsets
    allocation = opl_voices.allocate_three_voices(
        logical_notes, logical_voices, melodic_notes, protected,
        vgz.playable_note,
    )
    fingerprint_fields = {
        "logical_notes": [asdict(note) for note in logical_notes],
        "logical_voices": [asdict(voice) for voice in logical_voices],
        "continuation_assignments": [
            asdict(assignment) for assignment in assignments
        ],
        "three_voice_allocation": allocation,
        "melodic_eligibility": sorted(melodic_evidence.items()),
    }
    return {
        "name": name,
        "vgm_sha256": hashlib.sha256(data).hexdigest(),
        "duration_samples": info.total_samples,
        "segments": len(segments),
        "layer_candidates": sum(
            relation.kind == "layer_candidate" for relation in relations
        ),
        "logical_notes": len(logical_notes),
        "logical_voices": len(logical_voices),
        "continuation_assignments": len(assignments),
        "semantic_changes": sum(
            assignment.semantic_changes for assignment in assignments
        ),
        "channel_changes": sum(
            assignment.channel_changes for assignment in assignments
        ),
        "source_melodic_onsets": allocation["source_onsets"],
        "extended_sustained_layer_notes": len(extended_notes),
        "v1_retained_source_onsets": allocation["protected_onsets"],
        "provisional_retained_source_onsets": allocation["retained_onsets"],
        "provisional_gained_source_onsets": allocation["gained_onsets"],
        "provisional_regressed_v1_onsets": allocation[
            "missed_protected_onsets"
        ],
        "assignment_sha256": digest(fingerprint_fields),
    }


def analyze_archive(path: Path) -> dict:
    payload = path.read_bytes()
    archive_sha = hashlib.sha256(payload).hexdigest()
    pack = KNOWN_PACKS.get(archive_sha)
    tracks: list[dict] = []
    try:
        with zipfile.ZipFile(path) as archive:
            names = sorted(
                name for name in archive.namelist()
                if name.lower().endswith(".vgz")
            )
            if not names:
                raise ValueError(f"{path}: archive contains no VGZ tracks")
            for track_number, name in enumerate(names, 1):
                overrides = doom_library.MELODIC_OVERRIDES.get(
                    (pack, track_number), set(),
                ) if pack is not None else set()
                prioritize = (pack, track_number) in (
                    doom_library.ARTICULATION_PRIORITY
                ) if pack is not None else False
                tracks.append(analyze_track(
                    name, archive.read(name), overrides, prioritize,
                ))
    except zipfile.BadZipFile as exc:
        raise ValueError(f"{path}: invalid ZIP archive") from exc
    return {
        "name": path.name,
        "sha256": archive_sha,
        "known_policy_pack": pack,
        "tracks": tracks,
    }


def report(paths: list[Path]) -> dict:
    archives = [analyze_archive(path) for path in paths]
    tracks = [track for archive in archives for track in archive["tracks"]]
    count_fields = (
        "segments", "layer_candidates", "logical_notes", "logical_voices",
        "continuation_assignments", "semantic_changes", "channel_changes",
        "source_melodic_onsets", "v1_retained_source_onsets",
        "extended_sustained_layer_notes",
        "provisional_retained_source_onsets",
        "provisional_gained_source_onsets",
        "provisional_regressed_v1_onsets",
    )
    totals = {"tracks": len(tracks)}
    totals.update({
        field: sum(track[field] for track in tracks) for field in count_fields
    })
    result = {
        "schema": "jukupoly-opl-voice-pack-report-v3",
        "analysis": {
            "voice_schema": "jukupoly-opl-voice-evidence-v3",
            "policy": (
                "analysis-only layer collapse and deterministic global "
                "one-to-one continuation assignment plus monotonic "
                "three-voice onset allocation"
            ),
        },
        "archives": archives,
        "totals": totals,
    }
    result["report_sha256"] = digest(result)
    if totals["provisional_regressed_v1_onsets"]:
        raise ValueError(
            "provisional allocator regressed protected v1 source onsets: "
            f"{totals['provisional_regressed_v1_onsets']}"
        )
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("archives", nargs="+", type=Path,
                        help="ZIP archives containing VGZ tracks")
    parser.add_argument("--output", type=Path,
                        help="write JSON here instead of standard output")
    args = parser.parse_args()
    try:
        result = report(args.archives)
    except (OSError, ValueError, vgz.VgmError) as exc:
        parser.error(str(exc))
    rendered = json.dumps(result, indent=2, allow_nan=False) + "\n"
    if args.output is None:
        print(rendered, end="")
    else:
        args.output.write_text(rendered)
    totals = result["totals"]
    print(
        "JUKUPOLY-OPL-VOICE-REPORT: PASS "
        f"tracks={totals['tracks']} segments={totals['segments']} "
        f"notes={totals['logical_notes']} voices={totals['logical_voices']} "
        f"assignments={totals['continuation_assignments']} "
        f"onsets=+{totals['provisional_gained_source_onsets']}"
        f"/-{totals['provisional_regressed_v1_onsets']} "
        f"sha256={result['report_sha256']}",
        file=sys.stderr if args.output is None else sys.stdout,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
