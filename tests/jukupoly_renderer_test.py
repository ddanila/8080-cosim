#!/usr/bin/env python3
"""Regression for standalone and reusable-library cycle WAV rendering."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
import wave
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "spinoffs" / "jukupoly" / "tools"
sys.path.insert(0, str(TOOLS))

import report_jukupoly_baseline as baseline  # noqa: E402
import report_jukupoly_vibrato_target as target_report  # noqa: E402
import render_jukupoly_library as library_renderer  # noqa: E402


class JukuPolyRendererTest(unittest.TestCase):
    def test_current_best_render_rejects_control_only_library(self) -> None:
        with tempfile.TemporaryDirectory(prefix="jukupoly-control-guard.") as name:
            directory = Path(name)
            (directory / "JUKEBOX.COM").write_bytes(b"control")
            (directory / "catalog.json").write_text(json.dumps({
                "delivery": {
                    "player_capabilities": 0,
                    "enhanced_replacements": 0,
                },
                "tracks": [{"title": "control"}],
            }))
            with self.assertRaisesRegex(ValueError, "at least 1 required"):
                library_renderer.render_library(
                    directory, directory / "renders", "control", None, 1,
                )

    def test_reusable_player_jps_mode_renders_and_validates(self) -> None:
        with tempfile.TemporaryDirectory(prefix="jukupoly-renderer-test.") as name:
            directory = Path(name)
            renderer = directory / "render_jukupoly_wav"
            subprocess.run([
                "cc", "-std=c11", "-O2", "-Wall", "-Wextra", "-Werror",
                "-o", str(renderer),
                str(TOOLS / "render_jukupoly_wav.c"),
                str(ROOT / "cosim" / "i8080.c"), "-lm",
            ], check=True, cwd=ROOT)
            standalone, song = baseline.build_fixture(
                directory, "renderer", "jukupoly-library-v1-test.json",
            )
            player, symbols = target_report.build_player(
                directory, "renderer-player",
            )
            standalone_wav = directory / "standalone.wav"
            library_wav = directory / "library.wav"
            common = [
                str(renderer), "--sample-rate", "8000", "--lead", "0",
                "--tail", "0",
            ]
            subprocess.run(
                [*common, str(standalone), str(standalone_wav)],
                check=True, cwd=ROOT, stdout=subprocess.PIPE, text=True,
            )
            subprocess.run([
                *common, "--song", str(song), "--entry",
                f"{symbols['player_start']:x}", "--prepare",
                f"{symbols['envelope_dispatch_init']:x}", str(player),
                str(library_wav),
            ], check=True, cwd=ROOT, stdout=subprocess.PIPE, text=True)
            with wave.open(str(standalone_wav), "rb") as standalone_audio:
                standalone_frames = standalone_audio.getnframes()
            with wave.open(str(library_wav), "rb") as library_audio:
                library_frames = library_audio.getnframes()
                samples = library_audio.readframes(library_frames)
            # The P4 library executes its one-time dispatcher preparation
            # before player_start; that setup time is intentionally present
            # in the cycle render but remains below one 20 ms music frame.
            self.assertLess(abs(standalone_frames - library_frames), 160)
            self.assertNotEqual(samples, bytes(len(samples)))

            corrupt = directory / "corrupt.jps"
            payload = bytearray(song.read_bytes())
            payload[4:6] = (len(payload) + 1).to_bytes(2, "little")
            corrupt.write_bytes(payload)
            rejected = subprocess.run([
                *common, "--song", str(corrupt), "--entry",
                f"{symbols['player_start']:x}", str(player),
                str(directory / "rejected.wav"),
            ], cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            self.assertNotEqual(rejected.returncode, 0)


if __name__ == "__main__":
    unittest.main()
