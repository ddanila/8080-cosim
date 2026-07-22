#!/usr/bin/env python3
"""Build Jukuravi D0 rung 4b: serial survey plus beep-only RAM fallback."""

from __future__ import annotations

import argparse
import hashlib
import sys
from pathlib import Path

from build_d0_alive import (
    Assembler,
    DELAY_COUNT_OFFSET as ALIVE_DELAY_COUNT_OFFSET,
    ROM_SIZE,
    emit_alive_beep,
)
from build_d0_cpu import (
    EXPECTED_SIGNATURE,
    FAIL_TONE_DIVISOR as CPU_FAIL_TONE_DIVISOR,
    emit_cpu_self_test,
    emit_failure_tone,
)
from build_d0_ram import (
    PATTERN_SET,
    RETENTION_DELAY_COUNT,
    SURVEY_END_PAGE,
    SURVEY_START_PAGE,
    SURVEY_VERSION,
    VIDEO_PIT_WRITES,
    emit_fixed_frame,
    emit_ram_survey,
    emit_video_pit_init,
)
from build_d0_serial import (
    SERIAL_DEAD_TONE_DIVISOR,
    TRAIN_LENGTH,
    emit_ack_rx,
    emit_serial_ok,
    emit_status_wait,
    emit_table_tx,
    emit_train,
)
from build_d0_usart_local import (
    USART_FAIL_TONE_DIVISOR,
    emit_local_usart_test,
)


HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import protocol  # noqa: E402


OUTPUT = HERE / "diag-d0-ram-fallback.bin"
README = HERE / "README.md"
IDENTITY_OFFSET = 0x1F00
IDENTITY = b"JUKURAVI-D0-RAM-FALLBACK-1\0"
ROM_VERSION = 3
FALLBACK_WINDOWS = ((0x4000, 0x1000), (0xC000, 0x1000))
SERIAL_DEAD_MARK_COUNT = 20834  # nominally about 0.25 seconds
PULSE_COUNT = 8334              # nominally about 0.10 seconds
PULSE_GAP_COUNT = 4167          # nominally about 0.05 seconds
WINDOWS_FOUND_PULSES = 3
WINDOWS_FOUND_DIVISOR = 1000    # nominal 2 kHz
CHIP_ID_DIVISOR = 2000          # nominal 1 kHz
ROM_CHECKSUM_OFFSET = 0x000A
ROM_CHECKSUM_START = 0x000B
ROM_CHECKSUM_END = 0x0800
ROM_CHECK_FAIL_DIVISOR = 1000   # nominal 2 kHz, continuous
PIC_COMMAND_PORT = 0x00
PIC_DATA_PORT = 0x01
PIC_ICW1 = 0xD6                 # MCS-80 CALL mode, single, no ICW4
PIC_ICW2 = 0xFE                 # exact EktaSoft vector-page initialization
PIC_TEST_PATTERNS = (0x00, 0xFF)
PIC_SAFE_MASK = 0xFF
PIC_CHECK_FAIL_DIVISOR = 500    # nominal 4 kHz, continuous


def lxi_h(asm: Assembler, value: int) -> None:
    asm.emit(0x21, value & 0xFF, value >> 8)


def emit_window_loop_setup(
    asm: Assembler, start: int, count: int, *, offsets: list[int]
) -> None:
    lxi_h(asm, start)
    offsets.append(asm.pc + 1)
    asm.lxi_b(count)


def emit_window_loop_tail(asm: Assembler, label: str) -> None:
    asm.emit(0x23, 0x0B, 0x78, 0xB1)  # INX H / DCX B / MOV A,B / ORA C
    asm.jump(0xC2, label)


