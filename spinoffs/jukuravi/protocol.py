"""Wire-format primitives shared by Jukuravi firmware builders and host tools."""

from __future__ import annotations

from dataclasses import dataclass


SYNC = bytes((0xA5, 0x5A))
PROTOCOL_VERSION = 1
TYPE_BANNER = 0x01
TYPE_ACK = 0x81
MAX_PAYLOAD = 255


def crc8_atm(data: bytes) -> int:
    """CRC-8/ATM: poly=07, init=00, refin=false, xorout=00."""
    crc = 0
    for byte in data:
        crc ^= byte
        for _ in range(8):
            crc = ((crc << 1) ^ 0x07) & 0xFF if crc & 0x80 else crc << 1
    return crc


def crc16_ccitt_false(data: bytes) -> int:
    """CRC-16/CCITT-FALSE: poly=1021, init=FFFF, refin=false, xorout=0000."""
    crc = 0xFFFF
    for byte in data:
        crc ^= byte << 8
        for _ in range(8):
            crc = (
                ((crc << 1) ^ 0x1021) & 0xFFFF
                if crc & 0x8000
                else (crc << 1) & 0xFFFF
            )
    return crc


def encode_frame(record_type: int, payload: bytes) -> bytes:
    if not 0 <= record_type <= 0xFF:
        raise ValueError("record type is not one byte")
    if len(payload) > MAX_PAYLOAD:
        raise ValueError("payload is longer than one-byte length")
    body = bytes((record_type, len(payload))) + payload
    return SYNC + body + bytes((crc8_atm(body),))


@dataclass(frozen=True)
class Frame:
    record_type: int
    payload: bytes


class StreamDecoder:
    """Incremental decoder that resynchronizes at the next A5 5A marker."""

    def __init__(self) -> None:
        self._buffer = bytearray()

    def feed(self, data: bytes) -> list[Frame]:
        self._buffer.extend(data)
        frames: list[Frame] = []
        while True:
            marker = self._buffer.find(SYNC)
            if marker < 0:
                self._buffer[:] = self._buffer[-1:] if self._buffer.endswith(SYNC[:1]) else b""
                break
            if marker:
                del self._buffer[:marker]
            if len(self._buffer) < 5:
                break
            length = self._buffer[3]
            frame_length = 5 + length
            if len(self._buffer) < frame_length:
                break
            candidate = bytes(self._buffer[:frame_length])
            body = candidate[2:-1]
            if crc8_atm(body) == candidate[-1]:
                frames.append(Frame(body[0], body[2:]))
                del self._buffer[:frame_length]
            else:
                del self._buffer[0]
        return frames
