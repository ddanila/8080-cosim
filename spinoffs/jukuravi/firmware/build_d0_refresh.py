#!/usr/bin/env python3
"""Build historical T35 with its now-known high-byte refresh bug."""

from __future__ import annotations

import argparse
import hashlib

import build_d0_clocked_pit as t34
import build_d0_low4k as t31
import build_d0_resilient as base
import protocol
from build_d0_ram_fallback import lxi_h, lxi_h_label
from build_d2_loader import call
from build_d2_loader_v2 import lda, sta, store_immediate
from build_d6_loader_v6 import (
    REFRESH_COUNTER,
    REFRESH_MODE,
    emit_loader as emit_loader_v6,
)


OUTPUT = base.HERE / "diag-d0-refresh.bin"
DOS_OUTPUT = base.HERE / "dos" / "T35HOST.BIN"
README = base.HERE / "README.md"
DOS_MANIFEST = base.HERE / "dos" / "SHA256.TXT"
DOS_INFO = base.HERE / "dos" / "T35INFO.TXT"
ROM_VERSION = 0x1D
IDENTITY = b"JUKURAVI-D0-REFRESH-MONITOR-1\0"

REFRESH_ENABLED_SIGNATURE = bytes((0xA5, 0x5A, 0xC3))
REFRESH_DISABLED_SIGNATURE = bytes((0x5A, 0xA5, 0x3C))
REFRESH_POLICY_FLAGS = 0x07  # fail-safe, all 128 rows, cooperative public API
REFRESH_RESPONSE_BYTES = 9
REFRESH_ROWS = protocol.LOADER_V2_REFRESH_ROWS
REFRESH_ROW_START = protocol.LOADER_V2_REFRESH_ROW_START
REFRESH_BASE_ADDRESS = REFRESH_ROW_START << 8
REFRESH_INCREMENT_OPCODE = 0x24  # INR H: historical T35 physical-row bug
REFRESH_ADDRESS_AXIS = "cpu-high-byte"
REFRESH_GROUPS = REFRESH_ROWS // 4
REFRESH_ENABLED_TSTATES = 2115
CS00024_CPU_HZ = 1_714_065


def fixed_frames() -> dict[str, bytes]:
    ready_payload = bytes(
        (
            protocol.LOADER_V2_API_VERSION,
            protocol.LOADER_V2_MAX_DATA,
            protocol.LOADER_API_BASE >> 8,
            protocol.LOADER_API_BASE & 0xFF,
            protocol.LOADER_V2_T35_CAPABILITIES >> 8,
            protocol.LOADER_V2_T35_CAPABILITIES & 0xFF,
            protocol.LOADER_V2_LOAD_MIN >> 8,
            protocol.LOADER_V2_LOAD_END >> 8,
            protocol.LOADER_V2_WORKSPACE_BASE >> 8,
            protocol.LOADER_V2_WORKSPACE_END >> 8,
            protocol.LOADER_V2_T35_BOOT_VOTES,
        )
    )
    return {
        "ready": protocol.encode_frame(protocol.TYPE_LOADER_READY, ready_payload),
        "bad_crc": protocol.encode_frame(
            protocol.TYPE_LOADER_ERROR,
            bytes((protocol.LOADER_STATUS_BAD_CRC,)),
        ),
    }


def emit_pre_table(asm: base.Assembler) -> dict[str, int | bytes]:
    """Use T34's final low-ROM gap for the callable refresh primitive."""
    if asm.pc != protocol.LOADER_V2_REFRESH_API:
        raise ValueError(
            f"T35 refresh API moved from {protocol.LOADER_V2_REFRESH_API:04X}h "
            f"to {asm.pc:04X}h"
        )
    start = asm.pc
    asm.label("t35_refresh")
    asm.emit(0xC5, 0xE5)  # PUSH B / PUSH H

    # Only the complete three-byte disable signature suppresses refresh. Any
    # torn write, single-byte corruption, power-up residue, or RESYNC value
    # takes the safe refresh-on path.
    for index, value in enumerate(REFRESH_DISABLED_SIGNATURE):
        lda(asm, REFRESH_MODE + index)
        asm.emit(0xFE, value)
        asm.jump(0xC2, "t35_refresh_sweep")
    asm.jump(0xC3, "t35_refresh_exit")

    asm.label("t35_refresh_sweep")
    lxi_h(asm, REFRESH_BASE_ADDRESS)
    asm.emit(0x06, REFRESH_GROUPS)  # MVI B,32 groups of four rows
    asm.label("t35_refresh_rows")
    for _ in range(4):
        asm.emit(0x7E, REFRESH_INCREMENT_OPCODE)  # MOV A,M / legacy INR H
    asm.emit(0x05)
    asm.jump(0xC2, "t35_refresh_rows")
    asm.label("t35_refresh_exit")
    asm.emit(0xE1, 0xC1, 0xC9)  # POP H / POP B / RET

    # Keep the fixed send entry points low; their frame bytes live in the
    # guarded upper-ROM extension, reclaiming enough low-ROM space for calls
    # from every potentially blocking serial wait.
    frames = fixed_frames()
    for stem, frame in frames.items():
        asm.label(f"t28_send_{stem}")
        lxi_h_label(asm, f"t28_frame_{stem}")
        asm.emit(0x06, len(frame))
        asm.jump(0xC3, "t28_send_table")
    frame_offsets: dict[str, int] = {}
    for stem, frame in frames.items():
        asm.label(f"t28_frame_{stem}")
        frame_offsets[stem] = asm.pc
        asm.emit(*frame)

    if asm.pc > base.ROM_CHECKSUM_END:
        raise ValueError("T35 refresh primitive does not fit below 0800h")
    return {
        "refresh_api": start,
        "refresh_pre_table_end": asm.pc,
        "refresh_enabled_tstates": REFRESH_ENABLED_TSTATES,
        "refresh_ready_frame_offset": frame_offsets["ready"],
        "refresh_bad_crc_frame_offset": frame_offsets["bad_crc"],
    }


