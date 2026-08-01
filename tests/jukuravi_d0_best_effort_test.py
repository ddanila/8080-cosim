#!/usr/bin/env python3
"""Prove nonfatal peripheral reporting, UART-before-RAM, and RAM fallback."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "tests"), str(ROOT / "spinoffs" / "jukuravi"),
                str(ROOT / "spinoffs" / "jukuravi" / "firmware")]
import build_d0_best_effort as firmware  # noqa: E402
import build_d0_serial as serial_firmware  # noqa: E402
import jukuravi_d0_ram_fallback_test as runner  # noqa: E402
import protocol  # noqa: E402


def frames_from(outbound: bytes) -> list[protocol.Frame]:
    # Discard the local-test/training 55 bytes before framed traffic.
    return protocol.StreamDecoder().feed(outbound[serial_firmware.TRAIN_LENGTH:])


def run_case(trace, image, metadata, label, *, pit_fault=None, ram_fault=None,
             pic_fault=None, ppi_fault=None):
    expected_prefix = serial_firmware.TRAIN_LENGTH + len(metadata["banner"])
    result = runner.run_fallback(
        trace, image, label, pit_fault=pit_fault, ram_fault=ram_fault,
        pic_fault=pic_fault, ppi_fault=ppi_fault,
        reply=bytes(metadata["ack"]), reply_after=expected_prefix,
    )
    if result[0].returncode != 0:
        return result, [f"{label}: cosim exited {result[0].returncode}"]
    return result, []


def main() -> int:
    if len(sys.argv) != 3:
        print(f"usage: {Path(sys.argv[0]).name} trace diag-d0-best-effort.bin",
              file=sys.stderr)
        return 2
    trace, rom = map(lambda value: Path(value).resolve(), sys.argv[1:])
    image, metadata = firmware.build()
    if not trace.is_file() or not rom.is_file() or rom.read_bytes() != image:
        print("trace executable or exact best-effort image is missing", file=sys.stderr)
        return 2

    failures = []
    cases = [
        ("clean", None, None, 0x00, 0x83, "success_halt"),
        ("d55-bad", "16:80:00", None, firmware.FAULT_D55, 0x83, "success_halt"),
        ("ram-dead", None, "*:FF:00", 0x00, 0x80, "ram_fail_halt"),
    ]
    for label, pit_fault, ram_fault, peripheral, ram_status, halt_key in cases:
        result, problems = run_case(trace, image, metadata, label,
                                    pit_fault=pit_fault, ram_fault=ram_fault)
        failures.extend(problems)
        frames = frames_from(result[2])
        expected = [
            protocol.Frame(protocol.TYPE_BANNER, bytes(metadata["banner"])[4:-1]),
            protocol.Frame(protocol.TYPE_DIAG_STATUS, bytes((peripheral,))),
            protocol.Frame(protocol.TYPE_DIAG_STATUS, bytes((ram_status,))),
        ]
        if frames != expected:
            failures.append(f"{label}: frames={frames} != {expected}")
        expected_pc = int(metadata[halt_key]) + 1
        if result[1].get("pc") != f"{expected_pc:04X}":
            failures.append(f"{label}: pc={result[1].get('pc')} != {expected_pc:04X}")
        if result[1].get("sp") != "0000" or result[1].get("iff") != "0":
            failures.append(f"{label}: used stack or enabled interrupts")

    combined, problems = run_case(
        trace, image, metadata, "combined",
        pit_fault="16:80:00", pic_fault="01:00", ppi_fault="0D:01:00",
    )
    failures.extend(problems)
    combined_frames = frames_from(combined[2])
    if len(combined_frames) != 3 or combined_frames[1] != protocol.Frame(
        protocol.TYPE_DIAG_STATUS,
        bytes((firmware.FAULT_PIC | firmware.FAULT_PPI | firmware.FAULT_D55,)),
    ):
        failures.append(f"combined: frames={combined_frames}")

    # UART failure must happen before any RAM write and report slow code six.
    uart_dead = runner.run_fallback(trace, image, "uart-dead")
    if uart_dead[1].get("pc") != f"{int(metadata['uart_fail_halt']) + 1:04X}":
        failures.append("uart-dead: wrong terminal path")
    if any(uart_dead[3]):
        failures.append("uart-dead: RAM was touched before UART handshake")
    uart_stuck = runner.run_fallback(
        trace, image, "uart-stuck", usart_fault="tx_stuck"
    )
    if uart_stuck[1].get("pc") != f"{int(metadata['uart_fail_halt']) + 1:04X}":
        failures.append("uart-stuck: wrong terminal path")
    if any(uart_stuck[3]):
        failures.append("uart-stuck: RAM was touched before local UART failure")

    if failures:
        print("JUKURAVI-D0-BEST-EFFORT: FAIL", file=sys.stderr)
        for failure in failures:
            print(f"- {failure}", file=sys.stderr)
        return 1
    print("JUKURAVI-D0-BEST-EFFORT: PASS (D55 continues to UART; UART precedes RAM)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
