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
from typing import Iterable, NamedTuple

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


@dataclass(frozen=True)
class LogicalNote:
    identifier: int
    start: int
    end: int
    members: tuple[int, ...]
    patches: tuple[str, ...]
    channels: tuple[tuple[int, int], ...]
    initial_pitch: float | None
    final_pitch: float | None


@dataclass(frozen=True)
class ContinuationAssignment:
    previous: int
    following: int
    voice: int
    semantic_changes: int
    channel_changes: int
    unknown_pitch: int
    pitch_distance_cents: int
    gap_samples: int
    evidence: tuple[str, ...]


@dataclass(frozen=True)
class LogicalVoice:
    identifier: int
    notes: tuple[int, ...]


class _MatchCost(NamedTuple):
    semantic_changes: int
    channel_changes: int
    unknown_pitch: int
    pitch_distance_cents: int
    gap_samples: int


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
    if max(first.start, second.start) >= min(first.end, second.end):
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
        "keyed spans overlap",
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


def _mean(values: Iterable[float | None]) -> float | None:
    finite = [value for value in values
              if value is not None and math.isfinite(value)]
    return sum(finite) / len(finite) if finite else None


def group_layers(segments: list[NoteSegment],
                 relations: list[VoiceRelation]) -> list[LogicalNote]:
    """Collapse only the explicitly evidenced same-pitch layer components."""
    parents = list(range(len(segments)))

    def root(identifier: int) -> int:
        while parents[identifier] != identifier:
            parents[identifier] = parents[parents[identifier]]
            identifier = parents[identifier]
        return identifier

    def join(first: int, second: int) -> None:
        left, right = root(first), root(second)
        if left != right:
            parents[max(left, right)] = min(left, right)

    for relation in relations:
        if relation.kind == "layer_candidate":
            join(relation.first, relation.second)

    components: dict[int, list[NoteSegment]] = {}
    for segment in segments:
        components.setdefault(root(segment.identifier), []).append(segment)
    ordered = sorted(components.values(), key=lambda members: (
        min(member.start for member in members),
        max(member.end for member in members),
        min(member.identifier for member in members),
    ))
    notes: list[LogicalNote] = []
    for identifier, members in enumerate(ordered):
        members.sort(key=lambda member: member.identifier)
        notes.append(LogicalNote(
            identifier=identifier,
            start=min(member.start for member in members),
            end=max(member.end for member in members),
            members=tuple(member.identifier for member in members),
            patches=tuple(sorted({member.patch for member in members})),
            channels=tuple(sorted({
                (member.bank, member.channel) for member in members
            })),
            initial_pitch=_mean(
                member.pitches[0].midi_pitch for member in members
                if member.pitches
            ),
            final_pitch=_mean(
                member.pitches[-1].midi_pitch for member in members
                if member.pitches
            ),
        ))
    return notes


def _match_cost(previous: LogicalNote,
                following: LogicalNote) -> _MatchCost | None:
    gap = following.start - previous.end
    if not 0 <= gap <= ANALYSIS_FRAME:
        return None
    same_patch = not set(previous.patches).isdisjoint(following.patches)
    same_channel = not set(previous.channels).isdisjoint(following.channels)
    if not same_patch and not same_channel:
        return None
    unknown_pitch = int(
        previous.final_pitch is None or following.initial_pitch is None
    )
    if unknown_pitch:
        pitch_distance = 0
    else:
        assert previous.final_pitch is not None
        assert following.initial_pitch is not None
        pitch_distance = round(abs(
            previous.final_pitch - following.initial_pitch
        ) * 100)
    return _MatchCost(
        semantic_changes=int(not same_patch),
        channel_changes=int(not same_channel),
        unknown_pitch=unknown_pitch,
        pitch_distance_cents=pitch_distance,
        gap_samples=gap,
    )


def _add_cost(first: _MatchCost, second: _MatchCost) -> _MatchCost:
    return _MatchCost(*(left + right for left, right in zip(first, second)))


def _negate_cost(cost: _MatchCost) -> _MatchCost:
    return _MatchCost(*(-value for value in cost))


@dataclass
class _FlowEdge:
    destination: int
    reverse: int
    capacity: int
    cost: _MatchCost
    match: tuple[int, int] | None = None


