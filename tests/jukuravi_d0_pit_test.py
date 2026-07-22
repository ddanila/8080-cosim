#!/usr/bin/env python3
"""Prove Jukuravi's phase-tolerant D54/D55/D57 counter-register test."""

from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "tests"), str(ROOT / "spinoffs" / "jukuravi"),
                str(ROOT / "spinoffs" / "jukuravi" / "firmware")]
import build_d0_pit as firmware  # noqa: E402
import jukuravi_d0_ppi_test as ppi_test  # noqa: E402
import jukuravi_d0_ram_fallback_test as fallback_test  # noqa: E402
import jukuravi_d0_ram_test as ram_test  # noqa: E402
import protocol  # noqa: E402


PIT_FAIL_TONE = [
    ("OUT", 0x1B, 0x76), ("OUT", 0x19, 0x35), ("OUT", 0x19, 0x05)
]
PIT_RECOVERY = [
    ("OUT", 0x1B, 0x50), ("OUT", 0x19, 0x01),
    ("OUT", 0x1B, 0x90), ("OUT", 0x1A, 0x01),
]


def expected_pit_io() -> list[tuple[str, int, int]]:
    events: list[tuple[str, int, int]] = []
    for base in firmware.PIT_CHIP_BASES:
        control = base + 3
        for channel in range(3):
            port = base + channel
            events.extend([
                ("OUT", control, 0x20 | (channel << 6)),
                ("OUT", port, firmware.PIT_HIGH_COUNT),
                ("OUT", control, channel << 6),
                ("IN", port, firmware.PIT_HIGH_COUNT),
            ])
        events.extend([
            ("OUT", control, 0x20),
            ("OUT", base, firmware.PIT_LOW_COUNT),
            ("OUT", control, 0x00),
            ("IN", base, firmware.PIT_LOW_COUNT),
        ])
    return events + PIT_RECOVERY


def pit_slice(proc) -> list[tuple[str, int, int]]:
    events = ppi_test.io_events(proc)
    start = next(
        (index for index, event in enumerate(events)
         if event == ("OUT", 0x13, 0x20)),
        len(events),
    )
    return events[start:]


def verify_terminal_safety(label: str, state: dict[str, str]) -> list[str]:
    failures = ppi_test.verify_safe_state(label, state)
    for key, expected in (
        ("sp", "0000"), ("iff", "0"), ("mode", "0"),
        ("mode_switches", "0"), ("e", "D0"),
    ):
        if state.get(key) != expected:
            failures.append(f"{label}: {key}={state.get(key, 'missing')} != {expected}")
    return failures


def verify_pit_failure(
    label: str,
    result: tuple,
    metadata: dict[str, int | list[int] | bytes],
    expected_io: list[tuple[str, int, int]],
    *, port: int, stuck_low: int, stuck_high: int,
) -> list[str]:
    proc, state, outbound, ram = result
    failures: list[str] = []
    if proc.returncode != 0:
        failures.append(f"{label}: cosim exited {proc.returncode}")
    for key, expected in (
        ("pc", f"{int(metadata['pit_fail_halt']) + 1:04X}"),
        ("halted", "1"), ("usart_tx_bytes", "0"), ("usart_rx_bytes", "0"),
        ("pit_fault_enabled", "1"), ("pit_fault_port", f"{port:02X}"),
        ("pit_fault_stuck_low", f"{stuck_low:02X}"),
        ("pit_fault_stuck_high", f"{stuck_high:02X}"),
    ):
        if state.get(key) != expected:
            failures.append(f"{label}: {key}={state.get(key, 'missing')} != {expected}")
    failures.extend(verify_terminal_safety(label, state))
    if outbound:
        failures.append(f"{label}: transmitted before PIT verdict: {outbound.hex()}")
    if any(ram):
        failures.append(f"{label}: RAM changed before PIT verdict")
    actual = pit_slice(proc)
    if actual != expected_io:
        failures.append(f"{label}: PIT I/O {actual} != {expected_io}")
    return failures


