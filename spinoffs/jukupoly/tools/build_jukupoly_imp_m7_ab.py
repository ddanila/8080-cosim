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
TARGET_SHAPE_OUTPUT = ROOT / "out" / "jukupoly-imp-target-shape-ab"
TARGET_SHAPE_DISK_NAME = "jukupoly-imp-target-shape-ab.cpm"
RENDERER_SOURCE = SPINOFF / "tools" / "render_jukupoly_wav.c"
I8080_SOURCE = ROOT / "cosim" / "i8080.c"
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

TARGET_SHAPE_SCORES = (
    (
        "REAROLD.COM", "source-egt-rearticulation",
        FIRMWARE / "jukupoly-imp-30s-rearticulation-m7.json",
        "Control: merged lead; target sustain mode copied from source EGT.",
    ),
    (
        "REARNEW.COM", "target-shape-rearticulation",
        FIRMWARE / "jukupoly-imp-30s-rearticulation-target-shape-m7.json",
        "Same lead; target sustain mode selected by oracle envelope shape.",
    ),
    (
        "DETOLD.COM", "source-egt-detuned-members",
        FIRMWARE / "jukupoly-imp-30s-detuned-m7.json",
        "Control: source-member detuning with source-EGT target envelopes.",
    ),
    (
        "DETNEW.COM", "target-shape-detuned-members",
        FIRMWARE / "jukupoly-imp-30s-detuned-target-shape-m7.json",
        "Source-member detuning with oracle-selected target envelopes.",
    ),
)

# MVI A,3 / OUT 04h / IN 05h / ANI 0fh / CPI 06h / JZ target.  The standalone
# Escape build contains this sequence once in the frame poll and once in the
# key-release wait.  Checking the emitted machine code prevents the comparison
# README and protocol from silently getting ahead of the binaries again.
ESCAPE_POLL_PREFIX = bytes((
    0x3E, 0x03, 0xD3, 0x04, 0xDB, 0x05, 0xE6, 0x0F, 0xFE, 0x06, 0xCA,
))


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
        escape_polling=True,
    )
    return image, score, metadata


def readme_text(files: list[dict], *, target_shape: bool = False) -> str:
    if target_shape:
        lines = [
            "JukuPoly Imp target-envelope physical A/B",
            "=========================================",
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
            "Keep one volume/control position for all four runs.",
            "Compare each OLD/NEW pair for lead fade and note separation.",
            "",
            "Music: Robert Prince; original game: id Software.",
            "Source OPL3 pack: vgmrips.net / NewRisingSun.",
            "JukuPoly conversion/player: 8080-cosim contributors.",
            "",
        ))
        return "\r\n".join(lines)
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


def render_profile(renderer: Path, image: Path, wav: Path,
                   escape_at: float | None = None) -> dict:
    command = [
        str(renderer), "--lead", "0", "--tail", "0",
        "--max-seconds", "40" if escape_at is None else "5",
    ]
    if escape_at is not None:
        command.extend(("--escape-at", str(escape_at)))
    command.extend((str(image), str(wav)))
    result = subprocess.run(
        command, cwd=ROOT, check=True, text=True, stdout=subprocess.PIPE,
    )
    fields = {}
    for token in result.stdout.strip().split()[2:]:
        if "=" in token:
            key, value = token.split("=", 1)
            fields[key] = value
    try:
        return {
            "run_seconds": float(fields["run"][:-1]),
            "pit_writes": int(fields["writes"]),
            "pulse_intervals": int(fields["intervals"]),
            "keyboard_polls": int(fields["keyboard_polls"]),
            "escape": fields["escape"],
        }
    except (KeyError, ValueError) as exc:
        raise ValueError(
            f"unrecognized renderer output for {image.name}: {result.stdout.strip()}"
        ) from exc


def qualify_players(files: list[dict], built: dict[str, Path]) -> dict:
    compiler = shutil.which("cc")
    if not compiler:
        raise OSError("required C compiler is missing: cc")
    escape_at = 1.0
    with tempfile.TemporaryDirectory(prefix="jukupoly-imp-m7-qualify.") as name:
        temporary = Path(name)
        renderer = temporary / "render_jukupoly_wav"
        subprocess.run([
            compiler, "-std=c11", "-O2", "-Wall", "-Wextra", "-Werror",
            "-o", str(renderer), str(RENDERER_SOURCE), str(I8080_SOURCE), "-lm",
        ], cwd=ROOT, check=True)
        for item in files:
            stem = Path(item["filename"]).stem.lower()
            full = render_profile(
                renderer, built[item["filename"]], temporary / f"{stem}-full.wav",
            )
            escaped = render_profile(
                renderer, built[item["filename"]],
                temporary / f"{stem}-escape.wav", escape_at,
            )
            item["cycle_qualification"] = {
                "full": full,
                "injected_escape": escaped,
            }
    return {
        "cpu_hz": 1_700_000,
        "pit_hz": 2_000_000,
        "injected_escape_at_seconds": escape_at,
        "gates": {
            "all_full_runs_polled_keyboard": all(
                item["cycle_qualification"]["full"]["keyboard_polls"] >= 1500
                for item in files
            ),
            "all_injected_escapes_accepted": all(
                item["cycle_qualification"]["injected_escape"]["escape"] ==
                "accepted" for item in files
            ),
            "all_injected_escapes_returned_promptly": all(
                item["cycle_qualification"]["injected_escape"]["run_seconds"] <
                1.1 for item in files
            ),
        },
    }


