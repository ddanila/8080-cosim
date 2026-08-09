#!/usr/bin/env python3
"""Build T34: T31 transport with a clock-safe D55 functional-path test."""

from __future__ import annotations

import argparse
import hashlib

import build_d0_low4k as t31
import build_d0_resilient as base
from build_d0_ram_fallback import (
    PIT_CHIP_BASES,
    PIT_HIGH_COUNT,
    PIT_LOW_COUNT,
)


OUTPUT = base.HERE / "diag-d0-clocked-pit.bin"
DOS_OUTPUT = base.HERE / "dos" / "T34HOST.BIN"
README = base.HERE / "README.md"
ROM_VERSION = 0x1C
IDENTITY = b"JUKURAVI-D0-CLOCKED-PIT-MONITOR-1\0"

# Exact EKTA 3.7 D54 horizontal-chain programming, excluding all D55 writes.
# D54 OUT0 then clocks D55 counter 0, while D54 OUT2 triggers D56 whose Q2_N
# clocks D55 counters 1 and 2 on the exact .009 board topology.
D55_CLOCK_SOURCE_WRITES = (
    (0x13, 0x15), (0x13, 0x53), (0x13, 0x93),
    (0x10, 0x64), (0x11, 0x24), (0x12, 0x08),
)

# At the 2 MHz 8080 clock, MVI B + 40*(DCR/JNZ) is about 300 us.  The factory
# horizontal period is 64 us, so every D55 counting element sees at least four
# complete worst-phase source periods before it is latched and read.
D55_SETTLE_ITERATIONS = 40
ORIGINAL_SLOW_TERMINAL_CODE = base.emit_slow_terminal_code


def emit_d55_settle(asm: base.Assembler, label: str) -> None:
    asm.emit(0x06, D55_SETTLE_ITERATIONS)  # MVI B,n
    asm.label(label)
    asm.emit(0x05)                        # DCR B
    asm.jump(0xC2, label)                 # JNZ


def emit_clocked_nonfatal_pits(asm: base.Assembler) -> None:
    """Test all PIT paths, giving D55 the clocks required by a real 8253."""
    for chip, pit_base in enumerate(PIT_CHIP_BASES):
        bit = (base.FAULT_D54, base.FAULT_D55, base.FAULT_D57)[chip]
        control = pit_base + 3

        if chip == 1:
            for port, value in D55_CLOCK_SOURCE_WRITES:
                asm.mvi_a(value)
                asm.out(port)

        for channel in range(3):
            port = pit_base + channel
            asm.mvi_a(0x20 | (channel << 6))  # MSB-only, binary mode 0
            asm.out(control)
            asm.mvi_a(PIT_HIGH_COUNT)
            asm.out(port)
            if chip == 1:
                emit_d55_settle(asm, f"clocked_d55_{channel}_high_settle")
            asm.mvi_a(channel << 6)           # counter-latch command
            asm.out(control)
            asm.emit(0xDB, port, 0xB7)        # IN / ORA A
            base.conditional_fault(
                asm, 0xF2, f"clocked_pit_{chip}_{channel}_high", bit
            )

            # D55's external clocks are themselves part of the tested path.
            # Opposite-polarity writes on every channel make a missing clock,
            # ignored write, or stale counting element fail independently of
            # whatever value happened to be present before this test.
            if chip == 1:
                asm.mvi_a(0x20 | (channel << 6))
                asm.out(control)
                asm.mvi_a(PIT_LOW_COUNT)
                asm.out(port)
                emit_d55_settle(asm, f"clocked_d55_{channel}_low_settle")
                asm.mvi_a(channel << 6)
                asm.out(control)
                asm.emit(0xDB, port, 0xB7)
                base.conditional_fault(
                    asm, 0xFA, f"clocked_pit_{chip}_{channel}_low", bit
                )

        if chip != 1:
            asm.mvi_a(0x20)
            asm.out(control)
            asm.mvi_a(PIT_LOW_COUNT)
            asm.out(pit_base)
            asm.emit(0xAF)
            asm.out(control)
            asm.emit(0xDB, pit_base, 0xB7)
            base.conditional_fault(asm, 0xFA, f"clocked_pit_{chip}_low", bit)

    # Preserve T31's post-test D57 SOUND/SYNC-B quiescent state.
    for control, port in ((0x50, 0x19), (0x90, 0x1A)):
        asm.mvi_a(control)
        asm.out(0x1B)
        asm.mvi_a(0x01)
        asm.out(port)


def emit_t34_terminal_code(asm: base.Assembler, code: int, stem: str) -> int:
    # T31/T34 jump directly into the verified low-4K loader and never execute
    # the later full-workspace path. Keep its fixup target but reclaim the
    # unreachable grouped-tone body for the two extra D55 polarity predicates.
    if code == base.WORKSPACE_FAILURE_CODE:
        halt = asm.pc
        asm.emit(0x76)
        return halt
    return ORIGINAL_SLOW_TERMINAL_CODE(asm, code, stem)


def build():
    saved = (
        t31.ROM_VERSION,
        t31.IDENTITY,
        base.emit_nonfatal_pits,
        base.emit_slow_terminal_code,
    )
    try:
        t31.ROM_VERSION = ROM_VERSION
        t31.IDENTITY = IDENTITY
        base.emit_nonfatal_pits = emit_clocked_nonfatal_pits
        base.emit_slow_terminal_code = emit_t34_terminal_code
        image, metadata = t31.build()
        metadata.update({
            "d55_clock_source_writes": list(D55_CLOCK_SOURCE_WRITES),
            "d55_settle_iterations": D55_SETTLE_ITERATIONS,
            "d55_settle_us_nominal": 300,
            "d55_source_period_us": 64,
        })
        return image, metadata
    finally:
        (
            t31.ROM_VERSION,
            t31.IDENTITY,
            base.emit_nonfatal_pits,
            base.emit_slow_terminal_code,
        ) = saved


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    image, metadata = build()
    digest = hashlib.sha256(image).hexdigest()
    if args.check:
        for output in (OUTPUT, DOS_OUTPUT):
            if not output.exists() or output.read_bytes() != image:
                raise SystemExit(f"{output.name} is missing or stale")
        if not README.exists() or digest not in README.read_text():
            raise SystemExit("firmware README does not pin the T34 image SHA256")
        action = "checked"
    else:
        OUTPUT.write_bytes(image)
        DOS_OUTPUT.write_bytes(image)
        action = "wrote"
    print(
        f"JUKURAVI-D0-CLOCKED-PIT-BUILD: {action} {OUTPUT.name} "
        f"bytes={len(image)} loader_end={int(metadata['loader_extension_end']):04X} "
        f"self_crc16={metadata['checksum']:04X} sha256={digest}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
