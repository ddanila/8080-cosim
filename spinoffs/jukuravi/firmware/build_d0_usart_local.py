#!/usr/bin/env python3
"""Build Jukuravi D0 rung 3a: local 8251 transmit-state self-test."""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path

from build_d0_alive import Assembler, ROM_SIZE, emit_alive_beep
from build_d0_cpu import (
    EXPECTED_SIGNATURE,
    FAIL_TONE_DIVISOR as CPU_FAIL_TONE_DIVISOR,
    emit_cpu_self_test,
    emit_failure_tone,
)


HERE = Path(__file__).resolve().parent
OUTPUT = HERE / "diag-d0-usart-local.bin"
README = HERE / "README.md"
IDENTITY_OFFSET = 0x1F00
IDENTITY = b"JUKURAVI-D0-USART-LOCAL-1\0"

USART_DATA = 0x08
USART_CONTROL = 0x09
PIT_BAUD_COUNT = 0x18
PIT_CONTROL = 0x1B
USART_MODE = 0x4E       # asynchronous x16, 8 data bits, no parity, 1 stop bit
USART_COMMAND = 0x37    # TxEN, RxEN, DTR, RTS, reset error flags
USART_TEST_BYTE = 0x55
BAUD_DIVISOR = 8        # nominal 1.23 MHz / 8 / 16 ~= 9600 baud
TIMEOUT_COUNT = 0xFFFF  # about 1.67 seconds at the nominal 2 MHz CPU clock
USART_FAIL_TONE_DIVISOR = 4000  # nominal 500 Hz from D57 channel 1


def inp(asm: Assembler, port: int) -> None:
    asm.emit(0xDB, port)


def compare_masked(
    asm: Assembler, mask: int, expected: int, *, failure_label: str = "usart_fail"
) -> None:
    asm.emit(0xE6, mask)      # ANI mask
    asm.emit(0xFE, expected)  # CPI expected
    asm.jump(0xC2, failure_label)  # JNZ


def emit_timeout_wait(
    asm: Assembler, *, label: str, mask: int, done_label: str,
    failure_label: str = "usart_fail",
) -> int:
    """Poll a status bit with BC only; return the timeout immediate offset."""
    timeout_offset = asm.pc + 1
    asm.lxi_b(TIMEOUT_COUNT)
    asm.label(label)
    inp(asm, USART_CONTROL)
    asm.emit(0xE6, mask)       # ANI mask
    asm.jump(0xC2, done_label)  # JNZ done
    asm.emit(0x0B)             # DCX B
    asm.emit(0x78)             # MOV A,B
    asm.emit(0xB1)             # ORA C
    asm.jump(0xC2, label)      # JNZ poll
    asm.jump(0xC3, failure_label)
    asm.label(done_label)
    return timeout_offset


def emit_local_usart_test(
    asm: Assembler, *, failure_label: str = "usart_fail"
) -> list[int]:
    # Recover a known mode-instruction state even if D11 did not see a clean
    # board reset: sync mode + two sync bytes + internal-reset command.
    for value in (0x00, 0x00, 0x00, 0x40, USART_MODE, USART_COMMAND):
        asm.mvi_a(value)
        asm.out(USART_CONTROL)

    # At rest both the CPU-side holding register and transmitter must be empty.
    inp(asm, USART_CONTROL)
    compare_masked(asm, 0x05, 0x05, failure_label=failure_label)

    # Keep D57 channel 0 stopped until this read, making the holding-full state
    # observable before the first TxC edge transfers the byte to the shifter.
    asm.mvi_a(USART_TEST_BYTE)
    asm.out(USART_DATA)
    inp(asm, USART_CONTROL)
    compare_masked(asm, 0x05, 0x00, failure_label=failure_label)

    # D57 channel 0: binary mode 2, LSB+MSB, divisor 8. With the source-proved
    # nominal 1.23 MHz input and the 8251 x16 mode this is approximately 9600.
    asm.mvi_a(0x34)
    asm.out(PIT_CONTROL)
    asm.mvi_a(BAUD_DIVISOR)
    asm.out(PIT_BAUD_COUNT)
    asm.mvi_a(0x00)
    asm.out(PIT_BAUD_COUNT)

    timeout_offsets = [emit_timeout_wait(
        asm, label="wait_tx_ready", mask=0x01, done_label="tx_ready_seen",
        failure_label=failure_label,
    )]
    # TxRDY must rise while TxEMPTY remains low: the holding byte moved into
    # the active shifter rather than disappearing or remaining stuck.
    inp(asm, USART_CONTROL)
    compare_masked(asm, 0x05, 0x01, failure_label=failure_label)

    timeout_offsets.append(emit_timeout_wait(
        asm, label="wait_tx_empty", mask=0x04, done_label="tx_empty_seen",
        failure_label=failure_label,
    ))
    inp(asm, USART_CONTROL)
    compare_masked(asm, 0x05, 0x05, failure_label=failure_label)
    return timeout_offsets


def build() -> tuple[bytes, dict[str, int | list[int]]]:
    asm = Assembler()
    emit_alive_beep(asm, halt=False)
    signature_expected_offset = emit_cpu_self_test(asm)
    timeout_offsets = emit_local_usart_test(asm)

    success_halt = asm.pc
    asm.emit(0x76)

    asm.label("cpu_fail")
    emit_failure_tone(asm, CPU_FAIL_TONE_DIVISOR)
    cpu_fail_halt = asm.pc
    asm.emit(0x76)

    asm.label("usart_fail")
    emit_failure_tone(asm, USART_FAIL_TONE_DIVISOR)
    usart_fail_halt = asm.pc
    asm.emit(0x76)

    code = asm.resolve()
    image = bytearray([0x76] * ROM_SIZE)
    image[: len(code)] = code
    image[IDENTITY_OFFSET : IDENTITY_OFFSET + len(IDENTITY)] = IDENTITY
    metadata: dict[str, int | list[int]] = {
        "code_size": len(code),
        "signature_expected_offset": signature_expected_offset,
        "timeout_offsets": timeout_offsets,
        "success_halt": success_halt,
        "cpu_fail_halt": cpu_fail_halt,
        "usart_fail_halt": usart_fail_halt,
        "cpu_fail": asm.labels["cpu_fail"],
        "usart_fail": asm.labels["usart_fail"],
    }
    return bytes(image), metadata


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="fail if the committed image is stale")
    args = parser.parse_args()
    image, metadata = build()
    digest = hashlib.sha256(image).hexdigest()
    if args.check:
        if not OUTPUT.exists():
            raise SystemExit(f"missing generated image: {OUTPUT.name}")
        if OUTPUT.read_bytes() != image:
            raise SystemExit("diag-d0-usart-local.bin is stale; run build_d0_usart_local.py")
        if not README.exists() or digest not in README.read_text():
            raise SystemExit("firmware README does not pin the local-USART image SHA256")
        action = "checked"
    else:
        OUTPUT.write_bytes(image)
        action = "wrote"
    print(
        f"JUKURAVI-D0-USART-LOCAL-BUILD: {action} {OUTPUT.name} "
        f"bytes={len(image)} code={metadata['code_size']} "
        f"signature={EXPECTED_SIGNATURE:02X} sha256={digest}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