def emit_copy_signature(asm: base.Assembler, label: str) -> None:
    lxi_h_label(asm, label)
    asm.emit(0x11, REFRESH_MODE & 0xFF, REFRESH_MODE >> 8)  # LXI D
    asm.emit(0x06, len(REFRESH_ENABLED_SIGNATURE))
    asm.label(f"{label}_copy")
    asm.emit(0x7E, 0x12, 0x23, 0x13, 0x05)
    asm.jump(0xC2, f"{label}_copy")


def emit_post_loader(asm: base.Assembler) -> dict[str, int | bytes]:
    """Emit T35's optional upper-ROM refresh configuration command."""
    handler_start = asm.pc
    asm.label("t35_refresh_command")
    lda(asm, base.LOADER_WORKSPACE_BASE + 0x113)  # STATE_LENGTH
    asm.emit(0xFE, 4)
    asm.jump(0xC2, "t28_bad_length")
    lda(asm, base.LOADER_WORKSPACE_BASE + 3)  # LOADER_BUFFER + operation
    asm.emit(0xFE, protocol.LOADER_V2_REFRESH_RESET_COUNTER + 1)
    asm.jump(0xD2, "t28_bad_config")
    asm.emit(0xFE, protocol.LOADER_V2_REFRESH_QUERY)
    asm.jump(0xCA, "t35_refresh_response")
    asm.emit(0xFE, protocol.LOADER_V2_REFRESH_ENABLE)
    asm.jump(0xCA, "t35_refresh_enable")
    asm.emit(0xFE, protocol.LOADER_V2_REFRESH_DISABLE)
    asm.jump(0xCA, "t35_refresh_disable")
    asm.emit(0xAF)
    sta(asm, REFRESH_COUNTER)
    sta(asm, REFRESH_COUNTER + 1)
    asm.jump(0xC3, "t35_refresh_response")

    asm.label("t35_refresh_enable")
    emit_copy_signature(asm, "t35_refresh_enabled_signature")
    asm.jump(0xC3, "t35_refresh_response")
    asm.label("t35_refresh_disable")
    emit_copy_signature(asm, "t35_refresh_disabled_signature")

    asm.label("t35_refresh_response")
    store_immediate(
        asm, base.LOADER_WORKSPACE_BASE + 0x116, REFRESH_RESPONSE_BYTES
    )  # STATE_COUNT
    store_immediate(
        asm, base.LOADER_WORKSPACE_BASE + 8, protocol.LOADER_V2_REFRESH_VERSION
    )
    call(asm, "t35_refresh_is_enabled")
    sta(asm, base.LOADER_WORKSPACE_BASE + 9)
    store_immediate(asm, base.LOADER_WORKSPACE_BASE + 10, REFRESH_POLICY_FLAGS)
    store_immediate(
        asm,
        base.LOADER_WORKSPACE_BASE + 11,
        REFRESH_ROW_START,
    )
    store_immediate(asm, base.LOADER_WORKSPACE_BASE + 12, REFRESH_ROWS)
    store_immediate(
        asm, base.LOADER_WORKSPACE_BASE + 13, protocol.LOADER_V2_REFRESH_API >> 8
    )
    store_immediate(
        asm,
        base.LOADER_WORKSPACE_BASE + 14,
        protocol.LOADER_V2_REFRESH_API & 0xFF,
    )
    asm.emit(0x2A, REFRESH_COUNTER & 0xFF, REFRESH_COUNTER >> 8)
    asm.emit(0x7C)
    sta(asm, base.LOADER_WORKSPACE_BASE + 15)
    asm.emit(0x7D)
    sta(asm, base.LOADER_WORKSPACE_BASE + 16)
    call(asm, "t28_send_data")
    asm.jump(0xC3, "t28_loop")

    asm.label("t35_refresh_is_enabled")
    for index, value in enumerate(REFRESH_DISABLED_SIGNATURE):
        lda(asm, REFRESH_MODE + index)
        asm.emit(0xFE, value)
        asm.jump(0xC2, "t35_refresh_enabled")
    asm.emit(0xAF, 0xC9)
    asm.label("t35_refresh_enabled")
    asm.emit(0x3E, 1, 0xC9)

    asm.label("t35_refresh_enabled_signature")
    asm.emit(*REFRESH_ENABLED_SIGNATURE)
    asm.label("t35_refresh_disabled_signature")
    asm.emit(*REFRESH_DISABLED_SIGNATURE)
    return {
        "refresh_handler_start": handler_start,
        "refresh_handler_end": asm.pc,
        "refresh_ready_frame": fixed_frames()["ready"],
        "refresh_bad_crc_frame": fixed_frames()["bad_crc"],
    }


