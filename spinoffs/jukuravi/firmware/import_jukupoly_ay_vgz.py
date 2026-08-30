#!/usr/bin/env python3
"""Reduce a three-channel AY-3-8910/YM2149 VGM/VGZ to JukuPoly.

Tone periods become raw JukuPoly phase steps, retaining fine detuning that a
nearest-note conversion would erase.  AY noise gates are reduced to the common
JukuPoly percussion bank.  This is a musical register reduction, not a PSG
waveform emulator.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path

from import_jukupoly_vgz import (
    FRAME_SAMPLES,
    FRAMES_PER_SECOND,
    TARGET_RATE,
    VGM_RATE,
    VgmError,
    decode_source,
    parse_gd3,
    skip_command,
    u32,
)


@dataclass(frozen=True)
class AyWrite:
    sample: int
    register: int
    value: int


@dataclass
class AyInfo:
    version: int
    clock: int
    effective_clock: int
    chip_type: int
    chip_flags: int
    total_samples: int
    loop_samples: int
    loop_start_sample: int | None
    gd3: dict[str, str]


CHIP_NAMES = {
    0x00: "AY-3-8910",
    0x01: "AY-3-8912",
    0x02: "AY-3-8913",
    0x10: "YM2149",
    0x11: "YM3439",
    0x12: "YMZ284",
    0x13: "YMZ294",
}


def parse_ay_vgm(data: bytes) -> tuple[AyInfo, list[AyWrite]]:
    if len(data) < 0x80 or data[:4] != b"Vgm ":
        raise VgmError("input is not a VGM stream")
    version = u32(data, 8)
    if version < 0x151:
        raise VgmError("AY8910 clock metadata requires VGM 1.51 or newer")
    relative = u32(data, 0x34)
    data_offset = 0x34 + relative if relative else 0x40
    clock_field = u32(data, 0x74)
    if clock_field & 0x4000_0000:
        raise VgmError("dual AY/YM chips are not supported")
    clock = clock_field & 0x3FFF_FFFF
    if not clock:
        raise VgmError("VGM does not declare an AY8910/YM2149 clock")
    chip_type = data[0x78]
    chip_flags = data[0x79]
    effective_clock = clock
    if chip_type in (0x10, 0x11) and chip_flags & 1:
        # YM2149 /SEL low divides its master clock by two.
        effective_clock //= 2

    total_header = u32(data, 0x18)
    loop_relative = u32(data, 0x1C)
    loop_offset = 0x1C + loop_relative if loop_relative else None
    loop_samples = u32(data, 0x20)
    positions: dict[int, int] = {}
    writes: list[AyWrite] = []
    at = data_offset
    samples = 0
    ended = False
    while at < len(data):
        position = at
        positions[position] = samples
        command = data[at]
        at += 1
        if command == 0xA0:
            if at + 2 > len(data):
                raise VgmError("truncated AY8910 register write")
            register, value = data[at], data[at + 1]
            if register >= 16:
                raise VgmError(f"invalid AY8910 register {register:02X}h")
            writes.append(AyWrite(samples, register, value))
            at += 2
        elif command == 0x61:
            if at + 2 > len(data):
                raise VgmError("truncated VGM wait")
            samples += int.from_bytes(data[at:at + 2], "little")
            at += 2
        elif command == 0x62:
            samples += 735
        elif command == 0x63:
            samples += 882
        elif 0x70 <= command <= 0x7F:
            samples += (command & 15) + 1
        elif 0x80 <= command <= 0x8F:
            samples += command & 15
        elif command == 0x66:
            ended = True
            break
        elif command == 0x67:
            if at + 6 > len(data) or data[at] != 0x66:
                raise VgmError("invalid VGM data block")
            length = int.from_bytes(data[at + 2:at + 6], "little")
            at += 6 + length
        else:
            at = skip_command(data, at, command)
        if at > len(data):
            raise VgmError(f"truncated VGM command {command:02X}h")
    if not ended:
        raise VgmError("VGM stream has no end command")
    if total_header and samples != total_header:
        raise VgmError(
            f"VGM duration mismatch: header {total_header}, commands {samples}"
        )
    if loop_offset is not None and loop_offset not in positions:
        raise VgmError("VGM loop offset does not point to a command")
    loop_start = positions.get(loop_offset) if loop_offset is not None else None
    if loop_start is not None and loop_samples and samples - loop_start != loop_samples:
        raise VgmError(
            f"VGM loop duration mismatch: header {loop_samples}, "
            f"commands {samples - loop_start}"
        )
    return AyInfo(
        version=version,
        clock=clock,
        effective_clock=effective_clock,
        chip_type=chip_type,
        chip_flags=chip_flags,
        total_samples=samples,
        loop_samples=loop_samples,
        loop_start_sample=loop_start,
        gd3=parse_gd3(data),
    ), writes


def folded_frequency(frequency: float) -> float:
    while frequency < 82.0:
        frequency *= 2.0
    while frequency > 1000.0:
        frequency /= 2.0
    return frequency


def phase_step(frequency: float) -> int:
    step = round(folded_frequency(frequency) * 65536.0 / TARGET_RATE)
    if not 0 < step < 0x8000:
        raise VgmError(f"AY tone frequency produces invalid phase step {step}")
    return step


def tone_state(registers: list[int], channel: int, clock: int
               ) -> tuple[int, int, bool] | None:
    period = registers[channel * 2] | (registers[channel * 2 + 1] & 15) << 8
    level = registers[8 + channel]
    if not period or registers[7] & (1 << channel) or not level & 31:
        return None
    frequency = clock / (16.0 * period)
    volume = 16 if level & 0x10 else min(16, (level & 15) + 1)
    return phase_step(frequency), volume, bool(level & 0x10)


def compile_score(info: AyInfo, writes: list[AyWrite], source: Path,
                  compressed_sha: str, vgm_sha: str) -> dict:
    total_frames = (
        info.total_samples * FRAMES_PER_SECOND + VGM_RATE // 2
    ) // VGM_RATE
    by_frame: dict[int, list[AyWrite]] = defaultdict(list)
    for write in writes:
        frame = (write.sample * FRAMES_PER_SECOND + VGM_RATE // 2) // VGM_RATE
        if frame < total_frames:
            by_frame[frame].append(write)

    registers = [0] * 16
    previous: list[tuple[int, int, bool] | None] = [None, None, None]
    previous_noise = False
    last_noise_frame = -100
    rows: list[dict] = []
    active_peak = 0
    three_tone_frames = 0
    envelope_retriggers = 0
    percussion_hits: Counter[int] = Counter()
    frequencies: list[float] = []

    for frame in range(total_frames):
        envelope_restart = False
        for write in by_frame.get(frame, ()):
            registers[write.register] = write.value
            if write.register == 13:
                envelope_restart = True

        states = [tone_state(registers, channel, info.effective_clock)
                  for channel in range(3)]
        active = sum(state is not None for state in states)
        active_peak = max(active_peak, active)
        if active == 3:
            three_tone_frames += 1
        row: dict = {}
        for channel, state in enumerate(states):
            field = f"tone{channel + 1}"
            old = previous[channel]
            retrigger = bool(state and state[2] and envelope_restart)
            if state is None:
                if old is not None:
                    row[field] = {"note": "---"}
            elif state != old or retrigger:
                step, volume, uses_envelope = state
                row[field] = {
                    "phase_step": step,
                    "volume": volume,
                    "envelope_speed": 8,
                    "envelope_mode": "decay" if uses_envelope else "hold",
                }
                if retrigger:
                    envelope_retriggers += 1
                period = (registers[channel * 2] |
                          (registers[channel * 2 + 1] & 15) << 8)
                frequencies.append(info.effective_clock / (16.0 * period))
            previous[channel] = state

        noise_channels = [
            channel for channel in range(3)
            if not registers[7] & (1 << (channel + 3)) and registers[8 + channel] & 31
        ]
        noise_active = bool(noise_channels)
        noise_changed = any(write.register == 6 for write in by_frame.get(frame, ()))
        if noise_active and (not previous_noise or noise_changed) and frame - last_noise_frame > 1:
            period = registers[6] & 31
            sample = 3 if period <= 5 else 2
            level = max(registers[8 + channel] & 15 for channel in noise_channels)
            row["percussion"] = {
                "sample": sample,
                "volume": max(1, min(4, round((level or 15) / 4))),
                "filter": max(1, min(9, 9 - period // 4)),
                "offset": 1,
            }
            percussion_hits[sample] += 1
            last_noise_frame = frame
        previous_noise = noise_active

        if not row and rows and rows[-1]["frames"] < 255:
            rows[-1]["frames"] += 1
        else:
            rows.append({"frames": 1, **row})

    gd3 = info.gd3
    title = gd3.get("track_en") or gd3.get("track_jp") or source.stem
    composer = gd3.get("author_en") or gd3.get("author_jp") or "Unknown"
    chip_name = CHIP_NAMES.get(info.chip_type, f"AY-family type {info.chip_type:02X}h")
    return {
        "schema": "jukupoly-song-v1",
        "title": f"{title} ({chip_name}/VGZ JukuPoly reduction)",
        "composer": composer,
        "arrangement": (
            "Automatic AY-family reduction: three PSG tone periods to three "
            "raw Juku phase steps; PSG noise gates to synthesized percussion"
        ),
        "source": {
            "name": source.name,
            "format": "gzip-compressed VGM" if source.suffix.lower() == ".vgz" else "VGM",
            "compressed_sha256": compressed_sha,
            "vgm_sha256": vgm_sha,
            "vgm_version": f"{info.version >> 8}.{info.version & 0xFF:02X}",
            "chip": chip_name,
            "chip_clock_hz": info.clock,
            "effective_clock_hz": info.effective_clock,
            "chip_flags": info.chip_flags,
            "gd3": gd3,
            "license": "No new license asserted for the composition or source recording.",
        },
        "sample_rate_hz": TARGET_RATE,
        "frame_samples": FRAME_SAMPLES,
        "defaults": {
            "tone1": {"volume": 14, "envelope_speed": 8, "envelope_mode": "hold"},
            "tone2": {"volume": 14, "envelope_speed": 8, "envelope_mode": "hold"},
            "tone3": {"volume": 16, "envelope_speed": 8, "envelope_mode": "decay"},
        },
        "conversion": {
            "policy": "finite VGM stream only; never follow the loop back",
            "total_vgm_samples": info.total_samples,
            "duration_seconds": info.total_samples / VGM_RATE,
            "loop_start_sample": info.loop_start_sample,
            "loop_samples": info.loop_samples,
            "duration_frames": total_frames,
            "source_tone_channels_peak": active_peak,
            "three_tone_frames": three_tone_frames,
            "envelope_retriggers": envelope_retriggers,
            "percussion_hits": {str(key): value for key, value in percussion_hits.items()},
            "frequency_hz_min": min(frequencies) if frequencies else None,
            "frequency_hz_max": max(frequencies) if frequencies else None,
        },
        "notes": (
            "This is a register-level musical reduction, not AY/YM waveform "
            "emulation. Raw tone periods preserve source tuning and detuning."
        ),
        "rows": rows,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path,
                        help="AY/YM .vgm or gzip-compressed .vgz")
    parser.add_argument("output", type=Path,
                        help="output jukupoly-song-v1 JSON")
    args = parser.parse_args()
    data, compressed_sha = decode_source(args.source)
    info, writes = parse_ay_vgm(data)
    score = compile_score(
        info, writes, args.source, compressed_sha,
        hashlib.sha256(data).hexdigest(),
    )
    args.output.write_text(json.dumps(score, indent=2) + "\n")
    conversion = score["conversion"]
    print(
        f"JUKUPOLY-AY: wrote {args.output} rows={len(score['rows'])} "
        f"frames={conversion['duration_frames']} "
        f"duration={conversion['duration_seconds']:.3f}s "
        f"loop={conversion['loop_start_sample']}/+{conversion['loop_samples']} "
        f"tones={conversion['source_tone_channels_peak']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
