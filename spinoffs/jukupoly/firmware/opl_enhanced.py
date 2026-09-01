"""Build a guarded JPS v2 score from M2 voices and all-channel OPL probes."""

from __future__ import annotations

import math
from collections import defaultdict
from dataclasses import dataclass
from typing import Iterable

import import_jukupoly_vgz as vgz
import opl_envelope
import opl_oracle
import opl_tremolo
import opl_voices


# Real songs may use the largest guarded batch which their measured frame
# work permits.  The Imp M3 excerpt is much lighter than the synthetic
# three-envelope stress fixture and needs 143 iterations to retain the source
# duration.  Its cycle-model rate is calibrated below after the first pass.
ENHANCED_SAMPLE_RATE = 7_170
ENHANCED_FRAME_SAMPLES = 143
TREMOLO_SAMPLE_RATE = 6_970
TREMOLO_FRAME_SAMPLES = 140
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
    items = list(probes)
    final_sample = max(item.probe.sample for item in items)
    for item in items:
        if item.probe.sample % opl_voices.ANALYSIS_FRAME:
            # The bridge deliberately appends one exact end-of-stream probe.
            # A finite VGM need not end on a 20 ms boundary; this sentinel is
            # outside the emitted frame timeline and may be ignored.  Any
            # earlier off-grid row still indicates malformed oracle evidence.
            if item.probe.sample == final_sample:
                continue
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


def _logical_level_without_am(
        note: opl_voices.LogicalNote, frame: int,
        probes: dict[tuple[int, int], opl_oracle.OracleProbe],
) -> int:
    """Remove the oracle's exact AM attenuation before 4-bit quantization."""
    amplitude = 0.0
    for bank, channel in note.channels:
        probe = probes[(frame, bank * 9 + channel)]
        modulator = probe.modulator_output_attenuation - (
            probe.tremolo_value if probe.modulator_am else 0
        )
        carrier = probe.carrier_output_attenuation - (
            probe.tremolo_value if probe.carrier_am else 0
        )
        if modulator < 0 or carrier < 0:
            raise ValueError("oracle tremolo exceeds output attenuation")
        amplitude += opl_envelope.opl_channel_amplitude(
            modulator, carrier, probe.connection,
        )
    return round(15 * min(1.0, amplitude))


