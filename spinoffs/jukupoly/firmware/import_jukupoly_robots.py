#!/usr/bin/env python3
"""Make a one-minute JukuPoly reduction of Kraftwerk's The Robots."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import defaultdict
from pathlib import Path

from import_jukupoly_suspense import MidiError, note_name, parse_midi, quantized_frame


EXPECTED_MIDI_SHA256 = "74c6e1675ada8d1701433520e3f64b51bc96c8bc387c572e2d211fc0efbbd8d2"
SOURCE_URL = "https://bitmidi.com/kraftwerk-the-robot-mid"
SAMPLE_RATE = 7200
FRAME_SAMPLES = 144
FRAMES_PER_SECOND = SAMPLE_RATE // FRAME_SAMPLES
END_SECONDS = 60

TONE_TRACKS = (
    "Steel Drums",
    "Tremolo Strings",
    "5th Saw Wave",
    "Celesta",
    "Snyth Bass 2",  # Source spelling retained for the hash-locked MIDI.
)
PERCUSSION_TRACKS = (
    "Kick Drum 1",
    "Snare Drum 2",
    "Snare Drum 1",
    "Open High Hat",
    "High Tom 1",
    "High Tom 2",
    "Mid Tom 1",
    "Maracas",
    "Cabasa",
)


def events_by_frame(events: list[tuple[int, int, int, int]], division: int,
                    end_frame: int) -> dict[int, list[tuple[int, int, int]]]:
    result: dict[int, list[tuple[int, int, int]]] = defaultdict(list)
    for tick, kind, note, velocity in events:
        frame = quantized_frame(tick, division)
        if frame < end_frame:
            result[frame].append((kind, note, velocity))
    return result


def audible_note(note: int, channel: str) -> int:
    if channel == "tone3":
        while note < 48:  # Raise sub-C3 bass notes for the small Juku speaker.
            note += 12
        while note > 71:
            note -= 12
    else:
        while note > 83:  # Retain the line while avoiding very thin C6+ output.
            note -= 12
        while note < 48:
            note += 12
    return note


def selected_notes(frame: int, active: dict[str, set[int]]) -> dict[str, int | None]:
    # This MIDI is a progressive reconstruction. Use all three chord notes at
    # 4 s, replace the middle note with the saw figure at 12 s, the upper note
    # with celesta at 20.5 s, and the lower note with synth bass at 36 s.
    tremolo = sorted(active["Tremolo Strings"])
    if frame < 4 * FRAMES_PER_SECOND:
        tones = {
            "tone1": max(active["Steel Drums"], default=None),
            "tone2": None,
            "tone3": None,
        }
    else:
        tones = {
            "tone1": tremolo[-1] if tremolo else None,
            "tone2": tremolo[len(tremolo) // 2] if len(tremolo) >= 3 else None,
            "tone3": tremolo[0] if tremolo else None,
        }
    if frame >= 12 * FRAMES_PER_SECOND:
        tones["tone2"] = max(active["5th Saw Wave"], default=None)
    if frame >= round(20.5 * FRAMES_PER_SECOND):
        tones["tone1"] = max(active["Celesta"], default=None)
    if frame >= 36 * FRAMES_PER_SECOND:
        tones["tone3"] = min(active["Snyth Bass 2"], default=None)
    return tones


def percussion_at_frame(
        frame_events: dict[str, dict[int, list[tuple[int, int, int]]]],
        frame: int) -> dict | None:
    hits = {
        name for name in PERCUSSION_TRACKS
        if any(kind == 0x90 and velocity for kind, _note, velocity
               in frame_events[name].get(frame, ()))
    }
    if not hits:
        return None
    if "Kick Drum 1" in hits:
        return {"sample": 1, "volume": 4, "filter": 8, "offset": 1}
    if hits & {"Snare Drum 1", "Snare Drum 2"}:
        return {"sample": 2, "volume": 3, "filter": 7, "offset": 1}
    if hits & {"High Tom 1", "High Tom 2", "Mid Tom 1"}:
        return {"sample": 1, "volume": 3, "filter": 5, "offset": 3}
    return {"sample": 3, "volume": 2, "filter": 9, "offset": 3}


def compile_score(midi: bytes) -> dict:
    digest = hashlib.sha256(midi).hexdigest()
    if digest != EXPECTED_MIDI_SHA256:
        raise MidiError(f"unexpected The Robots MIDI SHA-256: {digest}")
    division, tracks = parse_midi(midi)
    by_name = {name: events for name, events in tracks}
    wanted = TONE_TRACKS + PERCUSSION_TRACKS
    missing = [name for name in wanted if name not in by_name]
    if missing:
        raise MidiError(f"missing source tracks: {', '.join(missing)}")

    end_frame = END_SECONDS * FRAMES_PER_SECOND
    framed = {
        name: events_by_frame(by_name[name], division, end_frame)
        for name in wanted
    }
    change_frames = {0, 4 * FRAMES_PER_SECOND, 12 * FRAMES_PER_SECOND,
                     round(20.5 * FRAMES_PER_SECOND), 36 * FRAMES_PER_SECOND}
    for events in framed.values():
        change_frames.update(events)

    active = {name: set() for name in TONE_TRACKS}
    previous: dict[str, int | None] = {name: None for name in ("tone1", "tone2", "tone3")}
    timeline: dict[int, dict] = defaultdict(dict)
    for frame in sorted(frame for frame in change_frames if frame < end_frame):
        for name in TONE_TRACKS:
            for kind, note, velocity in framed[name].get(frame, ()):
                if kind == 0x80 or velocity == 0:
                    active[name].discard(note)
                else:
                    active[name].add(note)
        selected = selected_notes(frame, active)
        for channel, note in selected.items():
            if note == previous[channel]:
                continue
            event = {"note": "---" if note is None else note_name(audible_note(note, channel))}
            timeline[frame][channel] = event
            previous[channel] = note
        percussion = percussion_at_frame(framed, frame)
        if percussion is not None:
            timeline[frame]["percussion"] = percussion

    event_frames = sorted(timeline)
    rows = []
    for index, frame in enumerate(event_frames):
        following = event_frames[index + 1] if index + 1 < len(event_frames) else end_frame
        duration = following - frame
        event = timeline[frame]
        first_piece = True
        while duration > 255:
            rows.append({"frames": 255, **(event if first_piece else {})})
            first_piece = False
            duration -= 255
        rows.append({"frames": duration, **(event if first_piece else {})})

    return {
        "schema": "jukupoly-song-v1",
        "title": "The Robots / Die Roboter (JukuPoly first-minute arrangement)",
        "composer": "Ralf Hütter, Florian Schneider, Karl Bartos",
        "arrangement": "Three-tone pin-pulse reduction for JukuPoly",
        "source": {
            "name": "KRAFTWERK.The robot.mid",
            "credit": (
                "The Robots performed by Kraftwerk; written by Ralf Hütter, "
                "Florian Schneider, and Karl Bartos"
            ),
            "url": SOURCE_URL,
            "download_sha256": digest,
        },
        "sample_rate_hz": SAMPLE_RATE,
        "frame_samples": FRAME_SAMPLES,
        "defaults": {
            "tone1": {"volume": 12, "envelope_speed": 1, "envelope_mode": "decay"},
            "tone2": {"volume": 10, "envelope_speed": 1, "envelope_mode": "decay"},
            "tone3": {"volume": 14, "envelope_speed": 2, "envelope_mode": "decay"},
        },
        "notes": (
            "Hash-locked archive MIDI, fixed 120 BPM, reduced through its first "
            "minute. The progressive 4/12/20.5/36-second layer entrances become "
            "three chord voices, then high line + saw figure + raised bass. Kick, "
            "snare, tom, and hat-family events share the three synthesized samples."
        ),
        "rows": rows,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("midi", type=Path, help="hash-matching archive MIDI")
    parser.add_argument("output", type=Path, help="output JukuPoly JSON score")
    parser.add_argument("--check", action="store_true", help="fail if output is stale")
    args = parser.parse_args()
    score = compile_score(args.midi.read_bytes())
    rendered = json.dumps(score, indent=2, ensure_ascii=False) + "\n"
    if args.check:
        if not args.output.exists() or args.output.read_text() != rendered:
            raise SystemExit(f"{args.output} is missing or stale")
        action = "checked"
    else:
        args.output.write_text(rendered)
        action = "wrote"
    print(
        f"JUKUPOLY-ROBOTS: {action} {args.output} rows={len(score['rows'])} "
        f"frames={END_SECONDS * FRAMES_PER_SECOND}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