def main() -> int:
    if len(sys.argv) != 3:
        print(
            f"usage: {Path(sys.argv[0]).name} /path/to/trace diag-d0-pit.bin",
            file=sys.stderr,
        )
        return 2
    trace = Path(sys.argv[1]).resolve()
    rom = Path(sys.argv[2]).resolve()
    image, metadata = firmware.build()
    if not trace.is_file() or not rom.is_file() or rom.read_bytes() != image:
        print("trace executable or exact PIT diagnostic image is missing", file=sys.stderr)
        return 2

    failures: list[str] = []
    start = int(metadata["pit_extension_start"])
    end = int(metadata["pit_extension_end"])
    if image[:3] != bytes((0xC3, firmware.ENTRY_OFFSET, 0x00)):
        failures.append(f"header: reset vector is {image[:3].hex()}")
    if image[int(metadata["rom_checksum_offset"])] != (
        sum(image[int(metadata["rom_checksum_start"]):int(metadata["rom_checksum_end"])]) & 0xFF
    ):
        failures.append("header: historical block-1 sum failed")
    if sum(image[start:end]) & 0xFF != metadata["pit_extension_checksum"]:
        failures.append("header: PIT extension checksum failed")
    if end - start != metadata["pit_extension_length"] or end - start > 0xFF:
        failures.append("header: PIT extension escaped its 8-bit guard")
    if bytes(metadata["banner"])[5] != firmware.ROM_VERSION:
        failures.append("header: banner does not advertise ROM version 07")

    checksum_image = bytearray(image)
    for offset in metadata["checksum_zero_offsets"]:
        checksum_image[int(offset)] = 0
    if protocol.crc16_ccitt_false(bytes(checksum_image)) != metadata["checksum"]:
        failures.append("header: full-image CRC-16 contract failed")

    valid = ram_test.run_survey(trace, image, bytes(metadata["ack"]), "pit-valid")
    expected_clean = expected_pit_io()
    prefix_video_writes = [
        (port, value) for direction, port, value in expected_clean
        if direction == "OUT" and 0x10 <= port <= 0x17
    ]
    failures.extend(ram_test.verify_run(
        "pit-valid", valid, metadata, {}, protocol.RamWindow(0x4000, 0x10000),
        pit_prefix_writes=prefix_video_writes,
    ))
    found = fallback_test.run_fallback(trace, image, "pit-found")
    failures.extend(fallback_test.verify_fallback(
        "pit-found", found, metadata, expected_e=0x03, no_windows=False,
        pit_prefix_events=expected_clean,
    ))
    for label, result in (("pit-valid", valid), ("pit-found", found)):
        actual = pit_slice(result[0])[:len(expected_clean)]
        if actual != expected_clean:
            failures.append(f"{label}: clean PIT I/O {actual} != {expected_clean}")
        failures.extend(ppi_test.verify_safe_state(label, result[1]))

    stuck_low = fallback_test.run_fallback(
        trace, image, "pit-stuck-low", pit_fault="10:80:00"
    )
    low_expected = expected_clean[:3] + [("IN", 0x10, 0x7F)] + PIT_RECOVERY + PIT_FAIL_TONE
    failures.extend(verify_pit_failure(
        "pit-stuck-low", stuck_low, metadata, low_expected,
        port=0x10, stuck_low=0x80, stuck_high=0x00,
    ))

    stuck_high = fallback_test.run_fallback(
        trace, image, "pit-stuck-high", pit_fault="14:00:80"
    )
    # D54 contributes 16 events; D55 contributes 12 high-range events and
    # three low-range writes before the injected BF read fails.
    high_expected = (
        expected_clean[:16] + expected_clean[16:31]
        + [("IN", 0x14, 0xBF)] + PIT_RECOVERY + PIT_FAIL_TONE
    )
    failures.extend(verify_pit_failure(
        "pit-stuck-high", stuck_high, metadata, high_expected,
        port=0x14, stuck_low=0x00, stuck_high=0x80,
    ))

    corrupt = bytearray(image)
    corrupt[start] ^= 0x01
    bad_extension = fallback_test.run_fallback(
        trace, bytes(corrupt), "pit-extension-corrupt"
    )
    proc, state, outbound, ram = bad_extension
    if proc.returncode != 0:
        failures.append(f"pit-extension-corrupt: cosim exited {proc.returncode}")
    if state.get("pc") != f"{int(metadata['rom_fail_halt']) + 1:04X}":
        failures.append(f"pit-extension-corrupt: wrong halt PC {state.get('pc')}")
    failures.extend(verify_terminal_safety("pit-extension-corrupt", state))
    if outbound or any(ram) or pit_slice(proc):
        failures.append("pit-extension-corrupt: reached PIT/USART/RAM after checksum fault")

    if failures:
        print("JUKURAVI-D0-PIT: FAIL", file=sys.stderr)
        for failure in failures:
            print(f"- {failure}", file=sys.stderr)
        return 1
    print(
        "JUKURAVI-D0-PIT: PASS "
        "(9 counter selects; DB7 high/low per chip; both fault polarities; "
        "extension checksum; ACK and fallback predecessors)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
