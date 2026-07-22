#!/usr/bin/env python3
"""Prove Jukuravi's RAM-free 8259 command/data and IMR self-test."""

from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "tests"), str(ROOT / "spinoffs" / "jukuravi"),
                str(ROOT / "spinoffs" / "jukuravi" / "firmware")]
import build_d0_pic as firmware  # noqa: E402
import jukuravi_d0_ram_fallback_test as fallback_test  # noqa: E402
import jukuravi_d0_ram_test as ram_test  # noqa: E402
import protocol  # noqa: E402


ALIVE_TONE_IO = [(0x1B, 0x76), (0x19, 0xD0), (0x19, 0x07),
                 (0x1B, 0x50), (0x19, 0x01)]
PIC_FAIL_IO = [(0x1B, 0x76), (0x19, 0xF4), (0x19, 0x01)]


def verify_pic_failure(
    label: str,
    result: tuple,
    metadata: dict[str, int | list[int] | bytes],
    *,
    expected_pic_io: list[tuple[str, int, int]],
    stuck_low: int,
    stuck_high: int,
) -> list[str]:
    proc, state, outbound, ram = result
    failures: list[str] = []
    if proc.returncode != 0:
        failures.append(f"{label}: cosim exited {proc.returncode}")
    if outbound:
        failures.append(f"{label}: transmitted before PIC verdict: {outbound.hex()}")
    for key, expected in (
        ("pc", f"{int(metadata['pic_fail_halt']) + 1:04X}"),
        ("sp", "0000"), ("halted", "1"), ("iff", "0"),
        ("mode", "0"), ("mode_switches", "0"),
        ("usart_tx_bytes", "0"), ("usart_rx_bytes", "0"),
        ("e", "D0"), ("pic_icw1", "D6"), ("pic_icw2", "FE"),
        ("pic_mask", "FF"), ("pic_expect_icw2", "0"),
        ("pic_fault_enabled", "1"),
        ("pic_fault_stuck_low", f"{stuck_low:02X}"),
        ("pic_fault_stuck_high", f"{stuck_high:02X}"),
    ):
        if state.get(key) != expected:
            failures.append(f"{label}: {key}={state.get(key, 'missing')} != {expected}")

    events = []
    for line in proc.stderr.splitlines():
        if match := ram_test.IO_RE.match(line):
            events.append((match.group(1).strip(), int(match.group(2), 16),
                           int(match.group(3), 16)))
    pic_io = [event for event in events if event[1] in (0x00, 0x01)]
    if pic_io != expected_pic_io:
        failures.append(f"{label}: PIC I/O {pic_io} != {expected_pic_io}")
    tone_writes = [(port, value) for direction, port, value in events
                   if direction == "OUT" and port in (0x19, 0x1B)]
    if tone_writes != ALIVE_TONE_IO + PIC_FAIL_IO:
        failures.append(f"{label}: tone writes differ: {tone_writes}")
    other_outputs = [(port, value) for direction, port, value in events
                     if direction == "OUT" and port not in (0x00, 0x01, 0x19, 0x1B)]
    if other_outputs:
        failures.append(f"{label}: later peripheral writes occurred: {other_outputs}")
    if any(ram):
        failures.append(f"{label}: RAM changed before PIC verdict")
    return failures


def main() -> int:
    if len(sys.argv) != 3:
        print(
            f"usage: {Path(sys.argv[0]).name} /path/to/trace diag-d0-pic.bin",
            file=sys.stderr,
        )
        return 2
    trace = Path(sys.argv[1]).resolve()
    rom = Path(sys.argv[2]).resolve()
    image, metadata = firmware.build()
    if not trace.is_file() or not rom.is_file() or rom.read_bytes() != image:
        print("trace executable or exact PIC diagnostic image is missing", file=sys.stderr)
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
        failures.append("header: banner does not advertise ROM version 05")

    checksum_image = bytearray(image)
    for checksum_offset in metadata["checksum_zero_offsets"]:
        checksum_image[int(checksum_offset)] = 0
    if protocol.crc16_ccitt_false(bytes(checksum_image)) != metadata["checksum"]:
        failures.append("header: full-image CRC-16 contract failed")

    valid = ram_test.run_survey(trace, image, bytes(metadata["ack"]), "pic-valid")
    failures.extend(ram_test.verify_run(
        "pic-valid", valid, metadata, {}, protocol.RamWindow(0x4000, 0x10000)
    ))
    found = fallback_test.run_fallback(trace, image, "pic-found")
    failures.extend(fallback_test.verify_fallback(
        "pic-found", found, metadata, expected_e=0x03, no_windows=False
    ))
    for label, result in (("pic-valid", valid), ("pic-found", found)):
        state = result[1]
        for key, expected in (
            ("pic_icw1", "D6"), ("pic_icw2", "FE"),
            ("pic_mask", "FF"), ("pic_expect_icw2", "0"),
            ("pic_fault_enabled", "0"),
        ):
            if state.get(key) != expected:
                failures.append(
                    f"{label}: {key}={state.get(key, 'missing')} != {expected}"
                )

    stuck_high = fallback_test.run_fallback(
        trace, image, "pic-stuck-high", pic_fault="00:01"
    )
    failures.extend(verify_pic_failure(
        "pic-stuck-high", stuck_high, metadata,
        expected_pic_io=[
            ("OUT", 0x00, 0xD6), ("OUT", 0x01, 0xFE),
            ("OUT", 0x01, 0x00), ("IN", 0x01, 0x01),
            ("OUT", 0x01, 0xFF),
        ],
        stuck_low=0x00,
        stuck_high=0x01,
    ))
    stuck_low = fallback_test.run_fallback(
        trace, image, "pic-stuck-low", pic_fault="01:00"
    )
    failures.extend(verify_pic_failure(
        "pic-stuck-low", stuck_low, metadata,
        expected_pic_io=[
            ("OUT", 0x00, 0xD6), ("OUT", 0x01, 0xFE),
            ("OUT", 0x01, 0x00), ("IN", 0x01, 0x00),
            ("OUT", 0x01, 0xFF), ("IN", 0x01, 0xFE),
            ("OUT", 0x01, 0xFF),
        ],
        stuck_low=0x01,
        stuck_high=0x00,
    ))

    if failures:
        print("JUKURAVI-D0-PIC: FAIL", file=sys.stderr)
        for failure in failures:
            print(f"- {failure}", file=sys.stderr)
        return 1
    print(
        "JUKURAVI-D0-PIC: PASS "
        "(D6/FE MCS-80 init; IMR 00/FF readback; both stuck polarities; "
        "terminal mask FF; ACK/no-ACK predecessors)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
