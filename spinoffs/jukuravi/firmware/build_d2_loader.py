#!/usr/bin/env python3
"""Build the cumulative Jukuravi Stage D2 RAM loader image."""

from __future__ import annotations

import argparse
import hashlib
import sys
from pathlib import Path

from build_d0_cpu import EXPECTED_SIGNATURE
from build_d0_ram_fallback import (
    FRAMEBUFFER_END,
    ROM_CHECKSUM_END,
    ROM_CHECKSUM_START,
    build_variant,
    lxi_h,
    lxi_h_label,
)
from build_d0_usart_local import USART_CONTROL, USART_DATA

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import protocol  # noqa: E402


OUTPUT = HERE / "diag-d2-loader.bin"
README = HERE / "README.md"
IDENTITY = b"JUKURAVI-D2-LOADER-1\0"
ROM_VERSION = 9
ENTRY_OFFSET = ROM_CHECKSUM_START

LOADER_API_BASE = 0x0A00
LOADER_API_SERIAL_GET = LOADER_API_BASE
LOADER_API_SERIAL_PUT = LOADER_API_BASE + 3
LOADER_API_RETURN = LOADER_API_BASE + 6
LOADER_API_PRINT = LOADER_API_BASE + 9
LOADER_BUFFER = 0xD800
LOADER_STACK_TOP = FRAMEBUFFER_END
LOAD_MIN_ADDRESS = 0x4000
LOAD_END_ADDRESS = 0xD800


def call(asm, label: str) -> None:
    asm.jump(0xCD, label)


def lda(asm, address: int) -> None:
    asm.emit(0x3A, address & 0xFF, address >> 8)


def emit_send_frame(asm, *, stem: str, table: str, length: int) -> None:
    asm.label(f"loader_send_{stem}")
    lxi_h_label(asm, table)
    asm.emit(0x06, length)  # MVI B,length
    asm.jump(0xC3, "loader_send_table")


