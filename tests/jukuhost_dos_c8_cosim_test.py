#!/usr/bin/env python3
"""Run the real 16-bit DOS host against the C8 Juku simulator."""

from __future__ import annotations

import os
from pathlib import Path
import re
import select
import shutil
import socket
import struct
import subprocess
import tempfile
import threading
import time

ROOT = Path(__file__).resolve().parents[1]
ROM = ROOT / "spinoffs/jukuravi/network-rom/juku-network-rom-abi1.3-c8.bin"
PACKAGE = ROOT / "build/dos-package"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(f"JUKUHOST-DOS-C8-COSIM-TEST: {message}")


def capture_events(path: Path) -> str:
    if not path.exists():
        return "<missing>"
    data = path.read_bytes()
    position = 16
    events: list[str] = []
    while position + 16 <= len(data):
        kind, _, length = struct.unpack_from("<BBH", data, position)
        end = position + 16 + length
        if end > len(data):
            break
        if kind == 3:
            events.append(data[position + 12:position + 12 + length].decode(
                "ascii", errors="replace"
            ))
        position = end
    return "\n".join(events)


class SerialBridge:
    def __init__(self, serial_fd: int, baud: int = 19200):
        self.serial_fd = serial_fd
        self.byte_delay = 11.0 / baud
        self.listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.listener.bind(("127.0.0.1", 0))
        self.listener.listen(1)
        self.port = self.listener.getsockname()[1]
        self.stop = threading.Event()
        self.error: BaseException | None = None
        self.thread = threading.Thread(target=self._run, daemon=True)

    def start(self) -> None:
        self.thread.start()

    def close(self) -> None:
        self.stop.set()
        self.listener.close()
        self.thread.join(timeout=2.0)

    def _run(self) -> None:
        connection: socket.socket | None = None
        try:
            self.listener.settimeout(15.0)
            connection, _ = self.listener.accept()
            connection.setblocking(False)
            os.set_blocking(self.serial_fd, False)
            while not self.stop.is_set():
                readable, _, _ = select.select(
                    [connection, self.serial_fd], [], [], 0.05
                )
                if connection in readable:
                    data = connection.recv(4096)
                    if not data:
                        break
                    # Match the host->Juku wire rate too. DOSBox can advance
                    # emulated UART time much faster than wall time and hand
                    # the TCP bridge a large burst.
                    for value in data:
                        while True:
                            try:
                                os.write(self.serial_fd, bytes((value,)))
                                break
                            except BlockingIOError:
                                select.select([], [self.serial_fd], [], 0.05)
                        time.sleep(self.byte_delay)
                if self.serial_fd in readable:
                    try:
                        data = os.read(self.serial_fd, 4096)
                    except BlockingIOError:
                        continue
                    if data:
                        # DOSBox-X otherwise injects a whole TCP chunk into
                        # its emulated 16550 at once. Pace Juku->DOS as an
                        # actual 19,200-baud 8O1 wire (11 bits/byte), so its
                        # UART FIFO and polling code see physical timing.
                        for value in data:
                            connection.sendall(bytes((value,)))
                            time.sleep(self.byte_delay)
        except (OSError, TimeoutError) as error:
            if not self.stop.is_set() and not (
                isinstance(error, BrokenPipeError) or
                getattr(error, "errno", None) in (32, 104)
            ):
                self.error = error
        finally:
            if connection is not None:
                connection.close()


def compile_simulator(destination: Path) -> Path:
    trace = destination / "trace"
    subprocess.run(
        [
            os.environ.get("CC", "cc"), "-O2", "-I", str(ROOT / "cosim"),
            "-o", str(trace), str(ROOT / "cosim/trace.c"),
            str(ROOT / "cosim/i8080.c"), str(ROOT / "cosim/juk_disk.c"),
            str(ROOT / "cosim/juku_fdc.c"),
        ],
        check=True,
    )
    return trace


