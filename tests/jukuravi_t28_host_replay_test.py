#!/usr/bin/env python3
"""Prove the host recovers a lost RETURN without running a snippet twice."""

from __future__ import annotations

import os
import pty
import subprocess
import sys
import tempfile
import tty
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FIRMWARE = ROOT / "spinoffs" / "jukuravi" / "firmware"
sys.path[:0] = [str(FIRMWARE.parent), str(FIRMWARE)]
import build_d0_buffer_verified as firmware  # noqa: E402
import host  # noqa: E402
import protocol  # noqa: E402


def fail(message: str) -> None:
    print(f"JUKURAVI-T28-HOST-REPLAY: FAIL: {message}", file=sys.stderr)
    raise SystemExit(1)


def main() -> int:
    if len(sys.argv) != 3:
        fail("usage: test.py /path/to/trace diag-d0-buffer-verified.bin")
    trace, rom_arg = (Path(value).resolve() for value in sys.argv[1:])
    image, metadata = firmware.build()
    if not trace.is_file() or rom_arg.read_bytes() != image:
        fail("trace or exact T28 image differs")

    # Increment the byte embedded at 4008h, return its new value, RET.
    payload = bytes((0x3A, 0x08, 0x40, 0x3C, 0x32, 0x08, 0x40, 0xC9, 0x00))
    with tempfile.TemporaryDirectory(prefix="jukuravi-t28-host-replay-") as temp_name:
        temp = Path(temp_name)
        rom = temp / "t28.bin"
        rom.write_bytes(image)
        master, slave = pty.openpty()
        tty.setraw(slave)
        environment = os.environ.copy()
        environment.update(
            JUKU_USART_PTY=os.ttyname(slave),
            JUKU_USART_TRANSFER_CYCLES="64",
            JUKU_USART_BYTE_CYCLES="512",
        )
        with (temp / "cosim.stdout").open("wb") as stdout, (
            temp / "cosim.stderr"
        ).open("wb") as stderr:
            cosim = subprocess.Popen(
                [str(trace), str(rom), "3000000000"],
                cwd=temp,
                env=environment,
                stdout=stdout,
                stderr=stderr,
            )
        logs = host.SessionLogs(temp / "logs", "cosim")
        session = host.HostSession(
            master,
            logs,
            60,
            30,
            firmware.ROM_VERSION,
            int(metadata["checksum"]),
            False,
            0.0,
            loader_retries=3,
            result_address=0x4008,
            result_length=1,
        )
        logs_finished = False
        try:
            session.begin_attempt(1)
            session.run()

            original_wait = session._wait_loader_frame
            dropped = False

            def drop_first_return(
                record_type: int,
                cursor: int,
                timeout: float,
                description: str,
            ) -> tuple[protocol.Frame, int]:
                nonlocal dropped
                frame, next_cursor = original_wait(
                    record_type, cursor, timeout, description
                )
                if record_type == protocol.TYPE_T28_RETURN and not dropped:
                    dropped = True
                    raise host.LoaderResponseTimeout(
                        next_cursor, "injected lost first RETURN"
                    )
                return frame, next_cursor

            session._wait_loader_frame = drop_first_return  # type: ignore[method-assign]
            session.run_loader(
                payload,
                "<increment-once>",
                0x4000,
                0x4000,
                30,
            )
            run = session.loader.get("run") if session.loader else None
            if (
                not dropped
                or not isinstance(run, dict)
                or run.get("return_replays") != 1
                or run.get("return_a") != "0x01"
                or run.get("result", {}).get("hex") != "01"
            ):
                fail(f"lost-RETURN recovery evidence differs: {run!r}")
            session.finish_attempt("ok")
            logs.finish(session.summary("ok"))
            logs_finished = True
        finally:
            if not logs_finished:
                logs.finish(session.summary("error", "test cleanup"))
            cosim.terminate()
            try:
                cosim.wait(timeout=5)
            except subprocess.TimeoutExpired:
                cosim.kill()
                cosim.wait()
            os.close(master)
            os.close(slave)

    print(
        "JUKURAVI-T28-HOST-REPLAY: PASS "
        "(injected lost RETURN; replay recovered A/RAM; side effect stayed once)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
