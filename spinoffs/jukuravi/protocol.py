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
TYPE_LOADER_V2_PROBE = 0x23
TYPE_LOADER_V2_CONFIG = 0x24
TYPE_LOADER_V2_LOAD = 0x25
TYPE_LOADER_V2_READ = 0x26
TYPE_LOADER_V2_CRC = 0x27
TYPE_LOADER_V2_RUN = 0x28
TYPE_LOADER_V2_RESYNC = 0x29
TYPE_LOADER_V2_REFRESH = 0x2A
TYPE_HEARTBEAT = 0x30
TYPE_NANO_LIVENESS = 0x40
TYPE_DIAG_STATUS = 0x50
TYPE_LOAD_RESULT = 0xA0
TYPE_RUN_ACK = 0xA2
TYPE_LOADER_READY = 0xA3
TYPE_LOADER_ERROR = 0xAF
TYPE_LOADER_V2_RESULT = 0xB0
TYPE_LOADER_V2_DATA = 0xB1
TYPE_LOADER_V2_RETURN = 0xB2
MAX_PAYLOAD = 255

LOADER_API_VERSION = 1
LOADER_V2_API_VERSION = 2
LOADER_API_BASE = 0x0A00
LOADER_MAX_DATA = MAX_PAYLOAD - 2
LOADER_LOAD_MIN = 0x4000
LOADER_LOAD_END = 0xD800
HEARTBEAT_VERSION = 1
NANO_LIVENESS_VERSION = 1
NANO_LIVENESS_ENABLED = 0x01
NANO_LIVENESS_RESET_RELEASED = 0x02
NANO_LIVENESS_CLOCK_SEEN = 0x04
NANO_LIVENESS_MRDC_SEEN = 0x08
NANO_LIVENESS_KNOWN_FLAGS = 0x0F
LOADER_STATUS_OK = 0
LOADER_STATUS_BAD_CRC = 1
LOADER_STATUS_BAD_COMMAND = 2
LOADER_STATUS_BAD_LENGTH = 3
LOADER_STATUS_BAD_RANGE = 4
LOADER_STATUS_VERIFY_FAILED = 5
LOADER_STATUS_STRONG_CRC = 6
LOADER_STATUS_BAD_CONFIG = 7
LOADER_STATUS_WORKSPACE = 8

