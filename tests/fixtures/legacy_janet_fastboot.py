#!/usr/bin/env python3
"""Frozen Python-era Fastboot fixture for PTY regressions and diagnostics.

The production entry point was retired at the portable C host M2 gate. This
module intentionally has no runnable CLI; normal Fastboot uses ``jukuhost``.

The stock Janet 1.2 client transfers a compact stage-1 program at 9600/8O1.
V1/v2 receive thirteen CRC-protected 512-byte blocks; v3-v5 use a one-record
core, a high-speed low-RAM extension, and one strong-CRC system stream. V6
retains 19,200/8N1 and sends a ZX0-classic compressed stream. V7 fixes that
stream's authenticated metadata in its two-record extension, removing one
extension record and four redundant bytes from the bulk stream. V8 uses the
D11 RxRDY interrupt and a linear buffer to overlap ZX0 expansion with reception.
V9 polls only its two-byte marker and transfers the resulting extension at its
exact byte length instead of padding it to Janet-style 128-byte records.
V10 makes every ZX0 input read wait at the interrupt-fed producer pointer,
removing v9's timing-sensitive fixed-lead assumption.
V11 adds an explicit high-speed core acknowledgement before the extension.
V12 makes that handshake overlap-safe; v13 adds the same protection and an
explicit ready acknowledgement for the compressed stream. V14 retains both
handshakes but receives and authenticates the whole stream before decoding it.
V15 applies that path to the self-describing 51K RAM BIOS. V16 stores the
generic receive/decompress extension in the network ROM and sends only the
checked compressed system stream after reset.
"""

from __future__ import annotations

import argparse
import os
import select
import sys
import termios
import time
from collections import deque
from collections.abc import Callable, Iterable
from pathlib import Path

try:
    from legacy_janet_netboot import (
        SYSTEM_BYTES,
        SYSTEM_PREFIX,
        configure_serial,
        serve as serve_stock,
        write_all,
    )
except ModuleNotFoundError:  # Imported as a package by repository tests.
    from tests.fixtures.legacy_janet_netboot import (
        SYSTEM_BYTES,
        SYSTEM_PREFIX,
        configure_serial,
        serve as serve_stock,
        write_all,
    )

FAST_BAUD = 19200
NEGOTIATED_BAUD = 28800
BLOCK_SIZE = 512
BLOCK_COUNT = SYSTEM_BYTES // BLOCK_SIZE
VERSION = 1
SUPPORTED_VERSIONS = (1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16)
BLOCK_PROTOCOL_VERSIONS = (1, 2)
READY = ord("R")
REPLY = ord("A")
PROBE = ord("Q")
HEADER_SEQUENCE = 0xFF
FINAL_SEQUENCE = BLOCK_COUNT
V3_BUNDLE_MAGIC = b"JFV3"
V4_BUNDLE_MAGIC = b"JFV4"
V5_BUNDLE_MAGIC = b"JFV5"
V6_BUNDLE_MAGIC = b"JFV6"
V7_BUNDLE_MAGIC = b"JFV7"
V8_BUNDLE_MAGIC = b"JFV8"
V9_BUNDLE_MAGIC = b"JFV9"
V10_BUNDLE_MAGIC = b"JF10"
V11_BUNDLE_MAGIC = b"JF11"
V12_BUNDLE_MAGIC = b"JF12"
V13_BUNDLE_MAGIC = b"JF13"
V14_BUNDLE_MAGIC = b"JF14"
V15_BUNDLE_MAGIC = b"JF15"
V16_BUNDLE_MAGIC = b"JF16"
V3_EXTENSION_MAGIC = b"\xA5\x3A"
V3_STREAM_MAGIC = b"JS"
V6_PAYLOAD_MAGIC = b"Z0"
V7_PAYLOAD_MAGIC = b"Z7"
V8_PAYLOAD_MAGIC = b"Z8"
V9_PAYLOAD_MAGIC = b"Z9"
V10_PAYLOAD_MAGIC = b"ZA"
V11_PAYLOAD_MAGIC = b"ZB"
V12_PAYLOAD_MAGIC = b"ZC"
V13_PAYLOAD_MAGIC = b"ZD"
V14_PAYLOAD_MAGIC = b"ZE"
V15_PAYLOAD_MAGIC = b"ZF"
V16_PAYLOAD_MAGIC = b"ZG"
EXTENSION_HEADER_ACK = 0xC5
AUTO_ROM_READY = 0xC4
AUTO_ROM_EMBEDDED_READY = 0xC7
STREAM_HEADER_ACK = 0xC6
V6_STREAM_MAGIC = b"JZ"
V6_COMPRESSED_LIMIT = 0x1800
V15_COMPRESSED_LIMIT = 0x2800
V3_WRITE_STALL_TIMEOUT = 10.0


def crc16_ccitt(data: bytes, initial: int = 0xFFFF) -> int:
    """Return the bitwise CRC16-CCITT used by the 8080 stage."""
    crc = initial
    for value in data:
        crc ^= value << 8
        for _ in range(8):
            crc = ((crc << 1) ^ 0x1021) & 0xFFFF \
                if crc & 0x8000 else (crc << 1) & 0xFFFF
    return crc


def crc16_ibm(data: bytes, initial: int = 0) -> int:
    """Return reflected CRC-16/IBM (poly A001h) used by Fast stage v3."""
    crc = initial
    for value in data:
        crc ^= value
        for _ in range(8):
            crc = (crc >> 1) ^ 0xA001 if crc & 1 else crc >> 1
    return crc


def fletcher16(data: bytes) -> tuple[int, int]:
    """Return the one's-complement Fletcher guard as (sum1, sum2)."""
    sum1 = 0
    sum2 = 0
    for value in data:
        total = sum1 + value
        sum1 = (total & 0xFF) + (total >> 8)
        total = sum2 + sum1
        sum2 = (total & 0xFF) + (total >> 8)
    return sum1, sum2


