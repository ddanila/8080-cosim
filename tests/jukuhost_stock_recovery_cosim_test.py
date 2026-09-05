#!/usr/bin/env python3
"""Prove stock 9600/JF17 NetDisk survives a complete target restart."""

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
CPM = Path(os.environ.get("CPM_PLUS_JUKU_ROOT", ROOT.parent / "cpm-plus-juku"))
HOST = ROOT / "build/jukuhost"
ROM = ROOT / "spinoffs/jukuravi/remix/ekta4401.bin"
SYSTEM = CPM / "out/cpm-plus-juku-stock-recovery-system.bin"
FASTBOOT = CPM / "out/cpm-plus-juku-stock-recovery-fastboot-v17.bin"
VOLUME = CPM / "out/cpm-plus-juku.img"


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


def drain(fd: int) -> None:
    while select.select([fd], [], [], 0.0)[0]:
        os.read(fd, 4096)


def main() -> int:
    required = (HOST, ROM, SYSTEM, FASTBOOT, VOLUME)
    require(all(path.is_file() for path in required),
            "missing host, stock ROM, JF17 system, fastboot, or volume")
    with tempfile.TemporaryDirectory(prefix="jukuhost-stock-recovery.") as name:
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
        )
        simulator_stderr = (temp / "simulator.stderr").open("wb")

        def start_simulator(number: int) -> subprocess.Popen[bytes]:
            run_environment = environment.copy()
            run_environment["JUKU_CHECKPOINT_PREFIX"] = str(
                temp / f"final-{number}"
            )
            return subprocess.Popen(
                [str(trace), str(ROM), "1000000000000", "0", "100000"],
                cwd=temp, env=run_environment, stdout=subprocess.DEVNULL,
                stderr=simulator_stderr,
            )

        simulator = start_simulator(1)
        host = subprocess.Popen([
            str(HOST), "--serial-fd", str(serial_master),
            "--system", str(SYSTEM), "--fast-stage", str(FASTBOOT),
            "--volume", str(VOLUME), "--disk-protocol", "3",
            "--disk-baud", "9600", "--recover-session",
            "--console-pty", os.ttyname(console_slave), "--timeout", "30",
            "--disk-timeout", "90", "--log", str(temp / "host.log"),
            "--capture", str(temp / "host.cap"), "--verbose",
        ], cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
           text=True, pass_fds=(serial_master,))
        try:
            # Include Janet polling, the 9600-baud stream, and CCP disk reads
            # on native macOS, where the complete boot can exceed 40 seconds.
            first = read_until(console_master, b"A>", 90.0)
            require(b"9600" in first and b"CP/M Plus" in first,
                    f"first boot banner differs: {first!r}")
            simulator.terminate()
            simulator.wait(timeout=5.0)
            drain(console_master)
            simulator = start_simulator(2)
            second = read_until(console_master, b"A>", 90.0)
            require(b"9600" in second and b"CP/M Plus" in second,
                    f"recovered boot banner differs: {second!r}")

            host.send_signal(signal.SIGINT)
            host.wait(timeout=5.0)
            require(host.returncode == 0,
                    f"host exit={host.returncode}: "
                    f"{host.stdout.read() if host.stdout else ''}")
            log = (temp / "host.log").read_text(errors="replace")
            require(log.count("checked stock Janet") >= 1,
                    f"initial stock discovery missing: {log}")
            require(log.count("stock bootstrap complete") >= 2 and
                    log.count("Fastboot V17 complete") >= 2,
                    f"two JF17 boots were not completed: {log}")
            require("received during NetDisk; target reset detected" in log and
                    "stock-ROM reset during NetDisk; restarting JF17" in log,
                    f"NetDisk reset was not recognized: {log}")
            require("target-resets=1" in log and "boot-restarts=1" in log,
                    f"recovery counters differ: {log}")
            converted = subprocess.run([
                sys.executable, str(ROOT / "tools/jukuhost_evidence.py"),
                str(temp / "host.cap"), "--requests-jsonl",
                str(temp / "requests.jsonl"), "--boot-result",
                str(temp / "boot.json"), "--system", str(SYSTEM),
                "--fast-stage", str(FASTBOOT), "--disk-baud", "9600",
                "--serial", "inherited-fd",
            ], cwd=ROOT, text=True, stdout=subprocess.PIPE,
               stderr=subprocess.STDOUT, check=False)
            require(converted.returncode == 0,
                    f"evidence conversion failed: {converted.stdout}")
            boot = json.loads((temp / "boot.json").read_text())
            require(boot["network_rom"] is False and
                    boot["fastboot_version"] == 17 and
                    boot["boot_baud"] == 9600 and
                    boot["effective_boot_baud"] == 9600 and
                    boot["disk_baud"] == 9600,
                    f"JF17 evidence differs: {boot}")
        except BaseException as error:
            if host.poll() is None:
                host.send_signal(signal.SIGINT)
                try:
                    host.wait(timeout=3.0)
                except subprocess.TimeoutExpired:
                    host.kill()
                    host.wait()
            simulator_stderr.flush()
            output = host.stdout.read() if host.stdout else ""
            log = (temp / "host.log").read_text(errors="replace") \
                if (temp / "host.log").exists() else "<missing>"
            sim = (temp / "simulator.stderr").read_text(errors="replace")
            raise AssertionError(
                f"{error}\nHOST:\n{output}\nLOG:\n{log}\nSIM:\n{sim[-3000:]}"
            ) from error
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
    print("JUKUHOST-STOCK-RECOVERY-COSIM-TEST: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
