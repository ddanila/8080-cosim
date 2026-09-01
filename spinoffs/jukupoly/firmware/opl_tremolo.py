"""Host model for a bounded shared-phase JukuPoly tremolo reduction."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

import opl_envelope


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


@dataclass(frozen=True)
class JointEnvelopeTremoloFit:
    depth_levels: int
    envelope: opl_envelope.EnvelopeFit
    baseline_envelope: opl_envelope.EnvelopeFit

    @property
    def squared_error_improvement(self) -> int:
        return (self.baseline_envelope.squared_error -
                self.envelope.squared_error)


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


def quantized_oracle_am_effect(
        modulator_output_attenuation: int,
        carrier_output_attenuation: int,
        connection: int,
        modulator_am: bool,
        carrier_am: bool,
        tremolo_attenuation: int,
        *, peak_level: int = 15,
) -> tuple[int, int]:
    """Return (without AM, with AM) levels from one exact oracle probe."""
    if tremolo_attenuation < 0:
        raise ValueError("tremolo attenuation must be nonnegative")
    base_modulator = modulator_output_attenuation - (
        tremolo_attenuation if modulator_am else 0
    )
    base_carrier = carrier_output_attenuation - (
        tremolo_attenuation if carrier_am else 0
    )
    if base_modulator < 0 or base_carrier < 0:
        raise ValueError("tremolo exceeds oracle output attenuation")
    with_am = round(peak_level * opl_envelope.opl_channel_amplitude(
        modulator_output_attenuation, carrier_output_attenuation, connection,
    ))
    without_am = round(peak_level * opl_envelope.opl_channel_amplitude(
        base_modulator, base_carrier, connection,
    ))
    return without_am, with_am


def fit_joint_envelope_tremolo(
        reference_levels: Sequence[int], *, start_frame: int,
        key_off_frame: int | None, sustain_while_keyed: bool,
        counter_at_onset: int = 1,
        preserve_significant_directions: bool = True,
        peak_level: int | None = None,
        baseline_envelope: opl_envelope.EnvelopeFit | None = None,
) -> JointEnvelopeTremoloFit:
    """Jointly search the exact envelope packet and bounded tremolo depth."""
    reference = tuple(reference_levels)
    fits = [] if baseline_envelope is None else [(0, baseline_envelope)]
    depths = tuple(range(
        0 if baseline_envelope is None else 1, MAX_DEPTH + 1,
    ))
    transforms = tuple(
        lambda levels, selected=depth: simulate_tremolo(
            levels, start_frame=start_frame, depth_levels=selected,
        )
        for depth in depths
    )
    variant_fits = opl_envelope.fit_envelope_variants(
        reference,
        key_off_frame=key_off_frame,
        sustain_while_keyed=sustain_while_keyed,
        counter_at_onset=counter_at_onset,
        preserve_significant_directions=preserve_significant_directions,
        peak_level=peak_level,
        prediction_transforms=transforms,
    )
    fits.extend(zip(depths, variant_fits))
    baseline = fits[0][1]
    depth, fit = min(fits, key=lambda item: (
        item[1].squared_error, item[1].absolute_error,
        item[1].maximum_error, item[0],
    ))
    return JointEnvelopeTremoloFit(depth, fit, baseline)
