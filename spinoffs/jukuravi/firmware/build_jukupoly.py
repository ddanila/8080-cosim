#!/usr/bin/env python3
"""Compile the JukuPoly score/sample bank and build its strict-8080 COM file."""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import math
import re
import subprocess
import sys
import tempfile
from pathlib import Path


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT / "tools"))
from build_zmac import executable  # noqa: E402


DEFAULT_SONG = HERE / "jukupoly-canyon-demo.json"
DEFAULT_GENERATED = HERE / "jukupoly-song-generated.inc"
SOURCE = HERE / "jukupoly-player-0100.asm"
DEFAULT_OUTPUT = HERE / "jukupoly.com"

TONE_FLAGS = {"tone1": 0x01, "tone2": 0x02, "tone3": 0x04}
SLIDE_FLAG = 0x08
PERCUSSION_FLAG = 0x10
END_FLAG = 0x80
MODE_CODES = {"attack": 0, "decay": 1, "hold": 2}
MOD_SET_MODE = 3
NOTE_OFF = "---"
NOTE_RE = re.compile(r"^([A-G])([#b]?)(-?\d+)$")
NOTE_BASE = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}


class SongError(ValueError):
    pass


def check_range(name: str, value: int, low: int, high: int) -> int:
    if not isinstance(value, int) or not low <= value <= high:
        raise SongError(f"{name} must be {low}..{high}, got {value!r}")
    return value


def note_frequency(name: str) -> float:
    match = NOTE_RE.fullmatch(name)
    if not match:
        raise SongError(f"invalid note name: {name!r}")
    letter, accidental, octave_text = match.groups()
    semitone = NOTE_BASE[letter]
    if accidental == "#":
        semitone += 1
    elif accidental == "b":
        semitone -= 1
    midi = (int(octave_text) + 1) * 12 + semitone
    if not 0 <= midi <= 127:
        raise SongError(f"note outside MIDI range: {name}")
    return 440.0 * 2.0 ** ((midi - 69) / 12.0)


def phase_step(note: str, detune: int | None, sample_rate: int) -> int:
    value = round(note_frequency(note) * 65536.0 / sample_rate)
    if detune is not None:
        value += check_range("detune", detune, 1, 9) - 5
    if not 0 < value < 0x8000:
        raise SongError(f"phase step for {note} is outside 1..32767: {value}")
    return value


def engine_volume(user_volume: int) -> int:
    """Map editor-facing 1..16 onto the nonzero QChan-style nibble 1..15."""
    check_range("volume", user_volume, 1, 16)
    return max(1, min(15, round(user_volume * 15 / 16)))


def decode_sample_bank(song: dict) -> dict[int, list[int]]:
    bank = song.get("sample_bank", {})
    if not isinstance(bank, dict):
        raise SongError("sample_bank must be an object")
    result: dict[int, list[int]] = {}
    for id_text, record in bank.items():
        try:
            sample = int(id_text)
        except ValueError as exc:
            raise SongError(f"invalid sample-bank ID {id_text!r}") from exc
        check_range("sample-bank ID", sample, 4, 99)
        if not isinstance(record, dict) or record.get("encoding") != "base64-u4":
            raise SongError(f"sample {sample} must use base64-u4 encoding")
        try:
            pcm = list(base64.b64decode(record["data"], validate=True))
        except (KeyError, ValueError) as exc:
            raise SongError(f"invalid base64 data for sample {sample}") from exc
        if not pcm or any(value > 15 for value in pcm):
            raise SongError(f"sample {sample} must contain nonempty 0..15 PCM")
        result[sample] = pcm
    return result


def base_drum(sample: int, frame_samples: int, sample_rate: int,
              sample_bank: dict[int, list[int]]) -> list[int]:
    if sample in sample_bank:
        return sample_bank[sample]
    if sample == 1:
        # Four-frame falling kick: sparse pitch impulses, 155 -> 58 Hz.
        length = frame_samples * 4
        phase = 0.0
        result: list[int] = []
        for index in range(length):
            position = index / length
            frequency = 155.0 * (1.0 - position) + 58.0 * position
            phase += frequency / sample_rate
            impulse = phase >= 1.0
            if impulse:
                phase -= 1.0
            result.append(round(15 * (1.0 - position)) if impulse else 0)
        return result
    if sample == 2:
        # Three-frame deterministic LFSR snare with a fast linear decay.
        length = frame_samples * 3
        state = 0xACE1
        result = []
        for index in range(length):
            state = (state >> 1) ^ (0xB400 if state & 1 else 0)
            level = round(15 * (1.0 - index / length))
            result.append(level if state & 0x0003 == 0 else 0)
        return result
    if sample == 3:
        # One-frame bright hat, denser than the snare and sharply decaying.
        length = frame_samples
        state = 0x1D0F
        result = []
        for index in range(length):
            state = (state >> 1) ^ (0xB400 if state & 1 else 0)
            envelope = (1.0 - index / length) ** 2
            result.append(round(15 * envelope) if state & 1 else 0)
        return result
    raise SongError(f"sample {sample} is not present in the demo bank (1..3)")


