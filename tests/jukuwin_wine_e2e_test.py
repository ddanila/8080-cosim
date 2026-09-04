#!/usr/bin/env python3
"""Run the actual Win32 host through Wine against stock and C11 cosim."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import tempfile
import time
import tty


ROOT = Path(__file__).resolve().parents[1]
CPM = Path(os.environ.get("CPM_PLUS_JUKU_ROOT", ROOT.parent / "cpm-plus-juku"))
TRACE_SOURCES = (
    ROOT / "cosim/trace.c",
    ROOT / "cosim/i8080.c",
    ROOT / "cosim/juk_disk.c",
    ROOT / "cosim/juku_fdc.c",
)


def wineserver_command() -> str:
    installed = shutil.which("wineserver")
    if installed is not None:
        return installed
    candidates = sorted(Path("/usr/lib").glob("*-linux-gnu/wine/wineserver"))
    if candidates:
        return str(candidates[0])
    raise AssertionError("Wine server binary is missing")


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def wine_path(path: Path) -> str:
    return "Z:" + str(path.resolve()).replace("/", "\\")


def wait_for(paths: tuple[Path, ...], process: subprocess.Popen[bytes],
             timeout: float) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if all(path.exists() for path in paths):
            return
        if process.poll() is not None:
            raise AssertionError(f"socat exited before PTYs were ready: {process.returncode}")
        time.sleep(0.05)
    raise AssertionError("socat did not create its PTY links")


def wait_for_output(path: Path, marker: bytes,
                    process: subprocess.Popen[bytes], timeout: float) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if path.exists() and marker in path.read_bytes():
            return
        if process.poll() is not None:
            raise AssertionError(
                f"Windows host exited before {marker!r}: {process.returncode}"
            )
        time.sleep(0.05)
    raise AssertionError(f"Windows host did not emit {marker!r}")


def build_trace(output: Path) -> None:
    subprocess.run([
        os.environ.get("CC", "cc"), "-O2", "-I", str(ROOT / "cosim"),
        "-o", str(output), *(str(path) for path in TRACE_SOURCES),
    ], check=True)


def config_text(mode: str, volume: Path, working: Path, drive_b: Path | None,
                evidence: Path) -> str:
    return f"""[juku]
mode={mode}
serial=COM1
serial_id=
auto_listen=no

[drive_a]
image={wine_path(volume)}
mode=snapshot
working={wine_path(working)}

[drive_b]
image={wine_path(drive_b) if drive_b else ''}

