#!/usr/bin/env python3
"""Boot the C8 ROM and CP/M Plus using only the native C production host."""

from __future__ import annotations

import os
from pathlib import Path
import select
import signal
import struct
import subprocess
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[1]
CPM = Path(os.environ.get("CPM_PLUS_JUKU_ROOT", ROOT.parent / "cpm-plus-juku"))
ROM = ROOT / "spinoffs/jukuravi/network-rom/juku-network-rom-abi1.3-c8.bin"
SYSTEM = CPM / "out/cpm-plus-juku-network-rom-c8-system.bin"
FASTBOOT = CPM / "out/cpm-plus-juku-network-rom-c8-fastboot-v16.bin"
VOLUME = CPM / "out/cpm-plus-juku-full.img"
HOST = ROOT / "build/jukuhost"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(f"JUKUHOST-C8-COSIM-TEST: {message}")


def read_until(fd: int, marker: bytes, timeout: float) -> bytes:
    result = bytearray()
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        ready, _, _ = select.select([fd], [], [], 0.1)
        if ready:
            result.extend(os.read(fd, 4096))
            if marker in result:
                return bytes(result)
    raise AssertionError(
        f"remote console did not produce {marker!r}: {bytes(result)[-1000:]!r}"
    )


def read_paged(fd: int, timeout: float) -> bytes:
    result = bytearray()
    handled = 0
    page_prompt = b"Press RETURN to Continue"
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        ready, _, _ = select.select([fd], [], [], 0.1)
        if ready:
            result.extend(os.read(fd, 4096))
        if b"A>" in result:
            return bytes(result)
        if page_prompt in result[handled:]:
            os.write(fd, b"\r")
            handled = len(result)
    raise AssertionError(f"paged command did not return: {bytes(result)[-1000:]!r}")


def wait_host_line(process: subprocess.Popen[str], marker: str,
                   timeout: float) -> str:
    assert process.stdout is not None
    result = ""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        ready, _, _ = select.select([process.stdout], [], [], 0.1)
        if not ready:
            continue
        chunk = os.read(process.stdout.fileno(), 4096)
        if not chunk:
            break
        result += chunk.decode(errors="replace")
        if marker in result:
            return result
    raise AssertionError(f"host did not emit {marker!r}: {result}")


def capture_tail(path: Path, records: int = 40) -> str:
    if not path.exists():
        return "<missing>"
    data = path.read_bytes()
    position = 16
    decoded: list[str] = []
    while position + 16 <= len(data):
        kind, flags, length = struct.unpack_from("<BBH", data, position)
        milliseconds = struct.unpack_from("<Q", data, position + 4)[0]
        end = position + 16 + length
        if end > len(data):
            decoded.append(f"truncated record at {position}")
            break
        payload = data[position + 12:position + 12 + length]
        decoded.append(
            f"{milliseconds:08d} {'RX' if kind == 1 else 'TX' if kind == 2 else 'EV'} "
            f"flags={flags:02x} bytes={payload.hex(' ')}"
        )
        position = end
    return "\n".join(decoded[-records:])


def failure_evidence(temp: Path, host: subprocess.Popen[str],
                     simulator: subprocess.Popen[bytes]) -> str:
    if host.poll() is None:
        host.send_signal(signal.SIGINT)
        try:
            host.wait(timeout=2.0)
        except subprocess.TimeoutExpired:
            host.kill()
            host.wait()
    if simulator.poll() is None:
        simulator.send_signal(signal.SIGUSR1)
        time.sleep(0.1)
        simulator.terminate()
        try:
            simulator.wait(timeout=2.0)
        except subprocess.TimeoutExpired:
            simulator.kill()
            simulator.wait()
    host_output = host.stdout.read() if host.stdout else ""
    simulator_output = (temp / "simulator.stderr").read_text(
        errors="replace") if (temp / "simulator.stderr").exists() else ""
    host_log = (temp / "host.log").read_text() \
        if (temp / "host.log").exists() else ""
    state = (temp / "final.state").read_text() \
        if (temp / "final.state").exists() else "<missing>"
    return (
        f"\nHOST OUTPUT:\n{host_output}\nHOST LOG:\n{host_log}"
        f"\nCAPTURE TAIL:\n{capture_tail(temp / 'host.cap')}"
        f"\nSIMULATOR STATE:\n{state}"
        f"\nSIMULATOR:\n{simulator_output[-3000:]}"
    )


