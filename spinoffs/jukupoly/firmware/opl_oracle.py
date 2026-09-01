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
    modulator_stage: int
    carrier_stage: int
    vibrato_phase: int
    tremolo_phase: int
    tremolo_value: int


@dataclass(frozen=True)
class OracleChannelProbe:
    channel: int
    probe: OracleProbe


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