LOADER_V2_CAP_PROBE = 0x0001
LOADER_V2_CAP_CONFIG_VOTES = 0x0002
LOADER_V2_CAP_LOAD = 0x0004
LOADER_V2_CAP_READ = 0x0008
LOADER_V2_CAP_CRC = 0x0010
LOADER_V2_CAP_RUN = 0x0020
LOADER_V2_CAP_RESYNC = 0x0040
LOADER_V2_CAP_TRANSACTIONS = 0x0080
LOADER_V2_CAP_VERIFIED_BUFFER = 0x0100
LOADER_V2_CAP_STRONG_CRC = 0x0200
LOADER_V2_CAP_CALL_RETURN = 0x0400
LOADER_V2_CAP_RUN_REPLAY = 0x0800
LOADER_V2_CAP_UART_RESTORE = 0x1000
LOADER_V2_CAP_IDLE_RESYNC = 0x2000
LOADER_V2_CAP_REFRESH = 0x4000
LOADER_V2_CAPABILITIES = (
    LOADER_V2_CAP_PROBE
    | LOADER_V2_CAP_CONFIG_VOTES
    | LOADER_V2_CAP_LOAD
    | LOADER_V2_CAP_READ
    | LOADER_V2_CAP_CRC
    | LOADER_V2_CAP_RUN
    | LOADER_V2_CAP_RESYNC
    | LOADER_V2_CAP_TRANSACTIONS
    | LOADER_V2_CAP_VERIFIED_BUFFER
    | LOADER_V2_CAP_STRONG_CRC
    | LOADER_V2_CAP_CALL_RETURN
    | LOADER_V2_CAP_RUN_REPLAY
    | LOADER_V2_CAP_UART_RESTORE
    | LOADER_V2_CAP_IDLE_RESYNC
)
LOADER_V2_BOOT_VOTES = 7
LOADER_V2_T35_BOOT_VOTES = 1
LOADER_V2_T36_BOOT_VOTES = 1
LOADER_V2_MIN_VOTES = 1
LOADER_V2_MAX_VOTES = 15
LOADER_V2_MAX_DATA = 32
LOADER_V2_MAX_PROBE = 16
LOADER_V2_LOAD_MIN = 0x4000
LOADER_V2_LOAD_END = 0xC000
LOADER_V2_WORKSPACE_BASE = 0xC000
LOADER_V2_WORKSPACE_END = 0xD000
LOADER_V2_RUN_CALL = 0
LOADER_V2_RUN_JUMP = 1
LOADER_V2_T35_CAPABILITIES = LOADER_V2_CAPABILITIES | LOADER_V2_CAP_REFRESH
LOADER_V2_T36_CAPABILITIES = LOADER_V2_T35_CAPABILITIES
LOADER_V2_REFRESH_API = 0x07A9
LOADER_V2_REFRESH_VERSION = 1
LOADER_V2_REFRESH_QUERY = 0
LOADER_V2_REFRESH_ENABLE = 1
LOADER_V2_REFRESH_DISABLE = 2
LOADER_V2_REFRESH_RESET_COUNTER = 3
LOADER_V2_REFRESH_ROW_START = 0x40
LOADER_V2_T36_REFRESH_ROW_START = 0x00
LOADER_V2_REFRESH_ROWS = 128

LOADER_V2_COMMAND_TYPES = (
    TYPE_LOADER_V2_PROBE,
    TYPE_LOADER_V2_CONFIG,
    TYPE_LOADER_V2_LOAD,
    TYPE_LOADER_V2_READ,
    TYPE_LOADER_V2_CRC,
    TYPE_LOADER_V2_RUN,
    TYPE_LOADER_V2_RESYNC,
    TYPE_LOADER_V2_REFRESH,
)


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


def encode_loader_v2_command(
    record_type: int, transaction: int, body: bytes = b""
) -> bytes:
    """Encode one loader API v2 command with outer CRC-8 and inner CRC-16.

    The inner checksum is calculated over type, final payload length, the
    transaction byte, and the command body. The ROM recomputes it from its RAM
    parser buffer, so a correct UART CRC cannot conceal a failed RAM store.
    """
    if record_type not in LOADER_V2_COMMAND_TYPES:
        raise ValueError("record type is not a loader API v2 command")
    if not 0 <= transaction <= 0xFF:
        raise ValueError("transaction does not fit one byte")
    payload_without_crc = bytes((transaction,)) + body
    final_length = len(payload_without_crc) + 2
    if final_length > MAX_PAYLOAD:
        raise ValueError("loader API v2 command payload is too long")
    protected = bytes((record_type, final_length)) + payload_without_crc
    strong_crc = crc16_ccitt_false(protected)
    return encode_frame(
        record_type,
        payload_without_crc + strong_crc.to_bytes(2, "big"),
    )


def validate_loader_v2_command(frame: Frame) -> tuple[int, bytes]:
    """Validate and split a loader API v2 command into transaction and body."""
    if frame.record_type not in LOADER_V2_COMMAND_TYPES:
        raise ValueError("frame is not a loader API v2 command")
    if len(frame.payload) < 3:
        raise ValueError(
            "loader API v2 command is shorter than transaction plus CRC-16"
        )
    payload_without_crc = frame.payload[:-2]
    received = int.from_bytes(frame.payload[-2:], "big")
    protected = bytes((frame.record_type, len(frame.payload))) + payload_without_crc
    if crc16_ccitt_false(protected) != received:
        raise ValueError("loader API v2 command inner CRC-16 differs")
    return payload_without_crc[0], payload_without_crc[1:]


