"""Bounded OPL vibrato model for guarded JukuPoly M5 experiments.

The source-side delta follows the pinned Nuked OPL3 phase generator exactly.
The target-side helpers use a non-accumulating delta from an immutable base
phase step; they do not imply that the 8080 representation has been accepted.
"""

from __future__ import annotations


PHASE_BITS = 16
PHASE_STEPS = 8
OPL_SAMPLES_PER_PHASE = 1024
DOOM_OPL_CLOCK_HZ = 14_318_180
DOOM_OPL_DIVIDER = 288
TARGET_FRAME_HZ = 50.0


def lfo_hz(opl_clock_hz: int = DOOM_OPL_CLOCK_HZ,
           opl_divider: int = DOOM_OPL_DIVIDER) -> float:
    if opl_clock_hz <= 0 or opl_divider <= 0:
        raise ValueError("OPL clock and divider must be positive")
    return opl_clock_hz / opl_divider / OPL_SAMPLES_PER_PHASE / PHASE_STEPS


def phase_increment(frame_hz: float = TARGET_FRAME_HZ) -> int:
    if frame_hz <= 0:
        raise ValueError("frame rate must be positive")
    return round(lfo_hz() / frame_hz * (1 << PHASE_BITS))


PHASE_INCREMENT = phase_increment()


def phase_at_frame(frame: int) -> int:
    if frame < 0:
        raise ValueError("frame must be nonnegative")
    return frame * PHASE_INCREMENT & 0xFFFF


def phase_position(phase: int) -> int:
    if not 0 <= phase <= 0xFFFF:
        raise ValueError("phase must be a 16-bit unsigned value")
    return phase >> (PHASE_BITS - 3)


def opl_f_number_delta(f_number: int, position: int, *, deep: bool) -> int:
    """Return Nuked's signed per-operator F-number deviation."""
    if not 0 <= f_number <= 0x3FF:
        raise ValueError("OPL F-number must be in 0..1023")
    if not 0 <= position < PHASE_STEPS:
        raise ValueError("vibrato position must be in 0..7")
    magnitude = (f_number >> 7) & 7
    if position & 3 == 0:
        magnitude = 0
    elif position & 1:
        magnitude >>= 1
    if not deep:
        magnitude >>= 1
    return -magnitude if position & 4 else magnitude


def target_step_delta(base_step: int, f_number: int, position: int,
                      *, deep: bool) -> int:
    """Precompute a signed Juku phase-step delta without cumulative drift."""
    if not 0 < base_step < 0x8000:
        raise ValueError("base phase step must be in 1..32767")
    if not 0 < f_number <= 0x3FF:
        raise ValueError("active OPL F-number must be in 1..1023")
    delta = opl_f_number_delta(f_number, position, deep=deep)
    magnitude = (base_step * abs(delta) + f_number // 2) // f_number
    return -magnitude if delta < 0 else magnitude


def target_steps(base_step: int, f_number: int, *, deep: bool) -> tuple[int, ...]:
    """Return the bounded eight-position target phase-step contour."""
    values = tuple(
        base_step + target_step_delta(
            base_step, f_number, position, deep=deep,
        )
        for position in range(PHASE_STEPS)
    )
    if min(values) <= 0 or max(values) >= 0x8000:
        raise ValueError("vibrato contour exceeds the 15-bit target range")
    return values