def emit_fixed_window_test(
    asm: Assembler, *, stem: str, start: int, size: int, flag: int
) -> dict[str, int | list[int]]:
    """Wholesale-test one candidate window and OR its good bit into E."""
    count_offsets: list[int] = []
    asm.emit(0x16, 0x00)  # MVI D,0 failure mask

    emit_window_loop_setup(asm, start, size, offsets=count_offsets)
    asm.label(f"{stem}_fill_00")
    asm.emit(0x36, 0x00)
    emit_window_loop_tail(asm, f"{stem}_fill_00")

    emit_window_loop_setup(asm, start, size, offsets=count_offsets)
    asm.label(f"{stem}_test_00")
    asm.emit(0x7E, 0xB2, 0x57, 0x36, 0xFF)  # MOV A,M / ORA D / MOV D,A / MVI M,FF
    emit_window_loop_tail(asm, f"{stem}_test_00")

    emit_window_loop_setup(asm, start, size, offsets=count_offsets)
    asm.label(f"{stem}_test_ff")
    asm.emit(0x7E, 0xEE, 0xFF, 0xB2, 0x57)  # compare FF, accumulate
    asm.emit(0x7C, 0xAD, 0x77)              # MOV A,H / XRA L / MOV M,A
    emit_window_loop_tail(asm, f"{stem}_test_ff")

    emit_window_loop_setup(asm, start, size, offsets=count_offsets)
    asm.label(f"{stem}_test_address")
    asm.emit(0x7C, 0xAD, 0xAE, 0xB2, 0x57)  # H xor L xor M, accumulate
    asm.emit(0x7C, 0xAD, 0x2F, 0x77)        # write ~(H xor L)
    emit_window_loop_tail(asm, f"{stem}_test_address")

    emit_window_loop_setup(asm, start, size, offsets=count_offsets)
    asm.label(f"{stem}_test_inverse")
    asm.emit(0x7C, 0xAD, 0x2F, 0xAE, 0xB2, 0x57)  # compare inverse
    asm.emit(0x36, 0x55)
    emit_window_loop_tail(asm, f"{stem}_test_inverse")

    retention_offset = asm.pc + 1
    asm.lxi_b(RETENTION_DELAY_COUNT)
    asm.label(f"{stem}_retention_delay")
    asm.emit(0x0B, 0x78, 0xB1)
    asm.jump(0xC2, f"{stem}_retention_delay")

    emit_window_loop_setup(asm, start, size, offsets=count_offsets)
    asm.label(f"{stem}_test_retained")
    asm.emit(0x7E, 0xEE, 0x55, 0xB2, 0x57)
    emit_window_loop_tail(asm, f"{stem}_test_retained")

    asm.emit(0x7A, 0xB7)  # MOV A,D / ORA A
    asm.jump(0xC2, f"{stem}_bad")
    asm.emit(0x7B, 0xF6, flag, 0x5F)  # MOV A,E / ORI flag / MOV E,A
    asm.label(f"{stem}_bad")
    return {
        "count_offsets": count_offsets,
        "retention_offset": retention_offset,
    }


def emit_register_delay(asm: Assembler, *, stem: str, count: int) -> int:
    offset = asm.pc + 1
    asm.lxi_b(count)
    asm.label(stem)
    asm.emit(0x0B, 0x78, 0xB1)
    asm.jump(0xC2, stem)
    return offset


def emit_tone_pulse(
    asm: Assembler, *, stem: str, divisor: int, count: int
) -> int:
    emit_failure_tone(asm, divisor)
    delay_offset = emit_register_delay(asm, stem=f"{stem}_delay", count=count)
    asm.mvi_a(0x50)
    asm.out(0x1B)
    asm.mvi_a(0x01)
    asm.out(0x19)
    return delay_offset


