#!/usr/bin/env python3
"""Pin the stock-ROM fast-bootstrap framing and CRC contract."""

from pathlib import Path
import os
import pty
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
    compressed_stream_packet,
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
from tools.janet_netboot import (  # noqa: E402
    SYSTEM_BYTES,
    SYSTEM_PREFIX,
    boot_frames,
    configure_serial,
    prepare_image,
    xor_bytes,
)
from tools import janet_netboot  # noqa: E402
from tools.janet_disk_server import boot_with_recovery  # noqa: E402


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

    stock_record = bytes(range(128))
    native_execute = boot_frames(stock_record)
    compact_execute = boot_frames(stock_record, compact_execute=True)
    assert len(native_execute) == 8
    assert sum(map(len, native_execute)) == 340
    assert native_execute[-3][6:8] == b"\x02\x0f"
    assert native_execute[-2][6] == 0x04
    assert native_execute[-1][6] == 0x09
    assert len(compact_execute) == 6
    assert sum(map(len, compact_execute)) == 198
    assert compact_execute[-1][6:-1] == b"\x03\x0f"
    assert xor_bytes(compact_execute[-1]) == 0

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
    bundle_core, bundle_extension, bundle_payload = \
        split_stage_artifact(core + extension)
    assert bundle_core == core
    assert bundle_extension == extension
    assert bundle_payload is None
    extension_wire = extension_packet(extension)
    assert extension_wire[:2] == b"\xA5\x3A"
    assert extension_wire[-2:] == bytes(fletcher16(extension))
    stream_wire = stream_packet(expected)
    assert stream_wire[:2] == b"JS"
    assert int.from_bytes(stream_wire[-2:], "big") == crc16_ibm(expected)

    core_v4 = b"\xC3\x09\x01JFV4\x01\x03".ljust(128, b"\0")
    extension_v4 = bytes(range(256)) + bytes(range(128))
    bundle_core, bundle_extension, bundle_payload = split_stage_artifact(
        core_v4 + extension_v4,
    )
    assert bundle_core == core_v4
    assert bundle_extension == extension_v4
    assert bundle_payload is None
    extension_wire = extension_packet(extension_v4)
    assert extension_wire[-2:] == bytes(fletcher16(extension_v4))

    core_v5 = b"\xC3\x09\x01JFV5\x01\x02".ljust(128, b"\0")
    bundle_core, bundle_extension, bundle_payload = \
        split_stage_artifact(core_v5 + extension)
    assert bundle_core == core_v5
    assert bundle_extension == extension
    assert bundle_payload is None

    core_v6 = b"\xC3\x09\x01JFV6\x01\x03".ljust(128, b"\0")
    extension_v6 = bytes(range(256)) + bytes(range(128))
    compressed = bytes((index * 29 + 7) & 0xFF for index in range(1024))
    bundle_v6 = (
        core_v6 + extension_v6 + b"Z0"
        + crc16_ibm(expected).to_bytes(2, "big") + compressed
    )
    bundle_core, bundle_extension, bundle_payload = \
        split_stage_artifact(bundle_v6)
    assert bundle_core == core_v6
    assert bundle_extension == extension_v6
    assert bundle_payload == compressed
    compressed_wire = compressed_stream_packet(compressed)
    assert compressed_wire[:2] == b"JZ"
    assert int.from_bytes(compressed_wire[2:4], "big") == len(compressed)
    assert int.from_bytes(compressed_wire[-2:], "big") == \
        crc16_ibm(compressed)

    core_v7 = b"\xC3\x09\x01JFV7\x01\x02".ljust(128, b"\0")
    extension_v7 = bytes(range(256))
    compressed_crc = crc16_ibm(compressed)
    bundle_v7 = (
        core_v7 + extension_v7 + b"Z7"
        + crc16_ibm(expected).to_bytes(2, "big")
        + len(compressed).to_bytes(2, "big")
        + compressed_crc.to_bytes(2, "big")
        + compressed
    )
    bundle_core, bundle_extension, bundle_payload = \
        split_stage_artifact(bundle_v7)
    assert bundle_core == core_v7
    assert bundle_extension == extension_v7
    assert bundle_payload == compressed
    compressed_wire_v7 = compressed_stream_packet(compressed, fixed=True)
    assert compressed_wire_v7 == b"JZ" + compressed
    for broken in (
        bundle_v7[:-1],
        bundle_v7[:-1] + bytes((bundle_v7[-1] ^ 1,)),
    ):
        try:
            split_stage_artifact(broken)
        except ValueError:
            pass
        else:
            raise AssertionError("malformed v7 artifact was accepted")

    core_v8 = b"\xC3\x09\x01JFV8\x01\x05".ljust(128, b"\0")
    extension_v8 = bytes(range(256)) * 2 + bytes(range(128))
    bundle_v8 = (
        core_v8 + extension_v8 + b"Z8"
        + crc16_ibm(expected).to_bytes(2, "big")
        + len(compressed).to_bytes(2, "big")
        + compressed_crc.to_bytes(2, "big")
        + compressed
    )
    bundle_core, bundle_extension, bundle_payload = \
        split_stage_artifact(bundle_v8)
    assert bundle_core == core_v8
    assert bundle_extension == extension_v8
    assert bundle_payload == compressed
    assert extension_packet(extension_v8)[-2:] == \
        bytes(fletcher16(extension_v8))
    short = compressed[:255]
    short_v8 = (
        core_v8 + extension_v8 + b"Z8"
        + crc16_ibm(expected).to_bytes(2, "big")
        + len(short).to_bytes(2, "big")
        + crc16_ibm(short).to_bytes(2, "big")
        + short
    )
    for broken in (
        bundle_v8[:-1],
        bundle_v8[:-1] + bytes((bundle_v8[-1] ^ 1,)),
        short_v8,
    ):
        try:
            split_stage_artifact(broken)
        except ValueError:
            pass
        else:
            raise AssertionError("malformed v8 artifact was accepted")

    extension_v9 = bytes(range(256)) * 2 + bytes(range(42))
    core_v9 = (
        b"\xC3\x0B\x01JFV9\x01\x00"
        + len(extension_v9).to_bytes(2, "little")
    ).ljust(128, b"\0")
    bundle_v9 = (
        core_v9 + extension_v9 + b"Z9"
        + crc16_ibm(expected).to_bytes(2, "big")
        + len(compressed).to_bytes(2, "big")
        + compressed_crc.to_bytes(2, "big")
        + compressed
    )
    bundle_core, bundle_extension, bundle_payload = \
        split_stage_artifact(bundle_v9)
    assert bundle_core == core_v9
    assert bundle_extension == extension_v9
    assert bundle_payload == compressed
    assert extension_packet(extension_v9)[-2:] == \
        bytes(fletcher16(extension_v9))
    for broken in (
        bundle_v9[:8] + b"\x01" + bundle_v9[9:],
        bundle_v9[:9] + b"\xff\xff" + bundle_v9[11:],
        bundle_v9[:-1],
        bundle_v9[:-1] + bytes((bundle_v9[-1] ^ 1,)),
    ):
        try:
            split_stage_artifact(broken)
        except ValueError:
            pass
        else:
            raise AssertionError("malformed v9 artifact was accepted")

    extension_v10 = extension_v9 + bytes(range(15))
    core_v10 = (
        b"\xC3\x0B\x01JF10\x01\x00"
        + len(extension_v10).to_bytes(2, "little")
    ).ljust(128, b"\0")
    bundle_v10 = (
        core_v10 + extension_v10 + b"ZA"
        + crc16_ibm(expected).to_bytes(2, "big")
        + len(compressed).to_bytes(2, "big")
        + compressed_crc.to_bytes(2, "big")
        + compressed
    )
    bundle_core, bundle_extension, bundle_payload = \
        split_stage_artifact(bundle_v10)
    assert bundle_core == core_v10
    assert bundle_extension == extension_v10
    assert bundle_payload == compressed
    for broken in (
        bundle_v10[:8] + b"\x01" + bundle_v10[9:],
        bundle_v10[:9] + b"\xff\xff" + bundle_v10[11:],
        bundle_v10[:-1],
        bundle_v10[:-1] + bytes((bundle_v10[-1] ^ 1,)),
    ):
        try:
            split_stage_artifact(broken)
        except ValueError:
            pass
        else:
            raise AssertionError("malformed v10 artifact was accepted")

    core_v11 = core_v10[:3] + b"JF11" + core_v10[7:]
    bundle_v11 = (
        core_v11 + extension_v10 + b"ZB"
        + crc16_ibm(expected).to_bytes(2, "big")
        + len(compressed).to_bytes(2, "big")
        + compressed_crc.to_bytes(2, "big")
        + compressed
    )
    bundle_core, bundle_extension, bundle_payload = \
        split_stage_artifact(bundle_v11)
    assert bundle_core == core_v11
    assert bundle_extension == extension_v10
    assert bundle_payload == compressed

    core_v12 = core_v10[:3] + b"JF12" + core_v10[7:]
    bundle_v12 = (
        core_v12 + extension_v10 + b"ZC"
        + crc16_ibm(expected).to_bytes(2, "big")
        + len(compressed).to_bytes(2, "big")
        + compressed_crc.to_bytes(2, "big")
        + compressed
    )
    bundle_core, bundle_extension, bundle_payload = \
        split_stage_artifact(bundle_v12)
    assert bundle_core == core_v12
    assert bundle_extension == extension_v10
    assert bundle_payload == compressed

    core_v13 = core_v10[:3] + b"JF13" + core_v10[7:]
    bundle_v13 = (
        core_v13 + extension_v10 + b"ZD"
        + crc16_ibm(expected).to_bytes(2, "big")
        + len(compressed).to_bytes(2, "big")
        + compressed_crc.to_bytes(2, "big")
        + compressed
    )
    bundle_core, bundle_extension, bundle_payload = \
        split_stage_artifact(bundle_v13)
    assert bundle_core == core_v13
    assert bundle_extension == extension_v10
    assert bundle_payload == compressed

    extension_v14 = bytes(range(256)) + bytes(range(11))
    core_v14 = (
        b"\xC3\x0B\x01JF14\x01\x00"
        + len(extension_v14).to_bytes(2, "little")
    ).ljust(128, b"\0")
    bundle_v14 = (
        core_v14 + extension_v14 + b"ZE"
        + crc16_ibm(expected).to_bytes(2, "big")
        + len(compressed).to_bytes(2, "big")
        + compressed_crc.to_bytes(2, "big")
        + compressed
    )
    bundle_core, bundle_extension, bundle_payload = \
        split_stage_artifact(bundle_v14)
    assert bundle_core == core_v14
    assert bundle_extension == extension_v14
    assert bundle_payload == compressed

    ram_system = bytes((index * 17 + 3) & 0xFF for index in range(0x2080))
    ram_header = (
        b"JUKURM1\x1a" + b"\x00\xb0\x00\xc6"
        + len(ram_system).to_bytes(2, "little")
        + crc16_ibm(ram_system).to_bytes(2, "little")
    ).ljust(SYSTEM_PREFIX, b"\x00")
    ram_image = ram_header + ram_system
    prepared_ram = prepare_image(ram_image)
    assert prepared_ram.load_address == 0x0100
    assert prepared_ram.entry == 0x0100
    assert prepared_ram.data[128:] == ram_system
    assert len(prepared_ram.data) == 128 + len(ram_system)
    assert prepared_ram.data[:4] == b"\xf3\x21\x80\x01"
    assert prepared_ram.data[4:7] == b"\x11\x00\xb0"
    assert prepared_ram.data[18:20] == b"\x0a\x01"
    assert prepared_ram.data[20:23] == b"\xc3\x00\xc6"
    try:
        prepare_image(ram_image[:-1] + bytes((ram_image[-1] ^ 1,)))
    except ValueError:
        pass
    else:
        raise AssertionError("corrupt JUKURM1 resident was accepted")

    core_v15 = core_v14[:3] + b"JF15" + core_v14[7:]
    bundle_v15 = (
        core_v15 + extension_v14 + b"ZF"
        + crc16_ibm(ram_system).to_bytes(2, "big")
        + len(compressed).to_bytes(2, "big")
        + compressed_crc.to_bytes(2, "big")
        + compressed
    )
    bundle_core, bundle_extension, bundle_payload = \
        split_stage_artifact(bundle_v15)
    assert bundle_core == core_v15
    assert bundle_extension == extension_v14
    assert bundle_payload == compressed
    assert extract_system(ram_image) == ram_system

    attempts = 0
    preparations = 0

    def reset_attempt() -> dict[str, object]:
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            raise TimeoutError("simulated target reset")
        return {"result": "second boot"}

    def prepare_retry() -> None:
        nonlocal preparations
        preparations += 1

    recovered = boot_with_recovery(
        reset_attempt, prepare_retry=prepare_retry,
        max_restarts=1, verbose=False,
    )
    assert recovered == {"result": "second boot", "boot_restarts": 1}
    assert attempts == 2 and preparations == 1

    # A USB serial driver may not advertise new write room until its several-
    # kilobyte URB drains. V3 grants that one long stream its real wire time.
    with mock.patch.object(
        janet_netboot.os, "write", side_effect=(1, BlockingIOError(), 2),
    ), mock.patch.object(
        janet_netboot.select, "select", return_value=([], [7], []),
    ) as serial_select:
        janet_netboot.write_all(7, b"abc", stall_timeout=10.0)
    assert serial_select.call_args.args[3] == 10.0

    if sys.platform.startswith("linux"):
        master, slave = pty.openpty()
        try:
            # PTYs do not retain parity, so this pins only the exact custom
            # termios2 rate path; physical CP2102 readback pins 8O1 later.
            configure_serial(master, 28800, parity="none")
        finally:
            os.close(master)
            os.close(slave)

    parser = TargetFrameParser()
    ready = checked_frame(READY, bytes((1, BLOCK_COUNT)))
    probe = checked_frame(ord("Q"), bytes((4, 1)))
    reply = checked_frame(ord("A"), b"\x07\x00")
    assert parser.feed(b"garbage" + ready[:3]) == []
    assert parser.feed(ready[3:] + probe + reply) == [
        (READY, 1, BLOCK_COUNT), (ord("Q"), 4, 1), (ord("A"), 7, 0),
    ]
    # Parsed frames remain queued so an early predicate match cannot discard
    # a coalesced final reply on a USB-UART read.
    assert list(parser.pending) == [
        (READY, 1, BLOCK_COUNT), (ord("Q"), 4, 1), (ord("A"), 7, 0),
    ]
    print(
        "JANET-FASTBOOT-PROTOCOL-TEST: PASS "
        f"({BLOCK_COUNT}x{BLOCK_SIZE}, CRC16-CCITT 29B1, "
        "CRC16/IBM BB3D vectors)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
