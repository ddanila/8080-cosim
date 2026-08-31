#!/usr/bin/env python3
"""Make the one-minute JukuPoly Suspense score from the original DOOM MIDI."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import defaultdict
from pathlib import Path


EXPECTED_MIDI_SHA256 = "ae1d9201e623310ba16a317ff93f1fecd5d42b4efd24212bc2476080d23ea7ec"
SOURCE_URL = "https://www.vgmpf.com/Wiki/images/4/46/Doom_%28DOS%29.zip"
SAMPLE_RATE = 7200
FRAME_SAMPLES = 144
FRAMES_PER_SECOND = SAMPLE_RATE // FRAME_SAMPLES
SHORT_SECONDS = 60
FULL_SECONDS = 164


class MidiError(ValueError):
    pass


def variable_length(data: bytes, offset: int) -> tuple[int, int]:
    value = 0
    for _ in range(4):
        byte = data[offset]
        offset += 1
        value = value << 7 | byte & 0x7f
        if byte & 0x80 == 0:
            return value, offset
    raise MidiError("invalid MIDI variable-length quantity")


def parse_midi(data: bytes) -> tuple[int, list[tuple[str, list[tuple[int, int, int, int]]]]]:
    if data[:4] != b"MThd" or len(data) < 14:
        raise MidiError("missing MIDI header")
    header_size = int.from_bytes(data[4:8], "big")
    header = data[8:8 + header_size]
    if len(header) < 6 or int.from_bytes(header[:2], "big") != 1:
        raise MidiError("expected a format-1 MIDI")
    track_count = int.from_bytes(header[2:4], "big")
    division = int.from_bytes(header[4:6], "big")
    if division & 0x8000:
        raise MidiError("SMPTE MIDI timing is unsupported")

    offset = 8 + header_size
    tracks = []
    tempos = []
    for _ in range(track_count):
        if data[offset:offset + 4] != b"MTrk":
            raise MidiError("missing MIDI track header")
        size = int.from_bytes(data[offset + 4:offset + 8], "big")
        track = data[offset + 8:offset + 8 + size]
        offset += 8 + size
        at = tick = 0
        running = None
        name = ""
        events = []
        while at < len(track):
            delta, at = variable_length(track, at)
            tick += delta
            status = track[at]
            if status < 0x80:
                if running is None:
                    raise MidiError("running status without channel status")
                status = running
            else:
                at += 1
            if status == 0xff:
                kind = track[at]
                at += 1
                length, at = variable_length(track, at)
                value = track[at:at + length]
                at += length
                if kind == 0x03:
                    name = value.decode("latin1").strip()
                elif kind == 0x51:
                    tempos.append((tick, int.from_bytes(value, "big")))
                running = None
                continue
            if status in (0xf0, 0xf7):
                length, at = variable_length(track, at)
                at += length
                running = None
                continue
            running = status
            kind = status & 0xf0
            channel = status & 0x0f
            if kind in (0xc0, 0xd0):
                at += 1
                continue
            first, second = track[at], track[at + 1]
            at += 2
            if kind in (0x80, 0x90):
                events.append((tick, kind, first, second))
        tracks.append((name, events))

    if tempos != [(0, 500000)]:
        raise MidiError(f"expected the original fixed 120 BPM tempo, got {tempos!r}")
    return division, tracks


def note_name(number: int) -> str:
    names = ("C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B")
    return f"{names[number % 12]}{number // 12 - 1}"


def quantized_frame(tick: int, division: int) -> int:
    # At 120 BPM there are division*2 ticks/s. Round to the nearest 20 ms frame.
    denominator = division * 2
    return (tick * FRAMES_PER_SECOND + denominator // 2) // denominator


def tone_events(events: list[tuple[int, int, int, int]], division: int,
                transpose: int, end_seconds: int) -> dict[int, dict]:
    grouped = defaultdict(list)
    for tick, kind, note, velocity in events:
        frame = quantized_frame(tick, division)
        if frame >= end_seconds * FRAMES_PER_SECOND:
            continue
        grouped[frame].append((kind, note, velocity))

    active = set()
    result = {}
    for frame, group in sorted(grouped.items()):
        starts = []
        for kind, note, velocity in group:
            if kind == 0x80 or velocity == 0:
                active.discard(note)
            else:
                active.add(note)
                starts.append(note)
        if starts:
            if len(active) != 1:
                raise MidiError(f"source track is not monophonic at frame {frame}: {active}")
            result[frame] = {"note": note_name(starts[-1] + transpose)}
        elif not active:
            result[frame] = {"note": "---"}
    return result


def compile_score(midi: bytes, end_seconds: int) -> dict:
    digest = hashlib.sha256(midi).hexdigest()
    if digest != EXPECTED_MIDI_SHA256:
        raise MidiError(f"unexpected M_E1M5.mid SHA-256: {digest}")
    division, tracks = parse_midi(midi)
    by_name = {name: events for name, events in tracks}
    wanted = (
        "String Bounce", "Bass Strings", "String Bounce 2", "String Bounce 3",
        "String Bounce 4", "Fret Noise", "Floor Tom", "Reverse Cymbal",
    )
    missing = [name for name in wanted if name not in by_name]
    if missing:
        raise MidiError(f"missing source tracks: {', '.join(missing)}")

    timeline: dict[int, dict] = defaultdict(dict)
    for source, target, transpose in (
            ("String Bounce", "tone1", 0),
            ("Bass Strings", "tone2", 12)):
        for frame, event in tone_events(
                by_name[source], division, transpose, end_seconds).items():
            timeline[frame][target] = event

    if end_seconds == SHORT_SECONDS:
        third_layers = (("String Bounce 2", 0, end_seconds),)
    else:
        # The original adds, rather than replaces, string voices after 88 s.
        # One JukuPoly channel follows the newest layer in each section.
        third_layers = (
            ("String Bounce 2", 0, 88),
            ("String Bounce 3", 88, 128),
            ("String Bounce 4", 128, end_seconds),
        )
        timeline[88 * FRAMES_PER_SECOND]["tone3"] = {"note": "---"}
        timeline[128 * FRAMES_PER_SECOND]["tone3"] = {"note": "---"}
    for source, start, end in third_layers:
        for frame, event in tone_events(
                by_name[source], division, 0, end_seconds).items():
            if start * FRAMES_PER_SECOND <= frame < end * FRAMES_PER_SECOND:
                timeline[frame]["tone3"] = event

    percussion_tracks = (
        ("Fret Noise", 2, 2, 4, 1),
        ("Reverse Cymbal", 3, 3, 5, 1),
        ("Floor Tom", 1, 4, 7, 1),
    )
    for source, sample, volume, filter_value, offset in percussion_tracks:
        for tick, kind, _note, velocity in by_name[source]:
            frame = quantized_frame(tick, division)
            if kind == 0x90 and velocity and frame < end_seconds * FRAMES_PER_SECOND:
                timeline[frame]["percussion"] = {
                    "sample": sample, "volume": volume,
                    "filter": filter_value, "offset": offset,
                }

    end_frame = end_seconds * FRAMES_PER_SECOND
    event_frames = sorted(frame for frame in timeline if frame < end_frame)
    if not event_frames or event_frames[0] != 0:
        raise MidiError("score does not begin at frame zero")
    rows = []
    for index, frame in enumerate(event_frames):
        following = event_frames[index + 1] if index + 1 < len(event_frames) else end_frame
        duration = following - frame
        if not 1 <= duration <= 255:
            raise MidiError(f"invalid row duration {duration} at frame {frame}")
        rows.append({"frames": duration, **timeline[frame]})

    return {
        "schema": "jukupoly-song-v1",
        "title": (
            "Suspense (JukuPoly first-minute arrangement)"
            if end_seconds == SHORT_SECONDS else
            "Suspense (JukuPoly full-song arrangement)"
        ),
        "composer": "Robert (Bobby) Prince",
        "arrangement": "Three-tone pin-pulse reduction for JukuPoly",
        "source": {
            "name": "DOOM E1M5 / M_E1M5.mid",
            "credit": "Music by Robert Prince; DOOM developed and published by id Software",
            "url": SOURCE_URL,
            "download_sha256": digest,
        },
        "sample_rate_hz": SAMPLE_RATE,
        "frame_samples": FRAME_SAMPLES,
        "defaults": {
            "tone1": {"volume": 11, "envelope_speed": 1, "envelope_mode": "decay"},
            "tone2": {"volume": 14, "envelope_speed": 4, "envelope_mode": "hold"},
            "tone3": {"volume": 10, "envelope_speed": 1, "envelope_mode": "decay"},
        },
        "notes": (
            f"Original 0:00-{end_seconds // 60}:{end_seconds % 60:02d} structure at "
            "120 BPM. Bass Strings is raised one octave for the Juku speaker. "
            + (
                "Tone 3 follows String Bounce 2 until 1:28, String Bounce 3 until "
                "2:08, then String Bounce 4; the source layers these voices. "
                if end_seconds == FULL_SECONDS else ""
            )
            + "Fret Noise, Reverse Cymbal, and Floor Tom are approximated with samples "
            "2, 3, and 1. The source MIDI is not required by the normal build."
        ),
        "rows": rows,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("midi", type=Path, help="original os2_doom1/M_E1M5.mid")
    parser.add_argument("output", type=Path, help="output JukuPoly JSON score")
    parser.add_argument("--seconds", type=int, choices=(SHORT_SECONDS, FULL_SECONDS),
                        default=SHORT_SECONDS, help="arrangement duration")
    parser.add_argument("--check", action="store_true", help="fail if output is stale")
    args = parser.parse_args()
    score = compile_score(args.midi.read_bytes(), args.seconds)
    rendered = json.dumps(score, indent=2, ensure_ascii=False) + "\n"
    if args.check:
        if not args.output.exists() or args.output.read_text() != rendered:
            raise SystemExit(f"{args.output} is missing or stale")
        action = "checked"
    else:
        args.output.write_text(rendered)
        action = "wrote"
    print(
        f"JUKUPOLY-SUSPENSE: {action} {args.output} rows={len(score['rows'])} "
        f"frames={args.seconds * FRAMES_PER_SECOND}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
