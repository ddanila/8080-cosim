#!/usr/bin/env python3
"""Emit the T28 burn-once, host-controlled bootstrap loader."""

from __future__ import annotations

import sys
from pathlib import Path

from build_d0_ram_fallback import lxi_h, lxi_h_label
from build_d0_usart_local import (
    PIT_BAUD_COUNT,
    PIT_CONTROL,
    USART_COMMAND,
    USART_CONTROL,
    USART_DATA,
    USART_MODE,
)
from build_d2_loader import call


HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import protocol  # noqa: E402


LOADER_API_BASE = protocol.LOADER_API_BASE
LOADER_API_SERIAL_GET = LOADER_API_BASE
LOADER_API_SERIAL_PUT = LOADER_API_BASE + 3
LOADER_API_RETURN = LOADER_API_BASE + 6
LOADER_API_PRINT = LOADER_API_BASE + 9

# T28 deliberately keeps its parser and stack in the independently tested
# C000h fallback window, away from the contended D800h framebuffer. Uploaded
# stage-two code lives below C000h and may reclaim this page after RUN.
LOADER_BUFFER = protocol.LOADER_V2_WORKSPACE_BASE
LOADER_STACK_TOP = protocol.LOADER_V2_WORKSPACE_END
LOAD_MIN_ADDRESS = protocol.LOADER_V2_LOAD_MIN
LOAD_END_ADDRESS = protocol.LOADER_V2_LOAD_END
MAX_DATA = protocol.LOADER_V2_MAX_DATA
MAX_PROBE = protocol.LOADER_V2_MAX_PROBE

# Result-state bytes are contiguous so one common response routine can copy
# them into a framed TYPE_LOADER_V2_RESULT payload.
STATE_TX = LOADER_BUFFER + 0x110
STATE_STATUS = STATE_TX + 1
STATE_COMMAND = STATE_TX + 2
STATE_LENGTH = STATE_TX + 3
STATE_ADDRESS_HI = STATE_TX + 4
STATE_ADDRESS_LO = STATE_TX + 5
STATE_COUNT = STATE_TX + 6
STATE_CRC_HI = STATE_TX + 7
STATE_CRC_LO = STATE_TX + 8
STATE_RETRIES = STATE_TX + 9
RESULT_STATE_BYTES = 10
STATE_VOTES = STATE_TX + 10
STATE_SEQUENCE = STATE_TX + 11
STATE_IDLE_TIMEOUTS = STATE_TX + 12
STATE_RETURN_A = STATE_TX + 13
STATE_RUN_VALID = STATE_TX + 14
STATE_RUN_COMPLETE = STATE_TX + 15
STATE_RUN_ID_0 = STATE_TX + 16
STATE_RUN_ID_1 = STATE_TX + 17
STATE_RUN_ID_2 = STATE_TX + 18
STATE_RUN_ID_3 = STATE_TX + 19
STATE_RUN_ADDRESS_HI = STATE_TX + 20
STATE_RUN_ADDRESS_LO = STATE_TX + 21
STATE_RUN_MODE = STATE_TX + 22
PROBE_SCRATCH = LOADER_BUFFER + 0x120

SYMBOL_REQUEST_0 = 0xC6
SYMBOL_REQUEST_1 = 0xC7
BUFFER_STORE_ATTEMPTS = 8
TARGET_STORE_ATTEMPTS = 8
IDLE_TIMEOUTS_BEFORE_DEFAULT = 8
BOOTSTRAP_BAUD_DIVISOR = 32


def lda(asm, address: int) -> None:
    asm.emit(0x3A, address & 0xFF, address >> 8)


def sta(asm, address: int) -> None:
    asm.emit(0x32, address & 0xFF, address >> 8)


def store_immediate(asm, address: int, value: int) -> None:
    asm.mvi_a(value)
    sta(asm, address)


def emit_send_fixed(asm, *, stem: str, table: str, length: int) -> None:
    asm.label(f"t28_send_{stem}")
    lxi_h_label(asm, table)
    asm.emit(0x06, length)  # MVI B,length
    asm.jump(0xC3, "t28_send_table")