def render_drum(sample: int, volume: int, filter_value: int, offset: int,
                frame_samples: int, sample_rate: int,
                sample_bank: dict[int, list[int]]) -> tuple[list[int], int]:
    check_range("sample", sample, 1, 99)
    check_range("percussion volume", volume, 1, 4)
    check_range("filter", filter_value, 1, 9)
    check_range("sample offset", offset, 1, 9)
    source = base_drum(sample, frame_samples, sample_rate, sample_bank)
    skip = (offset - 1) * len(source) // 10
    source = source[skip:]

    # Moving-average windows 9..1 implement muffled..normal at compile time.
    window = 10 - filter_value
    filtered: list[int] = []
    history: list[int] = []
    total = 0
    for value in source:
        history.append(value)
        total += value
        if len(history) > window:
            total -= history.pop(0)
        filtered.append(round(total / len(history)))
    scaled = [min(15, round(value * volume / 4)) for value in filtered]
    frames = max(1, math.ceil(len(scaled) / frame_samples))
    scaled.extend([0] * (frames * frame_samples - len(scaled)))
    return scaled, frames


def byte_lines(values: list[int], width: int = 16) -> list[str]:
    return [
        "        db      " + ",".join(f"{value:02x}h" for value in values[index:index + width])
        for index in range(0, len(values), width)
    ]


def asm_hex(value: int, width: int) -> str:
    """Format a zmac hexadecimal literal, guarding an alphabetic first digit."""
    digits = f"{value:0{width}x}"
    if digits[0].isalpha():
        digits = "0" + digits
    return digits + "h"


