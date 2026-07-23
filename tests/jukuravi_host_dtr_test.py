#!/usr/bin/env python3
"""Guard the host's dependency-free classic-Nano DTR restart sequence."""

from __future__ import annotations

import argparse
import errno
import socket
import struct
import sys
import termios
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "spinoffs" / "jukuravi"))
import host  # noqa: E402


def fail(message: str) -> None:
    print(f"JUKURAVI-HOST-DTR: FAIL: {message}", file=sys.stderr)
    raise SystemExit(1)


def main() -> int:
    events: list[tuple[object, ...]] = []

    def record_ioctl(fd: int, request: int, argument: bytes) -> int:
        events.append(("ioctl", fd, request, struct.unpack("i", argument)[0]))
        return 0

    def record_sleep(seconds: float) -> None:
        events.append(("sleep", seconds))

    def record_flush(fd: int, queue: int) -> None:
        events.append(("flush", fd, queue))

    with (
        mock.patch.object(host.fcntl, "ioctl", side_effect=record_ioctl),
        mock.patch.object(host.time, "sleep", side_effect=record_sleep),
        mock.patch.object(host.termios, "tcflush", side_effect=record_flush),
    ):
        host.pulse_nano_dtr(17)

    expected = [
        ("ioctl", 17, termios.TIOCMBIC, termios.TIOCM_DTR),
        ("sleep", host.DTR_RELEASE_SECONDS),
        ("ioctl", 17, termios.TIOCMBIS, termios.TIOCM_DTR),
        ("flush", 17, termios.TCIOFLUSH),
    ]
    if events != expected:
        fail(f"DTR event order differs: {events!r}")

    with mock.patch.object(
        host.fcntl,
        "ioctl",
        side_effect=OSError(errno.ENOTTY, "not a modem-control tty"),
    ):
        try:
            host.pulse_nano_dtr(18)
        except host.SessionError as error:
            if "cannot restart Nano through DTR" not in str(error):
                fail(f"ioctl failure lost context: {error}")
        else:
            fail("ioctl failure did not abort the session")

    parser = host.make_parser()
    normal = parser.parse_args(["--port", "/dev/ttyUSB0"])
    opted_out = parser.parse_args(
        ["--port", "/dev/ttyUSB0", "--no-nano-reset"]
    )
    inherited = parser.parse_args(["--fd", "7"])
    if normal.no_nano_reset or not opted_out.no_nano_reset:
        fail("--no-nano-reset parser contract differs")
    if inherited.no_nano_reset:
        fail("fd transport unexpectedly opts out of a port-only action")
    if normal.banner_timeout != host.DEFAULT_BANNER_TIMEOUT:
        fail("default banner deadline differs")
    if normal.reset_retries != host.DEFAULT_RESET_RETRIES:
        fail("default reset retry count differs")
    try:
        host.parse_nonnegative_int("-1")
    except argparse.ArgumentTypeError:
        pass
    else:
        fail("negative reset retry count was accepted")

    class FakeSession:
        def __init__(self, requested: bool, errors: list[Exception | None]) -> None:
            self.fd = 23
            self.nano_reset_requested = requested
            self.nano_dtr_sequence_completed = False
            self.nano_dtr_sequences_completed = 0
            self.errors = errors
            self.begun: list[int] = []
            self.finished: list[tuple[str, str | None]] = []

        def begin_attempt(self, number: int) -> None:
            self.begun.append(number)

        def finish_attempt(self, outcome: str, error: str | None = None) -> None:
            self.finished.append((outcome, error))

        def run(self) -> None:
            result = self.errors.pop(0)
            if result is not None:
                raise result

    retry_session = FakeSession(
        True, [host.BannerTimeout("timeout before session banner"), None]
    )
    with mock.patch.object(host, "pulse_nano_dtr") as pulse:
        host.run_session_with_retries(retry_session, 2)  # type: ignore[arg-type]
    if pulse.call_count != 2 or retry_session.begun != [1, 2]:
        fail("missing-banner retry did not perform two fresh reset attempts")
    if retry_session.finished != [
        ("banner_timeout", "timeout before session banner"),
        ("ok", None),
    ]:
        fail(f"retry attempt evidence differs: {retry_session.finished!r}")
    if retry_session.nano_dtr_sequences_completed != 2:
        fail("completed DTR sequence count differs after retry")

    exhausted_session = FakeSession(
        True,
        [host.BannerTimeout("timeout before session banner") for _ in range(3)],
    )
    with mock.patch.object(host, "pulse_nano_dtr") as pulse:
        try:
            host.run_session_with_retries(exhausted_session, 2)  # type: ignore[arg-type]
        except host.BannerTimeout:
            pass
        else:
            fail("exhausted missing-banner retries did not abort")
    if pulse.call_count != 3 or exhausted_session.begun != [1, 2, 3]:
        fail("missing-banner retry exceeded or stopped short of its bound")

    post_banner_failure = FakeSession(True, [host.SessionError("invalid survey")])
    with mock.patch.object(host, "pulse_nano_dtr") as pulse:
        try:
            host.run_session_with_retries(post_banner_failure, 2)  # type: ignore[arg-type]
        except host.SessionError:
            pass
        else:
            fail("post-banner session error did not abort")
    if pulse.call_count != 1 or post_banner_failure.begun != [1]:
        fail("post-banner session error was retried")

    no_reset_session = FakeSession(
        False, [host.BannerTimeout("timeout before session banner")]
    )
    with mock.patch.object(host, "pulse_nano_dtr") as pulse:
        try:
            host.run_session_with_retries(no_reset_session, 2)  # type: ignore[arg-type]
        except host.BannerTimeout:
            pass
        else:
            fail("no-reset missing-banner failure did not abort")
    if pulse.call_count != 0 or no_reset_session.begun != [1]:
        fail("no-reset transport unexpectedly retried or pulsed DTR")

    class NullLogs:
        @staticmethod
        def rx(_data: bytes) -> None:
            pass

        @staticmethod
        def tx(_data: bytes) -> None:
            pass

    reader, writer = socket.socketpair()
    try:
        deadline_session = host.HostSession(
            reader.fileno(), NullLogs(), 0.1, 0.01, None, None, False
        )  # type: ignore[arg-type]
        deadline_session.begin_attempt(1)
        try:
            deadline_session.run()
        except host.BannerTimeout:
            pass
        else:
            fail("silent transport did not produce a banner-specific timeout")
    finally:
        reader.close()
        writer.close()

    reader, writer = socket.socketpair()
    try:
        partial_session = host.HostSession(
            reader.fileno(), NullLogs(), 0.1, 0.01, None, None, False
        )  # type: ignore[arg-type]
        partial_session.begin_attempt(1)
        writer.sendall(host.protocol.encode_frame(host.protocol.TYPE_ACK, b""))
        try:
            partial_session.run()
        except host.BannerTimeout:
            fail("partial protocol evidence was classified as retryable")
        except host.SessionError as error:
            if "after protocol frames" not in str(error):
                fail(f"partial-evidence failure lost context: {error}")
        else:
            fail("partial protocol evidence did not abort")
    finally:
        reader.close()
        writer.close()

    print(
        "JUKURAVI-HOST-DTR: PASS "
        "(DTR order; bounded empty-banner retry; partial/post-banner/no-reset guards)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
