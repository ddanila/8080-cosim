#!/usr/bin/env python3
"""Import the credited TDK four-channel ProTracker tune into JukuPoly.

The importer is intentionally hash-locked to the inspected module.  It maps
MOD channels 1, 2, and 4 to Juku tone channels, treats channel 3 primarily as
percussion, compiles the effects used by this tune, and retains two small PCM
fragments which fit in a CP/M transient.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import math
from dataclasses import dataclass
from pathlib import Path


EXPECTED_SHA256 = "c9d89b05ed00ba80a93ec5f3c6448a40d925d0b65ad1eba3beb27234c7878c3e"
EXPECTED_MD5 = "d1b288d964ac4f7acb3216d0d9dfab77"
# The ABI-v2 effect handler consumes appreciably more time than the original
# player frame.  At the measured 1.70 MHz effective CPU rate, 139 hot-loop
# iterations plus that frame work land near 50 Hz and average about 6.94 kHz.
TARGET_RATE = 6940
FRAME_SAMPLES = 139
TONE_MAP = {0: "tone1", 1: "tone2", 3: "tone3"}
PCM_PERCUSSION = {1: 1, 2: 2, 13: 3}
NON_TONAL = {1, 2, 6, 8, 11, 12, 13, 14, 17, 18}


class ModError(ValueError):
    pass


@dataclass
class Sample:
    number: int
    name: str
    data: bytes
    finetune: int
    volume: int
    loop_start: int
    loop_length: int


@dataclass
class Event:
    sample: int
    period: int
    effect: int
    parameter: int


@dataclass
class Channel:
    sample: int = 0
    period: int = 0
    volume: int = 0
    volume_slide_memory: int = 0
    porta_memory: int = 0
    porta_target: int = 0


def parse_module(data: bytes) -> tuple[list[Sample], list[int], list[list[list[Event]]]]:
    if len(data) < 1084 or data[1080:1084] != b"M.K.":
        raise ModError("only a 31-sample, four-channel M.K. module is supported")
    song_length = data[950]
    if not 1 <= song_length <= 128:
        raise ModError(f"invalid song length {song_length}")
    orders = list(data[952:952 + song_length])
    pattern_count = max(orders) + 1
    sample_at = 1084 + pattern_count * 1024
    if sample_at > len(data):
        raise ModError("truncated pattern data")

    samples: list[Sample] = []
    for index in range(31):
        at = 20 + index * 30
        name = data[at:at + 22].rstrip(b"\0").decode("latin1", "replace")
        length = int.from_bytes(data[at + 22:at + 24], "big") * 2
        finetune = data[at + 24] & 15
        if finetune >= 8:
            finetune -= 16
        volume = min(64, data[at + 25])
        loop_start = int.from_bytes(data[at + 26:at + 28], "big") * 2
        loop_length = int.from_bytes(data[at + 28:at + 30], "big") * 2
        payload = data[sample_at:sample_at + length]
        if len(payload) != length:
            raise ModError(f"truncated sample {index + 1}")
        samples.append(Sample(index + 1, name, payload, finetune, volume,
                              loop_start, loop_length))
        sample_at += length
    if sample_at != len(data):
        raise ModError(f"unexpected trailing module data: {len(data) - sample_at} bytes")

    patterns: list[list[list[Event]]] = []
    for pattern in range(pattern_count):
        pattern_at = 1084 + pattern * 1024
        rows: list[list[Event]] = []
        for row in range(64):
            events: list[Event] = []
            for channel in range(4):
                at = pattern_at + (row * 4 + channel) * 4
                raw = data[at:at + 4]
                sample = (raw[0] & 0xF0) | (raw[2] >> 4)
                period = ((raw[0] & 0x0F) << 8) | raw[1]
                events.append(Event(sample, period, raw[2] & 0x0F, raw[3]))
            rows.append(events)
        patterns.append(rows)
    return samples, orders, patterns


def phase_step(period: int, finetune: int) -> int:
    if period <= 0:
        raise ModError(f"invalid phase period {period}")
    # MOD period 428 is C-2.  Map it to scientific C3: a useful register for
    # the Juku speaker while preserving every interval in the score.
    frequency = 130.81278265 * 428.0 / period * 2.0 ** (finetune / 96.0)
    return max(1, min(0x7FFF, round(frequency * 65536.0 / TARGET_RATE)))


def engine_volume(mod_volume: int) -> int:
    return max(0, min(15, round(mod_volume * 15 / 64)))


def editor_volume(nibble: int) -> int:
    return max(1, min(16, round(nibble * 16 / 15)))


def signed_samples(payload: bytes) -> list[int]:
    return [value - 256 if value >= 128 else value for value in payload]


def resample_u4(payload: bytes, source_rate: float, normalize: bool = False) -> list[int]:
    source = signed_samples(payload)
    if not source:
        raise ModError("cannot resample an empty sample")
    count = max(1, round(len(source) * TARGET_RATE / source_rate))
    peak = max(abs(value) for value in source) or 1
    scale = 120.0 / peak if normalize else 1.0
    output: list[int] = []
    for index in range(count):
        position = index * source_rate / TARGET_RATE
        left = min(len(source) - 1, int(position))
        right = min(len(source) - 1, left + 1)
        fraction = position - left
        value = (source[left] * (1.0 - fraction) + source[right] * fraction) * scale
        output.append(max(1, min(15, round(8.0 + value * 7.0 / 128.0))))
    # Ease the PWM midpoint down to the engine's no-pulse silence.  This turns
    # the otherwise abrupt DC transition into a 20 ms tail.
    output.extend(round(8 * (FRAME_SAMPLES - i - 1) / FRAME_SAMPLES)
                  for i in range(FRAME_SAMPLES))
    return output


def custom_sample_bank(samples: list[Sample]) -> dict[str, dict[str, str]]:
    short_fx = samples[5]  # MOD sample 6, one second at period 480.
    short_rate = 3546895.0 / 480.0
    short_pcm = resample_u4(short_fx.data, short_rate, normalize=True)

    offset_tail = samples[2]  # Sample 3 with effect 95B, only its last 3994 bytes.
    offset = 0x5B * 256
    # The complete offset tail would cost about 4 KiB.  Retain its first
    # 167 ms plus the click-suppressing ramp; this is the portion that fits
    # alongside the complete score and the more important one-second sample 6.
    tail_source_bytes = round(1200 * short_rate / TARGET_RATE)
    tail_pcm = resample_u4(
        offset_tail.data[offset:offset + tail_source_bytes], short_rate,
    )
    return {
        "4": {
            "encoding": "base64-u4",
            "name": "MOD sample 6, period 480, normalized short effect",
            "data": base64.b64encode(bytes(short_pcm)).decode("ascii"),
        },
        "5": {
            "encoding": "base64-u4",
            "name": "First 167 ms of MOD sample 3 tail selected by effect 95B",
            "data": base64.b64encode(bytes(tail_pcm)).decode("ascii"),
        },
    }


def slide_delta(period: int, parameter: int, upward: bool, finetune: int) -> int:
    if not period or not parameter:
        return 0
    next_period = max(113, period - parameter) if upward else min(856, period + parameter)
    return phase_step(next_period, finetune) - phase_step(period, finetune)


def portamento_rate(period: int, parameter: int, target: int, finetune: int) -> int:
    if not period or not target or not parameter:
        return 1
    if period < target:
        moved = min(target, period + parameter)
    else:
        moved = max(target, period - parameter)
    return max(1, abs(phase_step(moved, finetune) - phase_step(period, finetune)))


def compile_score(samples: list[Sample], orders: list[int],
                  patterns: list[list[list[Event]]], seconds: float | None) -> dict:
    channels = [Channel() for _ in range(4)]
    speed = 6
    elapsed_frames = 0
    rows: list[dict] = []
    previous_volume_delta = {tone: 0 for tone in TONE_MAP.values()}
    previous_pitch_mode = {tone: ("slide", 0) for tone in TONE_MAP.values()}
    stats = {"volume_set": 0, "volume_slide": 0, "pitch_slide": 0,
             "tone_portamento": 0, "sample_offset": 0, "speed": 0,
             "pcm_short": 0, "pcm_tail": 0}

    for order_index, pattern_number in enumerate(orders):
        for row_index, events in enumerate(patterns[pattern_number]):
            # Fxx takes effect on tick zero, including the duration of this row.
            for event in events:
                if event.effect == 0xF and event.parameter:
                    if event.parameter >= 0x20:
                        raise ModError("this importer does not implement MOD tempo commands")
                    speed = event.parameter
                    stats["speed"] += 1
            if seconds is not None and elapsed_frames >= math.ceil(seconds * 50.0):
                break

            output: dict = {"frames": speed}
            volume_set: dict[str, int] = {}
            wanted_volume_delta = {tone: 0 for tone in TONE_MAP.values()}
            wanted_pitch: dict[str, tuple[str, object]] = {
                tone: ("slide", 0) for tone in TONE_MAP.values()
            }
            pcm_candidates: list[tuple[int, int]] = []

            for channel_index, event in enumerate(events):
                state = channels[channel_index]
                tone = TONE_MAP.get(channel_index)
                old_sample = state.sample
                if event.sample:
                    state.sample = event.sample
                    state.volume = samples[event.sample - 1].volume
                    if tone is not None and not event.period:
                        volume_set[tone] = engine_volume(state.volume)

                if event.effect == 0xC:
                    state.volume = min(64, event.parameter)
                    if tone is not None:
                        volume_set[tone] = engine_volume(state.volume)
                    stats["volume_set"] += 1

                current_sample = samples[state.sample - 1] if state.sample else None
                is_portamento = event.effect == 3 and event.period
                if event.period and current_sample is not None:
                    if is_portamento:
                        state.porta_target = event.period
                    else:
                        state.period = event.period

                    if event.sample in PCM_PERCUSSION:
                        pcm_candidates.append((10, PCM_PERCUSSION[event.sample]))
                    elif event.sample == 6:
                        pcm_candidates.append((30, 4))
                        stats["pcm_short"] += 1
                    elif event.sample == 3 and event.effect == 9 and event.parameter == 0x5B:
                        pcm_candidates.append((40, 5))
                        stats["pcm_tail"] += 1
                        stats["sample_offset"] += 1

                    if tone is not None:
                        if state.sample in NON_TONAL or (event.sample == 3 and
                                                        event.effect == 9):
                            output[tone] = {"note": "---"}
                        elif not is_portamento:
                            nibble = max(1, engine_volume(state.volume))
                            output[tone] = {
                                "phase_step": phase_step(state.period, current_sample.finetune),
                                "volume": editor_volume(nibble),
                                "envelope_speed": 8,
                                "envelope_mode": "hold",
                            }

                if event.effect == 0xA and tone is not None:
                    parameter = event.parameter or state.volume_slide_memory
                    if event.parameter:
                        state.volume_slide_memory = event.parameter
                    up, down = parameter >> 4, parameter & 15
                    amount = up if up else -down
                    if amount:
                        delta = max(1, round(abs(amount) * 15 / 64))
                        wanted_volume_delta[tone] = delta if amount > 0 else -delta
                    stats["volume_slide"] += 1

                if event.effect in (1, 2) and tone is not None and current_sample is not None:
                    parameter = event.parameter
                    delta = slide_delta(state.period, parameter, event.effect == 1,
                                        current_sample.finetune)
                    wanted_pitch[tone] = ("slide", delta)
                    stats["pitch_slide"] += 1
                elif event.effect == 3 and tone is not None and current_sample is not None:
                    parameter = event.parameter or state.porta_memory
                    if event.parameter:
                        state.porta_memory = event.parameter
                    if state.porta_target and state.period:
                        target = phase_step(state.porta_target, current_sample.finetune)
                        rate = portamento_rate(state.period, parameter, state.porta_target,
                                               current_sample.finetune)
                        wanted_pitch[tone] = ("porta", {"target": target, "rate": rate})
                        stats["tone_portamento"] += 1

                # Keep importer state aligned with the effect's five nonzero ticks.
                if event.effect == 0xA:
                    parameter = event.parameter or state.volume_slide_memory
                    up, down = parameter >> 4, parameter & 15
                    state.volume = max(0, min(64, state.volume + (up - down) * (speed - 1)))
                elif event.effect == 1 and state.period:
                    state.period = max(113, state.period - event.parameter * (speed - 1))
                elif event.effect == 2 and state.period:
                    state.period = min(856, state.period + event.parameter * (speed - 1))
                elif event.effect == 3 and state.period and state.porta_target:
                    parameter = event.parameter or state.porta_memory
                    distance = parameter * (speed - 1)
                    if state.period < state.porta_target:
                        state.period = min(state.porta_target, state.period + distance)
                    else:
                        state.period = max(state.porta_target, state.period - distance)

                # Instrument-only changes set volume even if the same sample number repeats.
                if tone is not None and event.sample and event.sample != old_sample and not event.period:
                    volume_set[tone] = engine_volume(state.volume)

            if pcm_candidates:
                _, sample_id = max(pcm_candidates)
                output["percussion"] = {
                    "sample": sample_id, "volume": 4,
                    "filter": 9, "offset": 1,
                }

            effects: dict[str, dict] = {}
            # A triggered tone packet already carries the tick-zero Cxx or
            # instrument default volume.  Emitting a separate four-mask FX
            # packet for the same value wastes several kilobytes over this
            # long tune.
            for tone in list(volume_set):
                tone_event = output.get(tone)
                if isinstance(tone_event, dict) and "phase_step" in tone_event:
                    del volume_set[tone]
            if volume_set:
                effects["volume_set"] = volume_set
            volume_changes = {
                tone: delta for tone, delta in wanted_volume_delta.items()
                if delta != previous_volume_delta[tone]
            }
            if volume_changes:
                effects["volume_slide"] = volume_changes
            previous_volume_delta = wanted_volume_delta

            pitch_slides: dict[str, int] = {}
            portas: dict[str, dict] = {}
            for tone, wanted in wanted_pitch.items():
                if wanted[0] == "porta":
                    # Reassert active portamento each MOD row; the runtime clears
                    # its target automatically when it arrives.
                    portas[tone] = wanted[1]  # type: ignore[assignment]
                elif wanted != previous_pitch_mode[tone]:
                    pitch_slides[tone] = int(wanted[1])
            if pitch_slides:
                effects["pitch_slide"] = pitch_slides
            if portas:
                effects["tone_portamento"] = portas
            previous_pitch_mode = wanted_pitch
            if effects:
                output["effects"] = effects

            rows.append(output)
            elapsed_frames += speed
        else:
            continue
        break

    if seconds is None and len(rows) == len(orders) * 64:
        compiled_patterns: list[list[dict]] = []
        compiled_order: list[int] = []
        identities: dict[str, int] = {}
        for order_index in range(len(orders)):
            chunk = rows[order_index * 64:(order_index + 1) * 64]
            identity = json.dumps(chunk, sort_keys=True, separators=(",", ":"))
            if identity not in identities:
                identities[identity] = len(compiled_patterns)
                compiled_patterns.append(chunk)
            compiled_order.append(identities[identity])
    else:
        compiled_patterns = [rows]
        compiled_order = [0]

    return {
        "schema": "jukupoly-song-v1",
        "title": "The Robots (TDK, JukuPoly adaptation)",
        "composer": "Ralf Hütter, Florian Schneider, Karl Bartos",
        "tracker_arranger": "Mark Knight / T.D.K.",
        "juku_arrangement": "MOD channels 1, 2, and 4 as tones; channel 3 and selected short samples as concurrent PCM",
        "source": {
            "name": "tdk-the_robots.mod / The Robots",
            "tracker_arrangement_credit": "Mark Knight / T.D.K.",
            "underlying_song": "The Robots by Kraftwerk",
            "songwriters": "Ralf Hütter, Florian Schneider, Karl Bartos",
            "url": "https://modarchive.org/index.php?request=view_by_moduleid&query=59396",
            "download_sha256": EXPECTED_SHA256,
            "download_md5": EXPECTED_MD5,
            "license": "No new license asserted for the composition, tracker arrangement, or samples.",
        },
        "sample_rate_hz": TARGET_RATE,
        "frame_samples": FRAME_SAMPLES,
        "mod_effects": True,
        "defaults": {
            "tone1": {"volume": 12, "envelope_speed": 8, "envelope_mode": "hold"},
            "tone2": {"volume": 12, "envelope_speed": 8, "envelope_mode": "hold"},
            "tone3": {"volume": 12, "envelope_speed": 8, "envelope_mode": "hold"},
        },
        "sample_bank": custom_sample_bank(samples),
        "notes": (
            "Hash-locked ProTracker import. Effects 1xx/2xx/3xx, 9xx, Axy, Cxx, "
            "and Fxx are compiled; the actual one-second MOD sample 6 and the "
            "first 167 ms of the sample-3 tail selected by 95B are retained as 4-bit PCM. "
            "Long 4-second voice/effect samples are omitted to remain inside the CP/M TPA."
        ),
        "import_stats": stats,
        "duration_frames": elapsed_frames,
        "patterns": compiled_patterns,
        "order": compiled_order,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("module", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--seconds", type=float,
                        help="stop after approximately this many seconds")
    args = parser.parse_args()
    data = args.module.read_bytes()
    digest = hashlib.sha256(data).hexdigest()
    if digest != EXPECTED_SHA256:
        raise SystemExit(
            f"unexpected MOD SHA-256 {digest}; expected {EXPECTED_SHA256}"
        )
    samples, orders, patterns = parse_module(data)
    score = compile_score(samples, orders, patterns, args.seconds)
    args.output.write_text(json.dumps(score, indent=2) + "\n")
    print(
        f"JUKUPOLY-MOD: wrote {args.output} patterns={len(score['patterns'])} "
        f"rows={sum(len(pattern) for pattern in score['patterns'])} "
        f"frames={score['duration_frames']} duration={score['duration_frames'] / 50:.2f}s"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
