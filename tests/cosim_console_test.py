#!/usr/bin/env python3
"""Guard cosim's interactive console PTY (JUKU_CONSOLE_PTY).

Output: characters the firmware passes to the ROM's console routine are
mirrored to the terminal, so the boot banner arrives as text.
Input: bytes written to the terminal reach the emulated key matrix, so a
typed command produces its output.

Both directions run against the committed ekta4401 remix, whose `H` command
prints a known help text -- a deterministic round trip through the real ROM
console path rather than a pixel comparison.
"""

from __future__ import annotations

import os
import re
import select
import subprocess
import sys
import tempfile
import time
import tty
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ROM = ROOT / "spinoffs" / "jukuravi" / "remix" / "ekta4401.bin"
BANNER = "EktaSoft&D.Sukharev"
HELP_MARKER = "this help"
ATTACH_TIMEOUT = 15.0
BOOT_TIMEOUT = 25.0
REPLY_TIMEOUT = 25.0


def fail(message: str) -> None:
    print(f"COSIM-CONSOLE-TEST: FAIL: {message}", file=sys.stderr)
    raise SystemExit(1)


def read_until(fd: int, marker: str, timeout: float) -> str:
    text = ""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        ready, _, _ = select.select([fd], [], [], 0.2)
        if not ready:
            continue
        try:
            chunk = os.read(fd, 8192)
        except OSError:
            break
        if not chunk:
            break
        text += chunk.decode("ascii", "replace")
        if marker in text:
            return text
    return text


def main() -> int:
    if len(sys.argv) != 2:
        fail("usage: test.py /path/to/cosim-trace")
    trace = Path(sys.argv[1]).resolve()
    if not trace.is_file() or not ROM.is_file():
        fail("missing cosim executable or ekta4401 image")

    with tempfile.TemporaryDirectory(prefix="cosim-console-") as name:
        work = Path(name)
        log = work / "cosim.log"
        environment = os.environ.copy()
        environment.update(
            JUKU_CONSOLE_PTY="auto",
            # Real-time pacing: an interactive session needs the machine to
            # run at a speed a human (or this test) can type into.
            JUKU_REALTIME_HZ="2000000",
        )
        with log.open("w") as stream:
            cosim = subprocess.Popen(
                [str(trace), str(ROM), "600000000", "0", "200000"],
                cwd=work, env=environment,
                stdout=subprocess.DEVNULL, stderr=stream)
        try:
            console = None
            deadline = time.monotonic() + ATTACH_TIMEOUT
            while time.monotonic() < deadline and not console:
                found = re.search(r"\[TERM\] PTY slave=(\S+)", log.read_text())
                if found:
                    console = found.group(1)
                else:
                    time.sleep(0.05)
            if not console:
                fail("cosim never reported a console PTY")

            fd = os.open(console, os.O_RDWR | os.O_NOCTTY)
            tty.setraw(fd)
            try:
                boot = read_until(fd, BANNER, BOOT_TIMEOUT)
                if BANNER not in boot:
                    fail(f"boot banner never reached the console: {boot[:120]!r}")

                os.write(fd, b"H")
                reply = read_until(fd, HELP_MARKER, REPLY_TIMEOUT)
                if HELP_MARKER not in reply:
                    fail(
                        "typed key did not reach the key matrix, or its output "
                        f"did not return: {reply[:120]!r}"
                    )
            finally:
                os.close(fd)
        finally:
            if cosim.poll() is None:
                cosim.terminate()
                try:
                    cosim.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    cosim.kill()

    print("COSIM-CONSOLE-TEST: PASS (banner out, typed command in)", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