def emit_loader(
    asm, *, encoded_input: bool = True, symbol_repetitions: int = 7,
    solicited_input: bool = True, filter_invalid_symbols: bool = True,
    clear_invalid_errors: bool = True, verify_buffer_stores: bool = True,
    bounded_serial_put: bool = False,
    entry_progress_marker: int | None = None,
    avoid_tx_empty: bool = False,
    compact_bounded_serial_put: bool = False,
    boot_votes: int | None = None,
    capabilities: int | None = None,
    refresh_label: str | None = None,
    refresh_mode_address: int | None = None,
    refresh_counter_address: int | None = None,
    external_fixed_frames: bool = False,
    extra_dispatch: tuple[tuple[int, str], ...] = (),
) -> dict[str, int | list[int] | bytes]:
    """Emit T28. Compatibility keyword arguments are validated, not ignored."""
    effective_boot_votes = (
        protocol.LOADER_V2_BOOT_VOTES if boot_votes is None else boot_votes
    )
    effective_capabilities = (
        protocol.LOADER_V2_CAPABILITIES if capabilities is None else capabilities
    )
    if not (
        encoded_input
        and symbol_repetitions == effective_boot_votes
        and solicited_input
        and filter_invalid_symbols
        and clear_invalid_errors
        and verify_buffer_stores
    ):
        raise ValueError("T28 requires its verified solicited transport defaults")
    if entry_progress_marker is not None and not 0 <= entry_progress_marker <= 0xFF:
        raise ValueError("entry progress marker does not fit one byte")
    if not (
        protocol.LOADER_V2_MIN_VOTES <= effective_boot_votes
        <= protocol.LOADER_V2_MAX_VOTES
        and effective_boot_votes & 1
    ):
        raise ValueError("loader boot vote count must be odd and in 1..15")
    if not 0 <= effective_capabilities <= 0xFFFF:
        raise ValueError("loader capabilities do not fit 16 bits")

    ready_payload = bytes(
        (
            protocol.LOADER_V2_API_VERSION,
            MAX_DATA,
            LOADER_API_BASE >> 8,
            LOADER_API_BASE & 0xFF,
            effective_capabilities >> 8,
            effective_capabilities & 0xFF,
            LOAD_MIN_ADDRESS >> 8,
            LOAD_END_ADDRESS >> 8,
            LOADER_BUFFER >> 8,
            LOADER_STACK_TOP >> 8,
            effective_boot_votes,
        )
    )
    frames = {
        "ready": protocol.encode_frame(protocol.TYPE_LOADER_READY, ready_payload),
        "bad_crc": protocol.encode_frame(
            protocol.TYPE_LOADER_ERROR,
            bytes((protocol.LOADER_STATUS_BAD_CRC,)),
        ),
    }

    api_addresses = {"loader_api_serial_get": asm.pc}
    asm.jump(0xC3, "t28_serial_get")
    api_addresses["loader_api_serial_put"] = asm.pc
    asm.jump(0xC3, "t28_serial_put")
    api_addresses["loader_api_return"] = asm.pc
    asm.jump(0xC3, "t28_entry")
    api_addresses["loader_api_print"] = asm.pc
    asm.jump(0xC3, "t28_serial_print")
    if tuple(api_addresses.values()) != (
        LOADER_API_SERIAL_GET,
        LOADER_API_SERIAL_PUT,
        LOADER_API_RETURN,
        LOADER_API_PRINT,
    ):
        raise ValueError("T28 API vector addresses differ")

    # The cumulative diagnostic's guarded handoff uses this historical label;
    # keep it as an alias while the public API still returns through T28.
    asm.label("loader_entry")
    asm.label("t28_entry")
    asm.emit(0x31, LOADER_STACK_TOP & 0xFF, LOADER_STACK_TOP >> 8)  # LXI SP
    store_immediate(asm, STATE_VOTES, effective_boot_votes)
    store_immediate(asm, STATE_SEQUENCE, SYMBOL_REQUEST_0)
    asm.emit(0xAF)
    sta(asm, STATE_IDLE_TIMEOUTS)
    sta(asm, STATE_RUN_VALID)
    if refresh_mode_address is not None:
        sta(asm, refresh_mode_address)
    if refresh_counter_address is not None:
        sta(asm, refresh_counter_address)
        sta(asm, refresh_counter_address + 1)
    if entry_progress_marker is not None:
        asm.mvi_a(entry_progress_marker)
        call(asm, "t28_serial_put")
    call(asm, "t28_send_ready")

    asm.label("t28_loop")
    call(asm, "t28_receive_frame")
    asm.emit(0xB7)  # ORA A
    asm.jump(0xCA, "t28_prepare_dispatch")
    call(asm, "t28_send_bad_crc")
    asm.jump(0xC3, "t28_loop")

    # Snapshot everything needed for a detailed result before a handler is
    # allowed to reuse the parser buffer for its response frame.
    asm.label("t28_prepare_dispatch")
    lda(asm, LOADER_BUFFER)
    sta(asm, STATE_COMMAND)
    lda(asm, LOADER_BUFFER + 1)
    sta(asm, STATE_LENGTH)
    asm.emit(0xAF)
    for address in (
        STATE_TX, STATE_STATUS, STATE_ADDRESS_HI, STATE_ADDRESS_LO,
        STATE_COUNT, STATE_CRC_HI, STATE_CRC_LO,
    ):
        sta(asm, address)
    lda(asm, LOADER_BUFFER + 1)
    asm.emit(0xB7)
    asm.jump(0xCA, "t28_validate_inner")
    lda(asm, LOADER_BUFFER + 2)
    sta(asm, STATE_TX)

    asm.label("t28_validate_inner")
    call(asm, "t28_check_inner_crc")
    asm.emit(0xB7)
    asm.jump(0xCA, "t28_dispatch")
    sta(asm, STATE_STATUS)
    call(asm, "t28_send_result")
    asm.jump(0xC3, "t28_loop")

    asm.label("t28_dispatch")
    lda(asm, STATE_COMMAND)
    for record_type, label in (
        (protocol.TYPE_LOADER_V2_PROBE, "t28_probe"),
        (protocol.TYPE_LOADER_V2_CONFIG, "t28_config"),
        (protocol.TYPE_LOADER_V2_LOAD, "t28_load"),
        (protocol.TYPE_LOADER_V2_READ, "t28_read"),
        (protocol.TYPE_LOADER_V2_CRC, "t28_crc"),
        (protocol.TYPE_LOADER_V2_RUN, "t28_run"),
        (protocol.TYPE_LOADER_V2_RESYNC, "t28_resync"),
        *extra_dispatch,
    ):
        asm.emit(0xFE, record_type)
        asm.jump(0xCA, label)
    asm.mvi_a(protocol.LOADER_STATUS_BAD_COMMAND)
    sta(asm, STATE_STATUS)
    call(asm, "t28_send_result")
    asm.jump(0xC3, "t28_loop")

    # PROBE payload: txid, 0..16 opaque bytes, inner CRC16. DATA echoes the
    # opaque bytes exactly and reports every decoded header field separately.
    asm.label("t28_probe")
    lda(asm, STATE_LENGTH)
    asm.emit(0xFE, 0x03)
    asm.jump(0xDA, "t28_bad_length")
    asm.emit(0xFE, 0x03 + MAX_PROBE + 1)
    asm.jump(0xD2, "t28_bad_length")
    asm.emit(0xD6, 0x03)  # SUI txid+CRC16
    sta(asm, STATE_COUNT)
    asm.emit(0x47)  # MOV B,A
    lxi_h(asm, LOADER_BUFFER + 3)
    asm.emit(0x11, PROBE_SCRATCH & 0xFF, PROBE_SCRATCH >> 8)  # LXI D
    asm.emit(0x78, 0xB7)  # MOV A,B / ORA A
    asm.jump(0xCA, "t28_probe_copied")
    asm.label("t28_probe_copy")
    asm.emit(0x7E, 0x12, 0x23, 0x13, 0x05)  # MOV A,M/STAX D/INX H,D/DCR B
    asm.jump(0xC2, "t28_probe_copy")
    asm.label("t28_probe_copied")
    # DATA bytes start after its six-byte common payload header.
    lxi_h(asm, PROBE_SCRATCH)
    asm.emit(0x11, (LOADER_BUFFER + 8) & 0xFF, (LOADER_BUFFER + 8) >> 8)
    lda(asm, STATE_COUNT)
    asm.emit(0x47, 0xB7)
    asm.jump(0xCA, "t28_probe_ready")
    asm.label("t28_probe_response_copy")
    asm.emit(0x7E, 0x12, 0x23, 0x13, 0x05)
    asm.jump(0xC2, "t28_probe_response_copy")
    asm.label("t28_probe_ready")
    call(asm, "t28_send_data")
    asm.jump(0xC3, "t28_loop")

    # CONFIG payload: txid, odd vote count 1..15, inner CRC16. The response is
    # sent before the next receive uses the new setting, so the host switches
    # only after it has an acknowledged transaction.
    asm.label("t28_config")
    lda(asm, STATE_LENGTH)
    asm.emit(0xFE, 0x04)
    asm.jump(0xC2, "t28_bad_length")
    lda(asm, LOADER_BUFFER + 3)
    asm.emit(0xFE, protocol.LOADER_V2_MIN_VOTES)
    asm.jump(0xDA, "t28_bad_config")
    asm.emit(0xFE, protocol.LOADER_V2_MAX_VOTES + 1)
    asm.jump(0xD2, "t28_bad_config")
    asm.emit(0xE6, 0x01)
    asm.jump(0xCA, "t28_bad_config")
    lda(asm, LOADER_BUFFER + 3)
    sta(asm, STATE_VOTES)
    sta(asm, STATE_COUNT)
    call(asm, "t28_send_result")
    asm.jump(0xC3, "t28_loop")

    # LOAD payload: txid, address-high, address-low, 1..32 bytes, CRC16.
    asm.label("t28_load")
    lda(asm, STATE_LENGTH)
    asm.emit(0xFE, 0x06)
    asm.jump(0xDA, "t28_bad_length")
    asm.emit(0xFE, 0x06 + MAX_DATA)
    asm.jump(0xD2, "t28_bad_length")
    asm.emit(0xD6, 0x05)  # data count = len-(txid+address+CRC16)
    sta(asm, STATE_COUNT)
    lda(asm, LOADER_BUFFER + 3)
    sta(asm, STATE_ADDRESS_HI)
    lda(asm, LOADER_BUFFER + 4)
    sta(asm, STATE_ADDRESS_LO)
    call(asm, "t28_check_range")
    asm.emit(0xB7)
    asm.jump(0xC2, "t28_bad_range")
    lxi_h(asm, LOADER_BUFFER + 5)
    lda(asm, STATE_ADDRESS_HI)
    asm.emit(0x57)
    lda(asm, STATE_ADDRESS_LO)
    asm.emit(0x5F)
    lda(asm, STATE_COUNT)
    asm.emit(0x47)
    asm.label("t28_load_copy")
    call(asm, "t28_target_store")
    asm.emit(0xB7)
    asm.jump(0xC2, "t28_verify_failed")
    asm.emit(0x23, 0x13, 0x05)
    asm.jump(0xC2, "t28_load_copy")
    call(asm, "t28_crc_state_range")
    call(asm, "t28_send_result")
    asm.jump(0xC3, "t28_loop")

    # READ and CRC payload: txid, address-high, address-low, count, CRC16.
    asm.label("t28_read")
    call(asm, "t28_prepare_range_command")
    asm.emit(0xB7)
    asm.jump(0xC2, "t28_range_command_error")
    lda(asm, STATE_ADDRESS_HI)
    asm.emit(0x67)
    lda(asm, STATE_ADDRESS_LO)
    asm.emit(0x6F)
    asm.emit(0x11, (LOADER_BUFFER + 8) & 0xFF, (LOADER_BUFFER + 8) >> 8)
    lda(asm, STATE_COUNT)
    asm.emit(0x47)
    asm.label("t28_read_copy")
    asm.emit(0x7E, 0x12, 0x23, 0x13, 0x05)
    asm.jump(0xC2, "t28_read_copy")
    call(asm, "t28_crc_state_range")
    call(asm, "t28_send_data")
    asm.jump(0xC3, "t28_loop")

    asm.label("t28_crc")
    call(asm, "t28_prepare_range_command")
    asm.emit(0xB7)
    asm.jump(0xC2, "t28_range_command_error")
    call(asm, "t28_crc_state_range")
    call(asm, "t28_send_result")
    asm.jump(0xC3, "t28_loop")

    asm.label("t28_range_command_error")
    sta(asm, STATE_STATUS)
    call(asm, "t28_send_result")
    asm.jump(0xC3, "t28_loop")

    # RUN payload: txid, entry address, mode, 32-bit execution ID, CRC16.
    # CALL mode pushes a ROM continuation so an ordinary 8080 RET returns A
    # to the host and leaves the loader live. An exact duplicate execution ID
    # replays the completed result rather than invoking non-idempotent code a
    # second time. JUMP mode is reserved for non-returning software.
    asm.label("t28_run")
    lda(asm, STATE_LENGTH)
    asm.emit(0xFE, 0x0A)
    asm.jump(0xC2, "t28_bad_length")
    lda(asm, LOADER_BUFFER + 3)
    sta(asm, STATE_ADDRESS_HI)
    lda(asm, LOADER_BUFFER + 4)
    sta(asm, STATE_ADDRESS_LO)
    lda(asm, LOADER_BUFFER + 5)
    asm.emit(0xFE, protocol.LOADER_V2_RUN_JUMP + 1)
    asm.jump(0xD2, "t28_bad_config")
    sta(asm, STATE_COUNT)  # execution mode is reported in the count field
    # Range validation needs a nonzero span even though RUN does not write.
    asm.emit(0xF5)
    store_immediate(asm, STATE_COUNT, 1)
    call(asm, "t28_check_range")
    asm.emit(0x47, 0xF1)  # preserve range status across restored mode
    sta(asm, STATE_COUNT)
    asm.emit(0x78, 0xB7)
    asm.jump(0xC2, "t28_bad_range")

    # A retransmission after a damaged/lost ACK or RETURN must not execute the
    # snippet twice. Match the independent execution ID and all invocation
    # fields before replaying the cached completion.
    lda(asm, STATE_RUN_VALID)
    asm.emit(0xB7)
    asm.jump(0xCA, "t28_run_new")
    for incoming, saved in (
        (LOADER_BUFFER + 6, STATE_RUN_ID_0),
        (LOADER_BUFFER + 7, STATE_RUN_ID_1),
        (LOADER_BUFFER + 8, STATE_RUN_ID_2),
        (LOADER_BUFFER + 9, STATE_RUN_ID_3),
        (LOADER_BUFFER + 3, STATE_RUN_ADDRESS_HI),
        (LOADER_BUFFER + 4, STATE_RUN_ADDRESS_LO),
        (LOADER_BUFFER + 5, STATE_RUN_MODE),
    ):
        lda(asm, incoming)
        asm.emit(0x47)  # MOV B,A
        lda(asm, saved)
        asm.emit(0xB8)  # CMP B
        asm.jump(0xC2, "t28_run_new")
    call(asm, "t28_send_result")
    lda(asm, STATE_RUN_COMPLETE)
    asm.emit(0xB7)
    asm.jump(0xCA, "t28_loop")
    call(asm, "t28_send_return")
    asm.jump(0xC3, "t28_loop")

    asm.label("t28_run_new")
    for incoming, saved in (
        (LOADER_BUFFER + 6, STATE_RUN_ID_0),
        (LOADER_BUFFER + 7, STATE_RUN_ID_1),
        (LOADER_BUFFER + 8, STATE_RUN_ID_2),
        (LOADER_BUFFER + 9, STATE_RUN_ID_3),
        (LOADER_BUFFER + 3, STATE_RUN_ADDRESS_HI),
        (LOADER_BUFFER + 4, STATE_RUN_ADDRESS_LO),
        (LOADER_BUFFER + 5, STATE_RUN_MODE),
    ):
        lda(asm, incoming)
        sta(asm, saved)
    asm.emit(0xAF)
    sta(asm, STATE_RUN_COMPLETE)
    asm.mvi_a(1)
    sta(asm, STATE_RUN_VALID)
    call(asm, "t28_send_result")
    call(asm, "t28_wait_tx_empty")
    lda(asm, STATE_ADDRESS_HI)
    asm.emit(0x57)
    lda(asm, STATE_ADDRESS_LO)
    asm.emit(0x5F)
    lda(asm, STATE_COUNT)
    asm.emit(0xB7)
    asm.jump(0xC2, "t28_run_jump")
    lxi_h_label(asm, "t28_run_returned")
    asm.emit(0xE5, 0x62, 0x6B, 0xE9)  # PUSH continuation / MOV H,D / MOV L,E / PCHL
    asm.label("t28_run_jump")
    asm.emit(0x62, 0x6B, 0xE9)
    asm.label("t28_run_returned")
    sta(asm, STATE_RETURN_A)
    # A cooperative snippet only promises RET and a returned A. Recover the
    # remaining machine state that the immutable loader depends upon before
    # touching the wire again: interrupts off, known stack, and 2400-baud
    # 8251/PIT programming. This lets exploratory snippets use those resources
    # temporarily without forcing a board RESET afterward.
    asm.emit(0xF3)  # DI
    asm.emit(0x31, LOADER_STACK_TOP & 0xFF, LOADER_STACK_TOP >> 8)  # LXI SP
    call(asm, "t28_restore_serial")
    asm.mvi_a(1)
    sta(asm, STATE_RUN_COMPLETE)
    call(asm, "t28_send_return")
    asm.jump(0xC3, "t28_loop")

    # RESYNC returns to known transport defaults without a hardware RESET.
    asm.label("t28_resync")
    lda(asm, STATE_LENGTH)
    asm.emit(0xFE, 0x03)
    asm.jump(0xC2, "t28_bad_length")
    store_immediate(asm, STATE_VOTES, effective_boot_votes)
    if refresh_mode_address is not None:
        # Any value other than T35's complete disable signature is refresh-on.
        # Reusing the boot-vote A value makes RESYNC explicitly fail safe.
        sta(asm, refresh_mode_address)
    store_immediate(asm, STATE_SEQUENCE, SYMBOL_REQUEST_0)
    store_immediate(asm, STATE_COUNT, effective_boot_votes)
    call(asm, "t28_send_result")
    asm.jump(0xC3, "t28_loop")

    asm.label("t28_bad_length")
    asm.mvi_a(protocol.LOADER_STATUS_BAD_LENGTH)
    sta(asm, STATE_STATUS)
    call(asm, "t28_send_result")
    asm.jump(0xC3, "t28_loop")
    asm.label("t28_bad_config")
    asm.mvi_a(protocol.LOADER_STATUS_BAD_CONFIG)
    sta(asm, STATE_STATUS)
    call(asm, "t28_send_result")
    asm.jump(0xC3, "t28_loop")
    asm.label("t28_bad_range")
    asm.mvi_a(protocol.LOADER_STATUS_BAD_RANGE)
    sta(asm, STATE_STATUS)
    call(asm, "t28_send_result")
    asm.jump(0xC3, "t28_loop")

    asm.label("t28_restore_serial")
    # Force the 8251 back to mode-instruction state, then restore the exact
    # bootstrap format and D57 channel-0 baud clock used at startup.
    for value in (0x00, 0x00, 0x00, 0x40, USART_MODE, USART_COMMAND):
        asm.mvi_a(value)
        asm.out(USART_CONTROL)
    asm.mvi_a(0x34)  # D57 channel 0, mode 2, LSB then MSB
    asm.out(PIT_CONTROL)
    asm.mvi_a(BOOTSTRAP_BAUD_DIVISOR & 0xFF)
    asm.out(PIT_BAUD_COUNT)
    asm.mvi_a(BOOTSTRAP_BAUD_DIVISOR >> 8)
    asm.out(PIT_BAUD_COUNT)
    asm.emit(0xC9)  # RET
    asm.label("t28_verify_failed")
    sta(asm, STATE_STATUS)  # target-store helper returned VERIFY_FAILED
    call(asm, "t28_send_result")
    asm.jump(0xC3, "t28_loop")

    # Exact length/range setup shared by READ and CRC.
    asm.label("t28_prepare_range_command")
    lda(asm, STATE_LENGTH)
    asm.emit(0xFE, 0x06)
    asm.jump(0xC2, "t28_prepare_range_bad_length")
    lda(asm, LOADER_BUFFER + 3)
    sta(asm, STATE_ADDRESS_HI)
    lda(asm, LOADER_BUFFER + 4)
    sta(asm, STATE_ADDRESS_LO)
    lda(asm, LOADER_BUFFER + 5)
    sta(asm, STATE_COUNT)
    asm.emit(0xB7)
    asm.jump(0xCA, "t28_prepare_range_bad_length")
    asm.emit(0xFE, MAX_DATA + 1)
    asm.jump(0xD2, "t28_prepare_range_bad_length")
    call(asm, "t28_check_range")
    asm.emit(0xC9)
    asm.label("t28_prepare_range_bad_length")
    asm.mvi_a(protocol.LOADER_STATUS_BAD_LENGTH)
    asm.emit(0xC9)

    # Return A=0 only for [4000h,C000h), allowing an end exactly at C000h.
    asm.label("t28_check_range")
    lda(asm, STATE_ADDRESS_HI)
    asm.emit(0xFE, LOAD_MIN_ADDRESS >> 8)
    asm.jump(0xDA, "t28_check_range_bad")
    asm.emit(0xFE, LOAD_END_ADDRESS >> 8)
    asm.jump(0xD2, "t28_check_range_bad")
    asm.emit(0xFE, (LOAD_END_ADDRESS >> 8) - 1)
    asm.jump(0xC2, "t28_check_range_ok")
    lda(asm, STATE_ADDRESS_LO)
    asm.emit(0x47)
    lda(asm, STATE_COUNT)
    asm.emit(0x80)  # ADD B
    asm.jump(0xD2, "t28_check_range_ok")
    asm.jump(0xCA, "t28_check_range_ok")
    asm.label("t28_check_range_bad")
    asm.mvi_a(protocol.LOADER_STATUS_BAD_RANGE)
    asm.emit(0xC9)
    asm.label("t28_check_range_ok")
    asm.emit(0xAF, 0xC9)  # XRA A / RET

    # Compute CRC16 over the state range and retain it in the result state.
    asm.label("t28_crc_state_range")
    lda(asm, STATE_ADDRESS_HI)
    asm.emit(0x67)
    lda(asm, STATE_ADDRESS_LO)
    asm.emit(0x6F)
    lda(asm, STATE_COUNT)
    asm.emit(0x47)
    call(asm, "t28_crc16_range")
    asm.emit(0x7A)
    sta(asm, STATE_CRC_HI)
    asm.emit(0x7B)
    sta(asm, STATE_CRC_LO)
    asm.emit(0xC9)

    # Outer A5/5A/CRC8 parser. Each authoritative byte is read back from the
    # C000h buffer; eight failures abort safely before dispatch.
    asm.label("t28_receive_frame")
    asm.label("t28_sync_first")
    call(asm, "t28_serial_get")
    asm.emit(0xFE, protocol.SYNC[0])
    asm.jump(0xC2, "t28_sync_first")
    call(asm, "t28_serial_get")
    asm.emit(0xFE, protocol.SYNC[1])
    asm.jump(0xC2, "t28_sync_first")
    asm.emit(0xAF)
    sta(asm, STATE_RETRIES)
    lxi_h(asm, LOADER_BUFFER)
    asm.emit(0x1E, 0x00)  # E=outer CRC8
    call(asm, "t28_serial_get")
    call(asm, "t28_buffer_store")
    call(asm, "t28_crc8_update")
    asm.emit(0x23)
    call(asm, "t28_serial_get")
    call(asm, "t28_buffer_store")
    asm.emit(0x47)  # B=payload count
    call(asm, "t28_crc8_update")
    asm.emit(0x23, 0x78, 0xB7)
    asm.jump(0xCA, "t28_payload_done")
    asm.label("t28_payload_next")
    call(asm, "t28_serial_get")
    call(asm, "t28_buffer_store")
    call(asm, "t28_crc8_update")
    asm.emit(0x23, 0x05)
    asm.jump(0xC2, "t28_payload_next")
    asm.label("t28_payload_done")
    call(asm, "t28_serial_get")
    asm.emit(0xBB)  # CMP E
    asm.jump(0xC2, "t28_outer_bad_crc")
    asm.emit(0xAF, 0xC9)
    asm.label("t28_outer_bad_crc")
    asm.mvi_a(protocol.LOADER_STATUS_BAD_CRC)
    asm.emit(0xC9)

    asm.label("t28_buffer_store")
    asm.emit(0xC5, 0x06, BUFFER_STORE_ATTEMPTS)  # PUSH B / MVI B,n
    asm.label("t28_buffer_store_try")
    asm.emit(0x77, 0xBE)  # MOV M,A / CMP M
    asm.jump(0xCA, "t28_buffer_store_ok")
    asm.emit(0xF5)
    lda(asm, STATE_RETRIES)
    asm.emit(0x3C)
    sta(asm, STATE_RETRIES)
    asm.emit(0xF1, 0x05)
    asm.jump(0xC2, "t28_buffer_store_try")
    asm.emit(0xC1)
    asm.jump(0xC3, "t28_transport_failure")
    asm.label("t28_buffer_store_ok")
    asm.emit(0xC1, 0xC9)

    asm.label("t28_target_store")
    asm.emit(0xC5, 0xE5, 0x06, TARGET_STORE_ATTEMPTS)
    asm.label("t28_target_store_try")
    asm.emit(0x7E, 0x12, 0x1A, 0xBE)
    asm.jump(0xCA, "t28_target_store_ok")
    lda(asm, STATE_RETRIES)
    asm.emit(0x3C)
    sta(asm, STATE_RETRIES)
    asm.emit(0x05)
    asm.jump(0xC2, "t28_target_store_try")
    asm.emit(0xE1, 0xC1)
    asm.mvi_a(protocol.LOADER_STATUS_VERIFY_FAILED)
    asm.emit(0xC9)
    asm.label("t28_target_store_ok")
    asm.emit(0xE1, 0xC1, 0xAF, 0xC9)

    asm.label("t28_crc8_update")
    asm.emit(0xAB, 0x16, 0x08)  # XRA E / MVI D,8
    asm.label("t28_crc8_bit")
    asm.emit(0x87)
    asm.jump(0xD2, "t28_crc8_no_xor")
    asm.emit(0xEE, 0x07)
    asm.label("t28_crc8_no_xor")
    asm.emit(0x15)
    asm.jump(0xC2, "t28_crc8_bit")
    asm.emit(0x5F, 0xC9)

    # Validate inner CRC16 over type, final length, transaction and body as
    # actually stored in C000h. Return STRONG_CRC on any discrepancy.
    asm.label("t28_check_inner_crc")
    lda(asm, STATE_LENGTH)
    asm.emit(0xFE, 0x03)
    asm.jump(0xDA, "t28_inner_bad")
    asm.emit(0x47)
    lxi_h(asm, LOADER_BUFFER)
    call(asm, "t28_crc16_range")
    asm.emit(0x7A, 0xBE)
    asm.jump(0xC2, "t28_inner_bad")
    asm.emit(0x23, 0x7B, 0xBE)
    asm.jump(0xC2, "t28_inner_bad")
    asm.emit(0xAF, 0xC9)
    asm.label("t28_inner_bad")
    asm.mvi_a(protocol.LOADER_STATUS_STRONG_CRC)
    asm.emit(0xC9)

    # Input HL=start, B=count; output DE=CRC16/CCITT-FALSE.
    asm.label("t28_crc16_range")
    asm.emit(0x11, 0xFF, 0xFF)  # LXI D,FFFFh
    asm.label("t28_crc16_range_next")
    asm.emit(0x7E)
    call(asm, "t28_crc16_update")
    asm.emit(0x23, 0x05)
    asm.jump(0xC2, "t28_crc16_range_next")
    asm.emit(0xC9)

    # Input A=next byte, DE=CRC; output DE=updated CRC. Preserve B/count.
    asm.label("t28_crc16_update")
    asm.emit(0xC5, 0xAA, 0x57, 0x0E, 0x08)  # PUSH B / XRA D / MOV D,A / C=8
    asm.label("t28_crc16_bit")
    asm.emit(0x7B, 0x87, 0x5F, 0x7A, 0x17, 0x57)  # shift DE left
    asm.jump(0xD2, "t28_crc16_no_xor")
    asm.emit(0x7A, 0xEE, 0x10, 0x57, 0x7B, 0xEE, 0x21, 0x5F)
    asm.label("t28_crc16_no_xor")
    asm.emit(0x0D)
    asm.jump(0xC2, "t28_crc16_bit")
    asm.emit(0xC1, 0xC9)

    # Receiver-driven, filtered, host-configurable majority decoder.
    asm.label("t28_serial_get")
    asm.jump(0xC3, "t28_vote_entry")
    asm.label("t28_vote_raw_get")
    asm.emit(0xC5, 0xD5, 0xE5)
    asm.label("t28_vote_request")
    lda(asm, STATE_SEQUENCE)
    call(asm, "t28_serial_put")
    asm.lxi_b(0x0100 if refresh_label is not None else 0xFFFF)
    asm.label("t28_vote_raw_poll")
    if refresh_label is not None:
        call(asm, refresh_label)
        if refresh_counter_address is not None:
            asm.emit(
                0x2A,
                refresh_counter_address & 0xFF,
                refresh_counter_address >> 8,
                0x23,
                0x22,
                refresh_counter_address & 0xFF,
                refresh_counter_address >> 8,
            )  # LHLD counter / INX H / SHLD counter
    asm.emit(0xDB, USART_CONTROL, 0xE6, 0x02)
    asm.jump(0xC2, "t28_vote_raw_ready")
    asm.emit(0x0B, 0x78, 0xB1)
    asm.jump(0xC2, "t28_vote_raw_poll")
    lda(asm, STATE_IDLE_TIMEOUTS)
    asm.emit(0x3C)
    sta(asm, STATE_IDLE_TIMEOUTS)
    asm.emit(0xFE, IDLE_TIMEOUTS_BEFORE_DEFAULT)
    asm.jump(0xDA, "t28_vote_request")
    # Do not change vote width in the middle of a logical byte. Abandon the
    # entire partial parser stack and restart framing at the documented
    # baseline, which makes a later host attach deterministic.
    asm.jump(0xC3, "t28_idle_transport_reset")
    asm.label("t28_vote_raw_ready")
    asm.emit(0xDB, USART_DATA, 0xFE, 0x55)
    asm.jump(0xCA, "t28_vote_raw_valid")
    asm.emit(0xFE, 0xAA)
    asm.jump(0xCA, "t28_vote_raw_valid")
    asm.mvi_a(USART_COMMAND)
    asm.out(USART_CONTROL)
    asm.lxi_b(0x0100 if refresh_label is not None else 0xFFFF)
    asm.jump(0xC3, "t28_vote_raw_poll")
    asm.label("t28_vote_raw_valid")
    asm.emit(0xF5)
    asm.mvi_a(USART_COMMAND)
    asm.out(USART_CONTROL)
    lda(asm, STATE_SEQUENCE)
    asm.emit(0xEE, 0x01)
    sta(asm, STATE_SEQUENCE)
    asm.emit(0xAF)
    sta(asm, STATE_IDLE_TIMEOUTS)
    asm.emit(0xF1, 0xE1, 0xD1, 0xC1, 0xC9)

    asm.label("t28_vote_entry")
    asm.emit(0xC5, 0xD5, 0xE5, 0x06, 0x00, 0x0E, 0x08)
    asm.label("t28_vote_bit")
    asm.emit(0x16, 0x00, 0x26, 0x00)
    lda(asm, STATE_VOTES)
    asm.emit(0x5F)
    asm.label("t28_vote_sample")
    call(asm, "t28_vote_raw_get")
    asm.emit(0xFE, 0xAA)
    asm.jump(0xC2, "t28_vote_not_one")
    asm.emit(0x14)
    asm.jump(0xC3, "t28_vote_count")
    asm.label("t28_vote_not_one")
    asm.emit(0xFE, 0x55)
    asm.jump(0xC2, "t28_vote_count")
    asm.emit(0x24)
    asm.label("t28_vote_count")
    asm.emit(0x1D)
    asm.jump(0xC2, "t28_vote_sample")
    asm.emit(0x7C, 0xBA)
    asm.jump(0xDA, "t28_vote_one")
    asm.emit(0x78, 0x87, 0x47)
    asm.jump(0xC3, "t28_vote_next_bit")
    asm.label("t28_vote_one")
    asm.emit(0x78, 0x87, 0x47, 0x04)
    asm.label("t28_vote_next_bit")
    asm.emit(0x0D)
    asm.jump(0xC2, "t28_vote_bit")
    asm.emit(0x78, 0xE1, 0xD1, 0xC1, 0xC9)

    asm.label("t28_idle_transport_reset")
    asm.emit(0x31, LOADER_STACK_TOP & 0xFF, LOADER_STACK_TOP >> 8)
    store_immediate(asm, STATE_VOTES, effective_boot_votes)
    if refresh_mode_address is not None:
        sta(asm, refresh_mode_address)
    store_immediate(asm, STATE_SEQUENCE, SYMBOL_REQUEST_0)
    asm.emit(0xAF)
    sta(asm, STATE_IDLE_TIMEOUTS)
    asm.jump(0xC3, "t28_loop")

    asm.label("t28_transport_failure")
    asm.emit(0x31, LOADER_STACK_TOP & 0xFF, LOADER_STACK_TOP >> 8)
    store_immediate(asm, STATE_VOTES, effective_boot_votes)
    if refresh_mode_address is not None:
        sta(asm, refresh_mode_address)
    store_immediate(asm, STATE_SEQUENCE, SYMBOL_REQUEST_0)
    call(asm, "t28_send_bad_crc")
    asm.jump(0xC3, "t28_loop")

    asm.label("t28_serial_put")
    asm.emit(0xF5)  # PUSH PSW: retain the requested byte
    if bounded_serial_put and compact_bounded_serial_put:
        # Two attempts with one shared poll loop. D is saved explicitly and
        # reused as the attempt counter; this is thirteen bytes smaller than
        # the fully duplicated T29 form and keeps the complete loader below
        # the physical board's suspect 1000h execution boundary.
        asm.emit(0xC5, 0xD5, 0x16, 0x02)  # PUSH B / PUSH D / MVI D,2
        asm.label("t28_serial_put_compact_attempt")
        if refresh_label is not None:
            asm.emit(0x01, 0x00, 0x01)  # LXI B,0100h
        else:
            asm.emit(0x01, 0xFF, 0xFF)  # LXI B,FFFFh
        asm.label("t28_serial_put_compact_poll")
        if refresh_label is not None:
            call(asm, refresh_label)
        asm.emit(0xDB, USART_CONTROL, 0xE6, 0x01)
        asm.jump(0xC2, "t28_serial_put_compact_ready")
        asm.emit(0x0B, 0x78, 0xB1)
        asm.jump(0xC2, "t28_serial_put_compact_poll")
        asm.emit(0x15)  # DCR D
        asm.jump(0xCA, "uart_dead")
        call(asm, "t28_restore_serial")
        asm.jump(0xC3, "t28_serial_put_compact_attempt")
        asm.label("t28_serial_put_compact_ready")
        asm.emit(0xD1, 0xC1)  # POP D / POP B
    elif bounded_serial_put:
        # T28's original unbounded TxRDY poll could silently wait forever on
        # hardware even though all preceding diagnostics had transmitted.
        # Preserve BC for table loops, bound the wait, restore the known 8251
        # and PIT setup once, then take the existing audible UART-failure path
        # if the recovered transmitter still cannot become ready.
        asm.emit(0xC5, 0x01, 0xFF, 0xFF)  # PUSH B / LXI B,FFFFh
        asm.label("t28_serial_put_poll")
        if refresh_label is not None:
            call(asm, refresh_label)
        asm.emit(0xDB, USART_CONTROL, 0xE6, 0x01)
        asm.jump(0xC2, "t28_serial_put_ready")
        asm.emit(0x0B, 0x78, 0xB1)
        asm.jump(0xC2, "t28_serial_put_poll")
        call(asm, "t28_restore_serial")
        asm.emit(0x01, 0xFF, 0xFF)  # LXI B,FFFFh
        asm.label("t28_serial_put_recovered_poll")
        if refresh_label is not None:
            call(asm, refresh_label)
        asm.emit(0xDB, USART_CONTROL, 0xE6, 0x01)
        asm.jump(0xC2, "t28_serial_put_ready")
        asm.emit(0x0B, 0x78, 0xB1)
        asm.jump(0xC2, "t28_serial_put_recovered_poll")
        asm.jump(0xC3, "uart_dead")
        asm.label("t28_serial_put_ready")
        asm.emit(0xC1)  # POP B
    else:
        asm.label("t28_serial_put_poll")
        if refresh_label is not None:
            call(asm, refresh_label)
        asm.emit(0xDB, USART_CONTROL, 0xE6, 0x01)
        asm.jump(0xCA, "t28_serial_put_poll")
    asm.emit(0xF1, 0xD3, USART_DATA, 0xC9)

    asm.label("t28_wait_tx_empty")
    if refresh_label is not None:
        # Sixteen complete 128-row sweeps exceed four 2400-baud character
        # times even at the measured slow CS00024 CPU rate. The refresh
        # routine preserves B, so it is also a reliable Tx-drain delay on
        # 8251 variants whose TxEMPTY indication cannot be trusted.
        asm.emit(0xC5, 0x06, 16)  # PUSH B / MVI B,16
        asm.label("t28_tx_drain_refresh")
        call(asm, refresh_label)
        asm.emit(0x05)
        asm.jump(0xC2, "t28_tx_drain_refresh")
        asm.emit(0xC1)
    elif avoid_tx_empty:
        # Some real 8251-compatible parts keep status bit 2 low even after the
        # byte has appeared on the wire. Preserve BC and wait longer than four
        # 2400-baud characters without consulting that unreliable indication.
        asm.emit(0xC5, 0x01, 0x00, 0x08)  # PUSH B / LXI B,0800h
        asm.label("t28_tx_drain_delay")
        asm.emit(0x0B, 0x78, 0xB1)
        asm.jump(0xC2, "t28_tx_drain_delay")
        asm.emit(0xC1)  # POP B
    elif bounded_serial_put:
        asm.emit(0xC5, 0x01, 0xFF, 0xFF)  # PUSH B / LXI B,FFFFh
        asm.label("t28_wait_tx_empty_poll")
        asm.emit(0xDB, USART_CONTROL, 0xE6, 0x04)
        asm.jump(0xC2, "t28_wait_tx_empty_ready")
        asm.emit(0x0B, 0x78, 0xB1)
        asm.jump(0xC2, "t28_wait_tx_empty_poll")
        call(asm, "t28_restore_serial")
        asm.emit(0x01, 0xFF, 0xFF)
        asm.label("t28_wait_tx_empty_recovered_poll")
        asm.emit(0xDB, USART_CONTROL, 0xE6, 0x04)
        asm.jump(0xC2, "t28_wait_tx_empty_ready")
        asm.emit(0x0B, 0x78, 0xB1)
        asm.jump(0xC2, "t28_wait_tx_empty_recovered_poll")
        asm.jump(0xC3, "uart_dead")
        asm.label("t28_wait_tx_empty_ready")
        asm.emit(0xC1)  # POP B
    else:
        asm.emit(0xDB, USART_CONTROL, 0xE6, 0x04)
        asm.jump(0xCA, "t28_wait_tx_empty")
    asm.emit(0xC9)

    asm.label("t28_serial_print")
    asm.emit(0x7E, 0xB7, 0xC8)
    call(asm, "t28_serial_put")
    asm.emit(0x23)
    asm.jump(0xC3, "t28_serial_print")

    asm.label("t28_send_table")
    asm.label("t28_send_table_next")
    asm.emit(0x7E)
    call(asm, "t28_serial_put")
    asm.emit(0x23, 0x05)
    asm.jump(0xC2, "t28_send_table_next")
    asm.emit(0xC9)

    # Build a common detailed result from the contiguous state record.
    asm.label("t28_send_result")
    store_immediate(asm, LOADER_BUFFER, protocol.TYPE_LOADER_V2_RESULT)
    store_immediate(asm, LOADER_BUFFER + 1, RESULT_STATE_BYTES)
    lxi_h(asm, STATE_TX)
    asm.emit(0x11, (LOADER_BUFFER + 2) & 0xFF, (LOADER_BUFFER + 2) >> 8)
    asm.emit(0x06, RESULT_STATE_BYTES)
    asm.label("t28_result_copy")
    asm.emit(0x7E, 0x12, 0x23, 0x13, 0x05)
    asm.jump(0xC2, "t28_result_copy")
    asm.jump(0xC3, "t28_send_dynamic")

    # DATA payload header: txid,status,command,address-hi,address-lo,count.
    # Callers place count data bytes at BUFFER+8 before entering.
    asm.label("t28_send_data")
    store_immediate(asm, LOADER_BUFFER, protocol.TYPE_LOADER_V2_DATA)
    lda(asm, STATE_COUNT)
    asm.emit(0xC6, 0x06)
    sta(asm, LOADER_BUFFER + 1)
    for source, destination in (
        (STATE_TX, LOADER_BUFFER + 2),
        (STATE_STATUS, LOADER_BUFFER + 3),
        (STATE_COMMAND, LOADER_BUFFER + 4),
        (STATE_ADDRESS_HI, LOADER_BUFFER + 5),
        (STATE_ADDRESS_LO, LOADER_BUFFER + 6),
        (STATE_COUNT, LOADER_BUFFER + 7),
    ):
        lda(asm, source)
        sta(asm, destination)
    asm.jump(0xC3, "t28_send_dynamic")

    asm.label("t28_send_return")
    store_immediate(asm, LOADER_BUFFER, protocol.TYPE_LOADER_V2_RETURN)
    store_immediate(asm, LOADER_BUFFER + 1, 3)
    lda(asm, STATE_TX)
    sta(asm, LOADER_BUFFER + 2)
    lda(asm, STATE_STATUS)
    sta(asm, LOADER_BUFFER + 3)
    lda(asm, STATE_RETURN_A)
    sta(asm, LOADER_BUFFER + 4)
    asm.jump(0xC3, "t28_send_dynamic")

    asm.label("t28_send_dynamic")
    asm.mvi_a(protocol.SYNC[0])
    call(asm, "t28_serial_put")
    asm.mvi_a(protocol.SYNC[1])
    call(asm, "t28_serial_put")
    lda(asm, LOADER_BUFFER + 1)
    asm.emit(0xC6, 0x02, 0x47)  # ADI 2 / MOV B,A
    lxi_h(asm, LOADER_BUFFER)
    asm.emit(0x1E, 0x00)
    asm.label("t28_dynamic_next")
    asm.emit(0x7E)
    call(asm, "t28_serial_put")
    call(asm, "t28_crc8_update")
    asm.emit(0x23, 0x05)
    asm.jump(0xC2, "t28_dynamic_next")
    asm.emit(0x7B)
    call(asm, "t28_serial_put")
    asm.emit(0xC9)

    if not external_fixed_frames:
        for stem, frame in frames.items():
            emit_send_fixed(
                asm, stem=stem, table=f"t28_frame_{stem}", length=len(frame)
            )
        for stem, frame in frames.items():
            asm.label(f"t28_frame_{stem}")
            asm.emit(*frame)

    return {
        **api_addresses,
        "loader_entry": asm.labels["t28_entry"],
        "loader_loop": asm.labels["t28_loop"],
        "loader_buffer": LOADER_BUFFER,
        "loader_stack_top": LOADER_STACK_TOP,
        "loader_load_min": LOAD_MIN_ADDRESS,
        "loader_load_end": LOAD_END_ADDRESS,
        "loader_capabilities": effective_capabilities,
        "loader_boot_votes": effective_boot_votes,
        "loader_refresh_api": (
            None if refresh_label is None else asm.labels[refresh_label]
        ),
        "loader_refresh_mode": refresh_mode_address,
        "loader_refresh_counter": refresh_counter_address,
        "loader_ready_frame": frames["ready"],
        "loader_bad_crc_frame": frames["bad_crc"],
    }
