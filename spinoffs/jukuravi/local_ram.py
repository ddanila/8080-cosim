#!/usr/bin/env python3
"""Build and decode compact T36 cooperative-refresh full-RAM probes."""

from __future__ import annotations

from dataclasses import dataclass


REFRESH_API = 0x07A9
RESULT_OFFSET = 0x0300
RESULT_SIZE = 24
COMPLETE = 0xA5
REFRESH_INTERVAL_MASK = 0x7F

PATTERNS = (
    ("zeros", 0),
    ("ones", 1),
    ("checkerboard", 2),
    ("address-xor", 3),
)


@dataclass(frozen=True)
class Stage:
    name: str
    origin: int
    start: int
    end: int

    @property
    def fill_entry(self) -> int:
        return self.origin

    @property
    def verify_entry(self) -> int:
        return self.origin + 3

    @property
    def result_address(self) -> int:
        return self.origin + RESULT_OFFSET


STAGES = (
    Stage("low-resident", 0x4000, 0x5000, 0xC000),
    Stage("high-resident", 0xB000, 0x4000, 0xB000),
)


class Assembler:
    def __init__(self, origin: int) -> None:
        self.origin = origin
        self.code = bytearray()
        self.labels: dict[str, int] = {}
        self.fixups: list[tuple[int, str]] = []

    @property
    def pc(self) -> int:
        return self.origin + len(self.code)

    def emit(self, *values: int) -> None:
        if any(not 0 <= value <= 0xFF for value in values):
            raise ValueError(f"byte outside range: {values}")
        self.code.extend(values)

    def word(self, value: int) -> None:
        self.emit(value & 0xFF, value >> 8)

    def label(self, name: str) -> None:
        if name in self.labels:
            raise ValueError(f"duplicate label: {name}")
        self.labels[name] = self.pc

    def jump(self, opcode: int, label: str) -> None:
        self.emit(opcode, 0, 0)
        self.fixups.append((len(self.code) - 2, label))

    def absolute(self, opcode: int, address: int) -> None:
        self.emit(opcode)
        self.word(address)

    def resolve(self) -> bytes:
        for offset, label in self.fixups:
            if label not in self.labels:
                raise ValueError(f"unknown label: {label}")
            address = self.labels[label]
            self.code[offset] = address & 0xFF
            self.code[offset + 1] = address >> 8
        return bytes(self.code)


def _emit_pattern(asm: Assembler, pattern_id: int, stem: str) -> None:
    """Leave the expected byte for address HL in A."""
    if pattern_id == 0:
        asm.emit(0xAF)  # XRA A
    elif pattern_id == 1:
        asm.emit(0x3E, 0xFF)  # MVI A,FF
    elif pattern_id == 2:
        asm.emit(0x7D, 0xE6, 0x01)  # MOV A,L / ANI 1
        asm.jump(0xCA, f"{stem}_even")  # JZ
        asm.emit(0x3E, 0xAA)
        asm.jump(0xC3, f"{stem}_done")
        asm.label(f"{stem}_even")
        asm.emit(0x3E, 0x55)
        asm.label(f"{stem}_done")
    elif pattern_id == 3:
        asm.emit(0x7C, 0xAD, 0xEE, 0x5A)  # MOV A,H / XRA L / XRI 5A
    else:
        raise ValueError(f"unknown local RAM pattern {pattern_id}")


def _emit_refresh_and_end(
    asm: Assembler, *, stem: str, end: int, loop_label: str
) -> None:
    """Refresh every 128 bytes, then continue unless HL reached end."""
    asm.emit(0x7D, 0xE6, REFRESH_INTERVAL_MASK)  # MOV A,L / ANI 7F
    asm.jump(0xC2, f"{stem}_no_refresh")
    asm.absolute(0xCD, REFRESH_API)  # CALL
    asm.label(f"{stem}_no_refresh")
    asm.emit(0x7C, 0xFE, end >> 8)  # MOV A,H / CPI end high
    asm.jump(0xC2, loop_label)
    asm.emit(0x7D, 0xFE, end & 0xFF)  # MOV A,L / CPI end low
    asm.jump(0xC2, loop_label)


