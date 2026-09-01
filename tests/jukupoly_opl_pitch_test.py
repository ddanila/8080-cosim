#!/usr/bin/env python3
"""Regression for conservative M5 vibrato and held-pitch classification."""

from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FIRMWARE = ROOT / "spinoffs" / "jukupoly" / "firmware"
TOOLS = ROOT / "spinoffs" / "jukupoly" / "tools"
sys.path.insert(0, str(FIRMWARE))
sys.path.insert(0, str(TOOLS))
sys.path.insert(0, str(ROOT / "tests"))

import import_jukupoly_vgz as vgz  # noqa: E402
import jukupoly_opl_trace_test as synthetic  # noqa: E402
import report_opl_pitch  # noqa: E402


def signature(modulator: bool, carrier: bool, additive: bool) -> tuple[int, ...]:
    values = [0] * 11
    values[0] = 0x40 if modulator else 0
    values[4] = 0x40 if carrier else 0
    values[10] = 1 if additive else 0
    return tuple(values)


def check_paths() -> None:
    assert report_opl_pitch.vibrato_path(
        signature(True, True, False)) == "direct_common_pitch"
    assert report_opl_pitch.vibrato_path(
        signature(False, True, False)) == "direct_common_pitch"
    assert report_opl_pitch.vibrato_path(
        signature(True, False, False)) == "fm_modulator_only"
    assert report_opl_pitch.vibrato_path(
        signature(True, False, True)) == "additive_partial_pitch"
    assert report_opl_pitch.vibrato_path(
        signature(False, True, True)) == "additive_partial_pitch"
    assert report_opl_pitch.vibrato_path(
        signature(False, False, False)) == "none"


def check_held_pitch_coalescing() -> None:
    info, writes = vgz.parse_vgm(synthetic.synthetic_opl3_vgm())
    changes, raw = report_opl_pitch.held_pitch_changes(writes, info.banks)
    assert raw == 1
    assert len(changes) == 1
    change = changes[0]
    assert (change.sample, change.bank, change.channel) == (882, 0, 0)
    assert change.before_code == 0x234 << 4
    assert change.after_code == 0x240 << 4
    assert change.cents > 0
    assert report_opl_pitch.vibrato_path(
        change.signature) == "additive_partial_pitch"


def main() -> int:
    check_paths()
    check_held_pitch_coalescing()
    print("JUKUPOLY-OPL-PITCH: PASS conservative-vibrato-paths "
          "held-key-coalescing cents")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
