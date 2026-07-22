#!/usr/bin/env python3
"""Prove Jukuravi's safe D27/8255 all-port register test and recovery."""

from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "tests"), str(ROOT / "spinoffs" / "jukuravi"),
                str(ROOT / "spinoffs" / "jukuravi" / "firmware")]
import build_d0_ppi as firmware  # noqa: E402
import jukuravi_d0_ram_fallback_test as fallback_test  # noqa: E402
import jukuravi_d0_ram_test as ram_test  # noqa: E402
import protocol  # noqa: E402


ALIVE_TONE_IO = [(0x1B, 0x76), (0x19, 0xD0), (0x19, 0x07),
                 (0x1B, 0x50), (0x19, 0x01)]
PPI_FAIL_IO = [(0x1B, 0x76), (0x19, 0x6B), (0x19, 0x0A)]


def io_events(proc) -> list[tuple[str, int, int]]:
    events = []
    for line in proc.stderr.splitlines():
        if match := ram_test.IO_RE.match(line):
            events.append((match.group(1).strip(), int(match.group(2), 16),
                           int(match.group(3), 16)))
    return events


def clean_ppi_io() -> list[tuple[str, int, int]]:
    events: list[tuple[str, int, int]] = [("OUT", 0x0F, 0x80)]
    for port in firmware.PPI1_PORTS:
        events.extend([
            ("OUT", port, 0x00), ("IN", port, 0x00),
            ("OUT", port, 0xFF), ("IN", port, 0xFF),
        ])
    events.append(("OUT", 0x0F, 0x9B))
    events.extend(("OUT", port, 0x00) for port in firmware.PPI1_PORTS)
    return events


def verify_safe_state(label: str, state: dict[str, str]) -> list[str]:
    failures: list[str] = []
    for key, expected in (
        ("ppi1_control", "9B"), ("ppi1_pa_latch", "00"),
        ("ppi1_pb_latch", "00"), ("ppi1_pc_latch", "00"),
        ("pic_mask", "FF"), ("pic_expect_icw2", "0"),
    ):
        if state.get(key) != expected:
            failures.append(f"{label}: {key}={state.get(key, 'missing')} != {expected}")
    return failures


def verify_ppi_failure(
    label: str,
    result: tuple,
    metadata: dict[str, int | list[int] | bytes],
    *,
    expected_ppi_io: list[tuple[str, int, int]],
    fault_port: int,
    stuck_low: int,
    stuck_high: int,
) -> list[str]:
    proc, state, outbound, ram = result
    failures: list[str] = []
    if proc.returncode != 0:
        failures.append(f"{label}: cosim exited {proc.returncode}")
    if outbound:
        failures.append(f"{label}: transmitted before PPI verdict: {outbound.hex()}")
    for key, expected in (
        ("pc", f"{int(metadata['ppi_fail_halt']) + 1:04X}"),
        ("sp", "0000"), ("halted", "1"), ("iff", "0"),
        ("mode", "0"), ("mode_switches", "0"),
        ("usart_tx_bytes", "0"), ("usart_rx_bytes", "0"),
        ("e", "D0"), ("ppi_fault_enabled", "1"),
        ("ppi_fault_port", f"{fault_port:02X}"),
        ("ppi_fault_stuck_low", f"{stuck_low:02X}"),
        ("ppi_fault_stuck_high", f"{stuck_high:02X}"),
    ):
        if state.get(key) != expected:
            failures.append(f"{label}: {key}={state.get(key, 'missing')} != {expected}")
    failures.extend(verify_safe_state(label, state))

    events = io_events(proc)
    ppi_io = [event for event in events if 0x0C <= event[1] <= 0x0F]
    if ppi_io != expected_ppi_io:
        failures.append(f"{label}: PPI I/O {ppi_io} != {expected_ppi_io}")
    tone_writes = [(port, value) for direction, port, value in events
                   if direction == "OUT" and port in (0x19, 0x1B)]
    if tone_writes != ALIVE_TONE_IO + PPI_FAIL_IO:
        failures.append(f"{label}: tone writes differ: {tone_writes}")
    later_outputs = [
        (port, value) for direction, port, value in events
        if direction == "OUT" and port not in (0x00, 0x01, 0x0C, 0x0D, 0x0E,
                                                0x0F, 0x19, 0x1B)
    ]
    if later_outputs:
        failures.append(f"{label}: later peripheral writes occurred: {later_outputs}")
    if any(ram):
        failures.append(f"{label}: RAM changed before PPI verdict")
    return failures


