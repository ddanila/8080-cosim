#!/usr/bin/env python3
"""Synthetic regression for host-only OPL logical-voice evidence."""

from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FIRMWARE = ROOT / "spinoffs" / "jukupoly" / "firmware"
sys.path.insert(0, str(FIRMWARE))

import import_jukupoly_vgz as vgz  # noqa: E402
import opl_voices  # noqa: E402


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
    assert document["schema"] == "jukupoly-opl-voice-evidence-v1"
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
    json.dumps(document, allow_nan=False)


def check_non_layered_chord() -> None:
    segments = [
        opl_voices.NoteSegment(
            identifier, 0, identifier, 0, 1764, "patch",
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


def main() -> int:
    check_segments_and_relations()
    check_non_layered_chord()
    check_analysis_does_not_change_score()
    print("JUKUPOLY-OPL-VOICES: PASS keyed-segments live-pitch layers "
          "cross-channel-continuation chord-rejection inspectable-evidence")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
