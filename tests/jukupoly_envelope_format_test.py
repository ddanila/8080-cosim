#!/usr/bin/env python3
"""Strict host-format regression for the JPS v2 envelope vertical slice."""

from __future__ import annotations

import copy
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FIRMWARE = ROOT / "spinoffs" / "jukupoly" / "firmware"
sys.path.insert(0, str(FIRMWARE))

import build_jukupoly as build  # noqa: E402


ENVELOPE = {
    "peak_level": 15,
    "sustain_level": 8,
    "attack_period_frames": 0,
    "decay_period_frames": 2,
    "release_period_frames": 4,
    "sustain_while_keyed": True,
}


def score() -> dict:
    return {
        "schema": "jukupoly-song-v2",
        "title": "Synthetic envelope ABI fixture",
        "sample_rate_hz": 7120,
        "frame_samples": 143,
        "rows": [
            {
                "frames": 8,
                "tone1": {"note": "A3", "opl_envelope": ENVELOPE},
            },
            {"frames": 8, "tone1": {"note": "---"}},
        ],
    }


def check_encoding() -> None:
    assert build.encode_opl_envelope(ENVELOPE, "fixture") == (0xF8, 0xD0, 0x02)
    generated, metadata = build.compile_song(score())
    assert metadata["enhanced_envelopes"]
    assert not metadata["enhanced_vibrato"]
    assert not metadata["mod_effects"] and not metadata["patterns"]
    assert "JUKUPOLY_ENHANCED_ENVELOPES equ 1" in generated
    image = build.assemble_song_file(generated, metadata)
    assert image[:4] == b"JPS\2"
    assert int.from_bytes(image[4:6], "little") == len(image)
    assert image[6:8] == bytes((143, build.JPS2_ENVELOPE_CAPABILITY))
    rows = int.from_bytes(image[10:12], "little") - build.SONG_LOAD_ADDRESS
    assert image[rows:rows + 7] == bytes((8, 1)) + bytes(
        (build.phase_step("A3", None, 7120) & 0xFF,
         build.phase_step("A3", None, 7120) >> 8,
         0xF8, 0xD0, 0x02)
    )
    assert image[rows + 7:rows + 11] == bytes((8, 1, 0, 0))

    zero = score()
    zero["rows"][0]["tone1"]["opl_tremolo_depth"] = 0
    zero_generated, zero_metadata = build.compile_song(zero)
    assert not zero_metadata["enhanced_tremolo"]
    assert build.assemble_song_file(
        zero_generated, zero_metadata,
    ) == image

    tremolo = score()
    tremolo["rows"][0]["tone1"]["opl_tremolo_depth"] = 1
    tremolo_generated, tremolo_metadata = build.compile_song(tremolo)
    assert tremolo_metadata["enhanced_tremolo"]
    tremolo_image = build.assemble_song_file(
        tremolo_generated, tremolo_metadata,
    )
    assert tremolo_image[6:8] == bytes((
        143,
        build.JPS2_ENVELOPE_CAPABILITY | build.JPS2_TREMOLO_CAPABILITY,
    ))
    tremolo_rows = (
        int.from_bytes(tremolo_image[10:12], "little") -
        build.SONG_LOAD_ADDRESS
    )
    assert tremolo_image[tremolo_rows + 6] == 0x06
    assert build.assemble(
        tremolo_generated, enhanced_envelopes=True, enhanced_tremolo=True,
    )

    vibrato = score()
    vibrato["rows"][0]["tone1"]["opl_vibrato"] = {
        "mode": "shallow", "peak_step_delta": 256,
    }
    vibrato_generated, vibrato_metadata = build.compile_song(vibrato)
    assert vibrato_metadata["enhanced_vibrato"]
    assert not vibrato_metadata["enhanced_tremolo"]
    vibrato_image = build.assemble_song_file(
        vibrato_generated, vibrato_metadata,
    )
    assert vibrato_image[6:8] == bytes((
        143,
        build.JPS2_ENVELOPE_CAPABILITY | build.JPS2_PITCH_CAPABILITY,
    ))
    vibrato_rows = (
        int.from_bytes(vibrato_image[10:12], "little") -
        build.SONG_LOAD_ADDRESS
    )
    assert vibrato_image[vibrato_rows + 6:vibrato_rows + 8] == bytes((
        0x12, 0xFF,
    ))
    try:
        build.assemble(
            vibrato_generated, enhanced_envelopes=True,
            enhanced_vibrato=True,
        )
    except build.SongError as exc:
        assert "not implemented" in str(exc)
    else:
        raise AssertionError("host-only pitch capability assembled a target")

    combined = copy.deepcopy(vibrato)
    combined["rows"][0]["tone1"]["opl_tremolo_depth"] = 1
    combined["rows"][0]["tone1"]["opl_vibrato"]["mode"] = "deep"
    combined_generated, combined_metadata = build.compile_song(combined)
    combined_image = build.assemble_song_file(
        combined_generated, combined_metadata,
    )
    assert combined_image[7] == (
        build.JPS2_ENVELOPE_CAPABILITY |
        build.JPS2_TREMOLO_CAPABILITY |
        build.JPS2_PITCH_CAPABILITY
    )
    combined_rows = (
        int.from_bytes(combined_image[10:12], "little") -
        build.SONG_LOAD_ADDRESS
    )
    assert combined_image[combined_rows + 6:combined_rows + 8] == bytes((
        0x26, 0xFF,
    ))


