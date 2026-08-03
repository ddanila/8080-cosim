#!/usr/bin/env python3
"""Prove a repeated T28 execution ID replays completion without re-execution."""

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
    print(f"JUKURAVI-T28-REPLAY: FAIL: {message}", file=sys.stderr)
    raise SystemExit(1)


def main() -> int:
    if len(sys.argv) != 3:
        fail("usage: test.py /path/to/trace diag-d0-buffer-verified.bin")
    trace, rom_arg = (Path(value).resolve() for value in sys.argv[1:])
    image, metadata = firmware.build()
    if not trace.is_file() or rom_arg.read_bytes() != image:
        fail("trace or exact T28 image differs")

    # LDA 4100h / INR A / STA 4100h / RET. Re-execution is directly visible.
    payload = bytes((0x3A, 0x00, 0x41, 0x3C, 0x32, 0x00, 0x41, 0xC9))
    with tempfile.TemporaryDirectory(prefix="jukuravi-t28-replay-") as temp_name:
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
        )
        logs_finished = False
        try:
            session.begin_attempt(1)
            session.run()
            status_index = max(
                index
                for index, frame in enumerate(session.frames)
                if frame.record_type == protocol.TYPE_DIAG_STATUS
                and len(frame.payload) == 1
                and frame.payload[0] & 0x80
            )
            session.symbol_requests.clear()
            _, cursor = session._wait_loader_frame(
                protocol.TYPE_LOADER_READY, status_index + 1, 30, "T28 READY"
            )

            for transaction, address, data in (
                (0x10, 0x4000, payload),
                (0x11, 0x4100, b"\x00"),
            ):
                response, cursor, _ = session._loader_v2_transact(
                    protocol.encode_loader_v2_load(transaction, address, data),
                    transaction,
                    protocol.TYPE_LOADER_V2_RESULT,
                    cursor,
                    30,
                    "replay-test LOAD",
                )
                if host.decode_loader_v2_result(response)["status"] != protocol.LOADER_STATUS_OK:
                    fail("setup LOAD failed")

            def invoke(transaction: int, execution_id: int) -> int:
                nonlocal cursor
                command = protocol.encode_loader_v2_run(
                    transaction,
                    0x4000,
                    protocol.LOADER_V2_RUN_CALL,
                    execution_id,
                )
                response, cursor, _ = session._loader_v2_transact(
                    command,
                    transaction,
                    protocol.TYPE_LOADER_V2_RESULT,
                    cursor,
                    30,
                    "replay-test RUN",
                )
                detail = host.decode_loader_v2_result(response)
                if detail["status"] != protocol.LOADER_STATUS_OK:
                    fail(f"RUN failed: {detail!r}")
                while True:
                    returned, cursor = session._wait_loader_frame(
                        protocol.TYPE_LOADER_V2_RETURN, cursor, 30, "replay-test RETURN"
                    )
                    if returned.payload and returned.payload[0] == transaction:
                        break
                if len(returned.payload) != 3:
                    fail("RETURN length differs")
                return returned.payload[2]

            execution_id = 0x89ABCDEF
            first = invoke(0x20, execution_id)
            replayed = invoke(0x20, execution_id)
            second = invoke(0x21, execution_id + 1)

            detail, counter, cursor, _ = session._loader_v2_data_command(
                protocol.TYPE_LOADER_V2_READ,
                0x30,
                bytes((0x41, 0x00, 0x01)),
                cursor,
                30,
                "replay-test READ",
            )
            if detail["status"] != protocol.LOADER_STATUS_OK:
                fail("counter READ failed")
            if (first, replayed, second, counter) != (1, 1, 2, b"\x02"):
                fail(
                    "execution/replay evidence differs: "
                    f"first={first} replay={replayed} second={second} "
                    f"counter={counter.hex()}"
                )
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
        "JUKURAVI-T28-REPLAY: PASS "
        "(same execution ID replayed A=01 without a second side effect)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
