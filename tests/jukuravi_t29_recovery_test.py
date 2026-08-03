#!/usr/bin/env python3
"""Exercise exact T29 markers plus the retained T28 CALL/RET contract."""

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
import build_d0_host_recover as firmware  # noqa: E402

TEST_LABEL = "JUKURAVI-T29-RECOVERY"
PROGRESS_MARKERS = (0xE0, 0xE1, 0xE2, 0xE3)
SUCCESS_DETAIL = (
    "E0/E1/E2/E3 progress; one-shot TxRDY recovery; CALL/RET; A/RAM result"
)


def fail(message: str) -> None:
    print(f"{TEST_LABEL}: FAIL: {message}", file=sys.stderr)
    raise SystemExit(1)


def main() -> int:
    if len(sys.argv) != 3:
        fail("usage: test.py /path/to/trace diag-d0-host-recover.bin")
    trace, rom_arg = (Path(value).resolve() for value in sys.argv[1:])
    image, metadata = firmware.build()
    if not trace.is_file() or rom_arg.read_bytes() != image:
        fail("trace or exact T29 image differs")

    with tempfile.TemporaryDirectory(prefix="jukuravi-t29-") as temp_name:
        root_temp = Path(temp_name)
        for case, fault in (
            ("normal", None),
            ("tx-recovery", "tx_not_ready_once_after:64"),
        ):
            temp = root_temp / case
            temp.mkdir()
            rom = temp / "t29.bin"
            logs = temp / "logs"
            rom.write_bytes(image)
            master, slave = pty.openpty()
            tty.setraw(slave)
            environment = os.environ.copy()
            environment.update(
                JUKU_USART_PTY=os.ttyname(slave),
                JUKU_USART_TRANSFER_CYCLES="64",
                JUKU_USART_BYTE_CYCLES="512",
            )
            if fault is not None:
                environment["JUKU_USART_FAULT"] = fault
            with (temp / "cosim.stdout").open("wb") as stdout, (
                temp / "cosim.stderr"
            ).open("wb") as stderr:
                cosim = subprocess.Popen(
                    [str(trace), str(rom), "2500000000"],
                    cwd=temp,
                    env=environment,
                    stdout=stdout,
                    stderr=stderr,
                )
            try:
                result = subprocess.run(
                    [
                        sys.executable,
                        str(HOST),
                        "--fd", str(master),
                        "--timeout", "60",
                        "--loader-timeout", "30",
                        "--loader-guard-ms", "0",
                        "--expect-rom-version", f"{firmware.ROM_VERSION:02X}",
                        "--expect-crc16", f"{int(metadata['checksum']):04X}",
                        "--load", str(FIRMWARE / "return-4000.bin"),
                        "--load-address", "4000",
                        "--run-address", "4000",
                        "--run-mode", "call",
                        "--result-address", "4100",
                        "--result-length", "8",
                        "--log-dir", str(logs),
                    ],
                    cwd=ROOT,
                    pass_fds=(master,),
                    text=True,
                    capture_output=True,
                    timeout=120,
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

            if result.returncode:
                raw_files = list(logs.glob("*.rx.bin"))
                raw_hex = raw_files[0].read_bytes().hex(" ") if raw_files else "<none>"
                cosim_diagnostic = (temp / "cosim.stderr").read_text()
                fail(
                    f"{case} real CLI failed:\n{result.stdout}{result.stderr}"
                    f"cosim stderr:\n{cosim_diagnostic}\nraw RX: {raw_hex}"
                )
            summary = json.loads(next(logs.glob("*.json")).read_text())
            run = summary.get("loader", {}).get("run")
            if (
                not isinstance(run, dict)
                or run.get("returned") is not True
                or run.get("return_a") != "0x42"
                or run.get("result", {}).get("hex") != "5432385245542100"
            ):
                fail(f"{case} CALL/RET evidence differs: {run!r}")
            raw = next(logs.glob("*.rx.bin")).read_bytes()
            positions = [raw.find(bytes((marker,))) for marker in PROGRESS_MARKERS]
            if positions and (positions != sorted(positions) or positions[0] < 0):
                fail(f"{case} progress markers absent/out of order: {positions!r}")
            if fault is not None:
                cosim_stderr = (temp / "cosim.stderr").read_text()
                if "injected one-shot TxRDY stall after byte=64" not in cosim_stderr or (
                    "one-shot TxRDY stall cleared by 8251 reset" not in cosim_stderr
                ):
                    fail(f"{case} did not inject and recover the TxRDY stall")

    print(
        f"{TEST_LABEL}: PASS ({SUCCESS_DETAIL})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
