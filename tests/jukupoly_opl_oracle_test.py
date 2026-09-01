#!/usr/bin/env python3
"""Agreement checks between the semantic trace and pinned Nuked OPL3."""

from __future__ import annotations

import hashlib
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
import jukupoly_opl_trace_test as synthetic  # noqa: E402
import opl_oracle  # noqa: E402
import opl_vibrato  # noqa: E402


def render(tool: Path, writes: list, total_samples: int,
           directory: Path, name: str) -> tuple[list, list, str]:
    stream = directory / f"{name}.jop"
    pcm_path = directory / f"{name}.s16le"
    probes_path = directory / f"{name}.csv"
    count = opl_oracle.write_event_stream(
        stream, writes, total_samples, selected_channel=(0, 0),
    )
    result = subprocess.run(
        [str(tool), str(stream), str(pcm_path), str(probes_path), "0"],
        check=True, text=True, stdout=subprocess.PIPE,
    )
    assert f"writes={count}" in result.stdout
    return (opl_oracle.read_pcm(pcm_path),
            opl_oracle.read_probes(probes_path),
            hashlib.sha256(pcm_path.read_bytes()).hexdigest())


def check_oracle_agreement(tool: Path) -> None:
    info, writes = vgz.parse_vgm(synthetic.synthetic_opl3_vgm())
    timeline = __import__("opl_trace").OplTimeline(info.banks)
    timeline.apply_all(writes)

    with tempfile.TemporaryDirectory(prefix="jukupoly-opl-oracle.") as name:
        directory = Path(name)
        pcm, probes, digest = render(
            tool, writes, info.total_samples, directory, "modulated",
        )
        assert len(pcm) == info.total_samples
        assert any(left or right for left, right in pcm)
        assert any(left or right for left, right in pcm[982:])
        assert len(digest) == 64

        by_sample = {probe.sample: probe for probe in probes}
        assert {0, 882, 1764, 1864} <= by_sample.keys()
        assert by_sample[0].f_number == 0x234
        assert by_sample[0].block == 4 and by_sample[0].key
        assert by_sample[882].f_number == 0x240 and by_sample[882].key
        assert not by_sample[1764].key
        assert timeline.channel(0, 0).f_number == by_sample[1764].f_number
        assert timeline.channel(0, 0).block == by_sample[1764].block
        assert timeline.channel(0, 0).key_on == by_sample[1764].key

        # Nuked's carrier envelope has left reset attenuation during the held
        # note, then remains in a release tail after the exact key-off sample.
        assert by_sample[882].carrier_attenuation < by_sample[0].carrier_attenuation
        assert by_sample[1764].carrier_attenuation >= by_sample[882].carrier_attenuation
        assert by_sample[882].carrier_output_attenuation >= \
            by_sample[882].carrier_attenuation
        assert by_sample[882].modulator_output_attenuation >= \
            by_sample[882].modulator_attenuation
        assert by_sample[882].connection == timeline.channel(0, 0).connection
        assert by_sample[882].modulator_am == timeline.channel(0, 0).modulator.am
        assert by_sample[882].carrier_am == timeline.channel(0, 0).carrier.am
        assert by_sample[882].modulator_vibrato
        assert not by_sample[882].carrier_vibrato
        for probe in probes:
            expected = probe.f_number + opl_vibrato.opl_f_number_delta(
                probe.f_number, probe.vibrato_phase, deep=True,
            )
            assert probe.modulator_vibrato_f_number == expected
            assert probe.carrier_vibrato_f_number == probe.f_number

        # The shared OPL LFOs run independently of note events.  Their oracle
        # phases and tremolo value must progress across our 50 Hz probes.
        assert len({probe.vibrato_phase for probe in probes}) > 1
        assert len({probe.tremolo_phase for probe in probes}) > 1
        assert len({probe.tremolo_value for probe in probes}) > 1

        unmodulated = [
            vgz.RegisterWrite(write.sample, write.bank, write.register,
                              write.value & 0x3F)
            if write.bank == 0 and write.register in (0x20, 0x23)
            else write
            for write in writes
        ]
        _pcm2, _probes2, plain_digest = render(
            tool, unmodulated, info.total_samples, directory, "unmodulated",
        )
        assert plain_digest != digest

        stream = directory / "all.jop"
        all_pcm = directory / "all.s16le"
        all_csv = directory / "all.csv"
        opl_oracle.write_event_stream(stream, writes, info.total_samples)
        subprocess.run(
            [str(tool), str(stream), str(all_pcm), str(all_csv), "all"],
            check=True, text=True, stdout=subprocess.PIPE,
        )
        all_probes = opl_oracle.read_channel_probes(all_csv)
        assert len(all_probes) == len(probes) * 18
        channel_zero = [item.probe for item in all_probes if item.channel == 0]
        assert channel_zero == probes

        discard_csv = directory / "discard.csv"
        discarded = subprocess.run(
            [str(tool), str(stream), "-", str(discard_csv), "all"],
            check=True, text=True, stdout=subprocess.PIPE,
        )
        assert "nonzero=" in discarded.stdout
        assert opl_oracle.read_channel_probes(discard_csv) == all_probes


def check_channel_filter() -> None:
    assert opl_oracle.channel_write(vgz.RegisterWrite(0, 0, 0x20, 1), 0, 0)
    assert opl_oracle.channel_write(vgz.RegisterWrite(0, 0, 0x23, 1), 0, 0)
    assert not opl_oracle.channel_write(vgz.RegisterWrite(0, 0, 0x21, 1), 0, 0)
    assert opl_oracle.channel_write(vgz.RegisterWrite(0, 0, 0xBD, 1), 0, 0)
    assert opl_oracle.channel_write(vgz.RegisterWrite(0, 1, 0x05, 1), 0, 0)


def main() -> int:
    value = os.environ.get("JUKUPOLY_OPL_ORACLE")
    if not value:
        raise SystemExit("JUKUPOLY_OPL_ORACLE is not set")
    tool = Path(value)
    if not tool.is_file():
        raise SystemExit(f"oracle executable is missing: {tool}")
    check_channel_filter()
    check_oracle_agreement(tool)
    print("JUKUPOLY-OPL-ORACLE: PASS pinned-nuked key-pitch-envelope-lfo "
          "exact-vibrato-fnum release-tail channel-isolation")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
