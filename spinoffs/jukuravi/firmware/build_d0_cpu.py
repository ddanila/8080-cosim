#!/usr/bin/env python3
"""Build Jukuravi D0 rung 2: alive beep plus register-only CPU self-test."""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path

from build_d0_alive import Assembler, ROM_SIZE, emit_alive_beep


HERE = Path(__file__).resolve().parent
OUTPUT = HERE / "diag-d0-cpu.bin"
README = HERE / "README.md"
IDENTITY_OFFSET = 0x1F00
IDENTITY = b"JUKURAVI-D0-CPU-1\0"
SIGNATURE_SEED = 0xA5
EXPECTED_SIGNATURE = 0xD0
FAIL_TONE_DIVISOR = 8000  # nominal 250 Hz from D57 channel 1's 2 MHz clock

# Result bytes folded into E by XRA E / RLC / MOV E,A. This independently
# documents the signature oracle; build() verifies it before emitting firmware.
SIGNATURE_RESULTS = (
    0x80,  # 7F + 01
    0x00,  # FE + 01 + carry
    0xFF,  # 00 - 01
    0x00,  # 10 - 0F - borrow
    0x05,  # 55 AND 0F
    0x55,  # AA XOR FF
    0x81,  # 80 OR 01
    0x42,  # CMP equal preserves A
    0x10,  # CMP borrow preserves A
    0x03,  # RLC 81
    0x80,  # RRC 01
    0x01,  # RAL 80 with carry in
    0x80,  # RAR 01 with carry in
    0x80,  # INR 7F
    0xFF,  # DCR 00
    0x18,  # decimal 09 + 09
    0x98,  # decimal 99 + 99, carry set
)


def signature_oracle() -> int:
    signature = SIGNATURE_SEED
    for result in SIGNATURE_RESULTS:
        value = result ^ signature
        signature = ((value << 1) & 0xFF) | (value >> 7)
    return signature


def fail_if(asm: Assembler, opcode: int) -> None:
    asm.jump(opcode, "cpu_fail")


def mix_signature(asm: Assembler) -> None:
    asm.emit(0xAB)  # XRA E
    asm.emit(0x07)  # RLC
    asm.emit(0x5F)  # MOV E,A


def mvi(asm: Assembler, register_opcode: int, value: int) -> None:
    asm.emit(register_opcode, value)


def immediate(asm: Assembler, opcode: int, value: int) -> None:
    asm.emit(opcode, value)


