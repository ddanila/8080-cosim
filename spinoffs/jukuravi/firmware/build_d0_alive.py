#!/usr/bin/env python3
"""Build the first stack-free Jukuravi D15 diagnostic ROM checkpoint."""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path


HERE = Path(__file__).resolve().parent
OUTPUT = HERE / "diag-d0-alive.bin"
README = HERE / "README.md"
ROM_SIZE = 8192
IDENTITY_OFFSET = 0x0100
IDENTITY = b"JUKURAVI-D0-ALIVE-1\0"

# D57/PIT2 channel 1 is clocked at the source-proved nominal 2 MHz. 8253 mode
# 3 divides that input by the programmed count, so 2000 selects a 1 kHz tone.
TONE_DIVISOR = 2000

# The delay body is DCX B / MOV A,B / ORA C / JNZ: 24 8080 T-states per
# iteration. 41,667 iterations plus setup/exit give 1,000,035 T-states from
# the completed tone programming write to the silence control write: 0.5000175
# seconds at the nominal 2 MHz CPU clock.
DELAY_COUNT = 41667
DELAY_COUNT_OFFSET = 0x000D


class Assembler:
    def __init__(self) -> None:
        self.code = bytearray()
        self.labels: dict[str, int] = {}
        self.fixups: list[tuple[int, str]] = []

    @property
    def pc(self) -> int:
        return len(self.code)

    def emit(self, *values: int) -> None:
        if any(value < 0 or value > 0xFF for value in values):
            raise ValueError(f"byte outside range: {values}")
        self.code.extend(values)

    def label(self, name: str) -> None:
        if name in self.labels:
            raise ValueError(f"duplicate label: {name}")
        self.labels[name] = self.pc

    def mvi_a(self, value: int) -> None:
        self.emit(0x3E, value)

    def out(self, port: int) -> None:
        self.emit(0xD3, port)

    def lxi_b(self, value: int) -> None:
        self.emit(0x01, value & 0xFF, value >> 8)

    def jnz(self, label: str) -> None:
        self.jump(0xC2, label)

    def jump(self, opcode: int, label: str) -> None:
        self.emit(opcode, 0x00, 0x00)
        self.fixups.append((self.pc - 2, label))

    def resolve(self) -> bytes:
        for offset, name in self.fixups:
            if name not in self.labels:
                raise ValueError(f"unknown label: {name}")
            address = self.labels[name]
            self.code[offset] = address & 0xFF
            self.code[offset + 1] = address >> 8
        return bytes(self.code)


def emit_alive_beep(asm: Assembler, *, halt: bool) -> None:
    # Program D57 channel 1 for binary, LSB+MSB, mode 3, divisor 2000.
    asm.mvi_a(0x76)
    asm.out(0x1B)
    asm.mvi_a(TONE_DIVISOR & 0xFF)
    asm.out(0x19)
    asm.mvi_a(TONE_DIVISOR >> 8)
    asm.out(0x19)

    # Stack-free and RAM-free nominal half-second delay.
    asm.lxi_b(DELAY_COUNT)
    asm.label("tone_delay")
    asm.emit(0x0B)  # DCX B
    asm.emit(0x78)  # MOV A,B
    asm.emit(0xB1)  # ORA C
    asm.jnz("tone_delay")

    # Mode 0, LSB-only, count 1 returns OUT1 high after one input clock and
    # leaves a static (silent) speaker-drive level before the checkpoint halt.
    asm.mvi_a(0x50)
    asm.out(0x1B)
    asm.mvi_a(0x01)
    asm.out(0x19)
    if halt:
        asm.emit(0x76)  # HLT; reset IFF is still clear, so execution stops here.


def build() -> tuple[bytes, int]:
    asm = Assembler()
    emit_alive_beep(asm, halt=True)

    code = asm.resolve()
    image = bytearray([0x76] * ROM_SIZE)  # fail-closed HLT fill, not executable RAM use
    image[: len(code)] = code
    image[IDENTITY_OFFSET : IDENTITY_OFFSET + len(IDENTITY)] = IDENTITY
    return bytes(image), len(code)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="fail if the committed image is stale")
    args = parser.parse_args()
    image, code_size = build()
    digest = hashlib.sha256(image).hexdigest()

    if args.check:
        if not OUTPUT.exists():
            raise SystemExit(f"missing generated image: {OUTPUT.relative_to(HERE.parents[2])}")
        if OUTPUT.read_bytes() != image:
            raise SystemExit("diag-d0-alive.bin is stale; run build_d0_alive.py")
        if not README.exists() or digest not in README.read_text():
            raise SystemExit("firmware README does not pin the generated image SHA256")
        action = "checked"
    else:
        OUTPUT.write_bytes(image)
        action = "wrote"
    print(
        f"JUKURAVI-D0-BUILD: {action} {OUTPUT.name} bytes={len(image)} "
        f"code={code_size} sha256={digest}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