def generate(output: Path, *, target_shape: bool = False) -> dict:
    for tool in ("mkfs.cpm", "cpmcp", "cpmls"):
        if not shutil.which(tool):
            raise OSError(f"required cpmtools command is missing: {tool}")
    output.mkdir(parents=True, exist_ok=True)
    files = []
    source_vgm = None
    built: dict[str, Path] = {}
    scores = TARGET_SHAPE_SCORES if target_shape else SCORES
    for filename, strategy, score_path, description in scores:
        image, score, metadata = build_com(score_path)
        vgm_hash = score["source"]["vgm_sha256"]
        if source_vgm is None:
            source_vgm = vgm_hash
        elif source_vgm != vgm_hash:
            raise ValueError("comparison scores do not identify one source VGM")
        path = output / filename
        path.write_bytes(image)
        escape_poll_sites = image.count(ESCAPE_POLL_PREFIX)
        if image[0] != 0xf3:
            raise ValueError(f"{filename} is not a standalone player")
        if escape_poll_sites != 2:
            raise ValueError(
                f"{filename} has {escape_poll_sites} Escape poll sites, expected 2"
            )
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
            "standalone_player": True,
            "escape_polling_enabled": True,
            "escape_poll_sites": escape_poll_sites,
            "duration_frames": score["conversion"]["duration_frames"],
            "first_tone_frame": first_tone_frame(score),
        })
    readme = output / "README.TXT"
    readme.write_text(readme_text(files, target_shape=target_shape), newline="")
    built[readme.name] = readme

    disk = output / (
        TARGET_SHAPE_DISK_NAME if target_shape else DISK_NAME
    )
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
    qualification = qualify_players(files, built)
    if not all(qualification["gates"].values()):
        failed = sorted(
            key for key, value in qualification["gates"].items() if not value
        )
        raise ValueError(f"player qualification failed: {', '.join(failed)}")
    result = {
        "schema": (
            "jukupoly-imp-target-shape-physical-ab-v1"
            if target_shape else "jukupoly-imp-m7-physical-ab-v2"
        ),
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
        "cycle_qualification": qualification,
        "physical_protocol": {
            "order": [
                Path(item["filename"]).stem for item in files
            ] if target_shape else ["IMPV1", "IMPREAR", "IMPDET"],
            "same_volume": True,
            "escape_polling": "standalone player build option -P8=1",
            "listen_for": [
                "low-lead onset", "low-lead fade", "beating or roughness",
                "percussion balance", "Escape and CP/M return",
            ],
            "promotion_rule": (
                "promote target-shape fitting only when each NEW candidate "
                "has a clearly more OPL-like fade than its OLD control and "
                "all four programs return cleanly"
                if target_shape else
                "keep unchanged-v1 unless a source-derived candidate is "
                "clearly preferable and all three programs return cleanly"
            ),
        },
    }
    if target_shape:
        result["independent_pcm_audit"] = {
            "path": "OPL-IMP-TARGET-SHAPE-M7.json",
            "sha256": sha256(SPINOFF / "OPL-IMP-TARGET-SHAPE-M7.json"),
            "all_gates_pass": all(json.loads(
                (SPINOFF / "OPL-IMP-TARGET-SHAPE-M7.json").read_text()
            )["gates"].values()),
        }
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--report", type=Path)
    parser.add_argument(
        "--target-shape", action="store_true",
        help="build OLD/NEW envelope-shape pairs instead of the original trio",
    )
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    try:
        output_dir = args.output_dir or (
            TARGET_SHAPE_OUTPUT if args.target_shape else DEFAULT_OUTPUT
        )
        result = generate(
            output_dir.resolve(), target_shape=args.target_shape,
        )
    except (OSError, ValueError, subprocess.CalledProcessError,
            build_jukupoly.SongError) as exc:
        parser.error(str(exc))
    rendered = json.dumps(result, indent=2, sort_keys=True) + "\n"
    report = args.report or output_dir / "manifest.json"
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
