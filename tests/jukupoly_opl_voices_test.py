#!/usr/bin/env python3
"""Synthetic regression for host-only OPL logical-voice evidence."""

from __future__ import annotations

import gzip
import json
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FIRMWARE = ROOT / "spinoffs" / "jukupoly" / "firmware"
TOOLS = ROOT / "spinoffs" / "jukupoly" / "tools"
sys.path.insert(0, str(FIRMWARE))
sys.path.insert(0, str(TOOLS))
sys.path.insert(0, str(ROOT / "tests"))

import import_jukupoly_vgz as vgz  # noqa: E402
import jukupoly_opl_trace_test as trace_fixture  # noqa: E402
import opl_voices  # noqa: E402
import report_opl_voices  # noqa: E402


def writes() -> list[vgz.RegisterWrite]:
    result: list[vgz.RegisterWrite] = []

    def write(sample: int, channel: int, register: int, value: int) -> None:
        result.append(vgz.RegisterWrite(sample, 0, register + channel, value))

    # Give channels 0, 1, and 2 the same complete patch.  Operator addressing
    # is non-linear, so configure the fields which establish patch identity
    # through the channel registers used by this synthetic fixture.
    for channel in range(3):
        write(0, channel, 0xC0, 0x06)
        write(0, channel, 0xA0, 0x34)
        if channel < 2:
            write(0, channel, 0xB0, 0x32)

    # Channels 0 and 1 are a detuned layer with matching live pitch motion.
    write(882, 0, 0xA0, 0x40)
    write(882, 1, 0xA0, 0x40)
    write(1764, 0, 0xB0, 0x12)
    write(1764, 1, 0xB0, 0x12)

    # The same patch moves from hardware channel 0 to channel 2 exactly at
    # key-off; it is continuation evidence, not yet a forced assignment.
    write(1764, 2, 0xA0, 0x80)
    write(1764, 2, 0xB0, 0x32)
    write(2646, 2, 0xB0, 0x12)
    return sorted(result, key=lambda item: item.sample)


def check_segments_and_relations() -> None:
    document = opl_voices.voice_document(
        writes(), 1, 2646, 14_318_180, 288,
    )
    assert document["schema"] == "jukupoly-opl-voice-evidence-v2"
    assert "do not alter score" in document["status"]
    segments = document["segments"]
    assert len(segments) == 3
    first = segments[0]
    assert (first["bank"], first["channel"], first["start"], first["end"]) == (
        0, 0, 0, 1764,
    )
    assert [point["sample"] for point in first["pitches"]] == [0, 882]
    assert first["patch"] == segments[1]["patch"] == segments[2]["patch"]

    relation_keys = {
        (relation["kind"], relation["first"], relation["second"])
        for relation in document["relations"]
    }
    assert ("layer_candidate", 0, 1) in relation_keys
    assert ("continuation_candidate", 0, 2) in relation_keys
    assert document["relation_counts"] == {
        "layer_candidate": 1,
        "continuation_candidate": 2,
    }
    assert len(document["logical_notes"]) == 2
    assert document["logical_notes"][0]["members"] == (0, 1)
    assert document["logical_voices"] == [{"identifier": 0, "notes": (0, 1)}]
    assert len(document["continuation_assignments"]) == 1
    assignment = document["continuation_assignments"][0]
    assert (assignment["previous"], assignment["following"],
            assignment["voice"]) == (0, 1, 0)
    assert assignment["semantic_changes"] == 0
    assert assignment["channel_changes"] == 1
    json.dumps(document, allow_nan=False)


def check_non_layered_chord() -> None:
    segments = [
        opl_voices.NoteSegment(
            identifier, 0, identifier, 0, 1764, "patch", 192, 12, True,
            (opl_voices.PitchPoint(0, 0x200, 4, pitch),),
        )
        for identifier, pitch in enumerate((60.0, 64.0, 67.0))
    ]
    assert not [relation for relation in opl_voices.candidate_relations(segments)
                if relation.kind == "layer_candidate"]

    # A keyed zero-frequency channel is unusual but must still produce strict
    # JSON rather than Python's non-standard Infinity token.
    assert opl_voices.midi_pitch(0, 0, 14_318_180, 288) is None


