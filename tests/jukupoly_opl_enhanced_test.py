#!/usr/bin/env python3
"""Synthetic regression for real-song JPS v2 OPL-envelope reduction."""

from __future__ import annotations

import copy
import dataclasses
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FIRMWARE = ROOT / "spinoffs" / "jukupoly" / "firmware"
sys.path.insert(0, str(FIRMWARE))

import opl_enhanced  # noqa: E402
import opl_envelope  # noqa: E402
import opl_oracle  # noqa: E402
import opl_voices  # noqa: E402
import build_jukupoly  # noqa: E402
import import_jukupoly_vgz as vgz  # noqa: E402


def allocation() -> dict:
    def choice(note: int, midi: int) -> dict:
        return {
            "logical_note": note, "logical_voice": 7, "midi_note": midi,
            "protected_onset": False, "new_onset": True, "attack_rate": 8,
            "retained_voice": note != 0, "pitch_role": "bass+lead",
            "level_8bit": 128,
        }
    return {
        "schema": "jukupoly-opl-three-voice-allocation-v1",
        "source_onsets": 2, "protected_onsets": 1,
        "retained_onsets": 2, "gained_onsets": 1,
        "missed_protected_onsets": 0,
        "frames": [
            {"frame": 0, "selected": [choice(0, 42)]},
            {"frame": 2, "selected": [choice(1, 43)]},
            {"frame": 4, "selected": []},
        ],
    }


def envelope(peak: int) -> opl_envelope.EnvelopeFit:
    predicted = opl_envelope.simulate_envelope(
        6, key_off_frame=4, peak_level=peak, sustain_level=peak,
        attack_period_frames=0, decay_period_frames=0,
        release_period_frames=1, sustain_while_keyed=True,
    )
    return opl_envelope.EnvelopeFit(
        peak, peak, 0, 0, 1, True, predicted, 0, 0, 0,
    )


