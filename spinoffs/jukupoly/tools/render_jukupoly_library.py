#!/usr/bin/env python3
"""Cycle-render every song in a reusable JukuPoly library to WAV and MP3."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import subprocess
import tempfile
import unicodedata
from pathlib import Path

import report_jukupoly_baseline as baseline
import report_jukupoly_vibrato_target as target_report


ROOT = Path(__file__).resolve().parents[3]
DEFAULT_OUTPUT = ROOT / "out" / "jukupoly-library-renders"
RENDERER_SOURCE = (
    ROOT / "spinoffs" / "jukupoly" / "tools" / "render_jukupoly_wav.c"
)
RENDER_LINE = re.compile(
    r"run=(?P<run>[0-9.]+)s wav=(?P<wav>[0-9.]+)s .* "
    r"rate=(?P<rate>\d+)Hz writes=(?P<writes>\d+) "
    r"intervals=(?P<intervals>\d+) keyboard_polls=(?P<polls>\d+) .* "
    r"peak=(?P<peak>[0-9.]+)"
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def run(command: list[str], *, capture: bool = False) -> str:
    result = subprocess.run(
        command,
        cwd=ROOT,
        check=True,
        text=True,
        stdout=subprocess.PIPE if capture else None,
    )
    return result.stdout if result.stdout is not None else ""


def safe_stem(track: dict) -> str:
    title = unicodedata.normalize("NFKD", track["title"])
    title = title.encode("ascii", "ignore").decode("ascii").lower()
    title = re.sub(r"[^a-z0-9]+", "-", title).strip("-") or "untitled"
    return (
        f"{track['global_track']:02d}-{track['pack']}-"
        f"{track['local_track']:02d}-{title}"
    )


def build_renderer(directory: Path) -> Path:
    renderer = directory / "render_jukupoly_wav"
    run([
        "cc", "-std=c11", "-O2", "-Wall", "-Wextra", "-Werror",
        "-o", str(renderer), str(RENDERER_SOURCE),
        str(ROOT / "cosim" / "i8080.c"), "-lm",
    ])
    return renderer


def qualified_player(directory: Path, capabilities: int
                     ) -> tuple[Path, dict[str, int]]:
    return target_report.build_player(
        directory, "library-render-player",
        tremolo=bool(capabilities & 0x02),
        runtime_vibrato=bool(capabilities & 0x04),
    )


def ffprobe_seconds(path: Path) -> float:
    return float(run([
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", str(path),
    ], capture=True).strip())


def render_library(library: Path, output: Path, album: str,
                   report_path: Path | None,
                   minimum_enhanced_tracks: int = 0) -> dict:
    catalog_path = library / "catalog.json"
    player_path = library / "JUKEBOX.COM"
    songs_path = library / "songs"
    if not catalog_path.is_file() or not player_path.is_file():
        raise ValueError("library must contain catalog.json and JUKEBOX.COM")
    catalog = json.loads(catalog_path.read_text())
    tracks = catalog.get("tracks")
    if not isinstance(tracks, list) or not tracks:
        raise ValueError("library catalog has no tracks")
    capabilities = catalog.get("delivery", {}).get("player_capabilities", 0)
    if not isinstance(capabilities, int) or capabilities & ~0x07:
        raise ValueError("invalid library player capability mask")
    enhanced_tracks = catalog.get("delivery", {}).get(
        "enhanced_replacements", 0,
    )
    if (not isinstance(enhanced_tracks, int) or enhanced_tracks < 0 or
            enhanced_tracks > len(tracks)):
        raise ValueError("invalid enhanced replacement count")
    if enhanced_tracks < minimum_enhanced_tracks:
        raise ValueError(
            f"library has {enhanced_tracks} enhanced tracks; "
            f"at least {minimum_enhanced_tracks} required"
        )

    wav_directory = output / "wav"
    mp3_directory = output / "mp3"
    wav_directory.mkdir(parents=True, exist_ok=True)
    mp3_directory.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="jukupoly-library-render.") as name:
        temporary = Path(name)
        renderer = build_renderer(temporary)
        reference_player, symbols = qualified_player(temporary, capabilities)
        if reference_player.read_bytes() != player_path.read_bytes():
            raise ValueError(
                "JUKEBOX.COM does not match the reproducible qualified player build"
            )
        records = []
        for index, track in enumerate(tracks, 1):
            filename = track.get("filename")
            song = songs_path / filename if isinstance(filename, str) else None
            if song is None or not song.is_file():
                raise ValueError(f"catalog song is missing: {filename!r}")
            if sha256(song) != track.get("payload_sha256"):
                raise ValueError(f"catalog song hash mismatch: {filename}")
            stem = safe_stem(track)
            wav = wav_directory / f"{stem}.wav"
            mp3 = mp3_directory / f"{stem}.mp3"
            maximum = max(30, math.ceil(float(track["duration_seconds"]) * 1.03 + 10))
            print(
                f"JUKUPOLY-LIBRARY-RENDER: {index:02d}/{len(tracks):02d} "
                f"{track['pack']}/{track['local_track']:02d} {track['title']}",
                flush=True,
            )
            rendered = run([
                str(renderer), "--sample-rate", "48000", "--lead", "0.25",
                "--tail", "0.25", "--max-seconds", str(maximum),
                "--song", str(song), "--entry",
                f"{symbols['player_start']:x}", "--prepare",
                f"{symbols['envelope_dispatch_init']:x}", str(player_path),
                str(wav),
            ], capture=True)
            match = RENDER_LINE.search(rendered)
            if match is None:
                raise RuntimeError(f"cannot parse renderer result: {rendered!r}")
            run([
                "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
                "-i", str(wav), "-codec:a", "libmp3lame", "-q:a", "2",
                "-metadata", f"title={track['title']}",
                "-metadata", f"artist={track.get('composer') or 'Robert Prince'}",
                "-metadata", f"album={album}",
                "-metadata", f"track={track['global_track']}/{len(tracks)}",
                "-metadata", "comment=Cycle-rendered JukuPoly reduction",
                str(mp3),
            ])
            values = match.groupdict()
            records.append({
                "global_track": track["global_track"],
                "pack": track["pack"],
                "local_track": track["local_track"],
                "title": track["title"],
                "source_name": track["source_name"],
                "source_sha256": track["source_sha256"],
                "jps": {
                    "name": filename,
                    "bytes": song.stat().st_size,
                    "sha256": sha256(song),
                    "capability": track["capability"],
                },
                "render": {
                    "run_seconds": float(values["run"]),
                    "wav_seconds": float(values["wav"]),
                    "pcm_sample_rate_hz": int(values["rate"]),
                    "pit_writes": int(values["writes"]),
                    "pulse_intervals": int(values["intervals"]),
                    "keyboard_polls": int(values["polls"]),
                    "peak": float(values["peak"]),
                },
                "wav": {
                    "path": f"wav/{wav.name}",
                    "bytes": wav.stat().st_size,
                    "sha256": sha256(wav),
                },
                "mp3": {
                    "path": f"mp3/{mp3.name}",
                    "bytes": mp3.stat().st_size,
                    "sha256": sha256(mp3),
                    "duration_seconds": ffprobe_seconds(mp3),
                    "codec": "libmp3lame VBR quality 2",
                },
            })

    generic_policy = catalog.get("conversion_policy", {})
    generic_tracks = all(
        not item.get("melodic_signature_overrides") and
        item.get("voice_selection_policy") ==
        "sustaining-note continuity before newly articulated notes"
        for item in tracks
    )
    result = {
        "schema": "jukupoly-library-full-renders-v1",
        "status": (
            f"all {len(records)} finite library tracks were cycle-rendered "
            "through the reusable player and encoded to MP3"
        ),
        "library": {
            "catalog_sha256": sha256(catalog_path),
            "player_bytes": player_path.stat().st_size,
            "player_sha256": sha256(player_path),
            "player_capabilities": capabilities,
            "enhanced_tracks": enhanced_tracks,
            "conversion_policy": generic_policy,
        },
        "render_policy": {
            "engine": "cycle-level Intel 8080 plus D57 channel-1 Mode-0 pulses",
            "cpu_hz": 1_700_000,
            "pit_hz": 2_000_000,
            "pcm_sample_rate_hz": 48_000,
            "gain": 0.95,
            "dc_block_hz": 20,
            "lead_seconds": 0.25,
            "tail_seconds": 0.25,
            "mp3": "libmp3lame VBR quality 2",
            "song_specific_render_exceptions": [],
        },
        "tracks": records,
        "aggregate_gates": {
            "catalog_and_renders_have_same_track_count": len(records) == len(tracks),
            "every_catalog_payload_hash_matches": all(
                item["jps"]["sha256"] == tracks[index]["payload_sha256"]
                for index, item in enumerate(records)
            ),
            "every_render_has_audio": all(
                item["render"]["pit_writes"] >= 2 and
                item["render"]["pulse_intervals"] > 0 and
                item["render"]["peak"] > 0
                for item in records
            ),
            "generic_conversion_requested": generic_policy.get("generic_only") is True,
            "no_song_specific_conversion_exceptions": generic_tracks,
            "no_song_specific_render_exceptions": True,
            "minimum_enhanced_tracks_met":
                enhanced_tracks >= minimum_enhanced_tracks,
        },
    }
    rendered_report = json.dumps(result, indent=2, sort_keys=True) + "\n"
    (output / "manifest.json").write_text(rendered_report)
    if report_path is not None:
        report_path.write_text(rendered_report)
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--library", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument(
        "--album", default="DOOM and DOOM II — JukuPoly reductions",
    )
    parser.add_argument("--report", type=Path)
    parser.add_argument(
        "--minimum-enhanced-tracks", type=int, default=0,
        help=("refuse to render a control-only library when producing a "
              "current-best collection"),
    )
    args = parser.parse_args()
    if args.minimum_enhanced_tracks < 0:
        parser.error("--minimum-enhanced-tracks must be nonnegative")
    result = render_library(
        args.library.resolve(), args.output_dir.resolve(), args.album,
        None if args.report is None else args.report.resolve(),
        args.minimum_enhanced_tracks,
    )
    failed = [
        name for name, passed in result["aggregate_gates"].items() if not passed
    ]
    if failed:
        raise SystemExit("render gates failed: " + ", ".join(failed))
    print(
        f"JUKUPOLY-LIBRARY-RENDER: PASS tracks={len(result['tracks'])} "
        f"output={args.output_dir.resolve()}",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
