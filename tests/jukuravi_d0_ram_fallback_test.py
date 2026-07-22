#!/usr/bin/env python3
"""Prove Jukuravi's no-ACK fixed-window RAM fallback and beep verdicts."""

from __future__ import annotations

import errno
import os
import pty
import select
import subprocess
import sys
import tempfile
import time
import tty
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "tests"), str(ROOT / "spinoffs" / "jukuravi"),
                str(ROOT / "spinoffs" / "jukuravi" / "firmware")]
import build_d0_ram_fallback as firmware  # noqa: E402
import jukuravi_d0_ram_test as ram_test  # noqa: E402
import protocol  # noqa: E402


ALIVE_TONE_IO = [(0x1B, 0x76), (0x19, 0xD0), (0x19, 0x07),
                 (0x1B, 0x50), (0x19, 0x01)]
BAUD_CONTROL_IO = [(0x1B, 0x34)]
SERIAL_DEAD_MARK_IO = [(0x1B, 0x76), (0x19, 0x80), (0x19, 0x3E),
                       (0x1B, 0x50), (0x19, 0x01)]
WINDOW_PULSE_IO = [(0x1B, 0x76), (0x19, 0xE8), (0x19, 0x03),
                   (0x1B, 0x50), (0x19, 0x01)]
CHIP_PULSE_IO = [(0x1B, 0x76), (0x19, 0xD0), (0x19, 0x07),
                 (0x1B, 0x50), (0x19, 0x01)]
NO_WINDOW_IO = [(0x1B, 0x76), (0x19, 0x80), (0x19, 0x3E)]


def read_master(master: int, outbound: bytearray) -> bool:
    try:
        outbound.extend(os.read(master, 4096))
        return True
    except OSError as error:
        if error.errno != errno.EIO:
            raise
        return False


def run_fallback(
    trace: Path, image: bytes, label: str, *, ram_fault: str | None = None,
    pic_fault: str | None = None, ppi_fault: str | None = None,
    pit_fault: str | None = None,
) -> tuple[subprocess.CompletedProcess[str], dict[str, str], bytes, bytes]:
    with tempfile.TemporaryDirectory(prefix=f"juku-d0-fallback-{label}-") as tmp_name:
        tmp = Path(tmp_name)
        rom = tmp / "diag.bin"
        prefix = tmp / "checkpoint"
        stdout_path = tmp / "stdout"
        stderr_path = tmp / "stderr"
        rom.write_bytes(image)
        master, slave = pty.openpty()
        tty.setraw(slave)
        env = os.environ.copy()
        env.update({
            "JUKU_TRACE_IO": "1",
            "JUKU_CHECKPOINT_PREFIX": str(prefix),
            "JUKU_USART_PTY": os.ttyname(slave),
            "JUKU_USART_TRANSFER_CYCLES": "64",
            "JUKU_USART_BYTE_CYCLES": "512",
        })
        if ram_fault:
            env["JUKU_RAM_FAULT"] = ram_fault
        if pic_fault:
            env["JUKU_PIC_FAULT"] = pic_fault
        if ppi_fault:
            env["JUKU_PPI_FAULT"] = ppi_fault
        if pit_fault:
            env["JUKU_PIT_FAULT"] = pit_fault
        with stdout_path.open("wb") as stdout_file, stderr_path.open("wb") as stderr_file:
            process = subprocess.Popen(
                [str(trace), str(rom), "100000000"], cwd=tmp, env=env,
                stdout=stdout_file, stderr=stderr_file,
            )
            os.close(slave)
            outbound = bytearray()
            deadline = time.monotonic() + 30
            while process.poll() is None:
                if time.monotonic() >= deadline:
                    process.kill()
                    raise TimeoutError(f"{label}: cosim did not terminate")
                if select.select([master], [], [], 0.02)[0]:
                    read_master(master, outbound)
            while select.select([master], [], [], 0)[0]:
                if not read_master(master, outbound):
                    break
            returncode = process.wait()
        os.close(master)
        stdout = stdout_path.read_text(errors="replace")
        stderr = stderr_path.read_text(errors="replace")
        state = ram_test.parse_state(prefix.with_suffix(".state"))
        ram = prefix.with_suffix(".ram").read_bytes()
    return subprocess.CompletedProcess([], returncode, stdout, stderr), state, bytes(outbound), ram


