#!/usr/bin/env python3
"""Build the exact-EktaSoft raster-arm and unrefreshed-hold snippets.

These snippets implement the CS00024 video-slot refresh experiment described
in RASTER-REFRESH-EXPERIMENT.md. The arm snippet replays the exact D54/D55
PIT programming bytes that `roms/ekta37.bin` executes at boot (offsets
`01D4h..0221h`, filtered to video ports `10h..17h`), which is the same
recovered contract that `docs/video-pit-timing.md` proves drives the
autonomous D54/D55/D56/D34_SYNC raster chain. The optional SYNC_B stage adds
only EktaSoft's D57 channel-2 write (`B0h` control, `FFFFh` count). The D57
channel-0 (USART clock) and channel-1 (speaker) writes are deliberately
excluded: replaying them could disturb the live diagnostic serial link.

The hold snippet is a register-only busy wait. While it runs, the loader is
not in control, so T36's software refresh is provably absent; its own
instruction fetches keep only rows `40h..54h` alive. Every other physical
MK4564 row holds known, untouched content through the hold: the 64-byte
marker at `4D00h` covers rows `00h..3Fh`, and the padded hold image covers
rows `55h..7Fh` (plus rows `00h..3Fh` again at `4080h..40BFh`).
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path

HERE = Path(__file__).resolve().parent
EKTA37 = HERE.parent.parent / "roms" / "ekta37.bin"
EKTA37_SHA256 = "fc44df76b2601ab81745f2512edb7a56bb24dca6419e7173a5bf11cae4c1fc27"

PIT_SEQUENCE_START = 0x01D4
PIT_SEQUENCE_END = 0x0222

D54_PORTS = frozenset(range(0x10, 0x14))
D55_PORTS = frozenset(range(0x14, 0x18))
RASTER_PORTS = D54_PORTS | D55_PORTS
D57_CONTROL_PORT = 0x1B
D57_CH2_DATA_PORT = 0x1A

ARM_VARIANTS = ("raster", "raster-syncb")
ARM_ADDRESS = 0x4100
ARM_RETURN_A = 0x41

HOLD_ADDRESS = 0x4040
HOLD_IMAGE_SIZE = 128
HOLD_RETURN_A = 0x52
HOLD_FILL_XOR = 0xC3

MARKER_ADDRESS = 0x4D00
# retention.py's proven 32-byte marker followed by its bitwise complement,
# spanning all 64 physical rows 00h..3Fh from MARKER_ADDRESS.
_MARKER_HALF = bytes.fromhex(
    "00FF55AA966969963CC3C33C0FF0F00F"
    "0123456789ABCDEFFEDCBA9876543210"
)
MARKER = _MARKER_HALF + bytes(value ^ 0xFF for value in _MARKER_HALF)

ROW_MASK = 0x7F
ROW_COUNT = 128

# 8080 T-states for the hold loop pieces.
_TSTATES_LXI = 10
_TSTATES_INNER_ITERATION = 24  # DCX B / MOV A,B / ORA C / JNZ
_TSTATES_OUTER_OVERHEAD = 34  # LXI B / DCX D / MOV A,D / ORA E / JNZ
_TSTATES_EXIT = 17  # MVI A / RET
TSTATES_PER_OUTER = 0x10000 * _TSTATES_INNER_ITERATION + _TSTATES_OUTER_OVERHEAD

# Effective RAM-loop execution rate; CS00024 measured 1.701558..1.714065 MHz
# across the T34..T36 sessions.
DEFAULT_EFFECTIVE_MHZ = 1.702


@dataclass(frozen=True)
class PitWrite:
    offset: int
    port: int
    value: int
    reused_a: bool

    def describe(self) -> dict[str, object]:
        return {
            "rom_offset": f"0x{self.offset:04X}",
            "port": f"0x{self.port:02X}",
            "value": f"0x{self.value:02X}",
            "reused_a": self.reused_a,
        }


def load_ekta37() -> bytes:
    rom = EKTA37.read_bytes()
    digest = hashlib.sha256(rom).hexdigest()
    if digest != EKTA37_SHA256:
        raise ValueError(
            f"roms/ekta37.bin SHA256 {digest} differs from pinned {EKTA37_SHA256}"
        )
    return rom


def decode_pit_writes(rom: bytes | None = None) -> tuple[PitWrite, ...]:
    """Decode the boot PIT write sequence exactly as EktaSoft executes it."""
    if rom is None:
        rom = load_ekta37()
    writes: list[PitWrite] = []
    accumulator: int | None = None
    loaded_by_mvi = False
    offset = PIT_SEQUENCE_START
    while offset < PIT_SEQUENCE_END:
        opcode = rom[offset]
        if opcode == 0x3E:  # MVI A,value
            accumulator = rom[offset + 1]
            loaded_by_mvi = True
            offset += 2
        elif opcode == 0xD3:  # OUT port
            if accumulator is None:
                raise ValueError(f"OUT at {offset:04X}h before any MVI A")
            writes.append(
                PitWrite(offset, rom[offset + 1], accumulator, not loaded_by_mvi)
            )
            loaded_by_mvi = False
            offset += 2
        else:
            raise ValueError(
                f"unexpected opcode {opcode:02X}h at {offset:04X}h in the "
                "EktaSoft PIT window"
            )
    return tuple(writes)


def raster_writes(rom: bytes | None = None) -> tuple[PitWrite, ...]:
    """The D54/D55 video-timing subset, in EktaSoft's exact order."""
    return tuple(
        write for write in decode_pit_writes(rom) if write.port in RASTER_PORTS
    )


