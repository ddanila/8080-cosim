#!/usr/bin/env python3
"""Prove T36 refresh under deterministic DRAM decay and resident reattach."""

from __future__ import annotations

import hashlib
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
sys.path[:0] = [str(FIRMWARE), str(FIRMWARE.parent)]
import build_d0_clocked_pit as t34  # noqa: E402
import build_d0_refresh as t35  # noqa: E402
import build_d0_row_refresh as t36  # noqa: E402
import protocol  # noqa: E402

RETENTION_CYCLES = 350_000


def fail(message: str) -> None:
    print(f"JUKURAVI-T36-REFRESH: FAIL: {message}", file=sys.stderr)
    raise SystemExit(1)


def start_cosim(
    trace: Path,
    rom: Path,
    temp: Path,
    *,
    extra_environment: dict[str, str] | None = None,
) -> tuple[subprocess.Popen[bytes], int, int, Path]:
    master, slave = pty.openpty()
    tty.setraw(slave)
    stderr_path = temp / "cosim.stderr"
    environment = os.environ.copy()
    environment.update(
        JUKU_USART_PTY=os.ttyname(slave),
        JUKU_USART_TRANSFER_CYCLES="64",
        JUKU_USART_BYTE_CYCLES="512",
        JUKU_DRAM_RETENTION_CYCLES=str(RETENTION_CYCLES),
        JUKU_DRAM_RETENTION_ARM_PC="07A9",
    )
    if extra_environment is not None:
        environment.update(extra_environment)
    with (temp / "cosim.stdout").open("wb") as stdout, stderr_path.open("wb") as stderr:
        cosim = subprocess.Popen(
            [str(trace), str(rom), "5000000000"],
            cwd=temp,
            env=environment,
            stdout=stdout,
            stderr=stderr,
        )
    return cosim, master, slave, stderr_path


def stop_cosim(cosim: subprocess.Popen[bytes], master: int, slave: int) -> None:
    cosim.terminate()
    try:
        cosim.wait(timeout=5)
    except subprocess.TimeoutExpired:
        cosim.kill()
        cosim.wait()
    os.close(master)
    os.close(slave)


def run_host(
    master: int, arguments: list[str], timeout: float = 120
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(HOST), "--fd", str(master), *arguments],
        cwd=ROOT,
        pass_fds=(master,),
        text=True,
        capture_output=True,
        timeout=timeout,
        check=False,
    )


def verify_contract(image: bytes, metadata: dict[str, object]) -> None:
    if metadata["loader_extension_end"] != 0x0FFD:
        fail("blocking loader core crossed 1000h")
    if metadata["refresh_api"] != protocol.LOADER_V2_REFRESH_API:
        fail("public refresh API address differs")
    if (
        metadata["refresh_rows"] != 128
        or metadata["refresh_row_start"] != 0x00
        or metadata["refresh_base_address"] != 0x4000
        or metadata["refresh_increment_opcode"] != 0x2C
        or metadata["refresh_address_axis"] != "cpu-low-seven-bits"
    ):
        fail("refresh sweep does not cover physical MA0..MA6 rows")
    if not 1.2 < float(metadata["refresh_worst_ms_cs00024"]) < 1.3:
        fail("measured-CS00024 refresh timing budget differs")
    if metadata["loader_boot_votes"] != 1:
        fail("T36 did not remove the seven-vote bootstrap exposure")
    if metadata["loader_capabilities"] != protocol.LOADER_V2_T36_CAPABILITIES:
        fail("T36 refresh capability is absent")
    if (
        metadata["refresh_pre_table_end"] != 0x0800
        or metadata["refresh_handler_start"] < 0x1000
        or metadata["loader_entry"] >= 0x1000
        or metadata["loader_loop"] >= 0x1000
    ):
        fail("T36 low-core/optional-upper layout differs")
    for stem in ("ready", "bad_crc"):
        offset = int(metadata[f"refresh_{stem}_frame_offset"])
        frame = bytes(metadata[f"loader_{stem}_frame"])
        if offset + len(frame) > 0x0800 or image[offset : offset + len(frame)] != frame:
            fail(f"{stem} frame is not protected in low ROM")
    if len(image) != 8192 or bytes(metadata["loader_ready_frame"])[4] != 2:
        fail("T36 image/API identity differs")