def check_timeline_and_rows() -> None:
    timeline = opl_enhanced.selected_timeline(allocation(), 6)
    assert [tuple(item.logical_note for item in frame) for frame in timeline] == [
        (0,), (0,), (1,), (1,), (), (),
    ]
    first = opl_enhanced.assign_target_channels(timeline[0], (None,) * 3)
    second = opl_enhanced.assign_target_channels(timeline[2], first)
    assert first[0] is not None and first[0].logical_note == 0
    assert second[0] is not None and second[0].logical_note == 1

    notes = [
        opl_voices.LogicalNote(
            identifier, identifier * 1764, (identifier + 1) * 1764,
            (identifier,), (f"patch{identifier}",), ((0, identifier),),
            42.0 + identifier, 42.0 + identifier, 128, 8, True,
        )
        for identifier in range(2)
    ]
    v1 = {
        "schema": "jukupoly-song-v1", "title": "Synthetic (OPL2/VGZ JukuPoly reduction)",
        "conversion": {"duration_frames": 6, "duration_seconds": 0.12},
        "rows": [
            {"frames": 1},
            {"frames": 5, "percussion": {
                "sample": 1, "volume": 1, "filter": 7, "offset": 1,
            }},
        ],
    }
    score = opl_enhanced.compile_enhanced_score(
        v1, notes, allocation(), {0: envelope(12), 1: envelope(9)}, 6,
        {"selected_logical_notes": 2},
    )
    assert score["schema"] == "jukupoly-song-v2"
    assert score["frame_samples"] == 143
    starts = []
    frame = 0
    for row in score["rows"]:
        if "tone1" in row:
            starts.append((frame, row["tone1"]["note"]))
        frame += row["frames"]
    assert starts == [(0, "F#2"), (2, "G2"), (4, "---")]
    assert score["rows"][1]["percussion"]["sample"] == 1

    second_packet = envelope(7).packet()
    articulated = opl_enhanced.compile_enhanced_score(
        v1, notes, allocation(), {0: envelope(12), 1: envelope(9)}, 6,
        {
            "selected_logical_notes": 2,
            "notes": [{
                "logical_note": 0, "selected_frame": 0,
                "articulation_packets": [{
                    "frame_offset": 1, "packet": second_packet,
                }],
                "tremolo_analysis": {"emitted_depth_levels": 0},
            }],
        },
    )
    assert articulated["rows"][1]["tone1"] == {
        "note": "F#2", "opl_envelope": second_packet,
    }
    assert "rearticulation" in articulated["title"]

    detuned = opl_enhanced.compile_enhanced_score(
        v1, notes, allocation(), {0: envelope(12), 1: envelope(9)}, 6,
        {
            "selected_logical_notes": 2,
            "notes": [
                {
                    "logical_note": 0, "selected_frame": 0,
                    "articulation_packets": [{
                        "frame_offset": 1,
                        "packet": envelope(3).packet(),
                    }],
                    "tremolo_analysis": {"emitted_depth_levels": 0},
                },
                {
                    "logical_note": 1, "selected_frame": 2,
                    "articulation_packets": [{
                        "frame_offset": 1,
                        "packet": envelope(8).packet(),
                    }],
                    "tremolo_analysis": {"emitted_depth_levels": 0},
                },
            ],
            "detuned_layer_analysis": {"episodes": [{
                "logical_note": 0, "start_frame": 0, "end_frame": 2,
                "members": [
                    {"segment": 10, "phase_step": 777,
                     "packet": envelope(7).packet(),
                     "articulation_packets": [{
                         "frame_offset": 1,
                         "packet": envelope(5).packet(),
                     }]},
                    {"segment": 11, "phase_step": 785,
                     "packet": envelope(6).packet()},
                ],
            }]},
        },
    )
    assert detuned["rows"][0]["tone1"] == {
        "phase_step": 777, "opl_envelope": envelope(7).packet(),
    }
    assert detuned["rows"][0]["tone2"] == {
        "phase_step": 785, "opl_envelope": envelope(6).packet(),
    }
    detuned_frame = 0
    detuned_events = {}
    for row in detuned["rows"]:
        detuned_events[detuned_frame] = row
        detuned_frame += row["frames"]
    assert detuned_events[1]["tone1"] == {
        "phase_step": 777, "opl_envelope": envelope(5).packet(),
    }
    assert detuned_events[2]["tone2"] == {"note": "---"}
    assert detuned_events[3]["tone1"] == {
        "note": "G2", "opl_envelope": envelope(8).packet(),
    }
    assert detuned["conversion"]["enhanced_detuned_layers"][
        "member_rearticulation_packets"
    ] == 1
    assert "detuned-layers" in detuned["title"]
    assert "detuned-layer M7" in detuned["conversion"][
        "enhanced_limitations"
    ]

    tremolo_score = opl_enhanced.compile_enhanced_score(
        v1, notes, allocation(), {0: envelope(12), 1: envelope(9)}, 6,
        {
            "selected_logical_notes": 2,
            "notes": [{
                "logical_note": 0,
                "tremolo_analysis": {"emitted_depth_levels": 2},
            }],
        },
    )
    assert tremolo_score["frame_samples"] == 140
    assert tremolo_score["sample_rate_hz"] == 6970
    assert tremolo_score["rows"][0]["tone1"]["opl_tremolo_depth"] == 2
    assert "opl_tremolo_depth" not in tremolo_score["rows"][2]["tone1"]
    calibrated = opl_enhanced.compile_enhanced_score(
        v1, notes, allocation(), {0: envelope(12), 1: envelope(9)}, 6,
        {
            "notes": [{
                "logical_note": 0,
                "tremolo_analysis": {"emitted_depth_levels": 2},
            }],
        },
        target_sample_rate=7100, frame_samples=143,
    )
    assert calibrated["sample_rate_hz"] == 7100
    assert calibrated["frame_samples"] == 143

    pitch_segments = [
        opl_voices.NoteSegment(
            0, 0, 0, 0, 2 * 882, "patch0", 128, 8, True,
            (
                opl_voices.PitchPoint(0, 0x200, 4, 42.0),
                opl_voices.PitchPoint(882, 0x208, 4, 42.25),
            ),
        ),
        opl_voices.NoteSegment(
            1, 0, 1, 2 * 882, 4 * 882, "patch1", 128, 8, True,
            (opl_voices.PitchPoint(2 * 882, 0x210, 4, 43.0),),
        ),
    ]
    pitch_score = opl_enhanced.compile_enhanced_score(
        v1, notes, allocation(), {0: envelope(12), 1: envelope(9)}, 6,
        {"selected_logical_notes": 2}, segments=pitch_segments,
        enable_held_pitch=True,
    )
    events = []
    frame = 0
    for row in pitch_score["rows"]:
        if "tone1" in row:
            events.append((frame, row["tone1"]))
        frame += row["frames"]
    assert [frame for frame, _event in events] == [0, 1, 2, 4]
    assert "phase_step" in events[0][1] and "note" not in events[0][1]
    assert events[1][1]["legato"] is True
    assert events[1][1]["phase_step"] != events[0][1]["phase_step"]
    assert "legato" not in events[2][1]
    assert pitch_score["conversion"]["enhanced_held_pitch"] == {
        "enabled": True,
        "emitted_legato_packets": 1,
        "phase_step_generation_hz": 7170,
        "policy": (
            "50 Hz source pitch points quantized to target phase steps; "
            "emit only changes while the same logical note retains its "
            "target channel"
        ),
    }
    articulated_pitch = opl_enhanced.compile_enhanced_score(
        v1, notes, allocation(), {0: envelope(12), 1: envelope(9)}, 6,
        {
            "selected_logical_notes": 2,
            "notes": [{
                "logical_note": 0, "selected_frame": 0,
                "articulation_packets": [{
                    "frame_offset": 1, "packet": envelope(7).packet(),
                }],
                "tremolo_analysis": {"emitted_depth_levels": 0},
            }],
        },
        segments=pitch_segments, enable_held_pitch=True,
    )
    articulated_pitch_event = articulated_pitch["rows"][1]["tone1"]
    assert articulated_pitch_event["phase_step"] != (
        articulated_pitch["rows"][0]["tone1"]["phase_step"]
    )
    assert "legato" not in articulated_pitch_event
    assert articulated_pitch_event["opl_envelope"] == envelope(7).packet()
    pitch_generated, pitch_metadata = build_jukupoly.compile_song(pitch_score)
    pitch_jps = build_jukupoly.assemble_song_file(
        pitch_generated, pitch_metadata,
    )
    assert pitch_jps[7] == build_jukupoly.JPS2_ENVELOPE_CAPABILITY
    assert not pitch_metadata["enhanced_vibrato"]

    calibrated_pitch = opl_enhanced.compile_enhanced_score(
        v1, notes, allocation(), {0: envelope(12), 1: envelope(9)}, 6,
        {"selected_logical_notes": 2}, segments=pitch_segments,
        enable_held_pitch=True, target_sample_rate=6850, frame_samples=137,
    )
    calibrated_step = calibrated_pitch["rows"][0]["tone1"]["phase_step"]
    source_frequency = 440.0 * 2.0 ** ((42.0 - 69.0) / 12.0)
    assert calibrated_step == round(source_frequency * 65536.0 / 6850)
    assert calibrated_step > events[0][1]["phase_step"]
    assert calibrated_pitch["conversion"]["enhanced_held_pitch"][
        "phase_step_generation_hz"
    ] == calibrated_pitch["sample_rate_hz"]

    try:
        opl_enhanced.compile_enhanced_score(
            v1, notes, allocation(), {0: envelope(12), 1: envelope(9)}, 6,
            {"selected_logical_notes": 2}, enable_held_pitch=True,
        )
    except ValueError as exc:
        assert "requires source segments" in str(exc)
    else:
        raise AssertionError("held pitch accepted without source segments")


