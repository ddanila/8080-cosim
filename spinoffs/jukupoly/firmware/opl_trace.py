"""Lossless timed OPL2/OPL3 register state with decoded musical semantics.

This is deliberately a host-side model.  It records every register write and
decodes the state needed by the JukuPoly reducer; it does not synthesize audio
and is not intended for the 8080 target.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import asdict, dataclass
from typing import Iterable, Protocol


OPERATOR_OFFSETS = (0, 1, 2, 8, 9, 10, 16, 17, 18)
OPERATOR_TO_CHANNEL = {
    offset: (channel, operator)
    for channel, modulator in enumerate(OPERATOR_OFFSETS)
    for offset, operator in ((modulator, 0), (modulator + 3, 1))
}
OPERATOR_BASES = (0x20, 0x40, 0x60, 0x80, 0xE0)


class TimedWrite(Protocol):
    sample: int
    bank: int
    register: int
    value: int


@dataclass(frozen=True)
class OperatorState:
    am: bool
    vibrato: bool
    envelope_sustain: bool
    key_scale_rate: bool
    multiplier_code: int
    key_scale_level: int
    total_level: int
    attack_rate: int
    decay_rate: int
    sustain_level: int
    release_rate: int
    waveform: int


@dataclass(frozen=True)
class ChannelState:
    bank: int
    channel: int
    f_number: int
    block: int
    key_on: bool
    feedback: int
    connection: int
    stereo_a: bool
    stereo_b: bool
    stereo_c: bool
    stereo_d: bool
    four_operator_role: str
    four_operator_pair: int | None
    modulator: OperatorState
    carrier: OperatorState


@dataclass(frozen=True)
class GlobalState:
    tremolo_deep: bool
    vibrato_deep: bool
    rhythm_enabled: bool
    bass_drum: bool
    snare_drum: bool
    tom_tom: bool
    cymbal: bool
    hi_hat: bool
    opl3_enabled: bool
    four_operator_mask: int


@dataclass(frozen=True)
class TraceEvent:
    sample: int
    sequence: int
    bank: int
    register: int
    previous: int
    value: int
    kind: str
    channel: int | None
    operator: int | None
    key_transition: str | None


def operator_address(register: int) -> tuple[int, int, int] | None:
    """Return (base, channel, operator-index) for an operator register."""
    for base in OPERATOR_BASES:
        if base <= register <= base + 0x15:
            slot = register - base
            mapped = OPERATOR_TO_CHANNEL.get(slot)
            if mapped is not None:
                return base, mapped[0], mapped[1]
    return None


class OplTimeline:
    """Mutable raw register file plus ordered semantic write events."""

    def __init__(self, banks: int) -> None:
        if banks not in (1, 2):
            raise ValueError(f"OPL bank count must be 1 or 2, got {banks}")
        self.banks = banks
        self.registers = [[0] * 256 for _ in range(2)]
        self.events: list[TraceEvent] = []
        self._last_sample = 0

    def operator(self, bank: int, channel: int, operator: int) -> OperatorState:
        if not 0 <= bank < self.banks or not 0 <= channel < 9:
            raise ValueError("invalid OPL bank/channel")
        if operator not in (0, 1):
            raise ValueError("operator index must be 0 or 1")
        offset = OPERATOR_OFFSETS[channel] + 3 * operator
        reg20 = self.registers[bank][0x20 + offset]
        reg40 = self.registers[bank][0x40 + offset]
        reg60 = self.registers[bank][0x60 + offset]
        reg80 = self.registers[bank][0x80 + offset]
        reg_e0 = self.registers[bank][0xE0 + offset]
        return OperatorState(
            am=bool(reg20 & 0x80),
            vibrato=bool(reg20 & 0x40),
            envelope_sustain=bool(reg20 & 0x20),
            key_scale_rate=bool(reg20 & 0x10),
            multiplier_code=reg20 & 0x0F,
            key_scale_level=reg40 >> 6,
            total_level=reg40 & 0x3F,
            attack_rate=reg60 >> 4,
            decay_rate=reg60 & 0x0F,
            sustain_level=reg80 >> 4,
            release_rate=reg80 & 0x0F,
            waveform=reg_e0 & 0x07,
        )

    def _four_operator(self, bank: int, channel: int) -> tuple[str, int | None]:
        if channel < 3:
            pair = bank * 3 + channel
            if self.registers[1][0x04] & (1 << pair):
                return "primary", pair
        elif channel < 6:
            pair = bank * 3 + channel - 3
            if self.registers[1][0x04] & (1 << pair):
                return "secondary", pair
        return "none", None

    def channel(self, bank: int, channel: int) -> ChannelState:
        if not 0 <= bank < self.banks or not 0 <= channel < 9:
            raise ValueError("invalid OPL bank/channel")
        reg_b0 = self.registers[bank][0xB0 + channel]
        reg_c0 = self.registers[bank][0xC0 + channel]
        role, pair = self._four_operator(bank, channel)
        return ChannelState(
            bank=bank,
            channel=channel,
            f_number=(self.registers[bank][0xA0 + channel] |
                      (reg_b0 & 0x03) << 8),
            block=(reg_b0 >> 2) & 0x07,
            key_on=bool(reg_b0 & 0x20),
            feedback=(reg_c0 >> 1) & 0x07,
            connection=reg_c0 & 0x01,
            stereo_a=bool(reg_c0 & 0x10),
            stereo_b=bool(reg_c0 & 0x20),
            stereo_c=bool(reg_c0 & 0x40),
            stereo_d=bool(reg_c0 & 0x80),
            four_operator_role=role,
            four_operator_pair=pair,
            modulator=self.operator(bank, channel, 0),
            carrier=self.operator(bank, channel, 1),
        )

    def global_state(self) -> GlobalState:
        rhythm = self.registers[0][0xBD]
        return GlobalState(
            tremolo_deep=bool(rhythm & 0x80),
            vibrato_deep=bool(rhythm & 0x40),
            rhythm_enabled=bool(rhythm & 0x20),
            bass_drum=bool(rhythm & 0x10),
            snare_drum=bool(rhythm & 0x08),
            tom_tom=bool(rhythm & 0x04),
            cymbal=bool(rhythm & 0x02),
            hi_hat=bool(rhythm & 0x01),
            opl3_enabled=bool(self.registers[1][0x05] & 0x01),
            four_operator_mask=self.registers[1][0x04] & 0x3F,
        )

    def apply(self, write: TimedWrite) -> TraceEvent:
        if not 0 <= write.bank < self.banks:
            raise ValueError(f"write uses absent OPL bank {write.bank}")
        if not 0 <= write.register <= 0xFF or not 0 <= write.value <= 0xFF:
            raise ValueError("OPL register and value must be bytes")
        if write.sample < self._last_sample:
            raise ValueError("OPL writes are not in timestamp order")
        self._last_sample = write.sample

        previous = self.registers[write.bank][write.register]
        self.registers[write.bank][write.register] = write.value
        kind = "raw"
        channel: int | None = None
        operator: int | None = None
        transition: str | None = None

        decoded = operator_address(write.register)
        if decoded is not None:
            _base, channel, operator = decoded
            kind = "operator"
        elif 0xA0 <= write.register <= 0xA8:
            channel = write.register - 0xA0
            kind = "pitch"
        elif 0xB0 <= write.register <= 0xB8:
            channel = write.register - 0xB0
            old_key = bool(previous & 0x20)
            new_key = bool(write.value & 0x20)
            if old_key != new_key:
                transition = "key_on" if new_key else "key_off"
                kind = transition
            else:
                kind = "pitch"
        elif 0xC0 <= write.register <= 0xC8:
            channel = write.register - 0xC0
            kind = "channel"
        elif (write.bank == 0 and write.register == 0xBD) or (
                write.bank == 1 and write.register in (0x04, 0x05)):
            kind = "global"

        event = TraceEvent(
            sample=write.sample,
            sequence=len(self.events),
            bank=write.bank,
            register=write.register,
            previous=previous,
            value=write.value,
            kind=kind,
            channel=channel,
            operator=operator,
            key_transition=transition,
        )
        self.events.append(event)
        return event

    def apply_all(self, writes: Iterable[TimedWrite]) -> None:
        for write in writes:
            self.apply(write)

    def document(self, total_samples: int) -> dict:
        if total_samples < self._last_sample:
            raise ValueError("trace duration precedes its final register write")
        counts = Counter(event.kind for event in self.events)
        active = [
            asdict(self.channel(bank, channel))
            for bank in range(self.banks)
            for channel in range(9)
            if self.channel(bank, channel).key_on
        ]
        return {
            "schema": "jukupoly-opl-register-trace-v1",
            "banks": self.banks,
            "total_samples": total_samples,
            "writes": len(self.events),
            "event_kinds": dict(sorted(counts.items())),
            "global_final": asdict(self.global_state()),
            "active_channels_final": active,
            "registers_final": [
                bytes(self.registers[bank]).hex() for bank in range(self.banks)
            ],
            "events": [asdict(event) for event in self.events],
        }


def trace_document(writes: Iterable[TimedWrite], banks: int,
                   total_samples: int) -> dict:
    timeline = OplTimeline(banks)
    timeline.apply_all(writes)
    return timeline.document(total_samples)
