#!/usr/bin/env python3
"""Build the robust, RAM-independent full Jukuravi diagnostic ROM."""

from __future__ import annotations

import argparse
import hashlib
import sys
from pathlib import Path

from build_d0_alive import Assembler, ROM_SIZE, emit_alive_beep
from build_d0_cpu import (EXPECTED_SIGNATURE, FAIL_TONE_DIVISOR,
                          emit_cpu_self_test, emit_failure_tone)
from build_d0_ram_fallback import (
    FALLBACK_WINDOWS, FRAMEBUFFER_BASE, FRAMEBUFFER_BYTES, PIC_COMMAND_PORT,
    PIC_DATA_PORT, PIC_ICW1, PIC_ICW2,
    PIC_SAFE_MASK, PIT_CHIP_BASES, PIT_HIGH_COUNT, PIT_LOW_COUNT,
    PPI1_ALL_INPUT, PPI1_ALL_OUTPUT, PPI1_CONTROL_PORT, PPI1_PORTS,
    ROM_CHECKSUM_END, ROM_CHECKSUM_OFFSET, ROM_CHECKSUM_START,
    SLOW_REPORT_PAUSE_COUNT, WINDOWS_FOUND_DIVISOR,
    emit_compact_fixed_window_tests, emit_register_delay,
    emit_slow_grouped_pulse_loop, lxi_h,
)
from build_d2_loader import emit_loader
from build_d0_serial import (SERIAL_DEAD_TONE_DIVISOR, emit_ack_rx,
                             emit_status_wait, emit_table_tx, emit_train)
from build_d0_usart_local import emit_local_usart_test

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import protocol  # noqa: E402

OUTPUT = HERE / "diag-d0-stopwait.bin"
README = HERE / "README.md"
IDENTITY_OFFSET = 0x1F00
IDENTITY = b"JUKURAVI-D0-STOPWAIT-SERIAL-1\0"
ROM_VERSION = 16
ENTRY_OFFSET = ROM_CHECKSUM_START
CRC_TABLE_OFFSET = 0x0900

FAULT_PIC = 0x01
FAULT_PPI = 0x02
FAULT_D54 = 0x04
FAULT_D55 = 0x08
FAULT_D57 = 0x10
RAM_STATUS_FLAG = 0x80
UART_FAILURE_CODE = 6
RAM_FAILURE_CODE = 7
WORKSPACE_FAILURE_CODE = 8
ACK_SCAN_BUDGET = 72  # eight complete nine-byte ACK frames


def mark_fault(asm: Assembler, bit: int) -> None:
    asm.emit(0x7B, 0xF6, bit, 0x5F)  # MOV A,E / ORI bit / MOV E,A


def conditional_fault(asm: Assembler, opcode: int, label: str, bit: int) -> None:
    asm.jump(opcode, f"{label}_bad")
    asm.jump(0xC3, f"{label}_done")
    asm.label(f"{label}_bad")
    mark_fault(asm, bit)
    asm.label(f"{label}_done")


def emit_nonfatal_pic(asm: Assembler) -> None:
    asm.mvi_a(PIC_ICW1); asm.out(PIC_COMMAND_PORT)
    asm.mvi_a(PIC_ICW2); asm.out(PIC_DATA_PORT)
    asm.emit(0xAF); asm.out(PIC_DATA_PORT)
    asm.emit(0xDB, PIC_DATA_PORT, 0xB7)
    conditional_fault(asm, 0xC2, "best_pic_zero", FAULT_PIC)
    asm.mvi_a(0xFF); asm.out(PIC_DATA_PORT)
    asm.emit(0xDB, PIC_DATA_PORT, 0x3C)
    conditional_fault(asm, 0xC2, "best_pic_ff", FAULT_PIC)
    asm.mvi_a(PIC_SAFE_MASK); asm.out(PIC_DATA_PORT)


def emit_nonfatal_ppi(asm: Assembler) -> None:
    asm.mvi_a(PPI1_ALL_OUTPUT); asm.out(PPI1_CONTROL_PORT)
    for index, port in enumerate(PPI1_PORTS):
        asm.emit(0xAF); asm.out(port)
        asm.emit(0xDB, port, 0xB7)
        conditional_fault(asm, 0xC2, f"best_ppi_{index}_zero", FAULT_PPI)
        asm.mvi_a(0xFF); asm.out(port)
        asm.emit(0xDB, port, 0x3C)
        conditional_fault(asm, 0xC2, f"best_ppi_{index}_ff", FAULT_PPI)
    asm.mvi_a(PPI1_ALL_INPUT); asm.out(PPI1_CONTROL_PORT)
    asm.emit(0xAF)
    for port in PPI1_PORTS:
        asm.out(port)


