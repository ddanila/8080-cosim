#!/usr/bin/env python3
"""Regression for the packed 4-bit Juku standalone PCM player."""

from __future__ import annotations

import math
import re
import subprocess
import sys
import tempfile
import unittest
import wave
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FIRMWARE = ROOT / "spinoffs" / "jukupoly" / "firmware"
TOOLS = ROOT / "spinoffs" / "jukupoly" / "tools"
sys.path.insert(0, str(FIRMWARE))

import build_jukupoly_pcm as pcm  # noqa: E402


class JukuPolyPcmTest(unittest.TestCase):
    def test_packed_player_rate_duration_and_return(self) -> None:
        with tempfile.TemporaryDirectory(prefix="jukupoly-pcm-test.") as name:
            directory = Path(name)
            source = directory / "source.wav"
            rate = 16_000
            frames = round(rate * 0.25)
            with wave.open(str(source), "wb") as output:
                output.setnchannels(1)
                output.setsampwidth(2)
                output.setframerate(rate)
                data = bytearray()
                for index in range(frames):
                    value = round(
                        24_000 * math.sin(2 * math.pi * 440 * index / rate)
                    )
                    data.extend(value.to_bytes(2, "little", signed=True))
                output.writeframes(data)

            image, nibbles, metadata = pcm.build(
                source, pcm.DEFAULT_CPU_HZ, 0.96,
            )
            program = directory / "tone.com"
            program.write_bytes(image)
            self.assertEqual(len(nibbles) % 2, 0)
            self.assertEqual(metadata["maximum_code"], 15)
            self.assertTrue(all(1 <= value <= 15 for value in nibbles))
            self.assertAlmostEqual(
                float(metadata["target_rate_hz"]), 8056.872038, places=5,
            )

            renderer = directory / "render_jukupoly_wav"
            subprocess.run([
                "cc", "-std=c11", "-O2", "-Wall", "-Wextra", "-Werror",
                "-o", str(renderer), str(TOOLS / "render_jukupoly_wav.c"),
                str(ROOT / "cosim" / "i8080.c"), "-lm",
            ], check=True, cwd=ROOT)
            rendered = directory / "tone-rendered.wav"
            result = subprocess.run([
                str(renderer), "--lead", "0", "--tail", "0",
                str(program), str(rendered),
            ], check=True, cwd=ROOT, stdout=subprocess.PIPE, text=True)
            match = re.search(
                r"run=([0-9.]+)s.*writes=([0-9]+)", result.stdout,
            )
            self.assertIsNotNone(match)
            assert match is not None
            run_seconds = float(match.group(1))
            writes = int(match.group(2))
            self.assertLess(
                # The renderer includes setup, final silence, RET, and HLT;
                # the audio body itself remains cycle-fixed at 422/pair.
                abs(run_seconds - float(metadata["duration_seconds"])), 0.004,
            )
            self.assertEqual(writes, len(nibbles) + 4)
            with wave.open(str(rendered), "rb") as audio:
                self.assertGreater(audio.getnframes(), 0)


if __name__ == "__main__":
    unittest.main()