def split_stage_artifact(
    stage: bytes,
) -> tuple[bytes, bytes | None, bytes | None]:
    """Split a self-describing streaming bundle or retain a legacy stage."""
    if len(stage) >= 9 and stage[3:7] in (
        V3_BUNDLE_MAGIC, V4_BUNDLE_MAGIC, V5_BUNDLE_MAGIC, V6_BUNDLE_MAGIC,
        V7_BUNDLE_MAGIC, V8_BUNDLE_MAGIC, V9_BUNDLE_MAGIC,
        V10_BUNDLE_MAGIC, V11_BUNDLE_MAGIC, V12_BUNDLE_MAGIC,
        V13_BUNDLE_MAGIC, V14_BUNDLE_MAGIC, V15_BUNDLE_MAGIC,
        V16_BUNDLE_MAGIC,
    ):
        magic = stage[3:7]
        core_size = stage[7] * 128
        if magic in (
            V9_BUNDLE_MAGIC, V10_BUNDLE_MAGIC, V11_BUNDLE_MAGIC,
            V12_BUNDLE_MAGIC,
            V13_BUNDLE_MAGIC, V14_BUNDLE_MAGIC, V15_BUNDLE_MAGIC,
            V16_BUNDLE_MAGIC,
        ):
            if len(stage) < 11 or stage[8] != 0:
                raise ValueError("malformed exact-length fastboot metadata")
            extension_size = int.from_bytes(stage[9:11], "little")
        else:
            extension_size = stage[8] * 128
        expected_extension = {
            V4_BUNDLE_MAGIC: 384,
            V6_BUNDLE_MAGIC: 384,
            V8_BUNDLE_MAGIC: 640,
        }.get(magic, 256)
        payload_offset = core_size + extension_size
        if magic == V16_BUNDLE_MAGIC:
            extension_valid = extension_size == 0
        elif magic in (
            V9_BUNDLE_MAGIC, V10_BUNDLE_MAGIC, V11_BUNDLE_MAGIC,
            V12_BUNDLE_MAGIC, V13_BUNDLE_MAGIC, V14_BUNDLE_MAGIC,
            V15_BUNDLE_MAGIC,
        ):
            extension_valid = 256 <= extension_size <= 640
        else:
            extension_valid = extension_size == expected_extension
        if core_size != 128 or not extension_valid:
            raise ValueError("malformed streaming fast-bootstrap bundle")
        if magic == V6_BUNDLE_MAGIC:
            if len(stage) <= payload_offset + 4 or \
                    stage[payload_offset:payload_offset + 2] != \
                    V6_PAYLOAD_MAGIC:
                raise ValueError("malformed v6 compressed payload")
            compressed = stage[payload_offset + 4:]
            if len(compressed) >= V6_COMPRESSED_LIMIT:
                raise ValueError("v6 compressed payload exceeds target limit")
            return (
                stage[:core_size],
                stage[core_size:payload_offset],
                compressed,
            )
        if magic in (
            V7_BUNDLE_MAGIC, V8_BUNDLE_MAGIC, V9_BUNDLE_MAGIC,
            V10_BUNDLE_MAGIC, V11_BUNDLE_MAGIC, V12_BUNDLE_MAGIC,
            V13_BUNDLE_MAGIC, V14_BUNDLE_MAGIC, V15_BUNDLE_MAGIC,
            V16_BUNDLE_MAGIC,
        ):
            descriptor_size = 8
            version = {
                V7_BUNDLE_MAGIC: 7,
                V8_BUNDLE_MAGIC: 8,
                V9_BUNDLE_MAGIC: 9,
                V10_BUNDLE_MAGIC: 10,
                V11_BUNDLE_MAGIC: 11,
                V12_BUNDLE_MAGIC: 12,
                V13_BUNDLE_MAGIC: 13,
                V14_BUNDLE_MAGIC: 14,
                V15_BUNDLE_MAGIC: 15,
                V16_BUNDLE_MAGIC: 16,
            }[magic]
            payload_magic = {
                7: V7_PAYLOAD_MAGIC,
                8: V8_PAYLOAD_MAGIC,
                9: V9_PAYLOAD_MAGIC,
                10: V10_PAYLOAD_MAGIC,
                11: V11_PAYLOAD_MAGIC,
                12: V12_PAYLOAD_MAGIC,
                13: V13_PAYLOAD_MAGIC,
                14: V14_PAYLOAD_MAGIC,
                15: V15_PAYLOAD_MAGIC,
                16: V16_PAYLOAD_MAGIC,
            }[version]
            if len(stage) <= payload_offset + descriptor_size or \
                    stage[payload_offset:payload_offset + 2] != \
                    payload_magic:
                raise ValueError(f"malformed v{version} compressed payload")
            descriptor = stage[
                payload_offset:payload_offset + descriptor_size
            ]
            compressed = stage[payload_offset + descriptor_size:]
            declared_length = int.from_bytes(descriptor[4:6], "big")
            declared_crc = int.from_bytes(descriptor[6:8], "big")
            if not compressed or len(compressed) != declared_length:
                raise ValueError(
                    f"v{version} compressed payload length mismatch"
                )
            if version in (8, 9, 10, 11, 12, 13, 14, 15, 16) and \
                    len(compressed) < 256:
                raise ValueError(
                    f"v{version} compressed payload is shorter than its lead"
                )
            compressed_limit = V15_COMPRESSED_LIMIT \
                if version in (15, 16) else V6_COMPRESSED_LIMIT
            if len(compressed) >= compressed_limit:
                raise ValueError(
                    f"v{version} compressed payload exceeds target limit"
                )
            if crc16_ibm(compressed) != declared_crc:
                raise ValueError(
                    f"v{version} compressed payload CRC mismatch"
                )
            return (
                stage[:core_size],
                None if version == 16 else stage[core_size:payload_offset],
                compressed,
            )
        if len(stage) != payload_offset:
            raise ValueError("malformed streaming fast-bootstrap bundle")
        return stage[:core_size], stage[core_size:], None
    return stage, None, None


