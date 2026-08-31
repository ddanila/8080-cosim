#!/usr/bin/env python3
"""Measure and lock the pre-OPL JukuPoly library-player budget."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import subprocess
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
SPINOFF = ROOT / "spinoffs" / "jukupoly"
FIRMWARE = SPINOFF / "firmware"
BASELINE = SPINOFF / "OPL-BASELINE.json"
CPU_HZ = 1_700_000
COM_ADDRESS = 0x0100
SONG_ADDRESS = 0x1800
SONG_HARD_LIMIT = 0x8000
STACK_ADDRESS = 0x9BFE

FIXTURES = (
    ("doomgate", "jukupoly-doomgate-vgz.json"),
    ("demons", "jukupoly-demons-vgz.json"),
    ("supaplex", "jukupoly-supaplex-main-vgz.json"),
    ("arkanoid", "jukupoly-arkanoid-ending-vgz.json"),
)


def run(command: list[str], *, stdout: bool = True) -> str:
    result = subprocess.run(
        command,
        cwd=ROOT,
        check=True,
        text=True,
        stdout=subprocess.PIPE if stdout else subprocess.DEVNULL,
    )
    return result.stdout if result.stdout is not None else ""


def symbols(listing: str) -> dict[str, int]:
    result: dict[str, int] = {}
    in_table = False
    for line in listing.splitlines():
        if line == "Symbol Table:":
            in_table = True
            continue
        if not in_table:
            continue
        match = re.match(r"^(\S+)\s+([0-9A-F]+)\s+\d+\s*$", line)
        if match:
            result[match.group(1)] = int(match.group(2), 16)
    required = {"sample_loop", "frame_tick", "player_start", "saved_sp",
                "test_manifest"}
    missing = sorted(required - result.keys())
    if missing:
        raise RuntimeError("assembler listing lacks symbols: " + ", ".join(missing))
    return result


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def build_tools(directory: Path) -> tuple[Path, Path]:
    profiler = directory / "jukupoly_baseline_test"
    renderer = directory / "render_jukupoly_wav"
    common = ["cc", "-std=c11", "-O2", "-Wall", "-Wextra", "-Werror"]
    run(common + [
        "-o", str(profiler),
        "tests/jukupoly_baseline_test.c", "cosim/i8080.c",
    ], stdout=False)
    run(common + [
        "-o", str(renderer),
        "spinoffs/jukupoly/tools/render_jukupoly_wav.c", "cosim/i8080.c",
        "-lm",
    ], stdout=False)
    return profiler, renderer


def build_player(directory: Path) -> tuple[Path, str, dict[str, int]]:
    player = directory / "JUKEBOX.cim"
    command = [
        str(ROOT / "third_party" / "zmac" / "src" / "zmac"),
        "--nmnv", "--zmac", "-8", "-P2=1", "-L", "-l",
        f"-I{FIRMWARE}", "-o", str(player),
        str(FIRMWARE / "jukupoly-player-0100.asm"),
    ]
    listing = run(command)
    return player, listing, symbols(listing)


def build_fixture(directory: Path, label: str, source_name: str) -> tuple[Path, Path]:
    standalone = directory / f"{label}.com"
    song = directory / f"{label}.jps"
    run([
        "python3", str(FIRMWARE / "build_jukupoly.py"),
        "--song", str(FIRMWARE / source_name),
        "--generated", str(directory / f"{label}.inc"),
        "--output", str(standalone),
        "--song-output", str(song),
    ])
    return standalone, song


def profile(profiler: Path, player: Path, song: Path,
            entry: int, label: str) -> dict:
    output = run([
        str(profiler), str(player), str(song), f"{entry:x}", label,
    ])
    return json.loads(output)


def render_hash(renderer: Path, image: Path, output: Path) -> dict:
    run([
        str(renderer), "--sample-rate", "48000", "--lead", "0", "--tail", "0",
        str(image), str(output),
    ])
    return {
        "source": image.name,
        "sample_rate_hz": 48_000,
        "sha256": sha256(output),
        "bytes": output.stat().st_size,
    }


def generate() -> dict:
    with tempfile.TemporaryDirectory(prefix="jukupoly-baseline.") as name:
        directory = Path(name)
        profiler, renderer = build_tools(directory)
        player, _listing, symbol = build_player(directory)
        binary = player.read_bytes()
        loop_start = symbol["sample_loop"] - COM_ADDRESS
        loop_end = symbol["frame_tick"] - COM_ADDRESS
        if not 0 <= loop_start < loop_end <= len(binary):
            raise RuntimeError("sample-loop symbols fall outside the player image")

        profiles = []
        standalone: dict[str, Path] = {}
        for label, source_name in FIXTURES:
            image, song = build_fixture(directory, label, source_name)
            standalone[label] = image
            measured = profile(
                profiler, player, song, symbol["player_start"], label,
            )
            measured["ten_percent_floor_hz"] = (
                measured["effective_sample_hz"] * 0.9
            )
            profiles.append(measured)

        reference_wavs = {
            label: render_hash(
                renderer, standalone[label], directory / f"{label}.wav",
            )
            for label in ("doomgate", "arkanoid")
        }

        rates = [item["effective_sample_hz"] for item in profiles]
        frame_rates = [item["music_frame_hz"] for item in profiles]
        largest = max(profiles, key=lambda item: item["jps_bytes"])
        player_end = COM_ADDRESS + len(binary)
        result = {
            "schema": "jukupoly-opl-baseline-v1",
            "cpu_hz": CPU_HZ,
            "accepted_sample_rate_reduction_percent": 10,
            "player": {
                "build": "library ABI-v1 (-P2=1)",
                "bytes": len(binary),
                "load_address": f"0x{COM_ADDRESS:04x}",
                "end_address_exclusive": f"0x{player_end:04x}",
                "song_load_address": f"0x{SONG_ADDRESS:04x}",
                "song_window_margin_bytes": SONG_ADDRESS - player_end,
                "declared_state_region_bytes": (
                    symbol["test_manifest"] - symbol["saved_sp"]
                ),
                "sample_loop_address": f"0x{symbol['sample_loop']:04x}",
                "frame_tick_address": f"0x{symbol['frame_tick']:04x}",
                "sample_loop_bytes": loop_end - loop_start,
                "sample_loop_sha256": hashlib.sha256(
                    binary[loop_start:loop_end]
                ).hexdigest(),
            },
            "memory_guards": {
                "jps_hard_limit_bytes": SONG_HARD_LIMIT - 1,
                "stack_address": f"0x{STACK_ADDRESS:04x}",
                "minimum_stack_margin_at_jps_hard_limit_bytes": (
                    STACK_ADDRESS - (SONG_ADDRESS + SONG_HARD_LIMIT)
                ),
                "largest_reproducible_fixture": largest["label"],
                "largest_reproducible_fixture_bytes": largest["jps_bytes"],
            },
            "measured_guards": {
                "minimum_effective_sample_hz": min(rates),
                "maximum_effective_sample_hz": max(rates),
                "ten_percent_floor_from_minimum_hz": min(rates) * 0.9,
                "minimum_music_frame_hz": min(frame_rates),
                "maximum_music_frame_hz": max(frame_rates),
            },
            "profiles": profiles,
            "reference_wavs": reference_wavs,
        }
        if not math.isclose(
                result["measured_guards"]["ten_percent_floor_from_minimum_hz"],
                min(rates) * 0.9):
            raise AssertionError("sample-rate floor calculation failed")
        return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=BASELINE)
    parser.add_argument("--check", action="store_true",
                        help="fail unless the committed report is current")
    args = parser.parse_args()

    result = generate()
    rendered = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.check:
        if not args.output.exists() or args.output.read_text() != rendered:
            raise SystemExit(f"{args.output} is missing or stale")
        action = "checked"
    else:
        args.output.write_text(rendered)
        action = "wrote"
    print(
        f"JUKUPOLY-BASELINE: {action} {args.output} "
        f"profiles={len(result['profiles'])} "
        f"sample={result['measured_guards']['minimum_effective_sample_hz']:.1f}"
        f"..{result['measured_guards']['maximum_effective_sample_hz']:.1f}Hz "
        f"floor={result['measured_guards']['ten_percent_floor_from_minimum_hz']:.1f}Hz"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
