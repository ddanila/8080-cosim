#!/usr/bin/env python3
"""Regression checks for documented OPL-to-JukuPoly reduction rules."""

from __future__ import annotations

import importlib.util
import sys
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
IMPORTER = ROOT / "spinoffs/jukupoly/firmware/import_jukupoly_vgz.py"
sys.path.insert(0, str(IMPORTER.parent))
SPEC = importlib.util.spec_from_file_location("import_jukupoly_vgz", IMPORTER)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def check_volume() -> None:
    registers = [[0] * 256 for _ in range(2)]
    expected = {0: 16, 3: 13, 4: 12, 6: 10, 63: 1}
    for attenuation, volume in expected.items():
        registers[0][0x43] = attenuation
        assert MODULE.editor_volume(registers, 0, 0) == volume

    registers[0][0x40] = 6
    registers[0][0x43] = 6
    registers[0][0xC0] = 1
    assert MODULE.editor_volume(registers, 0, 0) == 16


def event(start: int, signature: tuple[int, ...], note: int,
          channel: int) -> object:
    return MODULE.KeyEvent(
        start=start, end=start + 100, bank=0, channel=channel,
        signature=signature, note=note,
    )


def check_classification() -> None:
    variable = (1,)
    chord = (2,)
    fixed = (3,)
    events = [
        event(0, variable, 48, 0),
        event(10, variable, 50, 0),
        event(20, variable, 52, 0),
        event(30, variable, 53, 0),
        event(100, chord, 60, 0),
        event(100, chord, 64, 1),
        event(100, chord, 67, 2),
        event(200, fixed, 48, 3),
    ]
    counts = Counter({variable: 8, chord: 3, fixed: 20})
    melodic = MODULE.melodic_signatures(events, counts)
    assert variable in melodic
    assert chord in melodic
    assert fixed not in melodic


def check_pitch_preservation() -> None:
    # The old per-note D2/E2 boundary turned the ascending source interval
    # D2->E2 into D3->E2.  Every representable source octave must survive.
    assert MODULE.playable_note(38) == 38       # D2, step 676
    assert MODULE.playable_note(40) == 40       # E2, step 759
    assert MODULE.playable_note(105) == 105     # A7, highest encodable MIDI note
    assert MODULE.playable_note(106) == 94      # A#7 needs one octave down
    assert MODULE.playable_note(107) == 95      # B7 needs one octave down

    def phase_step(note: int) -> int:
        frequency = 440.0 * 2.0 ** ((note - 69) / 12.0)
        return round(frequency * 65536.0 / MODULE.TARGET_RATE)

    # Lock the policy over the complete MIDI note range, rather than only the
    # notes seen in today's source packs.  A playable note is unchanged; an
    # unplayable one may move only by octaves, to the nearest playable octave.
    for source in range(128):
        mapped = MODULE.playable_note(source)
        assert 0 < phase_step(mapped) < 0x8000
        assert (source - mapped) % 12 == 0
        if 0 < phase_step(source) < 0x8000:
            assert mapped == source
        elif mapped < source:
            assert phase_step(mapped + 12) >= 0x8000
        else:
            assert phase_step(mapped - 12) <= 0


def check_articulated_voice_priority() -> None:
    # Dark Halls has a retriggered D#3 bass plus an upper chord.  At 12 s its
    # newly articulated G5 used to lose to three already sounding notes, so
    # the top-line event vanished entirely from the three-voice reduction.
    candidates = {
        51: MODULE.Candidate(51, 3),    # D#3 bass, also retriggered now
        73: MODULE.Candidate(73, 13),   # C#5 sustaining
        75: MODULE.Candidate(75, 13),   # D#5 sustaining
        79: MODULE.Candidate(79, 13),   # G5 newly articulated top line
    }
    selected = MODULE.choose_candidates(
        candidates, [51, 73, 75], {51, 79},
    )
    assert set(selected) == {51, 73, 79}


def main() -> int:
    check_volume()
    check_classification()
    check_pitch_preservation()
    check_articulated_voice_priority()
    print("JUKUPOLY-VGZ-IMPORT: PASS logarithmic-volume chord-classification "
          "source-octave-preservation articulated-voice-priority")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