def extension_packet(extension: bytes) -> bytes:
    if not 256 <= len(extension) <= 640:
        raise ValueError(
            "fast-bootstrap extension must contain 256..640 bytes"
        )
    sum1, sum2 = fletcher16(extension)
    return V3_EXTENSION_MAGIC + extension + bytes((sum1, sum2))


def stream_packet(system: bytes) -> bytes:
    if len(system) != SYSTEM_BYTES:
        raise ValueError(f"fast system must contain exactly {SYSTEM_BYTES} bytes")
    crc = crc16_ibm(system)
    return V3_STREAM_MAGIC + system + bytes((crc >> 8, crc & 0xFF))


def compressed_stream_packet(
    compressed: bytes, *, fixed: bool = False,
    compressed_limit: int = V6_COMPRESSED_LIMIT,
) -> bytes:
    if not compressed or len(compressed) >= compressed_limit:
        raise ValueError("invalid compressed fastboot payload length")
    if fixed:
        return V6_STREAM_MAGIC + compressed
    crc = crc16_ibm(compressed)
    return (
        V6_STREAM_MAGIC
        + len(compressed).to_bytes(2, "big")
        + compressed
        + bytes((crc >> 8, crc & 0xFF))
    )


def checked_frame(kind: int, payload: bytes) -> bytes:
    body = b"J" + bytes((kind,)) + payload
    checksum = 0
    for value in body:
        checksum ^= value
    return body + bytes((checksum,))


def header(system: bytes, version: int = VERSION) -> bytes:
    if len(system) != SYSTEM_BYTES:
        raise ValueError(f"fast system must contain exactly {SYSTEM_BYTES} bytes")
    crc = crc16_ccitt(system)
    if version not in BLOCK_PROTOCOL_VERSIONS:
        raise ValueError(f"unsupported fast-bootstrap version: {version}")
    return checked_frame(
        ord("H"), bytes((version, BLOCK_COUNT, crc >> 8, crc & 0xFF)),
    )


def data_block(
    sequence: int,
    payload: bytes,
    *,
    version: int = VERSION,
    cumulative_crc: int | None = None,
) -> bytes:
    if not 0 <= sequence < BLOCK_COUNT or len(payload) != BLOCK_SIZE:
        raise ValueError("invalid fast-bootstrap block")
    protected = bytes((sequence,)) + payload
    if version == 1 and cumulative_crc is None:
        crc = crc16_ccitt(protected)
    elif version == 2 and cumulative_crc is not None and \
            0 <= cumulative_crc <= 0xFFFF:
        crc = cumulative_crc
    else:
        raise ValueError("invalid CRC mode for fast-bootstrap block")
    return b"JB" + protected + bytes((crc >> 8, crc & 0xFF))


def extract_system(image: bytes) -> bytes:
    """Extract a resident payload from a supported Juku system container."""
    if image.startswith(b"JUKURM1\x1a"):
        size = int.from_bytes(image[12:14], "little")
        expected_crc = int.from_bytes(image[14:16], "little")
        if not size or size % 128 or len(image) != SYSTEM_PREFIX + size:
            raise ValueError("JUKURM1 fastboot image length is inconsistent")
        system = image[SYSTEM_PREFIX:]
        if crc16_ibm(system) != expected_crc:
            raise ValueError("JUKURM1 fastboot image CRC mismatch")
        return system
    if (len(image) != 10240 or
            image[:SYSTEM_PREFIX] != bytes((0xE5,)) * SYSTEM_PREFIX or
            image[SYSTEM_PREFIX] != 0xC3):
        raise ValueError("fast boot requires a 10 KiB JUKUSYS system image")
    return image[SYSTEM_PREFIX:SYSTEM_PREFIX + SYSTEM_BYTES]


class TargetFrameParser:
    """Recover fixed five-byte ready/reply frames after arbitrary garbage."""

    def __init__(self) -> None:
        self.buffer = bytearray()
        self.pending: deque[tuple[int, int, int]] = deque()

    def feed(self, data: bytes) -> list[tuple[int, int, int]]:
        self.buffer.extend(data)
        result: list[tuple[int, int, int]] = []
        while len(self.buffer) >= 5:
            start = self.buffer.find(b"J")
            if start < 0:
                self.buffer.clear()
                break
            if start:
                del self.buffer[:start]
            if len(self.buffer) < 5:
                break
            candidate = bytes(self.buffer[:5])
            if candidate[1] not in (READY, REPLY, PROBE) or \
                    candidate[0] ^ candidate[1] ^ candidate[2] ^ \
                    candidate[3] ^ candidate[4]:
                del self.buffer[0]
                continue
            target_frame = (candidate[1], candidate[2], candidate[3])
            result.append(target_frame)
            self.pending.append(target_frame)
            del self.buffer[:5]
        return result


def _read_frames(fd: int, parser: TargetFrameParser, deadline: float):
    while time.monotonic() < deadline:
        while parser.pending:
            yield parser.pending.popleft()
        ready, _, _ = select.select([fd], [], [], min(
            0.1, max(0.0, deadline - time.monotonic()),
        ))
        if not ready:
            continue
        incoming = os.read(fd, 4096)
        if incoming:
            parser.feed(incoming)


