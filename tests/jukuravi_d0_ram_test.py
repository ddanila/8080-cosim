#!/usr/bin/env python3
"""Prove the full Jukuravi D0 mode-0 RAM survey and bit-mask reporting."""

from __future__ import annotations

import errno
import os
import pty
import re
import select
import subprocess
import sys
import tempfile
import time
import tty
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "spinoffs" / "jukuravi"),
                str(ROOT / "spinoffs" / "jukuravi" / "firmware")]
import build_d0_ram as firmware  # noqa: E402
import protocol  # noqa: E402


IO_RE = re.compile(
    r"^\[IOSEQ\] (IN |OUT) port=0x([0-9A-Fa-f]{2}) "
    r"value=0x([0-9A-Fa-f]{2})"
)
WPAGE_RE = re.compile(r"^  0x([0-9A-Fa-f]{2})00 :\s+([0-9]+)$")


def parse_state(path: Path) -> dict[str, str]:
    return dict(line.split("=", 1) for line in path.read_text().splitlines() if "=" in line)


def read_master(master: int, outbound: bytearray) -> None:
    try:
        outbound.extend(os.read(master, 4096))
    except OSError as error:
        if error.errno != errno.EIO:
            raise


def run_survey(
    trace: Path,
    image: bytes,
    ack: bytes,
    label: str,
    *,
    ram_fault: str | None = None,
    ram_alias: str | None = None,
) -> tuple[subprocess.CompletedProcess[str], dict[str, str], bytes, bytes]:
    with tempfile.TemporaryDirectory(prefix=f"juku-d0-ram-{label}-") as tmp_name:
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
        if ram_alias:
            env["JUKU_RAM_ALIAS"] = ram_alias
        with stdout_path.open("wb") as stdout_file, stderr_path.open("wb") as stderr_file:
            process = subprocess.Popen(
                [str(trace), str(rom), "100000000"], cwd=tmp, env=env,
                stdout=stdout_file, stderr=stderr_file,
            )
            os.close(slave)
            outbound = bytearray()
            replied = False
            deadline = time.monotonic() + 30
            handshake_length = firmware.TRAIN_LENGTH + len(firmware.build()[1]["banner"])
            while process.poll() is None:
                if time.monotonic() >= deadline:
                    process.kill()
                    raise TimeoutError(f"{label}: cosim did not terminate")
                if select.select([master], [], [], 0.02)[0]:
                    read_master(master, outbound)
                if not replied and len(outbound) >= handshake_length:
                    os.write(master, ack)
                    replied = True
            while select.select([master], [], [], 0)[0]:
                before = len(outbound)
                read_master(master, outbound)
                if len(outbound) == before:
                    break
            returncode = process.wait()
        os.close(master)
        stdout = stdout_path.read_text(errors="replace")
        stderr = stderr_path.read_text(errors="replace")
        state = parse_state(prefix.with_suffix(".state"))
        ram = prefix.with_suffix(".ram").read_bytes()
    return subprocess.CompletedProcess([], returncode, stdout, stderr), state, bytes(outbound), ram


