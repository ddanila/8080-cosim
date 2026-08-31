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


def main() -> int:
    check_encoding()
    check_validation()
    print("JUKUPOLY-ENVELOPE-FORMAT: PASS jps2-header five-byte-tone "
          "resolved-levels resolved-rates strict-capability")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
