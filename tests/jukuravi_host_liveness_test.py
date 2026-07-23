#!/usr/bin/env python3
"""Guard Nano liveness framing, host evidence, and no-banner retry policy."""

from __future__ import annotations

import socket
import sys
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "spinoffs" / "jukuravi"))
import host  # noqa: E402
import protocol  # noqa: E402


def fail(message: str) -> None:
    print(f"JUKURAVI-HOST-LIVENESS: FAIL: {message}", file=sys.stderr)
    raise SystemExit(1)


class NullLogs:
    @staticmethod
    def rx(_data: bytes) -> None:
        pass

    @staticmethod
    def tx(_data: bytes) -> None:
        pass


def fresh_session(fd: int = -1) -> host.HostSession:
    session = host.HostSession(fd, NullLogs(), 0.1, 0.01, None, None, False)
    session.begin_attempt(1)
    return session


def expect_error(payload: bytes, expected: str) -> None:
    session = fresh_session()
    try:
        session._accept_nano_liveness(
            protocol.Frame(protocol.TYPE_NANO_LIVENESS, payload)
        )
    except host.SessionError as error:
        if str(error) != expected:
            fail(f"liveness validation error differs: {error!s}")
    else:
        fail(f"invalid Nano liveness payload was accepted: {payload.hex()}")


def main() -> int:
    all_flags = protocol.NANO_LIVENESS_KNOWN_FLAGS
    encoded = protocol.encode_nano_liveness_frame(all_flags)
    if encoded != bytes.fromhex("A55A4002010F75"):
        fail(f"Nano liveness frame differs: {encoded.hex()}")
    if protocol.StreamDecoder().feed(encoded) != [
        protocol.Frame(
            protocol.TYPE_NANO_LIVENESS,
            bytes((protocol.NANO_LIVENESS_VERSION, all_flags)),
        )
    ]:
        fail("Nano liveness frame does not round-trip")
    for flags in (0, 0x10, 0xFF):
        try:
            protocol.encode_nano_liveness_frame(flags)
        except ValueError:
            pass
        else:
            fail(f"invalid Nano liveness flags {flags:02X} were encoded")

    expect_error(b"\x01", "Nano liveness payload length is not two")
    expect_error(b"\x02\x01", "Nano liveness version 2 != 1")
    expect_error(b"\x01\x11", "Nano liveness flags contain unknown bits")
    expect_error(b"\x01\x00", "Nano liveness record is not enabled")

    duplicate = fresh_session()
    frame = protocol.Frame(
        protocol.TYPE_NANO_LIVENESS,
        bytes((protocol.NANO_LIVENESS_VERSION, all_flags)),
    )
    duplicate._accept_nano_liveness(frame)
    try:
        duplicate._accept_nano_liveness(frame)
    except host.SessionError as error:
        if str(error) != "duplicate Nano liveness record":
            fail(f"duplicate error differs: {error!s}")
    else:
        fail("duplicate Nano liveness record was accepted")

    after_banner = fresh_session()
    after_banner.banner_payload = b"\x01\x09\xDF\x64"
    try:
        after_banner._accept_nano_liveness(frame)
    except host.SessionError as error:
        if str(error) != "Nano liveness record arrived after the ROM banner":
            fail(f"post-banner error differs: {error!s}")
    else:
        fail("post-banner Nano liveness record was accepted")

    loader_phase = fresh_session()
    loader_phase.banner_payload = b"\x01\x09\xDF\x64"
    loader_phase.frames = [frame]
    try:
        loader_phase._wait_loader_frame(
            protocol.TYPE_LOADER_READY,
            0,
            1.0,
            "LOADER_READY",
        )
    except host.SessionError as error:
        if str(error) != "Nano liveness record arrived after the ROM banner":
            fail(f"loader-phase liveness error differs: {error!s}")
    else:
        fail("loader-phase Nano liveness record was ignored")

    reader, writer = socket.socketpair()
    try:
        session = host.HostSession(
            reader.fileno(), NullLogs(), 0.1, 0.01, None, None, True
        )
        writer.sendall(encoded)
        with mock.patch.object(host, "pulse_nano_dtr") as pulse:
            try:
                host.run_session_with_retries(session, 2)
            except host.SessionError as error:
                if str(error) != (
                    "timeout after Nano liveness but before session banner"
                ):
                    fail(f"pre-banner liveness timeout differs: {error!s}")
            else:
                fail("Nano liveness without a ROM banner did not abort")
        if pulse.call_count != 1:
            fail("decoded Nano liveness was incorrectly reset-retried")
    finally:
        reader.close()
        writer.close()

    expected = {
        "version": protocol.NANO_LIVENESS_VERSION,
        "flags_hex": "0F",
        "reset_released": True,
        "clock_seen": True,
        "mrdc_seen": True,
    }
    if session.nano_liveness != expected:
        fail(f"Nano liveness evidence differs: {session.nano_liveness!r}")
    if len(session.attempts) != 1:
        fail("Nano liveness no-banner failure produced multiple attempts")
    attempt = session.attempts[0]
    if (
        attempt.get("outcome") != "error"
        or attempt.get("nano_liveness") != expected
        or attempt.get("decoded_frames") != 1
    ):
        fail(f"attempt did not retain Nano liveness evidence: {attempt!r}")
    summary = session.summary("error", attempt["error"])
    nano_control = summary.get("nano_control")
    if not isinstance(nano_control, dict) or nano_control.get("liveness") != expected:
        fail("summary did not retain Nano liveness evidence")

    print(
        "JUKURAVI-HOST-LIVENESS: PASS "
        "(exact frame; validation; durable evidence; no missing-banner retry)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
