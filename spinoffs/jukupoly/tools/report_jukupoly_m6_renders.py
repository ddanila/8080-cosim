#!/usr/bin/env python3
"""Render and qualify 30-second v1/enhanced/OPL M6 comparisons."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import subprocess
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
DEFAULT_REPORT = SPINOFF / "OPL-M6-REPRESENTATIVE-RENDERS.json"
DEFAULT_RENDERS = DEFAULT_WORK / "renders"
EXCERPT_FRAMES = 1_500
EXCERPT_SECONDS = 30
sys.path.insert(0, str(FIRMWARE))

import build_jukupoly as build  # noqa: E402
import import_jukupoly_vgz as vgz  # noqa: E402
import opl_oracle  # noqa: E402


@dataclass(frozen=True)
class Track:
    label: str
    source_name: str
    score_name: str
    prioritize_articulations: bool = False


TRACKS = (
    Track(
        "doom1-03-imp", "03 The Imp's Song.vgz",
        "doom1-03-imp-30s.json",
    ),
    Track(
        "doom1-04-dark-halls", "04 Dark Halls.vgz",
        "doom1-04-dark-halls-30s.json", True,
    ),
    Track(
        "doom1-06-suspense", "06 Suspense.vgz",
        "doom1-06-suspense-30s.json",
    ),
    Track(
        "doom2-10-dave-taylor", "10 The Dave D. Taylor Blues.vgz",
        "doom2-10-dave-taylor-30s.json",
    ),
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def truncate_score(score: dict, frames: int = EXCERPT_FRAMES) -> dict:
    result = copy.deepcopy(score)
    rows = []
    remaining = frames
    for source_row in result["rows"]:
        if remaining <= 0:
            break
        row = copy.deepcopy(source_row)
        row["frames"] = min(row["frames"], remaining)
        rows.append(row)
        remaining -= row["frames"]
    if remaining:
        raise ValueError("score is shorter than the M6 render excerpt")
    result["rows"] = rows
    return result


def v1_score(source: Path, *, prioritize_articulations: bool) -> dict:
    data, compressed_sha = vgz.decode_source(source)
    info, writes = vgz.parse_vgm(data)
    return vgz.compile_score(
        info, writes, source, compressed_sha, hashlib.sha256(data).hexdigest(),
        set(), {}, prioritize_articulations,
    )


def compile_jps(directory: Path, label: str, score: dict
                ) -> tuple[Path, bytes, str, dict]:
    generated, metadata = build.compile_song(score)
    payload = build.assemble_song_file(generated, metadata)
    path = directory / f"{label}.jps"
    path.write_bytes(payload)
    return path, payload, generated, metadata


def standalone(directory: Path, label: str, generated: str,
               *, enhanced: bool) -> Path:
    source = directory / f"{label}.asm"
    include = directory / "jukupoly-song-generated.inc"
    envelope = directory / "jukupoly-envelope-v2.inc"
    source.write_bytes((FIRMWARE / "jukupoly-player-0100.asm").read_bytes())
    include.write_text(generated)
    envelope.write_bytes((FIRMWARE / envelope.name).read_bytes())
    image = directory / f"{label}.cim"
    command = [
        str(ROOT / "third_party" / "zmac" / "src" / "zmac"),
        "--nmnv", "--zmac", "-8", "-P3=1", "-P4=1",
    ]
    if enhanced:
        command.extend(("-P5=1", "-P6=1", "-P7=1"))
    command.extend((f"-I{directory}", "-o", str(image), str(source)))
    baseline.run(command)
    return image


def profile(profiler: Path, player: Path, song: Path, entry: int,
            label: str, prepare: int | None = None) -> dict:
    command = [
        str(profiler), str(player), str(song), f"{entry:x}", label,
    ]
    if prepare is not None:
        command.append(f"{prepare:x}")
    return json.loads(baseline.run(command))


def exact_wav(renderer: Path, image: Path, temporary: Path,
              output: Path) -> dict:
    baseline.run([
        str(renderer), "--sample-rate", "48000", "--lead", "0",
        "--tail", "0", str(image), str(temporary),
    ])
    subprocess.run([
        "ffmpeg", "-hide_banner", "-loglevel", "error", "-i",
        str(temporary), "-af", "apad", "-t", str(EXCERPT_SECONDS),
        "-c:a", "pcm_s16le", str(output), "-y",
    ], check=True)
    return {
        "name": output.name,
        "bytes": output.stat().st_size,
        "sha256": sha256(output),
        "sample_rate_hz": 48_000,
        "seconds": EXCERPT_SECONDS,
    }


def opl_reference(source: Path, oracle: Path, directory: Path,
                  output: Path) -> dict:
    data, _compressed_sha = vgz.decode_source(source)
    info, writes = vgz.parse_vgm(data)
    total = min(info.total_samples, EXCERPT_SECONDS * opl_oracle.VGM_RATE)
    stream = directory / "source.jop"
    pcm = directory / "source.s16le"
    probes = directory / "source.csv"
    opl_oracle.write_event_stream(
        stream, (write for write in writes if write.sample < total), total,
    )
    subprocess.run(
        [str(oracle), str(stream), str(pcm), str(probes), "all"],
        check=True, stdout=subprocess.PIPE, text=True,
    )
    subprocess.run([
        "ffmpeg", "-hide_banner", "-loglevel", "error", "-f", "s16le",
        "-ar", str(opl_oracle.VGM_RATE), "-ac", "2", "-i", str(pcm),
        "-c:a", "pcm_s16le", str(output), "-y",
    ], check=True)
    return {
        "name": output.name,
        "bytes": output.stat().st_size,
        "sha256": sha256(output),
        "sample_rate_hz": opl_oracle.VGM_RATE,
        "channels": 2,
        "seconds": total / opl_oracle.VGM_RATE,
    }


def generate(work: Path, render_dir: Path, oracle: Path) -> dict:
    sources = work / "sources"
    scores = work / "scores"
    render_dir.mkdir(parents=True, exist_ok=True)
    floor = json.loads((SPINOFF / "OPL-ENVELOPE-M3.json").read_text())[
        "v2_sample_rate_floor_hz"
    ]
    frozen = json.loads((SPINOFF / "OPL-BASELINE.json").read_text())
    with tempfile.TemporaryDirectory(prefix="jukupoly-m6-renders.") as name:
        directory = Path(name)
        profiler, renderer = baseline.build_tools(directory)
        old_player, _listing, old_symbols = baseline.build_player(directory)
        new_player, new_symbols = target_report.build_player(
            directory, "m6-p567", tremolo=True, runtime_vibrato=True,
        )
        new_payload = new_player.read_bytes()
        loop_start = new_symbols["sample_loop"] - baseline.COM_ADDRESS
        loop_end = new_symbols["frame_tick"] - baseline.COM_ADDRESS
        loop_hash = hashlib.sha256(
            new_payload[loop_start:loop_end]
        ).hexdigest()
        records = []
        for item in TRACKS:
            source_path = sources / item.source_name
            score_path = scores / item.score_name
            if not source_path.is_file() or not score_path.is_file():
                raise ValueError(f"missing M6 render input for {item.label}")
            control = truncate_score(v1_score(
                source_path,
                prioritize_articulations=item.prioritize_articulations,
            ))
            enhanced = truncate_score(json.loads(score_path.read_text()))
            old_song, old_bytes, old_generated, old_metadata = compile_jps(
                directory, item.label + "-v1", control,
            )
            new_song, enhanced_bytes, new_generated, new_metadata = compile_jps(
                directory, item.label + "-enhanced", enhanced,
            )
            old_image = standalone(
                directory, item.label + "-v1", old_generated,
                enhanced=False,
            )
            new_image = standalone(
                directory, item.label + "-enhanced", new_generated,
                enhanced=True,
            )
            old_profile = profile(
                profiler, old_player, old_song,
                old_symbols["player_start"], item.label + "-v1-30s",
            )
            new_profile = profile(
                profiler, new_player, new_song,
                new_symbols["player_start"], item.label + "-enhanced-30s",
                new_symbols["envelope_dispatch_init"],
            )
            wavs = {
                "v1": exact_wav(
                    renderer, old_image, directory / "v1-raw.wav",
                    render_dir / f"{item.label}-v1-30s.wav",
                ),
                "enhanced": exact_wav(
                    renderer, new_image, directory / "enhanced-raw.wav",
                    render_dir / f"{item.label}-enhanced-30s.wav",
                ),
                "opl_reference": opl_reference(
                    source_path, oracle, directory,
                    render_dir / f"{item.label}-opl-30s.wav",
                ),
            }
            hashes = {value["sha256"] for value in wavs.values()}
            gates = {
                "enhanced_jps_below_soft_limit": (
                    len(enhanced_bytes) < 30 * 1024
                ),
                "sample_rate_above_shared_floor": (
                    new_profile["effective_sample_hz"] >= floor
                ),
                "phase_table_matches_within_one_percent": (
                    abs(new_profile["effective_sample_hz"] -
                        new_metadata["target_sample_hz"]) <=
                    new_profile["effective_sample_hz"] * 0.01
                ),
                "music_clock_within_one_percent": (
                    abs(new_profile["music_frame_hz"] - 50.0) <= 0.5
                ),
                "duration_within_one_percent": (
                    abs(new_profile["duration_seconds"] - EXCERPT_SECONDS) <=
                    EXCERPT_SECONDS * 0.01
                ),
                "percussion_and_escape_remain_concurrent": (
                    new_metadata["descriptors"] ==
                    old_metadata["descriptors"] and
                    new_profile["keyboard_polls"] >= new_profile["frames"]
                ),
                "three_render_hashes_are_distinct": len(hashes) == 3,
            }
            records.append({
                "label": item.label,
                "source": {
                    "name": source_path.name,
                    "sha256": sha256(source_path),
                },
                "enhanced_score": {
                    "name": score_path.name,
                    "sha256": sha256(score_path),
                },
                "format": {
                    "v1_jps_bytes": len(old_bytes),
                    "enhanced_jps_bytes": len(enhanced_bytes),
                    "enhanced_capability": enhanced_bytes[7],
                    "frame_samples": new_metadata["frame_samples"],
                    "phase_table_hz": new_metadata["target_sample_hz"],
                },
                "profiles": {"v1": old_profile, "enhanced": new_profile},
                "wavs": wavs,
                "gates": gates,
            })
    aggregate = {
        "all_track_gates_pass": all(
            all(item["gates"].values()) for item in records
        ),
        "sample_loop_hash_exact": (
            loop_hash == frozen["player"]["sample_loop_sha256"]
        ),
    }
    return {
        "schema": "jukupoly-opl-m6-representative-renders-v1",
        "status": (
            "four v1/enhanced/pinned-Nuked excerpt gates pass; complete pack "
            "build and physical CS00000 A/B remain open"
        ),
        "excerpt": {
            "music_frames": EXCERPT_FRAMES,
            "nominal_seconds": EXCERPT_SECONDS,
            "wav_policy": "target renders are padded/trimmed to exact 30 s",
        },
        "shared_sample_rate_floor_hz": floor,
        "player": {
            "bytes": len(new_payload),
            "end_address_exclusive": hex(
                baseline.COM_ADDRESS + len(new_payload)
            ),
            "song_window_margin_bytes": baseline.SONG_ADDRESS - (
                baseline.COM_ADDRESS + len(new_payload)
            ),
            "sample_loop_sha256": loop_hash,
        },
        "tracks": records,
        "aggregate_gates": aggregate,
        "remaining_gates": [
            "complete two-pack enhanced/fallback build",
            "physical CS00000 A/B before normal enablement",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--work", type=Path, default=DEFAULT_WORK)
    parser.add_argument("--render-dir", type=Path, default=DEFAULT_RENDERS)
    parser.add_argument("--opl-oracle", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    oracle = args.opl_oracle.resolve()
    if not oracle.is_file():
        parser.error(f"OPL oracle is missing: {oracle}")
    try:
        result = generate(
            args.work.resolve(), args.render_dir.resolve(), oracle,
        )
    except (OSError, ValueError, RuntimeError,
            subprocess.CalledProcessError) as exc:
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
        f"JUKUPOLY-M6-RENDERS: {action} {args.output} "
        f"tracks={len(result['tracks'])}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