def compile_song(song: dict) -> tuple[str, dict]:
    if song.get("schema") != "jukupoly-song-v1":
        raise SongError("song schema must be jukupoly-song-v1")
    sample_rate = check_range("sample_rate_hz", song["sample_rate_hz"], 4000, 12000)
    frame_samples = check_range("frame_samples", song["frame_samples"], 64, 255)
    rows = song.get("rows")
    patterns = song.get("patterns")
    pattern_order = song.get("order")
    pattern_mode = patterns is not None or pattern_order is not None
    if pattern_mode:
        if not isinstance(patterns, list) or not patterns or not all(
                isinstance(pattern, list) and pattern for pattern in patterns):
            raise SongError("song patterns must be a nonempty list of row lists")
        if not isinstance(pattern_order, list) or not pattern_order:
            raise SongError("pattern song order must be a nonempty list")
        for index in pattern_order:
            check_range("pattern order index", index, 0, len(patterns) - 1)
        logical_row_count = sum(len(pattern) for pattern in patterns)
        rows = []
        for pattern_index, pattern in enumerate(patterns):
            rows.append({"__pattern_label": pattern_index})
            rows.extend(pattern)
            rows.append({"__pattern_end": True})
    else:
        if not isinstance(rows, list) or not rows:
            raise SongError("song rows must be a nonempty list")
        logical_row_count = len(rows)

    sample_bank = decode_sample_bank(song)
    mod_effects = bool(song.get("mod_effects", False))
    defaults = song.get("defaults", {})
    channel_settings: dict[str, dict] = {}
    for channel in TONE_FLAGS:
        record = dict(defaults.get(channel, {}))
        record.setdefault("volume", 12)
        record.setdefault("envelope_speed", 3)
        record.setdefault("envelope_mode", "hold")
        channel_settings[channel] = record

    descriptors: dict[tuple[int, int, int, int], int] = {}
    rendered: list[tuple[tuple[int, int, int, int], list[int], int]] = []
    output: list[str] = [
        "; Generated by build_jukupoly.py; do not edit by hand.",
        f"JUKUPOLY_FRAME_SAMPLES equ     {frame_samples}",
        f"JUKUPOLY_TARGET_HZ    equ     {sample_rate}",
        f"JUKUPOLY_ROW_COUNT    equ     {logical_row_count}",
        "",
    ]
    if pattern_mode:
        output.extend([
            "jukupoly_song_order:",
            *(f"        dw      jukupoly_pattern_{index}" for index in pattern_order),
            "        dw      0000h",
            "",
        ])
    else:
        output.append("jukupoly_song_rows:")

    for row_index, row in enumerate(rows):
        if not isinstance(row, dict):
            raise SongError(f"row {row_index} must be an object")
        if "__pattern_label" in row:
            pattern_index = row["__pattern_label"]
            if pattern_index == 0:
                output.append("jukupoly_song_rows:")
            output.append(f"jukupoly_pattern_{pattern_index}:")
            continue
        if "__pattern_end" in row:
            output.append("        db      00h,40h        ; next pattern")
            continue
        frames = check_range(f"row {row_index} frames", row.get("frames", 1), 1, 255)
        flags = 0
        payload: list[str] = []
        for channel, flag in TONE_FLAGS.items():
            event = row.get(channel)
            if event is None:
                continue
            if not isinstance(event, dict):
                raise SongError(f"row {row_index} {channel} must be an object")
            settings = channel_settings[channel]
            for field in ("volume", "envelope_speed", "envelope_mode"):
                if field in event:
                    settings[field] = event[field]
            note = event.get("note")
            raw_step = event.get("phase_step")
            if note is None and raw_step is None:
                continue
            flags |= flag
            if note == NOTE_OFF:
                payload.append("        dw      0000h")
                continue
            if note is not None and raw_step is not None:
                raise SongError(f"row {row_index} {channel} has note and phase_step")
            if raw_step is not None:
                step = check_range(
                    f"row {row_index} {channel} phase_step", raw_step, 1, 0x7fff,
                )
                note_comment = f"step {step}"
            else:
                detune = event.get("detune")
                step = phase_step(note, detune, sample_rate)
                note_comment = note
            if bool(event.get("legato", False)):
                step |= 0x8000
            speed = check_range(
                f"row {row_index} {channel} envelope speed",
                settings["envelope_speed"], 1, 8,
            )
            mode_name = settings["envelope_mode"]
            if mode_name == "set":
                if not mod_effects:
                    raise SongError("set envelope mode requires mod_effects")
                mode_code = MOD_SET_MODE
            elif mode_name in MODE_CODES:
                mode_code = MODE_CODES[mode_name]
            else:
                raise SongError(f"invalid envelope mode {mode_name!r}")
            mask = (1 << speed) - 1
            config = mode_code << 4 | engine_volume(settings["volume"])
            payload.extend([
                f"        dw      {asm_hex(step, 4)}    ; {channel} {note_comment}",
                f"        db      {asm_hex(mask, 2)},{asm_hex(config, 2)}",
            ])

        tone1 = row.get("tone1")
        if isinstance(tone1, dict) and ("slide_up" in tone1 or "slide_down" in tone1):
            up = check_range("slide_up", tone1.get("slide_up", 0), 0, 9)
            down = check_range("slide_down", tone1.get("slide_down", 0), 0, 9)
            if up and down:
                raise SongError(f"row {row_index} cannot slide both up and down")
            flags |= SLIDE_FLAG
            payload.append(f"        dw      {asm_hex((up - down) & 0xffff, 4)}")

        percussion = row.get("percussion")
        if percussion is not None:
            if not isinstance(percussion, dict):
                raise SongError(f"row {row_index} percussion must be an object")
            key = (
                check_range("sample", percussion["sample"], 1, 99),
                check_range("percussion volume", percussion["volume"], 1, 4),
                check_range("filter", percussion["filter"], 1, 9),
                check_range("sample offset", percussion["offset"], 1, 9),
            )
            if key not in descriptors:
                descriptor = len(descriptors)
                descriptors[key] = descriptor
                pcm, drum_frames = render_drum(
                    *key, frame_samples, sample_rate, sample_bank,
                )
                rendered.append((key, pcm, drum_frames))
            flags |= PERCUSSION_FLAG
            payload.append(f"        dw      jukupoly_drum_desc_{descriptors[key]}")

        effects = row.get("effects")
        if effects is not None:
            if not mod_effects:
                raise SongError(f"row {row_index} effects require mod_effects")
            if not isinstance(effects, dict):
                raise SongError(f"row {row_index} effects must be an object")
            flags |= 0x20
            effect_payload: list[str] = []
            masks: list[int] = []
            fields = (
                ("volume_set", -15, 15, 1),
                ("volume_slide", -15, 15, 1),
                ("pitch_slide", -0x7fff, 0x7fff, 2),
                ("tone_portamento", 0, 0, 4),
            )
            records: list[tuple[str, dict, int]] = []
            for field, low, high, width in fields:
                record = effects.get(field, {})
                if not isinstance(record, dict):
                    raise SongError(f"row {row_index} effects.{field} must be an object")
                mask = 0
                for channel_index, channel in enumerate(TONE_FLAGS):
                    if channel not in record:
                        continue
                    mask |= 1 << channel_index
                    value = record[channel]
                    if field == "volume_set":
                        check_range(f"row {row_index} {field}", value, 0, 15)
                    elif field != "tone_portamento":
                        check_range(f"row {row_index} {field}", value, low, high)
                    else:
                        if not isinstance(value, dict):
                            raise SongError(f"row {row_index} {field}.{channel} must be an object")
                        check_range("portamento target", value.get("target"), 1, 0x7fff)
                        check_range("portamento rate", value.get("rate"), 1, 0x7fff)
                masks.append(mask)
                records.append((field, record, width))
            effect_payload.append(
                "        db      " + ",".join(f"{mask:02x}h" for mask in masks)
            )
            for field, record, width in records:
                for channel in TONE_FLAGS:
                    if channel not in record:
                        continue
                    value = record[channel]
                    if field == "tone_portamento":
                        effect_payload.extend([
                            f"        dw      {value['target']:04x}h",
                            f"        dw      {value['rate']:04x}h",
                        ])
                    elif width == 1:
                        effect_payload.append(
                            f"        db      {asm_hex(value & 0xff, 2)}"
                        )
                    else:
                        effect_payload.append(
                            f"        dw      {asm_hex(value & 0xffff, 4)}"
                        )
            payload.extend(effect_payload)

        output.append(f"        db      {frames:02x}h,{flags:02x}h        ; row {row_index}")
        output.extend(payload)

    output.extend([
        f"        db      00h,{END_FLAG:02x}h        ; end",
        "",
        "jukupoly_silence:",
        *byte_lines([0] * frame_samples),
        "",
    ])
    for descriptor, (key, pcm, frames) in enumerate(rendered):
        sample, volume, filter_value, offset = key
        output.extend([
            f"jukupoly_drum_desc_{descriptor}:",
            f"        dw      jukupoly_drum_pcm_{descriptor}",
            f"        db      {frames:02x}h",
            f"jukupoly_drum_pcm_{descriptor}:",
            f"        ; sample={sample} volume={volume} filter={filter_value} offset={offset}",
            *byte_lines(pcm),
            "",
        ])

    text = "\n".join(output).rstrip() + "\n"
    metadata = {
        "rows": logical_row_count,
        "patterns": len(patterns) if pattern_mode else 0,
        "order_length": len(pattern_order) if pattern_mode else 0,
        "descriptors": len(descriptors),
        "pcm_bytes": sum(len(pcm) for _, pcm, _ in rendered),
        "frame_samples": frame_samples,
        "target_sample_hz": sample_rate,
        "mod_effects": mod_effects,
        "score_sha256": hashlib.sha256(text.encode()).hexdigest(),
    }
    return text, metadata


