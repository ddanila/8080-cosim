#!/usr/bin/env python3
"""Distinguish correct T31 upper-ROM access from an A12-low alias."""

from __future__ import annotations

import json
import os
import pty
import subprocess
import sys
import tempfile
import time
import tty
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HOST = ROOT / "spinoffs" / "jukuravi" / "host.py"
FIRMWARE = ROOT / "spinoffs" / "jukuravi" / "firmware"
READ_LOW = FIRMWARE / "rom-read-0017.bin"
READ_HIGH = FIRMWARE / "rom-read-1017.bin"
READ_UPPER = FIRMWARE / "rom-read-upper-4000.bin"
REENTER = FIRMWARE / "rom-reenter-4000.bin"
EXEC_HIGH = FIRMWARE / "rom-exec-106f.bin"
sys.path[:0] = [str(FIRMWARE), str(FIRMWARE.parent)]
import build_d0_low4k as firmware  # noqa: E402


def fail(message: str) -> None:
    print(f"JUKURAVI-T31-A12: FAIL: {message}", file=sys.stderr)
    raise SystemExit(1)


def run_host(master: int, arguments: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            str(HOST),
            "--fd", str(master),
            "--loader-timeout", "30",
            "--loader-guard-ms", "0",
            "--loader-votes", "1",
            *arguments,
        ],
        cwd=ROOT,
        pass_fds=(master,),
        text=True,
        capture_output=True,
        timeout=120,
    )


def summary(logs: Path) -> dict[str, object]:
    return json.loads(next(logs.glob("*.json")).read_text())


def check_sample(logs: Path, target: int, expected: int) -> None:
    run = summary(logs).get("loader", {}).get("run")
    wanted = (
        b"A12S"
        + target.to_bytes(2, "big")
        + bytes((expected, 16, 0xA5))
        + bytes((expected,)) * 16
    ).hex().upper()
    if (
        not isinstance(run, dict)
        or run.get("returned") is not True
        or run.get("return_a") != "0x00"
        or run.get("result", {}).get("hex") != wanted
    ):
        fail(f"ROM sample at {target:04X} differs: {run!r}")


def check_upper_samples(logs: Path) -> None:
    expected = bytearray(b"U12D\x04\x10\xA5\x00")
    for target, value in ((0x100C, 0xB1), (0x106F, 0xC3),
                          (0x1070, 0x0C), (0x1071, 0x0A)):
        expected.extend(target.to_bytes(2, "big"))
        expected.append(value)
        expected.extend(bytes((value,)) * 16)
    run = summary(logs).get("loader", {}).get("run")
    if (
        not isinstance(run, dict)
        or run.get("returned") is not True
        or run.get("return_a") != "0x00"
        or run.get("result", {}).get("hex") != expected.hex().upper()
    ):
        fail(f"focused upper-ROM samples differ: {run!r}")


def start_cosim(
    trace: Path, rom: Path, temp: Path
) -> tuple[subprocess.Popen[bytes], int, int]:
    master, slave = pty.openpty()
    tty.setraw(slave)
    environment = os.environ.copy()
    environment.update(
        JUKU_USART_PTY=os.ttyname(slave),
        JUKU_USART_TRANSFER_CYCLES="64",
        JUKU_USART_BYTE_CYCLES="512",
        JUKU_PIT_FAULT="14:00:80",
        JUKU_TRACE_IO="1",
    )
    stdout = (temp / "cosim.stdout").open("wb")
    stderr = (temp / "cosim.stderr").open("wb")
    process = subprocess.Popen(
        [str(trace), str(rom), "5000000000"],
        cwd=temp,
        env=environment,
        stdout=stdout,
        stderr=stderr,
    )
    stdout.close()
    stderr.close()
    return process, master, slave


def stop_cosim(process: subprocess.Popen[bytes], master: int, slave: int) -> None:
    if process.poll() is None:
        process.terminate()
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait()
    os.close(master)
    os.close(slave)


