#!/usr/bin/env python3
"""Regression for the bounded host-side M5 vibrato model."""

from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FIRMWARE = ROOT / "spinoffs" / "jukupoly" / "firmware"
sys.path.insert(0, str(FIRMWARE))

import opl_vibrato  # noqa: E402


def check_source_rate_and_shape() -> None:
    assert abs(opl_vibrato.lfo_hz() - 6.0688357883) < 1e-9
    assert opl_vibrato.PHASE_INCREMENT == 7955
    assert opl_vibrato.phase_at_frame(137) == 137 * 7955 & 0xFFFF
    actual_cycles = 500 * opl_vibrato.PHASE_INCREMENT / 65536
    assert abs(actual_cycles - 10 * opl_vibrato.lfo_hz()) < 1 / 16

    assert tuple(opl_vibrato.opl_f_number_delta(
        0x3FF, position, deep=True,
    ) for position in range(8)) == (0, 3, 7, 3, 0, -3, -7, -3)
    assert tuple(opl_vibrato.opl_f_number_delta(
        0x3FF, position, deep=False,
    ) for position in range(8)) == (0, 1, 3, 1, 0, -1, -3, -1)


def check_nonaccumulating_target_contour() -> None:
    deep = opl_vibrato.target_steps(0x4000, 0x3FF, deep=True)
    shallow = opl_vibrato.target_steps(0x4000, 0x3FF, deep=False)
    assert deep[0] == deep[4] == 0x4000
    assert deep[2] - 0x4000 == 0x4000 - deep[6]
    assert shallow[2] - 0x4000 == 0x4000 - shallow[6]
    assert max(deep) - min(deep) > max(shallow) - min(shallow)
    # Every value is independently derived from the immutable base; applying
    # repeated cycles can never walk the base step up or down.
    assert opl_vibrato.target_steps(0x4000, 0x3FF, deep=True) == deep


def check_bounds() -> None:
    for arguments in ((0, 1), (0x8000, 1), (1, 0)):
        try:
            opl_vibrato.target_steps(*arguments, deep=True)
        except ValueError:
            pass
        else:
            raise AssertionError(f"invalid target contour accepted: {arguments}")
    assert all(opl_vibrato.opl_f_number_delta(
        0x7F, position, deep=True,
    ) == 0 for position in range(8))


def main() -> int:
    check_source_rate_and_shape()
    check_nonaccumulating_target_contour()
    check_bounds()
    print("JUKUPOLY-OPL-VIBRATO: PASS exact-nuked-shape fractional-rate "
          "bounded-step no-drift")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