def emit_pulse_loop(
    asm: Assembler, *, stem: str, divisor: int, done_label: str
) -> tuple[int, int]:
    """Emit D short pulses and jump to done_label."""
    asm.label(f"{stem}_pulse")
    emit_failure_tone(asm, divisor)
    pulse_offset = emit_register_delay(
        asm, stem=f"{stem}_pulse_delay", count=PULSE_COUNT
    )
    asm.mvi_a(0x50)
    asm.out(0x1B)
    asm.mvi_a(0x01)
    asm.out(0x19)
    gap_offset = emit_register_delay(
        asm, stem=f"{stem}_gap_delay", count=PULSE_GAP_COUNT
    )
    asm.emit(0x15)  # DCR D
    asm.jump(0xC2, f"{stem}_pulse")
    asm.jump(0xC3, done_label)
    return pulse_offset, gap_offset


def emit_rom_convention_check(asm: Assembler) -> dict[str, int]:
    """Verify EktaSoft's stored additive checksum without RAM or a stack."""
    asm.emit(0x16, 0x00)  # MVI D,0 additive accumulator
    lxi_h(asm, ROM_CHECKSUM_START)
    asm.lxi_b(ROM_CHECKSUM_END - ROM_CHECKSUM_START)
    asm.label("rom_checksum_loop")
    asm.emit(0x7A, 0x86, 0x57)        # MOV A,D / ADD M / MOV D,A
    asm.emit(0x23, 0x0B, 0x78, 0xB1)  # INX H / DCX B / MOV A,B / ORA C
    asm.jump(0xC2, "rom_checksum_loop")
    asm.emit(0x3A, ROM_CHECKSUM_OFFSET & 0xFF, ROM_CHECKSUM_OFFSET >> 8)
    asm.emit(0xBA)  # CMP D
    asm.jump(0xC2, "rom_fail")
    return {
        "rom_checksum_loop": asm.labels["rom_checksum_loop"],
        "rom_check_pass": asm.pc,
    }


def emit_pic_register_check(asm: Assembler) -> dict[str, int | list[int]]:
    """Wiggle every 8259 IMR bit, then leave every interrupt masked."""
    if PIC_TEST_PATTERNS != (0x00, 0xFF):
        raise ValueError("compact PIC check requires complementary 00/FF patterns")
    asm.mvi_a(PIC_ICW1)
    asm.out(PIC_COMMAND_PORT)
    asm.mvi_a(PIC_ICW2)
    asm.out(PIC_DATA_PORT)
    read_offsets: list[int] = []
    asm.emit(0xAF)                     # XRA A: all IRQs unmasked, IFF stays clear
    asm.out(PIC_DATA_PORT)
    read_offsets.append(asm.pc)
    asm.emit(0xDB, PIC_DATA_PORT, 0xB7)  # IN IMR / ORA A: expect 00
    asm.jump(0xC2, "pic_fail")
    asm.emit(0x2F)                     # CMA: A=FF, all IRQs masked
    asm.out(PIC_DATA_PORT)
    read_offsets.append(asm.pc)
    asm.emit(0xDB, PIC_DATA_PORT, 0x3C)  # IN IMR / INR A: expect FF -> 00
    asm.jump(0xC2, "pic_fail")
    asm.mvi_a(PIC_SAFE_MASK)
    asm.out(PIC_DATA_PORT)
    return {
        "pic_read_offsets": read_offsets,
        "pic_patterns": list(PIC_TEST_PATTERNS),
        "pic_check_pass": asm.pc,
    }


