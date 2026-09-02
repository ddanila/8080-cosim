"""Event-stream and probe helpers for the host-only Nuked OPL3 oracle."""

from __future__ import annotations

import csv
import struct
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import opl_trace


VGM_RATE = 44_100


@dataclass(frozen=True)
class OracleProbe:
    sample: int
    f_number: int
    block: int
    key: bool
    modulator_attenuation: int
    carrier_attenuation: int
    modulator_output_attenuation: int
    carrier_output_attenuation: int
    connection: int
    modulator_am: bool
    carrier_am: bool
    modulator_vibrato: bool
    carrier_vibrato: bool
    modulator_vibrato_f_number: int
    carrier_vibrato_f_number: int
    modulator_stage: int
    carrier_stage: int
    vibrato_phase: int
    tremolo_phase: int
    tremolo_value: int


@dataclass(frozen=True)
class OracleChannelProbe:
    channel: int
    probe: OracleProbe


@dataclass(frozen=True)
class IsolatedWrite:
    """A rebased register write produced by :func:`isolate_note_writes`."""

    sample: int
    bank: int
    register: int
    value: int


def _write_channel(write: opl_trace.TimedWrite) -> tuple[int, int] | None:
    if 0xA0 <= write.register <= 0xA8:
        return write.bank, write.register - 0xA0
    if 0xB0 <= write.register <= 0xB8:
        return write.bank, write.register - 0xB0
    if 0xC0 <= write.register <= 0xC8:
        return write.bank, write.register - 0xC0
    decoded = opl_trace.operator_address(write.register)
    return None if decoded is None else (write.bank, decoded[1])


def isolate_note_writes(
        writes: Iterable[opl_trace.TimedWrite],
        spans: Iterable[tuple[int, int, int, int]],
        window_start: int, window_end: int,
) -> list[IsolatedWrite]:
    """Extract exact OPL state for selected keyed spans.

    ``spans`` contains ``(bank, channel, start, end)`` tuples in original VGM
    sample time.  All operator, frequency, feedback/connection, waveform and
    LFO-depth writes for those physical channels are retained.  B0 key bits
    are admitted only while a selected span is active, and BD hardware-rhythm
    trigger bits are cleared, so the resulting stream contains no unrelated
    notes or percussion.

    Writes before ``window_start`` are collapsed into a state-prime at sample
    zero with keys off.  This makes late-song excerpts reproducible without
    replaying the whole composition or restarting an envelope in mid-note.
    Callers should therefore choose a window no later than the selected onset.
    """
    ordered = list(writes)
    selected_spans = tuple(spans)
    if window_start < 0 or window_end <= window_start:
        raise ValueError("invalid isolated OPL window")
    if any(
            not (0 <= bank <= 1 and 0 <= channel < 9 and
                 window_start <= start < end <= window_end)
            for bank, channel, start, end in selected_spans):
        raise ValueError("selected OPL span is outside the isolation window")
    channels = {(bank, channel) for bank, channel, _start, _end
                in selected_spans}
    if not channels:
        raise ValueError("no OPL spans selected")
    by_channel: dict[tuple[int, int], list[tuple[int, int]]] = {}
    for bank, channel, start, end in selected_spans:
        by_channel.setdefault((bank, channel), []).append((start, end))

    def relevant(write: opl_trace.TimedWrite) -> bool:
        return (
            (write.bank == 0 and write.register in (0x01, 0x08, 0xBD)) or
            (write.bank == 1 and write.register in (0x04, 0x05)) or
            _write_channel(write) in channels
        )

    def isolated_value(write: opl_trace.TimedWrite, *, prime: bool) -> int:
        if write.bank == 0 and write.register == 0xBD:
            # Preserve global AM/vibrato depth but never leak rhythm voices.
            return write.value & 0xC0
        target = _write_channel(write)
        if target in channels and 0xB0 <= write.register <= 0xB8:
            keyed = not prime and any(
                start <= write.sample < end
                for start, end in by_channel[target]
            )
            return (write.value | 0x20) if keyed and write.value & 0x20 \
                else (write.value & ~0x20)
        return write.value

    previous_sample = -1
    primed: dict[tuple[int, int], tuple[int, IsolatedWrite]] = {}
    live: list[tuple[int, IsolatedWrite]] = []
    for sequence, write in enumerate(ordered):
        if write.sample < previous_sample:
            raise ValueError("OPL writes are not in timestamp order")
        previous_sample = write.sample
        if not relevant(write) or write.sample >= window_end:
            continue
        if write.sample < window_start:
            value = isolated_value(write, prime=True)
            primed[(write.bank, write.register)] = (
                sequence, IsolatedWrite(0, write.bank, write.register, value),
            )
        else:
            value = isolated_value(write, prime=False)
            live.append((sequence, IsolatedWrite(
                write.sample - window_start, write.bank,
                write.register, value,
            )))
    return [item for _sequence, item in sorted(primed.values())] + [
        item for _sequence, item in live
    ]