def verify_fallback(
    label: str,
    result: tuple[subprocess.CompletedProcess[str], dict[str, str], bytes, bytes],
    metadata: dict[str, int | list[int] | bytes],
    *,
    expected_e: int,
    no_windows: bool,
    pit_prefix_events: list[tuple[str, int, int]] | None = None,
) -> list[str]:
    proc, state, outbound, ram = result
    failures: list[str] = []
    expected_outbound = bytes((0x55,)) * firmware.TRAIN_LENGTH + bytes(metadata["banner"])
    if proc.returncode != 0:
        failures.append(f"{label}: cosim exited {proc.returncode}")
    if outbound != expected_outbound:
        failures.append(f"{label}: outbound {outbound.hex()} != {expected_outbound.hex()}")
    expected_pc = int(metadata["no_windows_halt" if no_windows else "windows_found_halt"])
    for key, expected in (
        ("pc", f"{expected_pc + 1:04X}"), ("sp", "0000"),
        ("halted", "1"), ("iff", "0"), ("mode", "0"),
        ("mode_switches", "0"), ("usart_tx_bytes", "25"),
        ("usart_rx_bytes", "0"), ("e", f"{expected_e:02X}"),
    ):
        if state.get(key) != expected:
            failures.append(f"{label}: {key}={state.get(key, 'missing')} != {expected}")

    events = []
    for line in proc.stderr.splitlines():
        if match := ram_test.IO_RE.match(line):
            events.append((match.group(1).strip(), int(match.group(2), 16),
                           int(match.group(3), 16)))
    tone_writes = [(port, value) for direction, port, value in events
                   if direction == "OUT" and port in (0x19, 0x1B)]
    terminal_io = (
        CHIP_PULSE_IO * 4 + NO_WINDOW_IO
        if no_windows else WINDOW_PULSE_IO * firmware.WINDOWS_FOUND_PULSES
    )
    prefix_tones = [
        (port, value) for direction, port, value in (pit_prefix_events or [])
        if direction == "OUT" and port in (0x19, 0x1B)
    ]
    expected_tones = (
        ALIVE_TONE_IO + prefix_tones + BAUD_CONTROL_IO
        + SERIAL_DEAD_MARK_IO + terminal_io
    )
    if tone_writes != expected_tones:
        failures.append(f"{label}: tone writes differ: {tone_writes}")
    pit_writes = [(port, value) for direction, port, value in events
                  if direction == "OUT" and 0x10 <= port <= 0x17]
    prefix_video = [
        (port, value) for direction, port, value in (pit_prefix_events or [])
        if direction == "OUT" and 0x10 <= port <= 0x17
    ]
    if pit_writes != prefix_video + list(firmware.VIDEO_PIT_WRITES):
        failures.append(f"{label}: video PIT init differs: {pit_writes}")
    not_ready = sum(direction == "IN" and port == 0x09 and value & 0x02 == 0
                    for direction, port, value in events)
    if not_ready < 0xFFFF:
        failures.append(f"{label}: ACK timeout had only {not_ready} not-ready reads")

    writes = {
        int(match.group(1), 16): int(match.group(2))
        for line in proc.stdout.splitlines()
        if (match := ram_test.WPAGE_RE.match(line))
    }
    candidate_pages = set(range(0x40, 0x50)) | set(range(0xC0, 0xD0))
    for page in range(0x100):
        expected = 1280 if page in candidate_pages else None
        if writes.get(page) != expected:
            failures.append(f"{label}: page {page:02X} writes={writes.get(page)} != {expected}")
            break
    for start, size in firmware.FALLBACK_WINDOWS:
        if ram[start : start + size] != bytes((0x55,)) * size:
            failures.append(f"{label}: window {start:04X} final fill is not 55")
    if no_windows:
        for key, expected in (("ram_fault_enabled", "1"), ("ram_fault_all", "1"),
                              ("ram_fault_stuck_low", "08")):
            if state.get(key) != expected:
                failures.append(f"{label}: {key}={state.get(key, 'missing')} != {expected}")
    return failures


def main() -> int:
    if len(sys.argv) != 3:
        print(
            f"usage: {Path(sys.argv[0]).name} /path/to/trace diag-d0-ram-fallback.bin",
            file=sys.stderr,
        )
        return 2
    trace = Path(sys.argv[1]).resolve()
    rom = Path(sys.argv[2]).resolve()
    image, metadata = firmware.build()
    if not trace.is_file() or not rom.is_file() or rom.read_bytes() != image:
        print("trace executable or exact RAM-fallback ROM is missing", file=sys.stderr)
        return 2

    # The cumulative image must retain the complete acknowledged serial survey.
    valid = ram_test.run_survey(trace, image, bytes(metadata["ack"]), "fallback-valid")
    failures = ram_test.verify_run(
        "fallback-valid", valid, metadata, {}, protocol.RamWindow(0x4000, 0x10000)
    )
    found = run_fallback(trace, image, "found")
    second_only = run_fallback(
        trace, image, "second-only", ram_fault="4008:08:00"
    )
    dead_chip = run_fallback(trace, image, "dead-chip", ram_fault="*:08:00")
    failures.extend(verify_fallback(
        "found", found, metadata, expected_e=0x03, no_windows=False
    ))
    failures.extend(verify_fallback(
        "second-only", second_only, metadata, expected_e=0x02, no_windows=False
    ))
    failures.extend(verify_fallback(
        "dead-chip", dead_chip, metadata, expected_e=0x00, no_windows=True
    ))

    if failures:
        print("JUKURAVI-D0-RAM-FALLBACK: FAIL", file=sys.stderr)
        for failure in failures:
            print(f"- {failure}", file=sys.stderr)
        return 1
    print(
        "JUKURAVI-D0-RAM-FALLBACK: PASS "
        "(ACK->192-page stream; no ACK + both/second window->3x2kHz; "
        "global D87-low->4x1kHz + continuous 125Hz)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