def emit_nonfatal_pits(asm: Assembler) -> None:
    for chip, base in enumerate(PIT_CHIP_BASES):
        bit = (FAULT_D54, FAULT_D55, FAULT_D57)[chip]
        control = base + 3
        for channel in range(3):
            port = base + channel
            asm.mvi_a(0x20 | (channel << 6)); asm.out(control)
            asm.mvi_a(PIT_HIGH_COUNT); asm.out(port)
            asm.mvi_a(channel << 6); asm.out(control)
            asm.emit(0xDB, port, 0xB7)
            conditional_fault(asm, 0xF2, f"best_pit_{chip}_{channel}_high", bit)
        asm.mvi_a(0x20); asm.out(control)
        asm.mvi_a(PIT_LOW_COUNT); asm.out(base)
        asm.emit(0xAF); asm.out(control)
        asm.emit(0xDB, base, 0xB7)
        conditional_fault(asm, 0xFA, f"best_pit_{chip}_low", bit)

    # Restore D57 SOUND and SYNC-B before its channel 0 becomes the baud clock.
    for control, port in ((0x50, 0x19), (0x90, 0x1A)):
        asm.mvi_a(control); asm.out(0x1B)
        asm.mvi_a(0x01); asm.out(port)


def tx_byte(asm: Assembler, stem: str, source: str | int,
            failure_label: str = "uart_dead") -> None:
    emit_status_wait(asm, stem=stem, mask=0x01, failure_label=failure_label)
    if source == "e":
        asm.emit(0x7B)  # MOV A,E
    elif source == "m":
        asm.emit(0x7E)  # MOV A,M
    else:
        asm.mvi_a(int(source))
    asm.out(0x08)


def emit_dynamic_status(asm: Assembler, stem: str) -> None:
    for index, value in enumerate((0xA5, 0x5A, protocol.TYPE_DIAG_STATUS, 0x01)):
        tx_byte(asm, f"{stem}_{index}", value)
    tx_byte(asm, f"{stem}_value", "e")
    asm.mvi_a(CRC_TABLE_OFFSET >> 8)
    asm.emit(0x67, 0x6B)  # MOV H,A / MOV L,E
    tx_byte(asm, f"{stem}_crc", "m")


def emit_rx_drain(asm: Assembler, stem: str) -> None:
    """Discard at most 255 stale bytes without waiting for new input."""
    asm.emit(0x16, 0xFF)  # MVI D,255
    asm.label(f"{stem}_drain")
    asm.emit(0xDB, 0x09, 0xE6, 0x02)  # IN status / ANI RxRDY
    asm.jump(0xCA, f"{stem}_drain_done")
    asm.emit(0xDB, 0x08, 0x15)  # IN data / DCR D
    asm.jump(0xC2, f"{stem}_drain")
    asm.label(f"{stem}_drain_done")


def emit_stopwait_ack(asm: Assembler, count: int) -> None:
    """Challenge/echo every ACK byte with eight bounded attempts per byte."""
    label_address = lambda opcode, label: (
        asm.emit(opcode, 0x00, 0x00), asm.fixups.append((asm.pc - 2, label))
    )
    asm.emit(0x43)                         # MOV B,E: preserve fault bitmap
    label_address(0x21, "ack_expected")
    asm.label("stopwait_next")
    asm.emit(0x0E, 0x08)                   # MVI C,8 attempts
    asm.label("stopwait_attempt")
    # Local TxRDY already passed; an asserted looped CTS is required.
    asm.emit(0xDB, 0x09, 0xE6, 0x01)
    asm.jump(0xCA, "stopwait_attempt")
    asm.emit(0x7E, 0xD3, 0x08)             # MOV A,M / OUT data
    # DE provides a long per-attempt receive timeout (~0.4 s nominal).
    asm.emit(0x11, 0x00, 0x40)             # LXI D,4000h
    asm.label("stopwait_rx_poll")
    asm.emit(0xDB, 0x09, 0xE6, 0x02)
    asm.jump(0xC2, "stopwait_rx_seen")
    asm.emit(0x1B, 0x7A, 0xB3)             # DCX D / MOV A,D / ORA E
    asm.jump(0xC2, "stopwait_rx_poll")
    asm.jump(0xC3, "stopwait_retry")
    asm.label("stopwait_rx_seen")
    asm.emit(0xDB, 0x08, 0xBE)             # IN data / CMP M
    asm.jump(0xCA, "stopwait_match")
    asm.label("stopwait_retry")
    asm.emit(0x0D)                         # DCR C
    asm.jump(0xC2, "stopwait_attempt")
    asm.jump(0xC3, "uart_dead")
    asm.label("stopwait_match")
    asm.emit(0x23, 0x7D)                   # INX H / MOV A,L
    # ACK table is wholly within page 08; compare against its fixed end.
    asm.emit(0xFE, (0x0809 + count) & 0xFF)  # CPI end of ACK table
    asm.jump(0xC2, "stopwait_next")
    asm.emit(0x58)                         # MOV E,B: restore fault bitmap


