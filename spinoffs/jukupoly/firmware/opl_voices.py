"""Host-only reconstruction of OPL note segments and voice relationships.

This module deliberately stops short of changing target-side JukuPoly
allocation.  It turns the exact register timeline into inspectable evidence
and a provisional host-only allocation which can be validated across complete
source packs before it affects a score.
"""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import asdict, dataclass
from typing import Callable, Iterable, NamedTuple

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
    level_8bit: int
    attack_rate: int
    sustained_envelope: bool
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
    level_8bit: int
    attack_rate: int
    sustained_envelope: bool


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


@dataclass(frozen=True)
class AllocationChoice:
    logical_note: int
    logical_voice: int
    midi_note: int | None
    protected_onset: bool
    new_onset: bool
    attack_rate: int
    retained_voice: bool
    pitch_role: str
    level_8bit: int


@dataclass(frozen=True)
class AllocationFrame:
    frame: int
    active_notes: int
    selected: tuple[AllocationChoice, ...]
    dropped_new_onsets: tuple[int, ...]


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


def channel_salience(state: opl_trace.ChannelState) -> tuple[int, int, bool]:
    """Return bounded level, attack rate, and EGT evidence for allocation.

    OPL TL is logarithmic 0.75 dB attenuation.  In FM mode the carrier is the
    audible output; in additive mode both operators contribute.  This is a
    ranking feature, not a claim to reproduce FM timbre.
    """
    carrier = 10.0 ** (-(state.carrier.total_level * 0.75) / 20.0)
    amplitude = carrier
    attack_rate = state.carrier.attack_rate
    sustained = state.carrier.envelope_sustain
    if state.connection:
        amplitude += 10.0 ** (-(state.modulator.total_level * 0.75) / 20.0)
        attack_rate = max(attack_rate, state.modulator.attack_rate)
        sustained = sustained or state.modulator.envelope_sustain
    return (
        round(min(1.0, amplitude) * 255), attack_rate, sustained,
    )


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
    active: dict[
        tuple[int, int],
        tuple[int, int, str, int, int, bool, list[PitchPoint]],
    ] = {}
    segments: list[NoteSegment] = []

    def finish(key: tuple[int, int], end: int) -> None:
        (identifier, start, patch, level, attack_rate,
         sustained, pitches) = active.pop(key)
        segments.append(NoteSegment(
            identifier, key[0], key[1], start, end, patch, level,
            attack_rate, sustained, tuple(pitches),
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
            level, attack_rate, sustained = channel_salience(state)
            active[key] = (
                len(segments) + len(active), write.sample,
                patch_identifier(state), level, attack_rate, sustained,
                [_pitch_point(write.sample, state, clock, frequency_divider)],
            )
        elif event.kind == "key_off":
            if key in active:
                finish(key, write.sample)
        elif key in active:
            point = _pitch_point(write.sample, state, clock, frequency_divider)
            pitches = active[key][6]
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
        segment.patch, segment.level_8bit, segment.attack_rate,
        segment.sustained_envelope, segment.pitches,
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
            level_8bit=min(255, sum(member.level_8bit for member in members)),
            attack_rate=max(member.attack_rate for member in members),
            sustained_envelope=any(
                member.sustained_envelope for member in members
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

    # The following side is bounded by the OPL channel count at one exact key
    # timestamp, so Bellman-Ford keeps residual negative edges transparent.
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


def analysis_frame(sample: int) -> int:
    """Round a VGM sample timestamp to the existing 50 Hz reducer grid."""
    return (sample + ANALYSIS_FRAME // 2) // ANALYSIS_FRAME


def allocate_three_voices(
        notes: list[LogicalNote], voices: list[LogicalVoice],
        melodic_notes: set[int],
        protected_onsets: set[tuple[int, int]] | None = None,
        pitch_mapper: Callable[[int], int] | None = None,
) -> dict:
    """Make an inspectable, monotonic host-only three-voice allocation.

    ``protected_onsets`` is the generic compatibility guard: source onsets
    already retained by the v1 reducer rank ahead of new opportunities.  The
    result may add onset coverage but must report any protected miss.
    """
    protected = protected_onsets or set()
    mapper = pitch_mapper or (lambda note: note)
    voice_for_note = {
        note: voice.identifier for voice in voices for note in voice.notes
    }
    by_identifier = {note.identifier: note for note in notes}
    midi_for_note = {
        note.identifier: (
            None if note.initial_pitch is None else
            mapper(round(note.initial_pitch))
        )
        for note in notes
    }
    starts: dict[int, list[int]] = {}
    ends: dict[int, list[int]] = {}
    source_onsets: set[tuple[int, int]] = set()
    for identifier in sorted(melodic_notes):
        note = by_identifier[identifier]
        start = analysis_frame(note.start)
        end = max(start + 1, analysis_frame(note.end))
        starts.setdefault(start, []).append(identifier)
        ends.setdefault(end, []).append(identifier)
        midi = midi_for_note[identifier]
        if midi is not None:
            source_onsets.add((start, midi))

    active: set[int] = set()
    previous_selected: tuple[int, ...] = ()
    previous_voices: set[int] = set()
    retained_onsets: set[tuple[int, int]] = set()
    decisions: list[AllocationFrame] = []
    if starts or ends:
        last_frame = max((*starts.keys(), *ends.keys()))
    else:
        last_frame = -1

    for frame in range(last_frame + 1):
        for identifier in ends.get(frame, ()):
            active.discard(identifier)
        new_onsets = set(starts.get(frame, ()))
        active.update(new_onsets)
        known_midis = [
            midi_for_note[identifier] for identifier in active
            if midi_for_note[identifier] is not None
        ]
        low = min(known_midis) if known_midis else None
        high = max(known_midis) if known_midis else None

        def role(midi: int | None) -> str:
            if midi is None:
                return "unknown"
            if midi == low and midi == high:
                return "bass+lead"
            if midi == low:
                return "bass"
            if midi == high:
                return "lead"
            return "middle"

        def rank(identifier: int) -> tuple[int, ...]:
            note = by_identifier[identifier]
            midi = midi_for_note[identifier]
            onset = identifier in new_onsets
            protected_now = onset and midi is not None and (
                frame, midi
            ) in protected
            pitch_role = role(midi)
            return (
                int(protected_now),
                int(onset),
                note.attack_rate if onset else 0,
                int(voice_for_note[identifier] in previous_voices),
                int(pitch_role != "middle" and pitch_role != "unknown"),
                note.level_8bit,
                int(note.sustained_envelope),
                analysis_frame(note.end) - frame,
                -identifier,
            )

        # The target emits one pulse voice per distinct pitch.  When several
        # logical notes share it, retain the strongest deterministic owner.
        best_by_midi: dict[int, int] = {}
        for identifier in sorted(active):
            midi = midi_for_note[identifier]
            if midi is None:
                continue
            if midi not in best_by_midi or rank(identifier) > rank(
                    best_by_midi[midi]):
                best_by_midi[midi] = identifier
        selected = tuple(sorted(
            best_by_midi.values(), key=rank, reverse=True,
        )[:3])
        selected_set = set(selected)
        choices: list[AllocationChoice] = []
        for identifier in selected:
            note = by_identifier[identifier]
            midi = midi_for_note[identifier]
            onset = identifier in new_onsets
            protected_now = onset and midi is not None and (
                frame, midi
            ) in protected
            choices.append(AllocationChoice(
                logical_note=identifier,
                logical_voice=voice_for_note[identifier],
                midi_note=midi,
                protected_onset=protected_now,
                new_onset=onset,
                attack_rate=note.attack_rate,
                retained_voice=voice_for_note[identifier] in previous_voices,
                pitch_role=role(midi),
                level_8bit=note.level_8bit,
            ))
            if onset and midi is not None:
                retained_onsets.add((frame, midi))
        dropped = tuple(sorted(new_onsets - selected_set))
        if new_onsets or dropped or selected != previous_selected:
            decisions.append(AllocationFrame(
                frame=frame,
                active_notes=len(active),
                selected=tuple(choices),
                dropped_new_onsets=dropped,
            ))
        previous_selected = selected
        previous_voices = {
            voice_for_note[identifier] for identifier in selected
        }

    protected_source = protected & source_onsets
    missed = protected_source - retained_onsets
    gained = retained_onsets - protected_source
    return {
        "schema": "jukupoly-opl-three-voice-allocation-v1",
        "status": "analysis-only; does not alter score allocation",
        "ranking": [
            "protected v1 source onset",
            "new source onset",
            "onset attack rate",
            "logical-voice continuity",
            "bass or lead pitch role",
            "logarithmic-TL level estimate",
            "sustained-envelope evidence",
            "remaining keyed duration",
            "stable logical-note identifier",
        ],
        "source_onsets": len(source_onsets),
        "protected_onsets": len(protected_source),
        "retained_onsets": len(retained_onsets & source_onsets),
        "gained_onsets": len(gained & source_onsets),
        "missed_protected_onsets": len(missed),
        "source_onset_keys": sorted(source_onsets),
        "retained_onset_keys": sorted(retained_onsets & source_onsets),
        "missed_protected_keys": sorted(missed),
        "frames": [asdict(decision) for decision in decisions],
    }


def melodic_logical_notes(
        segments: list[NoteSegment], notes: list[LogicalNote],
        melodic_keys: set[tuple[int, int, int]],
) -> set[int]:
    """Map importer-classified (start, bank, channel) keys through layers."""
    melodic_segments = {
        segment.identifier for segment in segments
        if (segment.start, segment.bank, segment.channel) in melodic_keys
    }
    return {
        note.identifier for note in notes
        if any(member in melodic_segments for member in note.members)
    }


def voice_document(writes: Iterable[opl_trace.TimedWrite], banks: int,
                   total_samples: int, clock: int,
                   frequency_divider: int,
                   melodic_keys: set[tuple[int, int, int]] | None = None,
                   protected_onsets: set[tuple[int, int]] | None = None,
                   pitch_mapper: Callable[[int], int] | None = None) -> dict:
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
    document = {
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
    if melodic_keys is not None:
        melodic_notes = melodic_logical_notes(
            segments, logical_notes, melodic_keys,
        )
        document["three_voice_allocation"] = allocate_three_voices(
            logical_notes, logical_voices, melodic_notes,
            protected_onsets, pitch_mapper,
        )
    return document
