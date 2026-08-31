#!/usr/bin/env python3
"""Build a reusable JukuPoly player and an 800 KiB DOOM music disk."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import tempfile
import zipfile
from pathlib import Path

import build_jukupoly
import import_jukupoly_vgz as vgz


HERE = Path(__file__).resolve().parent
SPINOFF = HERE.parent
ROOT = SPINOFF.parents[1]
PLAYER_SOURCE = HERE / "jukupoly-player-0100.asm"
DISK_NAME = "jukupoly-doom-library.cpm"
DISK_FORMAT = "juku-logical"
JUKU_DISK_BYTES = 80 * 2 * 10 * 512
JUKU_TRACK_BYTES = 10 * 512
JUKU_LOGICAL_TRACKS = 80 * 2
EXPECTED_TRACKS = {"doom1": 23, "doom2": 21}

# The seven-second DOOM title fanfare uses several patches at only one or two
# pitches.  That is below the converter's safe automatic melodic threshold, so
# retain the three frequent chord voices explicitly.  The IDs are stable hashes
# of their OPL operator-register signatures and are also recorded in catalog.json.
MELODIC_OVERRIDES = {
    ("doom1", 1): {
        "d357f6e830b6",
        "22c93b76b58b",
        "514d6277991a",
    },
}

# Dark Halls layers a retriggered bass beneath a three-note arpeggiated pad;
# continuity-first selection erased 198 newly arriving pad notes.  This
# source/MIDI-confirmed arrangement needs articulated notes selected before
# already-sustaining voices.
ARTICULATION_PRIORITY = {("doom1", 4)}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def archive_tracks(path: Path) -> list[tuple[str, bytes]]:
    with zipfile.ZipFile(path) as archive:
        names = sorted(
            name for name in archive.namelist()
            if Path(name).suffix.lower() == ".vgz" and "/" not in name
        )
        return [(name, archive.read(name)) for name in names]


def compile_track(source: Path, overrides: set[str],
                  prioritize_articulations: bool) -> tuple[bytes, dict]:
    data, compressed_sha = vgz.decode_source(source)
    info, writes = vgz.parse_vgm(data)
    score = vgz.compile_score(
        info,
        writes,
        source,
        compressed_sha,
        hashlib.sha256(data).hexdigest(),
        overrides,
        {},
        prioritize_articulations,
    )
    generated, metadata = build_jukupoly.compile_song(score)
    payload = build_jukupoly.assemble_song_file(generated, metadata)
    return payload, score


def build_player(output: Path) -> None:
    with tempfile.TemporaryDirectory(prefix="jukupoly-library-player.") as name:
        image = Path(name) / "jukebox.cim"
        command = [
            str(build_jukupoly.executable()),
            "--nmnv",
            "--zmac",
            "-8",
            "-P2=1",
            f"-I{HERE}",
            "-o",
            str(image),
            str(PLAYER_SOURCE),
        ]
        subprocess.run(command, check=True)
        output.write_bytes(image.read_bytes())
    if output.stat().st_size >= build_jukupoly.SONG_LOAD_ADDRESS - 0x100:
        raise SystemExit(
            f"library player overlaps the 1800h song window: {output.stat().st_size} bytes"
        )


def readme_text(catalog: list[dict], archives: list[dict]) -> str:
    lines = [
        "JukuPoly DOOM music library",
        "===========================",
        "",
        "44 finite three-voice-plus-percussion reductions for the Juku speaker.",
        "Run JUKEBOX.COM and select tracks 01 through 44.",
        "",
        "Music: Robert Prince",
        "Games and original releases: id Software",
        "OPL3 VGM/VGZ packages: vgmrips.net; packs by NewRisingSun",
        "JukuPoly conversion/player: 8080-cosim contributors",
        "",
        "These are register-level musical reductions, not OPL3 emulation.",
        "Timbres, stereo, feedback, modulation, and exact envelopes are not retained.",
        "The player follows each VGM command stream once and never repeats its loop.",
        "",
        "Source archives:",
    ]
    lines.extend(f"  {item['name']}  SHA-256 {item['sha256']}" for item in archives)
    lines.extend(["", "Catalog:"])
    for item in catalog:
        seconds = item["duration_seconds"]
        minutes, second = divmod(round(seconds), 60)
        lines.append(
            f"  {item['global_track']:02d} {item['title']} ({minutes}:{second:02d})"
        )
    return "\r\n".join(lines) + "\r\n"


def cpm_run(arguments: list[str]) -> None:
    subprocess.run(arguments, cwd=SPINOFF, check=True)


def logical_to_native(source: Path, destination: Path) -> None:
    """Convert CP/M's side-major tracks to Juku's cylinder-interleaved image."""
    logical = source.read_bytes()
    if len(logical) > JUKU_DISK_BYTES:
        raise SystemExit(f"logical disk is too large: {len(logical)} bytes")
    logical = logical.ljust(JUKU_DISK_BYTES, b"\0")
    native = bytearray(JUKU_DISK_BYTES)
    for logical_track in range(JUKU_LOGICAL_TRACKS):
        physical_track = (logical_track % 80) * 2 + logical_track // 80
        logical_offset = logical_track * JUKU_TRACK_BYTES
        physical_offset = physical_track * JUKU_TRACK_BYTES
        native[physical_offset:physical_offset + JUKU_TRACK_BYTES] = (
            logical[logical_offset:logical_offset + JUKU_TRACK_BYTES]
        )
    destination.write_bytes(native)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--doom", type=Path, required=True,
                        help="vgmrips Doom_(PC).zip")
    parser.add_argument("--doom2", type=Path, required=True,
                        help="vgmrips Doom_II...zip")
    parser.add_argument("--output-dir", type=Path,
                        default=ROOT / "out" / "jukupoly-doom-library")
    args = parser.parse_args()
    for path in (args.doom, args.doom2):
        if not path.is_file():
            parser.error(f"archive does not exist: {path}")
    for tool in ("mkfs.cpm", "cpmcp", "cpmls"):
        if shutil.which(tool) is None:
            parser.error(f"{tool} is required (install cpmtools)")

    output = args.output_dir.resolve()
    songs = output / "songs"
    songs.mkdir(parents=True, exist_ok=True)
    player = output / "JUKEBOX.COM"
    build_player(player)

    archive_specs = (
        ("doom1", args.doom.resolve()),
        ("doom2", args.doom2.resolve()),
    )
    archive_records = [
        {"pack": pack, "name": path.name, "sha256": sha256(path)}
        for pack, path in archive_specs
    ]
    catalog: list[dict] = []
    global_track = 0
    with tempfile.TemporaryDirectory(prefix="jukupoly-doom.") as temp_name:
        temp = Path(temp_name)
        for pack, archive_path in archive_specs:
            sources = archive_tracks(archive_path)
            if len(sources) != EXPECTED_TRACKS[pack]:
                raise SystemExit(
                    f"{archive_path.name}: expected {EXPECTED_TRACKS[pack]} VGZ "
                    f"tracks, found {len(sources)}"
                )
            for local_track, (source_name, source_bytes) in enumerate(sources, 1):
                global_track += 1
                source = temp / source_name
                source.write_bytes(source_bytes)
                overrides = MELODIC_OVERRIDES.get((pack, local_track), set())
                prioritize_articulations = (pack, local_track) in ARTICULATION_PRIORITY
                payload, score = compile_track(
                    source, overrides, prioritize_articulations,
                )
                game = 1 if pack == "doom1" else 2
                cpm_name = f"D{game}T{local_track:02d}.JPS"
                song_path = songs / cpm_name
                song_path.write_bytes(payload)
                conversion = score["conversion"]
                gd3 = score["source"]["gd3"]
                catalog.append({
                    "global_track": global_track,
                    "pack": pack,
                    "local_track": local_track,
                    "filename": cpm_name,
                    "title": gd3.get("track_en") or Path(source_name).stem,
                    "composer": score["composer"],
                    "duration_seconds": conversion["duration_seconds"],
                    "duration_frames": conversion["duration_frames"],
                    "bytes": len(payload),
                    "source_name": source_name,
                    "source_sha256": score["source"]["compressed_sha256"],
                    "melodic_signature_overrides": sorted(overrides),
                    "voice_selection_policy": conversion["voice_selection_policy"],
                })

    readme = output / "README.TXT"
    readme.write_text(readme_text(catalog, archive_records), newline="")
    manifest = {
        "schema": "jukupoly-doom-library-v1",
        "player": {
            "filename": player.name,
            "bytes": player.stat().st_size,
            "sha256": sha256(player),
            "song_load_address": build_jukupoly.SONG_LOAD_ADDRESS,
        },
        "archives": archive_records,
        "tracks": catalog,
    }
    (output / "catalog.json").write_text(json.dumps(manifest, indent=2) + "\n")

    disk = output / DISK_NAME
    with tempfile.TemporaryDirectory(prefix="jukupoly-disk.") as disk_temp_name:
        logical_disk = Path(disk_temp_name) / "library-logical.cpm"
        cpm_run(["mkfs.cpm", "-f", DISK_FORMAT, str(logical_disk)])
        cpm_run(["cpmcp", "-f", DISK_FORMAT, str(logical_disk), str(player),
                 "0:JUKEBOX.COM"])
        cpm_run(["cpmcp", "-f", DISK_FORMAT, str(logical_disk), str(readme),
                 "0:README.TXT"])
        for item in catalog:
            path = songs / item["filename"]
            cpm_run(["cpmcp", "-f", DISK_FORMAT, str(logical_disk), str(path),
                     f"0:{item['filename']}"])
        listing = subprocess.run(
            ["cpmls", "-f", DISK_FORMAT, "-d", str(logical_disk)],
            cwd=SPINOFF,
            check=True,
            text=True,
            stdout=subprocess.PIPE,
        ).stdout
        logical_to_native(logical_disk, disk)
    (output / "directory.txt").write_text(listing)
    print(
        f"JUKUPOLY-DOOM-LIBRARY: wrote {disk} tracks={len(catalog)} "
        f"songs={sum(item['bytes'] for item in catalog)} "
        f"player={player.stat().st_size} disk={disk.stat().st_size}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
