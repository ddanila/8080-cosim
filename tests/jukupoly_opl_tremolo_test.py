#!/usr/bin/env python3
"""Regression for the bounded host-side M4 tremolo model."""

from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FIRMWARE = ROOT / "spinoffs" / "jukupoly" / "firmware"
sys.path.insert(0, str(FIRMWARE))

import opl_tremolo  # noqa: E402


def check_shared_phase_and_rate() -> None:
    assert opl_tremolo.PHASE_INCREMENT == 4850
    assert opl_tremolo.phase_at_frame(0) == 0
    assert opl_tremolo.phase_at_frame(137) == (
        137 * opl_tremolo.PHASE_INCREMENT & 0xFFFF
    )
    # Over ten seconds, the fixed-point accumulator must stay within one
    # sixteenth-table phase of the intended 37 OPL tremolo cycles.
    frames = 500
    actual_cycles = frames * opl_tremolo.PHASE_INCREMENT / (1 << 16)
    assert abs(actual_cycles - 37.0) < 1 / 16


def check_exact_quantized_fit() -> None:
    envelope = (12,) * 96
    reference = opl_tremolo.simulate_tremolo(
        envelope, start_frame=23, depth_levels=3,
    )
    fit = opl_tremolo.fit_tremolo(
        reference, envelope, start_frame=23,
    )
    assert fit.depth_levels == 3
    assert fit.predicted_levels == reference
    assert fit.squared_error == 0
    assert fit.squared_error_improvement > 0


def check_inaudible_modulator_does_not_become_volume_lfo() -> None:
    # In FM connection mode an AM-enabled modulator changes timbre, not direct
    # carrier amplitude.  The semantic reference therefore remains flat and
    # depth zero must win; no source flag alone can enable target tremolo.
    carrier_envelope = (9,) * 96
    fit = opl_tremolo.fit_tremolo(
        carrier_envelope, carrier_envelope, start_frame=0,
    )
    assert fit.depth_levels == 0
    assert fit.squared_error == 0
    assert fit.squared_error_improvement == 0


def check_joint_envelope_fit() -> None:
    envelope = opl_tremolo.opl_envelope.simulate_envelope(
        48, key_off_frame=36, peak_level=12, sustain_level=8,
        attack_period_frames=1, decay_period_frames=4,
        release_period_frames=2, sustain_while_keyed=True,
        counter_at_onset=8,
    )
    reference = opl_tremolo.simulate_tremolo(
        envelope, start_frame=7, depth_levels=2,
    )
    fit = opl_tremolo.fit_joint_envelope_tremolo(
        reference, start_frame=7, key_off_frame=36,
        sustain_while_keyed=True, counter_at_onset=8,
    )
    assert fit.depth_levels == 2
    assert fit.envelope.predicted_levels == reference
    assert fit.envelope.squared_error == 0
    assert fit.squared_error_improvement > 0
    baseline = opl_tremolo.opl_envelope.fit_envelope(
        reference, key_off_frame=36, sustain_while_keyed=True,
        counter_at_onset=8,
    )
    reused = opl_tremolo.fit_joint_envelope_tremolo(
        reference, start_frame=7, key_off_frame=36,
        sustain_while_keyed=True, counter_at_onset=8,
        baseline_envelope=baseline,
    )
    assert reused == fit
    target_wrapper = opl_tremolo.fit_target_envelope_tremolo(
        reference, start_frame=7, key_off_frame=36,
        source_sustain_while_keyed=True,
        allow_alternate_sustain_mode=False, counter_at_onset=8,
    )
    assert target_wrapper == fit


def check_joint_target_shape_fit() -> None:
    # Source EGT is sustained, but the target's existing two-slope automatic
    # release is the exact reduction.  Joint tremolo fitting must search that
    # alternate target state rather than either rejecting the combination or
    # forcing the source-semantic state back into the result.
    envelope = opl_tremolo.opl_envelope.simulate_envelope(
        88, key_off_frame=None, peak_level=12, sustain_level=11,
        attack_period_frames=1, decay_period_frames=64,
        release_period_frames=2, sustain_while_keyed=False,
        counter_at_onset=1,
    )
    reference = opl_tremolo.simulate_tremolo(
        envelope, start_frame=0, depth_levels=2,
    )
    semantic = opl_tremolo.fit_target_envelope_tremolo(
        reference, start_frame=0, key_off_frame=None,
        source_sustain_while_keyed=True,
        allow_alternate_sustain_mode=False,
    )
    shaped = opl_tremolo.fit_target_envelope_tremolo(
        reference, start_frame=0, key_off_frame=None,
        source_sustain_while_keyed=True,
        allow_alternate_sustain_mode=True,
    )
    assert semantic.envelope.squared_error > 0
    assert shaped.depth_levels == 2
    assert shaped.envelope.sustain_while_keyed is False
    assert shaped.envelope.predicted_levels == reference
    assert shaped.envelope.squared_error == 0
    assert shaped.squared_error_improvement > 0


def check_joint_direction_priority() -> None:
    # Regression found by a deterministic bounded-trace search.  Selecting
    # tremolo depth by least squares alone chooses depth 1 with one significant
    # release-direction mismatch (31 squared error).  The converter-wide
    # direction guard must prefer depth 2 with no mismatch (35 squared error).
    reference = (
        2, 2, 4, 4, 4, 2, 0, 2, 2, 2, 2, 2,
        3, 1, 1, 1, 0, 0, 0, 0, 0, 0, 1, 3,
    )
    fitted = opl_tremolo.fit_joint_envelope_tremolo(
        reference, start_frame=14, key_off_frame=20,
        sustain_while_keyed=True, counter_at_onset=15,
        preserve_significant_directions=True,
    )
    directions = opl_tremolo.opl_envelope.envelope_directions(
        reference, fitted.envelope.predicted_levels, 20,
    )
    assert fitted.depth_levels == 2
    assert fitted.envelope.squared_error == 35
    assert directions["mismatches"] == 0


def check_bounds() -> None:
    try:
        opl_tremolo.simulate_tremolo(
            (10,), start_frame=0, depth_levels=4,
        )
    except ValueError as exc:
        assert "0..3" in str(exc)
    else:
        raise AssertionError("out-of-range tremolo depth accepted")

    # AM on an indirect FM modulator cannot change the semantic carrier level.
    assert opl_tremolo.quantized_oracle_am_effect(
        40, 32, 0, True, False, 8,
    ) == opl_tremolo.quantized_oracle_am_effect(
        32, 32, 0, False, False, 0,
    )
    without, with_am = opl_tremolo.quantized_oracle_am_effect(
        32, 32, 0, False, True, 8,
    )
    assert without >= with_am


def main() -> int:
    check_shared_phase_and_rate()
    check_exact_quantized_fit()
    check_inaudible_modulator_does_not_become_volume_lfo()
    check_joint_envelope_fit()
    check_joint_target_shape_fit()
    check_joint_direction_priority()
    check_bounds()
    print("JUKUPOLY-OPL-TREMOLO: PASS shared-phase fixed-rate exact-fit "
          "bounded-depth direction-priority inaudible-modulator-guard")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
