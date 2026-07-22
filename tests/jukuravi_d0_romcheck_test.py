#!/usr/bin/env python3
"""Prove Jukuravi's historical block-1 ROM checksum convention and fault code."""

from __future__ import annotations

import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "tests"), str(ROOT / "spinoffs" / "jukuravi"),
                str(ROOT / "spinoffs" / "jukuravi" / "firmware")]
import build_d0_romcheck as firmware  # noqa: E402
import jukuravi_d0_ram_fallback_test as fallback_test  # noqa: E402
import jukuravi_d0_ram_test as ram_test  # noqa: E402
import protocol  # noqa: E402


ALIVE_TONE_IO = [(0x1B, 0x76), (0x19, 0xD0), (0x19, 0x07),
                 (0x1B, 0x50), (0x19, 0x01)]
ROM_FAIL_IO = [(0x1B, 0x76), (0x19, 0xE8), (0x19, 0x03)]
HISTOGRAM_RE = re.compile(r"^\s+0x([0-9A-Fa-f]{4})\s+:\s+([0-9]+)$")


def verify_rom_failure(
    result: tuple, metadata: dict[str, int | list[int] | bytes]
) -> list[str]:
    proc, state, outbound, ram = result
    failures: list[str] = []
    if proc.returncode != 0:
        failures.append(f"corrupt: cosim exited {proc.returncode}")
    if outbound:
        failures.append(f"corrupt: transmitted before ROM verdict: {outbound.hex()}")
    for key, expected in (
        ("pc", f"{int(metadata['rom_fail_halt']) + 1:04X}"),
        ("sp", "0000"), ("halted", "1"), ("iff", "0"),
        ("mode", "0"), ("mode_switches", "0"),
        ("usart_tx_bytes", "0"), ("usart_rx_bytes", "0"),
        ("b", "00"), ("c", "00"), ("e", "D0"),
        ("h", "08"), ("l", "00"),
    ):
        if state.get(key) != expected:
            failures.append(f"corrupt: {key}={state.get(key, 'missing')} != {expected}")

    events = []
    for line in proc.stderr.splitlines():
        if match := ram_test.IO_RE.match(line):
            events.append((match.group(1).strip(), int(match.group(2), 16),
                           int(match.group(3), 16)))
    tone_writes = [(port, value) for direction, port, value in events
                   if direction == "OUT" and port in (0x19, 0x1B)]
    if tone_writes != ALIVE_TONE_IO + ROM_FAIL_IO:
        failures.append(f"corrupt: tone writes differ: {tone_writes}")
    non_tone_writes = [(port, value) for direction, port, value in events
                       if direction == "OUT" and port not in (0x19, 0x1B)]
    if non_tone_writes:
        failures.append(f"corrupt: peripheral writes before ROM verdict: {non_tone_writes}")
    if any(ram):
        failures.append("corrupt: RAM changed before ROM verdict")

    histogram = {
        int(match.group(1), 16): int(match.group(2))
        for line in proc.stdout.splitlines()
        if (match := HISTOGRAM_RE.match(line))
    }
    loop = int(metadata["rom_checksum_loop"])
    expected_iterations = int(metadata["rom_checksum_end"]) - int(
        metadata["rom_checksum_start"]
    )
    if histogram.get(loop) != expected_iterations:
        failures.append(
            f"corrupt: checksum loop count={histogram.get(loop)} != {expected_iterations}"
        )
    return failures


def main() -> int:
    if len(sys.argv) != 3:
        print(
            f"usage: {Path(sys.argv[0]).name} /path/to/trace diag-d0-romcheck.bin",
            file=sys.stderr,
        )
        return 2
    trace = Path(sys.argv[1]).resolve()
    rom = Path(sys.argv[2]).resolve()
    image, metadata = firmware.build()
    if not trace.is_file() or not rom.is_file() or rom.read_bytes() != image:
        print("trace executable or exact ROM-check image is missing", file=sys.stderr)
        return 2

    failures: list[str] = []
    start = int(metadata["rom_checksum_start"])
    end = int(metadata["rom_checksum_end"])
    offset = int(metadata["rom_checksum_offset"])
    computed = sum(image[start:end]) & 0xFF
    if image[:3] != bytes((0xC3, 0x10, 0x00)):
        failures.append(f"header: reset vector is {image[:3].hex()} instead of C31000")
    if offset != 0x000A or start != 0x000B or end != 0x0800:
        failures.append(f"header: convention bounds are {offset:04X}/{start:04X}/{end:04X}")
    if image[offset] != computed or computed != int(metadata["rom_checksum"]):
        failures.append(
            f"header: stored={image[offset]:02X} computed={computed:02X} "
            f"metadata={int(metadata['rom_checksum']):02X}"
        )
    if int(metadata["banner_offset"]) != end:
        failures.append("header: protocol tables overlap the checksummed block")
    if bytes(metadata["banner"])[5] != firmware.ROM_VERSION:
        failures.append("header: banner does not advertise ROM version 04")

    checksum_image = bytearray(image)
    for checksum_offset in metadata["checksum_zero_offsets"]:
        checksum_image[int(checksum_offset)] = 0
    if protocol.crc16_ccitt_false(bytes(checksum_image)) != metadata["checksum"]:
        failures.append("header: full-image CRC-16 contract failed")

    # This convention is not invented for the diagnostic: every official
    # EktaSoft image in the repository stores the same block-1 sum at 000Ah.
    for name in ("ekta24.bin", "ekta31.bin", "ekta32.bin", "ekta35.bin", "ekta37.bin"):
        official = (ROOT / "roms" / name).read_bytes()
        official_sum = sum(official[start:end]) & 0xFF
        if official[offset] != official_sum:
            failures.append(
                f"{name}: stored={official[offset]:02X} computed={official_sum:02X}"
            )

    valid = ram_test.run_survey(trace, image, bytes(metadata["ack"]), "romcheck-valid")
    failures.extend(ram_test.verify_run(
        "romcheck-valid", valid, metadata, {}, protocol.RamWindow(0x4000, 0x10000)
    ))
    found = fallback_test.run_fallback(trace, image, "romcheck-found")
    failures.extend(fallback_test.verify_fallback(
        "romcheck-found", found, metadata, expected_e=0x03, no_windows=False
    ))

    corrupt = bytearray(image)
    fault_offset = int(metadata["rom_fault_offset"])
    corrupt[fault_offset] ^= 0x01
    if (sum(corrupt[start:end]) & 0xFF) == corrupt[offset]:
        failures.append("corrupt: injected byte did not break the block-1 checksum")
    corrupt_result = fallback_test.run_fallback(
        trace, bytes(corrupt), "romcheck-corrupt"
    )
    failures.extend(verify_rom_failure(corrupt_result, metadata))

    if failures:
        print("JUKURAVI-D0-ROMCHECK: FAIL", file=sys.stderr)
        for failure in failures:
            print(f"- {failure}", file=sys.stderr)
        return 1
    print(
        "JUKURAVI-D0-ROMCHECK: PASS "
        "(official 000A=sum[000B:0800]; clean ACK/no-ACK predecessors; "
        "covered-byte fault->continuous 2kHz before USART/RAM)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