def check_probe_fit() -> None:
    segment = opl_voices.NoteSegment(
        0, 0, 0, 0, 3 * 882, "patch", 128, 8, True,
        (opl_voices.PitchPoint(0, 0x200, 4, 42.0),),
    )
    note = opl_voices.LogicalNote(
        0, 0, 3 * 882, (0,), ("patch",), ((0, 0),), 42.0, 42.0,
        128, 8, True,
    )
    levels = (511, 32, 0, 32, 64, 128)
    probes = []
    for frame, attenuation in enumerate(levels):
        probe = opl_oracle.OracleProbe(
            sample=frame * 882, f_number=0x200, block=4, key=frame < 3,
            modulator_attenuation=0, carrier_attenuation=0,
            modulator_output_attenuation=511,
            carrier_output_attenuation=attenuation, connection=0,
            modulator_am=False, carrier_am=False,
            modulator_vibrato=False, carrier_vibrato=False,
            modulator_vibrato_f_number=0x200,
            carrier_vibrato_f_number=0x200,
            modulator_stage=0, carrier_stage=0, vibrato_phase=0,
            tremolo_phase=0, tremolo_value=0,
        )
        probes.append(opl_oracle.OracleChannelProbe(0, probe))
    probes.append(opl_oracle.OracleChannelProbe(
        0, opl_oracle.OracleProbe(
            sample=6 * 882 + 17, f_number=0x200, block=4, key=False,
            modulator_attenuation=0, carrier_attenuation=0,
            modulator_output_attenuation=511,
            carrier_output_attenuation=511, connection=0,
            modulator_am=False, carrier_am=False,
            modulator_vibrato=False, carrier_vibrato=False,
            modulator_vibrato_f_number=0x200,
            carrier_vibrato_f_number=0x200,
            modulator_stage=0, carrier_stage=0, vibrato_phase=0,
            tremolo_phase=0, tremolo_value=0,
        ),
    ))
    fits, report = opl_enhanced.fit_selected_envelopes(
        [segment], [note], {
            "schema": "jukupoly-opl-three-voice-allocation-v1",
            "frames": [{"frame": 0, "selected": [{
                "logical_note": 0, "logical_voice": 0, "midi_note": 42,
            }]}],
        }, probes, 6,
    )
    assert set(fits) == {0}
    assert report["selected_logical_notes"] == 1
    assert report["target_shape_fit"]["enabled"] is False
    assert 1 <= fits[0].peak_level <= 15

    # The two guarded host features must compose.  Marking the carrier as a
    # direct AM path forces the joint envelope+tremolo fitter to run even
    # though zero oracle AM attenuation correctly results in no emitted LFO.
    am_probes = [
        opl_oracle.OracleChannelProbe(
            item.channel, dataclasses.replace(
                item.probe, carrier_am=True,
            ),
        )
        for item in probes
    ]
    _combined_fits, combined_report = opl_enhanced.fit_selected_envelopes(
        [segment], [note], {
            "schema": "jukupoly-opl-three-voice-allocation-v1",
            "frames": [{"frame": 0, "selected": [{
                "logical_note": 0, "logical_voice": 0, "midi_note": 42,
            }]}],
        }, am_probes, 6,
        enable_tremolo=True, enable_target_shape_fit=True,
    )
    assert combined_report["target_shape_fit"]["enabled"] is True
    assert combined_report["tremolo_analysis"]["enabled"] is True

    layered_segments = [
        opl_voices.NoteSegment(
            identifier, 0, identifier, 0, 3 * 882,
            f"layer{identifier}", 128, 8, True,
            (opl_voices.PitchPoint(
                0, 0x200 + identifier, 4,
                42.0 if identifier == 4 else 42.0 + identifier * 0.2,
            ),),
        )
        for identifier in range(5)
    ]
    layered_note = opl_voices.LogicalNote(
        0, 0, 3 * 882, (0, 1, 4), ("layer0", "layer1", "layer4"),
        ((0, 0), (0, 1), (0, 4)), 42.0, 42.0, 128, 8, True,
    )
    layered_probes = []
    for channel in range(5):
        attenuation_trace = (
            (511, 511, 511, 511, 511, 511)
            if channel == 4 else (32, 32, 32, 64, 128, 511)
        )
        for frame, attenuation in enumerate(attenuation_trace):
            layered_probes.append(opl_oracle.OracleChannelProbe(
                channel,
                opl_oracle.OracleProbe(
                    sample=frame * 882, f_number=0x200 + channel,
                    block=4, key=frame < 3,
                    modulator_attenuation=0, carrier_attenuation=0,
                    modulator_output_attenuation=511,
                    carrier_output_attenuation=attenuation, connection=0,
                    modulator_am=False, carrier_am=False,
                    modulator_vibrato=False, carrier_vibrato=False,
                    modulator_vibrato_f_number=0x200 + channel,
                    carrier_vibrato_f_number=0x200 + channel,
                    modulator_stage=0, carrier_stage=0, vibrato_phase=0,
                    tremolo_phase=0, tremolo_value=0,
                ),
            ))
    _layered_fits, layered_report = opl_enhanced.fit_selected_envelopes(
        layered_segments, [layered_note], {
            "schema": "jukupoly-opl-three-voice-allocation-v1",
            "frames": [
                {"frame": 0, "selected": [{
                    "logical_note": 0, "logical_voice": 0,
                    "midi_note": 42,
                }]},
                {"frame": 3, "selected": []},
            ],
        }, layered_probes, 6, enable_detuned_layers=True,
    )
    detuned = layered_report["detuned_layer_analysis"]
    assert detuned["logical_notes"] == 1
    assert detuned["extra_voices"] == 1
    assert [
        member["segment"] for member in detuned["episodes"][0]["members"]
    ] == [0, 1]
    by_segment = {
        member["segment"]: member
        for member in detuned["episodes"][0]["members"]
    }
    assert by_segment[0]["source_segments"] == [0, 4]
    assert by_segment[0]["source_channels"] == [0, 4]
    assert detuned["source_members_merged"] == 3
    assert len({
        member["phase_step"]
        for member in detuned["episodes"][0]["members"]
    }) == 2

    second_layered_note = opl_voices.LogicalNote(
        1, 0, 3 * 882, (2, 3), ("layer2", "layer3"),
        ((0, 2), (0, 3)), 42.4, 42.4, 128, 8, True,
    )
    _overlap_fits, overlap_report = opl_enhanced.fit_selected_envelopes(
        layered_segments, [layered_note, second_layered_note], {
            "schema": "jukupoly-opl-three-voice-allocation-v1",
            "frames": [
                {"frame": 0, "selected": [
                    {"logical_note": 0, "logical_voice": 0,
                     "midi_note": 42},
                    {"logical_note": 1, "logical_voice": 1,
                     "midi_note": 47},
                ]},
                {"frame": 3, "selected": []},
            ],
        }, layered_probes, 6, enable_detuned_layers=True,
    )
    overlap = overlap_report["detuned_layer_analysis"]
    assert overlap["logical_notes"] == 1
    assert overlap["extra_voices"] == 1
    assert overlap["rejections"]["overlapping_episode_capacity"] == 1