def build_variant(
    *, rom_version: int, identity: bytes, rom_convention: bool,
    entry_offset: int = 0x0010, pic_check: bool = False,
) -> tuple[bytes, dict[str, int | list[int] | bytes]]:
    if pic_check and not rom_convention:
        raise ValueError("PIC profile requires the cumulative ROM convention")
    begin_payload = bytes((SURVEY_VERSION, SURVEY_START_PAGE,
                           SURVEY_END_PAGE, PATTERN_SET))
    end_payload = bytes((SURVEY_START_PAGE, SURVEY_END_PAGE))
    begin_frame = protocol.encode_frame(protocol.TYPE_RAM_BEGIN, begin_payload)
    end_frame = protocol.encode_frame(protocol.TYPE_RAM_END, end_payload)

    asm = Assembler()
    if rom_convention:
        # Match the official EktaSoft block-1 layout: reset jumps over a
        # reserved header whose byte 000Ah stores sum(000Bh..07FFh) mod 256.
        asm.jump(0xC3, "entry")
        while asm.pc < ROM_CHECKSUM_OFFSET:
            asm.emit(0x76)
        asm.emit(0x00)  # additive checksum placeholder
        if entry_offset < ROM_CHECKSUM_START:
            raise ValueError("ROM-convention entry overlaps the stored checksum")
        while asm.pc < entry_offset:
            asm.emit(0x76)
        asm.label("entry")
    alive_start = asm.pc
    emit_alive_beep(asm, halt=False)
    alive_delay_offset = alive_start + ALIVE_DELAY_COUNT_OFFSET
    signature_expected_offset = emit_cpu_self_test(asm)
    rom_metadata = emit_rom_convention_check(asm) if rom_convention else {}
    pic_metadata = emit_pic_register_check(asm) if pic_check else {}
    local_timeout_offsets = emit_local_usart_test(asm)
    train_timeout_offset = emit_train(asm, failure_label="ram_fallback")

    placeholder_payload = bytes((protocol.PROTOCOL_VERSION, rom_version, 0, 0))
    placeholder_banner = protocol.encode_frame(protocol.TYPE_BANNER, placeholder_payload)
    placeholder_ack = protocol.encode_frame(protocol.TYPE_ACK, placeholder_payload)
    banner_timeout_offsets = emit_table_tx(
        asm, "banner", len(placeholder_banner), failure_label="ram_fallback"
    )
    banner_empty_timeout_offset = emit_status_wait(
        asm, stem="banner_empty", mask=0x04, failure_label="ram_fallback"
    )
    ack_timeout_offsets = emit_ack_rx(
        asm, len(placeholder_ack), failure_label="ram_fallback"
    )

    serial_ok_delay_offset = emit_serial_ok(asm, halt=False)
    emit_video_pit_init(asm)
    begin_timeout_offsets = emit_fixed_frame(
        asm, begin_frame, stem="ram_begin", failure_label="ram_fallback"
    )
    survey_metadata = emit_ram_survey(asm, failure_label="ram_fallback")
    end_timeout_offsets = emit_fixed_frame(
        asm, end_frame, stem="ram_end", failure_label="ram_fallback"
    )
    final_empty_timeout_offset = emit_status_wait(
        asm, stem="ram_end_empty", mask=0x04, failure_label="ram_fallback"
    )
    success_halt = asm.pc
    asm.emit(0x76)

    asm.label("cpu_fail")
    emit_failure_tone(asm, CPU_FAIL_TONE_DIVISOR)
    cpu_fail_halt = asm.pc
    asm.emit(0x76)
    rom_fail_halt = -1
    if rom_convention:
        asm.label("rom_fail")
        emit_failure_tone(asm, ROM_CHECK_FAIL_DIVISOR)
        rom_fail_halt = asm.pc
        asm.emit(0x76)
    pic_fail_halt = -1
    if pic_check:
        asm.label("pic_fail")
        asm.mvi_a(PIC_SAFE_MASK)
        asm.out(PIC_DATA_PORT)
        emit_failure_tone(asm, PIC_CHECK_FAIL_DIVISOR)
        pic_fail_halt = asm.pc
        asm.emit(0x76)
    asm.label("usart_fail")
    emit_failure_tone(asm, USART_FAIL_TONE_DIVISOR)
    usart_fail_halt = asm.pc
    asm.emit(0x76)

    asm.label("ram_fallback")
    serial_dead_mark_delay_offset = emit_tone_pulse(
        asm,
        stem="serial_dead_mark",
        divisor=SERIAL_DEAD_TONE_DIVISOR,
        count=SERIAL_DEAD_MARK_COUNT,
    )
    emit_video_pit_init(asm)
    asm.emit(0x1E, 0x00)  # MVI E,0 candidate-good flags
    fallback_tests = [
        emit_fixed_window_test(
            asm, stem=f"fallback_window_{index}", start=start,
            size=size, flag=1 << index,
        )
        for index, (start, size) in enumerate(FALLBACK_WINDOWS)
    ]
    asm.emit(0x7B, 0xB7)  # MOV A,E / ORA A
    asm.jump(0xCA, "no_windows")

    asm.emit(0x16, WINDOWS_FOUND_PULSES)  # MVI D,3
    windows_pulse_offsets = emit_pulse_loop(
        asm, stem="windows_found", divisor=WINDOWS_FOUND_DIVISOR,
        done_label="windows_found_done",
    )
    asm.label("windows_found_done")
    windows_found_halt = asm.pc
    asm.emit(0x76)

    asm.label("no_windows")
    asm.emit(0x7A, 0xB7)  # MOV A,D / ORA A
    asm.jump(0xCA, "no_windows_continuous")
    asm.emit(0x0E, 0x01)  # MVI C,1; one pulse means D84/bit 0
    asm.label("chip_index_scan")
    asm.emit(0x0F)        # RRC: candidate failure bit -> carry
    asm.jump(0xDA, "chip_index_found")
    asm.emit(0x0C)        # INR C
    asm.jump(0xC3, "chip_index_scan")
    asm.label("chip_index_found")
    asm.emit(0x51)        # MOV D,C
    chip_pulse_offsets = emit_pulse_loop(
        asm, stem="chip_id", divisor=CHIP_ID_DIVISOR,
        done_label="no_windows_continuous",
    )
    asm.label("no_windows_continuous")
    emit_failure_tone(asm, SERIAL_DEAD_TONE_DIVISOR)
    no_windows_halt = asm.pc
    asm.emit(0x76)

    if rom_convention:
        if asm.pc > ROM_CHECKSUM_END:
            raise ValueError(
                "ROM-convention executable overlaps the protocol-table boundary"
            )
        while asm.pc < ROM_CHECKSUM_END:
            asm.emit(0x76)
    asm.label("banner")
    banner_offset = asm.pc
    asm.emit(*placeholder_banner)
    asm.label("ack_expected")
    ack_offset = asm.pc
    asm.emit(*placeholder_ack)

    code = bytearray(asm.resolve())
    image = bytearray([0x76] * ROM_SIZE)
    image[: len(code)] = code
    image[IDENTITY_OFFSET : IDENTITY_OFFSET + len(identity)] = identity
    rom_checksum = -1
    if rom_convention:
        if banner_offset != ROM_CHECKSUM_END:
            raise ValueError("ROM-convention protocol tables must start at 0800h")
        rom_checksum = sum(image[ROM_CHECKSUM_START:ROM_CHECKSUM_END]) & 0xFF
        image[ROM_CHECKSUM_OFFSET] = rom_checksum
    checksum_offsets = [
        banner_offset + 6, banner_offset + 7,
        ack_offset + 6, ack_offset + 7,
    ]
    checksum_zero_offsets = checksum_offsets + [banner_offset + 8, ack_offset + 8]
    checksum_image = bytearray(image)
    for offset in checksum_zero_offsets:
        checksum_image[offset] = 0
    checksum = protocol.crc16_ccitt_false(bytes(checksum_image))
    banner_payload = bytes(
        (protocol.PROTOCOL_VERSION, rom_version, checksum >> 8, checksum & 0xFF)
    )
    banner = protocol.encode_frame(protocol.TYPE_BANNER, banner_payload)
    ack = protocol.encode_frame(protocol.TYPE_ACK, banner_payload)
    image[banner_offset : banner_offset + len(banner)] = banner
    image[ack_offset : ack_offset + len(ack)] = ack
    if rom_convention:
        computed = sum(image[ROM_CHECKSUM_START:ROM_CHECKSUM_END]) & 0xFF
        if computed != rom_checksum:
            raise ValueError("protocol patch changed the historical ROM checksum")

    metadata: dict[str, int | list[int] | bytes] = {
        "code_size": len(code),
        "alive_delay_offset": alive_delay_offset,
        "signature_expected_offset": signature_expected_offset,
        "local_timeout_offsets": local_timeout_offsets,
        "train_timeout_offset": train_timeout_offset,
        "banner_timeout_offsets": banner_timeout_offsets,
        "banner_empty_timeout_offset": banner_empty_timeout_offset,
        "ack_timeout_offsets": ack_timeout_offsets,
        "serial_ok_delay_offset": serial_ok_delay_offset,
        "begin_timeout_offsets": begin_timeout_offsets,
        "end_timeout_offsets": end_timeout_offsets,
        "final_empty_timeout_offset": final_empty_timeout_offset,
        "success_halt": success_halt,
        "cpu_fail_halt": cpu_fail_halt,
        "rom_fail_halt": rom_fail_halt,
        "pic_fail_halt": pic_fail_halt,
        "usart_fail_halt": usart_fail_halt,
        "ram_fallback": asm.labels["ram_fallback"],
        "windows_found_halt": windows_found_halt,
        "no_windows_halt": no_windows_halt,
        "serial_dead_mark_delay_offset": serial_dead_mark_delay_offset,
        "windows_pulse_offsets": list(windows_pulse_offsets),
        "chip_pulse_offsets": list(chip_pulse_offsets),
        "fallback_count_offsets": [
            offset for item in fallback_tests for offset in item["count_offsets"]
        ],
        "fallback_retention_offsets": [
            item["retention_offset"] for item in fallback_tests
        ],
        "banner_offset": banner_offset,
        "ack_offset": ack_offset,
        "checksum_offsets": checksum_offsets,
        "checksum_zero_offsets": checksum_zero_offsets,
        "checksum": checksum,
        "banner": banner,
        "ack": ack,
        "begin_frame": begin_frame,
        "end_frame": end_frame,
        "rom_checksum_offset": ROM_CHECKSUM_OFFSET,
        "rom_checksum_start": ROM_CHECKSUM_START,
        "rom_checksum_end": ROM_CHECKSUM_END,
        "rom_checksum": rom_checksum,
        "rom_fault_offset": ROM_CHECKSUM_END - 1,
        **rom_metadata,
        **pic_metadata,
        **survey_metadata,
    }
    return bytes(image), metadata


def build() -> tuple[bytes, dict[str, int | list[int] | bytes]]:
    return build_variant(
        rom_version=ROM_VERSION, identity=IDENTITY, rom_convention=False
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--check", action="store_true", help="fail if the committed image is stale"
    )
    args = parser.parse_args()
    image, metadata = build()
    digest = hashlib.sha256(image).hexdigest()
    if args.check:
        if not OUTPUT.exists():
            raise SystemExit(f"missing generated image: {OUTPUT.name}")
        if OUTPUT.read_bytes() != image:
            raise SystemExit(
                "diag-d0-ram-fallback.bin is stale; run build_d0_ram_fallback.py"
            )
        if not README.exists() or digest not in README.read_text():
            raise SystemExit("firmware README does not pin the RAM-fallback SHA256")
        action = "checked"
    else:
        OUTPUT.write_bytes(image)
        action = "wrote"
    print(
        f"JUKURAVI-D0-RAM-FALLBACK-BUILD: {action} {OUTPUT.name} "
        f"bytes={len(image)} code={metadata['code_size']} "
        f"signature={EXPECTED_SIGNATURE:02X} "
        f"self_crc16={metadata['checksum']:04X} sha256={digest}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
