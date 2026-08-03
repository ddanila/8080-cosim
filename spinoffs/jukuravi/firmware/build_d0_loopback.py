#!/usr/bin/env python3
"""Build T18: RAM-independent external X3 RS-232 loopback diagnostic."""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path

from build_d0_alive import Assembler, ROM_SIZE, emit_alive_beep
from build_d0_cpu import emit_failure_tone
from build_d0_ram_fallback import (
    SLOW_REPORT_PAUSE_COUNT,
    WINDOWS_FOUND_DIVISOR,
    emit_register_delay,
    emit_slow_grouped_pulse_loop,
)
from build_d0_serial import SERIAL_DEAD_TONE_DIVISOR, emit_status_wait
from build_d0_usart_local import (
    BAUD_DIVISOR,
    PIT_BAUD_COUNT,
    PIT_CONTROL,
    USART_COMMAND,
    USART_CONTROL,
    USART_DATA,
    USART_MODE,
    inp,
)


HERE = Path(__file__).resolve().parent
OUTPUT = HERE / "diag-d0-loopback.bin"
IDENTITY_OFFSET = 0x1F00
IDENTITY = b"JUKURAVI-D0-X3-LOOPBACK-1\0"
PATTERN = bytes((0x55, 0xAA, 0x00, 0xFF, 0x96, 0x69))


def terminal_code(asm: Assembler, code: int, stem: str) -> int:
    emit_register_delay(asm, stem=f"{stem}_lead", count=SLOW_REPORT_PAUSE_COUNT)
    asm.emit(0x16, code)  # MVI D,code
    emit_slow_grouped_pulse_loop(
        asm, stem=stem, divisor=WINDOWS_FOUND_DIVISOR,
        done_label=f"{stem}_tail",
    )
    asm.label(f"{stem}_tail")
    emit_register_delay(asm, stem=f"{stem}_pause", count=SLOW_REPORT_PAUSE_COUNT)
    emit_failure_tone(asm, SERIAL_DEAD_TONE_DIVISOR)
    halt = asm.pc
    asm.emit(0x76)
    return halt


def build() -> tuple[bytes, dict[str, int | list[int]]]:
    asm = Assembler()
    emit_alive_beep(asm, halt=False)

    # Put the 8251 in a known asynchronous state without transmitting the
    # local-test byte used by T03/T17.  Receiver state is therefore clean when
    # the first externally looped byte arrives.
    for value in (0x00, 0x00, 0x00, 0x40, USART_MODE, USART_COMMAND):
        asm.mvi_a(value)
        asm.out(USART_CONTROL)

    # D57 channel 0 supplies the shared TxC/RxC x16 baud clock.
    asm.mvi_a(0x34)
    asm.out(PIT_CONTROL)
    asm.mvi_a(BAUD_DIVISOR)
    asm.out(PIT_BAUD_COUNT)
    asm.mvi_a(0x00)
    asm.out(PIT_BAUD_COUNT)

    timeout_offsets: list[int] = []
    for index, value in enumerate(PATTERN):
        timeout_offsets.append(emit_status_wait(
            asm, stem=f"loop_tx_{index}", mask=0x01,
            failure_label="tx_dead",
        ))
        asm.mvi_a(value)
        asm.out(USART_DATA)
        timeout_offsets.append(emit_status_wait(
            asm, stem=f"loop_rx_{index}", mask=0x02,
            failure_label="no_rx",
        ))
        inp(asm, USART_DATA)
        asm.emit(0xFE, value)  # CPI expected
        asm.jump(0xC2, "wrong_rx")

    # Four slow pulses and silence: all six bytes crossed the complete
    # D11->X3.9->X3.4->D104->D11 external loop.
    asm.emit(0x16, 0x04)
    emit_slow_grouped_pulse_loop(
        asm, stem="loop_pass", divisor=WINDOWS_FOUND_DIVISOR,
        done_label="loop_pass_halt",
    )
    asm.label("loop_pass_halt")
    pass_halt = asm.pc
    asm.emit(0x76)

    # After the initial alive beep:
    #   1 pulse + continuous low tone = RxRDY never asserted
    #   2 pulses + continuous low tone = a byte arrived incorrectly
    #   3 pulses + continuous low tone = transmitter/CTS never became ready
    asm.label("no_rx")
    no_rx_halt = terminal_code(asm, 1, "loop_no_rx")
    asm.label("wrong_rx")
    wrong_rx_halt = terminal_code(asm, 2, "loop_wrong_rx")
    asm.label("tx_dead")
    tx_dead_halt = terminal_code(asm, 3, "loop_tx_dead")

    code = asm.resolve()
    image = bytearray([0x76] * ROM_SIZE)
    image[:len(code)] = code
    image[IDENTITY_OFFSET:IDENTITY_OFFSET + len(IDENTITY)] = IDENTITY
    return bytes(image), {
        "code_size": len(code), "pattern": list(PATTERN),
        "timeout_offsets": timeout_offsets, "pass_halt": pass_halt,
        "no_rx_halt": no_rx_halt, "wrong_rx_halt": wrong_rx_halt,
        "tx_dead_halt": tx_dead_halt,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    image, metadata = build()
    if args.check:
        if not OUTPUT.exists() or OUTPUT.read_bytes() != image:
            raise SystemExit("diag-d0-loopback.bin is missing or stale")
        action = "checked"
    else:
        OUTPUT.write_bytes(image)
        action = "wrote"
    print(
        f"JUKURAVI-D0-LOOPBACK-BUILD: {action} {OUTPUT.name} "
        f"bytes={len(image)} code={metadata['code_size']} "
        f"sha256={hashlib.sha256(image).hexdigest()}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
