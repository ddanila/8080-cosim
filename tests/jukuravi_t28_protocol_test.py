#!/usr/bin/env python3
"""Pin loader API v2 against the exact T28 reference ROM contract."""

from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "spinoffs" / "jukuravi"))
import protocol  # noqa: E402
import host  # noqa: E402


def fail(message: str) -> None:
    print(f"JUKURAVI-T28-PROTOCOL: FAIL: {message}", file=sys.stderr)
    raise SystemExit(1)


def decode_one(encoded: bytes) -> protocol.Frame:
    frames = protocol.StreamDecoder().feed(encoded)
    if len(frames) != 1:
        fail(f"encoded command decoded as {len(frames)} frames")
    return frames[0]


def main() -> int:
    if protocol.crc16_ccitt_false(b"123456789") != 0x29B1:
        fail("CRC-16/CCITT-FALSE check vector differs")

    load = protocol.encode_loader_v2_load(0x42, 0x4000, b"\x76\x00")
    frame = decode_one(load)
    transaction, body = protocol.validate_loader_v2_command(frame)
    if (
        frame.record_type != protocol.TYPE_LOADER_V2_LOAD
        or transaction != 0x42
        or body != b"\x40\x00\x76\x00"
    ):
        fail("LOAD transaction did not round-trip exactly")

    for record_type in (protocol.TYPE_LOADER_V2_READ, protocol.TYPE_LOADER_V2_CRC):
        command = protocol.encode_loader_v2_range_command(
            record_type, 0xA5, 0xBFE0, protocol.LOADER_V2_MAX_DATA
        )
        transaction, body = protocol.validate_loader_v2_command(decode_one(command))
        if transaction != 0xA5 or body != b"\xBF\xE0\x20":
            fail(f"range command 0x{record_type:02X} differs")

    run = protocol.encode_loader_v2_run(
        0x17, 0x4567, protocol.LOADER_V2_RUN_CALL, 0x89ABCDEF
    )
    transaction, body = protocol.validate_loader_v2_command(decode_one(run))
    if transaction != 0x17 or body != b"\x45\x67\x00\x89\xAB\xCD\xEF":
        fail("replay-safe RUN command differs")
    required_caps = (
        protocol.LOADER_V2_CAP_CALL_RETURN
        | protocol.LOADER_V2_CAP_RUN_REPLAY
        | protocol.LOADER_V2_CAP_UART_RESTORE
        | protocol.LOADER_V2_CAP_IDLE_RESYNC
    )
    if protocol.LOADER_V2_CAPABILITIES & required_caps != required_caps:
        fail("recoverability capabilities are not advertised")

    # Change one protected byte, then repair only the outer CRC-8.  This is
    # the exact class of corruption T26 could accept when its parser-buffer
    # contents differed from the UART-side CRC accumulator.
    corrupt = bytearray(load)
    corrupt[6] ^= 0x01
    corrupt[-1] = protocol.crc8_atm(bytes(corrupt[2:-1]))
    damaged = decode_one(bytes(corrupt))
    try:
        protocol.validate_loader_v2_command(damaged)
    except ValueError as error:
        if "CRC-16" not in str(error):
            fail(f"inner corruption raised the wrong error: {error}")
    else:
        fail("inner corruption survived repaired outer CRC-8")

    demux = host.LoaderRequestDemux()
    framed_tokens = protocol.encode_frame(0xB1, b"\xC6\xC7\x55\xAA")
    mixed = b"\xC6" + framed_tokens + b"\xC7"
    requests: list[int] = []
    for split in (mixed[:4], mixed[4:9], mixed[9:]):
        requests.extend(demux.feed(split))
    if requests != [0xC6, 0xC7]:
        fail(f"request demultiplexing leaked framed C6/C7: {requests!r}")

    # A DATA-producing command returns RESULT when the ROM's parser-buffer
    # CRC rejects a stored command. The host must pass that structured error
    # to its transaction layer and retry the identical command, rather than
    # rejecting RESULT as the wrong response type before retry policy runs.
    strong_crc = protocol.Frame(
        protocol.TYPE_LOADER_V2_RESULT,
        bytes((0x42, protocol.LOADER_STATUS_STRONG_CRC, 0x37, 0x3F,
               0, 0, 0, 0, 0, 0)),
    )
    wait_session = object.__new__(host.HostSession)
    wait_session.solicited_host_tx = False
    wait_session.symbol_requests = []
    wait_session.frames = [strong_crc]
    returned, cursor = wait_session._wait_loader_frame(
        protocol.TYPE_LOADER_V2_DATA, 0, 0.1, "injected DATA failure"
    )
    if returned is not strong_crc or cursor != 1:
        fail("DATA response filter did not surface structured RESULT failure")

    data_ok = protocol.Frame(
        protocol.TYPE_LOADER_V2_DATA,
        bytes((0x42, protocol.LOADER_STATUS_OK, protocol.TYPE_LOADER_V2_PROBE,
               0, 0, 1, 0x58)),
    )
    retry_session = object.__new__(host.HostSession)
    retry_session.loader_retries = 3
    sent: list[bytes] = []
    replies = iter(((strong_crc, 1), (data_ok, 2)))
    retry_session._send_loader_frame = (  # type: ignore[method-assign]
        lambda command, timeout, description: sent.append(command)
    )
    retry_session._wait_loader_frame = (  # type: ignore[method-assign]
        lambda expected, cursor, timeout, description: next(replies)
    )
    command = protocol.encode_loader_v2_command(
        protocol.TYPE_LOADER_V2_PROBE, 0x42, b"X"
    )
    response, cursor, attempts = retry_session._loader_v2_transact(
        command, 0x42, protocol.TYPE_LOADER_V2_DATA, 0, 0.1, "injected PROBE"
    )
    if response is not data_ok or cursor != 2 or attempts != 2 or sent != [command, command]:
        fail("strong-CRC DATA retry was not identical and bounded")

    print(
        "JUKURAVI-T28-PROTOCOL: PASS "
        "(strong CRC retry; bounded ranges; replay-safe RUN; recoverability caps; demux)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
