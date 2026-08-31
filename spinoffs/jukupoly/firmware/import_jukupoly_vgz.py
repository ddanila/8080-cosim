#!/usr/bin/env python3
"""Reduce a two-operator OPL VGM/VGZ command stream to a JukuPoly score.

The converter follows one finite VGM command stream (an intro plus one pass of
its loop, when present), reconstructs the 9-channel YM3812 or 18-channel
YMF262 register state, groups key-ons by instrument register signature, and
keeps at most three distinct pitched notes.  Fixed-pitch/rare instruments
become synthesized JukuPoly percussion.  It is intentionally a reduction, not
an OPL emulator.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import itertools
import json
import math
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path

import opl_trace


VGM_RATE = 44_100
# The normal JukuPoly frame path averages about 7.12 kHz at the calibrated
# 1.70 MHz effective CPU rate.  A 143-sample frame keeps a 50 Hz VGM reduction
# close to source tempo without enabling the heavier MOD-effects ABI.
TARGET_RATE = 7_120
FRAME_SAMPLES = 143
FRAMES_PER_SECOND = 50
OPERATOR_OFFSETS = (0, 1, 2, 8, 9, 10, 16, 17, 18)


class VgmError(ValueError):
    pass


@dataclass(frozen=True)
class RegisterWrite:
    sample: int
    bank: int
    register: int
    value: int


@dataclass
class KeyEvent:
    start: int
    end: int
    bank: int
    channel: int
    signature: tuple[int, ...]
    note: int


@dataclass
class Candidate:
    note: int
    volume: int


@dataclass
class VgmInfo:
    version: int
    clock: int
    frequency_divider: int
    chip: str
    banks: int
    total_samples: int
    loop_samples: int
    loop_start_sample: int | None
    loop_offset: int | None
    gd3: dict[str, str]


def u32(data: bytes, offset: int) -> int:
    if offset + 4 > len(data):
        raise VgmError("truncated VGM header")
    return int.from_bytes(data[offset:offset + 4], "little")


def decode_source(path: Path) -> tuple[bytes, str]:
    payload = path.read_bytes()
    compressed_sha = hashlib.sha256(payload).hexdigest()
    if payload.startswith(b"\x1f\x8b"):
        try:
            payload = gzip.decompress(payload)
        except (EOFError, OSError) as exc:
            raise VgmError(f"invalid gzip/VGZ stream: {exc}") from exc
    return payload, compressed_sha


def parse_gd3(data: bytes) -> dict[str, str]:
    relative = u32(data, 0x14)
    if not relative:
        return {}
    offset = 0x14 + relative
    if offset + 12 > len(data) or data[offset:offset + 4] != b"Gd3 ":
        raise VgmError("invalid GD3 offset or signature")
    length = u32(data, offset + 8)
    if offset + 12 + length > len(data) or length & 1:
        raise VgmError("truncated GD3 text")
    fields = data[offset + 12:offset + 12 + length].decode("utf-16le").split("\0")
    names = (
        "track_en", "track_jp", "game_en", "game_jp", "system_en",
        "system_jp", "author_en", "author_jp", "date", "creator", "notes",
    )
    return {name: value for name, value in zip(names, fields) if value}


def skip_command(data: bytes, at: int, command: int) -> int:
    if command in (0x4F, 0x50):
        return at + 1
    if 0x51 <= command <= 0x5F or 0xA0 <= command <= 0xBF:
        return at + 2
    if 0xC0 <= command <= 0xDF:
        return at + 3
    if 0xE0 <= command <= 0xFF:
        return at + 4
    if command == 0x68:
        return at + 11
    if command in (0x90, 0x91):
        return at + 4
    if command == 0x92:
        return at + 5
    if command == 0x93:
        return at + 10
    if command == 0x94:
        return at + 1
    if command == 0x95:
        return at + 4
    raise VgmError(f"unsupported VGM command {command:02X}h at {at - 1:08X}h")


def parse_vgm(data: bytes) -> tuple[VgmInfo, list[RegisterWrite]]:
    if len(data) < 0x80 or data[:4] != b"Vgm ":
        raise VgmError("input is not a VGM stream")
    version = u32(data, 8)
    if version < 0x150:
        data_offset = 0x40
    else:
        relative = u32(data, 0x34)
        data_offset = 0x34 + relative if relative else 0x40
    ymf262_clock = u32(data, 0x5C) & 0x3FFF_FFFF
    ym3812_clock = u32(data, 0x50) & 0x3FFF_FFFF
    if ymf262_clock:
        clock = ymf262_clock
        frequency_divider = 288
        chip = "YMF262 (OPL3)"
        banks = 2
        write_commands = {0x5E: 0, 0x5F: 1}
    elif ym3812_clock:
        clock = ym3812_clock
        frequency_divider = 72
        chip = "YM3812 (OPL2)"
        banks = 1
        write_commands = {0x5A: 0}
    else:
        raise VgmError("VGM does not declare a YM3812 or YMF262 clock")
    total_header = u32(data, 0x18)
    loop_relative = u32(data, 0x1C)
    loop_offset = 0x1C + loop_relative if loop_relative else None
    loop_samples = u32(data, 0x20)

    writes: list[RegisterWrite] = []
    command_positions: dict[int, int] = {}
    at = data_offset
    samples = 0
    ended = False
    while at < len(data):
        position = at
        command_positions[position] = samples
        command = data[at]
        at += 1
        if command in write_commands:
            if at + 2 > len(data):
                raise VgmError("truncated OPL register write")
            writes.append(RegisterWrite(samples, write_commands[command],
                                        data[at], data[at + 1]))
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
    if loop_offset is not None and loop_offset not in command_positions:
        raise VgmError("VGM loop offset does not point to a command")
    loop_start = command_positions.get(loop_offset) if loop_offset is not None else None
    if loop_start is not None and loop_samples and samples - loop_start != loop_samples:
        raise VgmError(
            f"VGM loop duration mismatch: header {loop_samples}, "
            f"commands {samples - loop_start}"
        )
    return VgmInfo(
        version=version,
        clock=clock,
        frequency_divider=frequency_divider,
        chip=chip,
        banks=banks,
        total_samples=samples,
        loop_samples=loop_samples,
        loop_start_sample=loop_start,
        loop_offset=loop_offset,
        gd3=parse_gd3(data),
    ), writes


def instrument_signature(registers: list[list[int]], bank: int,
                         channel: int) -> tuple[int, ...]:
    modulator = OPERATOR_OFFSETS[channel]
    carrier = modulator + 3
    values: list[int] = []
    for operator in (modulator, carrier):
        values.extend(registers[bank][base + operator]
                      for base in (0x20, 0x60, 0x80, 0xE0))
    # Modulator level is part of FM timbre.  Carrier level is note volume, so
    # retain only its key-scale bits when identifying an instrument.
    values.extend((registers[bank][0x40 + modulator],
                   registers[bank][0x40 + carrier] & 0xC0,
                   registers[bank][0xC0 + channel] & 0x0F))
    return tuple(values)


def channel_frequency(registers: list[list[int]], bank: int, channel: int,
                      info: VgmInfo) -> float:
    low = registers[bank][0xA0 + channel]
    high = registers[bank][0xB0 + channel]
    f_number = low | (high & 3) << 8
    block = high >> 2 & 7
    return (f_number * (1 << block) * info.clock /
            (info.frequency_divider * (1 << 20)))


def frequency_note(frequency: float) -> int:
    if frequency <= 0:
        raise VgmError("key-on uses a zero OPL frequency")
    return round(69 + 12 * math.log2(frequency / 440.0))


def playable_note(note: int) -> int:
    """Preserve the source octave unless the 15-bit phase step cannot encode it."""
    def step(value: int) -> int:
        frequency = 440.0 * 2.0 ** ((value - 69) / 12.0)
        return round(frequency * 65536.0 / TARGET_RATE)

    while step(note) <= 0:
        note += 12
    while step(note) >= 0x8000:
        note -= 12
    return note


def note_name(note: int) -> str:
    names = ("C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B")
    return f"{names[note % 12]}{note // 12 - 1}"


def signature_id(signature: tuple[int, ...]) -> str:
    return hashlib.sha256(bytes(signature)).hexdigest()[:12]


def key_events(writes: list[RegisterWrite], info: VgmInfo
               ) -> tuple[list[KeyEvent], Counter[tuple[int, ...]]]:
    registers = [[0] * 256 for _ in range(2)]
    active: dict[tuple[int, int], KeyEvent] = {}
    events: list[KeyEvent] = []
    counts: Counter[tuple[int, ...]] = Counter()
    for write in writes:
        old = registers[write.bank][write.register]
        registers[write.bank][write.register] = write.value
        if not 0xB0 <= write.register <= 0xB8:
            continue
        channel = write.register - 0xB0
        key = (write.bank, channel)
        old_on, new_on = bool(old & 0x20), bool(write.value & 0x20)
        if old_on and not new_on and key in active:
            active[key].end = write.sample
            events.append(active.pop(key))
        elif not old_on and new_on:
            signature = instrument_signature(registers, write.bank, channel)
            event = KeyEvent(
                start=write.sample,
                end=info.total_samples,
                bank=write.bank,
                channel=channel,
                signature=signature,
                note=frequency_note(channel_frequency(
                    registers, write.bank, channel, info,
                )),
            )
            active[key] = event
            counts[signature] += 1
    for event in active.values():
        events.append(event)
    return events, counts


def melodic_signatures(events: list[KeyEvent], counts: Counter[tuple[int, ...]]
                       ) -> set[tuple[int, ...]]:
    pitches: dict[tuple[int, ...], set[int]] = defaultdict(set)
    simultaneous: dict[tuple[tuple[int, ...], int], list[KeyEvent]] = defaultdict(list)
    for event in events:
        pitches[event.signature].add(event.note)
        simultaneous[event.signature, event.start].append(event)
    result = {
        signature for signature, count in counts.items()
        if count >= 8 and len(pitches[signature]) >= 4
    }
    # A register stream can voice a chord with one instrument on several OPL
    # channels at exactly the same VGM sample.  Three distinct simultaneous
    # pitches are direct evidence of a melodic chord even when that patch is
    # never used at a fourth pitch.
    for (signature, _start), group in simultaneous.items():
        if (len({event.note for event in group}) >= 3 and
                len({(event.bank, event.channel) for event in group}) >= 3):
            result.add(signature)
    return result


def editor_volume(registers: list[list[int]], bank: int, channel: int) -> int:
    modulator = OPERATOR_OFFSETS[channel]
    carrier = modulator + 3
    connection = registers[bank][0xC0 + channel] & 1
    carrier_attenuation = registers[bank][0x40 + carrier] & 63
    # YM3812 total-level values are logarithmic attenuation in 0.75 dB steps,
    # not linear volume.  Convert dB to linear amplitude before quantizing to
    # JukuPoly's linear 1..16 editor scale.
    amplitude = 10.0 ** (-(carrier_attenuation * 0.75) / 20.0)
    if connection:
        # In parallel connection mode the manual specifies the sum of both
        # operators.  JukuPoly has one bounded pulse-amplitude channel, so cap
        # that sum at its full-scale output.
        modulator_attenuation = registers[bank][0x40 + modulator] & 63
        amplitude += 10.0 ** (-(modulator_attenuation * 0.75) / 20.0)
    return max(1, min(16, round(min(1.0, amplitude) * 15) + 1))


def choose_candidates(candidates: dict[int, Candidate], previous: list[int | None],
                      started: set[int]) -> dict[int, Candidate]:
    if len(candidates) <= 3:
        return candidates
    previous_notes = {note for note in previous if note is not None}
    best: tuple[tuple[int, int, int, int], tuple[int, ...]] | None = None
    for notes in itertools.combinations(sorted(candidates), 3):
        score = (
            # A newly articulated note is musical information; retaining a
            # sustaining voice in its place can erase an entire melody note.
            sum(note in started for note in notes),
            sum(note in previous_notes for note in notes),
            sum(candidates[note].volume for note in notes),
            max(notes) - min(notes),
        )
        if best is None or score > best[0]:
            best = score, notes
    assert best is not None
    return {note: candidates[note] for note in best[1]}


def assign_channels(candidates: dict[int, Candidate], previous: list[int | None]
                    ) -> list[Candidate | None]:
    result: list[Candidate | None] = [None, None, None]
    remaining = dict(candidates)
    for channel, note in enumerate(previous):
        if note in remaining:
            result[channel] = remaining.pop(note)
    free = [channel for channel, value in enumerate(result) if value is None]
    free.sort(key=lambda channel: (
        previous[channel] is None,
        previous[channel] if previous[channel] is not None else channel,
    ))
    for channel, note in zip(free, sorted(remaining)):
        result[channel] = remaining[note]
    return result


def percussion_for(note: int) -> tuple[int, int, int]:
    if note <= 44:
        return 1, 7, 3                 # kick, filter, selection priority
    if note <= 69:
        return 2, 8, 2                 # snare/tom reduction
    return 3, 9, 1                     # hat/cymbal reduction


def compile_score(info: VgmInfo, writes: list[RegisterWrite], source: Path,
                  compressed_sha: str, vgm_sha: str,
                  melodic_overrides: set[str],
                  percussion_overrides: dict[str, int],
                  prioritize_articulations: bool = False) -> dict:
    if any(write.bank == 1 and write.register == 0x04 and write.value & 0x3F
           for write in writes):
        raise VgmError("four-operator OPL3 channels are not supported")
    if any(write.bank == 0 and write.register == 0xBD and write.value & 0x20
           for write in writes):
        raise VgmError("OPL hardware-rhythm mode is not supported")
    events, instrument_counts = key_events(writes, info)
    melodic = melodic_signatures(events, instrument_counts)
    known_signatures = {signature_id(signature): signature
                        for signature in instrument_counts}
    unknown_melodic = sorted(melodic_overrides - set(known_signatures))
    if unknown_melodic:
        raise VgmError("unknown melodic signature(s): " +
                       ", ".join(unknown_melodic))
    melodic.update(known_signatures[identifier]
                   for identifier in melodic_overrides)
    if not melodic:
        # A useful failure is better than silently turning every note into a
        # drum.  Test this after applying explicit overrides so a fixed-pitch
        # fanfare or chord can still be imported deliberately.
        raise VgmError(
            "could not identify any variable-pitch OPL instrument; "
            "use --melodic-signature for a known fixed-pitch voice"
        )
    unknown_overrides = sorted(set(percussion_overrides) - set(known_signatures))
    if unknown_overrides:
        raise VgmError("unknown percussion signature(s): " +
                       ", ".join(unknown_overrides))
    conflicting_overrides = sorted(
        identifier for identifier, signature in known_signatures.items()
        if identifier in percussion_overrides and signature in melodic
    )
    if conflicting_overrides:
        raise VgmError("percussion override identifies melodic signature(s): " +
                       ", ".join(conflicting_overrides))
    total_frames = (info.total_samples * FRAMES_PER_SECOND + VGM_RATE // 2) // VGM_RATE
    by_frame: dict[int, list[RegisterWrite]] = defaultdict(list)
    for write in writes:
        frame = (write.sample * FRAMES_PER_SECOND + VGM_RATE // 2) // VGM_RATE
        if frame < total_frames:
            by_frame[frame].append(write)

    registers = [[0] * 256 for _ in range(2)]
    previous_notes: list[int | None] = [None, None, None]
    last_note_trigger: dict[int, int] = {}
    last_drum_trigger = {1: -100, 2: -100, 3: -100}
    rows: list[dict] = []
    source_polyphony = 0
    selected_polyphony = 0
    percussion_hits = Counter()
    dropped_note_frames = 0

    for frame in range(total_frames):
        started: set[int] = set()
        drum_candidates: list[tuple[int, int, int, int]] = []
        for write in by_frame.get(frame, ()):
            old = registers[write.bank][write.register]
            registers[write.bank][write.register] = write.value
            if not 0xB0 <= write.register <= 0xB8:
                continue
            if old & 0x20 or not write.value & 0x20:
                continue
            channel = write.register - 0xB0
            signature = instrument_signature(registers, write.bank, channel)
            note = frequency_note(channel_frequency(
                registers, write.bank, channel, info,
            ))
            folded = playable_note(note)
            if signature in melodic:
                started.add(folded)
            else:
                identifier = signature_id(signature)
                if identifier in percussion_overrides:
                    sample = percussion_overrides[identifier]
                    filter_value = {1: 7, 2: 8, 3: 9}[sample]
                    priority = {1: 3, 2: 2, 3: 1}[sample]
                else:
                    sample, filter_value, priority = percussion_for(note)
                volume = max(1, min(4, round(editor_volume(
                    registers, write.bank, channel,
                ) / 4)))
                drum_candidates.append((priority, volume, sample, filter_value))

        candidates: dict[int, Candidate] = {}
        active_count = 0
        for bank in range(info.banks):
            for channel in range(9):
                if not registers[bank][0xB0 + channel] & 0x20:
                    continue
                signature = instrument_signature(registers, bank, channel)
                if signature not in melodic:
                    continue
                note = playable_note(frequency_note(channel_frequency(
                    registers, bank, channel, info,
                )))
                volume = editor_volume(registers, bank, channel)
                active_count += 1
                if note not in candidates or candidates[note].volume < volume:
                    candidates[note] = Candidate(note, volume)
        source_polyphony = max(source_polyphony, active_count)
        if len(candidates) > 3:
            dropped_note_frames += 1
        candidates = choose_candidates(
            candidates,
            previous_notes,
            started if prioritize_articulations else set(),
        )
        selected_polyphony = max(selected_polyphony, len(candidates))
        assigned = assign_channels(candidates, previous_notes)

        row: dict = {}
        for channel, candidate in enumerate(assigned):
            field = f"tone{channel + 1}"
            previous = previous_notes[channel]
            if candidate is None:
                if previous is not None:
                    row[field] = {"note": "---"}
                previous_notes[channel] = None
                continue
            retrigger = candidate.note in started and (
                frame - last_note_trigger.get(candidate.note, -100) > 1
            )
            if previous != candidate.note or retrigger:
                row[field] = {
                    "note": note_name(candidate.note),
                    "volume": candidate.volume,
                    "envelope_speed": 8,
                    "envelope_mode": "hold",
                }
                if retrigger:
                    last_note_trigger[candidate.note] = frame
            previous_notes[channel] = candidate.note

        if drum_candidates:
            _priority, volume, sample, filter_value = max(drum_candidates)
            if frame - last_drum_trigger[sample] > 1:
                row["percussion"] = {
                    "sample": sample,
                    "volume": volume,
                    "filter": filter_value,
                    "offset": 1,
                }
                last_drum_trigger[sample] = frame
                percussion_hits[sample] += 1

        if not row and rows and rows[-1]["frames"] < 255:
            rows[-1]["frames"] += 1
        else:
            rows.append({"frames": 1, **row})

    signatures = []
    pitches: dict[tuple[int, ...], set[int]] = defaultdict(set)
    for event in events:
        pitches[event.signature].add(event.note)
    for signature, count in instrument_counts.most_common():
        signatures.append({
            "id": signature_id(signature),
            "key_ons": count,
            "distinct_pitches": len(pitches[signature]),
            "melodic": signature in melodic,
        })

    gd3 = info.gd3
    title = gd3.get("track_en") or gd3.get("track_jp") or source.stem
    composer = gd3.get("author_en") or gd3.get("author_jp") or "Unknown"
    opl_generation = "OPL3" if info.banks == 2 else "OPL2"
    return {
        "schema": "jukupoly-song-v1",
        "title": f"{title} ({opl_generation}/VGZ JukuPoly reduction)",
        "composer": composer,
        "arrangement": (
            f"Automatic {info.chip.split()[0]} reduction: variable-pitch OPL instruments to "
            "three deduplicated tones; fixed-pitch instruments to percussion"
        ),
        "source": {
            "name": source.name,
            "format": "gzip-compressed VGM" if source.suffix.lower() == ".vgz" else "VGM",
            "compressed_sha256": compressed_sha,
            "vgm_sha256": vgm_sha,
            "vgm_version": f"{info.version >> 8}.{info.version & 0xFF:02X}",
            "chip": info.chip,
            "chip_clock_hz": info.clock,
            "gd3": gd3,
            "license": "No new license asserted for the composition or source recording.",
        },
        "sample_rate_hz": TARGET_RATE,
        "frame_samples": FRAME_SAMPLES,
        "defaults": {
            "tone1": {"volume": 14, "envelope_speed": 8, "envelope_mode": "hold"},
            "tone2": {"volume": 14, "envelope_speed": 8, "envelope_mode": "hold"},
            "tone3": {"volume": 14, "envelope_speed": 8, "envelope_mode": "hold"},
        },
        "conversion": {
            "policy": "finite VGM stream only; never follow the loop back",
            "total_vgm_samples": info.total_samples,
            "duration_seconds": info.total_samples / VGM_RATE,
            "loop_start_sample": info.loop_start_sample,
            "loop_samples": info.loop_samples,
            "duration_frames": total_frames,
            "opl_instruments": signatures,
            "source_melodic_channels_peak": source_polyphony,
            "selected_distinct_tones_peak": selected_polyphony,
            "frames_with_more_than_three_distinct_notes": dropped_note_frames,
            "percussion_hits": {str(key): value for key, value in percussion_hits.items()},
            "melodic_signature_overrides": sorted(melodic_overrides),
            "percussion_signature_overrides": percussion_overrides,
            "voice_selection_policy": (
                "newly articulated notes before sustaining notes"
                if prioritize_articulations else
                "sustaining-note continuity before newly articulated notes"
            ),
            "pitch_policy": (
                "preserve the source MIDI octave; transpose down only when "
                "the 15-bit Juku phase step cannot encode the source note"
            ),
        },
        "notes": (
            f"This is a register-level musical reduction, not {info.chip.split()[0]} emulation. "
            "OPL timbres, envelopes, stereo, feedback, and modulation are not retained."
        ),
        "rows": rows,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path,
                        help="YM3812/YMF262 .vgm or gzip-compressed .vgz")
    parser.add_argument("output", type=Path, help="output jukupoly-song-v1 JSON")
    parser.add_argument(
        "--melodic-signature", action="append", default=[], metavar="ID",
        help="explicitly retain an identified OPL signature as pitched notes",
    )
    parser.add_argument(
        "--percussion-signature", action="append", default=[], metavar="ID=SAMPLE",
        help=("map an identified fixed-pitch OPL signature to JukuPoly "
              "percussion sample 1 (kick), 2 (snare), or 3 (hat)"),
    )
    parser.add_argument(
        "--prioritize-articulations", action="store_true",
        help=("when source polyphony exceeds three tones, retain newly "
              "articulated notes before already-sustaining notes"),
    )
    parser.add_argument(
        "--opl-trace-output", type=Path,
        help=("also write a lossless timed OPL register/semantic trace for "
              "host-side analysis; this does not change the Juku score"),
    )
    args = parser.parse_args()
    melodic_overrides: set[str] = set()
    for identifier in args.melodic_signature:
        if (len(identifier) != 12 or
                any(character not in "0123456789abcdef" for character in identifier)):
            parser.error(f"invalid melodic signature: {identifier!r}")
        if identifier in melodic_overrides:
            parser.error(f"duplicate melodic signature: {identifier}")
        melodic_overrides.add(identifier)
    percussion_overrides: dict[str, int] = {}
    for value in args.percussion_signature:
        identifier, separator, sample_text = value.partition("=")
        if (not separator or len(identifier) != 12 or
                any(character not in "0123456789abcdef" for character in identifier)):
            parser.error(f"invalid percussion signature mapping: {value!r}")
        try:
            sample = int(sample_text)
        except ValueError:
            parser.error(f"invalid percussion sample in mapping: {value!r}")
        if sample not in (1, 2, 3):
            parser.error(f"percussion sample must be 1, 2, or 3: {value!r}")
        if identifier in percussion_overrides:
            parser.error(f"duplicate percussion signature: {identifier}")
        percussion_overrides[identifier] = sample
    data, compressed_sha = decode_source(args.source)
    info, writes = parse_vgm(data)
    if args.opl_trace_output is not None:
        trace = opl_trace.trace_document(writes, info.banks, info.total_samples)
        trace.update({
            "chip": info.chip,
            "chip_clock_hz": info.clock,
            "source_name": args.source.name,
            "source_vgm_sha256": hashlib.sha256(data).hexdigest(),
        })
        args.opl_trace_output.write_text(json.dumps(trace, indent=2) + "\n")
    score = compile_score(
        info, writes, args.source, compressed_sha,
        hashlib.sha256(data).hexdigest(),
        melodic_overrides,
        percussion_overrides,
        args.prioritize_articulations,
    )
    args.output.write_text(json.dumps(score, indent=2) + "\n")
    conversion = score["conversion"]
    print(
        f"JUKUPOLY-VGZ: wrote {args.output} rows={len(score['rows'])} "
        f"frames={conversion['duration_frames']} "
        f"duration={conversion['duration_seconds']:.3f}s "
        f"loop={conversion['loop_start_sample']}/+{conversion['loop_samples']} "
        f"tones={conversion['selected_distinct_tones_peak']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
