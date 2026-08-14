#!/usr/bin/env python3
"""Boot a Juku with its stock ROM, then load CP/M at 19200 baud.

The stock Janet 1.2 client transfers a compact stage-1 program at 9600/8O1.
V1/v2 receive thirteen CRC-protected 512-byte blocks; v3 uses a one-record
core, a high-speed low-RAM extension, and one strong-CRC system stream.
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
    from janet_netboot import (
        SYSTEM_BYTES,
        SYSTEM_PREFIX,
        configure_serial,
        serve as serve_stock,
        write_all,
    )
except ModuleNotFoundError:  # Imported as tools.janet_fastboot by tests.
    from tools.janet_netboot import (
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
SUPPORTED_VERSIONS = (1, 2, 3, 4)
BLOCK_PROTOCOL_VERSIONS = (1, 2)
READY = ord("R")
REPLY = ord("A")
PROBE = ord("Q")
HEADER_SEQUENCE = 0xFF
FINAL_SEQUENCE = BLOCK_COUNT
V3_BUNDLE_MAGIC = b"JFV3"
V4_BUNDLE_MAGIC = b"JFV4"
V3_EXTENSION_MAGIC = b"\xA5\x3A"
V3_STREAM_MAGIC = b"JS"
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


def split_stage_artifact(stage: bytes) -> tuple[bytes, bytes | None]:
    """Split a self-describing streaming bundle or retain a legacy stage."""
    if len(stage) >= 9 and stage[3:7] in (
        V3_BUNDLE_MAGIC, V4_BUNDLE_MAGIC,
    ):
        core_size = stage[7] * 128
        extension_size = stage[8] * 128
        expected_extension = 256 if stage[3:7] == V3_BUNDLE_MAGIC else 384
        if core_size != 128 or extension_size != expected_extension or \
                len(stage) != core_size + extension_size:
            raise ValueError("malformed streaming fast-bootstrap bundle")
        return stage[:core_size], stage[core_size:]
    return stage, None


def extension_packet(extension: bytes) -> bytes:
    if len(extension) not in (256, 384):
        raise ValueError("fast-bootstrap extension must be 256 or 384 bytes")
    sum1, sum2 = fletcher16(extension)
    return V3_EXTENSION_MAGIC + extension + bytes((sum1, sum2))


def stream_packet(system: bytes) -> bytes:
    if len(system) != SYSTEM_BYTES:
        raise ValueError(f"fast system must contain exactly {SYSTEM_BYTES} bytes")
    crc = crc16_ibm(system)
    return V3_STREAM_MAGIC + system + bytes((crc >> 8, crc & 0xFF))


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
    """Extract the resident B400h-CDFFh bytes from a JUKUSYS image."""
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
    verbose: bool = True,
    block_filter: Callable[[int, int, bytes], bytes] | None = None,
    reply_filter: Callable[[int, int, tuple[int, int, int]], bool] | None = None,
    extension_filter: Callable[[int, bytes], bytes] | None = None,
    rate_probe_filter: Callable[[int, bytes], bytes] | None = None,
    configure_rate: bool = True,
) -> dict[str, int | float]:
    """Load stage 1 through stock Janet, then send the resident image fast."""
    if not stage1 or len(stage1) > 0x1000:
        raise ValueError("stage 1 has an implausible size")
    if retries < 1:
        raise ValueError("retry count must be positive")
    stock_stage, extension = split_stage_artifact(stage1)
    bundle_version = 4 if stock_stage[3:7] == V4_BUNDLE_MAGIC else 3
    system = extract_system(image)
    stock = serve_stock(
        fd, stock_stage, load_address=0x0100, entry=0x0100,
        client=client, server=server, timeout=stock_timeout, verbose=verbose,
    )
    stock_finished = time.monotonic()
    request_started_at = float(stock["request_started_at"])
    stage_seconds = float(stock["transfer_seconds"])
    # PTY cosim models the target clock from D57 and has no physical line
    # rate; production callers retain the real termios transition.
    if extension is not None:
        # The stock execute service is unacknowledged. Give its final bytes
        # time to leave the USB-UART before tcflush changes the line rate.
        time.sleep(0.050)
    if configure_rate:
        configure_serial(fd, FAST_BAUD)
    parser = TargetFrameParser()

    extension_retries = 0
    transfer_baud = FAST_BAUD
    rate_fallback = 0
    rate_setup_error = ""
    rate_failure_stage = ""
    rate_flag = 1
    if extension is not None:
        packet = extension_packet(extension)
        extension_ready = (
            READY, bundle_version, 2 if bundle_version == 4 else 1,
        )
        ready = None
        for attempt in range(retries):
            time.sleep(turnaround_guard)
            outgoing = extension_filter(attempt, packet) \
                if extension_filter is not None else packet
            write_all(fd, outgoing)
            ready = wait_frame(
                fd, parser,
                lambda item: item == extension_ready,
                reply_timeout,
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

    if verbose:
        extension_detail = "" if extension is None else \
            f"; {len(extension)}-byte extension at high speed"
        print(
            f"Fast stage ready: {len(stock_stage)} bytes via stock Janet"
            f"{extension_detail}; "
            f"protocol v{protocol_version}; switching bulk load to "
            f"{transfer_baud} baud, 8O1"
            + (" (19200 fallback)" if rate_fallback else ""),
            flush=True,
        )

    retries_used = 0

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

    if protocol_version in (3, 4):
        packet = stream_packet(system)
        stream_ready = (READY, protocol_version, rate_flag)
        success_sequence = 4 if protocol_version == 4 else 0
        for attempt in range(retries):
            time.sleep(turnaround_guard)
            outgoing = block_filter(0, attempt, packet) \
                if block_filter is not None else packet
            write_all(fd, outgoing, stall_timeout=V3_WRITE_STALL_TIMEOUT)

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
        if protocol_version == 4:
            # The target emits three success copies, drains them, restores
            # 19200/8O1, and only then enters NETROM2. Avoid changing the host
            # rate in the middle of those repeated frames.
            time.sleep(0.080)
            if configure_rate:
                configure_serial(fd, FAST_BAUD)
        finished = time.monotonic()
        if verbose:
            print(
                f"Fast bootstrap complete: {SYSTEM_BYTES} bytes, "
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
            "extension_bytes": len(extension),
            "system_bytes": len(system),
            "blocks": 1,
            "protocol_version": protocol_version,
            "extension_retries": extension_retries,
            "transfer_baud": transfer_baud,
            "rate_fallback": rate_fallback,
            "rate_setup_error": rate_setup_error,
            "rate_failure_stage": rate_failure_stage,
            "retries": retries_used,
            "crc16": crc16_ibm(system),
            "request_started_at": request_started_at,
            "stage_seconds": stage_seconds,
            "bulk_seconds": finished - stock_finished,
            "total_seconds": finished - request_started_at,
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
            f"Fast bootstrap complete: {SYSTEM_BYTES} bytes, "
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
    return result


def main(argv: Iterable[str] | None = None) -> int:
    args = parser().parse_args(argv)
    fd = os.open(args.serial, os.O_RDWR | os.O_NOCTTY | os.O_NONBLOCK)
    try:
        configure_serial(fd, 9600)
        serve_fast(
            fd, args.stage1.read_bytes(), args.system.read_bytes(),
            client=args.client, server=args.server,
            stock_timeout=args.timeout, reply_timeout=args.reply_timeout,
            retries=args.retries,
        )
    finally:
        os.close(fd)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print("janet-fastboot: stopped by operator", file=sys.stderr)
        raise SystemExit(130)
    except (OSError, RuntimeError, TimeoutError, ValueError) as error:
        print(f"janet-fastboot: {error}", file=sys.stderr)
        raise SystemExit(1)