def wait_frame(
    fd: int,
    parser: TargetFrameParser,
    predicate: Callable[[tuple[int, int, int]], bool],
    timeout: float,
) -> tuple[int, int, int] | None:
    deadline = time.monotonic() + timeout
    for target_frame in _read_frames(fd, parser, deadline):
        if predicate(target_frame):
            return target_frame
    return None


def wait_byte(fd: int, value: int, timeout: float) -> bool:
    """Wait for one raw core-handshake byte before framed replies begin."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        ready, _, _ = select.select(
            [fd], [], [], min(0.02, max(0.0, deadline - time.monotonic())),
        )
        if not ready:
            continue
        if bytes((value,)) in os.read(fd, 4096):
            return True
    return False


def serve_fast(
    fd: int,
    stage1: bytes,
    image: bytes,
    *,
    client: int | None = None,
    server: int | None = None,
    stock_timeout: float = 120.0,
    reply_timeout: float = 2.0,
    retries: int = 5,
    turnaround_guard: float = 0.020,
    extension_guard: float | None = None,
    stock_handoff_guard: float = 0.030,
    verbose: bool = True,
    block_filter: Callable[[int, int, bytes], bytes] | None = None,
    reply_filter: Callable[[int, int, tuple[int, int, int]], bool] | None = None,
    extension_filter: Callable[[int, bytes], bytes] | None = None,
    extension_header_filter: Callable[[int, int, bytes], bytes] | None = None,
    stream_header_filter: Callable[[int, int, bytes], bytes] | None = None,
    rate_probe_filter: Callable[[int, bytes], bytes] | None = None,
    configure_rate: bool = True,
    compact_stock_execute: bool = False,
    low_latency_guards: bool = False,
    direct_core: bool = False,
    auto_rom_ready: bool = False,
) -> dict[str, int | float]:
    """Load through stock Janet, or enter a ROM-resident V15 core directly."""
    if not stage1:
        raise ValueError("stage 1 is empty")
    if retries < 1:
        raise ValueError("retry count must be positive")
    if turnaround_guard < 0 or stock_handoff_guard < 0 or \
            (extension_guard is not None and extension_guard < 0):
        raise ValueError("fast-bootstrap guards must not be negative")
    stock_stage, extension, compressed = split_stage_artifact(stage1)
    if len(stock_stage) > 0x1000:
        raise ValueError("stage 1 has an implausible stock-loaded size")
    bundle_version = {
        V3_BUNDLE_MAGIC: 3,
        V4_BUNDLE_MAGIC: 4,
        V5_BUNDLE_MAGIC: 5,
        V6_BUNDLE_MAGIC: 6,
        V7_BUNDLE_MAGIC: 7,
        V8_BUNDLE_MAGIC: 8,
        V9_BUNDLE_MAGIC: 9,
        V10_BUNDLE_MAGIC: 10,
        V11_BUNDLE_MAGIC: 11,
        V12_BUNDLE_MAGIC: 12,
        V13_BUNDLE_MAGIC: 13,
        V14_BUNDLE_MAGIC: 14,
        V15_BUNDLE_MAGIC: 15,
        V16_BUNDLE_MAGIC: 16,
    }.get(stock_stage[3:7], 3)
    if direct_core and bundle_version not in (15, 16):
        raise ValueError("direct ROM fastboot requires a V15/V16 artifact")
    if direct_core and compact_stock_execute:
        raise ValueError("direct ROM fastboot has no stock execute stage")
    if auto_rom_ready and not direct_core:
        raise ValueError("automatic ROM readiness requires direct-core mode")
    if low_latency_guards and not compact_stock_execute:
        raise ValueError(
            "low-latency guards require compact stock execute"
        )
    if low_latency_guards and bundle_version not in (
        7, 8, 9, 10, 11, 12, 13, 14, 15, 16,
    ):
        raise ValueError(
            "low-latency guards require fastboot v7 through v16"
        )
    effective_extension_guard = turnaround_guard \
        if extension_guard is None else extension_guard
    system = extract_system(image)
    if bundle_version in (6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16):
        if bundle_version == 16:
            payload_offset = len(stock_stage)
            expected_crc = int.from_bytes(
                stage1[payload_offset + 2:payload_offset + 4], "big",
            )
            if expected_crc != crc16_ibm(system):
                raise ValueError(
                    "fastboot v16 compressed payload does not match system image"
                )
        else:
            if extension is None:
                raise ValueError(
                    f"fastboot v{bundle_version} extension is missing"
                )
            payload_offset = len(stock_stage) + len(extension)
            expected_crc = int.from_bytes(
                stage1[payload_offset + 2:payload_offset + 4], "big",
            )
            if expected_crc != crc16_ibm(system):
                raise ValueError(
                    f"fastboot v{bundle_version} compressed payload does not "
                    "match system image"
                )
    if direct_core:
        now = time.monotonic()
        stock: dict[str, int | float] = {
            "server": server if server is not None else 2,
            "client": client if client is not None else 1,
            "sent_frames": 0,
            "sent_bytes": 0,
            "acks": 0,
            "rejects": 0,
            "request_started_at": now,
            "transfer_seconds": 0.0,
        }
        stock_finished = now
        request_started_at = now
        stage_seconds = 0.0
    else:
        stock = serve_stock(
            fd, stock_stage, load_address=0x0100, entry=0x0100,
            client=client, server=server, timeout=stock_timeout,
            verbose=verbose, compact_execute=compact_stock_execute,
        )
        stock_finished = time.monotonic()
        request_started_at = float(stock["request_started_at"])
        stage_seconds = float(stock["transfer_seconds"])
    # PTY cosim models the target clock from D57 and has no physical line
    # rate; production callers retain the real termios transition.
    if extension is not None and not direct_core:
        # The stock execute service is unacknowledged. Give its final bytes
        # time to leave the USB-UART before tcflush changes the line rate.
        if low_latency_guards:
            termios.tcdrain(fd)
            time.sleep(stock_handoff_guard)
        else:
            time.sleep(0.050)
    if configure_rate:
        configure_serial(
            fd, FAST_BAUD,
            parity="none"
            if bundle_version in (
                5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16,
            ) else "odd",
        )
    parser = TargetFrameParser()
    auto_ready_seen = 0
    if auto_rom_ready and bundle_version != 16:
        # C4 avoids speculative traffic during the ordinary reset/POST path,
        # but it is deliberately not a permanent dependency. A server may be
        # restarted after the one-shot byte has left the UART; after a short
        # observation window the ordinary self-synchronizing A5/3A probes can
        # recover a target already waiting anywhere in the header scanner.
        ready_timeout = min(stock_timeout, 3.0)
        auto_ready_seen = int(wait_byte(
            fd, AUTO_ROM_READY, ready_timeout,
        ))
        if verbose and not auto_ready_seen:
            print(
                "Automatic ROM C4 readiness was not observed; "
                "falling back to synchronized V15 probes",
                flush=True,
            )
    extension_retries = 0
    transfer_baud = FAST_BAUD
    rate_fallback = 0
    rate_setup_error = ""
    rate_failure_stage = ""
    rate_flag = 1
    extension_header_acks = 0
    extension_header_probes = 0
    if bundle_version == 16:
        ready = wait_frame(
            fd, parser, lambda item: item == (READY, 16, 1),
            min(stock_timeout, 3.0),
        )
        if ready is not None:
            auto_ready_seen = 1
        else:
            # A restarted host may miss both one-shot C7 and JR frames while
            # the resident extension is already waiting for JZ. The stream's
            # overlap-safe header ACK is sufficient synchronization.
            ready = (READY, 16, 1)
    elif extension is not None:
        packet = extension_packet(extension)
        extension_ready = (
            READY, bundle_version, 2 if bundle_version == 4 else 1,
        )
        ready = None
        for attempt in range(retries):
            time.sleep(
                0 if bundle_version in (11, 12, 13, 14, 15)
                else effective_extension_guard
            )
            outgoing = extension_filter(attempt, packet) \
                if extension_filter is not None else packet
            if bundle_version in (12, 13, 14, 15) and len(outgoing) >= 2:
                header_acknowledged = False
                probe_limit = 32 if not direct_core else max(
                    32, int(stock_timeout / 0.025) + 1,
                )
                for probe in range(probe_limit):
                    # A zero before every repeated A5/3A pair releases an
                    # overlap-safe parser from a lone A5 received while D11
                    # changes rate. Never send the extension body until the
                    # resident core explicitly confirms readiness.
                    probe_packet = (b"\0" if probe else b"") + outgoing[:2]
                    if extension_header_filter is not None:
                        probe_packet = extension_header_filter(
                            attempt, probe, probe_packet,
                        )
                    write_all(fd, probe_packet)
                    extension_header_probes += 1
                    if wait_byte(fd, EXTENSION_HEADER_ACK, 0.025):
                        extension_header_acks += 1
                        header_acknowledged = True
                        if direct_core:
                            # Exclude the operator's wait before pressing N.
                            request_started_at = time.monotonic()
                            stock_finished = request_started_at
                            stock["request_started_at"] = request_started_at
                        break
                if not header_acknowledged:
                    extension_retries += 1
                    if verbose:
                        print(
                            f"Fast v{bundle_version} extension: core did not "
                            f"acknowledge "
                            f"{probe_limit} header probes; retry "
                            f"{attempt + 1}/"
                            f"{retries - 1}",
                            flush=True,
                        )
                    continue
                time.sleep(effective_extension_guard)
                write_all(fd, outgoing[2:])
            elif bundle_version == 11 and len(outgoing) >= 2:
                write_all(fd, outgoing[:2])
                if wait_byte(fd, EXTENSION_HEADER_ACK, 0.100):
                    extension_header_acks += 1
                    # Physical D11/D104/USB-UART tests showed that receiving
                    # the ACK does not yet guarantee a clean target RX turn
                    # two milliseconds later. Preserve the normal extension
                    # turnaround interval after the explicit handshake.
                    time.sleep(effective_extension_guard)
                write_all(fd, outgoing[2:])
            else:
                write_all(fd, outgoing)
            ready = wait_frame(
                fd, parser,
                lambda item: item == extension_ready,
                min(reply_timeout, 0.750)
                if bundle_version in (11, 12, 13, 14, 15) else reply_timeout,
            )
            if ready is not None:
                break
            extension_retries += 1
            if verbose:
                print(
                    f"Fast v{bundle_version} extension: no ready marker; "
                    f"retry {attempt + 1}/{retries - 1}",
                    flush=True,
                )
        if ready is None:
            raise TimeoutError(
                f"fast-bootstrap v{bundle_version} extension did not start"
            )
    else:
        ready = wait_frame(
            fd, parser,
            lambda item: (
                item[0] == READY and
                item[1] in BLOCK_PROTOCOL_VERSIONS and
                item[2] == BLOCK_COUNT
            ),
            reply_timeout * retries,
        )
    if ready is None:
        raise TimeoutError("fast-bootstrap stage did not announce readiness")
    protocol_version = ready[1]

    if protocol_version == 4:
        # Ask for the faster in-spec x1 clock while both ends are still at the
        # physically proven 19200 setting. The target falls back by repeatedly
        # probing at 19200 if this bidirectional 28800 handshake fails.
        write_all(fd, checked_frame(ord("F"), bytes((4, 1))))
        if configure_rate:
            # Unlike write_all(), tcdrain waits for the five command bytes to
            # leave the USB-UART. The target's fixed drain then provides the
            # safe window in which to change the host clock.
            try:
                termios.tcdrain(fd)
                configure_serial(fd, NEGOTIATED_BAUD)
            except (OSError, RuntimeError, ValueError) as error:
                rate_setup_error = str(error)
                configure_serial(fd, FAST_BAUD)
        fast_probe = None if rate_setup_error else wait_frame(
            fd, parser, lambda item: item == (PROBE, 4, 1), 0.5,
        )
        if rate_setup_error:
            rate_failure_stage = "host-rate-setup"
        elif fast_probe is None:
            rate_failure_stage = "target-probe-not-received"
        elif verbose:
            print(
                "Fast v4: target-to-host 28800 probe received; "
                "sending host-to-target ACK",
                flush=True,
            )
        fast_ready = None
        if fast_probe is not None:
            fast_ack = checked_frame(ord("K"), bytes((4, 1)))
            outgoing = rate_probe_filter(1, fast_ack) \
                if rate_probe_filter is not None else fast_ack
            write_all(fd, outgoing)
            fast_ready = wait_frame(
                fd, parser, lambda item: item == (READY, 4, 1),
                0.5,
            )
            if fast_ready is None:
                rate_failure_stage = "probe-ack-or-final-ready-not-received"
        if fast_ready is not None:
            ready = fast_ready
            transfer_baud = NEGOTIATED_BAUD
        else:
            rate_fallback = 1
            rate_flag = 0
            if configure_rate:
                configure_serial(fd, FAST_BAUD)
            # A real termios rate change flushes unread garbage. Mirror that
            # boundary in cosim and wait for the target's repeated slow probe.
            parser = TargetFrameParser()
            for _attempt in range(retries):
                slow_probe = wait_frame(
                    fd, parser, lambda item: item == (PROBE, 4, 0),
                    reply_timeout,
                )
                if slow_probe is None:
                    continue
                slow_ack = checked_frame(ord("K"), bytes((4, 0)))
                outgoing = rate_probe_filter(0, slow_ack) \
                    if rate_probe_filter is not None else slow_ack
                write_all(fd, outgoing)
                ready = wait_frame(
                    fd, parser, lambda item: item == (READY, 4, 0),
                    reply_timeout,
                )
                if ready is not None:
                    break
            else:
                raise TimeoutError("fast-bootstrap v4 fallback probe failed")

        if rate_setup_error and verbose:
            print(
                f"Fast v4: 28800 host setup failed ({rate_setup_error}); "
                "recovered through the 19200 target fallback",
                flush=True,
            )
        elif rate_fallback and verbose:
            print(
                f"Fast v4: 28800 negotiation failed at "
                f"{rate_failure_stage}; recovered at 19200",
                flush=True,
            )

    transfer_framing = \
        "8N1" if protocol_version in (
            5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16,
        ) else "8O1"
    if verbose:
        stage_detail = "direct ROM core" if direct_core else \
            f"{len(stock_stage)} bytes via stock Janet"
        extension_detail = "" if extension is None else \
            f"; {len(extension)}-byte extension at high speed"
        print(
            f"Fast stage ready: {stage_detail}"
            f"{extension_detail}; "
            f"protocol v{protocol_version}; switching bulk load to "
            f"{transfer_baud} baud, {transfer_framing}"
            + (" (19200 fallback)" if rate_fallback else ""),
            flush=True,
        )

    retries_used = 0
    stream_header_acks = 0
    stream_header_probes = 0
    completion_confirmed = 1

    def exchange(packet: bytes, sequence: int) -> int:
        nonlocal retries_used
        for attempt in range(retries):
            time.sleep(turnaround_guard)
            outgoing = block_filter(sequence, attempt, packet) \
                if block_filter is not None else packet
            write_all(fd, outgoing)

            def matching_reply(item: tuple[int, int, int]) -> bool:
                if item[0] != REPLY or item[1] != sequence:
                    return False
                return reply_filter is None or reply_filter(
                    sequence, attempt, item,
                )

            response = wait_frame(fd, parser, matching_reply, reply_timeout)
            if response is not None and response[2] == 0:
                return attempt
            retries_used += 1
            if verbose:
                reason = "timeout" if response is None \
                    else f"target status {response[2]}"
                print(
                    f"Fast block {sequence:02X}: {reason}; "
                    f"retry {attempt + 1}/{retries - 1}",
                    flush=True,
                )
        raise TimeoutError(f"fast-bootstrap exchange {sequence:02X} failed")

    if protocol_version in (
        3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16,
    ):
        packet = compressed_stream_packet(
            compressed, fixed=protocol_version in (
                7, 8, 9, 10, 11, 12, 13, 14, 15,
            ),
            compressed_limit=(
                V15_COMPRESSED_LIMIT
                if protocol_version in (15, 16) else V6_COMPRESSED_LIMIT
            ),
        ) \
            if protocol_version in (6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16) \
            and compressed is not None \
            else stream_packet(system)
        stream_ready = (READY, protocol_version, rate_flag)
        success_sequence = 4 if protocol_version == 4 else 0
        for attempt in range(retries):
            stream_acknowledged = False
            time.sleep(turnaround_guard)
            outgoing = block_filter(0, attempt, packet) \
                if block_filter is not None else packet
            if protocol_version in (13, 14, 15, 16) and len(outgoing) >= 2:
                stream_acknowledged = False
                for probe in range(32):
                    probe_packet = (b"\0" if probe else b"") + outgoing[:2]
                    if stream_header_filter is not None:
                        probe_packet = stream_header_filter(
                            attempt, probe, probe_packet,
                        )
                    write_all(fd, probe_packet)
                    stream_header_probes += 1
                    if wait_byte(fd, STREAM_HEADER_ACK, 0.025):
                        stream_header_acks += 1
                        stream_acknowledged = True
                        break
                if not stream_acknowledged:
                    retries_used += 1
                    if verbose:
                        print(
                            f"Fast v{protocol_version} stream: extension did "
                            "not acknowledge "
                            f"32 header probes; retry {attempt + 1}/"
                            f"{retries - 1}",
                            flush=True,
                        )
                    continue
                time.sleep(turnaround_guard)
                write_all(
                    fd, outgoing[2:], stall_timeout=V3_WRITE_STALL_TIMEOUT,
                )
            elif protocol_version in (8, 9, 10, 11, 12) and len(outgoing) >= 2:
                # Let v8-v12 consume JZ and atomically arm the linear producer
                # before the first compressed byte reaches D11.
                write_all(
                    fd, outgoing[:2], stall_timeout=V3_WRITE_STALL_TIMEOUT,
                )
                time.sleep(0.002)
                write_all(
                    fd, outgoing[2:], stall_timeout=V3_WRITE_STALL_TIMEOUT,
                )
            else:
                write_all(
                    fd, outgoing, stall_timeout=V3_WRITE_STALL_TIMEOUT,
                )

            def matching_stream_reply(item: tuple[int, int, int]) -> bool:
                if item == stream_ready:
                    return True
                if item[0] != REPLY or item[1] != success_sequence:
                    return False
                return reply_filter is None or reply_filter(
                    success_sequence, attempt, item,
                )

            response = wait_frame(
                fd, parser, matching_stream_reply,
                reply_timeout,
            )
            if response is not None and response[0] == REPLY and \
                    response[2] == 0:
                break
            # V15 has already authenticated the complete compressed stream
            # before it jumps into the all-RAM system. On a real machine the
            # three final replies can be lost exactly while the target changes
            # from 8N1 to the resident BIOS's 8O1. Re-sending the whole stream
            # at this point is harmful: the receiver may already be CP/M's
            # NetDisk loop. Treat a missing final reply as explicitly
            # *unconfirmed*, then let the first valid disk request be the
            # authoritative evidence that the target entered CP/M.
            if response is None and protocol_version in (15, 16) and \
                    stream_acknowledged:
                completion_confirmed = 0
                if verbose:
                    print(
                        f"Fast v{protocol_version} stream was fully sent after "
                        "a target header "
                        "ACK, but its final reply was not observed; proceeding "
                        "to NetDisk attach instead of retransmitting into a "
                        "possibly running CP/M",
                        flush=True,
                    )
                break
            retries_used += 1
            if verbose:
                reason = "timeout" if response is None else \
                    "target restarted stream"
                print(
                    f"Fast v{protocol_version} stream: {reason}; "
                    f"retry {attempt + 1}/{retries - 1}",
                    flush=True,
                )
        else:
            raise TimeoutError(
                f"fast-bootstrap v{protocol_version} stream failed"
            )
        if protocol_version in (
            4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16,
        ):
            # The target emits three success copies and drains them before
            # entering the resident BIOS. V4-v6 restore 8O1; v7-v16 rely
            # on NETROM2's immediate NETINIT. Avoid changing the host framing
            # in the middle of the repeated success frames.
            success_guard = 0.010 if low_latency_guards else \
                (0.020 if protocol_version in (
                    7, 8, 9, 10, 11, 12, 13, 14, 15, 16,
                ) else 0.080)
            time.sleep(success_guard)
            if configure_rate:
                configure_serial(fd, FAST_BAUD)
        finished = time.monotonic()
        if verbose:
            compression_detail = \
                f"ZX0={len(compressed)} bytes, " if compressed else ""
            print(
                ("Fast bootstrap complete: " if completion_confirmed else
                 "Fast bootstrap transfer sent (completion unconfirmed): ")
                + f"{len(system)} bytes, "
                f"{compression_detail}"
                f"CRC16/IBM={crc16_ibm(system):04X}, "
                f"extension-retries={extension_retries}, "
                f"stream-retries={retries_used}, "
                f"stage={stage_seconds:.2f}s, "
                f"bulk={finished - stock_finished:.2f}s",
                flush=True,
            )
        return {
            **{f"stock_{key}": value for key, value in stock.items()},
            "stage_bytes": len(stock_stage),
            "artifact_bytes": len(stage1),
            "extension_bytes": len(extension) if extension is not None else 0,
            "system_bytes": len(system),
            "stream_bytes": len(compressed) if compressed else len(system),
            "blocks": 1,
            "protocol_version": protocol_version,
            "extension_retries": extension_retries,
            "extension_header_acks": extension_header_acks,
            "extension_header_probes": extension_header_probes,
            "stream_header_acks": stream_header_acks,
            "stream_header_probes": stream_header_probes,
            "transfer_baud": transfer_baud,
            "rate_fallback": rate_fallback,
            "rate_setup_error": rate_setup_error,
            "rate_failure_stage": rate_failure_stage,
            "transfer_framing": transfer_framing,
            "retries": retries_used,
            "completion_confirmed": completion_confirmed,
            "crc16": crc16_ibm(system),
            "request_started_at": request_started_at,
            "stage_seconds": stage_seconds,
            "bulk_seconds": finished - stock_finished,
            "total_seconds": finished - request_started_at,
            "low_latency_guards": int(low_latency_guards),
            "turnaround_guard_ms": effective_extension_guard * 1000,
            "extension_guard_ms": effective_extension_guard * 1000,
            "stream_guard_ms": turnaround_guard * 1000,
            "stock_handoff": (
                "not applicable" if direct_core else
                ("tcdrain" if low_latency_guards else "50ms guard")
            ),
            "stock_handoff_guard_ms": (
                0 if direct_core else
                (stock_handoff_guard * 1000 if low_latency_guards else 50)
            ),
            "success_guard_ms": 10 if low_latency_guards else 20,
            "direct_core": int(direct_core),
            "auto_rom_ready": int(auto_rom_ready),
            "auto_ready_seen": auto_ready_seen,
        }

    exchange(header(system, protocol_version), HEADER_SEQUENCE)
    # The target repeats this critical ACK three times. Hearing the first copy
    # does not yet mean it has released the half-duplex line; v1's first
    # physical run exposed this race as an otherwise unnecessary block-0
    # timeout. Allow all copies and the fixed target drain to finish.
    if protocol_version == 2:
        time.sleep(0.080)
    running_crc = 0xFFFF
    for sequence in range(BLOCK_COUNT):
        offset = sequence * BLOCK_SIZE
        payload = system[offset:offset + BLOCK_SIZE]
        if protocol_version == 2:
            running_crc = crc16_ccitt(payload, running_crc)
            packet = data_block(
                sequence, payload, version=2, cumulative_crc=running_crc,
            )
        else:
            packet = data_block(sequence, payload)
        exchange(packet, sequence)
        if verbose:
            print(
                f"Fast bootstrap: {(sequence + 1) * 100 // BLOCK_COUNT:3d}% "
                f"({sequence + 1}/{BLOCK_COUNT} blocks)",
                flush=True,
            )

    final = wait_frame(
        fd, parser,
        lambda item: item[0] == REPLY and item[1] == FINAL_SEQUENCE,
        max(5.0, reply_timeout),
    )
    if final is None:
        raise TimeoutError("fast-bootstrap final verification timed out")
    if final[2] != 0:
        raise RuntimeError(
            f"fast-bootstrap whole-image verification failed ({final[2]})"
        )
    finished = time.monotonic()
    if verbose:
        print(
            f"Fast bootstrap complete: {len(system)} bytes, "
            f"CRC16={crc16_ccitt(system):04X}, retries={retries_used}, "
            f"stage={stage_seconds:.2f}s, "
            f"bulk={finished - stock_finished:.2f}s",
            flush=True,
        )
    return {
        **{f"stock_{key}": value for key, value in stock.items()},
        "stage_bytes": len(stage1),
        "system_bytes": len(system),
        "blocks": BLOCK_COUNT,
        "protocol_version": protocol_version,
        "retries": retries_used,
        "crc16": crc16_ccitt(system),
        "request_started_at": request_started_at,
        "stage_seconds": stage_seconds,
        "bulk_seconds": finished - stock_finished,
        "total_seconds": finished - request_started_at,
        "low_latency_guards": int(low_latency_guards),
        "turnaround_guard_ms": effective_extension_guard * 1000,
        "extension_guard_ms": effective_extension_guard * 1000,
        "stream_guard_ms": turnaround_guard * 1000,
        "stock_handoff": "not applicable" if direct_core else
        ("tcdrain" if low_latency_guards else "50ms guard"),
        "stock_handoff_guard_ms": (
            0 if direct_core else
            (stock_handoff_guard * 1000 if low_latency_guards else 50)
        ),
        "success_guard_ms": (
            10 if low_latency_guards
            else (20 if protocol_version in (
                7, 8, 9, 10, 11, 12, 13, 14, 15, 16,
            ) else 80)
        ),
        "direct_core": int(direct_core),
        "auto_rom_ready": int(auto_rom_ready),
        "auto_ready_seen": auto_ready_seen,
    }


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("serial", help="serial device, for example /dev/ttyUSB0")
    result.add_argument("stage1", type=Path, help="juku-fastboot-stage1.bin")
    result.add_argument("system", type=Path, help="10 KiB JUKUSYS image")
    result.add_argument("--client", type=lambda value: int(value, 0))
    result.add_argument("--server", type=lambda value: int(value, 0))
    result.add_argument("--timeout", type=float, default=120.0)
    result.add_argument("--reply-timeout", type=float, default=2.0)
    result.add_argument("--retries", type=int, default=5)
    result.add_argument(
        "--compact-stock-execute", action="store_true",
        help="use the ROM-proven one-fragment 0Fh execute service",
    )
    result.add_argument(
        "--low-latency-guards", action="store_true",
        help="with compact execute, drain stock TX and use a 10 ms success "
             "guard",
    )
    result.add_argument(
        "--extension-guard-ms", type=float, default=20.0,
        help="delay before sending the high-speed extension (default: 20 ms)",
    )
    result.add_argument(
        "--stock-handoff-guard-ms", type=float, default=30.0,
        help="after TX drain, allow final 9600-baud bytes to leave the USB "
             "UART (default: 30 ms)",
    )
    result.add_argument(
        "--direct-core", action="store_true",
        help="wait for the ekta4402 N command at 19200 and skip stock Janet",
    )
    result.add_argument(
        "--network-rom", action="store_true",
        help="prefer the automatic ROM's C4 ready byte, then use restart-safe "
             "direct V15",
    )
    return result


def main(argv: Iterable[str] | None = None) -> int:
    args = parser().parse_args(argv)
    direct_core = args.direct_core or args.network_rom
    fd = os.open(args.serial, os.O_RDWR | os.O_NOCTTY | os.O_NONBLOCK)
    try:
        configure_serial(fd, FAST_BAUD if direct_core else 9600,
                         parity="none" if direct_core else "odd")
        serve_fast(
            fd, args.stage1.read_bytes(), args.system.read_bytes(),
            client=args.client, server=args.server,
            stock_timeout=args.timeout, reply_timeout=args.reply_timeout,
            retries=args.retries,
            extension_guard=args.extension_guard_ms / 1000.0,
            stock_handoff_guard=args.stock_handoff_guard_ms / 1000.0,
            compact_stock_execute=args.compact_stock_execute,
            low_latency_guards=args.low_latency_guards,
            direct_core=direct_core,
            auto_rom_ready=args.network_rom,
        )
    finally:
        os.close(fd)
    return 0
