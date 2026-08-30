#!/usr/bin/env python3
"""Focused audio-container and three-voice timeline guard for JukuPoly WAV."""

from __future__ import annotations

import array
import math
import sys
import wave
from pathlib import Path


def fail(message: str) -> None:
    raise SystemExit(f"JUKUPOLY-WAV: FAIL {message}")


def rms(samples: array.array[int], rate: int, start: float, end: float) -> float:
    first = round(start * rate)
    last = round(end * rate)
    window = samples[first:last]
    if not window:
        fail(f"empty analysis window {start:.2f}..{end:.2f}s")
    return math.sqrt(sum(value * value for value in window) / len(window))


def main() -> None:
    if len(sys.argv) != 2:
        fail("usage: jukuravi_wav_test.py three-voice.wav")
    path = Path(sys.argv[1])
    with wave.open(str(path), "rb") as source:
        if source.getnchannels() != 1 or source.getsampwidth() != 2:
            fail("output is not 16-bit mono PCM")
        rate = source.getframerate()
        frames = source.getnframes()
        raw = source.readframes(frames)
    if rate != 48_000:
        fail(f"unexpected test sample rate {rate}")
    duration = frames / rate
    if not 9.50 < duration < 9.75:
        fail(f"unexpected duration {duration:.6f}s")

    samples = array.array("h")
    samples.frombytes(raw)
    if sys.byteorder != "little":
        samples.byteswap()
    if max(abs(value) for value in samples) < 25_000:
        fail("rendered pulses do not reach the expected level")
    if any(samples[: round(0.20 * rate)]):
        fail("lead-in is not silent")

    one_voice = rms(samples, rate, 0.75, 1.75)
    two_voices = rms(samples, rate, 2.75, 3.75)
    three_voices = rms(samples, rate, 4.75, 5.75)
    if not (one_voice > 500 and two_voices > one_voice * 1.05 and
            three_voices > two_voices * 1.05):
        fail(
            "voice entrances lack increasing energy: "
            f"{one_voice:.1f}/{two_voices:.1f}/{three_voices:.1f}"
        )
    print(
        "JUKUPOLY-WAV: PASS "
        f"rate={rate}Hz duration={duration:.3f}s "
        f"rms={one_voice:.1f}/{two_voices:.1f}/{three_voices:.1f}"
    )


if __name__ == "__main__":
    main()