def channel_write(write: opl_trace.TimedWrite, bank: int, channel: int) -> bool:
    """Whether a write affects the selected two-operator channel or globals."""
    if write.bank == 0 and write.register in (0x01, 0x08, 0xBD):
        return True
    if write.bank == 1 and write.register in (0x04, 0x05):
        return True
    if write.bank != bank:
        return False
    if write.register in (0xA0 + channel, 0xB0 + channel, 0xC0 + channel):
        return True
    decoded = opl_trace.operator_address(write.register)
    return decoded is not None and decoded[1] == channel


def write_event_stream(path: Path, writes: Iterable[opl_trace.TimedWrite],
                       total_samples: int, *, sample_rate: int = VGM_RATE,
                       selected_channel: tuple[int, int] | None = None) -> int:
    selected = [
        write for write in writes
        if selected_channel is None or channel_write(
            write, selected_channel[0], selected_channel[1],
        )
    ]
    if total_samples <= 0 or not 8000 <= sample_rate <= 192000:
        raise ValueError("invalid oracle duration or sample rate")
    previous = 0
    for write in selected:
        if write.sample < previous or write.sample >= total_samples:
            raise ValueError("oracle writes must be ordered inside the duration")
        previous = write.sample
    with path.open("wb") as output:
        output.write(struct.pack(
            "<4sIII", b"JOP\1", total_samples, sample_rate, len(selected),
        ))
        for write in selected:
            output.write(struct.pack(
                "<IHBx", write.sample,
                write.register | write.bank << 8, write.value,
            ))
    return len(selected)


def read_probes(path: Path) -> list[OracleProbe]:
    with path.open(newline="") as source:
        rows = csv.DictReader(source)
        expected = list(OracleProbe.__dataclass_fields__)
        if rows.fieldnames != expected:
            raise ValueError(f"unexpected oracle probe columns: {rows.fieldnames}")
        return [OracleProbe(
            sample=int(row["sample"]),
            f_number=int(row["f_number"]),
            block=int(row["block"]),
            key=bool(int(row["key"])),
            modulator_attenuation=int(row["modulator_attenuation"]),
            carrier_attenuation=int(row["carrier_attenuation"]),
            modulator_output_attenuation=int(
                row["modulator_output_attenuation"]
            ),
            carrier_output_attenuation=int(
                row["carrier_output_attenuation"]
            ),
            connection=int(row["connection"]),
            modulator_am=bool(int(row["modulator_am"])),
            carrier_am=bool(int(row["carrier_am"])),
            modulator_vibrato=bool(int(row["modulator_vibrato"])),
            carrier_vibrato=bool(int(row["carrier_vibrato"])),
            modulator_vibrato_f_number=int(
                row["modulator_vibrato_f_number"]
            ),
            carrier_vibrato_f_number=int(
                row["carrier_vibrato_f_number"]
            ),
            modulator_stage=int(row["modulator_stage"]),
            carrier_stage=int(row["carrier_stage"]),
            vibrato_phase=int(row["vibrato_phase"]),
            tremolo_phase=int(row["tremolo_phase"]),
            tremolo_value=int(row["tremolo_value"]),
        ) for row in rows]


def read_channel_probes(path: Path) -> list[OracleChannelProbe]:
    """Read the oracle's one-pass, all-18-channel probe form."""
    with path.open(newline="") as source:
        rows = csv.DictReader(source)
        expected = ["channel", *OracleProbe.__dataclass_fields__]
        if rows.fieldnames != expected:
            raise ValueError(
                f"unexpected all-channel oracle probe columns: {rows.fieldnames}"
            )
        result = []
        for row in rows:
            channel = int(row.pop("channel"))
            if not 0 <= channel < 18:
                raise ValueError(f"invalid oracle channel: {channel}")
            probe = OracleProbe(
                sample=int(row["sample"]),
                f_number=int(row["f_number"]),
                block=int(row["block"]),
                key=bool(int(row["key"])),
                modulator_attenuation=int(row["modulator_attenuation"]),
                carrier_attenuation=int(row["carrier_attenuation"]),
                modulator_output_attenuation=int(
                    row["modulator_output_attenuation"]
                ),
                carrier_output_attenuation=int(
                    row["carrier_output_attenuation"]
                ),
                connection=int(row["connection"]),
                modulator_am=bool(int(row["modulator_am"])),
                carrier_am=bool(int(row["carrier_am"])),
                modulator_vibrato=bool(int(row["modulator_vibrato"])),
                carrier_vibrato=bool(int(row["carrier_vibrato"])),
                modulator_vibrato_f_number=int(
                    row["modulator_vibrato_f_number"]
                ),
                carrier_vibrato_f_number=int(
                    row["carrier_vibrato_f_number"]
                ),
                modulator_stage=int(row["modulator_stage"]),
                carrier_stage=int(row["carrier_stage"]),
                vibrato_phase=int(row["vibrato_phase"]),
                tremolo_phase=int(row["tremolo_phase"]),
                tremolo_value=int(row["tremolo_value"]),
            )
            result.append(OracleChannelProbe(channel, probe))
        return result


def read_pcm(path: Path) -> list[tuple[int, int]]:
    payload = path.read_bytes()
    if len(payload) % 4:
        raise ValueError("oracle PCM is not stereo signed-16 little-endian")
    return list(struct.iter_unpack("<hh", payload))
