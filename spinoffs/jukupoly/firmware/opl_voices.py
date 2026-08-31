"""Host-only reconstruction of OPL note segments and voice relationships.

This module deliberately stops short of changing JukuPoly allocation.  It
turns the exact register timeline into inspectable evidence which later M2
policy can validate across complete source packs before it affects a score.
"""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import asdict, dataclass
from typing import Iterable

import opl_trace


VGM_RATE = 44_100
ANALYSIS_FRAME = VGM_RATE // 50
DETUNE_LIMIT_CENTS = 50.0
CONTOUR_LIMIT_CENTS = 25.0


@dataclass(frozen=True)
class PitchPoint:
    sample: int
    f_number: int
    block: int
    midi_pitch: float | None


@dataclass(frozen=True)
class NoteSegment:
    identifier: int
    bank: int
    channel: int
    start: int
    end: int
    patch: str
    pitches: tuple[PitchPoint, ...]


@dataclass(frozen=True)
class VoiceRelation:
    kind: str
    first: int
    second: int
    evidence: tuple[str, ...]


def midi_pitch(f_number: int, block: int, clock: int,
               frequency_divider: int) -> float | None:
    frequency = (f_number * (1 << block) * clock /
                 (frequency_divider * (1 << 20)))
    if frequency <= 0:
        return None
    return 69.0 + 12.0 * math.log2(frequency / 440.0)


