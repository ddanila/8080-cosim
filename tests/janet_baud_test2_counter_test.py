#!/usr/bin/env python3
"""Guard optional Linux serial counters used by resilient BAUDTEST2."""

from __future__ import annotations

import errno
import io
import sys
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import janet_baud_test2 as baudtest2  # noqa: E402


def main() -> int:
    sizes: list[int] = []

    def supported(fd: int, request: int, values: object, mutate: bool) -> int:
        del fd, request, mutate
        sizes.append(len(values))  # type: ignore[arg-type]
        for index in range(11):
            values[index] = index + 10  # type: ignore[index]
        return 0

    with mock.patch.object(baudtest2.fcntl, "ioctl", side_effect=supported):
        counters = baudtest2.serial_counters(7)
    if sizes != [20] or counters is None:
        raise SystemExit(
            f"BAUDTEST2-COUNTERS: FAIL: ioctl buffer/counters {sizes} {counters}"
        )
    if counters["cts"] != 10 or counters["buffer_overrun"] != 20:
        raise SystemExit(
            f"BAUDTEST2-COUNTERS: FAIL: counter mapping {counters}"
        )

    for error in (
        OSError(errno.ENOTTY, "unsupported"),
        SystemError("driver returned an incompatible payload"),
    ):
        with mock.patch.object(baudtest2.fcntl, "ioctl", side_effect=error):
            if baudtest2.serial_counters(7) is not None:
                raise SystemExit(
                    "BAUDTEST2-COUNTERS: FAIL: optional ioctl failure escaped"
                )

    console = io.StringIO()
    logfile = io.StringIO()
    with mock.patch.object(baudtest2.time, "strftime", return_value="STAMP"):
        tee = baudtest2.TimestampedTee(console, logfile, "INFO")
        tee.write("first\nsecond")
        tee.write(" half\n")
    expected = "[STAMP] [INFO] first\n[STAMP] [INFO] second half\n"
    if console.getvalue() != expected or logfile.getvalue() != expected:
        raise SystemExit(
            "BAUDTEST2-COUNTERS: FAIL: timestamped tee differs "
            f"{console.getvalue()!r} {logfile.getvalue()!r}"
        )

    print(
        "BAUDTEST2-COUNTERS: PASS "
        "(20-int ABI; optional failures contained; timestamped tee)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
