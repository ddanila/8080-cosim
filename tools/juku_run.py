#!/usr/bin/env python3
"""Run a Juku in the emulator with an attachable terminal, in one command.

Starts cosim paced at the real 2 MHz clock with an interactive console PTY,
and optionally brings up the native C Juku host as well:

    tools/juku_run.py                                   # ROM monitor only
    tools/juku_run.py --netboot media/system/EKDOS230.BIN
    tools/juku_run.py --disk ../cpmish/juku-net-system.bin \\
                      ../cpmish/juku-flat.img --writable
    tools/juku_run.py --disk ../cpmish/juku-net-mode2-system.bin \\
                      ../cpmish/juku-net-mode2.img \\
                      --drive-b J3KGAME2.JUK --writable

It prints the console device to attach to, for example:

    screen /dev/ttys014         (leave with ctrl-a k)
    cu -l /dev/ttys014          (leave with ~.)

Pass --attach to bridge this terminal instead of printing a device path.
Everything stops on ctrl-c.
"""

from __future__ import annotations

import argparse
import os
import re
import select
import shutil
import signal
import subprocess
import sys
import termios
import time
import tty
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NOMINAL_HZ = 2_000_000
FRAME_IRQ_CYCLES = "200000"
DEFAULT_HOST = ROOT / "build" / "jukuhost"


def build_trace(destination: Path) -> Path:
    compiler = os.environ.get("CC", "cc")
    subprocess.run(
        [compiler, "-O2", "-I", str(ROOT / "cosim"), "-o", str(destination),
         *(str(ROOT / "cosim" / name) for name in
           ("trace.c", "i8080.c", "juk_disk.c", "juku_fdc.c"))],
        check=True, cwd=ROOT,
    )
    return destination


def build_host() -> Path:
    subprocess.run(
        [str(ROOT / "sync" / "jukuhost_linux_build.sh")],
        check=True, cwd=ROOT,
    )
    return DEFAULT_HOST


def host_command(arguments: argparse.Namespace, serial: str,
                 work: Path, host: Path) -> list[str]:
    command = [
        str(host), "--serial", serial,
        "--log", str(work / "jukuhost.log"),
        "--capture", str(work / "jukuhost.cap"),
    ]
    if arguments.netboot:
        command.extend((
            "--system", str(arguments.netboot), "--boot-only",
        ))
        return command
    system, volume = arguments.disk
    command.extend((
        "--system", system, "--volume", volume,
        "--disk-baud", str(arguments.disk_baud),
        "--disk-protocol", str(arguments.disk_protocol),
        "--read-ahead", str(arguments.read_ahead),
        "--verbose",
    ))
    if arguments.drive_b:
        command.extend(("--drive-b", str(arguments.drive_b)))
    if arguments.writable:
        command.append("--writable")
    return command


def wait_for(pattern: str, log: Path, timeout: float) -> str | None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if log.exists():
            found = re.search(pattern, log.read_text(errors="replace"))
            if found:
                return found.group(1)
        time.sleep(0.05)
    return None


