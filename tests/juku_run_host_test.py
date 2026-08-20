#!/usr/bin/env python3
"""Prove the interactive wrapper has only the native C serving path."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import juku_run  # noqa: E402
import netboot_demo_gifs as demos  # noqa: E402


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="juku-run-host.") as name:
        work = Path(name)
        common = dict(
            drive_b=None, writable=False, disk_baud=19200,
            disk_protocol=3, read_ahead=8,
        )
        netboot = argparse.Namespace(
            netboot=Path("system.bin"), disk=None, **common,
        )
        command = juku_run.host_command(
            netboot, "/dev/pts/1", work, Path("/host/jukuhost"),
        )
        if command != [
            "/host/jukuhost", "--serial", "/dev/pts/1",
            "--log", str(work / "jukuhost.log"),
            "--capture", str(work / "jukuhost.cap"),
            "--system", "system.bin", "--boot-only",
        ]:
            raise AssertionError(f"native netboot command differs: {command}")

        disk = argparse.Namespace(
            netboot=None, disk=["system.bin", "volume.img"],
            drive_b=Path("games.juk"), writable=True,
            disk_baud=19200, disk_protocol=3, read_ahead=8,
        )
        command = juku_run.host_command(
            disk, "/dev/pts/2", work, Path("/host/jukuhost"),
        )
        joined = " ".join(map(str, command))
        for required in (
            "/host/jukuhost --serial /dev/pts/2",
            "--system system.bin --volume volume.img",
            "--disk-baud 19200 --disk-protocol 3 --read-ahead 8",
            "--drive-b games.juk --writable",
        ):
            if required not in joined:
                raise AssertionError(
                    f"native disk command lacks {required!r}: {joined}"
                )
        if "python" in joined or "janet_" in joined:
            raise AssertionError(f"Python host fallback remains: {joined}")

        for scenario in ("cpm22", "cpm31_netrom"):
            command, _rom, _keys = demos.scenario_command(
                scenario, "/dev/pts/3", work, "/dev/pts/4",
            )
            joined = " ".join(command)
            if command[0] != str(ROOT / "build" / "jukuhost") or \
                    "python" in joined or "janet_" in joined:
                raise AssertionError(
                    f"{scenario} demo retained another host: {joined}"
                )
            if scenario == "cpm31_netrom" and \
                    "--fast-stage" not in command:
                raise AssertionError("current network-ROM demo lacks V16")
    print("JUKU-RUN-HOST-TEST: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
