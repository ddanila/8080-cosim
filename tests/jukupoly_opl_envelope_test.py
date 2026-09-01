#!/usr/bin/env python3
"""Host-side compact-envelope fitter and pinned-oracle regression."""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FIRMWARE = ROOT / "spinoffs" / "jukupoly" / "firmware"
sys.path.insert(0, str(FIRMWARE))
sys.path.insert(0, str(ROOT / "tests"))

import import_jukupoly_vgz as vgz  # noqa: E402
import build_jukupoly  # noqa: E402
import jukupoly_opl_trace_test as synthetic  # noqa: E402
import opl_envelope  # noqa: E402
import opl_oracle  # noqa: E402


def check_exact_target_fit() -> None:
    expected = opl_envelope.simulate_envelope(
        54,
        key_off_frame=30,
        peak_level=12,
        sustain_level=6,
        attack_period_frames=2,
        decay_period_frames=4,
        release_period_frames=2,
        sustain_while_keyed=True,
        counter_at_onset=9,
    )
    fitted = opl_envelope.fit_envelope(
        expected,
        key_off_frame=30,
        sustain_while_keyed=True,
        counter_at_onset=9,
    )
    assert fitted.predicted_levels == expected
    assert not fitted.squared_error and not fitted.maximum_error
    assert set(fitted.packet()) == {
        "peak_level", "sustain_level", "attack_period_frames",
        "decay_period_frames", "release_period_frames",
        "sustain_while_keyed",
    }
    build_jukupoly.encode_opl_envelope(fitted.packet(), "exact fit")

    percussive = opl_envelope.simulate_envelope(
        32,
        key_off_frame=None,
        peak_level=10,
        sustain_level=4,
        attack_period_frames=0,
        decay_period_frames=1,
        release_period_frames=2,
        sustain_while_keyed=False,
    )
    fitted = opl_envelope.fit_envelope(
        percussive, key_off_frame=None, sustain_while_keyed=False,
    )
    assert fitted.predicted_levels == percussive
    assert percussive[0] == 10 and percussive[-1] == 0


def check_semantic_attenuation_mapping() -> None:
    # 32 oracle attenuation units are 6 dB, approximately half amplitude.
    half = opl_envelope.opl_channel_amplitude(511, 32, 0)
    assert 0.49 < half < 0.51
    assert opl_envelope.quantize_opl_channel(
        (511, 511, 511), (511, 32, 0), (0, 0, 0),
    ) == (0, 8, 15)

    # Additive connection exposes both operators, but cannot exceed Juku's
    # single-channel full-scale mixer level.
    assert opl_envelope.opl_channel_amplitude(32, 32, 1) == 1.0
    assert opl_envelope.quantize_opl_channel(
        (32,), (32,), (1,), peak_level=12,
    ) == (12,)


def check_direction_priority() -> None:
    # Pure least squares can flatten a small but significant keyed decay.
    # The real-song policy ranks preservation of a >=2-level direction first.
    reference = (0, 14, 12, 12, 12, 12, 12, 12, 12, 12)
    unconstrained = opl_envelope.fit_envelope(
        reference, key_off_frame=None, sustain_while_keyed=True,
    )
    guarded = opl_envelope.fit_envelope(
        reference, key_off_frame=None, sustain_while_keyed=True,
        preserve_significant_directions=True,
    )
    before = opl_envelope.envelope_directions(
        reference, unconstrained.predicted_levels, None,
    )
    after = opl_envelope.envelope_directions(
        reference, guarded.predicted_levels, None,
    )
    assert before["mismatches"] == 1
    assert after["mismatches"] == 0


def stretched_oracle_source() -> tuple[list[vgz.RegisterWrite], int]:
    info, writes = vgz.parse_vgm(synthetic.synthetic_opl3_vgm())
    key_off_sample = 20 * opl_oracle.VGM_RATE // 50
    result = []
    for write in writes:
        sample = write.sample
        value = write.value
        if write.bank == 1 and write.register == 0x04:
            value = 0  # isolate an ordinary two-operator channel
        elif write.bank == 0 and write.register == 0xBD:
            value = 0  # no hardware rhythm routing in this fixture
        elif write.bank == 0 and write.register == 0xC0:
            value = 0xF0  # FM connection, carrier is the audible envelope
        if write.bank == 0 and write.register == 0x83:
            value = 0x04  # carrier SL=0 keeps an audible keyed plateau
        if (write.bank == 0 and write.register == 0xB0 and
                not write.value & 0x20):
            sample = key_off_sample
        result.append(vgz.RegisterWrite(
            sample, write.bank, write.register, value,
        ))
    result.sort(key=lambda write: write.sample)
    return result, 48 * opl_oracle.VGM_RATE // 50


def check_oracle_fit(tool: Path) -> opl_envelope.EnvelopeFit:
    writes, total_samples = stretched_oracle_source()
    with tempfile.TemporaryDirectory(prefix="jukupoly-envelope-fit.") as name:
        directory = Path(name)
        stream = directory / "source.jop"
        pcm_path = directory / "source.s16le"
        probes_path = directory / "source.csv"
        opl_oracle.write_event_stream(
            stream, writes, total_samples, selected_channel=(0, 0),
        )
        subprocess.run(
            [str(tool), str(stream), str(pcm_path), str(probes_path), "0"],
            check=True, stdout=subprocess.PIPE, text=True,
        )
        pcm = opl_oracle.read_pcm(pcm_path)
        reference = opl_envelope.quantize_isolated_pcm(
            pcm,
            start_sample=0,
            frames=48,
            peak_level=12,
            normalization_frames=20,
        )
        fitted = opl_envelope.fit_envelope(
            reference,
            key_off_frame=20,
            sustain_while_keyed=True,
            peak_level=12,
        )
        assert max(reference[:20]) == 12
        assert reference[-1] < reference[20]
        assert fitted.predicted_levels[0] <= fitted.predicted_levels[10]
        assert fitted.predicted_levels[-1] <= fitted.predicted_levels[20]
        assert fitted.maximum_error <= 6
        assert fitted.absolute_error / len(reference) <= 2.0
        build_jukupoly.encode_opl_envelope(fitted.packet(), "oracle fit")
        return fitted


def main() -> int:
    value = os.environ.get("JUKUPOLY_OPL_ORACLE")
    if not value:
        raise SystemExit("JUKUPOLY_OPL_ORACLE is not set")
    tool = Path(value)
    if not tool.is_file():
        raise SystemExit(f"oracle executable is missing: {tool}")
    check_exact_target_fit()
    check_semantic_attenuation_mapping()
    check_direction_priority()
    fitted = check_oracle_fit(tool)
    print("JUKUPOLY-OPL-ENVELOPE: PASS target-exact grid-fit "
          "oracle-rms 50Hz-4bit bounded-error "
          f"fit={fitted.packet()} mae={fitted.absolute_error / 48:.3f} "
          f"max={fitted.maximum_error}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