def emit_loader(asm) -> dict[str, int | list[int] | bytes]:
    frames = {
        "ready": protocol.encode_frame(
            protocol.TYPE_LOADER_READY,
            bytes(
                (
                    protocol.LOADER_API_VERSION,
                    protocol.LOADER_MAX_DATA,
                    LOADER_API_BASE >> 8,
                    LOADER_API_BASE & 0xFF,
                )
            ),
        ),
        "load_ok": protocol.encode_frame(
            protocol.TYPE_LOAD_RESULT, bytes((protocol.LOADER_STATUS_OK,))
        ),
        "load_bad_length": protocol.encode_frame(
            protocol.TYPE_LOAD_RESULT,
            bytes((protocol.LOADER_STATUS_BAD_LENGTH,)),
        ),
        "load_bad_range": protocol.encode_frame(
            protocol.TYPE_LOAD_RESULT,
            bytes((protocol.LOADER_STATUS_BAD_RANGE,)),
        ),
        "load_verify_failed": protocol.encode_frame(
            protocol.TYPE_LOAD_RESULT,
            bytes((protocol.LOADER_STATUS_VERIFY_FAILED,)),
        ),
        "error_bad_crc": protocol.encode_frame(
            protocol.TYPE_LOADER_ERROR,
            bytes((protocol.LOADER_STATUS_BAD_CRC,)),
        ),
        "error_bad_command": protocol.encode_frame(
            protocol.TYPE_LOADER_ERROR,
            bytes((protocol.LOADER_STATUS_BAD_COMMAND,)),
        ),
        "error_bad_length": protocol.encode_frame(
            protocol.TYPE_LOADER_ERROR,
            bytes((protocol.LOADER_STATUS_BAD_LENGTH,)),
        ),
        "error_bad_range": protocol.encode_frame(
            protocol.TYPE_LOADER_ERROR,
            bytes((protocol.LOADER_STATUS_BAD_RANGE,)),
        ),
        "run_ack": protocol.encode_frame(protocol.TYPE_RUN_ACK, b""),
    }

    api_addresses = {
        "loader_api_serial_get": asm.pc,
    }
    asm.jump(0xC3, "loader_serial_get")
    api_addresses["loader_api_serial_put"] = asm.pc
    asm.jump(0xC3, "loader_serial_put")
    api_addresses["loader_api_return"] = asm.pc
    asm.jump(0xC3, "loader_entry")
    api_addresses["loader_api_print"] = asm.pc
    asm.jump(0xC3, "loader_serial_print")
    if tuple(api_addresses.values()) != (
        LOADER_API_SERIAL_GET,
        LOADER_API_SERIAL_PUT,
        LOADER_API_RETURN,
        LOADER_API_PRINT,
    ):
        raise ValueError("loader API vector addresses differ")

    asm.label("loader_entry")
    asm.emit(0x31, LOADER_STACK_TOP & 0xFF, LOADER_STACK_TOP >> 8)  # LXI SP
    call(asm, "loader_send_ready")

    asm.label("loader_loop")
    call(asm, "loader_receive_frame")
    asm.emit(0xB7)  # ORA A
    asm.jump(0xCA, "loader_dispatch")
    call(asm, "loader_send_error_bad_crc")
    asm.jump(0xC3, "loader_loop")

    asm.label("loader_dispatch")
    lda(asm, LOADER_BUFFER)
    asm.emit(0xFE, protocol.TYPE_LOAD)  # CPI TYPE_LOAD
    asm.jump(0xCA, "loader_load")
    asm.emit(0xFE, protocol.TYPE_RUN)  # CPI TYPE_RUN
    asm.jump(0xCA, "loader_run")
    call(asm, "loader_send_error_bad_command")
    asm.jump(0xC3, "loader_loop")

    # LOAD payload: address high, address low, and 1..253 data bytes.
    asm.label("loader_load")
    lda(asm, LOADER_BUFFER + 1)
    asm.emit(0xFE, 0x03)  # CPI minimum payload length
    asm.jump(0xDA, "loader_load_bad_length")  # JC
    asm.emit(0x47, 0x05, 0x05)  # MOV B,A / DCR B / DCR B = data count
    lxi_h(asm, LOADER_BUFFER + 2)
    asm.emit(0x56, 0x23, 0x5E, 0x23)  # MOV D,M / INX H / MOV E,M / INX H

    asm.emit(0x7A, 0xFE, LOAD_MIN_ADDRESS >> 8)  # MOV A,D / CPI 40
    asm.jump(0xDA, "loader_load_bad_range")
    asm.emit(0xFE, LOAD_END_ADDRESS >> 8)  # CPI D8
    asm.jump(0xD2, "loader_load_bad_range")  # JNC
    asm.emit(0xFE, (LOAD_END_ADDRESS >> 8) - 1)  # CPI D7
    asm.jump(0xC2, "loader_load_copy")
    asm.emit(0x7B, 0x80)  # MOV A,E / ADD B
    asm.jump(0xD2, "loader_load_copy")  # no carry: remains below D800
    asm.jump(0xCA, "loader_load_copy")  # carry+zero: ends exactly at D800
    asm.jump(0xC3, "loader_load_bad_range")

    asm.label("loader_load_copy")
    asm.emit(0x7E, 0x12, 0x1A, 0xBE)  # MOV A,M / STAX D / LDAX D / CMP M
    asm.jump(0xC2, "loader_load_verify_failed")
    asm.emit(0x23, 0x13, 0x05)  # INX H / INX D / DCR B
    asm.jump(0xC2, "loader_load_copy")
    call(asm, "loader_send_load_ok")
    asm.jump(0xC3, "loader_loop")

    asm.label("loader_load_bad_length")
    call(asm, "loader_send_load_bad_length")
    asm.jump(0xC3, "loader_loop")
    asm.label("loader_load_bad_range")
    call(asm, "loader_send_load_bad_range")
    asm.jump(0xC3, "loader_loop")
    asm.label("loader_load_verify_failed")
    call(asm, "loader_send_load_verify_failed")
    asm.jump(0xC3, "loader_loop")

    # RUN accepts one in-range entry address, acknowledges it, drains the UART,
    # and transfers control. Uploaded code returns with JMP 0A06h.
    asm.label("loader_run")
    lda(asm, LOADER_BUFFER + 1)
    asm.emit(0xFE, 0x02)
    asm.jump(0xC2, "loader_run_bad_length")
    lxi_h(asm, LOADER_BUFFER + 2)
    asm.emit(0x56, 0x23, 0x5E)  # MOV D,M / INX H / MOV E,M
    asm.emit(0x7A, 0xFE, LOAD_MIN_ADDRESS >> 8)
    asm.jump(0xDA, "loader_run_bad_range")
    asm.emit(0xFE, LOAD_END_ADDRESS >> 8)
    asm.jump(0xD2, "loader_run_bad_range")
    asm.emit(0xD5)  # PUSH D: preserve entry across response transmission
    call(asm, "loader_send_run_ack")
    call(asm, "loader_wait_tx_empty")
    asm.emit(0xE1, 0xE9)  # POP H / PCHL

    asm.label("loader_run_bad_length")
    call(asm, "loader_send_error_bad_length")
    asm.jump(0xC3, "loader_loop")
    asm.label("loader_run_bad_range")
    call(asm, "loader_send_error_bad_range")
    asm.jump(0xC3, "loader_loop")

    # Receive one standard A5 5A frame into the proven framebuffer workspace.
    # Return A=0 only when CRC-8/ATM covers type, length, and every payload byte.
    asm.label("loader_receive_frame")
    asm.label("loader_sync_first")
    call(asm, "loader_serial_get")
    asm.emit(0xFE, protocol.SYNC[0])
    asm.jump(0xC2, "loader_sync_first")
    call(asm, "loader_serial_get")
    asm.emit(0xFE, protocol.SYNC[1])
    asm.jump(0xC2, "loader_sync_first")
    lxi_h(asm, LOADER_BUFFER)
    asm.emit(0x1E, 0x00)  # MVI E,0 CRC accumulator
    call(asm, "loader_serial_get")
    asm.emit(0x77)  # MOV M,A: type
    call(asm, "loader_crc8_update")
    asm.emit(0x23)
    call(asm, "loader_serial_get")
    asm.emit(0x77, 0x47)  # MOV M,A / MOV B,A: payload count
    call(asm, "loader_crc8_update")
    asm.emit(0x23, 0x78, 0xB7)  # INX H / MOV A,B / ORA A
    asm.jump(0xCA, "loader_payload_done")
    asm.label("loader_payload_next")
    call(asm, "loader_serial_get")
    asm.emit(0x77)
    call(asm, "loader_crc8_update")
    asm.emit(0x23, 0x05)  # INX H / DCR B
    asm.jump(0xC2, "loader_payload_next")
    asm.label("loader_payload_done")
    call(asm, "loader_serial_get")
    asm.emit(0xBB)  # CMP E
    asm.jump(0xC2, "loader_frame_bad_crc")
    asm.emit(0xAF, 0xC9)  # XRA A / RET
    asm.label("loader_frame_bad_crc")
    asm.mvi_a(protocol.LOADER_STATUS_BAD_CRC)
    asm.emit(0xC9)

    asm.label("loader_crc8_update")
    asm.emit(0xAB, 0x16, 0x08)  # XRA E / MVI D,8
    asm.label("loader_crc8_bit")
    asm.emit(0x87)  # ADD A
    asm.jump(0xD2, "loader_crc8_no_xor")
    asm.emit(0xEE, 0x07)
    asm.label("loader_crc8_no_xor")
    asm.emit(0x15)  # DCR D
    asm.jump(0xC2, "loader_crc8_bit")
    asm.emit(0x5F, 0xC9)  # MOV E,A / RET

    asm.label("loader_serial_get")
    asm.label("loader_serial_get_poll")
    asm.emit(0xDB, USART_CONTROL, 0xE6, 0x02)  # IN status / ANI RxRDY
    asm.jump(0xCA, "loader_serial_get_poll")
    asm.emit(0xDB, USART_DATA, 0xC9)  # IN data / RET

    asm.label("loader_serial_put")
    asm.emit(0xF5)  # PUSH PSW
    asm.label("loader_serial_put_poll")
    asm.emit(0xDB, USART_CONTROL, 0xE6, 0x01)  # IN status / ANI TxRDY
    asm.jump(0xCA, "loader_serial_put_poll")
    asm.emit(0xF1, 0xD3, USART_DATA, 0xC9)  # POP PSW / OUT data / RET

    asm.label("loader_wait_tx_empty")
    asm.emit(0xDB, USART_CONTROL, 0xE6, 0x04)
    asm.jump(0xCA, "loader_wait_tx_empty")
    asm.emit(0xC9)

    asm.label("loader_serial_print")
    asm.emit(0x7E, 0xB7, 0xC8)  # MOV A,M / ORA A / RZ
    call(asm, "loader_serial_put")
    asm.emit(0x23)
    asm.jump(0xC3, "loader_serial_print")

    asm.label("loader_send_table")
    asm.label("loader_send_table_next")
    asm.emit(0x7E)  # MOV A,M
    call(asm, "loader_serial_put")
    asm.emit(0x23, 0x05)  # INX H / DCR B
    asm.jump(0xC2, "loader_send_table_next")
    asm.emit(0xC9)

    for stem, frame in frames.items():
        emit_send_frame(
            asm,
            stem=stem,
            table=f"loader_frame_{stem}",
            length=len(frame),
        )

    for stem, frame in frames.items():
        asm.label(f"loader_frame_{stem}")
        asm.emit(*frame)

    return {
        **api_addresses,
        "loader_entry": asm.labels["loader_entry"],
        "loader_loop": asm.labels["loader_loop"],
        "loader_buffer": LOADER_BUFFER,
        "loader_stack_top": LOADER_STACK_TOP,
        "loader_load_min": LOAD_MIN_ADDRESS,
        "loader_load_end": LOAD_END_ADDRESS,
        **{f"loader_{name}_frame": frame for name, frame in frames.items()},
    }