def build_probe(stage: Stage, pattern_id: int) -> bytes:
    """Return a relocatable two-entry fill/verify probe for one safe range."""
    if not (
        0x4000 <= stage.origin < 0xC000
        and 0x4000 <= stage.start < stage.end <= 0xC000
    ):
        raise ValueError("local RAM stage is outside host-safe RAM")
    if stage.start <= stage.origin + RESULT_OFFSET < stage.end:
        raise ValueError("local RAM result overlaps its target range")

    result = stage.result_address
    asm = Assembler(stage.origin)
    asm.jump(0xC3, "fill")
    asm.jump(0xC3, "verify")

    asm.label("fill")
    asm.emit(0x21)
    asm.word(stage.start)  # LXI H,start
    asm.label("fill_loop")
    _emit_pattern(asm, pattern_id, "fill_pattern")
    asm.emit(0x77, 0x23)  # MOV M,A / INX H
    _emit_refresh_and_end(
        asm, stem="fill", end=stage.end, loop_label="fill_loop"
    )
    asm.emit(0xAF, 0xC9)  # XRA A / RET

    asm.label("verify")
    # Reset mutable result fields while retaining the static identity/range.
    asm.emit(0xAF)
    for offset in (4, 10, 11, 12, 13):
        asm.absolute(0x32, result + offset)  # STA
    asm.emit(0x3E, 0xFF)
    for offset in (14, 15, 16, 17):
        asm.absolute(0x32, result + offset)

    asm.emit(0x21)
    asm.word(stage.start)  # LXI H,start
    asm.emit(0x01, 0x00, 0x00)  # LXI B,0 mismatch count
    asm.emit(0x16, 0x00)  # MVI D,0 aggregate XOR mask
    asm.label("verify_loop")
    _emit_pattern(asm, pattern_id, "verify_pattern")
    asm.emit(0x5F, 0x7E, 0xAB)  # MOV E,A / MOV A,M / XRA E
    asm.jump(0xCA, "verify_match")

    # Capture the first mismatch before incrementing BC.
    asm.emit(0x78, 0xB1)  # MOV A,B / ORA C
    asm.jump(0xC2, "verify_not_first")
    asm.emit(0x7D)
    asm.absolute(0x32, result + 14)  # first address low
    asm.emit(0x7C)
    asm.absolute(0x32, result + 15)  # first address high
    asm.emit(0x7B)
    asm.absolute(0x32, result + 16)  # first expected
    asm.emit(0x7E)
    asm.absolute(0x32, result + 17)  # first observed
    asm.label("verify_not_first")
    asm.emit(0x03)  # INX B
    asm.emit(0x7E, 0xAB, 0xB2, 0x57)  # MOV A,M / XRA E / ORA D / MOV D,A

    asm.label("verify_match")
    asm.emit(0x23)  # INX H
    _emit_refresh_and_end(
        asm, stem="verify", end=stage.end, loop_label="verify_loop"
    )
    asm.emit(0x79)
    asm.absolute(0x32, result + 10)  # mismatch count low
    asm.emit(0x78)
    asm.absolute(0x32, result + 11)  # mismatch count high
    asm.emit(0x7A)
    asm.absolute(0x32, result + 12)  # aggregate XOR
    asm.emit(0x3E, COMPLETE)
    asm.absolute(0x32, result + 4)
    asm.emit(0xAF, 0xC9)  # XRA A / RET

    code = bytearray(asm.resolve())
    if len(code) > RESULT_OFFSET:
        raise ValueError("local RAM probe exceeds reserved code area")
    code.extend(b"\x00" * (RESULT_OFFSET - len(code)))
    code.extend(
        b"FRT1"
        + bytes((0, pattern_id))
        + stage.start.to_bytes(2, "little")
        + stage.end.to_bytes(2, "little")
        + b"\x00\x00\x00\x00"
        + b"\xFF\xFF\xFF\xFF"
        + bytes((128, STAGES.index(stage)))
        + b"\x00\x00\x00\x00"
    )
    if len(code) != RESULT_OFFSET + RESULT_SIZE:
        raise AssertionError("local RAM result size differs")
    return bytes(code)


def decode_result(data: bytes, stage: Stage, pattern_id: int) -> dict[str, object]:
    if len(data) != RESULT_SIZE:
        raise ValueError(f"local RAM result is {len(data)} bytes, expected {RESULT_SIZE}")
    if data[:4] != b"FRT1" or data[4] != COMPLETE:
        raise ValueError("local RAM result identity/completion marker differs")
    if data[5] != pattern_id:
        raise ValueError("local RAM result pattern differs")
    if int.from_bytes(data[6:8], "little") != stage.start:
        raise ValueError("local RAM result start differs")
    if int.from_bytes(data[8:10], "little") != stage.end:
        raise ValueError("local RAM result end differs")
    if data[18] != 128 or data[19] != STAGES.index(stage):
        raise ValueError("local RAM result refresh/stage metadata differs")
    mismatches = int.from_bytes(data[10:12], "little")
    first_address = int.from_bytes(data[14:16], "little")
    if mismatches == 0 and data[12] != 0:
        raise ValueError("zero-mismatch local RAM result has nonzero XOR mask")
    if mismatches == 0 and first_address != 0xFFFF:
        raise ValueError("zero-mismatch local RAM result has a first address")
    return {
        "stage": stage.name,
        "start": f"0x{stage.start:04X}",
        "end_exclusive": f"0x{stage.end:04X}",
        "bytes": stage.end - stage.start,
        "mismatching_bytes": mismatches,
        "xor_or": f"0x{data[12]:02X}",
        "first_mismatch": (
            None
            if mismatches == 0
            else {
                "address": f"0x{first_address:04X}",
                "expected": f"0x{data[16]:02X}",
                "observed": f"0x{data[17]:02X}",
                "xor": f"0x{data[16] ^ data[17]:02X}",
            }
        ),
        "refresh_interval_bytes": data[18],
        "verdict": "pass" if mismatches == 0 else "fail",
    }
