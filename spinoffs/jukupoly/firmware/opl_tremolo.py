"""Host model for a bounded shared-phase JukuPoly tremolo reduction."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence


TARGET_FRAME_MILLIHZ = 50_000
OPL_TREMOLO_MILLIHZ = 3_700
PHASE_SCALE = 1 << 16
PHASE_INCREMENT = round(
    PHASE_SCALE * OPL_TREMOLO_MILLIHZ / TARGET_FRAME_MILLIHZ
)
TRIANGLE = (0, 1, 2, 3, 4, 5, 6, 7, 7, 6, 5, 4, 3, 2, 1, 0)
MAX_DEPTH = 3
TABLES = tuple(
    tuple(round(depth * value / max(TRIANGLE)) for value in TRIANGLE)
    for depth in range(MAX_DEPTH + 1)
)


@dataclass(frozen=True)
class TremoloFit:
    depth_levels: int
    predicted_levels: tuple[int, ...]
    squared_error: int
    absolute_error: int
    maximum_error: int
    baseline_squared_error: int

    @property
    def squared_error_improvement(self) -> int:
        return self.baseline_squared_error - self.squared_error


def phase_at_frame(frame: int) -> int:
    if not isinstance(frame, int) or frame < 0:
        raise ValueError("frame must be a nonnegative integer")
    return frame * PHASE_INCREMENT & 0xFFFF


def simulate_tremolo(envelope_levels: Sequence[int], *, start_frame: int,
                      depth_levels: int) -> tuple[int, ...]:
    """Apply a shared 3.7 Hz attenuation-only LFO at the 50 Hz frame rate."""
    if not envelope_levels or any(
            not isinstance(level, int) or not 0 <= level <= 15
            for level in envelope_levels):
        raise ValueError("envelope_levels must be a nonempty 0..15 sequence")
    if not isinstance(depth_levels, int) or not 0 <= depth_levels <= MAX_DEPTH:
        raise ValueError(f"depth_levels must be 0..{MAX_DEPTH}")
    phase = phase_at_frame(start_frame)
    table = TABLES[depth_levels]
    result = []
    for level in envelope_levels:
        attenuation = table[phase >> 12]
        result.append(max(0, level - attenuation))
        phase = (phase + PHASE_INCREMENT) & 0xFFFF
    return tuple(result)


def fit_tremolo(reference_levels: Sequence[int],
                envelope_levels: Sequence[int], *, start_frame: int
                ) -> TremoloFit:
    """Choose the least-error representable shared-LFO depth.

    Depth zero is a real candidate and wins ties.  Consequently AM on an
    inaudible FM modulator cannot manufacture square-wave volume modulation:
    the semantic carrier-amplitude reference has no matching residual.
    """
    reference = tuple(reference_levels)
    envelope = tuple(envelope_levels)
    if (not reference or len(reference) != len(envelope) or
            any(not isinstance(level, int) or not 0 <= level <= 15
                for level in reference)):
        raise ValueError("reference and envelope must be equal nonempty traces")
    baseline_squared = sum(
        (actual - predicted) ** 2
        for actual, predicted in zip(reference, envelope)
    )
    best = None
    best_score = None
    for depth in range(MAX_DEPTH + 1):
        predicted = simulate_tremolo(
            envelope, start_frame=start_frame, depth_levels=depth,
        )
        differences = tuple(
            actual - expected
            for actual, expected in zip(predicted, reference)
        )
        squared = sum(value * value for value in differences)
        absolute = sum(abs(value) for value in differences)
        maximum = max(abs(value) for value in differences)
        score = (squared, absolute, maximum, depth)
        if best_score is None or score < best_score:
            best_score = score
            best = TremoloFit(
                depth, predicted, squared, absolute, maximum,
                baseline_squared,
            )
    assert best is not None
    return best
