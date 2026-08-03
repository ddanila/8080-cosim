#!/usr/bin/env python3
"""Build T19: bounded, noise-tolerant external serial loopback diagnostic."""

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
OUTPUT = HERE / "diag-d0-tolerant-loopback.bin"
IDENTITY_OFFSET = 0x1F00
IDENTITY = b"JUKURAVI-D0-X3-TOLERANT-1\0"
PATTERN = bytes((0x55, 0xAA, 0x00, 0xFF, 0x96, 0x69))
RETRIES = 8
RX_TIMEOUT = 0x4000  # roughly 0.4 seconds at the nominal 2 MHz CPU clock


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

    # D is a sticky recovery flag.  Drain up to 255 bytes which arrived during
    # reset/adapter startup; those bytes must not poison the first comparison.
    asm.emit(0x16, 0x00, 0x1E, 0xFF)  # MVI D,0 / MVI E,255
    asm.label("drain_rx")
    inp(asm, USART_CONTROL)
    asm.emit(0xE6, 0x02)  # ANI RxRDY
    asm.jump(0xCA, "drain_done")
    inp(asm, USART_DATA)
    asm.emit(0x16, 0x01, 0x1D)  # MVI D,1 / DCR E
    asm.jump(0xC2, "drain_rx")
    asm.label("drain_done")

    timeout_offsets: list[int] = []
    for index, value in enumerate(PATTERN):
        asm.emit(0x1E, RETRIES)  # MVI E,retries
        asm.label(f"byte_{index}_attempt")
        timeout_offsets.append(emit_status_wait(
            asm, stem=f"loop_tx_{index}", mask=0x01,
            failure_label="tx_dead",
        ))
        asm.mvi_a(value)
        asm.out(USART_DATA)

        # Use a shorter per-attempt receive window and retry both a missing
        # response and a corrupt/stale byte.  This tolerates adapter turn-around
        # delay and line-start glitches while remaining bounded (~3.2 s/byte).
        timeout_offsets.append(asm.pc + 1)
        asm.lxi_b(RX_TIMEOUT)
        asm.label(f"byte_{index}_rx_wait")
        inp(asm, USART_CONTROL)
        asm.emit(0xE6, 0x02)
        asm.jump(0xC2, f"byte_{index}_rx_seen")
        asm.emit(0x0B, 0x78, 0xB1)
        asm.jump(0xC2, f"byte_{index}_rx_wait")
        asm.jump(0xC3, f"byte_{index}_retry")
        asm.label(f"byte_{index}_rx_seen")
        inp(asm, USART_DATA)
        asm.emit(0xFE, value)  # CPI expected
        asm.jump(0xCA, f"byte_{index}_good")
        asm.label(f"byte_{index}_retry")
        asm.emit(0x16, 0x01, 0x1D)  # MVI D,1 / DCR E
        asm.jump(0xC2, f"byte_{index}_attempt")
        asm.jump(0xC3, "no_match")
        asm.label(f"byte_{index}_good")

    # Four slow pulses and silence = completely clean.  Five and silence = all
    # bytes eventually matched, but startup draining or a retry was required.
    asm.emit(0x7A, 0xB7)  # MOV A,D / ORA A
    asm.jump(0xC2, "loop_recovered")
    asm.emit(0x16, 0x04)
    asm.jump(0xC3, "loop_report")
    asm.label("loop_recovered")
    asm.emit(0x16, 0x05)
    asm.label("loop_report")
    emit_slow_grouped_pulse_loop(
        asm, stem="loop_pass", divisor=WINDOWS_FOUND_DIVISOR,
        done_label="loop_pass_halt",
    )
    asm.label("loop_pass_halt")
    pass_halt = asm.pc
    asm.emit(0x76)

    # One pulse + continuous tone means no correct echo was found in eight
    # bounded attempts; this includes absent and persistently corrupt replies.
    asm.label("no_match")
    no_match_halt = terminal_code(asm, 1, "loop_no_match")
    # Three pulses + continuous tone means transmitter/CTS never became ready.
    asm.label("tx_dead")
    tx_dead_halt = terminal_code(asm, 3, "loop_tx_dead")

    code = asm.resolve()
    image = bytearray([0x76] * ROM_SIZE)
    image[:len(code)] = code
    image[IDENTITY_OFFSET:IDENTITY_OFFSET + len(IDENTITY)] = IDENTITY
    return bytes(image), {
        "code_size": len(code), "pattern": list(PATTERN),
        "timeout_offsets": timeout_offsets, "pass_halt": pass_halt,
        "no_match_halt": no_match_halt,
        "tx_dead_halt": tx_dead_halt,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    image, metadata = build()
    if args.check:
        if not OUTPUT.exists() or OUTPUT.read_bytes() != image:
            raise SystemExit("diag-d0-tolerant-loopback.bin is missing or stale")
        action = "checked"
    else:
        OUTPUT.write_bytes(image)
        action = "wrote"
    print(
        f"JUKURAVI-D0-TOLERANT-LOOPBACK-BUILD: {action} {OUTPUT.name} "
        f"bytes={len(image)} code={metadata['code_size']} "
        f"sha256={hashlib.sha256(image).hexdigest()}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
