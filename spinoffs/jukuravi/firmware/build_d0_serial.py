#!/usr/bin/env python3
"""Build Jukuravi D0 rung 3b: framed external serial handshake."""

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
from build_d0_usart_local import (
    TIMEOUT_COUNT,
    USART_CONTROL,
    USART_DATA,
    USART_FAIL_TONE_DIVISOR,
    USART_TEST_BYTE,
    emit_local_usart_test,
    inp,
)


HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import protocol  # noqa: E402


OUTPUT = HERE / "diag-d0-serial.bin"
README = HERE / "README.md"
IDENTITY_OFFSET = 0x1F00
IDENTITY = b"JUKURAVI-D0-SERIAL-1\0"
ROM_VERSION = 1
TRAIN_LENGTH = 16
SERIAL_OK_TONE_DIVISOR = 1000   # nominal 2 kHz
SERIAL_OK_DELAY_COUNT = 10417    # about 0.125 seconds at nominal 2 MHz
SERIAL_DEAD_TONE_DIVISOR = 16000  # nominal 125 Hz, continuous


def label_address(asm: Assembler, opcode: int, label: str) -> None:
    asm.emit(opcode, 0x00, 0x00)
    asm.fixups.append((asm.pc - 2, label))


def emit_status_wait(
    asm: Assembler, *, stem: str, mask: int, failure_label: str
) -> int:
    timeout_offset = asm.pc + 1
    asm.lxi_b(TIMEOUT_COUNT)
    asm.label(f"{stem}_poll")
    inp(asm, USART_CONTROL)
    asm.emit(0xE6, mask)
    asm.jump(0xC2, f"{stem}_ready")
    asm.emit(0x0B, 0x78, 0xB1)  # DCX B / MOV A,B / ORA C
    asm.jump(0xC2, f"{stem}_poll")
    asm.jump(0xC3, failure_label)
    asm.label(f"{stem}_ready")
    return timeout_offset


def emit_train(asm: Assembler) -> int:
    """The local-test 55 is byte one; emit the remaining train bytes."""
    asm.emit(0x16, TRAIN_LENGTH - 1)  # MVI D,n
    asm.label("train_next")
    timeout = emit_status_wait(
        asm, stem="train_tx", mask=0x01, failure_label="serial_dead"
    )
    asm.mvi_a(USART_TEST_BYTE)
    asm.out(USART_DATA)
    asm.emit(0x15)  # DCR D
    asm.jump(0xC2, "train_next")
    return timeout


def emit_table_tx(asm: Assembler, table_label: str, count: int) -> list[int]:
    label_address(asm, 0x21, table_label)  # LXI H,table
    asm.emit(0x16, count)                 # MVI D,count
    asm.label("banner_next")
    timeout = emit_status_wait(
        asm, stem="banner_tx", mask=0x01, failure_label="serial_dead"
    )
    asm.emit(0x7E)       # MOV A,M
    asm.out(USART_DATA)
    asm.emit(0x23, 0x15)  # INX H / DCR D
    asm.jump(0xC2, "banner_next")
    return [timeout]


def emit_ack_rx(asm: Assembler, count: int) -> list[int]:
    label_address(asm, 0x21, "ack_expected")
    asm.emit(0x16, count)
    asm.label("ack_next")
    timeout = emit_status_wait(
        asm, stem="ack_rx", mask=0x02, failure_label="serial_dead"
    )
    inp(asm, USART_DATA)
    asm.emit(0xBE)  # CMP M
    asm.jump(0xC2, "serial_dead")
    asm.emit(0x23, 0x15)  # INX H / DCR D
    asm.jump(0xC2, "ack_next")
    return [timeout]


