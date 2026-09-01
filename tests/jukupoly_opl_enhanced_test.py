#!/usr/bin/env python3
"""Synthetic regression for real-song JPS v2 OPL-envelope reduction."""

from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FIRMWARE = ROOT / "spinoffs" / "jukupoly" / "firmware"
sys.path.insert(0, str(FIRMWARE))

import opl_enhanced  # noqa: E402
import opl_envelope  # noqa: E402
import opl_oracle  # noqa: E402
import opl_voices  # noqa: E402


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
            frame * 882, 0x200, 4, frame < 3, 0, 0,
            511, attenuation, 0, 0, 0, 0, 0, 0,
        )
        probes.append(opl_oracle.OracleChannelProbe(0, probe))
    probes.append(opl_oracle.OracleChannelProbe(
        0, opl_oracle.OracleProbe(
            6 * 882 + 17, 0x200, 4, False, 0, 0,
            511, 511, 0, 0, 0, 0, 0, 0,
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
    assert 1 <= fits[0].peak_level <= 15


def main() -> int:
    check_timeline_and_rows()
    check_probe_fit()
    print("JUKUPOLY-OPL-ENHANCED: PASS allocation channel-continuity "
          "percussion envelope-fit v2-score")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