def main() -> int:
    if len(sys.argv) != 3:
        print(
            f"usage: {Path(sys.argv[0]).name} /path/to/trace diag-d0-ppi.bin",
            file=sys.stderr,
        )
        return 2
    trace = Path(sys.argv[1]).resolve()
    rom = Path(sys.argv[2]).resolve()
    image, metadata = firmware.build()
    if not trace.is_file() or not rom.is_file() or rom.read_bytes() != image:
        print("trace executable or exact PPI diagnostic image is missing", file=sys.stderr)
        return 2

    failures: list[str] = []
    offset = int(metadata["rom_checksum_offset"])
    start = int(metadata["rom_checksum_start"])
    end = int(metadata["rom_checksum_end"])
    if image[:3] != bytes((0xC3, firmware.ENTRY_OFFSET, 0x00)):
        failures.append(f"header: reset vector is {image[:3].hex()}")
    if image[offset] != (sum(image[start:end]) & 0xFF):
        failures.append("header: historical block-1 sum failed")
    if int(metadata["banner_offset"]) != end:
        failures.append("header: executable code escaped the checked block")
    if bytes(metadata["banner"])[5] != firmware.ROM_VERSION:
        failures.append("header: banner does not advertise ROM version 06")
    if (
        len(metadata["fallback_count_offsets"]) != 6
        or len(metadata["fallback_rewind_offsets"]) != 5
        or len(metadata["fallback_first_end_page_offsets"]) != 1
    ):
        failures.append("header: shared fallback loop is not selected")

    checksum_image = bytearray(image)
    for checksum_offset in metadata["checksum_zero_offsets"]:
        checksum_image[int(checksum_offset)] = 0
    if protocol.crc16_ccitt_false(bytes(checksum_image)) != metadata["checksum"]:
        failures.append("header: full-image CRC-16 contract failed")

    valid = ram_test.run_survey(trace, image, bytes(metadata["ack"]), "ppi-valid")
    failures.extend(ram_test.verify_run(
        "ppi-valid", valid, metadata, {}, protocol.RamWindow(0x4000, 0x10000)
    ))
    found = fallback_test.run_fallback(trace, image, "ppi-found")
    second_only = fallback_test.run_fallback(
        trace, image, "ppi-second-only", ram_fault="4008:08:00"
    )
    dead_chip = fallback_test.run_fallback(
        trace, image, "ppi-dead-chip", ram_fault="*:08:00"
    )
    failures.extend(fallback_test.verify_fallback(
        "ppi-found", found, metadata, expected_e=0x03, no_windows=False
    ))
    failures.extend(fallback_test.verify_fallback(
        "ppi-second-only", second_only, metadata, expected_e=0x02, no_windows=False
    ))
    failures.extend(fallback_test.verify_fallback(
        "ppi-dead-chip", dead_chip, metadata, expected_e=0x00, no_windows=True
    ))
    expected_clean = clean_ppi_io()
    for label, result in (
        ("ppi-valid", valid), ("ppi-found", found),
        ("ppi-second-only", second_only), ("ppi-dead-chip", dead_chip),
    ):
        failures.extend(verify_safe_state(label, result[1]))
        actual = [event for event in io_events(result[0]) if 0x0C <= event[1] <= 0x0F]
        if actual != expected_clean:
            failures.append(f"{label}: clean PPI I/O differs: {actual}")

    recovery = [("OUT", 0x0F, 0x9B)] + [
        ("OUT", port, 0x00) for port in firmware.PPI1_PORTS
    ]
    stuck_high = fallback_test.run_fallback(
        trace, image, "ppi-stuck-high", ppi_fault="0C:00:01"
    )
    failures.extend(verify_ppi_failure(
        "ppi-stuck-high", stuck_high, metadata,
        expected_ppi_io=[
            ("OUT", 0x0F, 0x80), ("OUT", 0x0C, 0x00),
            ("IN", 0x0C, 0x01), *recovery,
        ],
        fault_port=0x0C, stuck_low=0x00, stuck_high=0x01,
    ))
    stuck_low = fallback_test.run_fallback(
        trace, image, "ppi-stuck-low", ppi_fault="0E:01:00"
    )
    before_last_read = clean_ppi_io()[:-5]
    # Remove the expected clean FF read of Port C; the fault returns FE instead.
    before_last_read.append(("IN", 0x0E, 0xFE))
    failures.extend(verify_ppi_failure(
        "ppi-stuck-low", stuck_low, metadata,
        expected_ppi_io=before_last_read + recovery,
        fault_port=0x0E, stuck_low=0x01, stuck_high=0x00,
    ))

    if failures:
        print("JUKURAVI-D0-PPI: FAIL", file=sys.stderr)
        for failure in failures:
            print(f"- {failure}", file=sys.stderr)
        return 1
    print(
        "JUKURAVI-D0-PPI: PASS "
        "(D27 PA/PB/PC 00/FF; both stuck polarities; terminal 9B/input+zero; "
        "shared fallback clean/second-only/dead-chip; ACK predecessor)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