def emit_serial_ok(asm: Assembler) -> int:
    emit_failure_tone(asm, SERIAL_OK_TONE_DIVISOR)
    delay_offset = asm.pc + 1
    asm.lxi_b(SERIAL_OK_DELAY_COUNT)
    asm.label("serial_ok_delay")
    asm.emit(0x0B, 0x78, 0xB1)
    asm.jump(0xC2, "serial_ok_delay")
    asm.mvi_a(0x50)
    asm.out(0x1B)
    asm.mvi_a(0x01)
    asm.out(0x19)
    asm.emit(0x76)
    return delay_offset


def build() -> tuple[bytes, dict[str, int | list[int] | bytes]]:
    asm = Assembler()
    emit_alive_beep(asm, halt=False)
    signature_expected_offset = emit_cpu_self_test(asm)
    local_timeout_offsets = emit_local_usart_test(asm)
    train_timeout_offset = emit_train(asm)

    placeholder_payload = bytes((protocol.PROTOCOL_VERSION, ROM_VERSION, 0, 0))
    placeholder_banner = protocol.encode_frame(protocol.TYPE_BANNER, placeholder_payload)
    placeholder_ack = protocol.encode_frame(protocol.TYPE_ACK, placeholder_payload)
    banner_timeout_offsets = emit_table_tx(asm, "banner", len(placeholder_banner))
    tx_empty_timeout_offset = emit_status_wait(
        asm, stem="banner_empty", mask=0x04, failure_label="serial_dead"
    )
    ack_timeout_offsets = emit_ack_rx(asm, len(placeholder_ack))

    serial_ok = asm.pc
    serial_ok_delay_offset = emit_serial_ok(asm)

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

    # The image checksum is defined with every stored copy of its two bytes
    # and the two frame-CRC bytes derived from them zeroed. This avoids both a
    # direct and an indirect fixed-point checksum while covering all other ROM
    # bytes, including identity, executable code, framing fields, and fill.
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
    payload = bytes(
        (protocol.PROTOCOL_VERSION, ROM_VERSION, checksum >> 8, checksum & 0xFF)
    )
    banner = protocol.encode_frame(protocol.TYPE_BANNER, payload)
    ack = protocol.encode_frame(protocol.TYPE_ACK, payload)
    image[banner_offset : banner_offset + len(banner)] = banner
    image[ack_offset : ack_offset + len(ack)] = ack

    metadata: dict[str, int | list[int] | bytes] = {
        "code_size": len(code),
        "signature_expected_offset": signature_expected_offset,
        "local_timeout_offsets": local_timeout_offsets,
        "train_timeout_offset": train_timeout_offset,
        "banner_timeout_offsets": banner_timeout_offsets,
        "tx_empty_timeout_offset": tx_empty_timeout_offset,
        "ack_timeout_offsets": ack_timeout_offsets,
        "serial_ok_delay_offset": serial_ok_delay_offset,
        "serial_ok": serial_ok,
        "serial_ok_halt": asm.labels["cpu_fail"] - 1,
        "cpu_fail_halt": cpu_fail_halt,
        "usart_fail_halt": usart_fail_halt,
        "serial_dead_halt": serial_dead_halt,
        "cpu_fail": asm.labels["cpu_fail"],
        "usart_fail": asm.labels["usart_fail"],
        "serial_dead": asm.labels["serial_dead"],
        "banner_offset": banner_offset,
        "ack_offset": ack_offset,
        "checksum_offsets": checksum_offsets,
        "checksum_zero_offsets": checksum_zero_offsets,
        "checksum": checksum,
        "banner": banner,
        "ack": ack,
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
            raise SystemExit("diag-d0-serial.bin is stale; run build_d0_serial.py")
        if not README.exists() or digest not in README.read_text():
            raise SystemExit("firmware README does not pin the serial image SHA256")
        action = "checked"
    else:
        OUTPUT.write_bytes(image)
        action = "wrote"
    print(
        f"JUKURAVI-D0-SERIAL-BUILD: {action} {OUTPUT.name} bytes={len(image)} "
        f"code={metadata['code_size']} signature={EXPECTED_SIGNATURE:02X} "
        f"self_crc16={metadata['checksum']:04X} sha256={digest}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