def emit_slow_terminal_code(asm: Assembler, code: int, stem: str) -> int:
    emit_register_delay(asm, stem=f"{stem}_lead_pause",
                        count=SLOW_REPORT_PAUSE_COUNT)
    asm.emit(0x16, code)
    emit_slow_grouped_pulse_loop(
        asm, stem=stem, divisor=WINDOWS_FOUND_DIVISOR,
        done_label=f"{stem}_tail_pause",
    )
    asm.label(f"{stem}_tail_pause")
    emit_register_delay(asm, stem=f"{stem}_tail_delay",
                        count=SLOW_REPORT_PAUSE_COUNT)
    emit_failure_tone(asm, SERIAL_DEAD_TONE_DIVISOR)
    halt = asm.pc
    asm.emit(0x76)
    return halt


def emit_loader_workspace_test(asm: Assembler) -> None:
    """Prove the D800..FDA7 loader buffer/stack workspace without a stack."""
    # Fill/read 55, then address-XOR/read.  The second pattern catches aliases
    # which a uniform fill cannot expose.
    lxi_h(asm, FRAMEBUFFER_BASE)
    asm.lxi_b(FRAMEBUFFER_BYTES)
    asm.emit(0x16, 0x55)  # MVI D,55; BC loop bookkeeping clobbers A
    asm.label("robust_ws_fill")
    asm.emit(0x7A, 0x77, 0x23, 0x0B, 0x78, 0xB1)  # MOV A,D / MOV M,A
    asm.jump(0xC2, "robust_ws_fill")
    lxi_h(asm, FRAMEBUFFER_BASE)
    asm.lxi_b(FRAMEBUFFER_BYTES)
    asm.label("robust_ws_55_read")
    asm.emit(0x7E, 0xFE, 0x55)
    asm.jump(0xC2, "workspace_dead")
    asm.emit(0x23, 0x0B, 0x78, 0xB1)
    asm.jump(0xC2, "robust_ws_55_read")
    lxi_h(asm, FRAMEBUFFER_BASE)
    asm.lxi_b(FRAMEBUFFER_BYTES)
    asm.label("robust_ws_xor_fill")
    asm.emit(0x7C, 0xAD, 0x77, 0x23, 0x0B, 0x78, 0xB1)
    asm.jump(0xC2, "robust_ws_xor_fill")
    lxi_h(asm, FRAMEBUFFER_BASE)
    asm.lxi_b(FRAMEBUFFER_BYTES)
    asm.label("robust_ws_xor_read")
    asm.emit(0x7C, 0xAD, 0x57, 0x7E, 0xBA)
    asm.jump(0xC2, "workspace_dead")
    asm.emit(0x23, 0x0B, 0x78, 0xB1)
    asm.jump(0xC2, "robust_ws_xor_read")


def emit_loader_guard(asm: Assembler) -> tuple[int, int]:
    asm.emit(0x16, 0x00)  # MVI D,additive accumulator
    asm.emit(0x21, 0x00, 0x00)
    asm.fixups.append((asm.pc - 2, "loader_extension_start"))
    length_offset = asm.pc + 1
    asm.lxi_b(0x0000)
    asm.label("robust_loader_sum")
    asm.emit(0x7A, 0x86, 0x57, 0x23, 0x0B, 0x78, 0xB1)
    asm.jump(0xC2, "robust_loader_sum")
    asm.emit(0x7A)
    checksum_offset = asm.pc + 1
    asm.emit(0xFE, 0x00)
    asm.jump(0xC2, "rom_fail")
    emit_rx_drain(asm, "loader")
    asm.jump(0xC3, "loader_entry")
    return length_offset, checksum_offset


