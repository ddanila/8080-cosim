#!/usr/bin/env python3
"""Prove Jukuravi's surveyed-RAM address-XOR framebuffer checkpoint."""

from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "tests"), str(ROOT / "spinoffs" / "jukuravi"),
                str(ROOT / "spinoffs" / "jukuravi" / "firmware")]
import build_d0_framebuffer as firmware  # noqa: E402
import jukuravi_d0_pit_test as pit_test  # noqa: E402
import jukuravi_d0_ppi_test as ppi_test  # noqa: E402
import jukuravi_d0_ram_fallback_test as fallback_test  # noqa: E402
import jukuravi_d0_ram_test as ram_test  # noqa: E402
import protocol  # noqa: E402


ROM_FAIL_IO = [
    ("OUT", 0x1B, 0x76), ("OUT", 0x19, 0xE8), ("OUT", 0x19, 0x03),
]
FRAMEBUFFER_FAIL_IO = [(0x1B, 0x76), (0x19, 0x9B), (0x19, 0x02)]


def clean_final_ram() -> bytearray:
    expected = bytearray((0x55,) * (0x10000 - 0x4000))
    for address in range(firmware.FRAMEBUFFER_BASE, firmware.FRAMEBUFFER_END):
        expected[address - 0x4000] = (address >> 8) ^ (address & 0xFF)
    return expected


def pattern_page_writes() -> dict[int, int]:
    writes: dict[int, int] = {}
    for address in range(firmware.FRAMEBUFFER_BASE, firmware.FRAMEBUFFER_END):
        page = address >> 8
        writes[page] = writes.get(page, 0) + 1
    return writes


def verify_corrupt_extension(
    label: str,
    result: tuple,
    metadata: dict[str, int | list[int] | bytes],
    expected_pit: list[tuple[str, int, int]],
) -> list[str]:
    proc, state, outbound, ram = result
    failures: list[str] = []
    if proc.returncode != 0:
        failures.append(f"{label}: cosim exited {proc.returncode}")
    if state.get("pc") != f"{int(metadata['rom_fail_halt']) + 1:04X}":
        failures.append(f"{label}: wrong ROM-fail PC {state.get('pc')}")
    failures.extend(pit_test.verify_terminal_safety(label, state))
    if outbound or any(ram):
        failures.append(f"{label}: reached USART/RAM after extension fault")
    actual_pit = pit_test.pit_slice(proc)
    if actual_pit != expected_pit:
        failures.append(f"{label}: PIT/ROM-fail I/O {actual_pit} != {expected_pit}")
    return failures