def main() -> int:
    if len(sys.argv) != 3:
        fail("usage: test.py /path/to/trace diag-d0-row-refresh.bin")
    trace, rom_arg = (Path(value).resolve() for value in sys.argv[1:])
    image, metadata = t36.build()
    verify_contract(image, metadata)
    if not trace.is_file() or not rom_arg.is_file() or rom_arg.read_bytes() != image:
        fail("trace or exact T36 image differs")

    old_image, old_metadata = t34.build()
    if (
        hashlib.sha256(old_image).hexdigest()
        != ("63f69281e632324083bd5e7040d19a7939936b98a4d5cb245e008ea491d45cb5")
        or old_metadata["checksum"] != 0xA637
    ):
        fail("historical T34 was not preserved byte-exactly")
    old_refresh_image, old_refresh_metadata = t35.build()
    if (
        hashlib.sha256(old_refresh_image).hexdigest()
        != "ceb55556f11318dea5ef8c36b81f931813a139ce6ba6e07b607318571c6e1274"
        or old_refresh_metadata["checksum"] != 0x45C4
    ):
        fail("historical T35 was not preserved byte-exactly")

    with tempfile.TemporaryDirectory(prefix="jukuravi-t36-refresh-") as name:
        temp = Path(name)
        t36_rom = temp / "t36.bin"
        t36_rom.write_bytes(image)
        payload = temp / "long-return.bin"
        refresh_abi_program = bytes.fromhex(
            "01 34 12"  # LXI B,1234h
            "11 78 56"  # LXI D,5678h
            "21 00 00 39"  # LXI H,0 / DAD SP
            "22 00 41"  # SHLD 4100h (SP before)
            "21 BC 9A"  # LXI H,9ABCh
            "CD A9 07"  # CALL public T36 refresh API
            "22 02 41"  # SHLD 4102h
            "60 69 22 04 41"  # BC -> HL -> 4104h
            "62 6B 22 06 41"  # DE -> HL -> 4106h
            "21 00 00 39 22 08 41"  # SP after -> 4108h
            "3E 35 C9"  # returned A=35h / RET
        )
        payload.write_bytes(
            refresh_abi_program
            + (bytes(range(256)) * 5)[: 1025 - len(refresh_abi_program)]
        )
        cold_logs = temp / "cold-logs"
        attach_logs = temp / "attach-logs"
        cosim, master, slave, stderr_path = start_cosim(trace, t36_rom, temp)
        try:
            cold = run_host(
                master,
                [
                    "--timeout",
                    "60",
                    "--loader-timeout",
                    "30",
                    "--loader-guard-ms",
                    "0",
                    "--expect-rom-version",
                    f"{t36.ROM_VERSION:02X}",
                    "--expect-crc16",
                    f"{int(metadata['checksum']):04X}",
                    "--load",
                    str(payload),
                    "--load-address",
                    "4000",
                    "--run-address",
                    "4000",
                    "--run-mode",
                    "call",
                    "--result-address",
                    "4100",
                    "--result-length",
                    "10",
                    "--log-dir",
                    str(cold_logs),
                ],
            )
            if cold.returncode:
                fail(
                    f"T36 decaying-RAM cold run failed:\n{cold.stdout}{cold.stderr}"
                    f"cosim:\n{stderr_path.read_text()}"
                )
            time.sleep(0.2)
            attach = run_host(
                master,
                [
                    "--attach-loader",
                    "--loader-bootstrap-votes",
                    "1",
                    "--probe-loader",
                    "--loader-refresh",
                    "query",
                    "--loader-timeout",
                    "30",
                    "--loader-guard-ms",
                    "0",
                    "--log-dir",
                    str(attach_logs),
                ],
            )
            if attach.returncode:
                fail(
                    f"T36 post-idle attach failed:\n{attach.stdout}{attach.stderr}"
                    f"cosim:\n{stderr_path.read_text()}"
                )
        finally:
            stop_cosim(cosim, master, slave)

        if "observed all 128 refresh rows in " not in stderr_path.read_text():
            fail("retention model did not observe one complete 128-row sweep")

        cold_summary = json.loads(next(cold_logs.glob("*.json")).read_text())
        loader = cold_summary.get("loader")
        if not isinstance(loader, dict) or loader.get("bytes") != 1025:
            fail("long upload evidence is absent")
        chunks = loader.get("chunks")
        if (
            not isinstance(chunks, list)
            or len(chunks) != 33
            or not all(item.get("verified") is True for item in chunks)
        ):
            fail(f"long upload verification differs: {chunks!r}")
        refresh = loader.get("refresh")
        if (
            not isinstance(refresh, dict)
            or refresh.get("enabled") is not True
            or refresh.get("api") != f"0x{protocol.LOADER_V2_REFRESH_API:04X}"
            or refresh.get("rows") != 128
        ):
            fail(f"cold refresh telemetry differs: {refresh!r}")
        run = loader.get("run")
        if not isinstance(run, dict) or run.get("return_a") != "0x35":
            fail(f"public refresh CALL did not return normally: {run!r}")
        result = bytes.fromhex(str(run.get("result", {}).get("hex", "")))
        if (
            len(result) != 10
            or result[:2] != result[8:10]
            or result[2:8] != bytes.fromhex("BC9A34127856")
        ):
            fail(f"public refresh ABI did not preserve SP/BC/DE/HL: {result.hex()}")

        attach_summary = json.loads(next(attach_logs.glob("*.json")).read_text())
        attach_loader = attach_summary.get("loader")
        attach_refresh = (
            None
            if not isinstance(attach_loader, dict)
            else attach_loader.get("refresh")
        )
        if (
            not isinstance(attach_loader, dict)
            or attach_loader.get("attached") is not True
            or not isinstance(attach_refresh, dict)
            or attach_refresh.get("enabled") is not True
        ):
            fail(f"resident refresh/attach evidence differs: {attach_loader!r}")

        for mode, expected_enabled in (
            ("enable", True),
            ("disable", False),
            ("reset-counter", True),
        ):
            mode_temp = temp / mode
            mode_temp.mkdir()
            mode_rom = mode_temp / "t36.bin"
            mode_rom.write_bytes(image)
            mode_logs = mode_temp / "logs"
            mode_cosim, mode_master, mode_slave, _ = start_cosim(
                trace,
                mode_rom,
                mode_temp,
                extra_environment={"JUKU_DRAM_RETENTION_CYCLES": "1000000000"},
            )
            try:
                mode_run = run_host(
                    mode_master,
                    [
                        "--timeout",
                        "60",
                        "--loader-timeout",
                        "30",
                        "--loader-guard-ms",
                        "0",
                        "--expect-rom-version",
                        f"{t36.ROM_VERSION:02X}",
                        "--expect-crc16",
                        f"{int(metadata['checksum']):04X}",
                        "--probe-loader",
                        "--loader-refresh",
                        mode,
                        "--log-dir",
                        str(mode_logs),
                    ],
                )
            finally:
                stop_cosim(mode_cosim, mode_master, mode_slave)
            if mode_run.returncode:
                fail(f"refresh {mode} failed: {mode_run.stdout}{mode_run.stderr}")
            mode_summary = json.loads(next(mode_logs.glob("*.json")).read_text())
            mode_refresh = mode_summary.get("loader", {}).get("refresh")
            if (
                not isinstance(mode_refresh, dict)
                or mode_refresh.get("enabled") is not expected_enabled
                or (
                    mode == "reset-counter"
                    and mode_refresh.get("rx_refresh_calls") != 0
                )
            ):
                fail(f"refresh {mode} telemetry differs: {mode_refresh!r}")

        # A deliberately torn three-byte disable write must leave refresh on,
        # and the host must reject the requested transition rather than
        # claiming that the unsafe mode took effect.
        torn_temp = temp / "torn-disable"
        torn_temp.mkdir()
        torn_rom = torn_temp / "t36.bin"
        torn_rom.write_bytes(image)
        torn_logs = torn_temp / "logs"
        torn_cosim, torn_master, torn_slave, torn_stderr = start_cosim(
            trace,
            torn_rom,
            torn_temp,
            extra_environment={
                "JUKU_DRAM_RETENTION_CYCLES": "1000000000",
                "JUKU_RAM_DROP_WRITE": "C129:A5:1",
            },
        )
        try:
            torn = run_host(
                torn_master,
                [
                    "--timeout",
                    "60",
                    "--loader-timeout",
                    "30",
                    "--loader-guard-ms",
                    "0",
                    "--expect-rom-version",
                    f"{t36.ROM_VERSION:02X}",
                    "--expect-crc16",
                    f"{int(metadata['checksum']):04X}",
                    "--probe-loader",
                    "--loader-refresh",
                    "disable",
                    "--log-dir",
                    str(torn_logs),
                ],
            )
        finally:
            stop_cosim(torn_cosim, torn_master, torn_slave)
        if torn.returncode == 0 or "fail-safe refresh remains on" not in torn.stderr:
            fail(f"torn disable was not rejected safely: {torn.stdout}{torn.stderr}")
        if "dropped write address=0xC129 value=0xA5" not in torn_stderr.read_text():
            fail("torn-disable fault injection did not fire")

        # The direct negative control uses the exact physical T35 artifact and
        # arms decay at the same public refresh entry as T36. T35 repeatedly
        # touches only physical row 00; it must decay while T36 above survives.
        old_temp = temp / "t35-control"
        old_temp.mkdir()
        old_rom = old_temp / "t35.bin"
        old_rom.write_bytes(old_refresh_image)
        old_logs = old_temp / "logs"
        old_cosim, old_master, old_slave, old_stderr = start_cosim(
            trace,
            old_rom,
            old_temp,
        )
        try:
            old = run_host(
                old_master,
                [
                    "--timeout",
                    "30",
                    "--loader-timeout",
                    "12",
                    "--loader-guard-ms",
                    "0",
                    "--expect-rom-version",
                    f"{t35.ROM_VERSION:02X}",
                    "--expect-crc16",
                    f"{int(old_refresh_metadata['checksum']):04X}",
                    "--probe-loader",
                    "--log-dir",
                    str(old_logs),
                ],
                timeout=90,
            )
        finally:
            stop_cosim(old_cosim, old_master, old_slave)
        if old.returncode == 0:
            fail("retention fault was too weak: exact T35 unexpectedly passed")
        old_trace = old_stderr.read_text()
        if (
            "[DRAM] retention armed at pc=0x07A9" not in old_trace
            or "[DRAM] decayed refresh row=" not in old_trace
            or "observed all 128 refresh rows" in old_trace
        ):
            fail("T35 discriminator did not reproduce one-row refresh decay")

    print(
        "JUKURAVI-T36-REFRESH: PASS "
        "(physical MA0..MA6 128 rows/1.234ms; fail-safe policy; "
        "1025-byte upload; idle reattach; "
        "torn-disable rejection; exact T35 one-row decay discriminator; "
        "exact T34/T35 preserved)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
