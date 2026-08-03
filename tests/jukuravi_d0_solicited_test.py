#!/usr/bin/env python3
"""Exercise T25 through a lossy, corrupting bidirectional serial proxy."""

from __future__ import annotations

import os
import pty
import select
import subprocess
import sys
import tempfile
import threading
import tty
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HOST = ROOT / "spinoffs" / "jukuravi" / "host.py"
sys.path[:0] = [
    str(ROOT / "spinoffs" / "jukuravi"),
    str(ROOT / "spinoffs" / "jukuravi" / "firmware"),
]
import build_d0_solicited as firmware  # noqa: E402


def fail(message: str) -> None:
    print(f"JUKURAVI-D0-SOLICITED: FAIL: {message}", file=sys.stderr)
    raise SystemExit(1)


def main() -> int:
    if len(sys.argv) != 3:
        fail("usage: test.py /path/to/trace diag-d0-solicited.bin")
    trace, rom = (Path(value).resolve() for value in sys.argv[1:])
    image, metadata = firmware.build()
    if rom.read_bytes() != image:
        fail("ROM differs from generated T25 image")

    juku_master, juku_slave = pty.openpty()
    host_master, host_slave = pty.openpty()
    tty.setraw(juku_slave)
    tty.setraw(host_slave)
    stopped = threading.Event()
    evidence = {
        "host_bytes": 0, "requests": 0, "drops": 0,
        "host_drops": 0, "corruptions": 0,
    }

    def relay() -> None:
        while not stopped.is_set():
            readable, _, _ = select.select(
                (juku_master, host_slave), (), (), 0.05
            )
            for fd in readable:
                try:
                    data = os.read(fd, 1)
                except OSError:
                    continue
                if not data:
                    continue
                byte = data[0]
                if fd == juku_master:
                    if byte in (0xC6, 0xC7):
                        evidence["requests"] += 1
                        if evidence["requests"] in (10, 75, 190):
                            evidence["drops"] += 1
                            continue
                    os.write(host_slave, data)
                else:
                    evidence["host_bytes"] += 1
                    if evidence["host_bytes"] == 454:
                        # Six adaptive-handshake bytes plus 8 logical LOAD
                        # frame bytes * 8 bits * 7 votes: delete the final
                        # physical LOAD symbol after the host thinks it sent
                        # the complete frame.
                        evidence["host_drops"] += 1
                        continue
                    if evidence["host_bytes"] in (40, 120):
                        byte = 0x00
                        evidence["corruptions"] += 1
                    elif evidence["host_bytes"] in (200, 310):
                        if byte == 0x55:
                            byte = 0xAA
                        elif byte == 0xAA:
                            byte = 0x55
                        evidence["corruptions"] += 1
                    os.write(juku_master, bytes((byte,)))

    relay_thread = threading.Thread(target=relay, daemon=True)
    relay_thread.start()
    try:
        with tempfile.TemporaryDirectory() as temp_name:
            temp = Path(temp_name)
            program = temp / "halt.bin"
            program.write_bytes(b"\x76")
            environment = os.environ.copy()
            environment.update(
                JUKU_USART_PTY=os.ttyname(juku_slave),
                JUKU_USART_TRANSFER_CYCLES="64",
                JUKU_USART_BYTE_CYCLES="512",
            )
            cosim = subprocess.Popen(
                [str(trace), str(rom), "5000000000"],
                cwd=temp,
                env=environment,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
            )
            try:
                host = subprocess.run(
                    [
                        sys.executable, str(HOST), "--fd", str(host_master),
                        "--timeout", "60", "--banner-timeout", "30",
                        "--expect-rom-version", f"{firmware.ROM_VERSION:02X}",
                        "--expect-crc16", f"{int(metadata['checksum']):04X}",
                        "--load", str(program), "--load-address", "4000",
                        "--run-address", "4000", "--loader-timeout", "30",
                        "--log-dir", str(temp / "logs"),
                    ],
                    cwd=ROOT,
                    pass_fds=(host_master,),
                    text=True,
                    capture_output=True,
                    timeout=90,
                )
            finally:
                cosim.terminate()
                cosim.wait(timeout=5)
            if host.returncode:
                fail(f"lossy upload failed:\n{host.stdout}{host.stderr}")
            if "run acknowledged address=0x4000" not in host.stdout:
                fail("host did not acknowledge uploaded HLT execution")
            if (
                evidence["drops"] != 3
                or evidence["host_drops"] != 1
                or evidence["corruptions"] != 4
            ):
                fail(f"fault injection evidence differs: {evidence}")
    finally:
        stopped.set()
        relay_thread.join(timeout=1)
        for fd in (juku_master, juku_slave, host_master, host_slave):
            os.close(fd)

    print(
        "JUKURAVI-D0-SOLICITED: PASS "
        f"(request drops={evidence['drops']}; final-symbol drops="
        f"{evidence['host_drops']}; corruptions={evidence['corruptions']})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