def exact_case(trace: Path, rom: Path, temp: Path, metadata: dict[str, object]) -> None:
    process, master, slave = start_cosim(trace, rom, temp)
    low_logs = temp / "read-low"
    high_logs = temp / "read-high"
    upper_logs = temp / "read-upper"
    reenter_logs = temp / "reenter"
    reenter_attach_logs = temp / "attach-after-reenter"
    jump_logs = temp / "exec-high"
    attach_logs = temp / "attach-after-exec"
    try:
        low = run_host(
            master,
            [
                "--timeout", "60",
                "--expect-rom-version", f"{firmware.ROM_VERSION:02X}",
                "--expect-crc16", f"{int(metadata['checksum']):04X}",
                "--load", str(READ_LOW),
                "--load-address", "4000",
                "--run-address", "4000",
                "--run-mode", "call",
                "--result-address", "4100",
                "--result-length", "25",
                "--log-dir", str(low_logs),
            ],
        )
        if low.returncode:
            fail(f"lower-ROM probe failed:\n{low.stdout}{low.stderr}")
        check_sample(low_logs, 0x0017, 0x01)

        high = run_host(
            master,
            [
                "--attach-loader",
                "--load", str(READ_HIGH),
                "--load-address", "4000",
                "--run-address", "4000",
                "--run-mode", "call",
                "--result-address", "4100",
                "--result-length", "25",
                "--log-dir", str(high_logs),
            ],
        )
        if high.returncode:
            fail(f"upper-ROM data probe failed:\n{high.stdout}{high.stderr}")
        check_sample(high_logs, 0x1017, 0xFE)

        upper = run_host(
            master,
            [
                "--attach-loader",
                "--load", str(READ_UPPER),
                "--load-address", "4000",
                "--run-address", "4000",
                "--run-mode", "call",
                "--result-address", "4200",
                "--result-length", "84",
                "--log-dir", str(upper_logs),
            ],
        )
        if upper.returncode:
            fail(f"focused upper-ROM probe failed:\n{upper.stdout}{upper.stderr}")
        check_upper_samples(upper_logs)

        reenter = run_host(
            master,
            [
                "--attach-loader",
                "--load", str(REENTER),
                "--load-address", "4000",
                "--run-address", "4000",
                "--run-mode", "jump",
                "--log-dir", str(reenter_logs),
            ],
        )
        if reenter.returncode:
            fail(f"RAM loader re-entry control failed:\n{reenter.stdout}{reenter.stderr}")
        reentered = run_host(
            master,
            [
                "--attach-loader",
                "--probe-loader",
                "--log-dir", str(reenter_attach_logs),
            ],
        )
        if reentered.returncode:
            fail(
                "T31 loader did not reappear after direct RAM re-entry:\n"
                f"{reentered.stdout}{reentered.stderr}"
            )

        jump = run_host(
            master,
            [
                "--attach-loader",
                "--load", str(EXEC_HIGH),
                "--load-address", "4000",
                "--run-address", "4000",
                "--run-mode", "jump",
                "--log-dir", str(jump_logs),
            ],
        )
        if jump.returncode:
            fail(f"upper-ROM execution probe failed:\n{jump.stdout}{jump.stderr}")

        attached = run_host(
            master,
            [
                "--attach-loader",
                "--probe-loader",
                "--log-dir", str(attach_logs),
            ],
        )
        if attached.returncode:
            fail(
                "T31 loader did not reappear after executing 106Fh:\n"
                f"{attached.stdout}{attached.stderr}"
            )
    finally:
        stop_cosim(process, master, slave)


def alias_case(trace: Path, image: bytes, temp: Path, metadata: dict[str, object]) -> None:
    aliased = bytearray(image)
    aliased[0x1000:0x2000] = image[0x0000:0x1000]
    rom = temp / "t31-a12-low.bin"
    rom.write_bytes(aliased)
    process, master, slave = start_cosim(trace, rom, temp)
    logs = temp / "exec-high"
    try:
        jumped = run_host(
            master,
            [
                "--timeout", "60",
                "--expect-rom-version", f"{firmware.ROM_VERSION:02X}",
                "--expect-crc16", f"{int(metadata['checksum']):04X}",
                "--load", str(EXEC_HIGH),
                "--load-address", "4000",
                "--run-address", "4000",
                "--run-mode", "jump",
                "--log-dir", str(logs),
            ],
        )
        if jumped.returncode:
            fail(f"A12-low execution setup failed:\n{jumped.stdout}{jumped.stderr}")
        deadline = time.monotonic() + 5
        while process.poll() is None and time.monotonic() < deadline:
            time.sleep(0.01)
        if process.poll() is None:
            fail("A12-low execution did not reach the expected HLT")
    finally:
        stop_cosim(process, master, slave)

    diagnostic = (temp / "cosim.stderr").read_text()
    expected = (
        "[IOSEQ] OUT port=0x1B value=0x76",
        "[IOSEQ] OUT port=0x19 value=0x40",
        "[IOSEQ] OUT port=0x19 value=0x1F",
        "stopped pc=0x066C",
        "halted=1",
    )
    missing = [marker for marker in expected if marker not in diagnostic]
    if missing:
        fail(f"A12-low failure signature differs; missing {missing!r}")


def main() -> int:
    if len(sys.argv) != 3:
        fail("usage: test.py /path/to/trace diag-d0-low4k.bin")
    trace, rom = (Path(value).resolve() for value in sys.argv[1:])
    image, metadata = firmware.build()
    if not trace.is_file() or rom.read_bytes() != image:
        fail("trace or exact T31 image differs")
    if image[0x006F:0x0072] != bytes.fromhex("FA 5F 06"):
        fail("lower alias target differs")
    if image[0x106F:0x1072] != bytes.fromhex("C3 0C 0A"):
        fail("upper loader trampoline differs")
    if EXEC_HIGH.read_bytes() != bytes.fromhex("C3 6F 10"):
        fail("RAM execution trampoline differs")
    if REENTER.read_bytes() != bytes.fromhex("C3 0C 0A"):
        fail("RAM loader re-entry control differs")

    with tempfile.TemporaryDirectory(prefix="jukuravi-t31-a12-") as temp_name:
        root = Path(temp_name)
        exact = root / "exact"
        alias = root / "alias"
        exact.mkdir()
        alias.mkdir()
        exact_case(trace, rom, exact, metadata)
        alias_case(trace, image, alias, metadata)

    print(
        "JUKURAVI-T31-A12: PASS "
        "(lower+upper data; upper instruction fetch; A12-low => 250 Hz CPU-fail tone)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
