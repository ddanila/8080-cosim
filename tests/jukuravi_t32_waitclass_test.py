#!/usr/bin/env python3
"""Execute every T32 upper-ROM wait-class trampoline and recover the loader."""

from __future__ import annotations

import hashlib
import json
import os
import pty
import subprocess
import sys
import tempfile
import tty
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HOST = ROOT / "spinoffs" / "jukuravi" / "host.py"
FIRMWARE = ROOT / "spinoffs" / "jukuravi" / "firmware"
sys.path[:0] = [str(FIRMWARE), str(FIRMWARE.parent), str(ROOT / "scripts")]
import build_d0_waitclass as firmware  # noqa: E402
import report_d2_ready_cycle_analysis as d2  # noqa: E402


def fail(message: str) -> None:
    print(f"JUKURAVI-T32-WAITCLASS: FAIL: {message}", file=sys.stderr)
    raise SystemExit(1)


def run_host(master: int, arguments: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            str(HOST),
            "--fd", str(master),
            "--loader-timeout", os.environ.get("JUKU_T32_LOADER_TIMEOUT", "30"),
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


def main() -> int:
    if len(sys.argv) != 3:
        fail("usage: test.py /path/to/trace diag-d0-waitclass.bin")
    trace, rom = (Path(value).resolve() for value in sys.argv[1:])
    image, metadata = firmware.build()
    if not trace.is_file() or rom.read_bytes() != image:
        fail("trace or exact T32 image differs")

    raw = d2.RAW.read_bytes()
    if hashlib.sha256(raw).hexdigest() != d2.EXPECTED_SHA256:
        fail("validated D2 image differs")
    classes = {
        address: d2.wait_class(raw, address) for address in firmware.TRAMPOLINES
    }
    if Counter(classes.values()) != Counter(
        {"CAS-gated": 2, "no wait": 2, "always wait": 4}
    ):
        fail(f"wait-class matrix differs: {classes!r}")
    for address in firmware.TRAMPOLINES:
        program = firmware.trampoline(address)
        if image[address:address + len(program)] != program:
            fail(f"trampoline bytes differ at {address:04X}h")

    target_filter = os.environ.get("JUKU_T32_TARGET")
    if target_filter:
        try:
            target = int(target_filter, 16)
        except ValueError:
            fail(f"invalid JUKU_T32_TARGET={target_filter!r}")
        if target not in classes:
            fail(f"JUKU_T32_TARGET={target:04X}h is not a T32 entry")
        classes = {target: classes[target]}
    jump_address_text = os.environ.get("JUKU_T32_JUMP_ADDRESS", "4000")
    try:
        jump_address = int(jump_address_text, 16)
    except ValueError:
        fail(f"invalid JUKU_T32_JUMP_ADDRESS={jump_address_text!r}")
    if not 0x4000 <= jump_address <= 0xBFFD:
        fail(f"JUKU_T32_JUMP_ADDRESS={jump_address:04X}h is outside RAM")
    premarker_text = os.environ.get("JUKU_T32_PREMARKER")
    premarker = None
    if premarker_text:
        try:
            premarker = int(premarker_text, 16)
        except ValueError:
            fail(f"invalid JUKU_T32_PREMARKER={premarker_text!r}")
        if not 0 <= premarker <= 0xFF:
            fail(f"JUKU_T32_PREMARKER={premarker:02X}h is not one byte")
    expect_loader_loss = os.environ.get("JUKU_T32_EXPECT_LOADER_LOSS") not in (
        None, "", "0"
    )
    if expect_loader_loss and len(classes) != 1:
        fail("JUKU_T32_EXPECT_LOADER_LOSS requires one JUKU_T32_TARGET")

    with tempfile.TemporaryDirectory(prefix="jukuravi-t32-waitclass-") as name:
        temp = Path(name)
        master, slave = pty.openpty()
        tty.setraw(slave)
        environment = os.environ.copy()
        environment.update(
            JUKU_USART_PTY=os.ttyname(slave),
            JUKU_USART_TRANSFER_CYCLES="64",
            JUKU_USART_BYTE_CYCLES="512",
            JUKU_PIT_FAULT="14:00:80",
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
        try:
            for index, (target, expected_class) in enumerate(classes.items()):
                probe = temp / f"exec-{target:04x}.bin"
                probe.write_bytes(
                    bytes((0xC3, target & 0xFF, target >> 8))
                    if premarker is None
                    else bytes(
                        (
                            0x3E, premarker,
                            0x32, firmware.RESULT_ADDRESS & 0xFF,
                            firmware.RESULT_ADDRESS >> 8,
                            0xC3, target & 0xFF, target >> 8,
                        )
                    )
                )
                logs = temp / f"exec-{target:04x}"
                arguments = (
                    [
                        "--timeout", "60",
                        "--expect-rom-version", f"{firmware.ROM_VERSION:02X}",
                        "--expect-crc16", f"{int(metadata['checksum']):04X}",
                    ]
                    if index == 0
                    else ["--attach-loader"]
                )
                arguments.extend(
                    [
                        "--load", str(probe),
                        "--load-address", f"{jump_address:04X}",
                        "--run-address", f"{jump_address:04X}",
                        "--run-mode", "jump",
                        "--log-dir", str(logs),
                    ]
                )
                jumped = run_host(master, arguments)
                if jumped.returncode:
                    fail(
                        f"{target:04X}h {expected_class} jump failed:\n"
                        f"{jumped.stdout}{jumped.stderr}"
                    )
                attached = run_host(
                    master,
                    [
                        "--attach-loader",
                        "--probe-loader",
                        "--read-address", f"{firmware.RESULT_ADDRESS:04X}",
                        "--read-length", "1",
                        "--log-dir", str(temp / f"attach-{target:04x}"),
                    ],
                )
                if attached.returncode:
                    if expect_loader_loss:
                        print(
                            "JUKURAVI-T32-WAITCLASS: PASS "
                            f"({target:04X}h loader loss reproduced)"
                        )
                        continue
                    fail(
                        f"loader did not recover after {target:04X}h "
                        f"{expected_class}:\n{attached.stdout}{attached.stderr}"
                    )
                summary = json.loads(next(logs.glob("*.json")).read_text())
                if summary.get("loader", {}).get("run", {}).get("mode") != "jump":
                    fail(f"{target:04X}h run evidence differs")
                attach_logs = temp / f"attach-{target:04x}"
                attach_summary = json.loads(next(attach_logs.glob("*.json")).read_text())
                observed = attach_summary.get("loader", {}).get("control_read", {}).get("hex")
                expected = os.environ.get(
                    "JUKU_T32_EXPECT_MARKER", f"{target >> 8:02X}"
                ).upper()
                if observed != expected:
                    fail(
                        f"{target:04X}h marker differs: expected {expected}, "
                        f"observed {observed!r}"
                    )
        finally:
            if process.poll() is None:
                process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
            os.close(master)
            os.close(slave)

    if not expect_loader_loss:
        print(
            "JUKURAVI-T32-WAITCLASS: PASS "
            f"({len(classes)} upper entr{'y' if len(classes) == 1 else 'ies'}; "
            "loader recovered; expected markers verified)"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
