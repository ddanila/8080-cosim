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


def check_bounds() -> None:
    try:
        opl_tremolo.simulate_tremolo(
            (10,), start_frame=0, depth_levels=4,
        )
    except ValueError as exc:
        assert "0..3" in str(exc)
    else:
        raise AssertionError("out-of-range tremolo depth accepted")


def main() -> int:
    check_shared_phase_and_rate()
    check_exact_quantized_fit()
    check_inaudible_modulator_does_not_become_volume_lfo()
    check_bounds()
    print("JUKUPOLY-OPL-TREMOLO: PASS shared-phase fixed-rate exact-fit "
          "bounded-depth inaudible-modulator-guard")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
