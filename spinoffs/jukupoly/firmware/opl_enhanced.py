"""Build a guarded JPS v2 score from M2 voices and all-channel OPL probes."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Iterable

import import_jukupoly_vgz as vgz
import opl_envelope
import opl_oracle
import opl_voices


# Real songs may use the largest guarded batch which their measured frame
# work permits.  The Imp M3 excerpt is much lighter than the synthetic
# three-envelope stress fixture and needs 143 iterations to retain the source
# duration.  Its cycle-model rate is calibrated below after the first pass.
ENHANCED_SAMPLE_RATE = 7_170
ENHANCED_FRAME_SAMPLES = 143
MAX_RELEASE_FRAMES = 64


@dataclass(frozen=True)
class SelectedTone:
    logical_note: int
    logical_voice: int
    midi_note: int


def selected_timeline(allocation: dict, frames: int
                      ) -> list[tuple[SelectedTone, ...]]:
    """Expand sparse inspectable allocator decisions to a 50 Hz timeline."""
    decisions = {item["frame"]: item["selected"]
                 for item in allocation["frames"] if item["frame"] < frames}
    current: tuple[SelectedTone, ...] = ()
    result = []
    for frame in range(frames):
        if frame in decisions:
            current = tuple(SelectedTone(
                item["logical_note"], item["logical_voice"], item["midi_note"],
            ) for item in decisions[frame] if item["midi_note"] is not None)
        result.append(current)
    return result


def assign_target_channels(selected: tuple[SelectedTone, ...],
                           previous: tuple[SelectedTone | None, ...]
                           ) -> tuple[SelectedTone | None, ...]:
    """Keep exact notes, then logical voices, on their prior Juku channels."""
    result: list[SelectedTone | None] = [None, None, None]
    remaining = list(selected)
    for channel, old in enumerate(previous):
        if old is None:
            continue
        match = next((item for item in remaining
                      if item.logical_note == old.logical_note), None)
        if match is not None:
            result[channel] = match
            remaining.remove(match)
    for channel, old in enumerate(previous):
        if result[channel] is not None or old is None:
            continue
        match = next((item for item in remaining
                      if item.logical_voice == old.logical_voice), None)
        if match is not None:
            result[channel] = match
            remaining.remove(match)
    free = [index for index, item in enumerate(result) if item is None]
    for channel, item in zip(free, sorted(
            remaining, key=lambda tone: (tone.midi_note, tone.logical_note))):
        result[channel] = item
    return tuple(result)


def _probe_table(probes: Iterable[opl_oracle.OracleChannelProbe]
                 ) -> dict[tuple[int, int], opl_oracle.OracleProbe]:
    result = {}
    for item in probes:
        if item.probe.sample % opl_voices.ANALYSIS_FRAME:
            raise ValueError("oracle probe is off the 50 Hz analysis grid")
        key = (item.probe.sample // opl_voices.ANALYSIS_FRAME, item.channel)
        if key in result:
            raise ValueError(f"duplicate oracle probe: {key}")
        result[key] = item.probe
    return result


def _logical_level(note: opl_voices.LogicalNote, frame: int,
                   probes: dict[tuple[int, int], opl_oracle.OracleProbe]) -> int:
    amplitude = 0.0
    for bank, channel in note.channels:
        probe = probes[(frame, bank * 9 + channel)]
        amplitude += opl_envelope.opl_channel_amplitude(
            probe.modulator_output_attenuation,
            probe.carrier_output_attenuation,
            probe.connection,
        )
    return round(15 * min(1.0, amplitude))


def fit_selected_envelopes(
        segments: list[opl_voices.NoteSegment],
        notes: list[opl_voices.LogicalNote], allocation: dict,
        channel_probes: Iterable[opl_oracle.OracleChannelProbe], frames: int,
) -> tuple[dict[int, opl_envelope.EnvelopeFit], dict]:
    """Fit every logical note selected within the excerpt.

    Release probes are used only until an OPL member channel is keyed again;
    this prevents the next instrument from contaminating the previous tail.
    """
    timeline = selected_timeline(allocation, frames)
    first_selected: dict[int, int] = {}
    for frame, selected in enumerate(timeline):
        for item in selected:
            first_selected.setdefault(item.logical_note, frame)
    by_identifier = {note.identifier: note for note in notes}
    probe_table = _probe_table(channel_probes)
    channel_starts: dict[tuple[int, int], list[int]] = defaultdict(list)
    for segment in segments:
        channel_starts[(segment.bank, segment.channel)].append(segment.start)

    fits: dict[int, opl_envelope.EnvelopeFit] = {}
    measurements = []
    direction_mismatches = 0
    for identifier, selected_frame in sorted(first_selected.items(),
                                              key=lambda item: item[1]):
        note = by_identifier[identifier]
        note_end = max(selected_frame + 1, opl_voices.analysis_frame(note.end))
        key_off_frame: int | None = note_end - selected_frame
        if note_end >= frames:
            note_end = frames
            key_off_frame = None
            reference_end = frames - 1
        else:
            next_starts = []
            for channel in note.channels:
                next_starts.extend(
                    start for start in channel_starts[channel]
                    if start >= note.end
                )
            next_frame = min(
                (opl_voices.analysis_frame(start) for start in next_starts),
                default=frames,
            )
            reference_end = min(
                frames - 1, note_end + MAX_RELEASE_FRAMES, next_frame - 1,
            )
            if reference_end < note_end:
                # An immediate key-on on every member channel replaces the
                # source release; there is no uncontaminated tail to fit.
                reference_end = max(selected_frame, note_end - 1)
                key_off_frame = None
        reference = tuple(
            _logical_level(note, frame, probe_table)
            for frame in range(selected_frame, reference_end + 1)
        )
        # A keyed but still inaudible source is not useful as a target voice.
        # Keep the allocator evidence visible but give the strict ABI its
        # quietest valid packet rather than inventing an audible envelope.
        peak = max(reference)
        if peak == 0:
            reference = tuple(0 for _ in reference)
            forced_peak = 1
        else:
            forced_peak = None
        if key_off_frame is not None and key_off_frame >= len(reference):
            key_off_frame = len(reference) - 1
        fit = opl_envelope.fit_envelope(
            reference,
            key_off_frame=key_off_frame,
            sustain_while_keyed=note.sustained_envelope,
            counter_at_onset=(selected_frame + 1) & 0xFF,
            peak_level=forced_peak,
        )
        fits[identifier] = fit
        keyed_end = (key_off_frame if key_off_frame is not None
                     else len(reference) - 1)
        reference_peak_at = max(
            range(keyed_end + 1), key=lambda index: reference[index],
        )
        predicted_peak_at = max(
            range(keyed_end + 1), key=lambda index: fit.predicted_levels[index],
        )

        def direction(first: int, last: int) -> int:
            return (last > first) - (last < first)

        directions = {
            "attack": {
                "reference": direction(reference[0], reference[reference_peak_at]),
                "predicted": direction(
                    fit.predicted_levels[0],
                    fit.predicted_levels[predicted_peak_at],
                ),
            },
            "decay": {
                "reference": direction(reference[reference_peak_at],
                                       reference[keyed_end]),
                "predicted": direction(
                    fit.predicted_levels[predicted_peak_at],
                    fit.predicted_levels[keyed_end],
                ),
            },
        }
        if key_off_frame is not None and key_off_frame + 1 < len(reference):
            directions["release"] = {
                "reference": direction(reference[key_off_frame], reference[-1]),
                "predicted": direction(
                    fit.predicted_levels[key_off_frame],
                    fit.predicted_levels[-1],
                ),
            }
        for stage, values in directions.items():
            if stage == "attack":
                reference_delta = reference[reference_peak_at] - reference[0]
                predicted_delta = (
                    fit.predicted_levels[predicted_peak_at] -
                    fit.predicted_levels[0]
                )
                immediate_equivalent = (
                    values["predicted"] == 0 and reference_peak_at <= 1
                )
            elif stage == "decay":
                reference_delta = reference[keyed_end] - reference[reference_peak_at]
                predicted_delta = (
                    fit.predicted_levels[keyed_end] -
                    fit.predicted_levels[predicted_peak_at]
                )
                immediate_equivalent = False
            else:
                assert key_off_frame is not None
                reference_delta = reference[-1] - reference[key_off_frame]
                predicted_delta = (
                    fit.predicted_levels[-1] -
                    fit.predicted_levels[key_off_frame]
                )
                immediate_equivalent = False
            values["reference_delta_levels"] = reference_delta
            values["predicted_delta_levels"] = predicted_delta
            values["significant"] = abs(reference_delta) >= 2
            values["match"] = (
                not values["significant"] or immediate_equivalent or
                values["reference"] == values["predicted"]
            )
            direction_mismatches += int(not values["match"])
        measurements.append({
            "logical_note": identifier,
            "selected_frame": selected_frame,
            "source_start_frame": opl_voices.analysis_frame(note.start),
            "source_end_frame": opl_voices.analysis_frame(note.end),
            "reference_frames": len(reference),
            "reference_peak": peak,
            "packet": fit.packet(),
            "mean_absolute_error": fit.absolute_error / len(reference),
            "maximum_error": fit.maximum_error,
            "directions": directions,
        })
    return fits, {
        "selected_logical_notes": len(fits),
        "mean_absolute_error": (
            sum(item["mean_absolute_error"] for item in measurements) /
            len(measurements) if measurements else 0.0
        ),
        "maximum_error": max(
            (item["maximum_error"] for item in measurements), default=0,
        ),
        "direction_mismatches": direction_mismatches,
        "notes": measurements,
    }


def _percussion_timeline(score: dict, frames: int) -> dict[int, dict]:
    result = {}
    frame = 0
    for row in score["rows"]:
        if frame >= frames:
            break
        if "percussion" in row:
            result[frame] = row["percussion"]
        frame += row["frames"]
    return result


def compile_enhanced_score(
        v1_score: dict, notes: list[opl_voices.LogicalNote], allocation: dict,
        fits: dict[int, opl_envelope.EnvelopeFit], frames: int,
        fit_report: dict,
) -> dict:
    """Serialize selected logical voices as generic JPS v2 score rows."""
    timeline = selected_timeline(allocation, frames)
    percussion = _percussion_timeline(v1_score, frames)
    previous: tuple[SelectedTone | None, ...] = (None, None, None)
    rows: list[dict] = []
    for frame, selected in enumerate(timeline):
        assigned = assign_target_channels(selected, previous)
        row: dict = {}
        for channel, (old, new) in enumerate(zip(previous, assigned), 1):
            if old == new:
                continue
            field = f"tone{channel}"
            if new is None:
                row[field] = {"note": "---"}
            else:
                row[field] = {
                    "note": vgz.note_name(new.midi_note),
                    "opl_envelope": fits[new.logical_note].packet(),
                }
        if frame in percussion:
            row["percussion"] = percussion[frame]
        if not row and rows and rows[-1]["frames"] < 255:
            rows[-1]["frames"] += 1
        else:
            rows.append({"frames": 1, **row})
        previous = assigned

    score = dict(v1_score)
    score.update({
        "schema": "jukupoly-song-v2",
        "title": v1_score["title"].replace(" JukuPoly reduction)",
                                                   " JukuPoly envelope reduction)"),
        "arrangement": (
            "Automatic guarded OPL logical-voice reduction with three tones, "
            "fitted 4-bit envelopes, and concurrent percussion"
        ),
        "sample_rate_hz": ENHANCED_SAMPLE_RATE,
        "frame_samples": ENHANCED_FRAME_SAMPLES,
        "rows": rows,
    })
    score["conversion"] = dict(v1_score["conversion"])
    score["conversion"].update({
        "duration_frames": frames,
        "duration_seconds": frames / 50,
        "enhanced_voice_schema": "jukupoly-opl-voice-evidence-v3",
        "enhanced_allocator_schema": allocation["schema"],
        "enhanced_allocation": {
            key: allocation[key] for key in (
                "source_onsets", "protected_onsets", "retained_onsets",
                "gained_onsets", "missed_protected_onsets",
            )
        },
        "enhanced_envelope_fit": fit_report,
        "enhanced_limitations": (
            "Envelope-only M3 slice: waveform, feedback, stereo, tremolo, "
            "vibrato, and held-key pitch automation are not reproduced"
        ),
    })
    score["notes"] = (
        "This is a guarded envelope-aware reduction, not OPL emulation. "
        "Every packet is fitted from pinned-Nuked post-envelope attenuation."
    )
    return score
