#!/usr/bin/env python3
"""Prove T28 rejects parser-buffer corruption and remains controllable."""

from __future__ import annotations

import os
import pty
import subprocess
import sys
import tempfile
import time
import tty
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FIRMWARE = ROOT / "spinoffs" / "jukuravi" / "firmware"
sys.path[:0] = [str(FIRMWARE.parent), str(FIRMWARE)]
import host  # noqa: E402
import protocol  # noqa: E402
import build_d0_buffer_verified as firmware  # noqa: E402


def fail(message: str) -> None:
    print(f"JUKURAVI-T28-STRONG-CRC: FAIL: {message}", file=sys.stderr)
    raise SystemExit(1)


def main() -> int:
    if len(sys.argv) != 3:
        fail("usage: test.py /path/to/trace diag-d0-buffer-verified.bin")
    trace, rom_arg = (Path(value).resolve() for value in sys.argv[1:])
    image, metadata = firmware.build()
    if not trace.is_file() or rom_arg.read_bytes() != image:
        fail("trace or exact T28 image differs")

    with tempfile.TemporaryDirectory(prefix="jukuravi-t28-crc-") as temp_name:
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
                [str(trace), str(rom), "2000000000"],
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
        try:
            session.begin_attempt(1)
            session.run()
            ram_status_index = max(
                index
                for index, frame in enumerate(session.frames)
                if frame.record_type == protocol.TYPE_DIAG_STATUS
                and len(frame.payload) == 1
                and frame.payload[0] & 0x80
            )
            session.symbol_requests.clear()
            _, cursor = session._wait_loader_frame(
                protocol.TYPE_LOADER_READY,
                ram_status_index + 1,
                30,
                "T28 READY",
            )

            command = bytearray(
                protocol.encode_loader_v2_command(protocol.TYPE_LOADER_V2_PROBE, 0x42, b"X")
            )
            command[5] ^= 0x01
            command[-1] = protocol.crc8_atm(bytes(command[2:-1]))
            session._send_loader_frame(bytes(command), 30, "inner-corrupt PROBE")
            response, cursor = session._wait_loader_frame(
                protocol.TYPE_LOADER_V2_RESULT,
                cursor,
                30,
                "strong-CRC rejection",
            )
            detail = host.decode_loader_v2_result(response)
            if (
                detail["transaction"] != 0x42
                or detail["command"] != protocol.TYPE_LOADER_V2_PROBE
                or detail["status"] != protocol.LOADER_STATUS_STRONG_CRC
            ):
                fail(f"detailed strong-CRC result differs: {detail!r}")

            resync, cursor, _ = session._loader_v2_result_command(
                protocol.TYPE_LOADER_V2_RESYNC,
                0x43,
                b"",
                cursor,
                30,
                "post-corruption RESYNC",
            )
            if resync["status"] != protocol.LOADER_STATUS_OK:
                fail(f"loader did not remain controllable: {resync!r}")
            session.finish_attempt("ok")
            logs.finish(session.summary("ok"))
        finally:
            if not logs._rx.closed:
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
        "JUKURAVI-T28-STRONG-CRC: PASS "
        "(outer CRC repaired; stored-command CRC rejected; RESYNC succeeded)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