def encode_loader_v2_load(transaction: int, address: int, data: bytes) -> bytes:
    if not LOADER_V2_LOAD_MIN <= address < LOADER_V2_LOAD_END:
        raise ValueError("load address is outside loader RAM")
    if not data or len(data) > LOADER_V2_MAX_DATA:
        raise ValueError(f"load data must contain 1..{LOADER_V2_MAX_DATA} bytes")
    if address + len(data) > LOADER_V2_LOAD_END:
        raise ValueError("load crosses the loader RAM boundary")
    return encode_loader_v2_command(
        TYPE_LOADER_V2_LOAD, transaction, address.to_bytes(2, "big") + data
    )


def encode_loader_v2_range_command(
    record_type: int, transaction: int, address: int, count: int
) -> bytes:
    if record_type not in (TYPE_LOADER_V2_READ, TYPE_LOADER_V2_CRC):
        raise ValueError("range command must be READ or CRC")
    if not LOADER_V2_LOAD_MIN <= address < LOADER_V2_LOAD_END:
        raise ValueError("range address is outside loader RAM")
    if not 1 <= count <= LOADER_V2_MAX_DATA or address + count > LOADER_V2_LOAD_END:
        raise ValueError(f"range count must fit 1..{LOADER_V2_MAX_DATA} bytes")
    return encode_loader_v2_command(
        record_type, transaction, address.to_bytes(2, "big") + bytes((count,))
    )


def encode_loader_v2_run(
    transaction: int, address: int, mode: int, execution_id: int
) -> bytes:
    """Encode a replay-safe loader API v2 RUN command.

    ``execution_id`` is independent of the one-byte transport transaction.
    The ROM caches the most recently completed invocation and replays its ACK
    and RETURN for an exact duplicate execution ID instead of executing it
    twice.
    """
    if not LOADER_V2_LOAD_MIN <= address < LOADER_V2_LOAD_END:
        raise ValueError("run address is outside loader RAM")
    if mode not in (LOADER_V2_RUN_CALL, LOADER_V2_RUN_JUMP):
        raise ValueError("run mode is invalid")
    if not 0 <= execution_id <= 0xFFFFFFFF:
        raise ValueError("execution ID does not fit 32 bits")
    return encode_loader_v2_command(
        TYPE_LOADER_V2_RUN,
        transaction,
        address.to_bytes(2, "big") + bytes((mode,)) + execution_id.to_bytes(4, "big"),
    )


def encode_heartbeat_frame(sequence: int) -> bytes:
    """Encode one uploaded-program liveness record."""
    if not 0 <= sequence <= 0xFF:
        raise ValueError("heartbeat sequence does not fit one byte")
    return encode_frame(TYPE_HEARTBEAT, bytes((HEARTBEAT_VERSION, sequence)))


def encode_nano_liveness_frame(flags: int) -> bytes:
    """Encode one Nano-side liveness observation record."""
    if not 0 <= flags <= NANO_LIVENESS_KNOWN_FLAGS:
        raise ValueError("Nano liveness flags contain unknown bits")
    if not flags & NANO_LIVENESS_ENABLED:
        raise ValueError("Nano liveness record is not enabled")
    return encode_frame(TYPE_NANO_LIVENESS, bytes((NANO_LIVENESS_VERSION, flags)))


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
                ((crc << 1) ^ 0x1021) & 0xFFFF if crc & 0x8000 else (crc << 1) & 0xFFFF
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
        (
            index
            for index, frame in enumerate(frames)
            if frame.record_type == TYPE_RAM_BEGIN
        ),
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
        tuple(
            start_page + index for index, mask in enumerate(masks) if mask & (1 << bit)
        )
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
                self._buffer[:] = (
                    self._buffer[-1:] if self._buffer.endswith(SYNC[:1]) else b""
                )
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
