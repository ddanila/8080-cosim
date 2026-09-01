"""Fit compact JPS v2 envelopes to host-side OPL reference levels.

The fitter models the target's actual 50 Hz state machine, including its
global power-of-two update masks.  It deliberately accepts already-quantized
0..15 reference levels: extracting a logical source voice and deciding its
absolute Juku loudness are separate conversion-policy steps.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from functools import lru_cache
from typing import Callable, Sequence


RATE_PERIODS = (0, 1, 2, 4, 8, 16, 32, 64)
OPL_ATTENUATION_DB = 0.1875

OFF = 0
ATTACK = 1
DECAY = 2
HOLD = 3
RELEASE = 4
SIGNIFICANT_REARTICULATION_LEVELS = 4


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
    prediction_transform: Callable[
        [tuple[int, ...]], tuple[int, ...]
    ] | None = None,
) -> EnvelopeFit:
    """Find the deterministic least-squares compact target approximation."""
    if not 0 <= counter_at_onset <= 255:
        raise ValueError("counter_at_onset must be 0..255")
    if prediction_transform is None:
        # Every target update period is a power of two no larger than 64, so
        # only the low six counter bits can affect a prediction.  Complete
        # pack sources repeat many identical quantized note envelopes; cache
        # their exact exhaustive result without changing the search.
        return _fit_envelope_cached(
            tuple(reference_levels), key_off_frame, sustain_while_keyed,
            counter_at_onset & 0x3F, peak_level,
            preserve_significant_directions,
        )
    return fit_envelope_variants(
        reference_levels,
        key_off_frame=key_off_frame,
        sustain_while_keyed=sustain_while_keyed,
        counter_at_onset=counter_at_onset,
        peak_level=peak_level,
        preserve_significant_directions=preserve_significant_directions,
        prediction_transforms=(prediction_transform,),
    )[0]


@lru_cache(maxsize=8192)
def _fit_envelope_cached(
        reference_levels: tuple[int, ...], key_off_frame: int | None,
        sustain_while_keyed: bool, counter_at_onset: int,
        peak_level: int | None, preserve_significant_directions: bool,
) -> EnvelopeFit:
    return fit_envelope_variants(
        reference_levels,
        key_off_frame=key_off_frame,
        sustain_while_keyed=sustain_while_keyed,
        counter_at_onset=counter_at_onset,
        peak_level=peak_level,
        preserve_significant_directions=preserve_significant_directions,
        prediction_transforms=(None,),
    )[0]


def fit_envelope_variants(
    reference_levels: Sequence[int],
    *,
    key_off_frame: int | None,
    sustain_while_keyed: bool,
    counter_at_onset: int = 1,
    peak_level: int | None = None,
    preserve_significant_directions: bool = False,
    prediction_transforms: Sequence[
        Callable[[tuple[int, ...]], tuple[int, ...]] | None
    ],
) -> tuple[EnvelopeFit, ...]:
    """Fit several transforms while simulating each envelope packet once."""
    reference = tuple(reference_levels)
    if not reference or any(
            not isinstance(level, int) or not 0 <= level <= 15
            for level in reference):
        raise ValueError("reference_levels must be a nonempty 0..15 sequence")
    if peak_level is not None and not 1 <= peak_level <= 15:
        raise ValueError("peak_level must be 1..15")
    transforms = tuple(prediction_transforms)
    if not transforms:
        raise ValueError("prediction_transforms must be nonempty")

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

    best: list[EnvelopeFit | None] = [None] * len(transforms)
    best_score: list[tuple[int, ...] | None] = [None] * len(transforms)
    for peak in sorted(peak_candidates):
        # Many parameter tuples collapse to the same short 4-bit trace (for
        # example, every release rate is irrelevant after an immediate
        # release has already reached zero).  Scoring those duplicates is the
        # dominant cost on complete packs.  Keep the tuple which would win the
        # existing deterministic parameter tie-break, then score each exact
        # prediction once.  This changes neither the candidate set nor the
        # selected fit.
        predictions: dict[
            tuple[int, ...],
            tuple[tuple[int, ...], int, int, int, int],
        ] = {}
        for sustain in range(peak + 1):
            for attack_index, attack in enumerate(RATE_PERIODS):
                for decay_index, decay in enumerate(RATE_PERIODS):
                    for release_index, release in enumerate(RATE_PERIODS):
                        envelope_prediction = simulate_envelope(
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
                        parameter_order = (
                            attack_index + decay_index + release_index,
                            sustain, attack_index, decay_index, release_index,
                        )
                        previous = predictions.get(envelope_prediction)
                        if previous is None or parameter_order < previous[0]:
                            predictions[envelope_prediction] = (
                                parameter_order, sustain, attack, decay,
                                release,
                            )
        for envelope_prediction, candidate in predictions.items():
            parameter_order, sustain, attack, decay, release = candidate
            for variant, transform in enumerate(transforms):
                predicted = (
                    transform(envelope_prediction)
                    if transform is not None else envelope_prediction
                )
                if len(predicted) != len(reference) or any(
                        not isinstance(level, int) or not 0 <= level <= 15
                        for level in predicted):
                    raise ValueError(
                        "prediction_transform returned invalid levels"
                    )
                differences = tuple(
                    actual - expected for actual, expected in zip(
                        predicted, reference,
                    )
                )
                squared = sum(value * value for value in differences)
                absolute = sum(abs(value) for value in differences)
                maximum = max(abs(value) for value in differences)
                score = (
                    direction_mismatches(predicted),
                    squared, absolute, maximum,
                    parameter_order[0], peak, sustain,
                    parameter_order[2], parameter_order[3],
                    parameter_order[4],
                )
                if best_score[variant] is None or score < best_score[variant]:
                    best_score[variant] = score
                    best[variant] = EnvelopeFit(
                        peak, sustain, attack, decay, release,
                        sustain_while_keyed, predicted,
                        squared, absolute, maximum,
                    )
    assert all(item is not None for item in best)
    return tuple(item for item in best if item is not None)


def envelope_directions(reference: Sequence[int], predicted: Sequence[int],
                        key_off_frame: int | None) -> dict:
    """Compare significant net ADSR directions after 4-bit quantization."""
    if not reference or len(reference) != len(predicted):
        raise ValueError("envelope direction traces must have equal nonzero length")
    if key_off_frame is not None and not 0 <= key_off_frame < len(reference):
        raise ValueError("key_off_frame must be inside direction traces")
    # `simulate_envelope` applies key-off while producing the sample at
    # `key_off_frame`, so that sample belongs to release, not to the keyed
    # decay interval.  Including it here lets an otherwise flat held envelope
    # masquerade as a decay merely because an immediate release reaches zero.
    keyed_end = (
        max(0, key_off_frame - 1)
        if key_off_frame is not None else len(reference) - 1
    )
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


def significant_rearticulations(
    levels: Sequence[int], key_off_frame: int | None, *,
    threshold: int = SIGNIFICANT_REARTICULATION_LEVELS,
) -> int:
    """Count keyed rises which one compact ADSR cannot represent.

    A JPS2 envelope can attack once and then only hold or fall.  Some OPL
    logical voices combine same-pitch layers whose attacks are staggered, or
    change audible operator parameters while the key remains held.  Once the
    source has fallen by ``threshold`` levels, a renewed rise by the same
    amount is therefore a distinct articulation which a single fitted packet
    cannot reproduce.  The four-level default is deliberately above the
    largest three-level target tremolo depth.
    """
    values = tuple(levels)
    if not values or any(
            not isinstance(level, int) or not 0 <= level <= 15
            for level in values):
        raise ValueError("envelope levels must be a nonempty 0..15 sequence")
    if key_off_frame is not None and not 0 <= key_off_frame < len(values):
        raise ValueError("key_off_frame must be inside envelope levels")
    if not isinstance(threshold, int) or not 1 <= threshold <= 15:
        raise ValueError("rearticulation threshold must be 1..15")

    keyed = values[:key_off_frame] if key_off_frame is not None else values
    if len(keyed) < 3:
        return 0
    peak = keyed[0]
    trough = keyed[0]
    waiting_for_rise = False
    count = 0
    for level in keyed[1:]:
        if waiting_for_rise:
            trough = min(trough, level)
            if level - trough >= threshold:
                count += 1
                peak = level
                waiting_for_rise = False
        else:
            peak = max(peak, level)
            if peak - level >= threshold:
                trough = level
                waiting_for_rise = True
    return count


def significant_rearticulation_frames(
    levels: Sequence[int], key_off_frame: int | None, *,
    threshold: int = SIGNIFICANT_REARTICULATION_LEVELS,
) -> tuple[int, ...]:
    """Return the first rising frame of each significant keyed re-attack."""
    values = tuple(levels)
    # Reuse the public validation and keep both diagnostics definitionally
    # aligned even when no re-articulation exists.
    significant_rearticulations(values, key_off_frame, threshold=threshold)
    keyed = values[:key_off_frame] if key_off_frame is not None else values
    if len(keyed) < 3:
        return ()
    peak = keyed[0]
    trough = keyed[0]
    rise_start: int | None = None
    waiting_for_rise = False
    result = []
    for index, level in enumerate(keyed[1:], 1):
        if waiting_for_rise:
            if level < trough:
                trough = level
                rise_start = None
            elif level > trough and rise_start is None:
                rise_start = index
            if level - trough >= threshold:
                result.append(rise_start if rise_start is not None else index)
                peak = level
                waiting_for_rise = False
                rise_start = None
        else:
            peak = max(peak, level)
            if peak - level >= threshold:
                trough = level
                waiting_for_rise = True
    return tuple(result)


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
