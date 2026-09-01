#!/usr/bin/env python3
"""Build a reproducible three-way physical Imp M7 comparison disk."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
SPINOFF = ROOT / "spinoffs" / "jukupoly"
FIRMWARE = SPINOFF / "firmware"
DEFAULT_OUTPUT = ROOT / "out" / "jukupoly-imp-m7-physical-ab"
DISK_NAME = "jukupoly-imp-m7-physical-ab.cpm"
sys.path.insert(0, str(FIRMWARE))

import build_doom_library  # noqa: E402
import build_jukupoly  # noqa: E402


SCORES = (
    (
        "IMPV1.COM", "unchanged-v1",
        FIRMWARE / "jukupoly-imp-30s-v1.json",
        "Control: the low lead first appears at 14.12 seconds.",
    ),
    (
        "IMPREAR.COM", "bounded-rearticulation",
        FIRMWARE / "jukupoly-imp-30s-rearticulation-m7.json",
        "Immediate merged low lead with bounded ADSR re-triggers.",
    ),
    (
        "IMPDET.COM", "detuned-source-members",
        FIRMWARE / "jukupoly-imp-30s-detuned-m7.json",
        "Immediate three-member low lead at source-derived phase steps.",
    ),
)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def first_tone_frame(score: dict) -> int | None:
    frame = 0
    for row in score["rows"]:
        if any(field in row for field in ("tone1", "tone2", "tone3")):
            return frame
        frame += row["frames"]
    return None


def build_com(score_path: Path) -> tuple[bytes, dict, dict]:
    score = json.loads(score_path.read_text())
    generated, metadata = build_jukupoly.compile_song(score)
    image = build_jukupoly.assemble(
        generated, metadata["mod_effects"], metadata["enhanced_envelopes"],
        metadata["enhanced_tremolo"], metadata["enhanced_vibrato"],
    )
    return image, score, metadata


def readme_text(files: list[dict]) -> str:
    lines = [
        "JukuPoly Imp M7 physical A/B",
        "=============================",
        "",
        "Run these 30-second excerpts from CP/M, in this order:",
        "",
    ]
    for item in files:
        lines.extend((
            f"  B:{Path(item['filename']).stem}",
            f"    {item['description']}",
        ))
    lines.extend((
        "",
        "ESC stops any excerpt and returns to CP/M.",
        "Use the same volume/control position for all three runs.",
        "Assess lead onset, fade, beating/roughness, drums, and stability.",
        "",
        "Music: Robert Prince; original game: id Software.",
        "Source OPL3 pack: vgmrips.net / NewRisingSun.",
        "JukuPoly conversion/player: 8080-cosim contributors.",
        "",
    ))
    return "\r\n".join(lines)


def cpm(arguments: list[str], *, capture: bool = False) -> str:
    result = subprocess.run(
        arguments, cwd=SPINOFF, check=True, text=capture,
        stdout=subprocess.PIPE if capture else None,
    )
    return result.stdout if capture else ""


def generate(output: Path) -> dict:
    for tool in ("mkfs.cpm", "cpmcp", "cpmls"):
        if not shutil.which(tool):
            raise OSError(f"required cpmtools command is missing: {tool}")
    output.mkdir(parents=True, exist_ok=True)
    files = []
    source_vgm = None
    built: dict[str, Path] = {}
    for filename, strategy, score_path, description in SCORES:
        image, score, metadata = build_com(score_path)
        vgm_hash = score["source"]["vgm_sha256"]
        if source_vgm is None:
            source_vgm = vgm_hash
        elif source_vgm != vgm_hash:
            raise ValueError("comparison scores do not identify one source VGM")
        path = output / filename
        path.write_bytes(image)
        built[filename] = path
        files.append({
            "filename": filename,
            "strategy": strategy,
            "description": description,
            "score": score_path.name,
            "score_sha256": sha256(score_path),
            "schema": score["schema"],
            "bytes": len(image),
            "sha256": sha256_bytes(image),
            "rows": metadata["rows"],
            "pcm_bytes": metadata["pcm_bytes"],
            "frame_samples": metadata["frame_samples"],
            "target_sample_hz": metadata["target_sample_hz"],
            "duration_frames": score["conversion"]["duration_frames"],
            "first_tone_frame": first_tone_frame(score),
        })
    readme = output / "README.TXT"
    readme.write_text(readme_text(files), newline="")
    built[readme.name] = readme

    disk = output / DISK_NAME
    with tempfile.TemporaryDirectory(prefix="jukupoly-imp-m7-ab.") as name:
        temporary = Path(name)
        logical = temporary / "comparison-logical.cpm"
        extracted = temporary / "extracted"
        extracted.mkdir()
        cpm(["mkfs.cpm", "-f", build_doom_library.DISK_FORMAT, str(logical)])
        for filename, path in built.items():
            cpm([
                "cpmcp", "-f", build_doom_library.DISK_FORMAT, str(logical),
                str(path), f"0:{filename}",
            ])
        listing = cpm([
            "cpmls", "-f", build_doom_library.DISK_FORMAT, "-d", str(logical),
        ], capture=True)
        for filename, original in built.items():
            target = extracted / filename
            cpm([
                "cpmcp", "-f", build_doom_library.DISK_FORMAT, str(logical),
                f"0:{filename}", str(target),
            ])
            if target.read_bytes() != original.read_bytes():
                raise ValueError(f"CP/M round-trip mismatch: {filename}")
        build_doom_library.logical_to_native(logical, disk)
    directory = output / "directory.txt"
    directory.write_text(listing)
    return {
        "schema": "jukupoly-imp-m7-physical-ab-v1",
        "source_vgm_sha256": source_vgm,
        "disk": {
            "filename": disk.name,
            "format": "Juku native cylinder-interleaved 800 KiB",
            "bytes": disk.stat().st_size,
            "sha256": sha256(disk),
            "directory_sha256": sha256(directory),
            "readme_sha256": sha256(readme),
            "cpm_round_trip_verified": True,
        },
        "files": files,
        "physical_protocol": {
            "order": ["IMPV1", "IMPREAR", "IMPDET"],
            "same_volume": True,
            "listen_for": [
                "low-lead onset", "low-lead fade", "beating or roughness",
                "percussion balance", "Escape and CP/M return",
            ],
            "promotion_rule": (
                "keep unchanged-v1 unless a source-derived candidate is "
                "clearly preferable and all three programs return cleanly"
            ),
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--report", type=Path)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    try:
        result = generate(args.output_dir.resolve())
    except (OSError, ValueError, subprocess.CalledProcessError,
            build_jukupoly.SongError) as exc:
        parser.error(str(exc))
    rendered = json.dumps(result, indent=2, sort_keys=True) + "\n"
    report = args.report or args.output_dir / "manifest.json"
    if args.check:
        if report.read_text() != rendered:
            raise SystemExit(f"{report} is missing or stale")
        action = "checked"
    else:
        report.write_text(rendered)
        action = "wrote"
    print(
        f"JUKUPOLY-IMP-M7-AB: {action} {report} "
        f"disk={result['disk']['sha256'][:16]} files={len(result['files'])}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