def build():
    saved = (
        t31.ROM_VERSION,
        t31.IDENTITY,
        t31.LOADER_EMITTER,
        t31.LOADER_SYMBOL_REPETITIONS,
        base.emit_nonfatal_pits,
        base.emit_slow_terminal_code,
        base.PRE_TABLE_EMITTER,
        base.POST_LOADER_EMITTER,
    )
    try:
        t31.ROM_VERSION = ROM_VERSION
        t31.IDENTITY = IDENTITY
        t31.LOADER_EMITTER = emit_loader_v6
        t31.LOADER_SYMBOL_REPETITIONS = protocol.LOADER_V2_T35_BOOT_VOTES
        base.emit_nonfatal_pits = t34.emit_clocked_nonfatal_pits
        base.emit_slow_terminal_code = t34.emit_t34_terminal_code
        base.PRE_TABLE_EMITTER = emit_pre_table
        base.POST_LOADER_EMITTER = emit_post_loader
        image, metadata = t31.build()
        metadata.update(
            {
                "d55_clock_source_writes": list(t34.D55_CLOCK_SOURCE_WRITES),
                "d55_settle_iterations": t34.D55_SETTLE_ITERATIONS,
                "refresh_mode_address": REFRESH_MODE,
                "refresh_counter_address": REFRESH_COUNTER,
                "refresh_disabled_signature": REFRESH_DISABLED_SIGNATURE,
                "refresh_rows": REFRESH_ROWS,
                "refresh_row_start": REFRESH_ROW_START,
                "refresh_base_address": REFRESH_BASE_ADDRESS,
                "refresh_increment_opcode": REFRESH_INCREMENT_OPCODE,
                "refresh_address_axis": REFRESH_ADDRESS_AXIS,
                "refresh_worst_ms_cs00024": (
                    REFRESH_ENABLED_TSTATES * 1000.0 / CS00024_CPU_HZ
                ),
            }
        )
        if metadata["loader_extension_end"] > 0x1000:
            raise ValueError("T35 blocking transport core crossed 1000h")
        return image, metadata
    finally:
        (
            t31.ROM_VERSION,
            t31.IDENTITY,
            t31.LOADER_EMITTER,
            t31.LOADER_SYMBOL_REPETITIONS,
            base.emit_nonfatal_pits,
            base.emit_slow_terminal_code,
            base.PRE_TABLE_EMITTER,
            base.POST_LOADER_EMITTER,
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
            raise SystemExit("firmware README does not pin the T35 image SHA256")
        manifest_line = f"{digest}  {DOS_OUTPUT.name}"
        if not DOS_MANIFEST.exists() or manifest_line not in DOS_MANIFEST.read_text():
            raise SystemExit("DOS SHA256 manifest does not pin T35HOST.BIN")
        info = "" if not DOS_INFO.exists() else DOS_INFO.read_text()
        for required in (
            f"ROM version: {ROM_VERSION:02X}h",
            f"Self CRC16: {int(metadata['checksum']):04X}h",
            f"SHA256: {digest}",
            f"CALL {protocol.LOADER_V2_REFRESH_API:04X}h",
        ):
            if required not in info:
                raise SystemExit(f"T35INFO.TXT is missing {required!r}")
        action = "checked"
    else:
        OUTPUT.write_bytes(image)
        DOS_OUTPUT.write_bytes(image)
        action = "wrote"
    print(
        f"JUKURAVI-D0-REFRESH-BUILD: {action} {OUTPUT.name} "
        f"bytes={len(image)} loader_end={int(metadata['loader_extension_end']):04X} "
        f"refresh_api={int(metadata['refresh_api']):04X} "
        f"refresh_ms={float(metadata['refresh_worst_ms_cs00024']):.3f} "
        f"self_crc16={int(metadata['checksum']):04X} sha256={digest}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