def build() -> tuple[bytes, dict[str, int | list[int] | bytes]]:
    image, metadata = build_variant(
        rom_version=ROM_VERSION,
        identity=IDENTITY,
        rom_convention=True,
        entry_offset=ENTRY_OFFSET,
        pic_check=True,
        compact_fallback=True,
        ppi_check=True,
        pit_check=True,
        framebuffer_pattern=True,
        loader_emitter=emit_loader,
    )
    if (
        metadata["loader_extension_start"] != LOADER_API_BASE
        or metadata["loader_api_serial_get"] != LOADER_API_SERIAL_GET
        or metadata["loader_api_serial_put"] != LOADER_API_SERIAL_PUT
        or metadata["loader_api_return"] != LOADER_API_RETURN
        or metadata["loader_api_print"] != LOADER_API_PRINT
        or metadata["loader_extension_end"] > 0x1F00
    ):
        raise ValueError("fixed loader layout differs")
    return image, metadata


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
            raise SystemExit("diag-d2-loader.bin is stale; run build_d2_loader.py")
        if not README.exists() or digest not in README.read_text():
            raise SystemExit("firmware README does not pin the loader image SHA256")
        action = "checked"
    else:
        OUTPUT.write_bytes(image)
        action = "wrote"
    print(
        f"JUKURAVI-D2-LOADER-BUILD: {action} {OUTPUT.name} "
        f"bytes={len(image)} code={metadata['code_size']} "
        f"loader={metadata['loader_extension_length']} "
        f"signature={EXPECTED_SIGNATURE:02X} "
        f"self_crc16={metadata['checksum']:04X} sha256={digest}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
