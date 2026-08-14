#!/usr/bin/env python3
"""Pin the stock-ROM fast-bootstrap framing and CRC contract."""

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.janet_fastboot import (  # noqa: E402
    BLOCK_COUNT,
    BLOCK_SIZE,
    READY,
    TargetFrameParser,
    checked_frame,
    crc16_ccitt,
    data_block,
    extract_system,
    header,
)
from tools.janet_netboot import SYSTEM_BYTES, SYSTEM_PREFIX  # noqa: E402


def main() -> int:
    assert crc16_ccitt(b"123456789") == 0x29B1
    system = bytes((index * 73 + 19) & 0xFF for index in range(SYSTEM_BYTES))
    image = bytes((0xE5,)) * SYSTEM_PREFIX + system + \
        bytes(10240 - SYSTEM_PREFIX - SYSTEM_BYTES)
    # The recognizer requires the resident image's ordinary JMP opcode.
    image = image[:SYSTEM_PREFIX] + b"\xC3" + image[SYSTEM_PREFIX + 1:]
    expected = b"\xC3" + system[1:]
    assert extract_system(image) == expected

    session_header = header(image[SYSTEM_PREFIX:SYSTEM_PREFIX + SYSTEM_BYTES])
    assert len(session_header) == 7
    assert not __import__("functools").reduce(int.__xor__, session_header)
    block = data_block(0, expected[:BLOCK_SIZE])
    assert len(block) == 2 + 1 + BLOCK_SIZE + 2
    assert crc16_ccitt(block[2:-2]) == int.from_bytes(block[-2:], "big")
    assert BLOCK_COUNT * BLOCK_SIZE == SYSTEM_BYTES

    parser = TargetFrameParser()
    ready = checked_frame(READY, bytes((1, BLOCK_COUNT)))
    reply = checked_frame(ord("A"), b"\x07\x00")
    assert parser.feed(b"garbage" + ready[:3]) == []
    assert parser.feed(ready[3:] + reply) == [
        (READY, 1, BLOCK_COUNT), (ord("A"), 7, 0),
    ]
    # Parsed frames remain queued so an early predicate match cannot discard
    # a coalesced final reply on a USB-UART read.
    assert list(parser.pending) == [
        (READY, 1, BLOCK_COUNT), (ord("A"), 7, 0),
    ]
    print(
        "JANET-FASTBOOT-PROTOCOL-TEST: PASS "
        f"({BLOCK_COUNT}x{BLOCK_SIZE}, CRC16-CCITT 29B1 vector)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