def check_direct_vibrato_score() -> None:
    segment = opl_voices.NoteSegment(
        0, 0, 0, 0, 4 * 882, "patch", 128, 8, True,
        (opl_voices.PitchPoint(0, 0x200, 4, 42.0),),
    )
    note = opl_voices.LogicalNote(
        0, 0, 4 * 882, (0,), ("patch",), ((0, 0),), 42.0, 42.0,
        128, 8, True,
    )
    selected = {
        "schema": "jukupoly-opl-three-voice-allocation-v1",
        "source_onsets": 1, "protected_onsets": 1,
        "retained_onsets": 1, "gained_onsets": 0,
        "missed_protected_onsets": 0,
        "frames": [
            {"frame": 0, "selected": [{
                "logical_note": 0, "logical_voice": 0, "midi_note": 42,
            }]},
            {"frame": 4, "selected": []},
        ],
    }
    carrier_vibrato = (True, True, False, True, False, False)
    modulator_vibrato = (False, False, True, False, False, False)
    probes = []
    for frame in range(6):
        delta = (0, 2, 4, 2, 0, -2)[frame]
        probe = opl_oracle.OracleProbe(
            sample=frame * 882, f_number=0x200, block=4, key=frame < 4,
            modulator_attenuation=0, carrier_attenuation=0,
            modulator_output_attenuation=511,
            carrier_output_attenuation=0, connection=0,
            modulator_am=False, carrier_am=False,
            modulator_vibrato=modulator_vibrato[frame],
            carrier_vibrato=carrier_vibrato[frame],
            modulator_vibrato_f_number=(
                0x200 + delta if modulator_vibrato[frame] else 0x200
            ),
            carrier_vibrato_f_number=(
                0x200 + delta if carrier_vibrato[frame] else 0x200
            ),
            modulator_stage=0, carrier_stage=0, vibrato_phase=frame,
            tremolo_phase=0, tremolo_value=0,
        )
        probes.append(opl_oracle.OracleChannelProbe(0, probe))
    v1 = {
        "schema": "jukupoly-song-v1",
        "title": "Synthetic (OPL2/VGZ JukuPoly reduction)",
        "conversion": {"duration_frames": 6, "duration_seconds": 0.12},
        "rows": [{"frames": 6}],
    }
    depths = (False, True, True, True, True, True)
    score = opl_enhanced.compile_enhanced_score(
        v1, [note], selected, {0: envelope(12)}, 6,
        {"selected_logical_notes": 1},
        target_sample_rate=6530, frame_samples=131,
        segments=[segment], channel_probes=probes,
        vibrato_depths=depths, enable_vibrato=True,
    )
    events = []
    frame = 0
    for row in score["rows"]:
        if "tone1" in row:
            events.append((frame, row["tone1"]))
        frame += row["frames"]
    assert [item[0] for item in events] == [0, 1, 2, 3, 4]
    assert events[0][1]["opl_vibrato"] == {
        "mode": "shallow", "peak_step_delta": 4,
    }
    assert events[1][1]["opl_vibrato"] == {
        "mode": "deep", "peak_step_delta": 7,
    }
    assert events[1][1]["legato"] is True
    assert "opl_vibrato" not in events[2][1]
    assert events[2][1]["legato"] is True
    assert events[3][1]["opl_vibrato"] == {
        "mode": "deep", "peak_step_delta": 7,
    }
    assert events[4][1] == {"note": "---"}

    articulated_score = opl_enhanced.compile_enhanced_score(
        v1, [note], selected, {0: envelope(12)}, 6,
        {
            "selected_logical_notes": 1,
            "notes": [{
                "logical_note": 0, "selected_frame": 0,
                "articulation_packets": [{
                    "frame_offset": 1, "packet": envelope(7).packet(),
                }],
                "tremolo_analysis": {"emitted_depth_levels": 0},
            }],
        },
        target_sample_rate=6530, frame_samples=131,
        segments=[segment], channel_probes=probes,
        vibrato_depths=depths, enable_vibrato=True,
    )
    articulated_event = articulated_score["rows"][1]["tone1"]
    assert "legato" not in articulated_event
    assert articulated_event["opl_vibrato"] == {
        "mode": "deep", "peak_step_delta": 7,
    }
    analysis = score["conversion"]["enhanced_vibrato"]
    assert analysis["direct_channel_frames"] == 3
    assert analysis["packets_with_vibrato"] == 3
    assert analysis["held_setting_updates"] == 3
    assert analysis["held_disable_updates"] == 1
    assert analysis["frame_decisions"] == {
        "direct": 3, "mixed_or_indirect": 1,
    }
    generated, metadata = build_jukupoly.compile_song(score)
    payload = build_jukupoly.assemble_song_file(generated, metadata)
    assert payload[7] == (
        build_jukupoly.JPS2_ENVELOPE_CAPABILITY |
        build_jukupoly.JPS2_PITCH_CAPABILITY
    )
    assert metadata["enhanced_vibrato"]

    writes = [
        vgz.RegisterWrite(0, 0, 0xBD, 0),
        vgz.RegisterWrite(882, 0, 0xBD, 0x40),
        vgz.RegisterWrite(1764, 0, 0xBD, 0),
    ]
    assert opl_enhanced.vibrato_depth_timeline(writes, 4) == (
        False, True, False, False,
    )
    try:
        opl_enhanced.compile_enhanced_score(
            v1, [note], selected, {0: envelope(12)}, 6,
            {"selected_logical_notes": 1}, segments=[segment],
            channel_probes=probes, vibrato_depths=depths,
            enable_vibrato=True,
        )
    except ValueError as exc:
        assert "requires measured" in str(exc)
    else:
        raise AssertionError("runtime vibrato accepted without calibration")