def main() -> int:
    require(shutil.which("dosbox-x") is not None, "dosbox-x is not installed")
    required = [
        ROM,
        PACKAGE / "JUKUHOST.EXE",
        PACKAGE / "JUKUHOST.INI",
        PACKAGE / "SYSTEM.BIN",
        PACKAGE / "FAST16.BIN",
        PACKAGE / "BASE.IMG",
        PACKAGE / "APPS.JUK",
    ]
    require(all(path.is_file() for path in required), "DOS package is incomplete")

    with tempfile.TemporaryDirectory(prefix="jukuhost-dos-c8-cosim.") as name:
        temp = Path(name)
        drive = temp / "drive"
        shutil.copytree(PACKAGE, drive)
        config = (drive / "JUKUHOST.INI").read_text()
        (drive / "JUKUHOST.INI").write_text(
            config.replace("disk_timeout=0", "disk_timeout=35").replace(
                "console=CON", "console=@12000:INPUT.TXT"
            ),
            newline="",
        )
        (drive / "INPUT.TXT").write_bytes(b"DIR\r")
        trace = compile_simulator(temp)
        serial_master, serial_slave = os.openpty()
        bridge = SerialBridge(serial_master)
        bridge.start()
        simulator_environment = os.environ.copy()
        simulator_environment.update(
            JUKU_USART_PTY=os.ttyname(serial_slave),
            JUKU_USART_TRANSFER_CYCLES="64",
            JUKU_USART_BYTE_CYCLES="2300",
            JUKU_USART_PIT_CLOCK="1",
            JUKU_USART_PIT_CPU_HZ="1700000",
            JUKU_REALTIME_HZ="20000000",
            JUKU_TRACE_BANK="1",
            JUKU_DISABLE_SETTLE="1",
            JUKU_S21_CONFIG="0x07",
        )
        simulator_log = (temp / "simulator.log").open("wb")
        simulator = subprocess.Popen(
            [str(trace), str(ROM), "1000000000000", "0", "100000"],
            cwd=temp,
            env=simulator_environment,
            stdout=subprocess.DEVNULL,
            stderr=simulator_log,
        )
        dos_environment = os.environ.copy()
        dos_environment.update(
            SDL_VIDEODRIVER="dummy",
            SDL_AUDIODRIVER="dummy",
        )
        command = [
            "dosbox-x", "-silent", "-fastlaunch", "-nogui", "-nomenu",
            "-noautoexec", "-exit", "-time-limit", "75",
            "-set", "cpu cputype=8086",
            "-set", "cpu core=normal",
            "-set", "cpu cycles=fixed 50000",
            "-set", (
                "serial serial1=nullmodem server:127.0.0.1 "
                f"port:{bridge.port} transparent:1 rxdelay:0 txdelay:0"
            ),
            "-c", f'mount c "{drive}"',
            "-c", "c:",
            "-c", "JUKUHOST > HOST.OUT",
            "-c", "exit",
        ]
        started = time.monotonic()
        dos = subprocess.run(
            command,
            cwd=temp,
            env=dos_environment,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=85.0,
            check=False,
        )
        elapsed = time.monotonic() - started
        bridge.close()
        if simulator.poll() is None:
            simulator.terminate()
            try:
                simulator.wait(timeout=2.0)
            except subprocess.TimeoutExpired:
                simulator.kill()
                simulator.wait()
        simulator_log.close()
        os.close(serial_master)
        os.close(serial_slave)

        output = (drive / "HOST.OUT").read_bytes() if (drive / "HOST.OUT").exists() else b""
        log = (drive / "JUKUHOST.LOG").read_text(errors="replace") \
            if (drive / "JUKUHOST.LOG").exists() else ""
        events = capture_events(drive / "JUKUHOST.CAP")
        diagnostic_events = "\n".join(events.splitlines()[-160:])
        diagnostic = (
            f"\nDOSBOX:\n{dos.stdout.decode(errors='replace')[-3000:]}"
            f"\nHOST.OUT:\n{output[-5000:]!r}\nHOST LOG:\n{log[-5000:]}"
            f"\nWORK.IMG: "
            f"{(drive / 'WORK.IMG').stat().st_size if (drive / 'WORK.IMG').exists() else 'missing'}"
            f"\nCAPTURE EVENTS:\n{diagnostic_events}"
            f"\nSIMULATOR:\n{(temp / 'simulator.log').read_text(errors='replace')[-3000:]}"
        )
        require(dos.returncode == 0, f"DOSBox-X exit={dos.returncode}{diagnostic}")
        require(bridge.error is None, f"serial bridge failed: {bridge.error}{diagnostic}")
        require(b"CP/M" in output,
                f"CP/M remote-console banner missing{diagnostic}")
        require(("Fastboot V16 complete" in log or
                 "V16 final reply not seen" in log) and
                "phase=netdisk" in log,
                f"host did not complete C8 boot{diagnostic}")
        counts = re.search(
            r"requests=(\d+) reads=(\d+) records=(\d+)", log
        )
        require("serial applied=19200 8N1" in log and
                "serving A:" in log and "N3," in log and
                counts is not None and int(counts.group(2)) >= 20 and
                int(counts.group(3)) >= 60 and
                "request op=21" in events and
                "request op=20" in events and "status=2" in events,
                f"serial/disk contract differs{diagnostic}")
        require("stop exit=0" in log and "uart-errors=0" in log,
                f"DOS host did not stop cleanly{diagnostic}")
        require((drive / "JUKUHOST.CAP").stat().st_size > 100,
                f"capture is unexpectedly small{diagnostic}")
        require((drive / "WORK.IMG").stat().st_size == 409600,
                f"snapshot image is missing or wrong{diagnostic}")

    print(
        "JUKUHOST-DOS-C8-COSIM-TEST: PASS "
        f"(16-bit EXE -> COM1 -> C8 V16 -> N3/N4 console, {elapsed:.1f}s)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