def bridge(console: str) -> None:
    """Put this terminal on the console PTY until ctrl-] is pressed."""
    fd = os.open(console, os.O_RDWR | os.O_NOCTTY)
    tty.setraw(fd)
    stdin = sys.stdin.fileno()
    saved = termios.tcgetattr(stdin)
    tty.setraw(stdin)
    print("\r\n[attached — ctrl-] to detach]\r\n", end="", flush=True)
    try:
        while True:
            ready, _, _ = select.select([fd, stdin], [], [], 0.2)
            if fd in ready:
                data = os.read(fd, 4096)
                if data:
                    os.write(sys.stdout.fileno(), data)
            if stdin in ready:
                typed = os.read(stdin, 1024)
                if b"\x1d" in typed:            # ctrl-]
                    break
                os.write(fd, typed)
    finally:
        termios.tcsetattr(stdin, termios.TCSADRAIN, saved)
        os.close(fd)
        print("\r\n[detached]")


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--rom", type=Path,
                        default=ROOT / "roms" / "ekta37.bin")
    parser.add_argument("--netboot", type=Path, metavar="SYSTEM",
                        help="serve one Janet network boot of SYSTEM")
    parser.add_argument("--disk", nargs=2, metavar=("SYSTEM", "VOLUME"),
                        help="netboot SYSTEM then serve VOLUME as drive A:")
    parser.add_argument("--drive-b", type=Path, metavar="GAME.JUK",
                        help="serve a native 800 KiB Juku image as B:")
    parser.add_argument("--disk-image", type=Path, metavar="IMG",
                        help="attach a raw floppy image as the local drive")
    parser.add_argument("--writable", action="store_true",
                        help="allow the served A: volume to be written")
    parser.add_argument("--disk-baud", type=int, default=9600,
                        help="served-disk baud rate (default: 9600)")
    parser.add_argument("--disk-protocol", type=int, choices=(1, 2, 3),
                        default=2,
                        help="served-disk protocol (default: 2)")
    parser.add_argument("--read-ahead", type=int, choices=range(1, 9),
                        default=3,
                        help="NetDisk-v3 records per read (default: 3)")
    parser.add_argument("--attach", action="store_true",
                        help="bridge this terminal instead of printing a device")
    parser.add_argument("--max-speed", action="store_true",
                        help="run flat out instead of at the 2 MHz machine clock")
    parser.add_argument("--keys", help="type this string automatically")
    parser.add_argument("--trace", type=Path, help="prebuilt cosim binary")
    parser.add_argument("--host", type=Path,
                        help="prebuilt native jukuhost executable")
    parser.add_argument("--keep-logs", action="store_true",
                        help="keep the run directory and cosim's verbose "
                             "bank-switch logging (writes GBs on long runs)")
    arguments = parser.parse_args()

    if arguments.netboot and arguments.disk:
        parser.error("--netboot and --disk are alternatives")
    if arguments.drive_b and not arguments.disk:
        parser.error("--drive-b requires --disk")
    if arguments.disk_protocol != 3 and arguments.read_ahead != 3:
        parser.error("--read-ahead applies only to --disk-protocol 3")
    arguments.rom = arguments.rom.resolve()
    if not arguments.rom.is_file():
        parser.error(f"ROM not found: {arguments.rom}")
    if arguments.netboot:
        arguments.netboot = arguments.netboot.resolve()
        if not arguments.netboot.is_file():
            parser.error(f"system image not found: {arguments.netboot}")
    if arguments.disk:
        arguments.disk = [str(Path(item).resolve()) for item in arguments.disk]
        for item in arguments.disk:
            if not Path(item).is_file():
                parser.error(f"not found: {item}")
    if arguments.drive_b:
        arguments.drive_b = arguments.drive_b.resolve()
        if not arguments.drive_b.is_file():
            parser.error(f"game image not found: {arguments.drive_b}")

    disk = arguments.disk_image or (
        Path(os.environ["JUKU_DISK"]) if os.environ.get("JUKU_DISK") else None)
    if disk is not None:
        disk = disk.resolve()
        if not disk.is_file():
            parser.error(f"disk image not found: {disk}")

    work = Path(os.environ.get("TMPDIR", "/tmp")) / f"juku-run-{os.getpid()}"
    work.mkdir(parents=True, exist_ok=True)
    trace = arguments.trace or build_trace(work / "trace")
    host = None
    if arguments.netboot or arguments.disk:
        host = arguments.host.resolve() if arguments.host else DEFAULT_HOST
        if not host.is_file():
            if arguments.host:
                parser.error(f"host executable not found: {host}")
            host = build_host()

    environment = os.environ.copy()
    environment["JUKU_CONSOLE_PTY"] = "auto"
    # cosim logs every memory-bank switch, and the Juku switches banks
    # constantly: an interactive session left running writes gigabytes of
    # stderr (one session here reached 52 GB and filled the disk). Keep it
    # off unless the logs are explicitly wanted.
    if not arguments.keep_logs:
        environment["JUKU_TRACE_BANK"] = "0"
    # cosim runs in its own working directory, so every path it receives
    # must be absolute -- a relative JUKU_DISK would silently fail to open.
    if disk is not None:
        environment["JUKU_DISK"] = str(disk)
    else:
        environment.pop("JUKU_DISK", None)
    if not arguments.max_speed:
        environment["JUKU_REALTIME_HZ"] = str(NOMINAL_HZ)
    if arguments.netboot or arguments.disk:
        environment["JUKU_USART_PTY"] = "auto"
        environment["JUKU_USART_TRANSFER_CYCLES"] = "64"
        environment["JUKU_USART_BYTE_CYCLES"] = "2300"
        environment["JUKU_USART_PIT_CLOCK"] = "1"
    if arguments.keys:
        environment["JUKU_KEYS"] = arguments.keys
        environment["JUKU_KEY_HOLD_FRAMES"] = "6"
        environment["JUKU_KEY_GAP_FRAMES"] = "8"

    log = work / "cosim.log"
    with log.open("w") as stream:
        cosim = subprocess.Popen(
            [str(trace), str(arguments.rom), "1000000000000", "0",
             FRAME_IRQ_CYCLES],
            cwd=work, env=environment, stdout=subprocess.DEVNULL, stderr=stream)

    console = wait_for(r"\[TERM\] PTY slave=(\S+)", log, 10)
    if not console:
        cosim.kill()
        detail = log.read_text(errors="replace").strip().splitlines()
        for line in detail[-3:]:
            print(f"cosim: {line}", file=sys.stderr)
        print(f"no console PTY appeared; full log: {log}", file=sys.stderr)
        return 1

    server = None
    if arguments.netboot or arguments.disk:
        serial = wait_for(r"\[USART\] PTY slave=(\S+)", log, 10)
        if not serial:
            cosim.kill()
            print(f"cosim did not report a serial PTY; see {log}", file=sys.stderr)
            return 1
        assert host is not None
        command = host_command(arguments, serial, work, host)
        server = subprocess.Popen(command, cwd=ROOT)
        print(f"jukuhost: {host.name} on {serial}")

    if disk is not None:
        print(f"disk: {disk}  (boot it with T D D)")
    print(f"console: {console}")
    if not arguments.attach:
        viewer = "screen" if shutil.which("screen") else "cu -l"
        print(f"attach with:  {viewer} {console}")
        print("type T then N to boot from the network; ctrl-c here stops everything")
    print(f"logs: {log}")

    def stop(signum, frame):                      # noqa: ARG001
        raise KeyboardInterrupt
    signal.signal(signal.SIGTERM, stop)

    try:
        if arguments.attach:
            bridge(console)
        else:
            while cosim.poll() is None:
                time.sleep(0.5)
    except KeyboardInterrupt:
        pass
    finally:
        for process in (server, cosim):
            if process and process.poll() is None:
                process.send_signal(
                    signal.SIGINT if process is server else signal.SIGTERM,
                )
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
        # cosim logs every bank switch, so a long session leaves hundreds of
        # megabytes behind; a run directory per invocation adds up fast.
        if arguments.keep_logs:
            print(f"logs kept: {work}")
        else:
            shutil.rmtree(work, ignore_errors=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
