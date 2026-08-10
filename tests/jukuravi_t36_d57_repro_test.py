#!/usr/bin/env python3
"""Reproduce the physical CS00024 D57 channel-2 signature in exact T36."""

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
    print(f"JUKURAVI-T36-D57-REPRO: FAIL: {message}", file=sys.stderr)
    raise SystemExit(1)


def main() -> int:
    if len(sys.argv) != 3:
        fail("usage: test.py /path/to/trace diag-d0-row-refresh.bin")
    trace, rom = (Path(value).resolve() for value in sys.argv[1:])
    image, _ = firmware.build()
    if not trace.is_file() or not rom.is_file() or rom.read_bytes() != image:
        fail("trace or exact T36 image differs")

    with tempfile.TemporaryDirectory(prefix="jukuravi-t36-d57-repro-") as name:
        temp = Path(name)
        logs = temp / "logs"
        master, slave = pty.openpty()
        tty.setraw(slave)
        environment = os.environ.copy()
        environment.update(
            JUKU_USART_PTY=os.ttyname(slave),
            JUKU_USART_TRANSFER_CYCLES="64",
            JUKU_USART_BYTE_CYCLES="512",
            # Apply the physical channel-2 read signature at port 1Ah.  This
            # is a discriminator reproduction, not a package-level cause
            # model: (value & ~66h) | 99h is always exactly 99h.
            JUKU_PIT_FAULT="1A:66:99",
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
                    "--only-d57",
                    "--log-dir",
                    str(logs),
                ],
                cwd=ROOT,
                pass_fds=(master,),
                text=True,
                capture_output=True,
                check=False,
                timeout=300,
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
        if completed.returncode != 1:
            fail(
                f"faulted batch returned {completed.returncode}:\n"
                f"{completed.stdout}{completed.stderr}"
                f"cosim:\n{stderr_path.read_text()}"
            )

        summaries = list(logs.glob("*.json"))
        if len(summaries) != 1:
            fail(f"expected one summary, found {len(summaries)}")
        summary = json.loads(summaries[0].read_text())
        diagnostic = summary.get("diagnostic_status")
        if not isinstance(diagnostic, dict) or diagnostic.get("d57") is not True:
            fail(f"boot D57 predicate unexpectedly detected channel 2: {diagnostic!r}")
        batch = summary.get("batch")
        if (
            not isinstance(batch, dict)
            or batch.get("overall_verdict") != "findings"
            or batch.get("core_failures") != ["d57-raw"]
            or batch.get("d57_only") is not True
        ):
            fail(f"focused batch verdict differs: {batch!r}")
        results = batch.get("results")
        if not isinstance(results, list):
            fail("result list is missing")
        by_name = {item.get("name"): item for item in results}
        if set(by_name) != {"verified-return", "cpu-host-timebase", "d57-raw"}:
            fail(f"focused result set differs: {sorted(by_name)}")
        raw = by_name["d57-raw"]
        expected_record = "FF3FFF3F9999"
        expected = "44353752A5010800" + expected_record * 8
        if raw.get("observed_hex") != expected or raw.get("verdict") != "fail":
            fail(f"D57 signature differs: {raw!r}")
        failures = raw.get("bad_samples")
        if (
            not isinstance(failures, list)
            or len(failures) != 8
            or any(
                item
                != {
                    "repetition": index,
                    "channel": 2,
                    "high": "99",
                    "low": "99",
                }
                for index, item in enumerate(failures, 1)
            )
        ):
            fail(f"channel attribution differs: {failures!r}")

    print(
        "JUKURAVI-T36-D57-REPRO: PASS "
        "(boot predicate clean; raw channel 2=99/99 x8; signature-only model)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
