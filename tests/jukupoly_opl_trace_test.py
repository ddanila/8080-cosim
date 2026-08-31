#!/usr/bin/env python3
"""Synthetic-register regression for the host-side OPL semantic timeline."""

from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FIRMWARE = ROOT / "spinoffs" / "jukupoly" / "firmware"
sys.path.insert(0, str(FIRMWARE))

import import_jukupoly_vgz as vgz  # noqa: E402
import opl_trace  # noqa: E402


def write_u32(data: bytearray, offset: int, value: int) -> None:
    data[offset:offset + 4] = value.to_bytes(4, "little")


def synthetic_opl3_vgm() -> bytes:
    commands = bytearray()

    def port0(register: int, value: int) -> None:
        commands.extend((0x5E, register, value))

    def port1(register: int, value: int) -> None:
        commands.extend((0x5F, register, value))

    port1(0x05, 0x01)       # OPL3 new mode
    port1(0x04, 0x01)       # bank-0 channels 0+3 form a four-op pair
    port0(0xBD, 0xFF)       # deep AM/VIB, rhythm enabled, all five drums

    port0(0x20, 0xF3)       # modulator: AM, VIB, EGT, KSR, MULT=3
    port0(0x40, 0x95)       # KSL=2, TL=21
    port0(0x60, 0xA4)       # AR=10, DR=4
    port0(0x80, 0xB6)       # SL=11, RR=6
    port0(0xE0, 0x07)       # waveform 7

    port0(0x23, 0x21)       # carrier: EGT, MULT=1
    port0(0x43, 0x07)       # carrier TL=7
    port0(0x63, 0x52)       # carrier AR=5, DR=2
    port0(0x83, 0x34)       # carrier SL=3, RR=4
    port0(0xE3, 0x02)       # carrier waveform 2

    port0(0xC0, 0xFB)       # all stereo outputs, feedback=5, additive
    port0(0xA0, 0x34)
    port0(0xB0, 0x32)       # FNUM high=2, block=4, key on
    commands.append(0x63)    # one 50 Hz VGM wait, 882 samples
    port0(0xA0, 0x40)       # live pitch write while key remains on
    commands.extend((0x61, 100, 0))
    port0(0xB0, 0x12)       # key off, retain pitch and block
    commands.append(0x63)
    commands.append(0x66)

    total_samples = 882 + 100 + 882
    header = bytearray(0x80)
    header[:4] = b"Vgm "
    write_u32(header, 0x04, len(header) + len(commands) - 4)
    write_u32(header, 0x08, 0x00000171)
    write_u32(header, 0x18, total_samples)
    write_u32(header, 0x34, 0x80 - 0x34)
    write_u32(header, 0x5C, 14_318_180)
    return bytes(header + commands)


def check_timed_semantics() -> None:
    info, writes = vgz.parse_vgm(synthetic_opl3_vgm())
    assert info.banks == 2
    assert info.total_samples == 1864
    assert [write.sample for write in writes[-3:]] == [0, 882, 982]

    timeline = opl_trace.OplTimeline(info.banks)
    keyed_state = None
    for write in writes:
        event = timeline.apply(write)
        if event.key_transition == "key_on":
            keyed_state = timeline.channel(0, 0)

    assert keyed_state is not None
    assert keyed_state.f_number == 0x234
    assert keyed_state.block == 4
    assert keyed_state.key_on
    assert keyed_state.feedback == 5
    assert keyed_state.connection == 1
    assert (keyed_state.stereo_a, keyed_state.stereo_b,
            keyed_state.stereo_c, keyed_state.stereo_d) == (True,) * 4
    assert keyed_state.four_operator_role == "primary"
    assert keyed_state.four_operator_pair == 0

    modulator = keyed_state.modulator
    assert (modulator.am, modulator.vibrato, modulator.envelope_sustain,
            modulator.key_scale_rate) == (True,) * 4
    assert modulator.multiplier_code == 3
    assert modulator.key_scale_level == 2
    assert modulator.total_level == 21
    assert (modulator.attack_rate, modulator.decay_rate,
            modulator.sustain_level, modulator.release_rate) == (10, 4, 11, 6)
    assert modulator.waveform == 7

    carrier = keyed_state.carrier
    assert carrier.envelope_sustain
    assert carrier.total_level == 7
    assert (carrier.attack_rate, carrier.decay_rate,
            carrier.sustain_level, carrier.release_rate) == (5, 2, 3, 4)
    assert carrier.waveform == 2

    global_state = timeline.global_state()
    assert global_state.opl3_enabled
    assert global_state.four_operator_mask == 1
    assert global_state.tremolo_deep and global_state.vibrato_deep
    assert global_state.rhythm_enabled
    assert (global_state.bass_drum, global_state.snare_drum,
            global_state.tom_tom, global_state.cymbal,
            global_state.hi_hat) == (True,) * 5

    kinds = [event.kind for event in timeline.events]
    assert kinds.count("key_on") == 1
    assert kinds.count("key_off") == 1
    assert kinds.count("pitch") == 2
    live_pitch = [event for event in timeline.events
                  if event.sample == 882 and event.register == 0xA0]
    assert len(live_pitch) == 1 and live_pitch[0].previous == 0x34
    assert not timeline.channel(0, 0).key_on
    assert timeline.channel(0, 0).f_number == 0x240


def check_lossless_document() -> None:
    info, writes = vgz.parse_vgm(synthetic_opl3_vgm())
    document = opl_trace.trace_document(writes, info.banks, info.total_samples)
    assert document["schema"] == "jukupoly-opl-register-trace-v1"
    assert document["writes"] == len(writes)
    assert len(document["events"]) == len(writes)
    assert [event["sequence"] for event in document["events"]] == list(
        range(len(writes))
    )
    same_sample = [event for event in document["events"] if event["sample"] == 0]
    assert [event["sequence"] for event in same_sample] == list(range(len(same_sample)))
    assert len(document["registers_final"]) == 2
    assert len(document["registers_final"][0]) == 512
    assert document["registers_final"][0][2 * 0x20:2 * 0x20 + 2] == "f3"
    json.dumps(document)


def check_validation() -> None:
    assert opl_trace.operator_address(0x20) == (0x20, 0, 0)
    assert opl_trace.operator_address(0x23) == (0x20, 0, 1)
    assert opl_trace.operator_address(0x26) is None
    timeline = opl_trace.OplTimeline(1)
    try:
        timeline.apply(vgz.RegisterWrite(0, 1, 0x20, 0))
    except ValueError as exc:
        assert "absent OPL bank" in str(exc)
    else:
        raise AssertionError("bank-1 write accepted by OPL2 timeline")


def main() -> int:
    check_timed_semantics()
    check_lossless_document()
    check_validation()
    print("JUKUPOLY-OPL-TRACE: PASS timed-registers operators envelopes "
          "lfo-depth rhythm four-op key-and-pitch-transitions")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
