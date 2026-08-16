#!/usr/bin/env python3
"""Prove quick POST and keyless 19200 boot of the network-first ROM."""

from __future__ import annotations

import errno
import os
import pty
import re
import select
import subprocess
import sys
import tempfile
import time
import tty
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FIRMWARE = ROOT / "spinoffs" / "jukuravi" / "network-rom"
sys.path.insert(0, str(FIRMWARE))
sys.path.insert(0, str(ROOT))
import build_network_rom as network_rom  # noqa: E402
from tools.janet_fastboot import (  # noqa: E402
    AUTO_ROM_READY,
    extension_packet,
    wait_byte,
)
from tools.janet_netboot import write_all  # noqa: E402


def fail(message: str) -> None:
    raise SystemExit(f"NETWORK-FIRST-ROM-BOOT-TEST: {message}")


def parse_state(path: Path) -> dict[str, str]:
    return dict(
        line.split("=", 1) for line in path.read_text().splitlines()
        if "=" in line
    )


def run_post_failure(trace: Path, temporary: Path, label: str, image: bytes,
                     expected: int, extra_env: dict[str, str] | None = None) -> None:
    case = temporary / label
    case.mkdir()
    rom = case / "rom.bin"
    rom.write_bytes(image)
    checkpoint = case / "checkpoint"
    environment = os.environ.copy()
    environment.update(
        JUKU_CHECKPOINT_PREFIX=str(checkpoint),
        JUKU_TRACE_BANK="0",
    )
    if extra_env:
        environment.update(extra_env)
    result = subprocess.run(
        [str(trace), str(rom), "2000000"], cwd=case, env=environment,
        stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, timeout=15.0,
    )
    if result.returncode != 0:
        fail(f"{label} cosim exited {result.returncode}")
    ram = checkpoint.with_suffix(".ram").read_bytes()
    state = parse_state(checkpoint.with_suffix(".state"))
    if ram[0xD610] != expected:
        fail(f"{label} POST status={ram[0xD610]:02X}, expected {expected:02X}")
    if state.get("halted") != "1" or state.get("mode") != "0" or \
            state.get("iff") != "0" or state.get("portc") != "80" or \
            state.get("pic_icw1") != "D6" or \
            state.get("pic_icw2") != "FE" or \
            state.get("pic_mask") != "FF" or \
            state.get("ppi1_control") != "9B":
        fail(f"{label} failure did not stop safely in reset view: {state}")
    if int(state["cyc"]) >= 1500000:
        fail(f"{label} POST failure was not bounded: {state['cyc']} cycles")


def wait_ack(fd: int, process: subprocess.Popen[bytes], timeout: float) -> bool:
    deadline = time.monotonic() + timeout
    probe = 0
    while time.monotonic() < deadline and process.poll() is None:
        try:
            write_all(fd, (b"\0" if probe else b"") + b"\xA5\x3A")
            probe += 1
        except OSError as error:
            if error.errno != errno.EIO:
                raise
            time.sleep(0.01)
            continue
        ready, _, _ = select.select([fd], [], [], 0.03)
        if ready:
            try:
                if b"\xC5" in os.read(fd, 4096):
                    return True
            except OSError as error:
                if error.errno != errno.EIO:
                    raise
        time.sleep(0.01)
    return False