def assemble(generated: str, mod_effects: bool = False) -> bytes:
    with tempfile.TemporaryDirectory(prefix="jukupoly.") as name:
        directory = Path(name)
        image = directory / "jukupoly.cim"
        source = directory / SOURCE.name
        include = directory / DEFAULT_GENERATED.name
        source.write_bytes(SOURCE.read_bytes())
        include.write_text(generated)
        command = [
            str(executable()), "--nmnv", "--zmac", "-8",
            f"-I{directory}", "-o", str(image), str(source),
        ]
        if mod_effects:
            command.insert(4, "-P1=1")
        subprocess.run(
            command,
            check=True,
        )
        return image.read_bytes()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true",
                        help="fail if generated score or COM image is stale")
    parser.add_argument("--song", type=Path, default=DEFAULT_SONG,
                        help="input jukupoly-song-v1 JSON")
    parser.add_argument("--generated", type=Path, default=DEFAULT_GENERATED,
                        help="generated assembler include")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT,
                        help="output CP/M COM image")
    args = parser.parse_args()
    song = json.loads(args.song.read_text())
    generated, metadata = compile_song(song)

    if args.check:
        if not args.generated.exists() or args.generated.read_text() != generated:
            raise SystemExit(f"{args.generated} is missing or stale")
    else:
        args.generated.write_text(generated)

    image = assemble(generated, metadata["mod_effects"])
    if args.check:
        if not args.output.exists() or args.output.read_bytes() != image:
            raise SystemExit(f"{args.output} is missing or stale")
        action = "checked"
    else:
        args.output.write_bytes(image)
        action = "wrote"
    print(
        f"JUKUPOLY: {action} {args.output.name} bytes={len(image)} "
        f"rows={metadata['rows']} drums={metadata['descriptors']} "
        f"pcm={metadata['pcm_bytes']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
