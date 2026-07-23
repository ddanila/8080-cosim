#!/usr/bin/env python3
"""Guard the host's dependency-free classic-Nano DTR restart sequence."""

from __future__ import annotations

import errno
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

    print(
        "JUKURAVI-HOST-DTR: PASS "
        "(release/wait/assert/flush; failure context; opt-out contract)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