def check_analysis_does_not_change_score() -> None:
    source_writes = writes()
    info = vgz.VgmInfo(
        version=0x171, clock=14_318_180, frequency_divider=288,
        chip="YMF262 (OPL3)", banks=1, total_samples=2646,
        loop_samples=0, loop_start_sample=None, loop_offset=None, gd3={},
    )
    events, _counts = vgz.key_events(source_writes, info)
    override = {vgz.signature_id(events[0].signature)}
    arguments = (
        info, source_writes, Path("synthetic.vgm"), "compressed", "vgm",
        override, {}, False,
    )
    before = vgz.compile_score(*arguments)
    opl_voices.voice_document(
        source_writes, info.banks, info.total_samples, info.clock,
        info.frequency_divider,
    )
    after = vgz.compile_score(*arguments)
    assert after == before


def logical_note(identifier: int, start: int, end: int, pitch: float,
                 channel: int) -> opl_voices.LogicalNote:
    return opl_voices.LogicalNote(
        identifier=identifier, start=start, end=end, members=(identifier,),
        patches=("patch",), channels=((0, channel),), initial_pitch=pitch,
        final_pitch=pitch, level_8bit=192, attack_rate=12,
        sustained_envelope=True,
    )


def check_global_boundary_matching() -> None:
    # A local first-edge choice would cross these two lines.  The boundary
    # matcher must retain both continuations and minimize their total motion.
    previous = [
        logical_note(0, 0, 882, 60.0, 0),
        logical_note(1, 0, 882, 64.0, 1),
    ]
    following = [
        logical_note(2, 882, 1764, 64.0, 2),
        logical_note(3, 882, 1764, 60.0, 3),
    ]
    matches = opl_voices._minimum_cost_matching(previous, following)
    assert [(old, new) for old, new, _cost in matches] == [(0, 3), (1, 2)]

    voices, assignments = opl_voices.assign_logical_voices(
        previous + following,
    )
    assert [voice.notes for voice in voices] == [(0, 3), (1, 2)]
    assert {(item.previous, item.following) for item in assignments} == {
        (0, 3), (1, 2),
    }

    # Maximum cardinality wins before cost: previous 1 has only one possible
    # successor, so previous 0 must take its alternative instead of greedily
    # consuming the shared edge.
    shared = opl_voices.LogicalNote(
        identifier=4, start=882, end=1764, members=(4,),
        patches=("patch", "second"), channels=((0, 2),),
        initial_pitch=60.0, final_pitch=60.0, level_8bit=192,
        attack_rate=12, sustained_envelope=True,
    )
    alternative = logical_note(5, 882, 1764, 61.0, 3)
    constrained = opl_voices.LogicalNote(
        identifier=6, start=0, end=882, members=(6,),
        patches=("second",), channels=((0, 4),),
        initial_pitch=70.0, final_pitch=70.0, level_8bit=192,
        attack_rate=12, sustained_envelope=True,
    )
    matches = opl_voices._minimum_cost_matching(
        [previous[0], constrained], [shared, alternative],
    )
    assert {(old, new) for old, new, _cost in matches} == {(0, 5), (6, 4)}