def syncb_writes(rom: bytes | None = None) -> tuple[PitWrite, ...]:
    """EktaSoft's D57 channel-2 (SYNC_B) writes only.

    Channel selection lives in control bits 7:6; only `B0h` (channel 2) is
    kept. The channel-0 USART clock and channel-1 speaker writes must never
    be replayed over the live diagnostic link.
    """
    kept: list[PitWrite] = []
    for write in decode_pit_writes(rom):
        if write.port == D57_CONTROL_PORT and (write.value & 0xC0) == 0x80:
            kept.append(write)
        elif write.port == D57_CH2_DATA_PORT:
            kept.append(write)
    return tuple(kept)


def arm_writes(variant: str, rom: bytes | None = None) -> tuple[PitWrite, ...]:
    if variant not in ARM_VARIANTS:
        raise ValueError(f"unknown arm variant: {variant}")
    if rom is None:
        rom = load_ekta37()
    writes = raster_writes(rom)
    if variant == "raster-syncb":
        writes += syncb_writes(rom)
    return writes


def build_arm_snippet(variant: str, rom: bytes | None = None) -> bytes:
    """Unrolled MVI/OUT replay of the selected writes, ending in RET.

    A bare OUT that reused the previous accumulator value in ROM stays a
    bare OUT here whenever the preceding kept write left A at that value,
    preserving EktaSoft's exact instruction shape.
    """
    code = bytearray()
    last_a: int | None = None
    for write in arm_writes(variant, rom):
        if not (write.reused_a and last_a == write.value):
            code.extend((0x3E, write.value))  # MVI A,value
        code.extend((0xD3, write.port))  # OUT port
        last_a = write.value
    code.extend((0x3E, ARM_RETURN_A, 0xC9))  # MVI A / RET
    return bytes(code)


def build_hold_code(outer: int) -> bytes:
    """Register-only busy wait: outer x 65,536 inner DCX iterations."""
    if not 1 <= outer <= 0xFFFF:
        raise ValueError("outer count must be 1..65535")
    inner_label = HOLD_ADDRESS + 6
    outer_label = HOLD_ADDRESS + 3
    code = bytes(
        (
            0x11, outer & 0xFF, outer >> 8,  # LXI D,outer
            0x01, 0x00, 0x00,  # LXI B,0 (65,536 inner iterations)
            0x0B,  # DCX B
            0x78,  # MOV A,B
            0xB1,  # ORA C
            0xC2, inner_label & 0xFF, inner_label >> 8,  # JNZ inner
            0x1B,  # DCX D
            0x7A,  # MOV A,D
            0xB3,  # ORA E
            0xC2, outer_label & 0xFF, outer_label >> 8,  # JNZ outer
            0x3E, HOLD_RETURN_A,  # MVI A,return marker
            0xC9,  # RET
        )
    )
    return code


def hold_fill_byte(address: int) -> int:
    return (address & 0xFF) ^ HOLD_FILL_XOR


def build_hold_image(outer: int) -> bytes:
    code = build_hold_code(outer)
    image = bytearray(code)
    for index in range(len(code), HOLD_IMAGE_SIZE):
        image.append(hold_fill_byte(HOLD_ADDRESS + index))
    return bytes(image)


def executed_rows(outer: int) -> tuple[int, ...]:
    """Rows the hold's own entry/loop/exit fetches keep alive."""
    length = len(build_hold_code(outer))
    return tuple((HOLD_ADDRESS + index) & ROW_MASK for index in range(length))


def hold_tstates(outer: int) -> int:
    return _TSTATES_LXI + outer * TSTATES_PER_OUTER + _TSTATES_EXIT


def hold_seconds(outer: int, effective_mhz: float) -> float:
    return hold_tstates(outer) / (effective_mhz * 1_000_000.0)


def outer_for_seconds(seconds: float, effective_mhz: float) -> int:
    if seconds <= 0 or effective_mhz <= 0:
        raise ValueError("hold seconds and effective MHz must be positive")
    outer = round(seconds * effective_mhz * 1_000_000.0 / TSTATES_PER_OUTER)
    return max(1, min(0xFFFF, outer))


def classify_readback(
    expected: bytes, observed: bytes, base_address: int
) -> dict[str, object]:
    """Compare a post-hold readback and map differences to physical rows."""
    if len(expected) != len(observed):
        raise ValueError("readback length differs from expected")
    differing: list[dict[str, object]] = []
    rows_failed: set[int] = set()
    for index, (want, got) in enumerate(zip(expected, observed)):
        if want != got:
            address = base_address + index
            rows_failed.add(address & ROW_MASK)
            differing.append(
                {
                    "address": f"0x{address:04X}",
                    "expected": f"0x{want:02X}",
                    "observed": f"0x{got:02X}",
                    "xor": f"0x{want ^ got:02X}",
                    "row": address & ROW_MASK,
                }
            )
    return {
        "bytes": len(expected),
        "differing_bytes": len(differing),
        "rows_failed": sorted(rows_failed),
        "differences": differing,
        "verdict": "pass" if not differing else "fail",
    }


def row_coverage(outer: int) -> dict[str, object]:
    """Account for all 128 physical rows in one stage."""
    marker_rows = {(MARKER_ADDRESS + i) & ROW_MASK for i in range(len(MARKER))}
    hold_rows = {(HOLD_ADDRESS + i) & ROW_MASK for i in range(HOLD_IMAGE_SIZE)}
    live = set(executed_rows(outer))
    evidence = (marker_rows | hold_rows) - live
    return {
        "marker_rows": sorted(marker_rows),
        "hold_image_rows": sorted(hold_rows),
        "live_rows_excluded": sorted(live),
        "evidence_rows": sorted(evidence),
        "complete": len(evidence | live) == ROW_COUNT,
    }