def check_timing_recalibration() -> None:
    score = {
        "schema": "jukupoly-song-v2",
        "sample_rate_hz": 7100,
        "frame_samples": 142,
        "rows": [{
            "frames": 2,
            "tone1": {"note": "C4", "opl_envelope": {
                "peak_level": 12, "sustain_level": 8,
                "attack_period_frames": 1, "decay_period_frames": 2,
                "release_period_frames": 4, "sustain_while_keyed": True,
            }},
        }],
        "conversion": {
            "enhanced_held_pitch": {"enabled": False},
            "enhanced_vibrato": {"enabled": False},
        },
    }
    calibrated = opl_enhanced.recalibrate_note_score(
        score, sample_rate=6850, frame_samples=137,
    )
    assert score["sample_rate_hz"] == 7100 and score["frame_samples"] == 142
    assert calibrated["sample_rate_hz"] == 6850
    assert calibrated["frame_samples"] == 137
    assert calibrated["rows"] == score["rows"]
    assert calibrated["conversion"]["timing_recalibration"] == {
        "source_sample_rate_hz": 7100,
        "source_frame_samples": 142,
        "sample_rate_hz": 6850,
        "frame_samples": 137,
        "policy": (
            "measured C-cosim timing-only adjustment; all pitches remain "
            "symbolic and are regenerated at the declared phase-table rate"
        ),
    }
    unsafe = copy.deepcopy(score)
    unsafe["rows"][0]["tone1"].pop("note")
    unsafe["rows"][0]["tone1"]["phase_step"] = 1234
    try:
        opl_enhanced.recalibrate_note_score(
            unsafe, sample_rate=6850, frame_samples=137,
        )
    except ValueError as exc:
        assert "source-aware" in str(exc)
    else:
        raise AssertionError("explicit phase step accepted timing-only change")


def main() -> int:
    check_timeline_and_rows()
    check_probe_fit()
    check_direct_vibrato_score()
    check_timing_recalibration()
    print("JUKUPOLY-OPL-ENHANCED: PASS allocation channel-continuity "
          "percussion envelope-fit bounded-rearticulation detuned-layers "
          "held-pitch-legato direct-vibrato v2-score")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
