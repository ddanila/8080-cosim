#!/usr/bin/env python3
"""Report deterministic M2 logical-voice evidence for VGM pack archives."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import sys
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
FIRMWARE = ROOT / "spinoffs" / "jukupoly" / "firmware"
sys.path.insert(0, str(FIRMWARE))

import import_jukupoly_vgz as vgz  # noqa: E402
import opl_voices  # noqa: E402


def digest(value: object) -> str:
    encoded = json.dumps(
        value, sort_keys=True, separators=(",", ":"), allow_nan=False,
    ).encode()
    return hashlib.sha256(encoded).hexdigest()


def analyze_track(name: str, payload: bytes) -> dict:
    try:
        data = gzip.decompress(payload)
    except (EOFError, OSError) as exc:
        raise ValueError(f"{name}: invalid VGZ stream: {exc}") from exc
    info, writes = vgz.parse_vgm(data)
    document = opl_voices.voice_document(
        writes, info.banks, info.total_samples, info.clock,
        info.frequency_divider,
    )
    assignments = document["continuation_assignments"]
    fingerprint_fields = {
        "logical_notes": document["logical_notes"],
        "logical_voices": document["logical_voices"],
        "continuation_assignments": assignments,
    }
    return {
        "name": name,
        "vgm_sha256": hashlib.sha256(data).hexdigest(),
        "duration_samples": info.total_samples,
        "segments": len(document["segments"]),
        "layer_candidates": document["relation_counts"]["layer_candidate"],
        "logical_notes": len(document["logical_notes"]),
        "logical_voices": len(document["logical_voices"]),
        "continuation_assignments": len(assignments),
        "semantic_changes": sum(
            assignment["semantic_changes"] for assignment in assignments
        ),
        "channel_changes": sum(
            assignment["channel_changes"] for assignment in assignments
        ),
        "assignment_sha256": digest(fingerprint_fields),
    }


def analyze_archive(path: Path) -> dict:
    payload = path.read_bytes()
    tracks: list[dict] = []
    try:
        with zipfile.ZipFile(path) as archive:
            names = sorted(
                name for name in archive.namelist()
                if name.lower().endswith(".vgz")
            )
            if not names:
                raise ValueError(f"{path}: archive contains no VGZ tracks")
            for name in names:
                tracks.append(analyze_track(name, archive.read(name)))
    except zipfile.BadZipFile as exc:
        raise ValueError(f"{path}: invalid ZIP archive") from exc
    return {
        "name": path.name,
        "sha256": hashlib.sha256(payload).hexdigest(),
        "tracks": tracks,
    }


def report(paths: list[Path]) -> dict:
    archives = [analyze_archive(path) for path in paths]
    tracks = [track for archive in archives for track in archive["tracks"]]
    count_fields = (
        "segments", "layer_candidates", "logical_notes", "logical_voices",
        "continuation_assignments", "semantic_changes", "channel_changes",
    )
    totals = {"tracks": len(tracks)}
    totals.update({
        field: sum(track[field] for track in tracks) for field in count_fields
    })
    result = {
        "schema": "jukupoly-opl-voice-pack-report-v1",
        "analysis": {
            "voice_schema": "jukupoly-opl-voice-evidence-v2",
            "policy": (
                "analysis-only layer collapse and deterministic global "
                "one-to-one continuation assignment"
            ),
        },
        "archives": archives,
        "totals": totals,
    }
    result["report_sha256"] = digest(result)
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
        f"sha256={result['report_sha256']}",
        file=sys.stderr if args.output is None else sys.stdout,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
