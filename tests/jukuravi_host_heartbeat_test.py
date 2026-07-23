#!/usr/bin/env python3
"""Guard the Jukuravi uploaded-program heartbeat protocol and host validator."""

from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "spinoffs" / "jukuravi"))
import host  # noqa: E402
import protocol  # noqa: E402


def fail(message: str) -> None:
    print(f"JUKURAVI-HOST-HEARTBEAT: FAIL: {message}", file=sys.stderr)
    raise SystemExit(1)


def evidence(count: int) -> dict[str, object]:
    return {
        "required": count,
        "received": 0,
        "timeout_seconds": 1.0,
        "status": "pending_run",
        "error": None,
        "events": [],
    }


def session_with(frames: list[protocol.Frame]) -> host.HostSession:
    session = object.__new__(host.HostSession)
    session.frames = frames
    return session


def expect_error(
    frames: list[protocol.Frame],
    count: int,
    expected: str,
) -> None:
    session = session_with(frames)
    record = evidence(count)
    try:
        session._monitor_heartbeats(0, count, 1.0, record)
    except host.SessionError as error:
        if str(error) != expected:
            fail(f"validator error differs: {error!s}")
    else:
        fail(f"validator accepted invalid heartbeat stream: {frames!r}")


def main() -> int:
    encoded = protocol.encode_heartbeat_frame(0xFE)
    decoded = protocol.StreamDecoder().feed(encoded)
    if decoded != [
        protocol.Frame(
            protocol.TYPE_HEARTBEAT,
            bytes((protocol.HEARTBEAT_VERSION, 0xFE)),
        )
    ]:
        fail("heartbeat encoder does not round-trip")
    for invalid in (-1, 0x100):
        try:
            protocol.encode_heartbeat_frame(invalid)
        except ValueError:
            pass
        else:
            fail(f"out-of-range heartbeat sequence {invalid} was accepted")

    frames = [
        protocol.Frame(
            protocol.TYPE_HEARTBEAT,
            bytes((protocol.HEARTBEAT_VERSION, sequence)),
        )
        for sequence in (0xFE, 0xFF, 0x00)
    ]
    record = evidence(3)
    session_with(frames)._monitor_heartbeats(0, 3, 1.0, record)
    if record != {
        "required": 3,
        "received": 3,
        "timeout_seconds": 1.0,
        "status": "complete",
        "error": None,
        "events": [
            {"index": 0, "frame_index": 0, "sequence": 0xFE},
            {"index": 1, "frame_index": 1, "sequence": 0xFF},
            {"index": 2, "frame_index": 2, "sequence": 0x00},
        ],
    }:
        fail(f"wraparound heartbeat evidence differs: {record!r}")

    expect_error(
        [
            protocol.Frame(protocol.TYPE_HEARTBEAT, bytes((1, 7))),
            protocol.Frame(protocol.TYPE_HEARTBEAT, bytes((1, 9))),
        ],
        2,
        "heartbeat sequence 09 does not follow 07",
    )
    expect_error(
        [protocol.Frame(protocol.TYPE_HEARTBEAT, bytes((2, 0)))],
        1,
        "heartbeat version 2 != 1",
    )
    expect_error(
        [protocol.Frame(protocol.TYPE_HEARTBEAT, b"\x01")],
        1,
        "heartbeat payload length is not two",
    )
    expect_error(
        [protocol.Frame(protocol.TYPE_LOADER_READY, b"")],
        1,
        "unexpected post-RUN frame 0xA3 while waiting for heartbeat",
    )

    print(
        "JUKURAVI-HOST-HEARTBEAT: PASS "
        "(CRC frame; sequence wrap; malformed and unexpected rejection)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
