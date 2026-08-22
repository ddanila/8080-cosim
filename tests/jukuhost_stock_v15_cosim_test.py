#!/usr/bin/env python3
"""Boot CP/M Plus through stock Janet and V15 using only the C host."""

from __future__ import annotations

import json
import os
from pathlib import Path
import pty
import select
import signal
import subprocess
import sys
import tempfile
import time
import tty


ROOT = Path(__file__).resolve().parents[1]
CPM_ROOT = os.environ.get("CPM_PLUS_JUKU_ROOT")
CPM = Path(CPM_ROOT) / "out" if CPM_ROOT else ROOT / "tests/fixtures/jukuhost-v15"
HOST = ROOT / "build/jukuhost"
ROM = ROOT / "spinoffs/jukuravi/remix/ekta4401.bin"
SYSTEM = CPM / "cpm-plus-juku-system.bin"
FASTBOOT = CPM / "cpm-plus-juku-fastboot-v15.bin"
VOLUME = CPM / "cpm-plus-juku.img"
EVIDENCE = ROOT / "tools/jukuhost_evidence.py"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


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


def main() -> int:
    required = (HOST, ROM, SYSTEM, FASTBOOT, VOLUME)
    require(all(path.is_file() for path in required),
            "missing host, ROM, CP/M, V15, or volume artifact")
    with tempfile.TemporaryDirectory(prefix="jukuhost-stock-v15.") as name:
        temp = Path(name)
        trace = temp / "trace"
        subprocess.run([
            os.environ.get("CC", "cc"), "-O2", "-I", str(ROOT / "cosim"),
            "-o", str(trace), str(ROOT / "cosim/trace.c"),
            str(ROOT / "cosim/i8080.c"), str(ROOT / "cosim/juk_disk.c"),
            str(ROOT / "cosim/juku_fdc.c"),
        ], check=True)
        serial_master, serial_slave = pty.openpty()
        console_master, console_slave = pty.openpty()
        tty.setraw(serial_slave)
        tty.setraw(console_slave)
        environment = os.environ.copy()
        environment.update(
            JUKU_USART_PTY=os.ttyname(serial_slave),
            JUKU_CONSOLE_PTY=os.ttyname(console_slave),
            JUKU_USART_TRANSFER_CYCLES="64",
            JUKU_USART_BYTE_CYCLES="2300",
            JUKU_USART_PIT_CLOCK="1",
            JUKU_USART_PIT_CPU_HZ="1700000",
            JUKU_REALTIME_HZ="1700000",
            JUKU_TRACE_BANK="1",
            JUKU_DISABLE_SETTLE="1",
            JUKU_KEY_HOLD_FRAMES="6",
            JUKU_KEY_GAP_FRAMES="8",
            JUKU_S21_CONFIG="0x06",
            JUKU_KEYS="TN",
            JUKU_CHECKPOINT_PREFIX=str(temp / "final"),
        )
        simulator_stderr = (temp / "simulator.stderr").open("wb")
        simulator = subprocess.Popen(
            [str(trace), str(ROM), "1000000000000", "0", "100000"],
            cwd=temp, env=environment, stdout=subprocess.DEVNULL,
            stderr=simulator_stderr,
        )
        host = subprocess.Popen([
            str(HOST), "--serial-fd", str(serial_master),
            "--system", str(SYSTEM), "--fast-stage", str(FASTBOOT),
            "--volume", str(VOLUME), "--disk-protocol", "3",
            "--disk-baud", "19200", "--console-pty",
            os.ttyname(console_slave), "--timeout", "30",
            "--disk-timeout", "60", "--log", str(temp / "host.log"),
            "--capture", str(temp / "host.cap"), "--verbose",
        ], cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
           text=True, pass_fds=(serial_master,))
        try:
            try:
                transcript = read_until(console_master, b"A>", 35.0)
            except AssertionError as error:
                host.send_signal(signal.SIGINT)
                host.wait(timeout=3.0)
                simulator.terminate()
                simulator.wait(timeout=3.0)
                output = host.stdout.read() if host.stdout else ""
                log = (temp / "host.log").read_text(errors="replace") \
                    if (temp / "host.log").exists() else "<missing>"
                sim = (temp / "simulator.stderr").read_text(errors="replace")
                raise AssertionError(
                    f"{error}\nHOST:\n{output}\nLOG:\n{log}\nSIM:\n{sim[-3000:]}"
                ) from error
            require(b"CP/M" in transcript,
                    f"prompt lacked CP/M banner: {transcript!r}")
            host.send_signal(signal.SIGINT)
            host.wait(timeout=5.0)
            require(host.returncode == 0,
                    f"host exit={host.returncode}: "
                    f"{host.stdout.read() if host.stdout else ''}")
            log = (temp / "host.log").read_text()
            require("stock-assisted V15 core" in log and
                    "stock bootstrap complete" in log and
                    ("Fastboot V15 complete" in log or
                     "V15 final reply not seen" in log) and
                    "phase=netdisk" in log and "requests=" in log,
                    f"host evidence incomplete: {log}")
            require((temp / "host.cap").stat().st_size > 1000,
                    "capture is unexpectedly small")
            converted = subprocess.run([
                sys.executable, str(EVIDENCE), str(temp / "host.cap"),
                "--requests-jsonl", str(temp / "requests.jsonl"),
                "--boot-result", str(temp / "boot.json"),
                "--system", str(SYSTEM), "--fast-stage", str(FASTBOOT),
                "--serial", "inherited-fd",
            ], cwd=ROOT, text=True, stdout=subprocess.PIPE,
               stderr=subprocess.STDOUT, check=False)
            require(converted.returncode == 0,
                    f"evidence conversion failed: {converted.stdout}")
            boot = json.loads((temp / "boot.json").read_text())
            require(boot["network_rom"] is False and
                    boot["fastboot_version"] == 15 and
                    boot["boot_baud"] == 9600 and
                    boot["effective_boot_baud"] == 19200 and
                    boot["disk_baud"] == 19200,
                    f"stock-assisted evidence differs: {boot}")
        finally:
            if host.poll() is None:
                host.kill()
                host.wait()
            if simulator.poll() is None:
                simulator.terminate()
                try:
                    simulator.wait(timeout=3.0)
                except subprocess.TimeoutExpired:
                    simulator.kill()
                    simulator.wait()
            simulator_stderr.close()
            os.close(serial_master)
            os.close(serial_slave)
            os.close(console_master)
            os.close(console_slave)
    print("JUKUHOST-STOCK-V15-COSIM-TEST: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