def build() -> tuple[bytes, dict[str, int]]:
    if signature_oracle() != EXPECTED_SIGNATURE:
        raise ValueError(
            f"signature oracle {signature_oracle():02X} != {EXPECTED_SIGNATURE:02X}"
        )

    asm = Assembler()
    emit_alive_beep(asm, halt=False)
    mvi(asm, 0x1E, SIGNATURE_SEED)  # MVI E,seed

    # ADD: 7F+01=80; S=1, Z=0, CY=0, parity odd.
    asm.mvi_a(0x7F)
    immediate(asm, 0xC6, 0x01)  # ADI
    for opcode in (0xF2, 0xCA, 0xDA, 0xEA):  # JP/JZ/JC/JPE
        fail_if(asm, opcode)
    mix_signature(asm)

    # ADC: FE+01+CY=00; S=0, Z=1, CY=1, parity even.
    asm.emit(0x37)  # STC
    asm.mvi_a(0xFE)
    immediate(asm, 0xCE, 0x01)  # ACI
    for opcode in (0xC2, 0xD2, 0xFA, 0xE2):  # JNZ/JNC/JM/JPO
        fail_if(asm, opcode)
    mix_signature(asm)

    # SUB: 00-01=FF; S=1, Z=0, borrow/CY=1, parity even.
    asm.mvi_a(0x00)
    immediate(asm, 0xD6, 0x01)  # SUI
    for opcode in (0xD2, 0xCA, 0xF2, 0xE2):  # JNC/JZ/JP/JPO
        fail_if(asm, opcode)
    mix_signature(asm)

    # SBB: 10-0F-CY=00 without borrow; S=0, Z=1, CY=0, parity even.
    asm.emit(0x37)
    asm.mvi_a(0x10)
    immediate(asm, 0xDE, 0x0F)  # SBI
    for opcode in (0xC2, 0xDA, 0xFA, 0xE2):  # JNZ/JC/JM/JPO
        fail_if(asm, opcode)
    mix_signature(asm)

    # Logical operations must clear carry and set Z/S/P from the result.
    for start, opcode, operand, bad_branches in (
        (0x55, 0xE6, 0x0F, (0xCA, 0xDA, 0xFA, 0xE2)),  # ANI -> 05, even parity
        (0xAA, 0xEE, 0xFF, (0xCA, 0xDA, 0xFA, 0xE2)),  # XRI -> 55, even parity
        (0x80, 0xF6, 0x01, (0xF2, 0xE2, 0xCA, 0xDA)),  # ORI -> 81, S + even parity
    ):
        asm.mvi_a(start)
        immediate(asm, opcode, operand)
        for branch in bad_branches:
            fail_if(asm, branch)
        mix_signature(asm)

    # CMP equality and borrow; both must preserve A for the signature.
    asm.mvi_a(0x42)
    immediate(asm, 0xFE, 0x42)
    for opcode in (0xC2, 0xDA, 0xFA, 0xE2):  # JNZ/JC/JM/JPO
        fail_if(asm, opcode)
    mix_signature(asm)
    asm.mvi_a(0x10)
    immediate(asm, 0xFE, 0x20)
    for opcode in (0xD2, 0xF2, 0xCA, 0xE2):  # JNC/JP/JZ/JPO
        fail_if(asm, opcode)
    mix_signature(asm)

    # All four rotates; rotate instructions change carry but leave Z/S/P alone.
    for start, rotate, use_carry in (
        (0x81, 0x07, False),  # RLC -> 03, CY=1
        (0x01, 0x0F, False),  # RRC -> 80, CY=1
        (0x80, 0x17, True),   # RAL -> 01, CY=1
        (0x01, 0x1F, True),   # RAR -> 80, CY=1
    ):
        asm.emit(0xAF)  # XRA A establishes Z=1, S=0, P=1, CY=0
        if use_carry:
            asm.emit(0x37)  # STC supplies the through-carry input
        asm.mvi_a(start)
        asm.emit(rotate)
        for opcode in (0xD2, 0xC2, 0xFA, 0xE2):  # JNC/JNZ/JM/JPO
            fail_if(asm, opcode)
        mix_signature(asm)

    # INR/DCR must update Z/S/P while preserving CY=1.
    asm.emit(0x37)
    mvi(asm, 0x06, 0x7F)  # MVI B,7F
    asm.emit(0x04)  # INR B -> 80
    for opcode in (0xD2, 0xF2, 0xCA, 0xEA):  # JNC/JP/JZ/JPE (parity is odd)
        fail_if(asm, opcode)
    asm.emit(0x78)  # MOV A,B
    mix_signature(asm)

    asm.emit(0x37)
    mvi(asm, 0x0E, 0x00)  # MVI C,00
    asm.emit(0x0D)  # DCR C -> FF
    for opcode in (0xD2, 0xF2, 0xCA, 0xE2):  # JNC/JP/JZ/JPO (parity is even)
        fail_if(asm, opcode)
    asm.emit(0x79)  # MOV A,C
    mix_signature(asm)

    # DAA must consume the half-carry/carry left by the preceding ADI.
    asm.mvi_a(0x09)
    immediate(asm, 0xC6, 0x09)
    asm.emit(0x27)  # DAA -> 18, CY=0, parity even
    for opcode in (0xCA, 0xDA, 0xFA, 0xE2):  # JZ/JC/JM/JPO
        fail_if(asm, opcode)
    mix_signature(asm)

    asm.mvi_a(0x99)
    immediate(asm, 0xC6, 0x99)
    asm.emit(0x27)  # DAA -> 98, CY=1, sign set, parity odd
    for opcode in (0xCA, 0xD2, 0xF2, 0xEA):  # JZ/JNC/JP/JPE
        fail_if(asm, opcode)
    mix_signature(asm)

    asm.emit(0x7B)  # MOV A,E
    signature_expected_offset = asm.pc + 1
    immediate(asm, 0xFE, EXPECTED_SIGNATURE)  # CPI expected signature
    fail_if(asm, 0xC2)  # JNZ cpu_fail
    success_halt = asm.pc
    asm.emit(0x76)

    # A mismatch leaves a continuous, unmistakably lower CPU-bad tone. The PIT
    # runs after HLT, so this path does not depend on another delay loop.
    asm.label("cpu_fail")
    asm.mvi_a(0x76)
    asm.out(0x1B)
    asm.mvi_a(FAIL_TONE_DIVISOR & 0xFF)
    asm.out(0x19)
    asm.mvi_a(FAIL_TONE_DIVISOR >> 8)
    asm.out(0x19)
    fail_halt = asm.pc
    asm.emit(0x76)

    code = asm.resolve()
    image = bytearray([0x76] * ROM_SIZE)
    image[: len(code)] = code
    image[IDENTITY_OFFSET : IDENTITY_OFFSET + len(IDENTITY)] = IDENTITY
    metadata = {
        "code_size": len(code),
        "signature_expected_offset": signature_expected_offset,
        "success_halt": success_halt,
        "fail_halt": fail_halt,
        "cpu_fail": asm.labels["cpu_fail"],
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
            raise SystemExit("diag-d0-cpu.bin is stale; run build_d0_cpu.py")
        if not README.exists() or digest not in README.read_text():
            raise SystemExit("firmware README does not pin the CPU image SHA256")
        action = "checked"
    else:
        OUTPUT.write_bytes(image)
        action = "wrote"
    print(
        f"JUKURAVI-D0-CPU-BUILD: {action} {OUTPUT.name} bytes={len(image)} "
        f"code={metadata['code_size']} signature={EXPECTED_SIGNATURE:02X} "
        f"sha256={digest}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
