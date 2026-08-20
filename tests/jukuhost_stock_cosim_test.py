#!/usr/bin/env python3
"""Boot every frozen stock system through the native C host executable."""

from __future__ import annotations

import concurrent.futures
import os
from pathlib import Path
import pty
import re
import subprocess
import tempfile
import tty

ROOT = Path(__file__).resolve().parents[1]
HOST = ROOT / "build" / "jukuhost"
ROM = ROOT / "roms" / "ekta37.bin"
SYSTEMS = (
    "CPM22.BIN", "CPM231E.BIN", "EKDOS229.BIN", "EKDOS230.BIN",
    "EKDOSVSW.BIN",
)
SYSTEM_PREFIX = 0x0200
SYSTEM_BYTES = 0x1A00
SYSTEM_LOAD = 0xB400


def parse_state(path: Path) -> dict[str, str]:
    return dict(
        line.split("=", 1) for line in path.read_text().splitlines()
        if "=" in line
    )


def run_one(trace: Path, system: Path, root: Path, auto_identity: bool) -> str:
    suffix = "-auto" if auto_identity else ""
    case = root / f"{system.stem.lower()}{suffix}"
    case.mkdir()
    checkpoint = case / "final"
    master, slave = pty.openpty()
    tty.setraw(master)
    tty.setraw(slave)
    environment = os.environ.copy()
    environment.update(
        JUKU_USART_PTY=os.ttyname(slave),
        JUKU_USART_TRANSFER_CYCLES="64",
        JUKU_USART_BYTE_CYCLES="2300",
        JUKU_KEYS="TN0907" if auto_identity else "TN0201",
        JUKU_KEY_HOLD_FRAMES="6",
        JUKU_KEY_GAP_FRAMES="8",
        JUKU_STOP_PC="0xCA00",
        JUKU_STOP_PC_AFTER_USART_RX="1000",
        JUKU_CHECKPOINT_PREFIX=str(checkpoint),
    )
    with (case / "simulator.stdout").open("wb") as simulator_stdout, \
            (case / "simulator.stderr").open("wb") as simulator_stderr:
        simulator = subprocess.Popen(
            [str(trace), str(ROM), "1000000000000", "0", "100000"],
            cwd=case, env=environment, stdout=simulator_stdout,
            stderr=simulator_stderr,
        )
        host = subprocess.Popen([
            str(HOST), "--serial-fd", str(master), "--system", str(system),
            "--boot-only", "--timeout", "120", "--log", str(case / "host.log"),
            "--capture", str(case / "host.cap"),
        ], cwd=ROOT, text=True, stdout=subprocess.PIPE,
           stderr=subprocess.STDOUT, pass_fds=(master,))
        try:
            host_output, _ = host.communicate(timeout=130)
            simulator.wait(timeout=20)
        finally:
            if host.poll() is None:
                host.kill()
                host.wait()
            if simulator.poll() is None:
                simulator.kill()
                simulator.wait()
            os.close(master)
            os.close(slave)
    assert host.returncode == 0, f"{system.name}: host failed\n{host_output}"
    assert simulator.returncode == 0, (
        f"{system.name}: simulator exit={simulator.returncode}\n{host_output}"
    )
    assert "stock bootstrap complete" in host_output
    identity = re.search(r"Janet request accepted: ([0-9A-F]{2}) -> ([0-9A-F]{2})",
                         host_output)
    assert identity is not None, f"{system.name}: no learned identity\n{host_output}"
    if auto_identity:
        assert identity.groups() != ("02", "01")
    else:
        assert identity.groups() == ("02", "01")
    state = parse_state(checkpoint.with_suffix(".state"))
    ram = checkpoint.with_suffix(".ram").read_bytes()
    expected = system.read_bytes()[SYSTEM_PREFIX:SYSTEM_PREFIX + SYSTEM_BYTES]
    assert state["pc"] == "CA00" and state["mode"] == "1"
    assert state["usart_mode"] == "5E" and state["usart_command"] == "35"
    assert ram[SYSTEM_LOAD:SYSTEM_LOAD + SYSTEM_BYTES] == expected
    capture = (case / "host.cap").read_bytes()
    assert capture.startswith(b"JHCAP1\x01") and len(capture) > 1000
    return f"{system.name}{' [learned identity]' if auto_identity else ''}"


def main() -> int:
    systems = tuple(ROOT / "media" / "system" / name for name in SYSTEMS)
    if not HOST.is_file() or not ROM.is_file() or not all(p.is_file() for p in systems):
        raise SystemExit("missing jukuhost, stock ROM, or frozen system images")
    with tempfile.TemporaryDirectory(prefix="jukuhost-stock-cosim.") as name:
        root = Path(name)
        trace = root / "trace"
        subprocess.run([
            os.environ.get("CC", "cc"), "-O2", "-I", str(ROOT / "cosim"),
            "-o", str(trace), str(ROOT / "cosim/trace.c"),
            str(ROOT / "cosim/i8080.c"), str(ROOT / "cosim/juk_disk.c"),
            str(ROOT / "cosim/juku_fdc.c"),
        ], check=True)
        cases = tuple((system, False) for system in systems) + ((systems[0], True),)
        with concurrent.futures.ThreadPoolExecutor(max_workers=len(cases)) as pool:
            futures = [
                pool.submit(run_one, trace, system, root, auto)
                for system, auto in cases
            ]
            completed = [future.result() for future in futures]
    print(
        "JUKUHOST-STOCK-COSIM-TEST: PASS ("
        + ", ".join(completed) + ")"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