def patch_identifier(state: opl_trace.ChannelState) -> str:
    """Stable instrument identity, excluding pitch, key, and output routing."""
    fields = {
        "feedback": state.feedback,
        "connection": state.connection,
        "four_operator_role": state.four_operator_role,
        "four_operator_pair": state.four_operator_pair,
        "modulator": asdict(state.modulator),
        "carrier": asdict(state.carrier),
    }
    encoded = json.dumps(fields, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()[:12]


def _pitch_point(sample: int, state: opl_trace.ChannelState, clock: int,
                 frequency_divider: int) -> PitchPoint:
    return PitchPoint(
        sample=sample,
        f_number=state.f_number,
        block=state.block,
        midi_pitch=midi_pitch(
            state.f_number, state.block, clock, frequency_divider,
        ),
    )


def reconstruct_segments(writes: Iterable[opl_trace.TimedWrite], banks: int,
                         total_samples: int, clock: int,
                         frequency_divider: int) -> list[NoteSegment]:
    """Reconstruct key spans and all pitch changes made while each key is held."""
    timeline = opl_trace.OplTimeline(banks)
    active: dict[tuple[int, int], tuple[int, int, str, list[PitchPoint]]] = {}
    segments: list[NoteSegment] = []

    def finish(key: tuple[int, int], end: int) -> None:
        identifier, start, patch, pitches = active.pop(key)
        segments.append(NoteSegment(
            identifier, key[0], key[1], start, end, patch, tuple(pitches),
        ))

    for write in writes:
        event = timeline.apply(write)
        if event.channel is None or event.kind not in (
                "key_on", "key_off", "pitch"):
            continue
        key = (write.bank, event.channel)
        state = timeline.channel(*key)
        if event.kind == "key_on":
            # A transition-based trace should never have an existing segment,
            # but retaining this guard makes malformed caller input explicit.
            if key in active:
                finish(key, write.sample)
            active[key] = (
                len(segments) + len(active), write.sample,
                patch_identifier(state),
                [_pitch_point(write.sample, state, clock, frequency_divider)],
            )
        elif event.kind == "key_off":
            if key in active:
                finish(key, write.sample)
        elif key in active:
            point = _pitch_point(write.sample, state, clock, frequency_divider)
            pitches = active[key][3]
            if (point.f_number, point.block) != (
                    pitches[-1].f_number, pitches[-1].block):
                pitches.append(point)

    for key in sorted(active):
        finish(key, total_samples)
    segments.sort(key=lambda segment: (
        segment.start, segment.end, segment.bank, segment.channel,
    ))
    return [NoteSegment(
        identifier, segment.bank, segment.channel, segment.start, segment.end,
        segment.patch, segment.pitches,
    ) for identifier, segment in enumerate(segments)]


def _layer_evidence(first: NoteSegment,
                    second: NoteSegment) -> tuple[str, ...] | None:
    if abs(first.start - second.start) > ANALYSIS_FRAME:
        return None
    if abs(first.end - second.end) > ANALYSIS_FRAME:
        return None
    if not first.pitches or not second.pitches:
        return None
    first_origin = first.pitches[0].midi_pitch
    second_origin = second.pitches[0].midi_pitch
    if first_origin is None or second_origin is None:
        return None
    detune = abs(first_origin - second_origin)
    if not math.isfinite(detune) or detune > DETUNE_LIMIT_CENTS / 100.0:
        return None
    if len(first.pitches) != len(second.pitches):
        return None
    for left, right in zip(first.pitches, second.pitches):
        if abs(left.sample - right.sample) > ANALYSIS_FRAME:
            return None
        if left.midi_pitch is None or right.midi_pitch is None:
            return None
        if abs((left.midi_pitch - first_origin) -
               (right.midi_pitch - second_origin)) > CONTOUR_LIMIT_CENTS / 100.0:
            return None
    return (
        "onsets within one 50 Hz analysis frame",
        "endings within one 50 Hz analysis frame",
        f"initial pitches within {DETUNE_LIMIT_CENTS:g} cents",
        f"held-note pitch contours agree within {CONTOUR_LIMIT_CENTS:g} cents",
    )


def _continuation_evidence(first: NoteSegment,
                           second: NoteSegment) -> tuple[str, ...] | None:
    if first.bank == second.bank and first.channel == second.channel:
        return None
    gap = second.start - first.end
    if not 0 <= gap <= ANALYSIS_FRAME or first.patch != second.patch:
        return None
    return (
        "previous key-off and next key-on within one 50 Hz analysis frame",
        "same complete two-operator patch",
        "different OPL hardware channels",
    )


def candidate_relations(segments: list[NoteSegment]) -> list[VoiceRelation]:
    """Return only high-confidence layer/continuation evidence.

    These are candidates rather than final logical voice assignments.  In
    particular, simultaneous same-patch chord notes can create ambiguous
    continuation edges; later allocation must resolve them globally.
    """
    relations: list[VoiceRelation] = []
    for at, first in enumerate(segments):
        for second in segments[at + 1:]:
            if second.start > max(first.end, first.start) + ANALYSIS_FRAME:
                break
            evidence = _layer_evidence(first, second)
            if evidence is not None:
                relations.append(VoiceRelation(
                    "layer_candidate", first.identifier, second.identifier,
                    evidence,
                ))
            evidence = _continuation_evidence(first, second)
            if evidence is not None:
                relations.append(VoiceRelation(
                    "continuation_candidate", first.identifier,
                    second.identifier, evidence,
                ))
    return relations


def voice_document(writes: Iterable[opl_trace.TimedWrite], banks: int,
                   total_samples: int, clock: int,
                   frequency_divider: int) -> dict:
    segments = reconstruct_segments(
        writes, banks, total_samples, clock, frequency_divider,
    )
    relations = candidate_relations(segments)
    counts = {
        kind: sum(relation.kind == kind for relation in relations)
        for kind in ("layer_candidate", "continuation_candidate")
    }
    return {
        "schema": "jukupoly-opl-voice-evidence-v1",
        "status": "analysis-only; candidates do not alter score allocation",
        "analysis_frame_samples": ANALYSIS_FRAME,
        "detune_limit_cents": DETUNE_LIMIT_CENTS,
        "contour_limit_cents": CONTOUR_LIMIT_CENTS,
        "segments": [asdict(segment) for segment in segments],
        "relation_counts": counts,
        "relations": [asdict(relation) for relation in relations],
    }
