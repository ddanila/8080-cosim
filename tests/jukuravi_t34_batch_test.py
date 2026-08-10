#!/usr/bin/env python3
"""Exercise the complete one-session T34 batch through the real host/PTTY path."""

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
import build_d0_clocked_pit as firmware


def fail(message: str) -> None:
    print(f"JUKURAVI-T34-BATCH: FAIL: {message}", file=sys.stderr)
    raise SystemExit(1)


def main() -> int:
    if len(sys.argv) != 3:
        fail("usage: test.py /path/to/trace diag-d0-clocked-pit.bin")
    trace, rom = (Path(value).resolve() for value in sys.argv[1:])
    image, _ = firmware.build()
    if not trace.is_file() or not rom.is_file() or rom.read_bytes() != image:
        fail("trace or exact T34 image differs")

    with tempfile.TemporaryDirectory(prefix="jukuravi-t34-batch-test-") as name:
        temp = Path(name)
        logs = temp / "logs"
        master, slave = pty.openpty()
        tty.setraw(slave)
        environment = os.environ.copy()
        environment.update(
            JUKU_USART_PTY=os.ttyname(slave),
            JUKU_USART_TRANSFER_CYCLES="64",
            JUKU_USART_BYTE_CYCLES="512",
        )
        with (
            (temp / "cosim.stdout").open("wb") as stdout,
            (temp / "cosim.stderr").open("wb") as stderr,
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
            fail(f"batch failed:\n{completed.stdout}{completed.stderr}")

        summaries = list(logs.glob("*.json"))
        if len(summaries) != 1:
            fail(f"expected one summary, found {len(summaries)}")
        summary = json.loads(summaries[0].read_text())
        batch = summary.get("batch")
        if not isinstance(batch, dict) or batch.get("overall_verdict") != "pass":
            fail(f"batch verdict differs: {batch!r}")
        loader = summary.get("loader")
        if not isinstance(loader, dict):
            fail("bootstrap loader evidence is missing")
        if loader.get("config", {}).get("order") != "before_probe":
            fail(f"CONFIG-first evidence differs: {loader.get('config')!r}")
        if loader.get("probe", {}).get("cookie_hex") != "5432380055AAC6C7":
            fail("bootstrap exact-cookie PROBE evidence is missing")

        results = batch.get("results")
        if not isinstance(results, list):
            fail("result list is missing")
        by_name = {item.get("name"): item for item in results}
        expected_passes = {
            "verified-return",
            "d57-raw",
            "a12-write-map",
            "a12-lhld",
            "a12-instruction",
            "a12-ready-classes",
            "a12-boundary",
            "cpu-increment-registers",
            "execution-address",
        }
        if set(by_name) != expected_passes | {"cpu-host-timebase"}:
            fail(f"result names differ: {sorted(by_name)}")
        bad = {
            name: by_name[name].get("verdict")
            for name in expected_passes
            if by_name[name].get("verdict") != "pass"
        }
        if bad:
            fail(f"clean functional results differ: {bad}")
        timing = by_name["cpu-host-timebase"]
        if (
            timing.get("verdict") != "measured"
            or not isinstance(timing.get("cpu_clock_mhz"), (int, float))
        ):
            fail(f"host-timed CPU result differs: {timing!r}")
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

    print(
        "JUKURAVI-T34-BATCH: PASS "
        "(CONFIG-first; one session; verified CALL; D57; six CPU/A12 probes; "
        "4000/5000 execution)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