def main() -> int:
    required = (ROM, SYSTEM, FASTBOOT, VOLUME, HOST)
    require(all(path.is_file() for path in required),
            "missing C8/CPM artifacts or build/jukuhost")
    discard_ready = os.environ.get("JUKUHOST_C8_DISCARD_READY") == "1"
    replace_host = os.environ.get("JUKUHOST_C8_REPLACE_HOST") == "1"
    reset_during_stream = os.environ.get("JUKUHOST_C8_TARGET_RESET") == "1"
    with tempfile.TemporaryDirectory(prefix="jukuhost-c8-cosim.") as name:
        temp = Path(name)
        trace = temp / "trace"
        subprocess.run([
            os.environ.get("CC", "cc"), "-O2", "-I", str(ROOT / "cosim"),
            "-o", str(trace), str(ROOT / "cosim/trace.c"),
            str(ROOT / "cosim/i8080.c"), str(ROOT / "cosim/juk_disk.c"),
            str(ROOT / "cosim/juku_fdc.c"),
        ], check=True)
        serial_master, serial_slave = os.openpty()
        console_master, console_slave = os.openpty()
        volume = temp / "working.img"
        volume.write_bytes(VOLUME.read_bytes())
        checkpoint = temp / "final"
        environment = os.environ.copy()
        environment.update(
            JUKU_USART_PTY=os.ttyname(serial_slave),
            JUKU_USART_TRANSFER_CYCLES="64",
            JUKU_USART_BYTE_CYCLES="2300",
            JUKU_USART_PIT_CLOCK="1",
            JUKU_USART_PIT_CPU_HZ="1700000",
            JUKU_REALTIME_HZ="20000000",
            JUKU_TRACE_BANK="1",
            JUKU_DISABLE_SETTLE="1",
            # Bit 0 is automatic netboot; bits 2:1 select 80x24.
            JUKU_S21_CONFIG="0x07",
            JUKU_CHECKPOINT_PREFIX=str(checkpoint),
        )
        if reset_during_stream:
            environment["JUKU_RESET_AFTER_USART_RX"] = "900"
        simulator_stderr = (temp / "simulator.stderr").open("wb")
        simulator = subprocess.Popen(
            [str(trace), str(ROM), "1000000000000", "0", "100000"],
            cwd=temp, env=environment, stdout=subprocess.DEVNULL,
            stderr=simulator_stderr,
        )
        if discard_ready:
            time.sleep(0.5)
            discarded = bytearray()
            while select.select([serial_master], [], [], 0.05)[0]:
                discarded.extend(os.read(serial_master, 4096))
            require(b"JR\x10\x01" in discarded,
                    f"one-shot JR16 readiness was not captured: {discarded.hex()}")
        host_command = [
            str(HOST), "--serial-fd", str(serial_master), "--system", str(SYSTEM),
            "--fast-stage", str(FASTBOOT), "--network-rom",
            "--volume", str(volume), "--writable", "--disk-protocol", "3",
            "--disk-baud", "19200", "--read-ahead", "3",
            "--console-pty", os.ttyname(console_slave), "--timeout", "30",
            "--disk-timeout", "120", "--log", str(temp / "host.log"),
            "--capture", str(temp / "host.cap"), "--verbose",
        ]
        host = subprocess.Popen(
            host_command, cwd=ROOT, stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT, text=True, pass_fds=(serial_master,))
        try:
            try:
                transcript = read_until(console_master, b"A>", 25.0)
            except AssertionError as error:
                raise AssertionError(
                    f"{error}{failure_evidence(temp, host, simulator)}"
                ) from error
            require(b"CP/M" in transcript, f"prompt lacked CP/M banner: {transcript!r}")
            # Match the physical acceptance harness: allow the target to
            # enter its idle console path before injecting the first command.
            time.sleep(0.25)
            os.write(console_master, b"DIR\r")
            try:
                directory = read_paged(console_master, 30.0)
            except AssertionError as error:
                raise AssertionError(
                    f"{error}{failure_evidence(temp, host, simulator)}"
                ) from error
            require(b"DIR" in directory or b"COM" in directory,
                    f"DIR produced no directory text: {directory!r}")
            if replace_host:
                host.send_signal(signal.SIGINT)
                host.wait(timeout=5.0)
                require(host.returncode == 0,
                        f"first host exit={host.returncode}")
                reconnect_command = [
                    str(HOST), "--serial-fd", str(serial_master),
                    "--volume", str(volume), "--resume-disk", "--writable",
                    "--disk-protocol", "3", "--disk-baud", "19200",
                    "--read-ahead", "3", "--console-pty",
                    os.ttyname(console_slave), "--disk-timeout", "120",
                    "--log", str(temp / "host-reconnect.log"),
                    "--capture", str(temp / "host-reconnect.cap"), "--verbose",
                ]
                host = subprocess.Popen(
                    reconnect_command, cwd=ROOT, stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT, text=True,
                    pass_fds=(serial_master,),
                )
                wait_host_line(host, "serving A:", 5.0)
                time.sleep(0.25)
                os.write(console_master, b"VER\r")
                resumed = read_until(console_master, b"A>", 30.0)
                require(b"VER" in resumed,
                        f"replacement host did not resume console: {resumed!r}")
            host.send_signal(signal.SIGINT)
            host.wait(timeout=5.0)
            require(host.returncode == 0,
                    f"host exit={host.returncode}: {host.stdout.read() if host.stdout else ''}")
            log = (temp / "host.log").read_text()
            require("Fastboot V16" in log and "requests=" in log,
                    f"host evidence incomplete: {log}")
            if reset_during_stream:
                require("boot-restarts=1" in log and "target-resets=1" in log,
                        f"target-reset recovery evidence differs: {log}")
            require((temp / "host.cap").stat().st_size > 100,
                    "capture is unexpectedly small")
            if replace_host:
                require("stop exit=0" in
                        (temp / "host-reconnect.log").read_text(),
                        "replacement host did not stop cleanly")
                require((temp / "host-reconnect.cap").stat().st_size > 100,
                        "replacement capture is unexpectedly small")
        finally:
            for process in (host, simulator):
                if process.poll() is None:
                    process.kill()
                    process.wait()
            os.close(console_master)
            os.close(console_slave)
            os.close(serial_master)
            os.close(serial_slave)
            simulator_stderr.close()
    additions = []
    if discard_ready:
        additions.append("missed-ready recovery")
    if replace_host:
        additions.append("host replacement")
    if reset_during_stream:
        additions.append("target-reset recovery")
    detail = "" if not additions else " + " + " + ".join(additions)
    print(f"JUKUHOST-C8-COSIM-TEST: PASS (C8 V16 -> N3/N4 -> DIR{detail})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
