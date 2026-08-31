#!/usr/bin/env python3
"""Measure the guarded JPS v2 envelope player against the frozen G0 baseline."""

from __future__ import annotations

import argparse
import hashlib
import json
import tempfile
from pathlib import Path

import report_jukupoly_baseline as baseline


ROOT = Path(__file__).resolve().parents[3]
SPINOFF = ROOT / "spinoffs" / "jukupoly"
FIRMWARE = SPINOFF / "firmware"
REPORT = SPINOFF / "OPL-ENVELOPE-M3.json"
CPU_HZ = 1_700_000
COM_ADDRESS = 0x0100
SONG_ADDRESS = 0x1800


def build_enhanced_player(directory: Path) -> tuple[Path, dict[str, int]]:
    player = directory / "JUKEBOX-V2.cim"
    command = [
        str(ROOT / "third_party" / "zmac" / "src" / "zmac"),
        "--nmnv", "--zmac", "-8", "-P2=1", "-P4=1", "-L", "-l",
        f"-I{FIRMWARE}", "-o", str(player),
        str(FIRMWARE / "jukupoly-player-0100.asm"),
    ]
    listing = baseline.run(command)
    return player, baseline.symbols(listing)


def build_v2_fixture(directory: Path) -> tuple[Path, Path]:
    standalone = directory / "envelope.com"
    song = directory / "envelope.jps"
    baseline.run([
        "python3", str(FIRMWARE / "build_jukupoly.py"),
        "--song", str(FIRMWARE / "jukupoly-envelope-v2-test.json"),
        "--generated", str(directory / "envelope.inc"),
        "--output", str(standalone),
        "--song-output", str(song),
    ])
    return standalone, song


def enhanced_profile(profiler: Path, player: Path, song: Path,
                     symbols: dict[str, int], label: str) -> dict:
    output = baseline.run([
        str(profiler), str(player), str(song),
        f"{symbols['player_start']:x}", label,
        f"{symbols['envelope_dispatch_init']:x}",
    ])
    return json.loads(output)


def exact_v1_profile(profile: dict, frozen: dict) -> bool:
    ignored = {
        "label", "com_bytes", "mutated_player_bytes", "ten_percent_floor_hz",
    }
    return {
        key: value for key, value in profile.items() if key not in ignored
    } == {
        key: value for key, value in frozen.items() if key not in ignored
    }


def generate() -> dict:
    frozen = json.loads(baseline.BASELINE.read_text())
    frozen_doomgate = next(
        item for item in frozen["profiles"] if item["label"] == "doomgate"
    )
    with tempfile.TemporaryDirectory(prefix="jukupoly-envelope-report.") as name:
        directory = Path(name)
        profiler, _renderer = baseline.build_tools(directory)
        player, symbols = build_enhanced_player(directory)
        binary = player.read_bytes()
        loop_start = symbols["sample_loop"] - COM_ADDRESS
        loop_end = symbols["frame_tick"] - COM_ADDRESS
        loop_hash = hashlib.sha256(binary[loop_start:loop_end]).hexdigest()

        _standalone, v1_song = baseline.build_fixture(
            directory, "doomgate", "jukupoly-doomgate-vgz.json",
        )
        _v2_standalone, v2_song = build_v2_fixture(directory)
        v1 = enhanced_profile(
            profiler, player, v1_song, symbols,
            "enhanced-player-v1-doomgate",
        )
        v2 = enhanced_profile(
            profiler, player, v2_song, symbols,
            "three-envelope-percussion-stress",
        )
        v2_floor = frozen_doomgate["ten_percent_floor_hz"]
        gates = {
            "frozen_v1_profile_exact": exact_v1_profile(v1, frozen_doomgate),
            "sample_loop_hash_exact": (
                loop_hash == frozen["player"]["sample_loop_sha256"]
            ),
            "v2_sample_rate_above_floor": (
                v2["effective_sample_hz"] >= v2_floor
            ),
            "v2_music_clock_within_one_percent": (
                abs(v2["music_frame_hz"] - 50.0) <= 0.5
            ),
            "player_below_song_window": (
                COM_ADDRESS + len(binary) < SONG_ADDRESS
            ),
            "v2_jps_below_soft_limit": v2["jps_bytes"] < 30 * 1024,
            "v2_uses_explicit_guarded_batch": (
                129 <= v2["frame_samples"] <= 143
            ),
        }
        if not all(gates.values()):
            failed = ", ".join(key for key, value in gates.items() if not value)
            raise RuntimeError(
                "JPS v2 envelope gate failure: " + failed
                + f" (sample={v2['effective_sample_hz']:.3f} Hz, "
                + f"music={v2['music_frame_hz']:.3f} Hz, "
                + f"max-frame={v2['frame_cycles']['max']} cycles)"
            )
        return {
            "schema": "jukupoly-opl-envelope-m3-report-v1",
            "cpu_hz": CPU_HZ,
            "frozen_baseline": {
                "path": "OPL-BASELINE.json",
                "sample_loop_sha256": frozen["player"]["sample_loop_sha256"],
                "doomgate_floor_hz": v2_floor,
            },
            "enhanced_player": {
                "build": "library ABI v1+v2 (-P2=1 -P4=1)",
                "bytes": len(binary),
                "end_address_exclusive": f"0x{COM_ADDRESS + len(binary):04x}",
                "song_window_margin_bytes": SONG_ADDRESS - (
                    COM_ADDRESS + len(binary)
                ),
                "declared_state_region_bytes": (
                    symbols["test_manifest"] - symbols["saved_sp"]
                ),
                "sample_loop_bytes": loop_end - loop_start,
                "sample_loop_sha256": loop_hash,
            },
            "v1_compatibility_profile": v1,
            "v2_stress_profile": v2,
            "v2_sample_rate_floor_hz": v2_floor,
            "gates": gates,
        }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=REPORT)
    parser.add_argument("--check", action="store_true")
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
    profile = result["v2_stress_profile"]
    print(
        f"JUKUPOLY-ENVELOPE-REPORT: {action} {args.output} "
        f"player={result['enhanced_player']['bytes']} bytes "
        f"sample={profile['effective_sample_hz']:.1f}Hz "
        f"music={profile['music_frame_hz']:.3f}Hz "
        f"floor={result['v2_sample_rate_floor_hz']:.1f}Hz"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
