#!/usr/bin/env python3
"""Pin the stock-ROM fast-bootstrap framing and CRC contract."""

from pathlib import Path
import sys
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.janet_fastboot import (  # noqa: E402
    BLOCK_COUNT,
    BLOCK_SIZE,
    READY,
    TargetFrameParser,
    checked_frame,
    crc16_ccitt,
    crc16_ibm,
    data_block,
    extension_packet,
    extract_system,
    fletcher16,
    header,
    split_stage_artifact,
    stream_packet,
)
from tools.janet_netboot import SYSTEM_BYTES, SYSTEM_PREFIX  # noqa: E402
from tools import janet_netboot  # noqa: E402


def main() -> int:
    assert crc16_ccitt(b"123456789") == 0x29B1
    assert crc16_ibm(b"123456789") == 0xBB3D
    # V3 uses the compact 8080 end-around-carry representation of Fletcher-16.
    assert fletcher16(b"123456789") == (0xDE, 0x1E)
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
    cumulative = crc16_ccitt(expected[:BLOCK_SIZE])
    block_v2 = data_block(
        0, expected[:BLOCK_SIZE], version=2, cumulative_crc=cumulative,
    )
    assert int.from_bytes(block_v2[-2:], "big") == cumulative
    assert header(image[SYSTEM_PREFIX:SYSTEM_PREFIX + SYSTEM_BYTES], 2)[2] == 2
    assert BLOCK_COUNT * BLOCK_SIZE == SYSTEM_BYTES

    core = b"\xC3\x09\x01JFV3\x01\x02".ljust(128, b"\0")
    extension = bytes(range(256))
    bundle_core, bundle_extension = split_stage_artifact(core + extension)
    assert bundle_core == core
    assert bundle_extension == extension
    extension_wire = extension_packet(extension)
    assert extension_wire[:2] == b"\xA5\x3A"
    assert extension_wire[-2:] == bytes(fletcher16(extension))
    stream_wire = stream_packet(expected)
    assert stream_wire[:2] == b"JS"
    assert int.from_bytes(stream_wire[-2:], "big") == crc16_ibm(expected)

    # A USB serial driver may not advertise new write room until its several-
    # kilobyte URB drains. V3 grants that one long stream its real wire time.
    with mock.patch.object(
        janet_netboot.os, "write", side_effect=(1, BlockingIOError(), 2),
    ), mock.patch.object(
        janet_netboot.select, "select", return_value=([], [7], []),
    ) as serial_select:
        janet_netboot.write_all(7, b"abc", stall_timeout=10.0)
    assert serial_select.call_args.args[3] == 10.0

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
        f"({BLOCK_COUNT}x{BLOCK_SIZE}, CRC16-CCITT 29B1, "
        "CRC16/IBM BB3D vectors)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