def run_reset_recovery(trace: Path, temporary: Path, image: bytes,
                       metadata: dict[str, object]) -> None:
    """Reset during an extension body, then boot on the same host link."""
    case = temporary / "reset-recovery"
    case.mkdir()
    rom = case / "rom.bin"
    rom.write_bytes(image)
    master, slave = pty.openpty()
    tty.setraw(slave)
    tty_name = os.ttyname(slave)

    def launch(name: str) -> tuple[subprocess.Popen[bytes], Path]:
        checkpoint = case / name
        environment = os.environ.copy()
        environment.update(
            JUKU_USART_PTY=tty_name,
            JUKU_USART_TRANSFER_CYCLES="16",
            JUKU_USART_BYTE_CYCLES="1024",
            JUKU_USART_PIT_CLOCK="1",
            JUKU_USART_PIT_CPU_HZ="1700000",
            JUKU_CHECKPOINT_PREFIX=str(checkpoint),
            JUKU_STOP_PC="0x0305",
            JUKU_STOP_PC_AFTER_USART_RX="500",
            JUKU_TRACE_BANK="1",
            JUKU_DISABLE_SETTLE="1",
            JUKU_REALTIME_HZ="20000000",
        )
        return subprocess.Popen(
            [str(trace), str(rom), "500000000"], cwd=case, env=environment,
            stdout=subprocess.DEVNULL, stderr=subprocess.PIPE,
        ), checkpoint

    extension = bytes((0x3E, 0x5A, 0x32, 0x00, 0x4E)).ljust(
        int(metadata["fastboot_extension_bytes"]), b"\0",
    )
    packet = extension_packet(extension)
    first, _ = launch("first")
    second: subprocess.Popen[bytes] | None = None
    try:
        if not wait_byte(master, AUTO_ROM_READY, 2.0) or \
                not wait_ack(master, first, 5.0):
            fail("reset fixture did not begin its first extension")
        partial = bytes(packet[2:2 + (len(packet) - 2) // 2])
        write_all(master, partial)
        time.sleep(0.05)
        first.terminate()
        first.wait(timeout=5.0)

        second, checkpoint = launch("second")
        if not wait_byte(master, AUTO_ROM_READY, 2.0) or \
                not wait_ack(master, second, 5.0):
            fail("reset fixture did not reacquire the restarted target")
        write_all(master, packet[2:])
        time.sleep(0.10)
        if second.poll() is None:
            if not wait_ack(master, second, 5.0):
                fail("reset fixture did not discard its stale partial body")
            write_all(master, packet[2:])
        second.wait(timeout=20.0)
        state = parse_state(checkpoint.with_suffix(".state"))
        ram = checkpoint.with_suffix(".ram").read_bytes()
        if second.returncode != 0 or state.get("pc") != "0305" or \
                state.get("mode") != "1" or ram[0x4E00] != 0x5A:
            detail = second.stderr.read().decode(errors="replace") \
                if second.stderr is not None else ""
            fail(f"reset-mid-extension recovery differs: {state}; {detail[-800:]}")
    finally:
        for process in (first, second):
            if process is not None and process.poll() is None:
                process.kill()
                process.wait()
        os.close(master)
        os.close(slave)


def main() -> int:
    if len(sys.argv) != 2:
        fail("usage: test.py /path/to/trace")
    trace = Path(sys.argv[1]).resolve()
    image, metadata = network_rom.build()

    with tempfile.TemporaryDirectory(prefix="network-first-rom-boot.") as name:
        temporary = Path(name)

        cpu_bad = bytearray(image)
        cpu_vector = bytes.fromhex("3E 7F C6 01 F2")
        if cpu_bad.count(cpu_vector) != 1:
            fail("CPU diagnostic vector signature differs")
        cpu_bad[cpu_bad.index(cpu_vector) + 1] = 0x7E  # 7F+1 no longer 80
        run_post_failure(trace, temporary, "cpu", bytes(cpu_bad), 0xC1)
        run_post_failure(
            trace, temporary, "ram", image, 0xC2,
            {"JUKU_RAM_FAULT": "0xD400:0x01:0"},
        )
        run_post_failure(
            trace, temporary, "address", image, 0xC3,
            {"JUKU_RAM_ALIAS": "0xC0:0xC1"},
        )
        rom_bad = bytearray(image)
        rom_bad[0x1800] ^= 0x01
        run_post_failure(trace, temporary, "rom", bytes(rom_bad), 0xC4)
        run_post_failure(
            trace, temporary, "pit", image, 0xC5,
            {"JUKU_PIT_FAULT": "18:00:80"},
        )
        run_post_failure(
            trace, temporary, "usart", image, 0xC5,
            {
                "JUKU_USART_PTY": "auto",
                "JUKU_USART_FAULT": "tx_not_ready_once_after:0",
            },
        )

        case = temporary / "automatic"
        case.mkdir()
        rom = case / "rom.bin"
        rom.write_bytes(image)
        checkpoint = case / "checkpoint"
        master, slave = pty.openpty()
        tty.setraw(slave)
        environment = os.environ.copy()
        environment.update(
            JUKU_USART_PTY=os.ttyname(slave),
            JUKU_USART_TRANSFER_CYCLES="16",
            JUKU_USART_BYTE_CYCLES="1024",
            JUKU_USART_PIT_CLOCK="1",
            JUKU_USART_PIT_CPU_HZ="1700000",
            JUKU_CHECKPOINT_PREFIX=str(checkpoint),
            JUKU_STOP_PC="0x0305",
            JUKU_STOP_PC_AFTER_USART_RX="500",
            JUKU_TRACE_BANK="1",
            JUKU_TRACE_TIMING="1",
            JUKU_REALTIME_HZ="20000000",
        )
        process = subprocess.Popen(
            [str(trace), str(rom), "500000000"], cwd=case, env=environment,
            stdout=subprocess.DEVNULL, stderr=subprocess.PIPE,
        )
        os.close(slave)
        try:
            # With no host, the bounded parser keeps looking; it neither halts
            # nor requires RESET. This delay is deliberately before any byte.
            time.sleep(0.25)
            if process.poll() is not None:
                early_stderr = process.stderr.read().decode(errors="replace") \
                    if process.stderr is not None else ""
                fail(
                    "automatic core stopped before a host appeared: "
                    f"rc={process.returncode}; {early_stderr[-800:]}"
                )
            if not wait_byte(master, AUTO_ROM_READY, 2.0):
                fail("automatic core did not announce its C4 readiness")

            extension = bytes((0x3E, 0x5A, 0x32, 0x00, 0x4E)).ljust(
                int(metadata["fastboot_extension_bytes"]), b"\0",
            )
            packet = extension_packet(extension)
            corrupted = bytearray(packet)
            corrupted[20] ^= 0x01

            if not wait_ack(master, process, 5.0):
                process.terminate()
                process.wait(timeout=5.0)
                detail = process.stderr.read().decode(errors="replace") \
                    if process.stderr is not None else ""
                fail(
                    "automatic core did not acknowledge extension header: "
                    f"rc={process.returncode}; {detail[-1200:]}"
                )
            write_all(master, bytes(corrupted[2:]))
            time.sleep(0.10)
            if process.poll() is not None:
                fail("corrupt extension escaped into execution")

            if not wait_ack(master, process, 5.0):
                process.terminate()
                process.wait(timeout=5.0)
                detail = process.stderr.read().decode(errors="replace") \
                    if process.stderr is not None else ""
                debug_state = parse_state(checkpoint.with_suffix(".state")) \
                    if checkpoint.with_suffix(".state").is_file() else {}
                fail(
                    "automatic core did not resynchronize after corruption: "
                    f"state={debug_state}; {detail[-1200:]}"
                )
            write_all(master, packet[2:])
            process.wait(timeout=20.0)
        finally:
            if process.poll() is None:
                process.kill()
                process.wait()
            os.close(master)
        stderr = process.stderr.read().decode(errors="replace") \
            if process.stderr is not None else ""
        if process.returncode != 0:
            fail(f"automatic cosim exited {process.returncode}: {stderr[-800:]}")
        ready_match = re.search(
            r"\[IOT\] first OUT port 0x08 val=0xC4 cyc=(\d+)", stderr,
        )
        if ready_match is None:
            fail("automatic core readiness has no cycle-stamped evidence")
        ready_cycles = int(ready_match.group(1))
        if ready_cycles >= 1_000_000:
            fail(f"successful quick POST took {ready_cycles} cycles")
        state = parse_state(checkpoint.with_suffix(".state"))
        ram = checkpoint.with_suffix(".ram").read_bytes()
        if state.get("pc") != "0305" or state.get("mode") != "1" or \
                state.get("iff") != "0" or state.get("portc") != "81" or \
                state.get("pic_icw1") != "D6" or \
                state.get("pic_icw2") != "FE" or \
                state.get("pic_mask") != "FF" or \
                state.get("ppi1_control") != "9B":
            fail(f"valid extension handoff state differs: {state}")
        if ram[0xD610] != 0:
            fail(f"successful quick POST status is {ram[0xD610]:02X}")
        core_bytes = int(metadata["fastboot_core_bytes"])
        expected_core = bytearray(image[0x0F00:0x0F00 + core_bytes])
        redirected_call = bytes.fromhex("CD 80 01 FE A5")
        if expected_core.count(redirected_call) != 1:
            fail("stored V15 ready-prelude call signature differs")
        operand = expected_core.index(redirected_call) + 1
        expected_core[operand:operand + 2] = bytes.fromhex("73 01")
        if ram[0x0100:0x0100 + core_bytes] != expected_core:
            fail("installed V15 core differs after its one-shot ready patch")
        if ram[0x0300:0x0300 + len(extension)] != extension:
            fail("valid extension was not installed byte-exactly")
        if ram[0x4E00] != 0x5A:
            fail("automatically loaded extension did not execute")
        if int(state.get("usart_rx_bytes", "0")) < len(packet) * 2:
            fail("corrupt-then-valid recovery did not consume both transfers")
        if state.get("usart_mode") != "4E" or \
                state.get("port_18", "").split(",", 1)[0] != "last:04":
            fail("automatic core did not retain proven 19200/8N1 state")
        for port, expected in (
            ("07", "0F"), ("10", "64"), ("11", "24"), ("12", "08"),
            ("14", "01"), ("15", "00"), ("16", "25"), ("17", "34"),
            ("1A", "FF"),
        ):
            if state.get(f"port_{port}", "").split(",", 1)[0] != \
                    f"last:{expected}":
                fail(f"automatic boot lost reset timer state at port {port}")

        run_reset_recovery(trace, temporary, image, metadata)

    print(
        "NETWORK-FIRST-ROM-BOOT-TEST: PASS "
        f"{metadata['image_sha256']} (POST C1/C2/C3/C4/C5; "
        f"ready={ready_cycles} cycles; absent host; corrupt recovery; "
        "reset-mid-extension recovery; keyless 19200 handoff)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