def fit_selected_envelopes(
        segments: list[opl_voices.NoteSegment],
        notes: list[opl_voices.LogicalNote], allocation: dict,
        channel_probes: Iterable[opl_oracle.OracleChannelProbe], frames: int,
        *, enable_tremolo: bool = False,
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
    tremolo_candidates = 0
    emitted_tremolo = 0
    rejected_indirect_tremolo = 0
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
        baseline_fit = opl_envelope.fit_envelope(
            reference,
            key_off_frame=key_off_frame,
            sustain_while_keyed=note.sustained_envelope,
            counter_at_onset=(selected_frame + 1) & 0xFF,
            peak_level=forced_peak,
            preserve_significant_directions=True,
        )
        direct_am = any(
            probe_table[(frame, bank * 9 + channel)].carrier_am or
            (probe_table[(frame, bank * 9 + channel)].connection == 1 and
             probe_table[(frame, bank * 9 + channel)].modulator_am)
            for frame in range(selected_frame, reference_end + 1)
            for bank, channel in note.channels
        )
        source_am_changed_frames = sum(
            reference[offset] != _logical_level_without_am(
                note, frame, probe_table,
            )
            for offset, frame in enumerate(
                range(selected_frame, reference_end + 1)
            )
        )
        if direct_am and enable_tremolo:
            joint = opl_tremolo.fit_joint_envelope_tremolo(
                reference, start_frame=selected_frame,
                key_off_frame=key_off_frame,
                sustain_while_keyed=note.sustained_envelope,
                counter_at_onset=(selected_frame + 1) & 0xFF,
                preserve_significant_directions=True,
                peak_level=forced_peak,
                baseline_envelope=baseline_fit,
            )
            fitted_depth = joint.depth_levels
            fitted_envelope = joint.envelope
            fitted_improvement = joint.squared_error_improvement
            fitted_squared_error = joint.envelope.squared_error
        else:
            # Preserve the cheap M3 diagnostic when tremolo is disabled, and
            # retain the false-positive audit for indirect FM modulators.
            residual = opl_tremolo.fit_tremolo(
                reference, baseline_fit.predicted_levels,
                start_frame=selected_frame,
            )
            rejected_indirect_tremolo += int(
                not direct_am and residual.depth_levels > 0 and
                residual.squared_error_improvement > 0
            )
            fitted_depth = residual.depth_levels if direct_am else 0
            fitted_envelope = baseline_fit
            fitted_improvement = (
                residual.squared_error_improvement if direct_am else 0
            )
            fitted_squared_error = (
                residual.squared_error if direct_am else
                baseline_fit.squared_error
            )
        semantic_candidate = (
            direct_am and source_am_changed_frames > 0 and
            fitted_depth > 0 and fitted_improvement > 0
        )
        tremolo_candidates += int(semantic_candidate)
        emitted_depth = (
            fitted_depth if enable_tremolo and semantic_candidate else 0
        )
        emitted_tremolo += int(emitted_depth > 0)
        fit = fitted_envelope if emitted_depth else baseline_fit
        fits[identifier] = fit
        direction_result = opl_envelope.envelope_directions(
            reference, fit.predicted_levels, key_off_frame,
        )
        directions = direction_result["stages"]
        direction_mismatches += direction_result["mismatches"]
        measurements.append({
            "logical_note": identifier,
            "selected_frame": selected_frame,
            "source_start_frame": opl_voices.analysis_frame(note.start),
            "source_end_frame": opl_voices.analysis_frame(note.end),
            "reference_frames": len(reference),
            "reference_peak": peak,
            "packet": fit.packet(),
            "baseline_packet": baseline_fit.packet(),
            "mean_absolute_error": fit.absolute_error / len(reference),
            "maximum_error": fit.maximum_error,
            "directions": directions,
            "tremolo_analysis": {
                "directly_audible_am_path": direct_am,
                "source_changed_frames_4bit": source_am_changed_frames,
                "best_depth_levels": fitted_depth,
                "emitted_depth_levels": emitted_depth,
                "baseline_squared_error": baseline_fit.squared_error,
                "fitted_squared_error": fitted_squared_error,
                "squared_error_improvement": fitted_improvement,
                "improvement_per_frame": fitted_improvement / len(reference),
                "semantic_candidate": semantic_candidate,
            },
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
        "tremolo_analysis": {
            "model": "shared 3.7 Hz 16-step phase; 0..3 level attenuation",
            "enabled": enable_tremolo,
            "semantic_candidates": tremolo_candidates,
            "emitted_notes": emitted_tremolo,
            "rejected_indirect_candidates": rejected_indirect_tremolo,
        },
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


def _pitch_at_frame(segment: opl_voices.NoteSegment, frame: int
                    ) -> float | None:
    result = None
    for point in segment.pitches:
        if opl_voices.analysis_frame(point.sample) > frame:
            break
        result = point.midi_pitch
    return result


def _logical_phase_step(
        note: opl_voices.LogicalNote,
        segments: dict[int, opl_voices.NoteSegment], frame: int,
        mapped_midi: int, sample_rate: int,
) -> int:
    pitches = [
        _pitch_at_frame(segments[identifier], frame)
        for identifier in note.members
    ]
    finite = [pitch for pitch in pitches
              if pitch is not None and math.isfinite(pitch)]
    if not finite or note.initial_pitch is None:
        raise ValueError("selected held-pitch note has no finite source pitch")
    source_pitch = sum(finite) / len(finite)
    octave_offset = mapped_midi - round(note.initial_pitch)
    target_pitch = source_pitch + octave_offset
    frequency = 440.0 * 2.0 ** ((target_pitch - 69.0) / 12.0)
    step = round(frequency * 65536.0 / sample_rate)
    if not 0 < step < 0x8000:
        raise ValueError("held-pitch phase step exceeds target range")
    return step


def compile_enhanced_score(
        v1_score: dict, notes: list[opl_voices.LogicalNote], allocation: dict,
        fits: dict[int, opl_envelope.EnvelopeFit], frames: int,
        fit_report: dict, *, target_sample_rate: int | None = None,
        frame_samples: int | None = None,
        segments: list[opl_voices.NoteSegment] | None = None,
        enable_held_pitch: bool = False,
) -> dict:
    """Serialize selected logical voices as generic JPS v2 score rows."""
    tremolo_depths = {
        item["logical_note"]: item["tremolo_analysis"].get(
            "emitted_depth_levels", 0,
        )
        for item in fit_report.get("notes", [])
    }
    tremolo_enabled = any(tremolo_depths.values())
    if target_sample_rate is None:
        target_sample_rate = (
            TREMOLO_SAMPLE_RATE if tremolo_enabled else ENHANCED_SAMPLE_RATE
        )
    if frame_samples is None:
        frame_samples = (
            TREMOLO_FRAME_SAMPLES if tremolo_enabled else
            ENHANCED_FRAME_SAMPLES
        )
    if not 4_000 <= target_sample_rate <= 12_000:
        raise ValueError("enhanced target_sample_rate must be 4000..12000")
    if not 129 <= frame_samples <= 143:
        raise ValueError("enhanced frame_samples must be 129..143")
    if enable_held_pitch and segments is None:
        raise ValueError("held-pitch conversion requires source segments")
    by_note = {note.identifier: note for note in notes}
    by_segment = {
        segment.identifier: segment for segment in (segments or [])
    }
    timeline = selected_timeline(allocation, frames)
    percussion = _percussion_timeline(v1_score, frames)
    previous: tuple[SelectedTone | None, ...] = (None, None, None)
    previous_steps: tuple[int | None, ...] = (None, None, None)
    held_pitch_packets = 0
    rows: list[dict] = []
    for frame, selected in enumerate(timeline):
        assigned = assign_target_channels(selected, previous)
        assigned_steps = tuple(
            None if tone is None else _logical_phase_step(
                by_note[tone.logical_note], by_segment, frame,
                tone.midi_note, target_sample_rate,
            )
            for tone in assigned
        ) if enable_held_pitch else (None, None, None)
        row: dict = {}
        for channel, (old, new, old_step, new_step) in enumerate(zip(
                previous, assigned, previous_steps, assigned_steps), 1):
            step_changed = (
                enable_held_pitch and old == new and new is not None and
                old_step != new_step
            )
            if old == new and not step_changed:
                continue
            field = f"tone{channel}"
            if new is None:
                row[field] = {"note": "---"}
            else:
                event = {
                    "opl_envelope": fits[new.logical_note].packet(),
                }
                if enable_held_pitch:
                    assert new_step is not None
                    event["phase_step"] = new_step
                    if step_changed:
                        event["legato"] = True
                        held_pitch_packets += 1
                else:
                    event["note"] = vgz.note_name(new.midi_note)
                depth = tremolo_depths.get(new.logical_note, 0)
                if depth:
                    event["opl_tremolo_depth"] = depth
                row[field] = event
        if frame in percussion:
            row["percussion"] = percussion[frame]
        if not row and rows and rows[-1]["frames"] < 255:
            rows[-1]["frames"] += 1
        else:
            rows.append({"frames": 1, **row})
        previous = assigned
        previous_steps = assigned_steps

    score = dict(v1_score)
    reduction_features = "envelope+tremolo" if tremolo_enabled else "envelope"
    if enable_held_pitch:
        reduction_features += "+held-pitch"
    reduction_name = f" JukuPoly {reduction_features} reduction)"
    arrangement_features = (
        "fitted 4-bit envelopes, guarded shared tremolo"
        if tremolo_enabled else "fitted 4-bit envelopes"
    )
    if enable_held_pitch:
        arrangement_features += ", held-key pitch automation"
    score.update({
        "schema": "jukupoly-song-v2",
        "title": v1_score["title"].replace(" JukuPoly reduction)",
                                                   reduction_name),
        "arrangement": (
            "Automatic guarded OPL logical-voice reduction with three tones, "
            f"{arrangement_features}, and concurrent percussion"
        ),
        "sample_rate_hz": target_sample_rate,
        "frame_samples": frame_samples,
        "rows": rows,
    })
    score["conversion"] = dict(v1_score["conversion"])
    source_duration = score["conversion"]["duration_seconds"]
    score["conversion"].update({
        "duration_frames": frames,
        "duration_seconds": frames / 50,
        "source_duration_seconds": source_duration,
        "enhanced_voice_schema": "jukupoly-opl-voice-evidence-v3",
        "enhanced_allocator_schema": allocation["schema"],
        "enhanced_allocation": {
            key: allocation[key] for key in (
                "source_onsets", "protected_onsets", "retained_onsets",
                "gained_onsets", "missed_protected_onsets",
            )
        },
        "enhanced_envelope_fit": fit_report,
        "enhanced_held_pitch": {
            "enabled": enable_held_pitch,
            "emitted_legato_packets": held_pitch_packets,
            "phase_step_generation_hz": (
                target_sample_rate if enable_held_pitch else None
            ),
            "policy": (
                "50 Hz source pitch points quantized to target phase steps; "
                "emit only changes while the same logical note retains its "
                "target channel"
            ),
        },
        "enhanced_limitations": (
            "Envelope plus guarded amplitude-tremolo slice: waveform, "
            "feedback, stereo, FM-modulator-only AM timbre, and vibrato are "
            "not reproduced" + (
                "" if enable_held_pitch else
                "; held-key pitch automation is not reproduced"
            )
            if tremolo_enabled else
            "Envelope-only M3 slice: waveform, feedback, stereo, tremolo, "
            "and vibrato are not reproduced" + (
                "" if enable_held_pitch else
                "; held-key pitch automation is not reproduced"
            )
        ),
    })
    score["notes"] = (
        "This is a guarded envelope/tremolo reduction, not OPL emulation. "
        "Every enabled depth has a direct AM path, survives 4-bit source "
        "quantization, and improves a joint pinned-Nuked fit."
        if tremolo_enabled else
        "This is a guarded envelope-aware reduction, not OPL emulation. "
        "Every packet is fitted from pinned-Nuked post-envelope attenuation."
    )
    if enable_held_pitch:
        score["notes"] += (
            " Selected 50 Hz source pitch changes are emitted through the "
            "existing JPS2 legato packet only when their quantized target "
            "phase step changes."
        )
    return score
