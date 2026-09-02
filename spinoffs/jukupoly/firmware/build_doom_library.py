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


def track_policy(pack: str, local_track: int, generic: bool
                 ) -> tuple[set[str], bool]:
    """Return explicit compatibility overrides or the shared generic policy."""
    if generic:
        return set(), False
    return (
        MELODIC_OVERRIDES.get((pack, local_track), set()),
        (pack, local_track) in ARTICULATION_PRIORITY,
    )


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


def build_player(output: Path, capabilities: int = 0) -> None:
    with tempfile.TemporaryDirectory(prefix="jukupoly-library-player.") as name:
        image = Path(name) / "jukebox.cim"
        command = [
            str(build_jukupoly.executable()),
            "--nmnv",
            "--zmac",
            "-8",
            "-P2=1",
            "-P4=1",
        ]
        if capabilities & build_jukupoly.JPS2_TREMOLO_CAPABILITY:
            command.append("-P5=1")
        if capabilities & build_jukupoly.JPS2_PITCH_CAPABILITY:
            command.extend(("-P6=1", "-P7=1"))
        command.extend((
            f"-I{HERE}", "-o", str(image), str(PLAYER_SOURCE),
        ))
        subprocess.run(command, check=True)
        output.write_bytes(image.read_bytes())
    if output.stat().st_size >= build_jukupoly.SONG_LOAD_ADDRESS - 0x100:
        raise SystemExit(
            f"library player overlaps the 1800h song window: {output.stat().st_size} bytes"
        )


def readme_text(catalog: list[dict], archives: list[dict],
                enhanced_tracks: int = 0) -> str:
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
    if enhanced_tracks:
        limitation = lines.index(
            "Timbres, stereo, feedback, modulation, and exact envelopes are not retained."
        )
        lines[limitation] = (
            "JPS1 fallbacks omit exact envelopes; JPS2 tracks retain only the "
            "guarded approximations recorded in their reports."
        )
        player_note = lines.index(
            "The player follows each VGM command stream once and never repeats its loop."
        )
        lines[player_note:player_note] = [
            "",
            f"This experimental disk contains {enhanced_tracks} guarded JPS2 tracks;",
            "the remaining tracks retain their unchanged JPS1 fallback.",
            "See catalog.json for the delivery mode and capability of each track.",
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


def load_replacements(manifest_path: Path | None,
                      payload_directory: Path | None
                      ) -> tuple[dict[tuple[str, int], dict], int]:
    if manifest_path is None and payload_directory is None:
        return {}, 0
    if manifest_path is None or payload_directory is None:
        raise ValueError(
            "replacement manifest and payload directory must be supplied together"
        )
    document = json.loads(manifest_path.read_text())
    if document.get("schema") != "jukupoly-library-replacements-v1":
        raise ValueError("unsupported replacement manifest schema")
    records = document.get("tracks")
    if not isinstance(records, list) or not records:
        raise ValueError("replacement manifest tracks must be a nonempty list")
    result = {}
    capabilities = 0
    for index, record in enumerate(records):
        fields = {
            "pack", "local_track", "source_name", "payload", "bytes",
            "sha256", "capability",
        }
        if not isinstance(record, dict) or set(record) != fields:
            raise ValueError(f"invalid replacement record {index}")
        pack = record["pack"]
        local_track = record["local_track"]
        if pack not in EXPECTED_TRACKS or not isinstance(local_track, int) or not (
                1 <= local_track <= EXPECTED_TRACKS[pack]):
            raise ValueError(f"invalid replacement target {pack}/{local_track}")
        key = (pack, local_track)
        if key in result:
            raise ValueError(f"duplicate replacement target {pack}/{local_track}")
        capability = record["capability"]
        if (not isinstance(capability, int) or capability & ~0x07 or
                not capability & build_jukupoly.JPS2_ENVELOPE_CAPABILITY):
            raise ValueError(f"invalid replacement capability for {pack}/{local_track}")
        payload = payload_directory / record["payload"]
        if not payload.is_file():
            raise ValueError(f"replacement payload is missing: {payload}")
        data = payload.read_bytes()
        if (len(data) != record["bytes"] or sha256(payload) != record["sha256"] or
                len(data) < 16 or data[:4] != b"JPS\2" or
                data[7] != capability):
            raise ValueError(f"replacement payload mismatch: {payload}")
        result[key] = {**record, "path": payload, "data": data}
        capabilities |= capability
    return result, capabilities


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--doom", type=Path, required=True,
                        help="vgmrips Doom_(PC).zip")
    parser.add_argument("--doom2", type=Path, required=True,
                        help="vgmrips Doom_II...zip")
    parser.add_argument("--output-dir", type=Path,
                        default=ROOT / "out" / "jukupoly-doom-library")
    parser.add_argument("--replacement-manifest", type=Path)
    parser.add_argument("--replacement-dir", type=Path)
    parser.add_argument(
        "--generic-conversion", action="store_true",
        help=("disable every song-specific melodic and allocation override; "
              "use only the converter's shared classification/selection policy"),
    )
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
    try:
        replacements, replacement_capabilities = load_replacements(
            args.replacement_manifest, args.replacement_dir,
        )
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        parser.error(str(exc))
    player = output / "JUKEBOX.COM"
    build_player(player, replacement_capabilities)

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
                overrides, prioritize_articulations = track_policy(
                    pack, local_track, args.generic_conversion,
                )
                payload, score = compile_track(
                    source, overrides, prioritize_articulations,
                )
                replacement = replacements.get((pack, local_track))
                if replacement is not None:
                    if replacement["source_name"] != source_name:
                        raise SystemExit(
                            f"replacement source mismatch for {pack}/{local_track}: "
                            f"{replacement['source_name']} != {source_name}"
                        )
                    payload = replacement["data"]
                    delivery_mode = "enhanced-replacement"
                    capability = replacement["capability"]
                else:
                    delivery_mode = "unchanged-v1"
                    capability = 0
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
                    "delivery_mode": delivery_mode,
                    "capability": capability,
                    "payload_sha256": hashlib.sha256(payload).hexdigest(),
                })

    readme = output / "README.TXT"
    readme.write_text(
        readme_text(catalog, archive_records, len(replacements)), newline="",
    )
    manifest = {
        "schema": "jukupoly-doom-library-v1",
        "player": {
            "filename": player.name,
            "bytes": player.stat().st_size,
            "sha256": sha256(player),
            "song_load_address": build_jukupoly.SONG_LOAD_ADDRESS,
        },
        "archives": archive_records,
        "delivery": {
            "enhanced_replacements": len(replacements),
            "unchanged_v1": len(catalog) - len(replacements),
            "player_capabilities": replacement_capabilities,
            "replacement_manifest": (
                None if args.replacement_manifest is None else
                args.replacement_manifest.name
            ),
        },
        "conversion_policy": {
            "generic_only": args.generic_conversion,
            "song_specific_melodic_overrides": not args.generic_conversion,
            "song_specific_allocation_overrides": not args.generic_conversion,
        },
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