def build() -> tuple[bytes, dict[str, int | list[int] | bytes]]:
    asm = Assembler()
    asm.jump(0xC3, "entry")
    while asm.pc < ROM_CHECKSUM_OFFSET:
        asm.emit(0x76)
    asm.emit(0x00)
    while asm.pc < ENTRY_OFFSET:
        asm.emit(0x76)
    asm.label("entry")
    emit_alive_beep(asm, halt=False)
    signature_expected_offset = emit_cpu_self_test(asm)

    # ROM is a hard prerequisite. No stack or RAM is touched here.
    asm.emit(0x16, 0x00)
    lxi_h(asm, ROM_CHECKSUM_START)
    asm.lxi_b(ROM_CHECKSUM_END - ROM_CHECKSUM_START)
    asm.label("best_rom_loop")
    asm.emit(0x7A, 0x86, 0x57, 0x23, 0x0B, 0x78, 0xB1)
    asm.jump(0xC2, "best_rom_loop")
    asm.emit(0x3A, ROM_CHECKSUM_OFFSET & 0xFF, ROM_CHECKSUM_OFFSET >> 8, 0xBA)
    asm.jump(0xC2, "rom_fail")

    asm.emit(0x1E, 0x00)  # E is the nonfatal peripheral-fault bitmap.
    emit_nonfatal_pic(asm)
    emit_nonfatal_ppi(asm)
    emit_nonfatal_pits(asm)

    emit_local_usart_test(asm, failure_label="uart_dead")
    train_timeout_offset = emit_train(asm, failure_label="uart_dead")
    placeholder_payload = bytes((protocol.PROTOCOL_VERSION, ROM_VERSION, 0, 0))
    placeholder_banner = protocol.encode_frame(protocol.TYPE_BANNER,
                                                placeholder_payload)
    placeholder_ack = protocol.encode_frame(protocol.TYPE_ACK,
                                             placeholder_payload)
    # Remove power-up/adapter garbage before inviting the host to respond.
    emit_rx_drain(asm, "banner")
    emit_table_tx(asm, "banner", len(placeholder_banner), stem="best_banner",
                  failure_label="uart_dead")
    emit_status_wait(asm, stem="best_banner_empty", mask=0x04,
                     failure_label="uart_dead")
    emit_stopwait_ack(asm, len(placeholder_ack))
    emit_dynamic_status(asm, "peripheral_status")

    # RAM follows the first successful serial report and may freely clobber E.
    asm.emit(0x1E, 0x00)  # MVI E,0: discard the already-transmitted fault map
    (first_start, first_size), (second_start, second_size) = FALLBACK_WINDOWS
    if first_size != second_size:
        raise ValueError("best-effort RAM windows must have equal sizes")
    emit_compact_fixed_window_tests(
        asm, first_start=first_start, second_start=second_start, size=first_size,
    )
    asm.emit(0x7B, 0xF6, RAM_STATUS_FLAG, 0x5F)  # E=80|good-window bits
    emit_dynamic_status(asm, "ram_status")
    emit_status_wait(asm, stem="best_final_empty", mask=0x04,
                     failure_label="uart_dead")
    asm.emit(0x7B, 0xE6, 0x03)  # MOV A,E / ANI window bits
    asm.jump(0xCA, "ram_dead")

    # The upload monitor needs its D800..FDA7 frame buffer and stack even when
    # one of the two general-purpose fallback windows is usable.
    asm.jump(0xC3, "robust_postdiag")
    success_halt = -1

    asm.label("cpu_fail")
    emit_failure_tone(asm, FAIL_TONE_DIVISOR)
    cpu_fail_halt = asm.pc; asm.emit(0x76)
    asm.label("rom_fail")
    emit_failure_tone(asm, WINDOWS_FOUND_DIVISOR)
    rom_fail_halt = asm.pc; asm.emit(0x76)
    asm.label("uart_dead")
    uart_fail_halt = emit_slow_terminal_code(asm, UART_FAILURE_CODE, "best_uart_fail")
    asm.label("ram_dead")
    ram_fail_halt = emit_slow_terminal_code(asm, RAM_FAILURE_CODE, "best_ram_fail")
    asm.label("workspace_dead")
    workspace_fail_halt = emit_slow_terminal_code(
        asm, WORKSPACE_FAILURE_CODE, "best_workspace_fail"
    )

    if asm.pc > ROM_CHECKSUM_END:
        raise ValueError("best-effort executable overlaps 0800h tables")
    while asm.pc < ROM_CHECKSUM_END:
        asm.emit(0x76)
    asm.label("banner")
    banner_offset = asm.pc; asm.emit(*placeholder_banner)
    asm.label("ack_expected")
    ack_offset = asm.pc; asm.emit(*placeholder_ack)
    while asm.pc < CRC_TABLE_OFFSET:
        asm.emit(0x76)
    crc_table = bytes(protocol.crc8_atm(bytes((protocol.TYPE_DIAG_STATUS, 1, value)))
                      for value in range(256))
    asm.emit(*crc_table)

    if asm.pc != 0x0A00:
        raise ValueError("robust loader API does not start at 0A00h")
    asm.label("loader_extension_start")
    loader_metadata = emit_loader(asm)
    asm.label("loader_extension_end")
    asm.label("robust_postdiag")
    emit_loader_workspace_test(asm)
    loader_length_offset, loader_checksum_offset = emit_loader_guard(asm)

    code = bytearray(asm.resolve())
    loader_start = asm.labels["loader_extension_start"]
    loader_end = asm.labels["loader_extension_end"]
    loader_length = loader_end - loader_start
    loader_checksum = sum(code[loader_start:loader_end]) & 0xFF
    code[loader_length_offset] = loader_length & 0xFF
    code[loader_length_offset + 1] = loader_length >> 8
    code[loader_checksum_offset] = loader_checksum
    image = bytearray([0x76] * ROM_SIZE)
    image[:len(code)] = code
    image[IDENTITY_OFFSET:IDENTITY_OFFSET + len(IDENTITY)] = IDENTITY
    rom_checksum = sum(image[ROM_CHECKSUM_START:ROM_CHECKSUM_END]) & 0xFF
    image[ROM_CHECKSUM_OFFSET] = rom_checksum
    checksum_offsets = [banner_offset + 6, banner_offset + 7,
                        ack_offset + 6, ack_offset + 7]
    checksum_image = bytearray(image)
    for offset in checksum_offsets + [banner_offset + 8, ack_offset + 8]:
        checksum_image[offset] = 0
    checksum = protocol.crc16_ccitt_false(bytes(checksum_image))
    payload = bytes((protocol.PROTOCOL_VERSION, ROM_VERSION,
                     checksum >> 8, checksum & 0xFF))
    banner = protocol.encode_frame(protocol.TYPE_BANNER, payload)
    ack = protocol.encode_frame(protocol.TYPE_ACK, payload)
    image[banner_offset:banner_offset + len(banner)] = banner
    image[ack_offset:ack_offset + len(ack)] = ack
    if sum(image[ROM_CHECKSUM_START:ROM_CHECKSUM_END]) & 0xFF != rom_checksum:
        raise ValueError("protocol patch changed best-effort ROM checksum")
    return bytes(image), {
        "code_size": len(code), "signature_expected_offset": signature_expected_offset,
        "train_timeout_offset": train_timeout_offset, "banner": banner, "ack": ack,
        "banner_offset": banner_offset, "ack_offset": ack_offset,
        "crc_table_offset": CRC_TABLE_OFFSET, "rom_checksum": rom_checksum,
        "checksum": checksum, "success_halt": success_halt,
        "cpu_fail_halt": cpu_fail_halt, "rom_fail_halt": rom_fail_halt,
        "uart_fail_halt": uart_fail_halt, "ram_fail_halt": ram_fail_halt,
        "workspace_fail_halt": workspace_fail_halt,
        "loader_extension_start": loader_start,
        "loader_extension_end": loader_end,
        "loader_extension_length": loader_length,
        "loader_extension_checksum": loader_checksum,
        **loader_metadata,
    }


def main() -> int:
    parser = argparse.ArgumentParser(); parser.add_argument("--check", action="store_true")
    args = parser.parse_args(); image, metadata = build()
    digest = hashlib.sha256(image).hexdigest()
    if args.check:
        if not OUTPUT.exists() or OUTPUT.read_bytes() != image:
            raise SystemExit("diag-d0-stopwait.bin is missing or stale")
        if not README.exists() or digest not in README.read_text():
            raise SystemExit("firmware README does not pin stop-wait SHA256")
        action = "checked"
    else:
        OUTPUT.write_bytes(image); action = "wrote"
    print(f"JUKURAVI-D0-STOPWAIT-FULL-BUILD: {action} {OUTPUT.name} bytes={len(image)} "
          f"code={metadata['code_size']} signature={EXPECTED_SIGNATURE:02X} "
          f"block1_sum={metadata['rom_checksum']:02X} self_crc16={metadata['checksum']:04X} "
          f"sha256={digest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
