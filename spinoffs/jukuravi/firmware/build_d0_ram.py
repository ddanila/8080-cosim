#!/usr/bin/env python3
"""Build Jukuravi D0 rung 4a: serial 48 KiB mode-0 RAM survey."""

from __future__ import annotations

import argparse
import hashlib
import sys
from pathlib import Path

from build_d0_alive import Assembler, ROM_SIZE, emit_alive_beep
from build_d0_cpu import (
    EXPECTED_SIGNATURE,
    FAIL_TONE_DIVISOR as CPU_FAIL_TONE_DIVISOR,
    emit_cpu_self_test,
    emit_failure_tone,
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


OUTPUT = HERE / "diag-d0-ram.bin"
README = HERE / "README.md"
IDENTITY_OFFSET = 0x1F00
IDENTITY = b"JUKURAVI-D0-RAM-1\0"
ROM_VERSION = 2
SURVEY_VERSION = 1
PATTERN_SET = 1
SURVEY_START_PAGE = 0x40
SURVEY_END_PAGE = 0xFF
RETENTION_DELAY_COUNT = 1667  # register-only nominal approximately 20 ms delay

VIDEO_PIT_WRITES = (
    (0x13, 0x15), (0x13, 0x53), (0x13, 0x93),
    (0x17, 0x73), (0x17, 0x93), (0x17, 0x34),
    (0x14, 0x39), (0x14, 0x01),
    (0x10, 0x64), (0x11, 0x24), (0x12, 0x08),
    (0x15, 0x72), (0x15, 0x00), (0x16, 0x25),
)


def emit_video_pit_init(asm: Assembler) -> None:
    """Reproduce the source-guarded Ekta 3.7 D54/D55 refresh/raster setup."""
    for port, value in VIDEO_PIT_WRITES:
        asm.mvi_a(value)
        asm.out(port)


def emit_fixed_frame(
    asm: Assembler, frame: bytes, *, stem: str, failure_label: str = "serial_dead"
) -> list[int]:
    offsets: list[int] = []
    for index, value in enumerate(frame):
        offsets.append(emit_status_wait(
            asm,
            stem=f"{stem}_{index}",
            mask=0x01,
            failure_label=failure_label,
        ))
        asm.mvi_a(value)
        asm.out(0x08)
    return offsets


def emit_memory_pass(
    asm: Assembler, *, stem: str, expected: int, replacement: int | None
) -> None:
    """Test one 256-byte page, folding every discrepant data bit into D."""
    asm.emit(0x0E, 0x00)  # MVI C,0: DCR wraps for exactly 256 iterations
    asm.label(stem)
    asm.emit(0x7E)             # MOV A,M
    asm.emit(0xEE, expected)   # XRI expected
    asm.emit(0xB2)             # ORA D
    asm.emit(0x57)             # MOV D,A
    if replacement is not None:
        asm.emit(0x36, replacement)  # MVI M,replacement
    asm.emit(0x23, 0x0D)       # INX H / DCR C
    asm.jump(0xC2, stem)
    asm.emit(0x25)             # DCR H: next-page 00 -> current-page 00


def emit_address_pass(asm: Assembler, *, stem: str, phase: str) -> None:
    """Use L/~L patterns to expose low-address aliasing within the page."""
    asm.emit(0x0E, 0x00)
    asm.label(stem)
    if phase == "seed":
        asm.emit(0x7E, 0xEE, 0xFF)  # MOV A,M / XRI FF
    elif phase == "address":
        asm.emit(0x7E, 0xAD)        # MOV A,M / XRA L
    elif phase == "inverse":
        asm.emit(0x7D, 0x2F, 0x5F)  # MOV A,L / CMA / MOV E,A
        asm.emit(0x7E, 0xAB)        # MOV A,M / XRA E
    else:
        raise ValueError(f"unknown address-pass phase: {phase}")
    asm.emit(0xB2, 0x57)            # ORA D / MOV D,A
    if phase == "seed":
        asm.emit(0x7D, 0x77)        # MOV A,L / MOV M,A
    elif phase == "address":
        asm.emit(0x7D, 0x2F, 0x77)  # MOV A,L / CMA / MOV M,A
    else:
        asm.emit(0x36, 0x55)        # MVI M,55
    asm.emit(0x23, 0x0D)
    asm.jump(0xC2, stem)
    asm.emit(0x25)


def emit_page_alias_probe(asm: Assembler) -> tuple[int, int]:
    """Detect high-address aliasing at offset 00 without changing final 55 fill."""
    asm.emit(0x44)             # MOV B,H: page under test
    asm.emit(0x78, 0x77)       # MOV A,B / MOV M,A: unique current sentinel
    start_offset = asm.pc + 1
    asm.emit(0x0E, SURVEY_START_PAGE)  # MVI C,first candidate page
    asm.label("page_alias_next")
    asm.emit(0x79, 0xB8)       # MOV A,C / CMP B
    asm.jump(0xCA, "page_alias_advance")
    asm.emit(0x61)             # MOV H,C
    asm.emit(0x78, 0x2F, 0x77)  # MOV A,B / CMA / MOV M,A
    asm.emit(0x60)             # MOV H,B
    asm.emit(0x7E, 0xA8, 0xB2, 0x57)  # MOV A,M / XRA B / ORA D / MOV D,A
    asm.emit(0x61)             # MOV H,C
    asm.emit(0x36, 0x55)       # restore candidate's final fill
    asm.label("page_alias_advance")
    asm.emit(0x79)             # MOV A,C
    end_offset = asm.pc + 1
    asm.emit(0xFE, SURVEY_END_PAGE)
    asm.jump(0xCA, "page_alias_done")
    asm.emit(0x0C)             # INR C
    asm.jump(0xC3, "page_alias_next")
    asm.label("page_alias_done")
    asm.emit(0x60, 0x2E, 0x00)  # MOV H,B / MVI L,0
    asm.emit(0x36, 0x55)       # restore current page offset 00
    return start_offset, end_offset


def emit_crc_fold(asm: Assembler, *, stem: str) -> None:
    """Fold A into the CRC-8/ATM accumulator E without memory or a table."""
    asm.emit(0xAB)       # XRA E
    asm.emit(0x0E, 0x08)  # MVI C,8
    asm.label(f"{stem}_bit")
    asm.emit(0x87)       # ADD A: logical left shift, outgoing MSB -> carry
    asm.jump(0xD2, f"{stem}_no_xor")  # JNC
    asm.emit(0xEE, 0x07)  # XRI polynomial
    asm.label(f"{stem}_no_xor")
    asm.emit(0x0D)       # DCR C
    asm.jump(0xC2, f"{stem}_bit")
    asm.emit(0x5F)       # MOV E,A


def emit_page_frame(
    asm: Assembler, *, failure_label: str = "serial_dead"
) -> list[int]:
    """Emit TYPE_RAM_BLOCK payload [H=current page, D=failure mask]."""
    asm.emit(0x1E, 0x00)  # MVI E,0 CRC accumulator
    for stem, load in (
        ("crc_type", (0x3E, protocol.TYPE_RAM_BLOCK)),
        ("crc_length", (0x3E, 0x02)),
        ("crc_page", (0x7C,)),   # MOV A,H
        ("crc_mask", (0x7A,)),   # MOV A,D
    ):
        asm.emit(*load)
        emit_crc_fold(asm, stem=stem)

    loads = (
        (0x3E, protocol.SYNC[0]),
        (0x3E, protocol.SYNC[1]),
        (0x3E, protocol.TYPE_RAM_BLOCK),
        (0x3E, 0x02),
        (0x7C,),  # MOV A,H
        (0x7A,),  # MOV A,D
        (0x7B,),  # MOV A,E
    )
    offsets: list[int] = []
    for index, load in enumerate(loads):
        offsets.append(emit_status_wait(
            asm,
            stem=f"page_tx_{index}",
            mask=0x01,
            failure_label=failure_label,
        ))
        asm.emit(*load)
        asm.out(0x08)
    return offsets


def emit_ram_survey(
    asm: Assembler, *, failure_label: str = "serial_dead"
) -> dict[str, int | list[int]]:
    start_page_offset = asm.pc + 1
    asm.emit(0x26, SURVEY_START_PAGE)  # MVI H,start page
    asm.emit(0x2E, 0x00)               # MVI L,0
    asm.label("survey_page")
    asm.emit(0x16, 0x00)               # MVI D,0 page failure mask

    # Fill 00, then read-before-write transitions 00->FF->L->~L->55.
    asm.emit(0x0E, 0x00)
    asm.label("fill_00")
    asm.emit(0x36, 0x00, 0x23, 0x0D)  # MVI M,0 / INX H / DCR C
    asm.jump(0xC2, "fill_00")
    asm.emit(0x25)
    emit_memory_pass(asm, stem="test_00", expected=0x00, replacement=0xFF)
    emit_address_pass(asm, stem="test_ff_seed_address", phase="seed")
    emit_address_pass(asm, stem="test_address", phase="address")
    emit_address_pass(asm, stem="test_inverse_address", phase="inverse")

    retention_delay_offset = asm.pc + 1
    asm.lxi_b(RETENTION_DELAY_COUNT)
    asm.label("retention_delay")
    asm.emit(0x0B, 0x78, 0xB1)  # DCX B / MOV A,B / ORA C
    asm.jump(0xC2, "retention_delay")
    emit_memory_pass(asm, stem="test_55_retained", expected=0x55, replacement=None)
    alias_start_page_offset, alias_end_page_offset = emit_page_alias_probe(asm)

    page_frame_timeout_offsets = emit_page_frame(
        asm, failure_label=failure_label
    )
    asm.emit(0x7C)  # MOV A,H
    end_page_offset = asm.pc + 1
    asm.emit(0xFE, SURVEY_END_PAGE)  # CPI end page
    asm.jump(0xCA, "survey_done")   # JZ
    asm.emit(0x24)                   # INR H
    asm.jump(0xC3, "survey_page")
    asm.label("survey_done")
    return {
        "start_page_offset": start_page_offset,
        "end_page_offset": end_page_offset,
        "retention_delay_offset": retention_delay_offset,
        "alias_start_page_offset": alias_start_page_offset,
        "alias_end_page_offset": alias_end_page_offset,
        "page_frame_timeout_offsets": page_frame_timeout_offsets,
    }


def build() -> tuple[bytes, dict[str, int | list[int] | bytes]]:
    begin_payload = bytes((SURVEY_VERSION, SURVEY_START_PAGE,
                           SURVEY_END_PAGE, PATTERN_SET))
    end_payload = bytes((SURVEY_START_PAGE, SURVEY_END_PAGE))
    begin_frame = protocol.encode_frame(protocol.TYPE_RAM_BEGIN, begin_payload)
    end_frame = protocol.encode_frame(protocol.TYPE_RAM_END, end_payload)

    asm = Assembler()
    emit_alive_beep(asm, halt=False)
    signature_expected_offset = emit_cpu_self_test(asm)
    local_timeout_offsets = emit_local_usart_test(asm)
    train_timeout_offset = emit_train(asm)

    placeholder_payload = bytes((protocol.PROTOCOL_VERSION, ROM_VERSION, 0, 0))
    placeholder_banner = protocol.encode_frame(protocol.TYPE_BANNER, placeholder_payload)
    placeholder_ack = protocol.encode_frame(protocol.TYPE_ACK, placeholder_payload)
    banner_timeout_offsets = emit_table_tx(asm, "banner", len(placeholder_banner))
    banner_empty_timeout_offset = emit_status_wait(
        asm, stem="banner_empty", mask=0x04, failure_label="serial_dead"
    )
    ack_timeout_offsets = emit_ack_rx(asm, len(placeholder_ack))

    serial_ok_delay_offset = emit_serial_ok(asm, halt=False)
    emit_video_pit_init(asm)
    begin_timeout_offsets = emit_fixed_frame(asm, begin_frame, stem="ram_begin")
    survey_metadata = emit_ram_survey(asm)
    end_timeout_offsets = emit_fixed_frame(asm, end_frame, stem="ram_end")
    final_empty_timeout_offset = emit_status_wait(
        asm, stem="ram_end_empty", mask=0x04, failure_label="serial_dead"
    )
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
    asm.label("serial_dead")
    emit_failure_tone(asm, SERIAL_DEAD_TONE_DIVISOR)
    serial_dead_halt = asm.pc
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
    image[IDENTITY_OFFSET : IDENTITY_OFFSET + len(IDENTITY)] = IDENTITY

    checksum_offsets = [
        banner_offset + 6,
        banner_offset + 7,
        ack_offset + 6,
        ack_offset + 7,
    ]
    checksum_zero_offsets = checksum_offsets + [banner_offset + 8, ack_offset + 8]
    checksum_image = bytearray(image)
    for offset in checksum_zero_offsets:
        checksum_image[offset] = 0
    checksum = protocol.crc16_ccitt_false(bytes(checksum_image))
    banner_payload = bytes(
        (protocol.PROTOCOL_VERSION, ROM_VERSION, checksum >> 8, checksum & 0xFF)
    )
    banner = protocol.encode_frame(protocol.TYPE_BANNER, banner_payload)
    ack = protocol.encode_frame(protocol.TYPE_ACK, banner_payload)
    image[banner_offset : banner_offset + len(banner)] = banner
    image[ack_offset : ack_offset + len(ack)] = ack

    metadata: dict[str, int | list[int] | bytes] = {
        "code_size": len(code),
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
        "usart_fail_halt": usart_fail_halt,
        "serial_dead_halt": serial_dead_halt,
        "banner_offset": banner_offset,
        "ack_offset": ack_offset,
        "checksum_offsets": checksum_offsets,
        "checksum_zero_offsets": checksum_zero_offsets,
        "checksum": checksum,
        "banner": banner,
        "ack": ack,
        "begin_frame": begin_frame,
        "end_frame": end_frame,
        **survey_metadata,
    }
    return bytes(image), metadata


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
            raise SystemExit("diag-d0-ram.bin is stale; run build_d0_ram.py")
        if not README.exists() or digest not in README.read_text():
            raise SystemExit("firmware README does not pin the RAM image SHA256")
        action = "checked"
    else:
        OUTPUT.write_bytes(image)
        action = "wrote"
    print(
        f"JUKURAVI-D0-RAM-BUILD: {action} {OUTPUT.name} bytes={len(image)} "
        f"code={metadata['code_size']} signature={EXPECTED_SIGNATURE:02X} "
        f"self_crc16={metadata['checksum']:04X} sha256={digest}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
