#!/usr/bin/env python3
"""Run the 16-bit DOS host's 9,600-baud Janet bootstrap in simulation."""

from __future__ import annotations

import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tests"))
from jukuhost_dos_c8_cosim_test import SerialBridge, compile_simulator  # noqa: E402

ROM = ROOT / "roms/ekta37.bin"
SYSTEM = ROOT / "media/system/CPM22.BIN"
HOST = ROOT / "build/dos/JUKUHOST.EXE"
SYSTEM_PREFIX = 0x0200
SYSTEM_BYTES = 0x1A00
SYSTEM_LOAD = 0xB400


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(f"JUKUHOST-DOS-STOCK-COSIM-TEST: {message}")


def parse_state(path: Path) -> dict[str, str]:
    return dict(
        line.split("=", 1) for line in path.read_text().splitlines()
        if "=" in line
    )


def main() -> int:
    require(shutil.which("dosbox-x") is not None, "dosbox-x is not installed")
    require(all(path.is_file() for path in (ROM, SYSTEM, HOST)),
            "host, stock ROM, or CPM22.BIN is missing")
    with tempfile.TemporaryDirectory(prefix="jukuhost-dos-stock-cosim.") as name:
        temp = Path(name)
        drive = temp / "drive"
        drive.mkdir()
        shutil.copyfile(HOST, drive / "JUKUHOST.EXE")
        shutil.copyfile(SYSTEM, drive / "CPM.BIN")
        # Required syntactically by the command-line interface; boot-only
        # never opens this image.
        (drive / "BASE.IMG").write_bytes(b"\x00" * 409600)
        trace = compile_simulator(temp)
        serial_master, serial_slave = os.openpty()
        bridge = SerialBridge(serial_master, baud=9600)
        bridge.start()
        checkpoint = temp / "final"
        environment = os.environ.copy()
        environment.update(
            JUKU_USART_PTY=os.ttyname(serial_slave),
            JUKU_USART_TRANSFER_CYCLES="64",
            JUKU_USART_BYTE_CYCLES="2300",
            JUKU_KEYS="TN0201",
            JUKU_KEY_HOLD_FRAMES="6",
            JUKU_KEY_GAP_FRAMES="8",
            JUKU_STOP_PC="0xCA00",
            JUKU_STOP_PC_AFTER_USART_RX="1000",
            JUKU_CHECKPOINT_PREFIX=str(checkpoint),
        )
        simulator_log = (temp / "simulator.log").open("wb")
        simulator = subprocess.Popen(
            [str(trace), str(ROM), "1000000000000", "0", "100000"],
            cwd=temp, env=environment, stdout=subprocess.DEVNULL,
            stderr=simulator_log,
        )
        dos_environment = os.environ.copy()
        dos_environment.update(SDL_VIDEODRIVER="dummy", SDL_AUDIODRIVER="dummy")
        dos = subprocess.run(
            [
                "dosbox-x", "-silent", "-fastlaunch", "-nogui", "-nomenu",
                "-noautoexec", "-exit", "-time-limit", "40",
                "-set", "cpu cputype=8086", "-set", "cpu core=normal",
                "-set", "cpu cycles=fixed 50000",
                "-set", (
                    "serial serial1=nullmodem server:127.0.0.1 "
                    f"port:{bridge.port} transparent:1 rxdelay:0 txdelay:0"
                ),
                "-c", f'mount c "{drive}"', "-c", "c:",
                "-c", (
                    "JUKUHOST --serial COM1 --system CPM.BIN "
                    "--volume BASE.IMG --boot-only > HOST.OUT"
                ),
                "-c", "exit",
            ],
            cwd=temp, env=dos_environment, stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT, timeout=50.0, check=False,
        )
        bridge.close()
        try:
            simulator.wait(timeout=10.0)
        except subprocess.TimeoutExpired:
            simulator.kill()
            simulator.wait()
        simulator_log.close()
        os.close(serial_master)
        os.close(serial_slave)
        output = (drive / "HOST.OUT").read_text(errors="replace") \
            if (drive / "HOST.OUT").exists() else ""
        diagnostic = (
            f"\nHOST:\n{output}\nDOSBOX:\n"
            f"{dos.stdout.decode(errors='replace')[-2000:]}\nSIMULATOR:\n"
            f"{(temp / 'simulator.log').read_text(errors='replace')[-2000:]}"
        )
        require(dos.returncode == 0 and bridge.error is None,
                f"DOS/bridge failure{diagnostic}")
        require("serial applied=9600 8O1" in output and
                "Janet request accepted: 02 -> 01" in output and
                "stock bootstrap complete" in output and "stop exit=0" in output,
                f"stock bootstrap evidence differs{diagnostic}")
        state = parse_state(checkpoint.with_suffix(".state"))
        ram = checkpoint.with_suffix(".ram").read_bytes()
        expected = SYSTEM.read_bytes()[SYSTEM_PREFIX:SYSTEM_PREFIX + SYSTEM_BYTES]
        require(state["pc"] == "CA00" and state["mode"] == "1",
                f"target did not enter CPM22{diagnostic}")
        require(ram[SYSTEM_LOAD:SYSTEM_LOAD + SYSTEM_BYTES] == expected,
                f"installed stock payload differs{diagnostic}")
    print("JUKUHOST-DOS-STOCK-COSIM-TEST: PASS (9600 8O1 Janet -> CPM22)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
