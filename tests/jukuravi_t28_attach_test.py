#!/usr/bin/env python3
"""Prove no-RESET T28 reattach and exact host-side upload resume."""

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
HOST = ROOT / "spinoffs" / "jukuravi" / "host.py"
FIRMWARE = ROOT / "spinoffs" / "jukuravi" / "firmware"
sys.path[:0] = [str(FIRMWARE), str(FIRMWARE.parent)]
import build_d0_buffer_verified as firmware  # noqa: E402


def fail(message: str) -> None:
    print(f"JUKURAVI-T28-ATTACH: FAIL: {message}", file=sys.stderr)
    raise SystemExit(1)


def run_host(master: int, arguments: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(HOST), "--fd", str(master), *arguments],
        cwd=ROOT,
        pass_fds=(master,),
        text=True,
        capture_output=True,
        timeout=120,
    )


def main() -> int:
    if len(sys.argv) != 3:
        fail("usage: test.py /path/to/trace diag-d0-buffer-verified.bin")
    trace, rom_arg = (Path(value).resolve() for value in sys.argv[1:])
    image, metadata = firmware.build()
    if not trace.is_file() or rom_arg.read_bytes() != image:
        fail("trace or exact T28 image differs")

    with tempfile.TemporaryDirectory(prefix="jukuravi-t28-attach-") as temp_name:
        temp = Path(temp_name)
        rom = temp / "t28.bin"
        first_logs = temp / "first"
        attach_logs = temp / "attach"
        resident_logs = temp / "resident"
        payload = FIRMWARE / "return-4000.bin"
        rom.write_bytes(image)
        master, slave = pty.openpty()
        tty.setraw(slave)
        environment = os.environ.copy()
        environment.update(
            JUKU_USART_PTY=os.ttyname(slave),
            JUKU_USART_TRANSFER_CYCLES="64",
            JUKU_USART_BYTE_CYCLES="512",
        )
        with (temp / "cosim.stdout").open("wb") as stdout, (
            temp / "cosim.stderr"
        ).open("wb") as stderr:
            cosim = subprocess.Popen(
                [str(trace), str(rom), "5000000000"],
                cwd=temp,
                env=environment,
                stdout=stdout,
                stderr=stderr,
            )
        try:
            first = run_host(
                master,
                [
                    "--timeout", "60",
                    "--loader-timeout", "30",
                    "--loader-guard-ms", "0",
                    "--loader-votes", "3",
                    "--loader-benchmark-passes", "3",
                    "--no-loader-readback",
                    "--expect-rom-version", f"{firmware.ROM_VERSION:02X}",
                    "--expect-crc16", f"{int(metadata['checksum']):04X}",
                    "--load", str(payload),
                    "--load-only",
                    "--log-dir", str(first_logs),
                ],
            )
            if first.returncode:
                fail(f"initial load failed:\n{first.stdout}{first.stderr}")

            attached = run_host(
                master,
                [
                    "--attach-loader",
                    "--loader-timeout", "30",
                    "--loader-guard-ms", "0",
                    "--loader-resume",
                    "--load", str(payload),
                    "--load-only",
                    "--log-dir", str(attach_logs),
                ],
            )
            if attached.returncode:
                fail(f"no-RESET resume failed:\n{attached.stdout}{attached.stderr}")

            resident = run_host(
                master,
                [
                    "--attach-loader",
                    "--probe-loader",
                    "--run-address", "4000",
                    "--run-mode", "call",
                    "--result-address", "4100",
                    "--result-length", "8",
                    "--loader-timeout", "30",
                    "--loader-guard-ms", "0",
                    "--log-dir", str(resident_logs),
                ],
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

        first_summary = json.loads(next(first_logs.glob("*.json")).read_text())
        benchmark = first_summary.get("loader", {}).get("benchmark")
        if (
            not isinstance(benchmark, dict)
            or benchmark.get("requested_passes") != 3
            or benchmark.get("completed_passes") != 3
            or benchmark.get("verification") != "crc16"
            or benchmark.get("load_retries") != 0
            or benchmark.get("verify_retries") != 0
            or benchmark.get("parser_store_retries") != 0
            or benchmark.get("verified_payload_bytes") != 87
            or benchmark.get("payload_bytes_per_second", 0) <= 0
            or len(benchmark.get("passes", [])) != 3
            or any(
                item.get("load_attempts") != 1
                or item.get("verify_attempts") != 1
                or not isinstance(item.get("seconds"), (int, float))
                for item in benchmark.get("passes", [])
            )
        ):
            fail(f"repeated LOAD+CRC benchmark evidence differs: {benchmark!r}")

        summary = json.loads(next(attach_logs.glob("*.json")).read_text())
        loader = summary.get("loader")
        if not isinstance(loader, dict) or loader.get("attached") is not True:
            fail(f"attach evidence is absent: {loader!r}")
        attach = loader.get("attach")
        if not isinstance(attach, dict) or attach.get("idle_requests", 0) < 9:
            fail(f"idle reset/RESYNC evidence differs: {attach!r}")
        chunks = loader.get("chunks")
        if not isinstance(chunks, list) or not chunks or any(
            chunk.get("status") != "already_present"
            or chunk.get("skipped") is not True
            or chunk.get("verified") is not True
            for chunk in chunks
        ):
            fail(f"exact resume did not skip retained RAM: {chunks!r}")
        if summary.get("nano_control", {}).get("dtr_sequences_completed") != 0:
            fail("attach evidence unexpectedly contains a reset sequence")

        if resident.returncode:
            fail(f"resident no-RESET call failed:\n{resident.stdout}{resident.stderr}")
        resident_summary = json.loads(next(resident_logs.glob("*.json")).read_text())
        resident_loader = resident_summary.get("loader")
        if not isinstance(resident_loader, dict):
            fail("resident-control evidence is absent")
        run = resident_loader.get("run")
        if (
            not isinstance(run, dict)
            or run.get("returned") is not True
            or run.get("return_a") != "0x42"
            or run.get("result", {}).get("hex") != "5432385245542100"
        ):
            fail(f"resident CALL/RET evidence differs: {run!r}")
        if resident_loader.get("bytes") != 0 or resident_loader.get("chunks") != []:
            fail("resident control unexpectedly uploaded RAM")
        if resident_summary.get("nano_control", {}).get("dtr_sequences_completed") != 0:
            fail("resident control unexpectedly contains a reset sequence")

    print(
        "JUKURAVI-T28-ATTACH: PASS "
        "(repeated LOAD+CRC timing; idle default; RESYNC; exact resume; "
        "resident CALL/RET; no RESET)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
