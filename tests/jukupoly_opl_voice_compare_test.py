#!/usr/bin/env python3
"""Focused guards for the isolated OPL/Juku comparison pipeline."""

from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "spinoffs" / "jukupoly" / "firmware"))
sys.path.insert(0, str(ROOT / "spinoffs" / "jukupoly" / "tools"))

import compare_jukupoly_opl_voice as compare  # noqa: E402
import opl_voices  # noqa: E402


def note(identifier: int, start: int, end: int, pitch: float
         ) -> opl_voices.LogicalNote:
    return opl_voices.LogicalNote(
        identifier, start, end, (identifier,), ("patch",), ((0, 0),),
        pitch, pitch, 100, 10, True,
    )


def main() -> int:
    notes = [note(0, 0, 882, 42.0), note(1, 0, 882, 54.0)]
    assert compare.select_logical_note(
        notes, identifier=1, at_seconds=0, midi_note=None,
    ).identifier == 1
    assert compare.select_logical_note(
        notes, identifier=None, at_seconds=0, midi_note=42,
    ).identifier == 0
    allocation = compare.isolated_allocation(notes[0], 3)
    assert allocation["frames"] == [
        {"frame": 0, "selected": [{
            "logical_note": 0, "logical_voice": 0, "midi_note": 42,
        }]},
        {"frame": 1, "selected": []},
    ]
    assert compare.frame_rows(511) == [
        {"frames": 255}, {"frames": 255}, {"frames": 1},
    ]
    audio = compare.Audio(100, 1, tuple((1000,) for _ in range(100)))
    assert len(compare.frame_rms(audio, 50)) == 50
    assert all(value > 0 for value in compare.frame_rms(audio, 50))
    assert compare.renderer_run_seconds(
        "JUKUPOLY-WAV: PASS run=1.250s wav=1.250s"
    ) == 1.25
    segment = opl_voices.NoteSegment(
        0, 0, 0, 0, 882, "patch", 100, 10, True,
        (opl_voices.PitchPoint(0, 0x200, 4, 42.0),),
    )
    report = {
        "detuned_layer_analysis": {
            "target_sample_rate_hz": 7170,
            "episodes": [{
                "logical_note": 0,
                "members": [{
                    "segment": 0, "source_segments": [0],
                    "phase_step": 845,
                }],
            }],
        },
        "notes": [{
            "logical_note": 0,
            "detuned_layer_episode": {
                "logical_note": 0, "members": [],
            },
        }],
    }
    retuned = compare.recalibrate_detuned_phase_steps(
        report, [segment], notes[0], 42, 7188,
    )
    assert retuned["detuned_layer_analysis"][
        "target_sample_rate_hz"
    ] == 7188
    assert retuned["detuned_layer_analysis"]["episodes"][0][
        "members"
    ][0]["phase_step"] == 843
    assert report["detuned_layer_analysis"]["episodes"][0][
        "members"
    ][0]["phase_step"] == 845
    print("JUKUPOLY-VOICE-DIFF: PASS selection allocation contour")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