def _minimum_cost_matching(
        previous: list[LogicalNote], following: list[LogicalNote],
) -> list[tuple[int, int, _MatchCost]]:
    """Maximum-cardinality, lexicographically minimum-cost bipartite match."""
    source = 0
    previous_base = 1
    following_base = previous_base + len(previous)
    sink = following_base + len(following)
    graph: list[list[_FlowEdge]] = [[] for _ in range(sink + 1)]
    zero = _MatchCost(0, 0, 0, 0, 0)

    def edge(start: int, end: int, cost: _MatchCost,
             match: tuple[int, int] | None = None) -> None:
        graph[start].append(_FlowEdge(
            end, len(graph[end]), 1, cost, match,
        ))
        graph[end].append(_FlowEdge(
            start, len(graph[start]) - 1, 0, _negate_cost(cost), None,
        ))

    for index in range(len(previous)):
        edge(source, previous_base + index, zero)
    for index in range(len(following)):
        edge(following_base + index, sink, zero)
    for left, old in enumerate(previous):
        for right, new in enumerate(following):
            cost = _match_cost(old, new)
            if cost is not None:
                edge(previous_base + left, following_base + right, cost,
                     (old.identifier, new.identifier))

    # The graph is tiny (at most the OPL channel count at one key timestamp),
    # so Bellman-Ford keeps residual negative edges correct and transparent.
    while True:
        distance: list[_MatchCost | None] = [None] * len(graph)
        predecessor: list[tuple[int, int] | None] = [None] * len(graph)
        distance[source] = zero
        for _pass in range(len(graph) - 1):
            changed = False
            for node, edges in enumerate(graph):
                if distance[node] is None:
                    continue
                for index, item in enumerate(edges):
                    if not item.capacity:
                        continue
                    candidate = _add_cost(distance[node], item.cost)
                    if (distance[item.destination] is None or
                            candidate < distance[item.destination]):
                        distance[item.destination] = candidate
                        predecessor[item.destination] = (node, index)
                        changed = True
            if not changed:
                break
        if predecessor[sink] is None:
            break
        node = sink
        while node != source:
            link = predecessor[node]
            assert link is not None
            origin, index = link
            item = graph[origin][index]
            item.capacity -= 1
            graph[node][item.reverse].capacity += 1
            node = origin

    result: list[tuple[int, int, _MatchCost]] = []
    for left, old in enumerate(previous):
        for item in graph[previous_base + left]:
            if item.match is not None and item.capacity == 0:
                new = following[item.destination - following_base]
                cost = _match_cost(old, new)
                assert cost is not None
                result.append((old.identifier, new.identifier, cost))
    return sorted(result)


def assign_logical_voices(notes: list[LogicalNote]) -> tuple[
        list[LogicalVoice], list[ContinuationAssignment]]:
    """Build deterministic chains using global one-to-one boundary matching."""
    by_start: dict[int, list[LogicalNote]] = {}
    for note in notes:
        by_start.setdefault(note.start, []).append(note)
    available: list[LogicalNote] = []
    voice_for_note: dict[int, int] = {}
    voice_notes: list[list[int]] = []
    assignments: list[ContinuationAssignment] = []

    for sample in sorted(by_start):
        following = sorted(by_start[sample], key=lambda note: note.identifier)
        available = [note for note in available
                     if note.end >= sample - ANALYSIS_FRAME]
        eligible = [note for note in available if note.end <= sample]
        matches = _minimum_cost_matching(eligible, following)
        used_previous = {previous for previous, _new, _cost in matches}
        match_for_new = {
            new: (previous, cost) for previous, new, cost in matches
        }
        for note in following:
            if note.identifier in match_for_new:
                previous, cost = match_for_new[note.identifier]
                voice = voice_for_note[previous]
                same_patch = cost.semantic_changes == 0
                same_channel = cost.channel_changes == 0
                evidence = [
                    "global maximum-cardinality one-to-one boundary match",
                    "gap is no more than one 50 Hz analysis frame",
                    "same complete patch" if same_patch else
                    "same OPL hardware channel",
                ]
                if cost.unknown_pitch:
                    evidence.append("pitch comparison unavailable")
                else:
                    evidence.append(
                        f"assigned pitch motion {cost.pitch_distance_cents} cents"
                    )
                assignments.append(ContinuationAssignment(
                    previous=previous,
                    following=note.identifier,
                    voice=voice,
                    semantic_changes=cost.semantic_changes,
                    channel_changes=cost.channel_changes,
                    unknown_pitch=cost.unknown_pitch,
                    pitch_distance_cents=cost.pitch_distance_cents,
                    gap_samples=cost.gap_samples,
                    evidence=tuple(evidence),
                ))
            else:
                voice = len(voice_notes)
                voice_notes.append([])
            voice_for_note[note.identifier] = voice
            voice_notes[voice].append(note.identifier)
        available = [note for note in available
                     if note.identifier not in used_previous]
        available.extend(following)

    voices = [
        LogicalVoice(identifier, tuple(members))
        for identifier, members in enumerate(voice_notes)
    ]
    return voices, assignments


def voice_document(writes: Iterable[opl_trace.TimedWrite], banks: int,
                   total_samples: int, clock: int,
                   frequency_divider: int) -> dict:
    segments = reconstruct_segments(
        writes, banks, total_samples, clock, frequency_divider,
    )
    relations = candidate_relations(segments)
    logical_notes = group_layers(segments, relations)
    logical_voices, assignments = assign_logical_voices(logical_notes)
    counts = {
        kind: sum(relation.kind == kind for relation in relations)
        for kind in ("layer_candidate", "continuation_candidate")
    }
    return {
        "schema": "jukupoly-opl-voice-evidence-v2",
        "status": "analysis-only; candidates do not alter score allocation",
        "analysis_frame_samples": ANALYSIS_FRAME,
        "detune_limit_cents": DETUNE_LIMIT_CENTS,
        "contour_limit_cents": CONTOUR_LIMIT_CENTS,
        "segments": [asdict(segment) for segment in segments],
        "relation_counts": counts,
        "relations": [asdict(relation) for relation in relations],
        "logical_notes": [asdict(note) for note in logical_notes],
        "logical_voices": [asdict(voice) for voice in logical_voices],
        "continuation_assignments": [
            asdict(assignment) for assignment in assignments
        ],
    }
