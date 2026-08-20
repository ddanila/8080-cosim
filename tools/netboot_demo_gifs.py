#!/usr/bin/env python3
"""Capture synchronized, real-time Juku network-boot demonstrations."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import pty
import re
import select
import signal
import struct
import subprocess
import threading
import time
import tty


ROOT = Path(__file__).resolve().parents[1]
FUN = ROOT.parent
CPMISH = FUN / "cpmish"
CPM3 = FUN / "cpm-plus-juku"
CPU_HZ = 1_700_000
FRAME_CYCLES = 100_000
CAPTURE_HEADER = struct.Struct("=QHH")


def build_trace(output: Path) -> None:
    compiler = os.environ.get("CC", "cc")
    subprocess.run([
        compiler, "-O2", "-I", str(ROOT / "cosim"), "-o", str(output),
        *(str(ROOT / "cosim" / name) for name in
          ("trace.c", "i8080.c", "juk_disk.c", "juku_fdc.c")),
    ], check=True, cwd=ROOT)


def require_files(paths: list[Path]) -> None:
    missing = [str(path) for path in paths if not path.is_file()]
    if missing:
        raise SystemExit("missing demonstration input:\n  " + "\n  ".join(missing))


def timestamp_lines(stream, started: float, destination: list[tuple[float, str]],
                    ready: threading.Event | None = None,
                    serial: list[str] | None = None,
                    console: list[str] | None = None) -> None:
    for raw in iter(stream.readline, ""):
        elapsed = time.monotonic() - started
        line = raw.rstrip()
        if serial is not None:
            match = re.search(r"\[USART\] PTY slave=(\S+)", line)
            if match:
                serial.append(match.group(1))
                ready.set()
            terminal = re.search(r"\[TERM\] PTY slave=(\S+)", line)
            if terminal and console is not None:
                console.append(terminal.group(1))
        else:
            destination.append((elapsed, line))
            print(f"[{elapsed:7.3f}] {line}")


def scenario_command(name: str, serial: str | int, output: Path,
                     console: str | None = None) -> tuple[list[str], Path, str]:
    server = str(ROOT / "build" / "jukuhost")
    serial_option = [
        "--serial-fd", str(serial),
    ] if isinstance(serial, int) else ["--serial", serial]
    evidence = [
        "--log", str(output / f"{name}.jukuhost.log"),
        "--capture", str(output / f"{name}.jukuhost.cap"),
        "--verbose",
    ]
    if name == "cpm22":
        return ([
            server, *serial_option,
            "--system", str(CPMISH / "juku-net-v2-system.bin"),
            "--volume", str(CPMISH / "juku-net-mode2.img"),
            "--disk-baud", "9600", "--disk-protocol", "2",
            "--timeout", "300", *evidence,
        ], ROOT / "roms" / "ekta37.bin", "TN0201")
    if name != "cpm31_netrom":
        raise ValueError(f"unknown demonstration scenario: {name}")
    network_rom = True
    command = [
        server, *serial_option,
        "--system", str(CPM3 / "out/cpm-plus-juku-network-rom-c8-system.bin"),
        "--volume", str(CPM3 / "out" / "cpm-plus-juku-full.img"),
        "--disk-baud", "19200", "--disk-protocol", "3",
        "--read-ahead", "8", "--timeout", "420", *evidence,
    ]
    if network_rom:
        command.extend((
            "--fast-stage",
            str(CPM3 / "out" /
                "cpm-plus-juku-network-rom-c8-fastboot-v16.bin"),
            "--network-rom",
        ))
    if console:
        command.extend(("--console-pty", console))
    rom = ROOT / "spinoffs" / "jukuravi" / "network-rom" / \
        "juku-network-rom-abi1.3-c8.bin" if network_rom else \
        ROOT / "roms" / "ekta37.bin"
    return command, rom, "" if network_rom else "TN0201"


def drive_remote_console(fd: int, name: str, started: float,
                         logs: list[tuple[float, str]], done: threading.Event) -> None:
    pending = bytearray()
    commands = (
        (b"VER\r", None),
        (b"WC TOOLS.TXT\r", None),
        (b"FIND TOOLS.TXT PANEL\r", None),
        (b"CRC TOOLS.TXT\r", None),
        (b"HIST\r", None),
        (b"!!\r", None),
        (b"PANEL\r", b"PANEL READY"),
    )
    command_index = 0
    # At the authentic 1.7 MHz pacing used for the visual timeline, the C8
    # decompressor and CP/M cold start take several minutes of wall time.
    deadline = time.monotonic() + 450
    while time.monotonic() < deadline and command_index <= len(commands):
        readable, _, _ = select.select([fd], [], [], 0.2)
        if not readable:
            continue
        data = os.read(fd, 4096)
        if not data:
            continue
        pending.extend(data)
        if b"A>" not in pending:
            continue
        pending.clear()
        if command_index == len(commands):
            logs.append((time.monotonic() - started, "CP/M prompt returned"))
            done.set()
            return
        command, interactive_hold = commands[command_index]
        logs.append((time.monotonic() - started,
                     f"N4 console input: {command[:-1].decode()}"))
        os.write(fd, command)
        command_index += 1
        if interactive_hold is not None:
            if isinstance(interactive_hold, bytes):
                screen_output = bytearray()
                screen_deadline = time.monotonic() + 90
                logs.append((time.monotonic() - started,
                             "Rendering final interactive screen"))
                while time.monotonic() < screen_deadline and \
                        interactive_hold not in screen_output:
                    readable, _, _ = select.select([fd], [], [], 0.2)
                    if readable:
                        screen_output.extend(os.read(fd, 4096))
                if interactive_hold not in screen_output:
                    logs.append((time.monotonic() - started,
                                 "Final control panel timeout"))
                    done.set()
                    return
                logs.append((time.monotonic() - started,
                             "Final control panel displayed"))
                time.sleep(3)
                done.set()
                return
            logs.append((time.monotonic() - started,
                         f"Holding interactive screen for "
                         f"{interactive_hold}s"))
            hold_deadline = time.monotonic() + interactive_hold
            while time.monotonic() < hold_deadline:
                readable, _, _ = select.select(
                    [fd], [], [], min(0.2, hold_deadline - time.monotonic()),
                )
                if readable:
                    os.read(fd, 4096)
            os.write(fd, b"\r")
            logs.append((time.monotonic() - started,
                         "N4 console input: RETURN"))
            pending.clear()
    logs.append((time.monotonic() - started, "N4 console command timeout"))
    done.set()


def drive_stock_keyboard(fd: int, started: float,
                         logs: list[tuple[float, str]], done: threading.Event) -> None:
    deadline = time.monotonic() + 330
    while time.monotonic() < deadline:
        if any(
            "Janet boot complete" in line
            or "stock bootstrap complete" in line
            for _, line in logs
        ):
            time.sleep(2)
            for command in (b"DIR\r", b"VER\r"):
                logs.append((time.monotonic() - started,
                             f"Juku keyboard input: {command[:-1].decode()}"))
                os.write(fd, command)
                time.sleep(4)
            time.sleep(4)
            done.set()
            return
        time.sleep(0.1)
    logs.append((time.monotonic() - started, "Stock keyboard command timeout"))
    done.set()


def run_scenario(name: str, output: Path, trace: Path) -> \
        tuple[Path, list[tuple[float, str]], float]:
    capture = output / f"{name}.frames"
    command_stub, rom, keys = scenario_command(name, "SERIAL", output)
    required = [rom, Path(command_stub[0])]
    for option in ("--system", "--volume", "--fast-stage"):
        if option in command_stub:
            required.append(Path(command_stub[command_stub.index(option) + 1]))
    require_files(required)
    environment = os.environ.copy()
    environment.update(
        JUKU_USART_TRANSFER_CYCLES="64",
        JUKU_USART_BYTE_CYCLES="2300",
        JUKU_USART_PIT_CLOCK="1",
        JUKU_USART_PIT_CPU_HZ=str(CPU_HZ),
        JUKU_REALTIME_HZ=os.environ.get("JUKU_DEMO_REALTIME_HZ", str(CPU_HZ)),
        JUKU_TRACE_BANK="0",
        JUKU_DISABLE_SETTLE="1",
        JUKU_KEYS=keys,
        JUKU_KEY_HOLD_FRAMES="6",
        JUKU_KEY_GAP_FRAMES="8",
        JUKU_VIDEO_CAPTURE=str(capture),
    )
    if name == "cpm31_netrom":
        environment.pop("JUKU_KEYS", None)
        environment["JUKU_TRACE_BANK"] = "1"
        environment["JUKU_S21_CONFIG"] = "0x07"
    serial_master, serial_slave = pty.openpty()
    tty.setraw(serial_slave)
    environment["JUKU_USART_PTY"] = os.ttyname(serial_slave)
    console_master, console_slave = pty.openpty()
    tty.setraw(console_slave)
    if name == "cpm22":
        environment["JUKU_CONSOLE_PTY"] = os.ttyname(console_slave)
        environment["JUKU_CONSOLE_OUT_PC"] = "0xffff"
        environment["JUKU_CONSOLE_IN_PC"] = "0xffff"
        environment["JUKU_KEY_HOLD_FRAMES"] = "3"
        environment["JUKU_KEY_GAP_FRAMES"] = "3"
    started = time.monotonic()
    simulator_log = (output / f"{name}.simulator.log").open("w")
    cosim = subprocess.Popen(
        [str(trace), str(rom),
         "1000000000000",
         "0", str(FRAME_CYCLES)],
        cwd=output, env=environment, stdout=subprocess.DEVNULL,
        stderr=simulator_log,
    )
    command, _, _ = scenario_command(
        name, serial_master, output,
        os.ttyname(console_slave) if name == "cpm31_netrom" else None,
    )
    logs: list[tuple[float, str]] = [(time.monotonic() - started,
                                     f"Starting {name} network boot")]
    server = subprocess.Popen(
        command, cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        text=True, bufsize=1, pass_fds=(serial_master,),
    )
    server_thread = threading.Thread(
        target=timestamp_lines,
        args=(server.stdout, started, logs), daemon=True,
    )
    server_thread.start()
    console_done = threading.Event()
    console_thread = None
    if name == "cpm22":
        console_thread = threading.Thread(
            target=drive_stock_keyboard,
            args=(console_master, started, logs, console_done), daemon=True,
        )
        console_thread.start()
    elif console_master is not None:
        console_thread = threading.Thread(
            target=drive_remote_console,
            args=(console_master, name, started, logs, console_done), daemon=True,
        )
        console_thread.start()
    try:
        if name == "cpm22":
            if not console_done.wait(360):
                raise RuntimeError("cpm22: keyboard commands did not complete")
            if any("timeout" in line.lower() for _, line in logs):
                raise RuntimeError("cpm22: keyboard command timeout")
            time.sleep(2)
            server.send_signal(signal.SIGINT)
            server.wait(timeout=10)
            if server.returncode != 0:
                raise RuntimeError(f"jukuhost exited {server.returncode}")
            cosim.terminate()
        else:
            if not console_done.wait(480):
                raise RuntimeError("cpm31: N4 console did not complete")
            if any("timeout" in line.lower() for _, line in logs):
                raise RuntimeError("cpm31: N4 console command timeout")
            time.sleep(2)
            logs.append((time.monotonic() - started,
                         "Stopping jukuhost after completed capture"))
            server.send_signal(signal.SIGINT)
            server.wait(timeout=10)
            if server.returncode != 0:
                raise RuntimeError(f"jukuhost exited {server.returncode}")
            cosim.terminate()
        cosim.wait(timeout=300)
        if cosim.returncode:
            raise RuntimeError(f"{name}: simulator exited {cosim.returncode}")
    finally:
        if cosim.poll() is None:
            cosim.terminate()
        if server.poll() is None:
            server.send_signal(signal.SIGINT)
        server.wait(timeout=10)
        server_thread.join(timeout=2)
        if console_thread:
            console_thread.join(timeout=2)
        simulator_log.close()
        for fd in (serial_master, serial_slave, console_master, console_slave):
            os.close(fd)
    logs.append((time.monotonic() - started, "Demonstration complete"))
    return capture, logs, started


def read_frames(path: Path, started: float) -> list[tuple[float, int, int, bytes]]:
    frames = []
    with path.open("rb") as stream:
        while header := stream.read(CAPTURE_HEADER.size):
            if len(header) != CAPTURE_HEADER.size:
                raise ValueError(f"truncated capture header: {path}")
            captured_ns, stride, lines = CAPTURE_HEADER.unpack(header)
            pixels = stream.read(stride * lines)
            if len(pixels) != stride * lines:
                raise ValueError(f"truncated capture frame: {path}")
            frames.append((captured_ns / 1_000_000_000,
                           stride, lines, pixels))
    if not frames:
        raise ValueError(f"empty capture: {path}")
    normalized = []
    correction = frames[0][0]
    previous = frames[0][0]
    for timestamp, stride, lines, pixels in frames:
        gap = timestamp - previous
        if gap > 60:
            correction += gap - FRAME_CYCLES / CPU_HZ
        normalized.append((timestamp - correction, stride, lines, pixels))
        previous = timestamp
    return normalized


def render(name: str, capture: Path, logs: list[tuple[float, str]],
           started: float, gif: Path) -> None:
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError as error:
        raise SystemExit("Pillow is required; install it with: python3 -m pip install Pillow") from error

    frames = read_frames(capture, started)
    timeline = sorted({time_value for time_value, *_ in frames} |
                      {time_value for time_value, _ in logs})
    frame_index = 0
    log_index = 0
    visible_logs: list[str] = []
    images = []
    durations = []
    title = {
        "cpm22": "Stock ROM + CP/M 2.2",
        "cpm31_netrom": "Netboot ROM + CP/M Plus 3.1",
    }[name]
    font_path = Path("/System/Library/Fonts/Menlo.ttc")
    font = ImageFont.truetype(str(font_path), 16) if font_path.is_file() else \
        ImageFont.load_default()
    small = ImageFont.truetype(str(font_path), 13) if font_path.is_file() else font
    for position, current in enumerate(timeline):
        while frame_index + 1 < len(frames) and frames[frame_index + 1][0] <= current:
            frame_index += 1
        while log_index < len(logs) and logs[log_index][0] <= current:
            stamp, line = logs[log_index]
            visible_logs.append(f"{stamp:7.3f}s  {line}")
            log_index += 1
        _, stride, lines, packed = frames[frame_index]
        screen = Image.new("RGB", (stride * 8, lines), "#101410")
        screen_pixels = screen.load()
        for y in range(lines):
            for byte_x in range(stride):
                value = packed[y * stride + byte_x]
                for bit in range(8):
                    if value & (0x80 >> bit):
                        screen_pixels[byte_x * 8 + bit, y] = (185, 235, 165)
        left_width = stride * 8
        canvas_height = max(500, lines + 44)
        canvas = Image.new("RGB", (left_width + 680, canvas_height), "#111418")
        canvas.paste(screen, (0, 44))
        draw = ImageDraw.Draw(canvas)
        draw.text((16, 12), title, font=font, fill="#f2f2f2")
        draw.text((left_width + 10, 14),
                  f"Native C jukuhost   elapsed {current:6.2f}s",
                  font=small, fill="#cfd8dc")
        for row, line in enumerate(visible_logs[-28:]):
            draw.text((left_width + 10, 50 + row * 16), line[:80],
                      font=small, fill="#b8c7d1")
        images.append(canvas)
        following = timeline[position + 1] if position + 1 < len(timeline) else current + 2
        durations.append(max(10, round((following - current) * 1000)))
    images[0].save(gif, save_all=True, append_images=images[1:],
                   duration=durations, loop=0, optimize=True, disposal=1)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "media" / "demos")
    parser.add_argument("--scenario",
                        choices=("cpm22", "cpm31_netrom", "all"),
                        default="all")
    arguments = parser.parse_args()
    output = arguments.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    trace = output / "trace-netboot-demo"
    build_trace(trace)
    names = ("cpm22", "cpm31_netrom") \
        if arguments.scenario == "all" else \
        (arguments.scenario,)
    for name in names:
        capture, logs, started = run_scenario(name, output, trace)
        gif = output / {
            "cpm22": "stock-rom-cpm22.gif",
            "cpm31_netrom": "netboot-rom-cpm31.gif",
        }[name]
        render(name, capture, logs, started, gif)
        capture.unlink()
        print(f"wrote {gif}")
    trace.unlink()
    (output / "vram.bin").unlink(missing_ok=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
