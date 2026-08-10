#!/usr/bin/env python3
"""Exercise the physical-row-refresh T36 batch through the real host/PTTY path."""

from __future__ import annotations

import json
import os
import pty
import subprocess
import sys
import tempfile
import tty
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BATCH = ROOT / "spinoffs" / "jukuravi" / "batch.py"
FIRMWARE = ROOT / "spinoffs" / "jukuravi" / "firmware"
sys.path.insert(0, str(FIRMWARE))
import build_d0_row_refresh as firmware  # noqa: E402


def fail(message: str) -> None:
    print(f"JUKURAVI-T36-BATCH: FAIL: {message}", file=sys.stderr)
    raise SystemExit(1)


def main() -> int:
    if len(sys.argv) != 3:
        fail("usage: test.py /path/to/trace diag-d0-row-refresh.bin")
    trace, rom = (Path(value).resolve() for value in sys.argv[1:])
    image, _ = firmware.build()
    if not trace.is_file() or not rom.is_file() or rom.read_bytes() != image:
        fail("trace or exact T36 image differs")

    with tempfile.TemporaryDirectory(prefix="jukuravi-t36-batch-test-") as name:
        temp = Path(name)
        logs = temp / "logs"
        master, slave = pty.openpty()
        tty.setraw(slave)
        environment = os.environ.copy()
        environment.update(
            JUKU_USART_PTY=os.ttyname(slave),
            JUKU_USART_TRANSFER_CYCLES="64",
            JUKU_USART_BYTE_CYCLES="512",
            JUKU_DRAM_RETENTION_CYCLES="350000",
            JUKU_DRAM_RETENTION_ARM_PC="07A9",
        )
        stderr_path = temp / "cosim.stderr"
        with (
            (temp / "cosim.stdout").open("wb") as stdout,
            stderr_path.open("wb") as stderr,
        ):
            cosim = subprocess.Popen(
                [str(trace), str(rom), "5000000000"],
                cwd=temp,
                env=environment,
                stdout=stdout,
                stderr=stderr,
            )
        try:
            completed = subprocess.run(
                [
                    sys.executable,
                    str(BATCH),
                    "--fd",
                    str(master),
                    "--rom",
                    "t36",
                    "--timeout",
                    "60",
                    "--banner-timeout",
                    "30",
                    "--loader-timeout",
                    "30",
                    "--loader-guard-ms",
                    "0",
                    "--retention-guards-ms",
                    "0,0",
                    "--full-ram-sweep",
                    "--full-ram-hold-ms",
                    "0",
                    "--full-ram-end",
                    "4200",
                    "--log-dir",
                    str(logs),
                ],
                cwd=ROOT,
                pass_fds=(master,),
                text=True,
                capture_output=True,
                check=False,
                timeout=600,
            )
        finally:
            cosim.terminate()
            try:
                cosim.wait(timeout=5)
            except subprocess.TimeoutExpired:
                cosim.kill()
                cosim.wait()
            os.close(master)
            os.close(slave)
        if completed.returncode:
            fail(
                f"batch failed:\n{completed.stdout}{completed.stderr}"
                f"cosim:\n{stderr_path.read_text()}"
            )

        summaries = list(logs.glob("*.json"))
        if len(summaries) != 1:
            fail(f"expected one summary, found {len(summaries)}")
        summary = json.loads(summaries[0].read_text())
        batch = summary.get("batch")
        if (
            not isinstance(batch, dict)
            or batch.get("overall_verdict") != "pass"
            or batch.get("rom_profile") != "t36"
            or batch.get("rom_version") != "0x1E"
            or batch.get("rom_crc16") != "0xC617"
        ):
            fail(f"batch identity/verdict differs: {batch!r}")
        loader = summary.get("loader")
        refresh = None if not isinstance(loader, dict) else loader.get("refresh")
        if not isinstance(refresh, dict) or refresh.get("enabled") is not True:
            fail(f"T36 refresh telemetry is missing: {refresh!r}")

        results = batch.get("results")
        if not isinstance(results, list):
            fail("result list is missing")
        by_name = {item.get("name"): item for item in results}
        expected = {
            "verified-return",
            "cpu-host-timebase",
            "d57-raw",
            "a12-write-map",
            "a12-lhld",
            "a12-instruction",
            "a12-ready-classes",
            "a12-boundary",
            "cpu-increment-registers",
            "execution-address",
            "full-ram-sweep",
        }
        if set(by_name) != expected:
            fail(f"result names differ: {sorted(by_name)}")
        bad = {
            name: item.get("verdict")
            for name, item in by_name.items()
            if item.get("verdict") not in ("pass", "measured")
        }
        if bad:
            fail(f"functional results differ: {bad}")
        full_ram = by_name["full-ram-sweep"]
        if (
            full_ram.get("bytes_per_pattern") != 0x0200
            or full_ram.get("failed_patterns") != []
            or [item.get("name") for item in full_ram.get("patterns", [])]
            != ["zeros", "ones", "checkerboard", "address"]
        ):
            fail(f"full-RAM sweep evidence differs: {full_ram!r}")
        timing = by_name["cpu-host-timebase"]
        if timing.get("delta_tstates") != 1_078_000:
            fail(f"refresh-safe timebase differs: {timing!r}")
        for name in (
            "a12-write-map",
            "a12-lhld",
            "a12-instruction",
            "a12-ready-classes",
            "a12-boundary",
            "cpu-increment-registers",
        ):
            operation = by_name[name].get("operation")
            wrapper = (
                None
                if not isinstance(operation, dict)
                else operation.get("refresh_wrapper")
            )
            if (
                not isinstance(wrapper, dict)
                or wrapper.get("api") != "0x07A9"
                or wrapper.get("address") != "0x6F00"
            ):
                fail(f"{name} did not use the T36 refresh wrapper")
        retention = batch.get("retention_sweep")
        if (
            not isinstance(retention, list)
            or len(retention) != 2
            or any(
                item.get("verdict") != "pass" or item.get("recovery") != "pass"
                for item in retention
            )
        ):
            fail(f"retention/recovery evidence differs: {retention!r}")
        if "observed all 128 refresh rows in " not in stderr_path.read_text():
            fail("retention model did not observe all refresh rows")

    print(
        "JUKURAVI-T36-BATCH: PASS "
        "(decaying RAM; 4x512-byte integration sweep; cooperative CPU+D57; full batch)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