def rejected(record: dict, expected: str) -> None:
    candidate = score()
    candidate["rows"][0]["tone1"]["opl_envelope"] = record
    try:
        build.compile_song(candidate)
    except build.SongError as exc:
        assert expected in str(exc), str(exc)
    else:
        raise AssertionError(f"invalid envelope accepted: {record}")


def check_validation() -> None:
    missing = copy.deepcopy(ENVELOPE)
    del missing["release_period_frames"]
    rejected(missing, "missing release_period_frames")
    unknown = copy.deepcopy(ENVELOPE)
    unknown["opl_rate"] = 15
    rejected(unknown, "unknown opl_rate")
    bad_period = copy.deepcopy(ENVELOPE)
    bad_period["decay_period_frames"] = 3
    rejected(bad_period, "must be one of")
    bad_sustain = copy.deepcopy(ENVELOPE)
    bad_sustain["sustain_level"] = 16
    rejected(bad_sustain, "sustain_level")
    bad_bool = copy.deepcopy(ENVELOPE)
    bad_bool["sustain_while_keyed"] = 1
    rejected(bad_bool, "must be boolean")
    candidate = score()
    candidate["mod_effects"] = True
    try:
        build.compile_song(candidate)
    except build.SongError as exc:
        assert "cannot use MOD effects" in str(exc)
    else:
        raise AssertionError("JPS v2 accepted MOD effects")
    for frame_samples in (128, 144):
        candidate = score()
        candidate["frame_samples"] = frame_samples
        try:
            build.compile_song(candidate)
        except build.SongError as exc:
            assert "129..143" in str(exc)
        else:
            raise AssertionError(
                f"JPS v2 accepted unsafe frame batch {frame_samples}"
            )
    candidate = score()
    candidate.pop("rows")
    candidate["patterns"] = [[score()["rows"][0]]]
    candidate["order"] = [0]
    try:
        build.compile_song(candidate)
    except build.SongError as exc:
        assert "cannot use patterns" in str(exc)
    else:
        raise AssertionError("JPS v2 accepted unsupported pattern dispatch")

    for depth in (-1, 4, True, "1"):
        candidate = score()
        candidate["rows"][0]["tone1"]["opl_tremolo_depth"] = depth
        try:
            build.compile_song(candidate)
        except build.SongError as exc:
            assert "opl_tremolo_depth" in str(exc), str(exc)
        else:
            raise AssertionError(f"invalid tremolo depth accepted: {depth!r}")

    candidate = score()
    candidate["schema"] = "jukupoly-song-v1"
    candidate["rows"][0]["tone1"]["opl_tremolo_depth"] = 1
    try:
        build.compile_song(candidate)
    except build.SongError as exc:
        assert "requires jukupoly-song-v2" in str(exc), str(exc)
    else:
        raise AssertionError("JPS v1 accepted tremolo depth")

    candidate = score()
    candidate["rows"][1]["tone1"]["opl_tremolo_depth"] = 1
    try:
        build.compile_song(candidate)
    except build.SongError as exc:
        assert "key-off cannot carry" in str(exc), str(exc)
    else:
        raise AssertionError("key-off accepted tremolo depth")

    invalid_vibrato = (
        None,
        True,
        "deep",
        {},
        {"mode": "off", "peak_step_delta": 1},
        {"mode": "deep"},
        {"mode": "deep", "peak_step_delta": 1, "rate": 6},
        {"mode": "deep", "peak_step_delta": 0},
        {"mode": "deep", "peak_step_delta": 257},
        {"mode": "deep", "peak_step_delta": True},
    )
    for record in invalid_vibrato:
        candidate = score()
        candidate["rows"][0]["tone1"]["opl_vibrato"] = record
        try:
            build.compile_song(candidate)
        except build.SongError as exc:
            assert "vibrato" in str(exc), str(exc)
        else:
            raise AssertionError(f"invalid vibrato accepted: {record!r}")

    candidate = score()
    candidate["schema"] = "jukupoly-song-v1"
    candidate["rows"][0]["tone1"]["opl_vibrato"] = {
        "mode": "deep", "peak_step_delta": 1,
    }
    try:
        build.compile_song(candidate)
    except build.SongError as exc:
        assert "requires jukupoly-song-v2" in str(exc), str(exc)
    else:
        raise AssertionError("JPS v1 accepted vibrato")

    candidate = score()
    candidate["rows"][1]["tone1"]["opl_vibrato"] = {
        "mode": "deep", "peak_step_delta": 1,
    }
    try:
        build.compile_song(candidate)
    except build.SongError as exc:
        assert "key-off cannot carry" in str(exc), str(exc)
    else:
        raise AssertionError("key-off accepted vibrato")

    for phase_step, delta, expected in (
        (100, 100, "underflows"),
        (0x7F80, 128, "overflows"),
    ):
        candidate = score()
        event = candidate["rows"][0]["tone1"]
        event.pop("note")
        event["phase_step"] = phase_step
        event["opl_vibrato"] = {
            "mode": "deep", "peak_step_delta": delta,
        }
        try:
            build.compile_song(candidate)
        except build.SongError as exc:
            assert expected in str(exc), str(exc)
        else:
            raise AssertionError(f"unsafe vibrato {expected} accepted")


def main() -> int:
    check_encoding()
    check_validation()
    print("JUKUPOLY-ENVELOPE-FORMAT: PASS jps2-header conditional-vibrato "
          "resolved-levels resolved-rates strict-capability tremolo-bits")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