[evidence]
directory={wine_path(evidence)}
capture=yes
verbose=yes
keep_sessions=0
"""


def simulator_environment(case: str, serial_path: Path, console_path: str,
                          checkpoint: Path) -> dict[str, str]:
    environment = os.environ.copy()
    environment.update(
        JUKU_USART_PTY=str(serial_path),
        JUKU_CONSOLE_PTY=console_path,
        JUKU_USART_TRANSFER_CYCLES="64",
        JUKU_USART_BYTE_CYCLES="2300",
        JUKU_USART_PIT_CLOCK="1",
        JUKU_USART_PIT_CPU_HZ="1700000",
        JUKU_REALTIME_HZ="1700000",
        JUKU_DISABLE_SETTLE="1",
        JUKU_S21_CONFIG="0x06",
        JUKU_CHECKPOINT_PREFIX=str(checkpoint),
    )
    if case == "stock":
        environment.update(
            JUKU_KEYS="TN",
            JUKU_KEY_HOLD_FRAMES="6",
            JUKU_KEY_GAP_FRAMES="8",
        )
    return environment


def decode_evidence(case: str, capture: Path, case_dir: Path,
                    system: Path, fastboot: Path) -> None:
    requests = case_dir / "requests.jsonl"
    boot = case_dir / "boot.json"
    result = subprocess.run([
        sys.executable, str(ROOT / "tools/jukuhost_evidence.py"), str(capture),
        "--requests-jsonl", str(requests), "--boot-result", str(boot),
        "--system", str(system), "--fast-stage", str(fastboot),
        "--serial", "Wine COM1",
    ], cwd=ROOT, text=True, stdout=subprocess.PIPE,
       stderr=subprocess.STDOUT, check=False)
    require(result.returncode == 0, f"{case}: evidence decode failed: {result.stdout}")
    boot_result = json.loads(boot.read_text())
    records = [json.loads(line) for line in requests.read_text().splitlines()]
    require(boot_result["network_rom"] is (case == "c11"),
            f"{case}: boot mode differs: {boot_result}")
    require(any(record["operation"] in (0x11, 0x13, 0x14)
                for record in records), f"{case}: no disk read request captured")


def run_case(case: str, executable: Path, prefix: Path, trace: Path,
             wine_environment: dict[str, str], evidence_root: Path) -> None:
    case_dir = evidence_root / case
    case_dir.mkdir()
    wine_serial = case_dir / "wine-com1"
    simulator_serial = case_dir / "simulator-serial"
    socat_log = (case_dir / "socat.stderr").open("wb")
    socat = subprocess.Popen([
        "socat", "-d", "-d",
        f"pty,raw,echo=0,link={wine_serial}",
        f"pty,raw,echo=0,link={simulator_serial}",
    ], stdout=subprocess.DEVNULL, stderr=socat_log)
    simulator: subprocess.Popen[bytes] | None = None
    host: subprocess.Popen[bytes] | None = None
    console_master, console_slave = os.openpty()
    tty.setraw(console_master)
    tty.setraw(console_slave)
    host_output = (case_dir / "wine-host.output").open("wb")
    simulator_output = (case_dir / "simulator.stderr").open("wb")
    try:
        wait_for((wine_serial, simulator_serial), socat, 5.0)
        com1 = prefix / "dosdevices/com1"
        if com1.is_symlink() or com1.exists():
            com1.unlink()
        com1.symlink_to(wine_serial.resolve())
        # Wine 10 can resolve \\.\COM1 relative to the process directory
        # instead of dosdevices (Wine bug 59272). Keep the normal mapping and
        # add the documented test-only workaround so this exercises serial I/O
        # rather than that Wine path-resolution defect.
        working_com1 = case_dir / "COM1"
        working_com1.symlink_to(wine_serial.resolve())
        # Wine's device manager also consults HKLM\Software\Wine\Ports. Wine
        # 10 needs this mapping for \\.\COM1 in addition to dosdevices on the
        # affected path-resolution builds (Wine bug 59272).
        server = wineserver_command()
        registry = subprocess.run([
            "xvfb-run", "-a", "wine", "reg", "add",
            r"HKLM\Software\Wine\Ports", "/v", "COM1", "/t", "REG_SZ",
            "/d", str(wine_serial.resolve()), "/f",
        ], cwd=case_dir, env=wine_environment, stdout=subprocess.PIPE,
           stderr=subprocess.STDOUT, text=True, check=False)
        require(registry.returncode == 0,
                f"{case}: cannot configure Wine COM1: {registry.stdout}")
        refresh = subprocess.run(
            ["xvfb-run", "-a", "wineboot", "-u"], cwd=case_dir,
            env=wine_environment, stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT, text=True, check=False)
        require(refresh.returncode == 0,
                f"{case}: Wine device refresh failed: {refresh.stdout}")
        subprocess.run([server, "-w"], env=wine_environment, check=True)

        if case == "c11":
            rom = ROOT / "spinoffs/jukuravi/network-rom/juku-network-rom-abi1.4-c11.bin"
            volume = CPM / "out/cpm-plus-juku-c11-full.img"
            drive_b = CPM / "out/cpm-plus-juku-apps.juk"
            system = CPM / "out/cpm-plus-juku-network-rom-c11-system.bin"
            fastboot = CPM / "out/cpm-plus-juku-network-rom-c11-fastboot-v16.bin"
        else:
            rom = ROOT / "spinoffs/jukuravi/remix/ekta4401.bin"
            volume = ROOT / "tests/fixtures/jukuhost-v15/cpm-plus-juku.img"
            drive_b = None
            system = ROOT / "tests/fixtures/jukuhost-v15/cpm-plus-juku-system.bin"
            fastboot = ROOT / "tests/fixtures/jukuhost-v15/cpm-plus-juku-fastboot-v15.bin"
        for artifact in (rom, volume, system, fastboot, *(tuple() if drive_b is None else (drive_b,))):
            require(artifact.is_file(), f"{case}: missing {artifact}")
        original_digest = hashlib.sha256(volume.read_bytes()).digest()
        working = case_dir / "working.img"
        logs = case_dir / "logs"
        config = case_dir / "JUKUWIN.INI"
        config.write_text(config_text(case, volume, working, drive_b, logs),
                          encoding="ascii", newline="\n")

        host_command = [
            "xvfb-run", "-a", "wine", str(executable), "--headless",
            "--config", wine_path(config), "--disk-timeout", "8",
        ]
        if os.environ.get("JUKUWIN_WINE_STRACE") == "1":
            host_command = [
                "strace", "-f", "-o", str(case_dir / "wine.strace"),
                "-e", "trace=openat,read,write,ioctl", *host_command,
            ]
        host = subprocess.Popen(host_command, cwd=case_dir,
           env=wine_environment, stdout=host_output,
           stderr=subprocess.STDOUT)
        wait_for_output(case_dir / "wine-host.output", b"serial applied=",
                        host, 15.0)
        simulator = subprocess.Popen([
            str(trace), str(rom), "1000000000000", "0", "100000",
        ], cwd=case_dir,
           env=simulator_environment(case, simulator_serial,
                                     os.ttyname(console_slave),
                                     case_dir / "final"),
           stdout=subprocess.DEVNULL, stderr=simulator_output)
        try:
            host.wait(timeout=float(os.environ.get(
                "JUKUWIN_WINE_CASE_TIMEOUT", "90")))
        except subprocess.TimeoutExpired as error:
            raise AssertionError(f"{case}: Windows host exceeded test timeout") from error
        require(host.returncode == 0,
                f"{case}: Wine/host exit was {host.returncode}")
        sessions = sorted(path for path in logs.iterdir() if path.is_dir())
        require(len(sessions) == 1, f"{case}: expected one evidence session")
        log = sessions[0] / "JUKUHOST.LOG"
        capture = sessions[0] / "JUKUHOST.CAP"
        text = log.read_text(errors="replace")
        require("phase=netdisk" in text and "stop exit=0" in text and
                "requests=" in text, f"{case}: host log is incomplete: {text}")
        if case == "c11":
            require("C11 boot beacon received" in text and
                    ("Fastboot V16 complete" in text or
                     "V16 final reply not seen" in text),
                    f"c11: boot evidence is incomplete: {text}")
        else:
            require("stock bootstrap complete" in text and
                    "stock-assisted V15 core" in text,
                    f"stock: boot evidence is incomplete: {text}")
        require(capture.stat().st_size > 100, f"{case}: capture is too small")
        require(working.stat().st_size == 409600,
                f"{case}: snapshot working image differs")
        require(hashlib.sha256(volume.read_bytes()).digest() == original_digest,
                f"{case}: immutable base image changed")
        decode_evidence(case, capture, case_dir, system, fastboot)
        print(f"JUKUWIN-WINE-E2E-{case.upper()}: PASS")
    except BaseException:
        print(f"JUKUWIN-WINE-E2E: retained failure evidence: {case_dir}",
              file=sys.stderr)
        raise
    finally:
        for process in (host, simulator, socat):
            if process is not None and process.poll() is None:
                process.send_signal(signal.SIGTERM)
                try:
                    process.wait(timeout=3.0)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()
        host_output.close()
        simulator_output.close()
        socat_log.close()
        os.close(console_master)
        os.close(console_slave)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--selftest-only", action="store_true")
    parser.add_argument("executable", type=Path)
    args = parser.parse_args()
    executable = args.executable.resolve()
    require(executable.is_file(), f"missing {executable}")
    wineserver = wineserver_command()
    with tempfile.TemporaryDirectory(
            prefix="jukuwin-wine-prefix.", dir=ROOT / "build") as prefix_name:
        prefix = Path(prefix_name)
        wine_environment = os.environ.copy()
        wine_environment.update(
            WINEPREFIX=str(prefix), WINEARCH="win32", WINEDEBUG="-all",
        )
        try:
            bootstrap = subprocess.run(
                ["xvfb-run", "-a", "wineboot", "-u"], env=wine_environment,
                cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True, check=False,
            )
            require(bootstrap.returncode == 0,
                    "32-bit Wine prefix initialization failed; install "
                    "wine32:i386:\n" + bootstrap.stdout)
            subprocess.run([wineserver, "-w"], env=wine_environment,
                           check=True)
            selftest = subprocess.run(
                ["xvfb-run", "-a", "wine", str(executable), "--selftest"],
                env=wine_environment, cwd=ROOT, stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT, text=True, check=False,
            )
            require(selftest.returncode == 0,
                    f"Windows self-test failed ({selftest.returncode}):\n"
                    f"{selftest.stdout}")
            print("JUKUWIN-WINE-SELFTEST: PASS")
            if not args.selftest_only:
                evidence_root = Path(tempfile.mkdtemp(
                    prefix="jukuwin-wine-e2e.", dir=ROOT / "build"))
                trace = evidence_root / "trace"
                build_trace(trace)
                for case in ("stock", "c11"):
                    run_case(case, executable, prefix, trace,
                             wine_environment, evidence_root)
                print(f"JUKUWIN-WINE-E2E: PASS (evidence {evidence_root})")
        finally:
            subprocess.run([wineserver, "-k"], env=wine_environment,
                           check=False)
            subprocess.run([wineserver, "-w"], env=wine_environment,
                           check=False)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (AssertionError, OSError) as error:
        raise SystemExit(f"JUKUWIN-WINE-E2E: {error}") from error