def main() -> int:
    if len(sys.argv) != 3:
        print(
            f"usage: {Path(sys.argv[0]).name} /path/to/trace "
            "diag-d0-framebuffer.bin",
            file=sys.stderr,
        )
        return 2
    trace = Path(sys.argv[1]).resolve()
    rom = Path(sys.argv[2]).resolve()
    image, metadata = firmware.build()
    if not trace.is_file() or not rom.is_file() or rom.read_bytes() != image:
        print("trace executable or exact framebuffer image is missing", file=sys.stderr)
        return 2

    failures: list[str] = []
    block_start = int(metadata["rom_checksum_start"])
    block_end = int(metadata["rom_checksum_end"])
    pit_start = int(metadata["pit_extension_start"])
    pit_end = int(metadata["pit_extension_end"])
    framebuffer_start = int(metadata["framebuffer_extension_start"])
    framebuffer_end = int(metadata["framebuffer_extension_end"])
    if image[:3] != bytes((0xC3, firmware.ENTRY_OFFSET, 0x00)):
        failures.append(f"header: reset vector is {image[:3].hex()}")
    if image[int(metadata["rom_checksum_offset"])] != (
        sum(image[block_start:block_end]) & 0xFF
    ):
        failures.append("header: historical block-1 sum failed")
    if pit_end - pit_start != 0x100 or (
        sum(image[pit_start:pit_end]) & 0xFF
        != metadata["pit_extension_checksum"]
    ):
        failures.append("header: full-page PIT extension guard failed")
    if framebuffer_end - framebuffer_start > 0xFF or (
        sum(image[framebuffer_start:framebuffer_end]) & 0xFF
        != metadata["framebuffer_extension_checksum"]
    ):
        failures.append("header: framebuffer extension guard failed")
    if bytes(metadata["banner"])[5] != firmware.ROM_VERSION:
        failures.append("header: banner does not advertise ROM version 08")
    checksum_image = bytearray(image)
    for offset in metadata["checksum_zero_offsets"]:
        checksum_image[int(offset)] = 0
    if protocol.crc16_ccitt_false(bytes(checksum_image)) != metadata["checksum"]:
        failures.append("header: full-image CRC-16 contract failed")

    expected_pit = pit_test.expected_pit_io()
    prefix_video = [
        (port, value) for direction, port, value in expected_pit
        if direction == "OUT" and 0x10 <= port <= 0x17
    ]
    clean = ram_test.run_survey(trace, image, bytes(metadata["ack"]), "framebuffer-clean")
    failures.extend(ram_test.verify_run(
        "framebuffer-clean", clean, metadata, {},
        protocol.RamWindow(0x4000, 0x10000),
        pit_prefix_writes=prefix_video,
        post_survey_page_writes=pattern_page_writes(),
        expected_final_ram=clean_final_ram(),
    ))
    if pit_test.pit_slice(clean[0])[:len(expected_pit)] != expected_pit:
        failures.append("framebuffer-clean: cumulative PIT traffic differs")
    failures.extend(ppi_test.verify_safe_state("framebuffer-clean", clean[1]))

    fault_ram = bytearray((0x55,) * (0x10000 - 0x4000))
    fault_ram[firmware.FRAMEBUFFER_BASE - 0x4000] = 0x54
    fault_metadata = dict(metadata)
    fault_metadata["success_halt"] = metadata["framebuffer_fail_halt"]
    fault = ram_test.run_survey(
        trace, image, bytes(metadata["ack"]), "framebuffer-fault",
        ram_fault="D800:01:00",
    )
    failures.extend(ram_test.verify_run(
        "framebuffer-fault", fault, fault_metadata, {0xD8: 0x01},
        protocol.RamWindow(0x4000, 0xD800),
        pit_prefix_writes=prefix_video,
        expected_final_ram=fault_ram,
    ))
    fault_tones = [
        (port, value)
        for direction, port, value in ppi_test.io_events(fault[0])
        if direction == "OUT" and port in (0x19, 0x1B)
    ]
    if fault_tones[-len(FRAMEBUFFER_FAIL_IO):] != FRAMEBUFFER_FAIL_IO:
        failures.append(f"framebuffer-fault: failure-tone suffix {fault_tones}")

    fallback = fallback_test.run_fallback(trace, image, "framebuffer-fallback")
    failures.extend(fallback_test.verify_fallback(
        "framebuffer-fallback", fallback, metadata,
        expected_e=0x03, no_windows=False, pit_prefix_events=expected_pit,
    ))

    pit_corrupt = bytearray(image)
    pit_corrupt[pit_start] ^= 1
    pit_bad = fallback_test.run_fallback(
        trace, bytes(pit_corrupt), "framebuffer-pit-extension-corrupt"
    )
    failures.extend(verify_corrupt_extension(
        "framebuffer-pit-extension-corrupt", pit_bad, metadata, []
    ))

    framebuffer_corrupt = bytearray(image)
    framebuffer_corrupt[framebuffer_start] ^= 1
    framebuffer_bad = fallback_test.run_fallback(
        trace, bytes(framebuffer_corrupt), "framebuffer-extension-corrupt"
    )
    failures.extend(verify_corrupt_extension(
        "framebuffer-extension-corrupt", framebuffer_bad, metadata,
        expected_pit + ROM_FAIL_IO,
    ))

    if failures:
        print("JUKURAVI-D0-FRAMEBUFFER: FAIL", file=sys.stderr)
        for failure in failures:
            print(f"- {failure}", file=sys.stderr)
        return 1
    print(
        "JUKURAVI-D0-FRAMEBUFFER: PASS "
        "(9640-byte address-XOR draw/readback; surveyed-RAM gate; both extension "
        "guards; ACK and no-ACK predecessors)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