def verify_run(
    label: str,
    result: tuple[subprocess.CompletedProcess[str], dict[str, str], bytes, bytes],
    metadata: dict[str, int | list[int] | bytes],
    expected_masks: dict[int, int],
    expected_window: protocol.RamWindow,
) -> list[str]:
    proc, state, outbound, ram = result
    failures: list[str] = []
    banner = bytes(metadata["banner"])
    expected_tx_count = (
        firmware.TRAIN_LENGTH + len(banner) + len(metadata["begin_frame"])
        + 7 * (firmware.SURVEY_END_PAGE - firmware.SURVEY_START_PAGE + 1)
        + len(metadata["end_frame"])
    )
    if proc.returncode != 0:
        failures.append(f"{label}: cosim exited {proc.returncode}")
    if outbound[:firmware.TRAIN_LENGTH] != bytes((0x55,)) * firmware.TRAIN_LENGTH:
        failures.append(f"{label}: training run differs")
    decoder = protocol.StreamDecoder()
    frames = decoder.feed(outbound)
    if len(frames) != 195:
        failures.append(f"{label}: decoded {len(frames)} frames instead of 195")
        return failures
    if frames[0] != protocol.Frame(protocol.TYPE_BANNER, banner[4:-1]):
        failures.append(f"{label}: banner frame differs")
    expected_begin = bytes((firmware.SURVEY_VERSION, firmware.SURVEY_START_PAGE,
                            firmware.SURVEY_END_PAGE, firmware.PATTERN_SET))
    if frames[1] != protocol.Frame(protocol.TYPE_RAM_BEGIN, expected_begin):
        failures.append(f"{label}: RAM_BEGIN differs: {frames[1]}")
    block_frames = frames[2:-1]
    for index, frame in enumerate(block_frames):
        page = firmware.SURVEY_START_PAGE + index
        expected_mask = expected_masks.get(page, 0)
        if frame != protocol.Frame(protocol.TYPE_RAM_BLOCK, bytes((page, expected_mask))):
            failures.append(
                f"{label}: page {page:02X} record {frame} != mask {expected_mask:02X}"
            )
            break
    expected_end = bytes((firmware.SURVEY_START_PAGE, firmware.SURVEY_END_PAGE))
    if frames[-1] != protocol.Frame(protocol.TYPE_RAM_END, expected_end):
        failures.append(f"{label}: RAM_END differs: {frames[-1]}")
    try:
        survey = protocol.decode_ram_survey(frames)
    except ValueError as error:
        failures.append(f"{label}: host survey decoder rejected stream: {error}")
        survey = None
    if survey is not None:
        if survey.largest_good_window != expected_window:
            failures.append(
                f"{label}: largest window {survey.largest_good_window} != {expected_window}"
            )
        for bit in range(8):
            expected_pages = tuple(
                page for page, mask in expected_masks.items() if mask & (1 << bit)
            )
            if survey.bad_pages_by_bit[bit] != expected_pages:
                failures.append(
                    f"{label}: bit {bit} bad pages {survey.bad_pages_by_bit[bit]} "
                    f"!= {expected_pages}"
                )

    for key, expected in (
        ("pc", f"{int(metadata['success_halt']) + 1:04X}"),
        ("sp", "0000"), ("halted", "1"), ("iff", "0"),
        ("mode", "0"), ("mode_switches", "0"),
        ("usart_tx_bytes", str(expected_tx_count)), ("usart_rx_bytes", "9"),
    ):
        if state.get(key) != expected:
            failures.append(f"{label}: {key}={state.get(key, 'missing')} != {expected}")

    writes = {
        int(match.group(1), 16): int(match.group(2))
        for line in proc.stdout.splitlines()
        if (match := WPAGE_RE.match(line))
    }
    for page in range(firmware.SURVEY_START_PAGE, firmware.SURVEY_END_PAGE + 1):
        if writes.get(page) != 1664:
            failures.append(f"{label}: page {page:02X} writes={writes.get(page)} != 1664")
            break
    expected_ram = bytearray((0x55,) * (0x10000 - 0x4000))
    for page, mask in expected_masks.items():
        if page == 0x7A and mask == 0x28:
            expected_ram[0x7A5C - 0x4000] = 0x75
    if label == "alias":
        expected_ram[0x9000 - 0x4000 : 0x9100 - 0x4000] = bytes(0x100)
    if ram[0x4000:] != expected_ram:
        mismatch = next(index for index, (actual, expected) in enumerate(
            zip(ram[0x4000:], expected_ram)) if actual != expected)
        failures.append(
            f"{label}: final RAM mismatch at {mismatch + 0x4000:04X}: "
            f"{ram[mismatch + 0x4000]:02X} != {expected_ram[mismatch]:02X}"
        )

    pit_writes = [
        (port, value)
        for line in proc.stderr.splitlines()
        if (match := IO_RE.match(line)) and match.group(1).strip() == "OUT"
        for port, value in [(int(match.group(2), 16), int(match.group(3), 16))]
        if 0x10 <= port <= 0x17
    ]
    if pit_writes != list(firmware.VIDEO_PIT_WRITES):
        failures.append(f"{label}: video PIT init differs: {pit_writes}")
    return failures


def main() -> int:
    if len(sys.argv) != 3:
        print(f"usage: {Path(sys.argv[0]).name} /path/to/trace diag-d0-ram.bin", file=sys.stderr)
        return 2
    trace = Path(sys.argv[1]).resolve()
    rom = Path(sys.argv[2]).resolve()
    image, metadata = firmware.build()
    if not trace.is_file() or not rom.is_file() or rom.read_bytes() != image:
        print("trace executable or exact RAM diagnostic ROM is missing", file=sys.stderr)
        return 2

    checksum_image = bytearray(image)
    for offset in metadata["checksum_zero_offsets"]:
        checksum_image[int(offset)] = 0
    if protocol.crc16_ccitt_false(bytes(checksum_image)) != metadata["checksum"]:
        print("JUKURAVI-D0-RAM: FAIL self-checksum contract", file=sys.stderr)
        return 1

    clean = run_survey(trace, image, bytes(metadata["ack"]), "clean")
    fault = run_survey(
        trace, image, bytes(metadata["ack"]), "fault", ram_fault="7A5C:08:20"
    )
    alias = run_survey(
        trace, image, bytes(metadata["ack"]), "alias", ram_alias="50:90"
    )
    failures = verify_run(
        "clean", clean, metadata, {}, protocol.RamWindow(0x4000, 0x10000)
    )
    failures.extend(verify_run(
        "fault", fault, metadata, {0x7A: 0x28},
        protocol.RamWindow(0x7B00, 0x10000),
    ))
    failures.extend(verify_run(
        "alias", alias, metadata, {0x50: 0xFF, 0x90: 0xFF},
        protocol.RamWindow(0x9100, 0x10000),
    ))
    for key, expected in (
        ("ram_fault_enabled", "1"), ("ram_fault_addr", "7A5C"),
        ("ram_fault_stuck_low", "08"), ("ram_fault_stuck_high", "20"),
    ):
        if fault[1].get(key) != expected:
            failures.append(f"fault: {key}={fault[1].get(key, 'missing')} != {expected}")
    for key, expected in (
        ("ram_alias_enabled", "1"), ("ram_alias_page_a", "50"),
        ("ram_alias_page_b", "90"),
    ):
        if alias[1].get(key) != expected:
            failures.append(f"alias: {key}={alias[1].get(key, 'missing')} != {expected}")

    if failures:
        print("JUKURAVI-D0-RAM: FAIL", file=sys.stderr)
        for failure in failures:
            print(f"- {failure}", file=sys.stderr)
        return 1
    print(
        "JUKURAVI-D0-RAM: PASS "
        "(192 pages, data/address/retention passes, clean masks=00, "
        "7A5C low08/high20 -> 7A:28, alias 50:90 -> 50/90:FF)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
