#!/usr/bin/env python3
"""Exercise the compact T36 local full-RAM sweep through host and cosim."""

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
JUKURAVI = ROOT / "spinoffs" / "jukuravi"
FIRMWARE = JUKURAVI / "firmware"
sys.path.insert(0, str(JUKURAVI))
sys.path.insert(0, str(FIRMWARE))
import build_d0_row_refresh as firmware  # noqa: E402
import local_ram  # noqa: E402


def fail(message: str) -> None:
    print(f"JUKURAVI-LOCAL-FULL-RAM: FAIL: {message}", file=sys.stderr)
    raise SystemExit(1)


def run_case(
    trace: Path, rom: Path, temp: Path, *, ram_fault: str | None = None
) -> tuple[subprocess.CompletedProcess[str], dict[str, object], str]:
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
    if ram_fault is not None:
        environment["JUKU_RAM_FAULT"] = ram_fault
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
                "--no-retention-sweep",
                "--local-full-ram-sweep",
                "--local-full-ram-hold-ms",
                "0",
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
    summaries = list(logs.glob("*.json"))
    if len(summaries) != 1:
        fail(f"expected one summary, found {len(summaries)}")
    return completed, json.loads(summaries[0].read_text()), stderr_path.read_text()


def local_result(summary: dict[str, object]) -> dict[str, object]:
    batch = summary.get("batch")
    if not isinstance(batch, dict):
        fail("batch summary is missing")
    results = batch.get("results")
    if not isinstance(results, list):
        fail("result list is missing")
    result = next(
        (item for item in results if item.get("name") == "local-full-ram-sweep"),
        None,
    )
    if not isinstance(result, dict):
        fail("local full-RAM result is missing")
    return result


def main() -> int:
    if len(sys.argv) != 3:
        fail("usage: test.py /path/to/trace diag-d0-row-refresh.bin")
    trace, rom = (Path(value).resolve() for value in sys.argv[1:])
    image, _ = firmware.build()
    if not trace.is_file() or not rom.is_file() or rom.read_bytes() != image:
        fail("trace or exact T36 image differs")

    for pattern_name, pattern_id in local_ram.PATTERNS:
        for stage in local_ram.STAGES:
            payload = local_ram.build_probe(stage, pattern_id)
            if (
                len(payload) != local_ram.RESULT_OFFSET + local_ram.RESULT_SIZE
                or payload[local_ram.RESULT_OFFSET : local_ram.RESULT_OFFSET + 4]
                != b"FRT1"
            ):
                fail(f"probe layout differs for {pattern_name}/{stage.name}")

    with tempfile.TemporaryDirectory(prefix="jukuravi-local-full-ram-") as name:
        completed, summary, cosim_stderr = run_case(trace, rom, Path(name))
        if completed.returncode:
            fail(
                f"batch failed:\n{completed.stdout}{completed.stderr}"
                f"cosim:\n{cosim_stderr}"
            )
        batch = summary.get("batch")
        if not isinstance(batch, dict) or batch.get("overall_verdict") != "pass":
            fail(f"batch verdict differs: {batch!r}")
        local = local_result(summary)
        if (
            not isinstance(local, dict)
            or local.get("verdict") != "pass"
            or local.get("bytes_per_pattern") != 0x8000
            or local.get("locally_tested_bytes_per_pattern") != 0xE000
            or local.get("failed_patterns") != []
        ):
            fail(f"local sweep summary differs: {local!r}")
        patterns = local.get("patterns")
        if (
            not isinstance(patterns, list)
            or [item.get("name") for item in patterns]
            != [name for name, _ in local_ram.PATTERNS]
            or any(item.get("verdict") != "pass" for item in patterns)
            or any(
                len(item.get("stages", [])) != 2
                or any(stage.get("verdict") != "pass" for stage in item["stages"])
                for item in patterns
            )
        ):
            fail(f"local pattern evidence differs: {patterns!r}")
        if batch.get("local_full_ram_sweep") is not True:
            fail("batch did not record local full-RAM selection")
        if "observed all 128 refresh rows in " not in cosim_stderr:
            fail("decay model did not observe complete physical-row refresh")

    with tempfile.TemporaryDirectory(prefix="jukuravi-local-full-ram-fault-") as name:
        completed, summary, cosim_stderr = run_case(
            trace, rom, Path(name), ram_fault="6000:01:00"
        )
        if completed.returncode != 1:
            fail(
                f"faulted batch returned {completed.returncode}:\n"
                f"{completed.stdout}{completed.stderr}cosim:\n{cosim_stderr}"
            )
        local = local_result(summary)
        if local.get("verdict") != "fail":
            fail(f"faulted local sweep passed: {local!r}")
        patterns = {item["name"]: item for item in local["patterns"]}
        if (
            patterns["zeros"]["verdict"] != "pass"
            or patterns["address-xor"]["verdict"] != "pass"
            or patterns["ones"]["mismatching_bytes"] != 2
            or patterns["checkerboard"]["mismatching_bytes"] != 2
            or patterns["ones"]["xor_or"] != "0x01"
            or patterns["checkerboard"]["xor_or"] != "0x01"
            or patterns["ones"]["candidate_packages"] != ["D84"]
            or patterns["checkerboard"]["candidate_packages"] != ["D84"]
        ):
            fail(f"fault attribution differs: {patterns!r}")
        for pattern_name in ("ones", "checkerboard"):
            for stage in patterns[pattern_name]["stages"]:
                if stage["first_mismatch"]["address"] != "0x6000":
                    fail(f"first fault address differs: {stage!r}")

    print(
        "JUKURAVI-LOCAL-FULL-RAM: PASS "
        "(T36 decay model; two code homes; four local patterns; "
        "32 KiB union; D84 fault attribution)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
