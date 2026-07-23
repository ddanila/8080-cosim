"""Wire-format primitives shared by Jukuravi firmware builders and host tools."""

from __future__ import annotations

from dataclasses import dataclass


SYNC = bytes((0xA5, 0x5A))
PROTOCOL_VERSION = 1
TYPE_BANNER = 0x01
TYPE_ACK = 0x81
TYPE_RAM_BEGIN = 0x10
TYPE_RAM_BLOCK = 0x11
TYPE_RAM_END = 0x12
TYPE_LOAD = 0x20
TYPE_RUN = 0x22
TYPE_LOAD_RESULT = 0xA0
TYPE_RUN_ACK = 0xA2
TYPE_LOADER_READY = 0xA3
TYPE_LOADER_ERROR = 0xAF
MAX_PAYLOAD = 255

LOADER_API_VERSION = 1
LOADER_MAX_DATA = MAX_PAYLOAD - 2
LOADER_STATUS_OK = 0
LOADER_STATUS_BAD_CRC = 1
LOADER_STATUS_BAD_COMMAND = 2
LOADER_STATUS_BAD_LENGTH = 3
LOADER_STATUS_BAD_RANGE = 4
LOADER_STATUS_VERIFY_FAILED = 5


def encode_load_frame(address: int, data: bytes) -> bytes:
    """Encode one independently checksummed loader chunk."""
    if not 0 <= address <= 0xFFFF:
        raise ValueError("load address does not fit 16 bits")
    if not data:
        raise ValueError("load chunk is empty")
    if len(data) > LOADER_MAX_DATA:
        raise ValueError(f"load chunk exceeds {LOADER_MAX_DATA} bytes")
    payload = address.to_bytes(2, "big") + data
    return encode_frame(TYPE_LOAD, payload)


def encode_run_frame(address: int) -> bytes:
    if not 0 <= address <= 0xFFFF:
        raise ValueError("run address does not fit 16 bits")
    return encode_frame(TYPE_RUN, address.to_bytes(2, "big"))


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


@dataclass(frozen=True)
class RamWindow:
    start: int
    end: int  # exclusive; may be 0x10000

    @property
    def length(self) -> int:
        return self.end - self.start


@dataclass(frozen=True)
class RamSurvey:
    version: int
    pattern_set: int
    start_page: int
    end_page: int
    masks: tuple[int, ...]
    bad_pages_by_bit: tuple[tuple[int, ...], ...]
    largest_good_window: RamWindow | None


def decode_ram_survey(frames: list[Frame]) -> RamSurvey:
    """Validate one complete ordered RAM survey and derive its host verdict."""
    begin_index = next(
        (index for index, frame in enumerate(frames) if frame.record_type == TYPE_RAM_BEGIN),
        None,
    )
    if begin_index is None:
        raise ValueError("RAM_BEGIN record is missing")
    begin = frames[begin_index]
    if len(begin.payload) != 4:
        raise ValueError("RAM_BEGIN payload length is not four")
    version, start_page, end_page, pattern_set = begin.payload
    if start_page > end_page:
        raise ValueError("RAM survey page range is reversed")

    page_count = end_page - start_page + 1
    block_frames = frames[begin_index + 1 : begin_index + 1 + page_count]
    if len(block_frames) != page_count:
        raise ValueError("RAM survey block records are incomplete")
    masks: list[int] = []
    for index, frame in enumerate(block_frames):
        expected_page = start_page + index
        if frame.record_type != TYPE_RAM_BLOCK or len(frame.payload) != 2:
            raise ValueError(f"RAM block {expected_page:02X} has wrong type or length")
        page, mask = frame.payload
        if page != expected_page:
            raise ValueError(
                f"RAM block page {page:02X} is out of order; expected {expected_page:02X}"
            )
        masks.append(mask)

    end_index = begin_index + 1 + page_count
    if end_index >= len(frames):
        raise ValueError("RAM_END record is missing")
    end = frames[end_index]
    if end != Frame(TYPE_RAM_END, bytes((start_page, end_page))):
        raise ValueError("RAM_END does not match RAM_BEGIN range")

    bad_pages_by_bit = tuple(
        tuple(start_page + index for index, mask in enumerate(masks) if mask & (1 << bit))
        for bit in range(8)
    )
    best_start: int | None = None
    best_length = 0
    run_start: int | None = None
    for index, mask in enumerate((*masks, 0xFF)):
        if mask == 0 and run_start is None:
            run_start = index
        elif mask != 0 and run_start is not None:
            run_length = index - run_start
            if run_length > best_length:
                best_start, best_length = run_start, run_length
            run_start = None
    largest = None
    if best_start is not None:
        largest = RamWindow(
            (start_page + best_start) << 8,
            (start_page + best_start + best_length) << 8,
        )
    return RamSurvey(
        version=version,
        pattern_set=pattern_set,
        start_page=start_page,
        end_page=end_page,
        masks=tuple(masks),
        bad_pages_by_bit=bad_pages_by_bit,
        largest_good_window=largest,
    )


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
