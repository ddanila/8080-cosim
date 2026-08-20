#!/usr/bin/env python3
"""Prove ekta4402's N command and ROM-resident V15 core in cosim."""

from __future__ import annotations

import errno
import hashlib
import os
import pty
import select
import subprocess
import sys
import tempfile
import time
import tty
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REMIX = ROOT / "spinoffs" / "jukuravi" / "remix"
sys.path.insert(0, str(REMIX))
sys.path.insert(0, str(ROOT))

import build_ekta4401 as ekta4401  # noqa: E402
import build_ekta4402 as ekta4402  # noqa: E402
from tests.fixtures.legacy_janet_fastboot import extension_packet  # noqa: E402
from tests.fixtures.legacy_janet_netboot import write_all  # noqa: E402


def fail(message: str) -> None:
    raise SystemExit(f"EKTA4402-DIRECT-FASTBOOT-TEST: {message}")


def parse_state(path: Path) -> dict[str, str]:
    return dict(
        line.split("=", 1) for line in path.read_text().splitlines()
        if "=" in line
    )


def wait_for_ack(fd: int, process: subprocess.Popen[bytes]) -> None:
    deadline = time.monotonic() + 20.0
    received = bytearray()
    probe = 0
    while time.monotonic() < deadline and process.poll() is None:
        try:
            write_all(fd, (b"\0" if probe else b"") + b"\xA5\x3A")
        except OSError as error:
            if error.errno != errno.EIO:
                raise
            time.sleep(0.01)  # trace has not opened the PTY slave yet
            continue
        probe += 1
        ready, _, _ = select.select([fd], [], [], 0.025)
        if ready:
            try:
                received.extend(os.read(fd, 4096))
            except OSError as error:
                if error.errno != errno.EIO:
                    raise
                time.sleep(0.01)
                continue
            if 0xC5 in received:
                return
    fail(
        "N did not acknowledge the V15 extension header "
        f"(target rc={process.poll()}, received={received.hex()})"
    )


def main() -> int:
    if len(sys.argv) != 2:
        fail("usage: test.py /path/to/trace")
    trace = Path(sys.argv[1]).resolve()
    if not trace.is_file():
        fail(f"trace executable is missing: {trace}")

    baseline, baseline_metadata = ekta4401.build()
    image, metadata = ekta4402.build()
    if hashlib.sha256(baseline).hexdigest() != \
            "452ecd09406f944162fa2a3e03d52035d86c28e3fc89e77e9abd740644131b18":
        fail("frozen ekta4401 baseline changed")
    if baseline_metadata["commands"] != "FDSXGMCEKTBRWPAHJV":
        fail("frozen ekta4401 command table changed")
    if metadata["commands"] != "FDSXGMCEKTBRWPAHJNV":
        fail(f"unexpected ekta4402 commands: {metadata['commands']}")
    if metadata["direct_core_sha256"] != ekta4401.DIRECT_CORE_SHA256:
        fail("direct core identity differs")

    direct_core = ekta4401.direct_fastboot_core()
    direct_runtime = int(str(metadata["direct_core_runtime"]), 16)
    direct_offset = direct_runtime - 0xC000
    if image[direct_offset:direct_offset + len(direct_core)] != direct_core:
        fail("ROM does not contain the pinned direct core")

    # This valid 267-byte extension stores a marker, then reaches the trace
    # stop PC. Loading it proves N copied and executed the core, initialized
    # D57/D11, recognized the overlap-safe A5/3A handshake, checked Fletcher,
    # installed the extension at 0300h, and transferred control to it.
    extension = bytes((0x3E, 0x5A, 0x32, 0x00, 0x4E)).ljust(0x010B, b"\0")
    packet = extension_packet(extension)

    with tempfile.TemporaryDirectory(prefix="ekta4402-direct-") as name:
        temp = Path(name)
        rom = temp / "ekta4402.bin"
        rom.write_bytes(image)
        prefix = temp / "checkpoint"
        master, slave = pty.openpty()
        tty.setraw(slave)
        environment = os.environ.copy()
        environment.update(
            JUKU_USART_PTY=os.ttyname(slave),
            JUKU_USART_TRANSFER_CYCLES="64",
            JUKU_USART_BYTE_CYCLES="1040",
            JUKU_USART_PIT_CLOCK="1",
            JUKU_KEYS="N",
            JUKU_KEY_HOLD_FRAMES="6",
            JUKU_KEY_GAP_FRAMES="8",
            JUKU_STOP_PC="0x0305",
            JUKU_CHECKPOINT_PREFIX=str(prefix),
            JUKU_TRACE_BANK="0",
            # Keep the target from consuming its intentionally huge cycle
            # budget before the host process gets scheduled to answer it.
            JUKU_REALTIME_HZ="20000000",
        )
        process = subprocess.Popen(
            [str(trace), str(rom), "40000000", "0", "200000"],
            cwd=temp, env=environment,
            stdout=subprocess.DEVNULL, stderr=subprocess.PIPE,
        )
        os.close(slave)
        try:
            wait_for_ack(master, process)
            write_all(master, packet[2:])
            process.wait(timeout=25.0)
        except BaseException:
            if process.poll() is None:
                process.kill()
                process.wait()
            raise
        finally:
            os.close(master)
        stderr = process.stderr.read().decode(errors="replace") \
            if process.stderr is not None else ""
        if process.returncode != 0:
            fail(f"cosim exited {process.returncode}: {stderr[-500:]}")

        state_path = prefix.with_suffix(".state")
        ram_path = prefix.with_suffix(".ram")
        if not state_path.is_file() or not ram_path.is_file():
            fail(f"cosim produced no stop-PC checkpoint: {stderr[-500:]}")
        state = parse_state(state_path)
        ram = ram_path.read_bytes()
        if state.get("pc") != "0305":
            fail(
                f"extension did not reach stop PC: {state.get('pc')}; "
                f"RX={state.get('usart_rx_bytes')}, "
                f"0300={ram[0x0300:0x0310].hex()}"
            )
        if state.get("mode") != "1":
            fail(f"N did not retain mapped-ROM mode 1: {state.get('mode')}")
        if state.get("usart_mode") != "4E" or \
                state.get("usart_command") != "35":
            fail(
                "direct core did not select 19200/8N1 "
                f"({state.get('usart_mode')}/{state.get('usart_command')})"
            )
        if state.get("port_18", "").split(",", 1)[0] != "last:04":
            fail(f"direct D57 divisor differs: {state.get('port_18')}")
        if ram[0x0100:0x0180] != direct_core:
            fail("N did not copy the direct core byte-exactly to 0100h")
        if ram[0x0300:0x0300 + len(extension)] != extension:
            fail("direct core did not install the extension byte-exactly")
        if ram[0x4E00] != 0x5A:
            fail("loaded extension did not execute its marker store")

    print(
        "EKTA4402-DIRECT-FASTBOOT-TEST: PASS "
        f"{metadata['image_sha256']} (N -> V15 core -> 0300h)",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
