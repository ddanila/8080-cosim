#!/usr/bin/env python3
"""Discriminate CS00015's CPU fault from CS00024's wrapper failure."""

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


def fail(message: str) -> None:
    print(f"JUKURAVI-T35-WRAPPER-A12: FAIL: {message}", file=sys.stderr)
    raise SystemExit(1)


def run_case(
    trace: Path,
    rom: Path,
    root: Path,
    label: str,
    wrapper_address: str,
    *,
    cpu_fault: bool,
    direct: bool = False,
    ram_lanes: bool = False,
    extra_environment: dict[str, str] | None = None,
) -> tuple[subprocess.CompletedProcess[str], dict[str, object], str]:
    case = root / label
    case.mkdir()
    logs = case / "logs"
    master, slave = pty.openpty()
    tty.setraw(slave)
    environment = os.environ.copy()
    environment.update(
        JUKU_USART_PTY=os.ttyname(slave),
        JUKU_USART_TRANSFER_CYCLES="64",
        JUKU_USART_BYTE_CYCLES="512",
        JUKU_DRAM_RETENTION_CYCLES="350000",
        JUKU_TRACE_IO="1",
    )
    if cpu_fault:
        environment["JUKU_CPU_A12_INCREMENT_FAULT"] = "1"
    if extra_environment is not None:
        environment.update(extra_environment)
    stderr_path = case / "cosim.stderr"
    with (case / "cosim.stdout").open("wb") as stdout, stderr_path.open("wb") as stderr:
        cosim = subprocess.Popen(
            [str(trace), str(rom), "5000000000"],
            cwd=case,
            env=environment,
            stdout=stdout,
            stderr=stderr,
        )
    try:
        command = [
            sys.executable,
            str(BATCH),
            "--fd",
            str(master),
            "--rom",
            "t35",
            "--timeout",
            "20",
            "--banner-timeout",
            "20",
            "--loader-timeout",
            "4",
            "--loader-guard-ms",
            "0",
            "--no-retention-sweep",
            "--log-dir",
            str(logs),
        ]
        if ram_lanes:
            command.extend(("--only-ram-lanes", "--ram-lane-hold-ms", "0"))
        else:
            command.extend(
                (
                    "--only-probe",
                    "cpu-increment-registers",
                    "--refresh-wrapper-address",
                    wrapper_address,
                )
            )
            if direct:
                command.extend(("--direct-probe", "cpu-increment-registers"))
        completed = subprocess.run(
            command,
            cwd=ROOT,
            pass_fds=(master,),
            text=True,
            capture_output=True,
            timeout=180,
            check=False,
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
        fail(f"{label}: expected one summary, got {len(summaries)}")
    return completed, json.loads(summaries[0].read_text()), stderr_path.read_text()


def final_frame_is_run_ack(summary: dict[str, object]) -> bool:
    frames = summary.get("frames")
    if not isinstance(frames, list) or not frames:
        return False
    payload = frames[-1].get("payload_hex")
    return (
        frames[-1].get("type") == "0xB0"
        and isinstance(payload, str)
        and payload.startswith("0400280A")
    )


def main() -> int:
    if len(sys.argv) != 3:
        fail("usage: test.py /path/to/trace diag-d0-refresh.bin")
    trace, rom = (Path(value).resolve() for value in sys.argv[1:])
    if not trace.is_file() or not rom.is_file():
        fail("trace or T35 ROM is missing")

    with tempfile.TemporaryDirectory(prefix="jukuravi-t35-wrapper-a12-") as name:
        root = Path(name)

        clean, clean_summary, _ = run_case(
            trace, rom, root, "clean-7f00", "7F00", cpu_fault=False
        )
        if clean.returncode:
            fail(f"clean 7F00 wrapper failed:\n{clean.stdout}{clean.stderr}")
        clean_results = clean_summary.get("batch", {}).get("results", [])
        clean_probe = next(
            (
                item
                for item in clean_results
                if item.get("name") == "cpu-increment-registers"
            ),
            None,
        )
        if not isinstance(clean_probe, dict) or clean_probe.get("verdict") != "pass":
            fail(f"clean 7F00 probe differs: {clean_probe!r}")

        cpu_fault, fault_summary, fault_trace = run_case(
            trace, rom, root, "fault-7f00", "7F00", cpu_fault=True
        )
        if cpu_fault.returncode == 0 or final_frame_is_run_ack(fault_summary):
            fail(
                "exact CPU fault unexpectedly reached the 7F00 RUN: "
                f"rc={cpu_fault.returncode} "
                f"last={fault_summary.get('frames', [])[-1:]}"
            )
        if "[CPU] A12 increment-retention fault enabled" not in fault_trace:
            fail("faulted 7F00 cosim injection was not active")
        frames = fault_summary.get("frames", [])
        if (
            not frames
            or frames[-1].get("payload_hex") != "0000230000085432380055AAC6C7"
        ):
            fail(f"exact CPU fault did not stop after READY: {frames[-1:]}")

        fetch, fetch_summary, fetch_trace = run_case(
            trace,
            rom,
            root,
            "fetch-7f02",
            "7F00",
            cpu_fault=False,
            extra_environment={"JUKU_EXEC_BYTE_FAULT": "7F02:00"},
        )
        if fetch.returncode == 0 or not final_frame_is_run_ack(fetch_summary):
            fail(
                "7F02 instruction-fetch fault did not reproduce "
                f"RUN-ACK/no-RETURN: rc={fetch.returncode} "
                f"last={fetch_summary.get('frames', [])[-1:]}"
            )
        expected_tone = (
            "OUT port=0x1B value=0x76",
            "OUT port=0x19 value=0x40",
            "OUT port=0x19 value=0x1F",
        )
        if any(marker not in fetch_trace for marker in expected_tone):
            fail("7F02 fetch fault did not reach the continuous low CPU tone")

        low, low_summary, _ = run_case(
            trace, rom, root, "clean-6f00", "6F00", cpu_fault=False
        )
        if low.returncode:
            fail(f"clean 6F00 wrapper failed:\n{low.stdout}{low.stderr}")
        low_results = low_summary.get("batch", {}).get("results", [])
        low_probe = next(
            (
                item
                for item in low_results
                if item.get("name") == "cpu-increment-registers"
            ),
            None,
        )
        if (
            not isinstance(low_probe, dict)
            or low_probe.get("verdict") != "pass"
            or low_probe.get("operation", {}).get("refresh_wrapper", {}).get("address")
            != "0x6F00"
        ):
            fail(f"clean 6F00 wrapper differs: {low_probe!r}")

        direct, direct_summary, _ = run_case(
            trace,
            rom,
            root,
            "clean-direct-4000",
            "6F00",
            cpu_fault=False,
            direct=True,
        )
        if direct.returncode:
            fail(f"clean direct 4000 probe failed:\n{direct.stdout}{direct.stderr}")
        direct_results = direct_summary.get("batch", {}).get("results", [])
        direct_probe = next(
            (
                item
                for item in direct_results
                if item.get("name") == "cpu-increment-registers"
            ),
            None,
        )
        if (
            not isinstance(direct_probe, dict)
            or direct_probe.get("verdict") != "pass"
            or "refresh_wrapper" in direct_probe.get("operation", {})
            or direct_summary.get("batch", {}).get("direct_probes")
            != ["cpu-increment-registers"]
        ):
            fail(f"clean direct 4000 probe differs: {direct_probe!r}")

        lanes, lanes_summary, _ = run_case(
            trace,
            rom,
            root,
            "clean-ram-lanes-4d00",
            "6F00",
            cpu_fault=False,
            ram_lanes=True,
        )
        if lanes.returncode:
            fail(f"clean RAM lane test failed:\n{lanes.stdout}{lanes.stderr}")
        lane_results = lanes_summary.get("batch", {}).get("results", [])
        lane_result = next(
            (item for item in lane_results if item.get("name") == "ram-lanes"),
            None,
        )
        if (
            not isinstance(lane_result, dict)
            or lane_result.get("verdict") != "pass"
            or lane_result.get("address") != "0x4D00"
            or lane_result.get("candidate_packages") != []
            or len(lane_result.get("patterns", [])) != 4
        ):
            fail(f"clean RAM lane result differs: {lane_result!r}")

    print(
        "JUKURAVI-T35-WRAPPER-A12: PASS "
        "(exact CS00015 CPU fault dies in T35 refresh before RUN; "
        "7F02 fetch corruption matches RUN-ACK/no-RETURN plus low tone; "
        "clean 7F00/6F00 wrappers, direct 4000, and RAM lanes pass)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
