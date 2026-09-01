#!/usr/bin/env python3
"""Boot the C8/C9/C10/C11 ROM and CP/M Plus using the production host."""

from __future__ import annotations

import json
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
RELEASE = os.environ.get("JUKUHOST_ROM_RELEASE", "c8").lower()
if RELEASE not in ("c8", "c9", "c10", "c11"):
    raise SystemExit(f"unsupported JUKUHOST_ROM_RELEASE={RELEASE!r}")
ROM_ABI = "1.4" if RELEASE in ("c9", "c10", "c11") else "1.3"
ROM = ROOT / f"spinoffs/jukuravi/network-rom/juku-network-rom-abi{ROM_ABI}-{RELEASE}.bin"
SYSTEM = CPM / f"out/cpm-plus-juku-network-rom-{RELEASE}-system.bin"
FASTBOOT = CPM / f"out/cpm-plus-juku-network-rom-{RELEASE}-fastboot-v16.bin"
VOLUME = CPM / (f"out/cpm-plus-juku-{RELEASE}-full.img"
                if RELEASE in ("c9", "c10", "c11") else
                "out/cpm-plus-juku-full.img")
DRIVE_B = CPM / "out/cpm-plus-juku-apps.juk"
HOST = ROOT / "build/jukuhost"
EVIDENCE = ROOT / "tools/jukuhost_evidence.py"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(f"JUKUHOST-{RELEASE.upper()}-COSIM-TEST: {message}")


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
    required = (ROM, SYSTEM, FASTBOOT, VOLUME, DRIVE_B, HOST)
    require(all(path.is_file() for path in required),
            "missing C8/CPM artifacts or build/jukuhost")
    discard_ready = os.environ.get("JUKUHOST_C8_DISCARD_READY") == "1"
    replace_host = os.environ.get("JUKUHOST_C8_REPLACE_HOST") == "1"
    reset_during_stream = os.environ.get("JUKUHOST_C8_TARGET_RESET") == "1"
    recover_session = os.environ.get("JUKUHOST_C11_RECOVER") == "1"
    netdisk_reset = os.environ.get("JUKUHOST_C11_NETDISK_RESET") == "1"
    late_host = os.environ.get("JUKUHOST_C11_LATE_HOST") == "1"
    require(not recover_session or RELEASE == "c11",
            "session recovery requires the C11 discovery beacon")
    require(not netdisk_reset or recover_session,
            "NetDisk reset fixture requires C11 session recovery")
    require(not late_host or recover_session,
            "late-host fixture requires C11 session recovery")
    disk_timeout = "240" if netdisk_reset else "120"
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
            # Keep target time and the modeled serial wire on the same clock.
            # Accelerating only the CPU makes its finite C6/capability windows
            # expire while the host is still draining bytes at 19,200 baud.
            JUKU_REALTIME_HZ="1700000",
            JUKU_TRACE_BANK="1",
            JUKU_DISABLE_SETTLE="1",
            # C8 needs bit 0 for autoboot. C9/C10/C11 reserve it and must boot
            # with the same 80x24 selection while it is clear.
            JUKU_S21_CONFIG="0x06" if RELEASE in ("c9", "c10", "c11") else "0x07",
            JUKU_CHECKPOINT_PREFIX=str(checkpoint),
        )
        if reset_during_stream:
            environment["JUKU_RESET_AFTER_USART_RX"] = "900"
        elif netdisk_reset:
            # The exact C11 V16 transfer is under 8 KiB.  This boundary fires
            # after CP/M has entered NetDisk and begun consuming disk replies,
            # but before the initial command workload is complete.
            environment["JUKU_RESET_AFTER_USART_RX"] = "7785"
        simulator_stderr = (temp / "simulator.stderr").open("wb")
        simulator = subprocess.Popen(
            [str(trace), str(ROM), "1000000000000", "0", "100000"],
            cwd=temp, env=environment, stdout=subprocess.DEVNULL,
            stderr=simulator_stderr,
        )
        if late_host:
            beacon = b"JB\x0b\x01\x02"
            time.sleep(0.8)
            first_interval = bytearray()
            while select.select([serial_master], [], [], 0.05)[0]:
                first_interval.extend(os.read(serial_master, 4096))
            time.sleep(1.8)
            second_interval = bytearray()
            while select.select([serial_master], [], [], 0.05)[0]:
                second_interval.extend(os.read(serial_master, 4096))
            require(beacon in first_interval and beacon in second_interval,
                    "C11 did not repeat its checked discovery beacon")
        elif discard_ready:
            time.sleep(0.5)
            discarded = bytearray()
            while select.select([serial_master], [], [], 0.05)[0]:
                discarded.extend(os.read(serial_master, 4096))
            require(b"JR\x10\x01" in discarded,
                    f"one-shot JR16 readiness was not captured: {discarded.hex()}")
        host_command = [
            str(HOST), "--serial-fd", str(serial_master), "--system", str(SYSTEM),
            "--fast-stage", str(FASTBOOT), "--network-rom",
            "--volume", str(volume), "--drive-b", str(DRIVE_B),
            "--writable", "--disk-protocol", "3",
            "--disk-baud", "19200", "--read-ahead", "3",
            "--console-pty", os.ttyname(console_slave), "--timeout", "30",
            "--disk-timeout", disk_timeout, "--log", str(temp / "host.log"),
            "--capture", str(temp / "host.cap"), "--verbose",
        ]
        if recover_session:
            host_command.append("--recover-session")
        host = subprocess.Popen(
            host_command, cwd=ROOT, stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT, text=True, pass_fds=(serial_master,))
        try:
            try:
                transcript = read_until(console_master, b"A>", 35.0)
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
            if RELEASE in ("c9", "c10", "c11"):
                os.write(console_master, b"STATUS\r")
                # STATUS 1.4 is deliberately verbose and C9 sends it through
                # the bounded, per-character production N4 path. Keep enough
                # margin for physical pacing and retain full evidence on a
                # genuine deadline failure.
                try:
                    status = read_until(console_master, b"A>", 90.0)
                except AssertionError as error:
                    raise AssertionError(
                        f"{error}{failure_evidence(temp, host, simulator)}"
                    ) from error
                require(b"ROM: Juku ABI 01.04" in status and
                        b"N4 state flags: 0F" in status and
                        b"N4 failure reason: none" in status,
                        f"{RELEASE.upper()} status telemetry differs: {status!r}")
                if RELEASE in ("c10", "c11"):
                    require(
                        b"PPI0 Port C: 01" in status and
                        b"POF: released (picture enabled)" in status,
                        f"{RELEASE.upper()} video-enable telemetry differs: {status!r}",
                    )
                os.write(console_master, b"VER\r")
                version = read_until(console_master, b"A>", 30.0)
                require(b"CP/M Plus 3.1 for Juku" in version,
                        f"{RELEASE.upper()} VER differs: {version!r}")
                os.write(console_master, b"DATE\r")
                date = read_until(console_master, b"A>", 30.0)
                require(b"DATE" in date,
                        f"{RELEASE.upper()} DATE produced no command transcript: {date!r}")
                os.write(console_master, b"DIAG CPU\r")
                diagnostic = read_until(console_master, b"A>", 60.0)
                require(b"CPU: PASS" in diagnostic,
                        f"{RELEASE.upper()} DIAG CPU differs: {diagnostic!r}")
                if RELEASE in ("c10", "c11"):
                    os.write(console_master, b"DIAG VIDEO\r")
                    video = read_until(console_master, b"A>", 60.0)
                    require(b"Video enable/console state: PASS" in video,
                            f"{RELEASE.upper()} DIAG VIDEO differs: {video!r}")
                os.write(console_master, b"DIR B:\r")
                drive_b = read_paged(console_master, 45.0)
                require(b"README" in drive_b or b"DIAG" in drive_b,
                        f"{RELEASE.upper()} native B: directory differs: {drive_b!r}")
                copy_name = f"{RELEASE.upper()}COPY.TXT".encode()
                os.write(console_master, b"PIP " + copy_name + b"=README.TXT\r")
                try:
                    copied = read_until(console_master, b"A>", 60.0)
                except AssertionError as error:
                    raise AssertionError(
                        f"{error}{failure_evidence(temp, host, simulator)}"
                    ) from error
                require(b"PIP " + copy_name + b"=README.TXT" in copied and
                        b"Bdos Err" not in copied,
                        f"{RELEASE.upper()} write exercise differs: {copied!r}")
                os.write(console_master, b"ERA " + copy_name + b"\r")
                try:
                    erased = read_until(console_master, b"A>", 30.0)
                except AssertionError as error:
                    raise AssertionError(
                        f"{error}{failure_evidence(temp, host, simulator)}"
                    ) from error
                require(b"ERA " + copy_name in erased,
                        f"{RELEASE.upper()} write cleanup differs: {erased!r}")
                os.write(console_master, b"WBOOT\r")
                try:
                    warm = read_until(console_master, b"A>", 45.0)
                except AssertionError as error:
                    raise AssertionError(
                        f"{error}{failure_evidence(temp, host, simulator)}"
                    ) from error
                require(b"CP/M" in warm or b"A>" in warm,
                        f"{RELEASE.upper()} warm boot differs: {warm!r}")
            if replace_host:
                host.send_signal(signal.SIGINT)
                host.wait(timeout=5.0)
                require(host.returncode == 0,
                        f"first host exit={host.returncode}")
                if RELEASE in ("c9", "c10", "c11"):
                    # Ensure at least one bounded target poll observes host
                    # loss before the stateless replacement appears.
                    time.sleep(0.5)
                if recover_session:
                    reconnect_command = [
                        str(HOST), "--serial-fd", str(serial_master),
                        "--system", str(SYSTEM), "--fast-stage", str(FASTBOOT),
                        "--network-rom", "--recover-session",
                        "--volume", str(volume), "--drive-b", str(DRIVE_B),
                        "--writable", "--disk-protocol", "3",
                        "--disk-baud", "19200", "--read-ahead", "3",
                        "--console-pty", os.ttyname(console_slave),
                        "--disk-timeout", disk_timeout,
                        "--log", str(temp / "host-reconnect.log"),
                        "--capture", str(temp / "host-reconnect.cap"),
                        "--verbose",
                    ]
                else:
                    reconnect_command = [
                        str(HOST), "--serial-fd", str(serial_master),
                        "--volume", str(volume), "--drive-b", str(DRIVE_B),
                        "--resume-disk", "--writable",
                        "--disk-protocol", "3", "--disk-baud", "19200",
                        "--read-ahead", "3", "--console-pty",
                        os.ttyname(console_slave), "--disk-timeout", disk_timeout,
                        "--log", str(temp / "host-reconnect.log"),
                        "--capture", str(temp / "host-reconnect.cap"),
                        "--verbose",
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
                if RELEASE in ("c9", "c10", "c11"):
                    os.write(console_master, b"STATUS\r")
                    recovered = read_until(console_master, b"A>", 60.0)
                    require(
                        b"N4 last failure: 02  reconnects: 01" in recovered
                        and b"N4 state flags: 1F  last operation: 20" in
                        recovered
                        and b"N4 failure reason: receive timeout" in recovered,
                        f"{RELEASE.upper()} reconnect telemetry differs: {recovered!r}",
                    )
            host.send_signal(signal.SIGINT)
            host.wait(timeout=5.0)
            require(host.returncode == 0,
                    f"host exit={host.returncode}: {host.stdout.read() if host.stdout else ''}")
            log = (temp / "host.log").read_text()
            require(("Fastboot V16" in log or
                     "V16 final reply not seen" in log) and
                    "requests=" in log,
                    f"host evidence incomplete: {log}")
            if reset_during_stream:
                require("boot-restarts=1" in log and "target-resets=1" in log,
                        f"target-reset recovery evidence differs: {log}")
            if recover_session:
                require("phase=discover serial=19200 8O1 passive" in log and
                        "C11 boot beacon received" in log,
                        f"C11 discovery evidence differs: {log}")
            if netdisk_reset:
                require("boot beacon received during NetDisk" in log and
                        "target reset during NetDisk; restarting V16" in log,
                        f"C11 NetDisk reset evidence differs: {log}")
            require((temp / "host.cap").stat().st_size > 100,
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
            requests = [json.loads(line) for line in
                        (temp / "requests.jsonl").read_text().splitlines()]
            require(boot["schema"] == "juku-janet-boot-result-v1" and
                    boot["network_rom"] is True and
                    boot["first_disk_request"]["elapsed_seconds"] > 0,
                    f"boot evidence differs: {boot}")
            require(any(record["operation"] in (0x11, 0x13, 0x14)
                        for record in requests),
                    "request evidence contains no disk read")
            require(any(record["operation"] == 0x21 for record in requests),
                    "request evidence contains no N4 console output")
            if RELEASE in ("c9", "c10", "c11"):
                for operation, description in (
                    (0x15, "NetDisk-v3 write"), (0x22, "time fetch"),
                    (0x24, "status publication"),
                    (0x25, "diagnostic publication"),
                    (0x27, "warm-boot publication"),
                ):
                    require(
                        any(record["operation"] == operation
                            for record in requests),
                        f"request evidence contains no {description} "
                        f"operation {operation:02X}",
                    )
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
    if recover_session:
        additions.append("passive session discovery")
    if netdisk_reset:
        additions.append("NetDisk-reset recovery")
    if late_host:
        additions.append("periodic late-host beacon")
    detail = "" if not additions else " + " + " + ".join(additions)
    print(
        f"JUKUHOST-{RELEASE.upper()}-COSIM-TEST: PASS "
        f"({RELEASE.upper()} V16 -> N3/N4 -> DIR{detail})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
