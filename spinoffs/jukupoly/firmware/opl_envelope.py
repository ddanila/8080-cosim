"""Fit compact JPS v2 envelopes to host-side OPL reference levels.

The fitter models the target's actual 50 Hz state machine, including its
global power-of-two update masks.  It deliberately accepts already-quantized
0..15 reference levels: extracting a logical source voice and deciding its
absolute Juku loudness are separate conversion-policy steps.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Sequence


RATE_PERIODS = (0, 1, 2, 4, 8, 16, 32, 64)
OPL_ATTENUATION_DB = 0.1875

OFF = 0
ATTACK = 1
DECAY = 2
HOLD = 3
RELEASE = 4


@dataclass(frozen=True)
class EnvelopeFit:
    peak_level: int
    sustain_level: int
    attack_period_frames: int
    decay_period_frames: int
    release_period_frames: int
    sustain_while_keyed: bool
    predicted_levels: tuple[int, ...]
    squared_error: int
    absolute_error: int
    maximum_error: int

    def packet(self) -> dict[str, int | bool]:
        """Return the strict `opl_envelope` object accepted by JPS v2."""
        return {
            "peak_level": self.peak_level,
            "sustain_level": self.sustain_level,
            "attack_period_frames": self.attack_period_frames,
            "decay_period_frames": self.decay_period_frames,
            "release_period_frames": self.release_period_frames,
            "sustain_while_keyed": self.sustain_while_keyed,
        }


def opl_channel_amplitude(modulator_attenuation: int,
                          carrier_attenuation: int,
                          connection: int) -> float:
    """Reduce post-EG OPL attenuation to a waveform-independent amplitude.

    Nuked's ``eg_out`` is in quarter-TL units: one unit is 0.1875 dB.  In FM
    connection mode only the carrier is a direct channel output; in additive
    mode both operators contribute.  The sum is capped because Juku has only
    one 4-bit level per logical voice.  This intentionally models amplitude,
    not OPL waveform or feedback timbre.
    """
    if (not isinstance(modulator_attenuation, int) or
            not isinstance(carrier_attenuation, int) or
            modulator_attenuation < 0 or carrier_attenuation < 0):
        raise ValueError("OPL attenuation must be nonnegative integers")
    if connection not in (0, 1):
        raise ValueError("OPL connection must be 0 or 1")

    def amplitude(attenuation: int) -> float:
        return 10.0 ** (-(attenuation * OPL_ATTENUATION_DB) / 20.0)

    result = amplitude(carrier_attenuation)
    if connection:
        result += amplitude(modulator_attenuation)
    return min(1.0, result)


def quantize_opl_channel(modulator_attenuation: Sequence[int],
                         carrier_attenuation: Sequence[int],
                         connection: Sequence[int],
                         *, peak_level: int = 15) -> tuple[int, ...]:
    """Map a 50 Hz oracle attenuation trace to absolute Juku levels."""
    if not 1 <= peak_level <= 15:
        raise ValueError("peak_level must be 1..15")
    if not (len(modulator_attenuation) == len(carrier_attenuation) ==
            len(connection)) or not modulator_attenuation:
        raise ValueError("OPL attenuation traces must have equal nonzero length")
    return tuple(round(peak_level * opl_channel_amplitude(modulator, carrier,
                                                          algorithm))
                 for modulator, carrier, algorithm in zip(
                     modulator_attenuation, carrier_attenuation, connection))


def _check_period(name: str, value: int) -> None:
    if value not in RATE_PERIODS:
        raise ValueError(f"{name} must be one of {RATE_PERIODS}, got {value}")


def simulate_envelope(
    frames: int,
    *,
    key_off_frame: int | None,
    peak_level: int,
    sustain_level: int,
    attack_period_frames: int,
    decay_period_frames: int,
    release_period_frames: int,
    sustain_while_keyed: bool,
    counter_at_onset: int = 1,
) -> tuple[int, ...]:
    """Execute the compact envelope with the target player's exact ordering.

    Frame zero contains the key-on parse.  On later frames the player first
    advances the old stage, then parses a key-off row at `key_off_frame`.
    Nonzero periods use the same global counter masks as the 8080 code.
    """
    if frames < 1:
        raise ValueError("frames must be positive")
    if key_off_frame is not None and not 0 <= key_off_frame < frames:
        raise ValueError("key_off_frame must be inside the rendered interval")
    if not 1 <= peak_level <= 15:
        raise ValueError("peak_level must be 1..15")
    if not 0 <= sustain_level <= peak_level:
        raise ValueError("sustain_level must be 0..peak_level")
    for name, value in (
        ("attack period", attack_period_frames),
        ("decay period", decay_period_frames),
        ("release period", release_period_frames),
    ):
        _check_period(name, value)
    if not isinstance(sustain_while_keyed, bool):
        raise ValueError("sustain_while_keyed must be boolean")
    if not 0 <= counter_at_onset <= 255:
        raise ValueError("counter_at_onset must be 0..255")

    volume = 0
    stage = ATTACK

    def settle() -> None:
        nonlocal volume, stage
        while True:
            if stage == ATTACK and attack_period_frames == 0:
                volume = peak_level
                stage = DECAY
            elif stage == DECAY and decay_period_frames == 0:
                volume = sustain_level
                stage = HOLD if sustain_while_keyed else RELEASE
            elif stage == RELEASE and release_period_frames == 0:
                volume = 0
                stage = OFF
            else:
                return

    def advance(counter: int) -> None:
        nonlocal volume, stage
        period = {
            ATTACK: attack_period_frames,
            DECAY: decay_period_frames,
            RELEASE: release_period_frames,
        }.get(stage)
        if period is None or period == 0 or counter & (period - 1):
            return
        if stage == ATTACK:
            volume += 1
            if volume >= peak_level:
                volume = peak_level
                stage = DECAY
                settle()
        elif stage == DECAY:
            volume -= 1
            if volume <= sustain_level:
                volume = sustain_level
                stage = HOLD if sustain_while_keyed else RELEASE
                settle()
        elif stage == RELEASE:
            volume -= 1
            if volume <= 0:
                volume = 0
                stage = OFF

    settle()
    if key_off_frame == 0:
        stage = RELEASE
        settle()
    result = [volume]
    for frame in range(1, frames):
        advance((counter_at_onset + frame) & 0xFF)
        if frame == key_off_frame:
            stage = RELEASE
            settle()
        result.append(volume)
    return tuple(result)


def fit_envelope(
    reference_levels: Sequence[int],
    *,
    key_off_frame: int | None,
    sustain_while_keyed: bool,
    counter_at_onset: int = 1,
    peak_level: int | None = None,
    preserve_significant_directions: bool = False,
) -> EnvelopeFit:
    """Find the deterministic least-squares compact target approximation."""
    reference = tuple(reference_levels)
    if not reference or any(
            not isinstance(level, int) or not 0 <= level <= 15
            for level in reference):
        raise ValueError("reference_levels must be a nonempty 0..15 sequence")
    if peak_level is not None and not 1 <= peak_level <= 15:
        raise ValueError("peak_level must be 1..15")

    observed_peak = max(reference)
    if peak_level is None:
        peak_candidates = set(range(
            max(1, observed_peak - 2), min(15, observed_peak + 2) + 1,
        ))
    else:
        peak_candidates = {peak_level}
    if not peak_candidates:
        peak_candidates.add(1)

    def direction_mismatches(predicted: Sequence[int]) -> int:
        if not preserve_significant_directions:
            return 0
        return envelope_directions(
            reference, predicted, key_off_frame,
        )["mismatches"]

    best: EnvelopeFit | None = None
    best_score: tuple[int, ...] | None = None
    for peak in sorted(peak_candidates):
        for sustain in range(peak + 1):
            for attack in RATE_PERIODS:
                for decay in RATE_PERIODS:
                    for release in RATE_PERIODS:
                        predicted = simulate_envelope(
                            len(reference),
                            key_off_frame=key_off_frame,
                            peak_level=peak,
                            sustain_level=sustain,
                            attack_period_frames=attack,
                            decay_period_frames=decay,
                            release_period_frames=release,
                            sustain_while_keyed=sustain_while_keyed,
                            counter_at_onset=counter_at_onset,
                        )
                        differences = tuple(
                            actual - expected
                            for actual, expected in zip(predicted, reference)
                        )
                        squared = sum(value * value for value in differences)
                        absolute = sum(abs(value) for value in differences)
                        maximum = max(abs(value) for value in differences)
                        score = (
                            direction_mismatches(predicted),
                            squared, absolute, maximum,
                            RATE_PERIODS.index(attack)
                            + RATE_PERIODS.index(decay)
                            + RATE_PERIODS.index(release),
                            peak, sustain,
                            RATE_PERIODS.index(attack),
                            RATE_PERIODS.index(decay),
                            RATE_PERIODS.index(release),
                        )
                        if best_score is None or score < best_score:
                            best_score = score
                            best = EnvelopeFit(
                                peak, sustain, attack, decay, release,
                                sustain_while_keyed, predicted,
                                squared, absolute, maximum,
                            )
    assert best is not None
    return best


def envelope_directions(reference: Sequence[int], predicted: Sequence[int],
                        key_off_frame: int | None) -> dict:
    """Compare significant net ADSR directions after 4-bit quantization."""
    if not reference or len(reference) != len(predicted):
        raise ValueError("envelope direction traces must have equal nonzero length")
    if key_off_frame is not None and not 0 <= key_off_frame < len(reference):
        raise ValueError("key_off_frame must be inside direction traces")
    keyed_end = key_off_frame if key_off_frame is not None else len(reference) - 1
    reference_peak_at = max(
        range(keyed_end + 1), key=lambda index: reference[index],
    )
    predicted_peak_at = max(
        range(keyed_end + 1), key=lambda index: predicted[index],
    )

    def direction(first: int, last: int) -> int:
        return (last > first) - (last < first)

    stages = {
        "attack": (
            reference[0], reference[reference_peak_at],
            predicted[0], predicted[predicted_peak_at],
        ),
        "decay": (
            reference[reference_peak_at], reference[keyed_end],
            predicted[predicted_peak_at], predicted[keyed_end],
        ),
    }
    if key_off_frame is not None and key_off_frame + 1 < len(reference):
        stages["release"] = (
            reference[key_off_frame], reference[-1],
            predicted[key_off_frame], predicted[-1],
        )

    result = {}
    mismatches = 0
    for stage, (reference_start, reference_end,
                predicted_start, predicted_end) in stages.items():
        reference_delta = reference_end - reference_start
        predicted_delta = predicted_end - predicted_start
        reference_direction = direction(reference_start, reference_end)
        predicted_direction = direction(predicted_start, predicted_end)
        significant = abs(reference_delta) >= 2
        immediate_equivalent = (
            stage == "attack" and predicted_direction == 0 and
            reference_peak_at <= 1
        )
        match = (
            not significant or immediate_equivalent or
            reference_direction == predicted_direction
        )
        mismatches += int(not match)
        result[stage] = {
            "reference": reference_direction,
            "predicted": predicted_direction,
            "reference_delta_levels": reference_delta,
            "predicted_delta_levels": predicted_delta,
            "significant": significant,
            "match": match,
        }
    return {"mismatches": mismatches, "stages": result}


def quantize_isolated_pcm(
    pcm: Sequence[tuple[int, int]],
    *,
    start_sample: int,
    frames: int,
    peak_level: int,
    samples_per_frame: int = 882,
    normalization_frames: int | None = None,
) -> tuple[int, ...]:
    """Reduce isolated oracle PCM to relative 4-bit frame RMS levels.

    `peak_level` is the independently resolved absolute Juku loudness.  The
    oracle PCM supplies only the evolving envelope shape, avoiding a claim
    that OPL waveform amplitude and one-bit speaker loudness are equivalent.
    """
    if start_sample < 0 or frames < 1 or samples_per_frame < 1:
        raise ValueError("invalid PCM frame interval")
    if not 1 <= peak_level <= 15:
        raise ValueError("peak_level must be 1..15")
    end = start_sample + frames * samples_per_frame
    if end > len(pcm):
        raise ValueError("PCM does not cover the requested frame interval")
    if normalization_frames is None:
        normalization_frames = frames
    if not 1 <= normalization_frames <= frames:
        raise ValueError("normalization_frames must be 1..frames")

    rms: list[float] = []
    for frame in range(frames):
        begin = start_sample + frame * samples_per_frame
        block = pcm[begin:begin + samples_per_frame]
        mean_square = sum(
            (left * left + right * right) / 2 for left, right in block
        ) / samples_per_frame
        rms.append(math.sqrt(mean_square))
    scale = max(rms[:normalization_frames])
    if not scale:
        return (0,) * frames
    return tuple(
        max(0, min(peak_level, round(peak_level * value / scale)))
        for value in rms
    )