def synthetic_melodic_vgm() -> bytes:
    commands = bytearray()
    total_samples = 0
    for f_number in (0x180, 0x1A0, 0x1C0, 0x1E0) * 2:
        commands.extend((0x5A, 0xA0, f_number & 0xFF))
        commands.extend((0x5A, 0xB0, 0x20 | 4 << 2 | f_number >> 8))
        commands.extend((0x61, 100, 0))
        commands.extend((0x5A, 0xB0, 4 << 2 | f_number >> 8))
        commands.extend((0x61, 100, 0))
        total_samples += 200
    commands.append(0x66)
    header = bytearray(0x80)
    header[:4] = b"Vgm "
    trace_fixture.write_u32(header, 0x04, len(header) + len(commands) - 4)
    trace_fixture.write_u32(header, 0x08, 0x171)
    trace_fixture.write_u32(header, 0x18, total_samples)
    trace_fixture.write_u32(header, 0x34, 0x80 - 0x34)
    trace_fixture.write_u32(header, 0x50, 3_579_545)
    return bytes(header + commands)


def check_pack_report_track() -> None:
    result = report_opl_voices.analyze_track(
        "synthetic.vgz", gzip.compress(synthetic_melodic_vgm()),
    )
    assert result["name"] == "synthetic.vgz"
    assert result["segments"] == 8
    assert result["logical_notes"] == 8
    assert result["logical_voices"] == 1
    assert result["provisional_regressed_v1_onsets"] == 0
    assert len(result["assignment_sha256"]) == 64


def check_importer_voice_output_is_non_mutating() -> None:
    with tempfile.TemporaryDirectory(prefix="jukupoly-opl-voice-test.") as name:
        directory = Path(name)
        source = directory / "synthetic.vgz"
        plain = directory / "plain.json"
        analyzed = directory / "analyzed.json"
        voices = directory / "voices.json"
        source.write_bytes(gzip.compress(synthetic_melodic_vgm()))
        subprocess.run(
            [sys.executable, str(FIRMWARE / "import_jukupoly_vgz.py"),
             str(source), str(plain)],
            check=True, stdout=subprocess.DEVNULL,
        )
        subprocess.run(
            [sys.executable, str(FIRMWARE / "import_jukupoly_vgz.py"),
             str(source), str(analyzed), "--opl-voice-output", str(voices)],
            check=True, stdout=subprocess.DEVNULL,
        )
        assert analyzed.read_bytes() == plain.read_bytes()
        evidence = json.loads(voices.read_text())
        allocation = evidence["three_voice_allocation"]
        assert allocation["missed_protected_onsets"] == 0


def check_monotonic_three_voice_allocation() -> None:
    pitches = (48.0, 60.0, 64.0, 72.0)
    notes = [
        opl_voices.LogicalNote(
            identifier=index, start=0, end=1764, members=(index,),
            patches=(f"patch{index}",), channels=((0, index),),
            initial_pitch=pitch, final_pitch=pitch, level_8bit=128 + index,
            attack_rate=8 + index, sustained_envelope=True,
        )
        for index, pitch in enumerate(pitches)
    ]
    voices = [
        opl_voices.LogicalVoice(index, (index,)) for index in range(4)
    ]
    allocation = opl_voices.allocate_three_voices(
        notes, voices, set(range(4)), {(0, 60), (0, 64)},
    )
    assert allocation["source_onsets"] == 4
    assert allocation["protected_onsets"] == 2
    assert allocation["retained_onsets"] == 3
    assert allocation["gained_onsets"] == 1
    assert allocation["missed_protected_onsets"] == 0
    first = allocation["frames"][0]
    selected_midis = {choice["midi_note"] for choice in first["selected"]}
    assert {60, 64} <= selected_midis
    assert len(first["dropped_new_onsets"]) == 1
    assert allocation["ranking"][0] == "protected v1 source onset"


def main() -> int:
    check_segments_and_relations()
    check_non_layered_chord()
    check_analysis_does_not_change_score()
    check_global_boundary_matching()
    check_pack_report_track()
    check_importer_voice_output_is_non_mutating()
    check_monotonic_three_voice_allocation()
    print("JUKUPOLY-OPL-VOICES: PASS keyed-segments live-pitch layers "
          "global-continuation chord-rejection monotonic-three-voice "
          "inspectable-evidence")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
